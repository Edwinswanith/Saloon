from flask import Blueprint, request, jsonify
from mongoengine import Q
from datetime import datetime, date
from models import MissedEnquiry, Appointment, Staff
from utils.auth import require_auth, get_current_user
from utils.branch_filter import get_selected_branch, filter_by_branch, get_user_branch
from models import to_dict

missed_enquiry_bp = Blueprint('missed_enquiry', __name__)

@missed_enquiry_bp.route('/', methods=['GET'])
@require_auth
def list_missed_enquiries(current_user=None):
    """List missed enquiries with filters"""
    try:
        status = request.args.get('status')
        enquiry_type = request.args.get('enquiry_type')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        
        query = Q()
        
        if status:
            query &= Q(status=status)
        if enquiry_type:
            query &= Q(enquiry_type=enquiry_type)
        if start_date:
            query &= Q(created_at__gte=datetime.fromisoformat(start_date))
        if end_date:
            query &= Q(created_at__lte=datetime.fromisoformat(end_date))
        
        # Filter by branch
        branch = get_selected_branch(request, current_user)
        enquiries = filter_by_branch(MissedEnquiry.objects(query), branch).order_by('-created_at')
        
        # Debug logging
        print(f"[Missed Enquiries] Branch: {branch.name if branch else 'ALL'}")
        print(f"[Missed Enquiries] Total enquiries found: {enquiries.count()}")
        
        result = []
        for enquiry in enquiries:
            data = to_dict(enquiry)
            if enquiry.created_by:
                data['created_by_name'] = f"{enquiry.created_by.first_name} {enquiry.created_by.last_name or ''}".strip()
            result.append(data)
        
        print(f"[Missed Enquiries] Returning {len(result)} enquiries")
        response = jsonify({'enquiries': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@missed_enquiry_bp.route('/', methods=['POST'])
@require_auth
def create_missed_enquiry(current_user=None):
    """Create a new missed enquiry"""
    try:
        data = request.json
        
        enquiry = MissedEnquiry(
            customer_name=data.get('customer_name'),
            customer_phone=data.get('customer_phone'),
            enquiry_type=data.get('enquiry_type', 'walk-in'),
            requested_service=data.get('requested_service'),
            requested_product=data.get('requested_product'),
            reason_not_delivered=data.get('reason_not_delivered'),
            follow_up_date=datetime.fromisoformat(data['follow_up_date']).date() if data.get('follow_up_date') else None,
            status=data.get('status', 'open'),
            notes=data.get('notes')
        )
        
        # Set created_by from current user
        if current_user and current_user.get('user_type') == 'staff':
            staff = Staff.objects(id=current_user['id']).first()
            if staff:
                enquiry.created_by = staff
        
        # Set branch from current user
        branch = get_user_branch(current_user)
        if branch:
            enquiry.branch = branch
        
        enquiry.save()
        
        result = to_dict(enquiry)
        response = jsonify({'enquiry': result, 'message': 'Missed enquiry created successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@missed_enquiry_bp.route('/<enquiry_id>', methods=['PUT'])
@require_auth
def update_missed_enquiry(enquiry_id, current_user=None):
    """Update a missed enquiry"""
    try:
        enquiry = MissedEnquiry.objects(id=enquiry_id).first()
        if not enquiry:
            response = jsonify({'error': 'Missed enquiry not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.json
        
        if 'customer_name' in data:
            enquiry.customer_name = data['customer_name']
        if 'customer_phone' in data:
            enquiry.customer_phone = data['customer_phone']
        if 'enquiry_type' in data:
            enquiry.enquiry_type = data['enquiry_type']
        if 'requested_service' in data:
            enquiry.requested_service = data['requested_service']
        if 'requested_product' in data:
            enquiry.requested_product = data['requested_product']
        if 'reason_not_delivered' in data:
            enquiry.reason_not_delivered = data['reason_not_delivered']
        if 'follow_up_date' in data:
            enquiry.follow_up_date = datetime.fromisoformat(data['follow_up_date']).date() if data['follow_up_date'] else None
        if 'status' in data:
            enquiry.status = data['status']
        if 'notes' in data:
            enquiry.notes = data['notes']
        
        enquiry.updated_at = datetime.utcnow()
        enquiry.save()
        
        result = to_dict(enquiry)
        response = jsonify({'enquiry': result, 'message': 'Missed enquiry updated successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@missed_enquiry_bp.route('/<enquiry_id>/convert', methods=['PUT'])
@require_auth
def convert_to_appointment(enquiry_id, current_user=None):
    """Convert missed enquiry to appointment"""
    try:
        enquiry = MissedEnquiry.objects(id=enquiry_id).first()
        if not enquiry:
            response = jsonify({'error': 'Missed enquiry not found'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 404
        
        data = request.json
        appointment_id = data.get('appointment_id')
        
        if appointment_id:
            appointment = Appointment.objects(id=appointment_id).first()
            if appointment:
                enquiry.converted_to_appointment = appointment
                enquiry.status = 'converted'
                enquiry.updated_at = datetime.utcnow()
                enquiry.save()
                
                result = to_dict(enquiry)
                response = jsonify({'enquiry': result, 'message': 'Missed enquiry converted to appointment'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 200
        
        response = jsonify({'error': 'Appointment ID required'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@missed_enquiry_bp.route('/stats', methods=['GET'])
@require_auth
def get_stats(current_user=None):
    """Get statistics for missed enquiries"""
    try:
        # Filter by branch
        branch = get_selected_branch(request, current_user)
        enquiries_filtered = filter_by_branch(MissedEnquiry.objects(), branch)
        
        total = enquiries_filtered.count()
        open_count = enquiries_filtered.filter(status='open').count()
        converted_count = enquiries_filtered.filter(status='converted').count()
        lost_count = enquiries_filtered.filter(status='lost').count()
        
        conversion_rate = (converted_count / total * 100) if total > 0 else 0
        
        stats = {
            'total': total,
            'open': open_count,
            'converted': converted_count,
            'lost': lost_count,
            'conversion_rate': round(conversion_rate, 2)
        }
        
        # Debug logging
        print(f"[Missed Enquiries Stats] Branch: {branch.name if branch else 'ALL'}")
        print(f"[Missed Enquiries Stats] {stats}")
        
        response = jsonify({'stats': stats})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@missed_enquiry_bp.route('/reminders', methods=['GET'])
@require_auth
def get_reminders(current_user=None):
    """Get missed enquiries with follow-up dates due"""
    try:
        today = date.today()
        
        # Filter by branch
        branch = get_selected_branch(request, current_user)
        enquiries = filter_by_branch(
            MissedEnquiry.objects(status='open', follow_up_date__lte=today),
            branch
        ).order_by('follow_up_date')
        
        # Debug logging
        print(f"[Missed Enquiries Reminders] Branch: {branch.name if branch else 'ALL'}")
        print(f"[Missed Enquiries Reminders] Found {enquiries.count()} reminders")
        
        result = []
        for enquiry in enquiries:
            data = to_dict(enquiry)
            result.append(data)
        
        response = jsonify({'enquiries': result, 'count': len(result)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

