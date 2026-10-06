from flask import Blueprint, request, jsonify
from models import StaffAttendance, Staff, StaffLeave
from datetime import datetime, date, time, timedelta
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from mongoengine import Q
from utils.branch_filter import apply_branch_scope, get_selected_branch
from utils.auth import require_auth, require_role

attendance_bp = Blueprint('attendance', __name__)


def _get_current_staff(current_user):
    if not current_user or current_user.get('user_type') != 'staff':
        return None
    user_id = current_user.get('user_id') or current_user.get('id')
    if not user_id or not ObjectId.is_valid(user_id):
        return None
    return Staff.objects(id=user_id).first()

@attendance_bp.route('/', methods=['GET'])
@require_auth
def get_attendance(current_user=None):
    """Get attendance records with optional filters"""
    try:
        # Query parameters
        staff_id = request.args.get('staff_id')
        attendance_date_param = request.args.get('date')  # For single date filtering
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        status = request.args.get('status')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = StaffAttendance.objects
        query = apply_branch_scope(query, branch, current_user)

        staff_user = _get_current_staff(current_user)
        if current_user and current_user.get('user_type') == 'staff':
            if not staff_user:
                return jsonify({'error': 'This endpoint is available for staff login only'}), 403
            if staff_id and str(staff_id) != str(staff_user.id):
                return jsonify({'error': 'Staff can only view their own attendance'}), 403
            query = query.filter(staff=staff_user)
        elif staff_id:
            if ObjectId.is_valid(staff_id):
                query = query.filter(staff=ObjectId(staff_id))
        
        # If 'date' parameter is provided, filter for that specific date
        if attendance_date_param:
            specific_date = datetime.strptime(attendance_date_param, '%Y-%m-%d').date()
            query = query.filter(attendance_date=specific_date)
        else:
            # Otherwise use start_date and end_date for range filtering
            if start_date:
                start = datetime.strptime(start_date, '%Y-%m-%d').date()
                query = query.filter(attendance_date__gte=start)
            if end_date:
                end = datetime.strptime(end_date, '%Y-%m-%d').date()
                query = query.filter(attendance_date__lte=end)
        
        if status:
            query = query.filter(status=status)

        # Force evaluation by converting to list
        attendance_records = list(query.order_by('-attendance_date'))

        return jsonify([{
            'id': str(a.id),
            'staff_id': str(a.staff.id) if a.staff else None,
            'staff_name': f"{a.staff.first_name} {a.staff.last_name}" if a.staff else None,
            'attendance_date': a.attendance_date.isoformat() if a.attendance_date else None,
            'check_in_time': a.check_in_time if a.check_in_time else None,
            'check_out_time': a.check_out_time if a.check_out_time else None,
            'status': a.status,
            'notes': a.notes,
            'created_at': a.created_at.isoformat() if a.created_at else None
        } for a in attendance_records])
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/me', methods=['GET'])
@require_auth
def get_my_attendance(current_user=None):
    """Staff-side attendance history for the logged-in staff user."""
    try:
        staff = _get_current_staff(current_user)
        if not staff:
            return jsonify({'error': 'This endpoint is available for staff login only'}), 403

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')
        if not start_date:
            start = date.today() - timedelta(days=30)
        else:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
        if not end_date:
            end = date.today()
        else:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()

        branch = get_selected_branch(request, current_user)
        query = StaffAttendance.objects(
            staff=staff,
            attendance_date__gte=start,
            attendance_date__lte=end
        )
        query = apply_branch_scope(query, branch, current_user)
        records = list(query.order_by('-attendance_date'))

        today_record = StaffAttendance.objects(staff=staff, attendance_date=date.today()).first()

        return jsonify({
            'staff': {
                'id': str(staff.id),
                'name': f"{staff.first_name} {staff.last_name}".strip(),
            },
            'today': {
                'id': str(today_record.id) if today_record else None,
                'attendance_date': today_record.attendance_date.isoformat() if today_record and today_record.attendance_date else date.today().isoformat(),
                'check_in_time': today_record.check_in_time if today_record else None,
                'check_out_time': today_record.check_out_time if today_record else None,
                'status': today_record.status if today_record else 'not_marked',
                'notes': today_record.notes if today_record else None,
            },
            'records': [{
                'id': str(a.id),
                'attendance_date': a.attendance_date.isoformat() if a.attendance_date else None,
                'check_in_time': a.check_in_time,
                'check_out_time': a.check_out_time,
                'status': a.status,
                'notes': a.notes,
            } for a in records]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/me/leave', methods=['POST'])
@require_auth
def my_leave(current_user=None):
    """Staff-side leave entry with a short reason for owner/manager visibility."""
    try:
        staff = _get_current_staff(current_user)
        if not staff:
            return jsonify({'error': 'This endpoint is available for staff login only'}), 403

        data = request.get_json() or {}
        reason = (data.get('reason') or '').strip()
        if not reason:
            return jsonify({'error': 'Leave reason is required'}), 400

        leave_date_raw = data.get('date') or data.get('attendance_date') or date.today().isoformat()
        leave_date = datetime.strptime(leave_date_raw, '%Y-%m-%d').date()
        leave_type = (data.get('leave_type') or 'casual').strip() or 'casual'

        branch = get_selected_branch(request, current_user) or staff.branch
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400

        existing = StaffAttendance.objects(staff=staff, attendance_date=leave_date).first()
        if existing and (existing.check_in_time or existing.check_out_time):
            return jsonify({'error': 'Attendance already has check-in/check-out for this date'}), 400

        note = f"{leave_type.title()} leave: {reason}"
        if existing:
            existing.branch = branch
            existing.status = 'leave'
            existing.check_in_time = None
            existing.check_out_time = None
            existing.notes = note
            existing.updated_at = datetime.utcnow()
            existing.save()
            attendance = existing
        else:
            attendance = StaffAttendance(
                staff=staff,
                branch=branch,
                attendance_date=leave_date,
                status='leave',
                notes=note
            )
            attendance.save()

        leave = StaffLeave.objects(
            staff=staff,
            start_date__lte=leave_date,
            end_date__gte=leave_date,
            status__in=['pending', 'approved']
        ).first()
        if leave:
            leave.branch = branch
            leave.leave_type = leave_type
            leave.reason = reason
            leave.updated_at = datetime.utcnow()
            leave.save()
        else:
            StaffLeave(
                staff=staff,
                branch=branch,
                start_date=leave_date,
                end_date=leave_date,
                leave_type=leave_type,
                reason=reason,
                status='pending',
                coverage_required=True
            ).save()

        return jsonify({
            'id': str(attendance.id),
            'message': 'Leave recorded successfully',
            'attendance_date': leave_date.isoformat(),
            'status': attendance.status,
            'notes': attendance.notes
        }), 201
    except ValueError:
        return jsonify({'error': 'Invalid date format. Use YYYY-MM-DD'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/me/check-in', methods=['POST'])
@require_auth
def my_check_in(current_user=None):
    """Staff-side self check-in."""
    try:
        staff = _get_current_staff(current_user)
        if not staff:
            return jsonify({'error': 'This endpoint is available for staff login only'}), 403

        today = date.today()
        existing = StaffAttendance.objects(staff=staff, attendance_date=today).first()
        current_time = datetime.now().strftime('%H:%M:%S')
        branch = get_selected_branch(request, current_user) or staff.branch
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400

        if existing:
            if existing.check_in_time:
                return jsonify({'error': 'Already checked in today'}), 400
            existing.check_in_time = current_time
            existing.status = 'present'
            existing.updated_at = datetime.utcnow()
            existing.save()
            return jsonify({'message': 'Checked in successfully', 'check_in_time': current_time})

        attendance = StaffAttendance(
            staff=staff,
            branch=branch,
            attendance_date=today,
            check_in_time=current_time,
            status='present'
        )
        attendance.save()

        return jsonify({'id': str(attendance.id), 'message': 'Checked in successfully', 'check_in_time': current_time}), 201
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@attendance_bp.route('/me/check-out', methods=['POST'])
@require_auth
def my_check_out(current_user=None):
    """Staff-side self check-out."""
    try:
        staff = _get_current_staff(current_user)
        if not staff:
            return jsonify({'error': 'This endpoint is available for staff login only'}), 403

        today = date.today()
        attendance = StaffAttendance.objects(staff=staff, attendance_date=today).first()
        if not attendance:
            return jsonify({'error': 'No check-in record found for today'}), 404
        if attendance.check_out_time:
            return jsonify({'error': 'Already checked out today'}), 400

        current_time = datetime.now().strftime('%H:%M:%S')
        attendance.check_out_time = current_time
        attendance.updated_at = datetime.utcnow()
        attendance.save()

        return jsonify({'message': 'Checked out successfully', 'check_out_time': current_time})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/<id>', methods=['GET'])
@require_auth
def get_attendance_record(id, current_user=None):
    """Get a single attendance record by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid attendance ID format'}), 400
        
        attendance = StaffAttendance.objects.get(id=id)
        staff_user = _get_current_staff(current_user)
        if current_user and current_user.get('user_type') == 'staff':
            if not staff_user or not attendance.staff or str(attendance.staff.id) != str(staff_user.id):
                return jsonify({'error': 'Staff can only view their own attendance'}), 403

        return jsonify({
            'id': str(attendance.id),
            'staff_id': str(attendance.staff.id) if attendance.staff else None,
            'staff_name': f"{attendance.staff.first_name} {attendance.staff.last_name}" if attendance.staff else None,
            'attendance_date': attendance.attendance_date.isoformat() if attendance.attendance_date else None,
            'check_in_time': attendance.check_in_time if attendance.check_in_time else None,
            'check_out_time': attendance.check_out_time if attendance.check_out_time else None,
            'status': attendance.status,
            'notes': attendance.notes,
            'created_at': attendance.created_at.isoformat() if attendance.created_at else None,
            'updated_at': attendance.updated_at.isoformat() if attendance.updated_at else None
        })
    except DoesNotExist:
        return jsonify({'error': 'Attendance record not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/check-in', methods=['POST'])
@require_auth
def check_in(current_user=None):
    """Staff check-in"""
    try:
        data = request.get_json()

        staff_id = data.get('staff_id')
        if not staff_id or not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400

        staff_user = _get_current_staff(current_user)
        if current_user and current_user.get('user_type') == 'staff':
            if not staff_user or str(staff_user.id) != str(staff_id):
                return jsonify({'error': 'Staff can only check in themselves'}), 403
        
        try:
            staff = Staff.objects.get(id=staff_id)
        except DoesNotExist:
            return jsonify({'error': 'Staff not found'}), 404

        today = date.today()

        # Check if already checked in today
        existing = StaffAttendance.objects.filter(
            staff=staff,
            attendance_date=today
        ).first()

        if existing:
            return jsonify({'error': 'Already checked in today'}), 400

        # Get current time as string (HH:MM:SS)
        current_time = datetime.now().time().strftime('%H:%M:%S')

        # Get branch from staff or request
        branch = staff.branch if staff.branch else get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400

        attendance = StaffAttendance(
            staff=staff,
            branch=branch,
            attendance_date=today,
            check_in_time=current_time,
            status='present',
            notes=data.get('notes')
        )
        attendance.save()

        return jsonify({
            'id': str(attendance.id),
            'message': 'Checked in successfully',
            'data': {
                'id': str(attendance.id),
                'check_in_time': current_time
            }
        }), 201
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/check-out', methods=['POST'])
@require_auth
def check_out(current_user=None):
    """Staff check-out"""
    try:
        data = request.get_json()

        staff_id = data.get('staff_id')
        if not staff_id or not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400

        staff_user = _get_current_staff(current_user)
        if current_user and current_user.get('user_type') == 'staff':
            if not staff_user or str(staff_user.id) != str(staff_id):
                return jsonify({'error': 'Staff can only check out themselves'}), 403
        
        try:
            staff = Staff.objects.get(id=staff_id)
        except DoesNotExist:
            return jsonify({'error': 'Staff not found'}), 404

        today = date.today()

        # Find today's attendance record
        attendance = StaffAttendance.objects.filter(
            staff=staff,
            attendance_date=today
        ).first()

        if not attendance:
            return jsonify({'error': 'No check-in record found for today'}), 404

        if attendance.check_out_time:
            return jsonify({'error': 'Already checked out today'}), 400

        # Update check-out time as string (HH:MM:SS)
        current_time = datetime.now().time().strftime('%H:%M:%S')
        attendance.check_out_time = current_time
        attendance.updated_at = datetime.utcnow()

        if 'notes' in data:
            attendance.notes = data['notes']

        attendance.save()

        return jsonify({
            'message': 'Checked out successfully',
            'check_out_time': current_time
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/mark', methods=['POST'])
@require_role('manager', 'owner')
def mark_attendance(current_user=None):
    """Mark attendance for a staff member (create or update) — manager/owner only"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'error': 'No data provided'}), 400

        # Parse date
        attendance_date = datetime.strptime(data['attendance_date'], '%Y-%m-%d').date()
        staff_id = data.get('staff_id')
        
        # Convert staff_id to string if it's not already
        if staff_id:
            staff_id = str(staff_id)
        
        if not staff_id or not ObjectId.is_valid(staff_id):
            return jsonify({'error': f'Invalid staff ID format: {staff_id}'}), 400
        
        try:
            staff = Staff.objects.get(id=staff_id)
        except DoesNotExist:
            return jsonify({'error': f'Staff not found with ID: {staff_id}'}), 404

        status = data.get('status', 'present')

        # Check if record already exists
        existing = StaffAttendance.objects.filter(
            staff=staff,
            attendance_date=attendance_date
        ).first()

        if existing:
            # Update existing record
            existing.status = status
            existing.updated_at = datetime.utcnow()
            if 'notes' in data:
                existing.notes = data['notes']
            
            # Explicitly save and handle any errors
            try:
                existing.save()
            except ValidationError as ve:
                return jsonify({'error': f'Validation error on save: {str(ve)}'}), 400
            except Exception as save_error:
                return jsonify({'error': f'Error saving attendance: {str(save_error)}'}), 500
            
            return jsonify({
                'id': str(existing.id),
                'message': 'Attendance updated successfully',
                'status': existing.status
            })
        else:
            # Get branch from staff or request
            branch = staff.branch if staff.branch else get_selected_branch(request, current_user)
            if not branch:
                return jsonify({'error': 'Branch is required'}), 400
            
            # Create new record
            attendance = StaffAttendance(
                staff=staff,
                branch=branch,
                attendance_date=attendance_date,
                status=status,
                notes=data.get('notes')
            )
            
            # Explicitly save and handle any errors
            try:
                attendance.save()
            except ValidationError as ve:
                return jsonify({'error': f'Validation error on save: {str(ve)}'}), 400
            except Exception as save_error:
                return jsonify({'error': f'Error saving attendance: {str(save_error)}'}), 500
            
            return jsonify({
                'id': str(attendance.id),
                'message': 'Attendance marked successfully',
                'status': attendance.status
            }), 201
    except ValueError as ve:
        return jsonify({'error': f'Invalid date format: {str(ve)}'}), 400
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        import traceback
        return jsonify({'error': f'Unexpected error: {str(e)}', 'traceback': traceback.format_exc()}), 500

@attendance_bp.route('/', methods=['POST'])
@require_role('manager', 'owner')
def create_attendance(current_user=None):
    """Create attendance record manually (manager/owner only)"""
    try:
        data = request.get_json()

        # Parse date and times
        attendance_date = datetime.strptime(data['attendance_date'], '%Y-%m-%d').date()

        staff_id = data.get('staff_id')
        if not staff_id or not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        
        try:
            staff = Staff.objects.get(id=staff_id)
        except DoesNotExist:
            return jsonify({'error': 'Staff not found'}), 404

        check_in_time = None
        if 'check_in_time' in data and data['check_in_time']:
            # If it's already a string, use it; otherwise parse and convert to string
            if isinstance(data['check_in_time'], str):
                check_in_time = data['check_in_time']
            else:
                check_in_time = datetime.strptime(data['check_in_time'], '%H:%M:%S').time().strftime('%H:%M:%S')

        check_out_time = None
        if 'check_out_time' in data and data['check_out_time']:
            # If it's already a string, use it; otherwise parse and convert to string
            if isinstance(data['check_out_time'], str):
                check_out_time = data['check_out_time']
            else:
                check_out_time = datetime.strptime(data['check_out_time'], '%H:%M:%S').time().strftime('%H:%M:%S')

        # Check if record already exists
        existing = StaffAttendance.objects.filter(
            staff=staff,
            attendance_date=attendance_date
        ).first()

        if existing:
            return jsonify({'error': 'Attendance record already exists for this date'}), 400

        # Get branch from staff or request
        branch = staff.branch if staff.branch else get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400

        attendance = StaffAttendance(
            staff=staff,
            branch=branch,
            attendance_date=attendance_date,
            check_in_time=check_in_time,
            check_out_time=check_out_time,
            status=data.get('status', 'present'),
            notes=data.get('notes')
        )
        attendance.save()

        return jsonify({
            'id': str(attendance.id),
            'message': 'Attendance record created successfully',
            'data': {
                'id': str(attendance.id)
            }
        }), 201
    except ValidationError as e:
        return jsonify({'error': f'Validation error: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/<id>', methods=['PUT'])
@require_role('manager', 'owner')
def update_attendance(id, current_user=None):
    """Update attendance record (manager/owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid attendance ID format'}), 400
        
        attendance = StaffAttendance.objects.get(id=id)
        data = request.get_json()

        # Update times if provided (store as strings)
        if 'check_in_time' in data:
            if data['check_in_time']:
                if isinstance(data['check_in_time'], str):
                    attendance.check_in_time = data['check_in_time']
                else:
                    attendance.check_in_time = datetime.strptime(data['check_in_time'], '%H:%M:%S').time().strftime('%H:%M:%S')
            else:
                attendance.check_in_time = None

        if 'check_out_time' in data:
            if data['check_out_time']:
                if isinstance(data['check_out_time'], str):
                    attendance.check_out_time = data['check_out_time']
                else:
                    attendance.check_out_time = datetime.strptime(data['check_out_time'], '%H:%M:%S').time().strftime('%H:%M:%S')
            else:
                attendance.check_out_time = None

        attendance.status = data.get('status', attendance.status)
        attendance.notes = data.get('notes', attendance.notes)
        attendance.updated_at = datetime.utcnow()
        attendance.save()

        return jsonify({
            'id': str(attendance.id),
            'message': 'Attendance record updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Attendance record not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/<id>', methods=['DELETE'])
@require_role('manager', 'owner')
def delete_attendance(id, current_user=None):
    """Delete attendance record (manager/owner only)"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid attendance ID format'}), 400
        
        attendance = StaffAttendance.objects.get(id=id)
        attendance.delete()

        return jsonify({'message': 'Attendance record deleted successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Attendance record not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/staff/<staff_id>', methods=['GET'])
@require_auth
def get_staff_attendance(staff_id, current_user=None):
    """Get attendance history for a specific staff member"""
    try:
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400

        staff_user = _get_current_staff(current_user)
        if current_user and current_user.get('user_type') == 'staff':
            if not staff_user or str(staff_user.id) != str(staff_id):
                return jsonify({'error': 'Staff can only view their own attendance'}), 403
        
        try:
            staff = Staff.objects.get(id=staff_id)
        except DoesNotExist:
            return jsonify({'error': 'Staff not found'}), 404

        # Branch scope — staff from another branch can't be queried across the boundary
        branch = get_selected_branch(request, current_user)
        if branch and staff.branch and str(staff.branch.id) != str(branch.id):
            return jsonify({'error': 'Staff does not belong to this branch'}), 403

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = StaffAttendance.objects.filter(staff=staff)
        query = apply_branch_scope(query, branch, current_user)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(attendance_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(attendance_date__lte=end)

        records = query.order_by('-attendance_date')

        return jsonify([{
            'id': str(a.id),
            'attendance_date': a.attendance_date.isoformat() if a.attendance_date else None,
            'check_in_time': a.check_in_time if a.check_in_time else None,
            'check_out_time': a.check_out_time if a.check_out_time else None,
            'status': a.status,
            'notes': a.notes
        } for a in records])
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@attendance_bp.route('/summary', methods=['GET'])
@require_role('manager', 'owner')
def get_attendance_summary(current_user=None):
    """Get attendance summary for all staff"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = StaffAttendance.objects
        query = apply_branch_scope(query, branch, current_user)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(attendance_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(attendance_date__lte=end)

        # Group by staff
        staff_list = Staff.objects.filter(status='active')
        staff_list = apply_branch_scope(staff_list, branch, current_user)

        summary = []
        for staff in staff_list:
            staff_records = list(query.filter(staff=staff))

            total_days = len(staff_records)
            present_days = len([r for r in staff_records if r.status == 'present'])
            absent_days = len([r for r in staff_records if r.status == 'absent'])
            late_days = len([r for r in staff_records if r.status == 'late'])

            summary.append({
                'staff_id': str(staff.id),
                'staff_name': f"{staff.first_name} {staff.last_name}",
                'total_days': total_days,
                'present_days': present_days,
                'absent_days': absent_days,
                'late_days': late_days,
                'attendance_rate': (present_days / total_days * 100) if total_days > 0 else 0
            })

        return jsonify(summary)
    except Exception as e:
        return jsonify({'error': str(e)}), 500
