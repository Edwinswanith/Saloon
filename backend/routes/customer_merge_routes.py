from flask import Blueprint, request, jsonify
from models import (Customer, Bill, Appointment, Membership,
                    Lead, Feedback, ServiceRecoveryCase, WhatsAppMessage,
                    CustomerMergeLog)
from datetime import datetime
from bson import ObjectId
from utils.auth import require_role
from utils.branch_filter import get_selected_branch

customer_merge_bp = Blueprint('customer_merge', __name__)


@customer_merge_bp.before_request
def handle_preflight():
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response


def customer_to_dict(c):
    return {
        'id': str(c.id),
        'mobile': c.mobile,
        'firstName': c.first_name or '',
        'lastName': c.last_name or '',
        'email': c.email or '',
        'source': c.source or '',
        'gender': c.gender or '',
        'totalVisits': c.total_visits or 0,
        'totalSpent': float(c.total_spent or 0),
        'lastVisitDate': c.last_visit_date.isoformat() if c.last_visit_date else None,
        'referralCode': c.referral_code or '',
        'secondaryMobiles': c.secondary_mobiles if hasattr(c, 'secondary_mobiles') and c.secondary_mobiles else [],
    }


def count_related_records(customer):
    return {
        'bills': Bill.objects(customer=customer).count(),
        'appointments': Appointment.objects(customer=customer).count(),
        'memberships': Membership.objects(customer=customer).count(),
        'leads': Lead.objects(customer=customer).count(),
        'feedback': Feedback.objects(customer=customer).count(),
        'serviceRecovery': ServiceRecoveryCase.objects(customer=customer).count(),
        'whatsappMessages': WhatsAppMessage.objects(customer=customer).count(),
    }


