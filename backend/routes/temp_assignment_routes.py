from flask import Blueprint, request, jsonify
from models import StaffTempAssignment, Staff, Branch, StaffLeave
from datetime import datetime, date
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from utils.auth import require_role

temp_assignment_bp = Blueprint('temp_assignments', __name__)

@temp_assignment_bp.before_request
def handle_preflight():
    """Handle CORS preflight requests"""
    if request.method == "OPTIONS":
        response = jsonify({})
        response.headers.add("Access-Control-Allow-Origin", "*")
        response.headers.add('Access-Control-Allow-Headers', "*")
        response.headers.add('Access-Control-Allow-Methods', "*")
        return response

@temp_assignment_bp.route('/', methods=['GET'])
@require_role('manager', 'owner')
def get_temp_assignments(current_user=None):
    """Get all temp assignments with filters"""
    try:
        branch_id = request.args.get('branch_id')
        status = request.args.get('status', 'active')
        staff_id = request.args.get('staff_id')
        
        query = StaffTempAssignment.objects()
        
        # Filter by status
        if status:
            query = query.filter(status=status)
        
        # Filter by branch (assignments TO this branch)
        if branch_id and ObjectId.is_valid(branch_id):
            try:
                branch = Branch.objects.get(id=branch_id)
                query = query.filter(temp_branch=branch)
            except DoesNotExist:
                pass
        
        # Filter by staff
        if staff_id and ObjectId.is_valid(staff_id):
            try:
                staff = Staff.objects.get(id=staff_id)
                query = query.filter(staff=staff)
            except DoesNotExist:
                pass
        
        assignments = query.order_by('-start_date')
        
        response = jsonify([{
            'id': str(a.id),
            'staff_id': str(a.staff.id),
            'staff_name': f"{a.staff.first_name} {a.staff.last_name}",
            'staff_mobile': a.staff.mobile if a.staff else None,
            'original_branch': a.original_branch.name if a.original_branch else None,
            'original_branch_id': str(a.original_branch.id) if a.original_branch else None,
            'original_branch_city': a.original_branch.city if a.original_branch else None,
            'temp_branch': a.temp_branch.name if a.temp_branch else None,
            'temp_branch_id': str(a.temp_branch.id) if a.temp_branch else None,
            'temp_branch_city': a.temp_branch.city if a.temp_branch else None,
            'start_date': a.start_date.isoformat() if a.start_date else None,
            'end_date': a.end_date.isoformat() if a.end_date else None,
            'reason': a.reason,
            'covering_for_id': str(a.covering_for.id) if a.covering_for else None,
            'covering_for': f"{a.covering_for.first_name} {a.covering_for.last_name}" if a.covering_for else None,
            'notes': a.notes,
            'status': a.status,
            'created_at': a.created_at.isoformat() if a.created_at else None
        } for a in assignments])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@temp_assignment_bp.route('/', methods=['POST'])
