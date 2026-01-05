from flask import Blueprint, request, jsonify
from models import Feedback, Customer, Bill, ServiceRecoveryCase
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from mongoengine import Q
from utils.branch_filter import get_selected_branch
from utils.auth import require_auth

feedback_bp = Blueprint('feedback', __name__)

@feedback_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@feedback_bp.route('/', methods=['GET'])
@require_auth
def get_feedback(current_user=None):
    """Get all feedback with optional filters"""
    try:
        # Query parameters
        customer_id = request.args.get('customer_id')
        bill_id = request.args.get('bill_id')
        min_rating = request.args.get('min_rating', type=int)
        max_rating = request.args.get('max_rating', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Feedback.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if customer_id:
            if ObjectId.is_valid(customer_id):
                query = query.filter(customer=ObjectId(customer_id))
        if bill_id:
            if ObjectId.is_valid(bill_id):
                query = query.filter(bill=ObjectId(bill_id))
        if min_rating:
            query = query.filter(rating__gte=min_rating)
        if max_rating:
            query = query.filter(rating__lte=max_rating)
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(created_at__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Set end to end of day to include all data from the end date
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(created_at__lte=end)

        # Force evaluation by converting to list
        feedbacks = list(query.order_by('-created_at'))

        response = jsonify([{
            'id': str(f.id),
            'customer_id': str(f.customer.id) if f.customer else None,
            'customer_name': f"{f.customer.first_name} {f.customer.last_name}" if f.customer else None,
            'customer_mobile': f.customer.mobile if f.customer else None,
            'bill_id': str(f.bill.id) if f.bill else None,
            'bill_number': f.bill.bill_number if f.bill else None,
            'staff_id': str(f.staff.id) if f.staff else None,
            'staff_name': f"{f.staff.first_name} {f.staff.last_name}" if f.staff else None,
            'rating': f.rating,
            'comment': f.comment,
            'created_at': f.created_at.isoformat() if f.created_at else None
        } for f in feedbacks])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@feedback_bp.route('/<id>', methods=['GET'])
@require_auth
def get_single_feedback(id, current_user=None):
    """Get a single feedback by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid feedback ID format'}), 400
        
        feedback = Feedback.objects.get(id=id)
        response = jsonify({
            'id': str(feedback.id),
            'customer_id': str(feedback.customer.id) if feedback.customer else None,
            'customer_name': f"{feedback.customer.first_name} {feedback.customer.last_name}" if feedback.customer else None,
            'bill_id': str(feedback.bill.id) if feedback.bill else None,
            'bill_number': feedback.bill.bill_number if feedback.bill else None,
            'rating': feedback.rating,
            'comment': feedback.comment,
            'created_at': feedback.created_at.isoformat() if feedback.created_at else None
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Feedback not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@feedback_bp.route('/', methods=['POST'])
@require_auth
def create_feedback(current_user=None):
    """Create new feedback"""
    try:
        data = request.get_json()

        # Validate rating
        rating = data.get('rating')
        if rating and (rating < 1 or rating > 5):
            response = jsonify({'error': 'Rating must be between 1 and 5'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Get branch for assignment
        branch = get_selected_branch(request, current_user)
        if not branch:
            response = jsonify({'error': 'Branch is required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400

        # Get customer reference
        customer = None
        customer_id = data.get('customer_id')
        if customer_id:
            if not ObjectId.is_valid(customer_id):
                return jsonify({'error': 'Invalid customer ID format'}), 400
            try:
                customer = Customer.objects.get(id=customer_id)
            except DoesNotExist:
                return jsonify({'error': 'Customer not found'}), 404

        # Get bill reference (optional)
        bill = None
        bill_id = data.get('bill_id')
        if bill_id:
            if not ObjectId.is_valid(bill_id):
                return jsonify({'error': 'Invalid bill ID format'}), 400
            try:
                bill = Bill.objects.get(id=bill_id)
            except DoesNotExist:
                return jsonify({'error': 'Bill not found'}), 404

        # Get staff reference
        staff = None
        staff_id = data.get('staff_id')
        
        # If staff_id not provided, try to get from bill
        if not staff_id and bill:
            # Get primary staff from bill items
            for item in bill.items:
                if item.staff:
                    staff = item.staff
                    break
        elif staff_id:
            if not ObjectId.is_valid(staff_id):
                return jsonify({'error': 'Invalid staff ID format'}), 400
            try:
                from models import Staff
                staff = Staff.objects.get(id=staff_id)
            except DoesNotExist:
                return jsonify({'error': 'Staff not found'}), 404

        # Phase 3: Google Review Gating Logic
        google_review_eligible = False
        service_recovery_required = False
        
        if rating:
            if rating >= 4:
                google_review_eligible = True
            elif rating <= 3:
                service_recovery_required = True
        
        feedback = Feedback(
            customer=customer,
            bill=bill,
            staff=staff,
            branch=branch,
            rating=rating,
            comment=data.get('comment'),
            google_review_eligible=google_review_eligible,
            service_recovery_required=service_recovery_required
        )
        feedback.save()
        
        # Phase 3: Create Service Recovery Case if rating <= 3
        service_recovery_case = None
        if service_recovery_required and customer and bill:
            service_recovery_case = ServiceRecoveryCase(
                feedback=feedback,
                customer=customer,
                branch=branch,
                bill=bill,
                issue_type='service_quality',
                description=f"Low rating ({rating}/5): {data.get('comment', 'No comment provided')}",
                status='open'
            )
            service_recovery_case.save()

        response_data = {
            'id': str(feedback.id),
            'message': 'Feedback created successfully',
            'data': {
                'id': str(feedback.id),
                'rating': feedback.rating,
                'google_review_eligible': google_review_eligible,
                'service_recovery_required': service_recovery_required
            }
        }
        
        if service_recovery_case:
            response_data['service_recovery_case_id'] = str(service_recovery_case.id)
        
        response = jsonify(response_data)
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except ValidationError as e:
        response = jsonify({'error': f'Validation error: {str(e)}'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@feedback_bp.route('/<id>', methods=['PUT'])
def update_feedback(id):
    """Update feedback"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid feedback ID format'}), 400
        
        feedback = Feedback.objects.get(id=id)
        data = request.get_json()

        # Validate rating if provided
        if 'rating' in data:
            rating = data['rating']
            if rating < 1 or rating > 5:
                response = jsonify({'error': 'Rating must be between 1 and 5'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            feedback.rating = rating

        feedback.comment = data.get('comment', feedback.comment)
        feedback.save()

        response = jsonify({
            'id': str(feedback.id),
            'message': 'Feedback updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Feedback not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@feedback_bp.route('/<id>', methods=['DELETE'])
def delete_feedback(id):
    """Delete feedback"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid feedback ID format'}), 400
        
        feedback = Feedback.objects.get(id=id)
        feedback.delete()

        response = jsonify({'message': 'Feedback deleted successfully'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        return jsonify({'error': 'Feedback not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@feedback_bp.route('/<id>/mark-review-clicked', methods=['PUT'])
def mark_review_clicked(id):
    """Mark Google review link as clicked (Phase 3)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid feedback ID format'}), 400
        
        feedback = Feedback.objects.get(id=id)
        feedback.google_review_link_clicked = True
        feedback.google_review_link_clicked_at = datetime.utcnow()
        feedback.save()
        
        response = jsonify({
            'id': str(feedback.id),
            'message': 'Review link click recorded'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 200
    except DoesNotExist:
        return jsonify({'error': 'Feedback not found'}), 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@feedback_bp.route('/stats', methods=['GET'])
@require_auth
def get_feedback_stats(current_user=None):
    """Get feedback statistics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Feedback.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply date filters
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(created_at__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            # Set end to end of day to include all data from the end date
            end = end.replace(hour=23, minute=59, second=59, microsecond=999999)
            query = query.filter(created_at__lte=end)

        # Force evaluation by converting to list
        feedbacks = list(query)

        # Calculate average rating
        if feedbacks:
            avg_rating = sum(f.rating for f in feedbacks if f.rating) / len(feedbacks)
        else:
            avg_rating = 0

        # Count by rating
        rating_counts = {}
        for f in feedbacks:
            if f.rating:
                rating_counts[f.rating] = rating_counts.get(f.rating, 0) + 1

        # Total count
        total = len(feedbacks)

        response = jsonify({
            'total_feedback': total,
            'average_rating': round(avg_rating, 2),
            'rating_distribution': rating_counts,
            'rating_breakdown': {
                '5_star': rating_counts.get(5, 0),
                '4_star': rating_counts.get(4, 0),
                '3_star': rating_counts.get(3, 0),
                '2_star': rating_counts.get(2, 0),
                '1_star': rating_counts.get(1, 0)
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@feedback_bp.route('/recent', methods=['GET'])
@require_auth
def get_recent_feedback(current_user=None):
    """Get recent feedback (last 10)"""
    try:
        limit = request.args.get('limit', 10, type=int)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Feedback.objects
        if branch:
            query = query.filter(branch=branch)
        # Force evaluation by converting to list
        feedbacks = list(query.order_by('-created_at').limit(limit))

        response = jsonify([{
            'id': str(f.id),
            'customer_name': f"{f.customer.first_name} {f.customer.last_name}" if f.customer else 'Anonymous',
            'rating': f.rating,
            'comment': f.comment,
            'created_at': f.created_at.isoformat() if f.created_at else None
        } for f in feedbacks])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500