@customer_merge_bp.route('/preview', methods=['POST'])
@require_role('manager', 'owner')
def merge_preview(current_user=None):
    """Preview what will happen when two customers are merged"""
    try:
        data = request.get_json()
        primary_id = data.get('primary_id')
        secondary_id = data.get('secondary_id')

        if not primary_id or not secondary_id:
            response = jsonify({'error': 'Both primary_id and secondary_id are required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if primary_id == secondary_id:
            response = jsonify({'error': 'Cannot merge a customer with itself'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        try:
            primary = Customer.objects.get(id=primary_id)
            secondary = Customer.objects.get(id=secondary_id)
        except Customer.DoesNotExist:
            response = jsonify({'error': 'One or both customers not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404

        # Check neither is already merged
        if primary.merged_into:
            response = jsonify({'error': 'Primary customer has already been merged into another customer'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if secondary.merged_into:
            response = jsonify({'error': 'Secondary customer has already been merged into another customer'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Count related records
        primary_records = count_related_records(primary)
        secondary_records = count_related_records(secondary)

        response = jsonify({
            'primary': customer_to_dict(primary),
            'secondary': customer_to_dict(secondary),
            'primaryRecords': primary_records,
            'secondaryRecords': secondary_records,
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@customer_merge_bp.route('/execute', methods=['POST'])
@require_role('manager', 'owner')
def merge_execute(current_user=None):
    """Execute the merge: move all records from secondary to primary"""
    try:
        data = request.get_json()
        primary_id = data.get('primary_id')
        secondary_id = data.get('secondary_id')

        if not primary_id or not secondary_id:
            response = jsonify({'error': 'Both primary_id and secondary_id are required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if primary_id == secondary_id:
            response = jsonify({'error': 'Cannot merge a customer with itself'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        try:
            primary = Customer.objects.get(id=primary_id)
            secondary = Customer.objects.get(id=secondary_id)
        except Customer.DoesNotExist:
            response = jsonify({'error': 'One or both customers not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404

        # Validate neither is already merged
        if primary.merged_into:
            response = jsonify({'error': 'Primary customer has already been merged'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        if secondary.merged_into:
            response = jsonify({'error': 'Secondary customer has already been merged'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Step 1: Clear secondary's referral_code to avoid unique constraint conflict
        if secondary.referral_code:
            secondary.referral_code = None
            secondary.save()

        # Step 2: Re-point all references from secondary to primary
        records_moved = {}
        records_moved['bills'] = Bill.objects(customer=secondary).update(set__customer=primary)
        records_moved['appointments'] = Appointment.objects(customer=secondary).update(set__customer=primary)
        records_moved['memberships'] = Membership.objects(customer=secondary).update(set__customer=primary)
        records_moved['leads'] = Lead.objects(customer=secondary).update(set__customer=primary)
        records_moved['feedback'] = Feedback.objects(customer=secondary).update(set__customer=primary)
        records_moved['serviceRecovery'] = ServiceRecoveryCase.objects(customer=secondary).update(set__customer=primary)
        records_moved['whatsappMessages'] = WhatsAppMessage.objects(customer=secondary).update(set__customer=primary)

        total_moved = sum(records_moved.values())

        # Step 3: Absorb secondary's mobile into primary's secondary_mobiles
        if secondary.mobile and secondary.mobile != primary.mobile:
            if not hasattr(primary, 'secondary_mobiles') or not primary.secondary_mobiles:
                primary.secondary_mobiles = []
            if secondary.mobile not in primary.secondary_mobiles:
                primary.secondary_mobiles.append(secondary.mobile)

        # Step 4: Fill in empty fields on primary from secondary
        if not primary.email and secondary.email:
            primary.email = secondary.email
        if not primary.gender and secondary.gender:
            primary.gender = secondary.gender
        if not primary.dob and secondary.dob:
            primary.dob = secondary.dob
        if not primary.dob_range and secondary.dob_range:
            primary.dob_range = secondary.dob_range
        if not primary.whatsapp_consent and secondary.whatsapp_consent:
            primary.whatsapp_consent = True

        # Step 5: Recalculate primary's stats from actual Bill data
        try:
            pipeline = [
                {"$match": {"customer": ObjectId(str(primary.id)), "is_deleted": {"$ne": True}}},
                {"$group": {
                    "_id": None,
                    "total_visits": {"$sum": 1},
                    "total_spent": {"$sum": {"$ifNull": ["$final_amount", 0]}},
                    "last_visit": {"$max": "$bill_date"}
                }}
            ]
            result = list(Bill.objects.aggregate(*pipeline))
            if result:
                primary.total_visits = result[0].get('total_visits', 0)
                primary.total_spent = float(result[0].get('total_spent', 0))
                if result[0].get('last_visit'):
                    primary.last_visit_date = result[0]['last_visit']
            else:
                primary.total_visits = (primary.total_visits or 0) + (secondary.total_visits or 0)
                primary.total_spent = float(primary.total_spent or 0) + float(secondary.total_spent or 0)
                if secondary.last_visit_date:
                    if not primary.last_visit_date or secondary.last_visit_date > primary.last_visit_date:
                        primary.last_visit_date = secondary.last_visit_date
        except Exception as e:
            print(f"[MERGE] Warning: Failed to recalculate stats via aggregation: {e}")
            primary.total_visits = (primary.total_visits or 0) + (secondary.total_visits or 0)
            primary.total_spent = float(primary.total_spent or 0) + float(secondary.total_spent or 0)

        primary.updated_at = datetime.utcnow()
        primary.save()

        # Step 6: Mark secondary as merged
        secondary.merged_into = primary
        secondary.merged_at = datetime.utcnow()
        secondary.save()

        # Step 7: Create audit log
        primary_name = f"{primary.first_name or ''} {primary.last_name or ''}".strip()
        secondary_name = f"{secondary.first_name or ''} {secondary.last_name or ''}".strip()

        # Get branch for audit log
        branch = primary.branch

        merge_log = CustomerMergeLog(
            primary_customer=primary,
            secondary_customer=secondary,
            branch=branch,
            merged_by_name=current_user.get('name', '') if current_user else '',
            secondary_mobile=secondary.mobile,
            secondary_name=secondary_name,
            primary_name=primary_name,
            records_moved=records_moved,
        )
        merge_log.save()

        response = jsonify({
            'message': f'Successfully merged "{secondary_name}" into "{primary_name}". {total_moved} records moved.',
            'recordsMoved': records_moved,
            'totalMoved': total_moved,
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        print(f"[MERGE] Error: {e}")
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500


@customer_merge_bp.route('/history', methods=['GET'])
@require_role('manager', 'owner')
def merge_history(current_user=None):
    """Get merge history for current branch"""
    try:
        branch = get_selected_branch(request, current_user)

        query = CustomerMergeLog.objects
        if branch:
            query = query.filter(branch=branch)

        logs = query.order_by('-created_at').limit(50)

        result = []
        for log in logs:
            result.append({
                'id': str(log.id),
                'primaryName': log.primary_name or '',
                'secondaryName': log.secondary_name or '',
                'secondaryMobile': log.secondary_mobile or '',
                'mergedByName': log.merged_by_name or '',
                'recordsMoved': log.records_moved or {},
                'createdAt': log.created_at.isoformat() if log.created_at else None,
            })

        response = jsonify({'history': result})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response

    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
