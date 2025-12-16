from flask import Blueprint, request, jsonify
from models import Feedback, Customer, Bill
from datetime import datetime
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from mongoengine import Q

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
def get_feedback():
    """Get all feedback with optional filters"""
    try:
        # Query parameters
        customer_id = request.args.get('customer_id')
        bill_id = request.args.get('bill_id')
        min_rating = request.args.get('min_rating', type=int)
        max_rating = request.args.get('max_rating', type=int)
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = Feedback.objects

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
            # Include the entire end date
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(created_at__lte=end)

        feedbacks = query.order_by('-created_at')

        response = jsonify([{
            'id': str(f.id),
            'customer_id': str(f.customer.id) if f.customer else None,
            'customer_name': f"{f.customer.first_name} {f.customer.last_name}" if f.customer else None,
            'customer_mobile': f.customer.mobile if f.customer else None,
            'bill_id': str(f.bill.id) if f.bill else None,
            'bill_number': f.bill.bill_number if f.bill else None,
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
def get_single_feedback(id):
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
def create_feedback():
    """Create new feedback"""
    try:
        data = request.get_json()

        # Validate rating
        rating = data.get('rating')
        if rating and (rating < 1 or rating > 5):
            response = jsonify({'error': 'Rating must be between 1 and 5'})
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

        feedback = Feedback(
            customer=customer,
            bill=bill,
            rating=rating,
            comment=data.get('comment')
        )
        feedback.save()

        response = jsonify({
            'id': str(feedback.id),
            'message': 'Feedback created successfully',
            'data': {
                'id': str(feedback.id),
                'rating': feedback.rating
            }
        })
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

@feedback_bp.route('/stats', methods=['GET'])
def get_feedback_stats():
    """Get feedback statistics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = Feedback.objects

        # Apply date filters
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d')
            query = query.filter(created_at__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d')
            end = end.replace(hour=23, minute=59, second=59)
            query = query.filter(created_at__lte=end)

        # Get all feedbacks
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
def get_recent_feedback():
    """Get recent feedback (last 10)"""
    try:
        limit = request.args.get('limit', 10, type=int)

        feedbacks = Feedback.objects.order_by('-created_at').limit(limit)

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