@require_role('manager', 'owner')
def create_temp_assignment(current_user=None):
    """Create a new temp assignment"""
    try:
        data = request.get_json()
        
        # Validate required fields
        if not data.get('staff_id') or not data.get('temp_branch_id'):
            response = jsonify({'error': 'Staff and temp branch are required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        if not data.get('start_date') or not data.get('end_date'):
            response = jsonify({'error': 'Start and end dates are required'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Validate staff exists
        staff = Staff.objects.get(id=data['staff_id'])
        original_branch = staff.branch
        
        if not original_branch:
            response = jsonify({'error': 'Staff must have an original branch assigned'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Validate temp branch exists and is different
        temp_branch = Branch.objects.get(id=data['temp_branch_id'])
        
        if str(original_branch.id) == str(temp_branch.id):
            response = jsonify({'error': 'Temp branch must be different from original branch'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Parse dates
        start_date = datetime.fromisoformat(data['start_date'].replace('Z', '')).date()
        end_date = datetime.fromisoformat(data['end_date'].replace('Z', '')).date()
        
        # Validate date range
        if end_date < start_date:
            response = jsonify({'error': 'End date must be after start date'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        if start_date < date.today():
            response = jsonify({'error': 'Start date cannot be in the past'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Check for overlapping assignments
        from mongoengine import Q
        existing = StaffTempAssignment.objects(
            staff=staff,
            status='active',
            start_date__lte=end_date,
            end_date__gte=start_date
        ).first()
        
        if existing:
            response = jsonify({
                'error': f'Staff already has an active assignment from {existing.start_date} to {existing.end_date}'
            })
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        # Create assignment
        assignment = StaffTempAssignment(
            staff=staff,
            original_branch=original_branch,
            temp_branch=temp_branch,
            start_date=start_date,
            end_date=end_date,
            reason=data.get('reason', 'leave_coverage'),
            notes=data.get('notes'),
            status='active',
            created_by=current_user
        )
        
        # Link to staff being covered if provided
        if data.get('covering_for_id'):
            try:
                covering_for = Staff.objects.get(id=data['covering_for_id'])
                assignment.covering_for = covering_for
                
                # Try to find and link the related leave request
                # Find active leave for this staff that overlaps with assignment dates
                from mongoengine import Q
                related_leave = StaffLeave.objects(
                    staff=covering_for,
                    status='approved',
                    start_date__lte=end_date,
                    end_date__gte=start_date,
                    coverage_required=True
                ).first()
                
                if related_leave:
                    assignment.related_leave = related_leave
                    # Update the leave to link back to this assignment
                    related_leave.covered_by = assignment
                    related_leave.updated_at = datetime.utcnow()
                    related_leave.save()
            except DoesNotExist:
                pass
        
        assignment.save()
        
        response = jsonify({
            'id': str(assignment.id),
            'message': 'Temp assignment created successfully',
            'data': {
                'staff_name': f"{staff.first_name} {staff.last_name}",
                'from_branch': original_branch.name,
                'to_branch': temp_branch.name,
                'period': f"{start_date} to {end_date}"
            }
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 201
    except DoesNotExist as e:
        response = jsonify({'error': 'Staff or Branch not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except ValidationError as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 400
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@temp_assignment_bp.route('/coverage-dashboard', methods=['GET'])
@require_role('manager', 'owner')
def get_coverage_dashboard(current_user=None):
    """Get comprehensive coverage dashboard data"""
    try:
        today = date.today()
        
        # 1. Get staff on leave today
        leaves_today = StaffLeave.objects(
            status='approved',
            start_date__lte=today,
            end_date__gte=today,
            coverage_required=True
        )
        
        # Get active assignments today to check coverage
        active_assignments = StaffTempAssignment.objects(
            status='active',
            start_date__lte=today,
            end_date__gte=today
        )
        
        # Create a set of covered leave IDs
        covered_leave_ids = set()
        for assignment in active_assignments:
            if assignment.covering_for:
                # Find leaves for the staff being covered
                covered_leaves = StaffLeave.objects(
                    staff=assignment.covering_for,
                    status='approved',
                    start_date__lte=today,
                    end_date__gte=today
                )
                for leave in covered_leaves:
                    covered_leave_ids.add(str(leave.id))
            if assignment.related_leave:
                covered_leave_ids.add(str(assignment.related_leave.id))
        
        # Build leaves_today list
        leaves_list = []
        branch_leaves_count = {}  # branch_id -> {total: count, uncovered: count}
        
        for leave in leaves_today:
            leave_id = str(leave.id)
            covered = leave_id in covered_leave_ids or leave.covered_by is not None
            
            branch_id = str(leave.branch.id) if leave.branch else None
            if branch_id:
                if branch_id not in branch_leaves_count:
                    branch_leaves_count[branch_id] = {'total': 0, 'uncovered': 0}
                branch_leaves_count[branch_id]['total'] += 1
                if not covered:
                    branch_leaves_count[branch_id]['uncovered'] += 1
            
            leaves_list.append({
                'leave_id': leave_id,
                'staff_id': str(leave.staff.id),
                'staff_name': f"{leave.staff.first_name} {leave.staff.last_name}",
                'branch_id': branch_id,
                'branch_name': leave.branch.name if leave.branch else None,
                'start_date': leave.start_date.isoformat() if leave.start_date else None,
                'end_date': leave.end_date.isoformat() if leave.end_date else None,
                'leave_type': leave.leave_type,
                'covered': covered,
                'coverage_assignment_id': str(leave.covered_by.id) if leave.covered_by else None
            })
        
        # 2. Branches needing coverage
        branches_needing_coverage = []
        for branch_id, counts in branch_leaves_count.items():
            if counts['uncovered'] > 0:
                try:
                    branch = Branch.objects.get(id=branch_id)
                    branches_needing_coverage.append({
                        'branch_id': branch_id,
                        'branch_name': branch.name,
                        'branch_city': branch.city if branch.city else None,
                        'leaves_count': counts['total'],
                        'uncovered_leaves': counts['uncovered']
                    })
                except DoesNotExist:
                    pass
        
        # 3. Available staff by branch
        all_branches = Branch.objects(is_active=True)
        available_staff_by_branch = []
        
        # Get all staff IDs on leave today
        staff_on_leave_ids = set(str(l.staff.id) for l in leaves_today)
        
        # Get all staff IDs currently temp-assigned elsewhere
        staff_temp_assigned_ids = set()
        for assignment in active_assignments:
            staff_temp_assigned_ids.add(str(assignment.staff.id))
        
        for branch in all_branches:
            # Get permanent staff for this branch
            permanent_staff = Staff.objects(
                branch=branch,
                status='active'
            )
            
            available_staff = []
            for staff in permanent_staff:
                staff_id = str(staff.id)
                
                # Check if staff is available (not on leave, not temp-assigned elsewhere)
                if staff_id not in staff_on_leave_ids and staff_id not in staff_temp_assigned_ids:
                    # Count current assignments for this staff
                    current_assignments = StaffTempAssignment.objects(
                        staff=staff,
                        status='active',
                        start_date__lte=today,
                        end_date__gte=today
                    ).count()
                    
                    available_staff.append({
                        'staff_id': staff_id,
                        'staff_name': f"{staff.first_name} {staff.last_name}",
                        'mobile': staff.mobile if staff.mobile else None,
                        'current_assignments': current_assignments
                    })
            
            if available_staff:  # Only include branches with available staff
                available_staff_by_branch.append({
                    'branch_id': str(branch.id),
                    'branch_name': branch.name,
                    'branch_city': branch.city if branch.city else None,
                    'available_staff': available_staff
                })
        
        # 4. Active assignments today (detailed)
        active_assignments_list = []
        for assignment in active_assignments:
            active_assignments_list.append({
                'id': str(assignment.id),
                'staff_id': str(assignment.staff.id),
                'staff_name': f"{assignment.staff.first_name} {assignment.staff.last_name}",
                'original_branch_id': str(assignment.original_branch.id) if assignment.original_branch else None,
                'original_branch': assignment.original_branch.name if assignment.original_branch else None,
                'temp_branch_id': str(assignment.temp_branch.id) if assignment.temp_branch else None,
                'temp_branch': assignment.temp_branch.name if assignment.temp_branch else None,
                'start_date': assignment.start_date.isoformat() if assignment.start_date else None,
                'end_date': assignment.end_date.isoformat() if assignment.end_date else None,
                'reason': assignment.reason,
                'covering_for_id': str(assignment.covering_for.id) if assignment.covering_for else None,
                'covering_for': f"{assignment.covering_for.first_name} {assignment.covering_for.last_name}" if assignment.covering_for else None
            })
        
        response = jsonify({
            'leaves_today': leaves_list,
            'branches_needing_coverage': branches_needing_coverage,
            'available_staff_by_branch': available_staff_by_branch,
            'active_assignments_today': active_assignments_list
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@temp_assignment_bp.route('/active-today', methods=['GET'])
def get_active_assignments_today(current_user=None):
    """Get all assignments active today"""
    try:
        today = date.today()
        
        assignments = StaffTempAssignment.objects(
            status='active',
            start_date__lte=today,
            end_date__gte=today
        )
        
        response = jsonify([{
            'id': str(a.id),
            'staff_id': str(a.staff.id),
            'staff_name': f"{a.staff.first_name} {a.staff.last_name}",
            'original_branch': a.original_branch.name if a.original_branch else None,
            'temp_branch': a.temp_branch.name if a.temp_branch else None,
            'end_date': a.end_date.isoformat() if a.end_date else None
        } for a in assignments])
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@temp_assignment_bp.route('/<id>', methods=['GET'])
@require_role('manager', 'owner')
def get_temp_assignment(id, current_user=None):
    """Get a single temp assignment"""
    try:
        if not ObjectId.is_valid(id):
            response = jsonify({'error': 'Invalid assignment ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        a = StaffTempAssignment.objects.get(id=id)
        
        response = jsonify({
            'id': str(a.id),
            'staff_id': str(a.staff.id),
            'staff_name': f"{a.staff.first_name} {a.staff.last_name}",
            'original_branch': a.original_branch.name if a.original_branch else None,
            'original_branch_id': str(a.original_branch.id) if a.original_branch else None,
            'temp_branch': a.temp_branch.name if a.temp_branch else None,
            'temp_branch_id': str(a.temp_branch.id) if a.temp_branch else None,
            'start_date': a.start_date.isoformat() if a.start_date else None,
            'end_date': a.end_date.isoformat() if a.end_date else None,
            'reason': a.reason,
            'covering_for_id': str(a.covering_for.id) if a.covering_for else None,
            'covering_for': f"{a.covering_for.first_name} {a.covering_for.last_name}" if a.covering_for else None,
            'notes': a.notes,
            'status': a.status
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Assignment not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@temp_assignment_bp.route('/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_temp_assignment(id, current_user=None):
    """Update a temp assignment"""
    try:
        if not ObjectId.is_valid(id):
            response = jsonify({'error': 'Invalid assignment ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        assignment = StaffTempAssignment.objects.get(id=id)
        data = request.get_json()
        
        # Update end date if provided
        if 'end_date' in data:
            new_end_date = datetime.fromisoformat(data['end_date'].replace('Z', '')).date()
            if new_end_date < assignment.start_date:
                response = jsonify({'error': 'End date must be after start date'})
                response.headers.add('Access-Control-Allow-Origin', '*')
                return response, 400
            assignment.end_date = new_end_date
        
        # Update notes if provided
        if 'notes' in data:
            assignment.notes = data['notes']
        
        # Update status if provided
        if 'status' in data and data['status'] in ['active', 'completed', 'cancelled']:
            old_status = assignment.status
            assignment.status = data['status']
            
            # If status changed to cancelled and there's a related leave, unlink it
            if old_status != 'cancelled' and data['status'] == 'cancelled' and assignment.related_leave:
                leave = assignment.related_leave
                leave.covered_by = None
                leave.updated_at = datetime.utcnow()
                leave.save()
        
        assignment.updated_at = datetime.utcnow()
        assignment.save()
        
        response = jsonify({
            'id': str(assignment.id),
            'message': 'Assignment updated successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Assignment not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

@temp_assignment_bp.route('/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def cancel_temp_assignment(id, current_user=None):
    """Cancel a temp assignment (soft delete)"""
    try:
        if not ObjectId.is_valid(id):
            response = jsonify({'error': 'Invalid assignment ID'})
            response.headers.add('Access-Control-Allow-Origin', '*')
            return response, 400
        
        assignment = StaffTempAssignment.objects.get(id=id)
        assignment.status = 'cancelled'
        assignment.updated_at = datetime.utcnow()
        
        # If this assignment was covering a leave, unlink it
        if assignment.related_leave:
            leave = assignment.related_leave
            leave.covered_by = None
            leave.updated_at = datetime.utcnow()
            leave.save()
        
        assignment.save()
        
        response = jsonify({
            'message': 'Assignment cancelled successfully'
        })
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response
    except DoesNotExist:
        response = jsonify({'error': 'Assignment not found'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 404
    except Exception as e:
        response = jsonify({'error': str(e)})
        response.headers.add('Access-Control-Allow-Origin', '*')
        return response, 500

