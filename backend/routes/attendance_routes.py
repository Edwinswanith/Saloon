from flask import Blueprint, request, jsonify
from models import StaffAttendance, Staff
from datetime import datetime, date, time
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from mongoengine import Q
from utils.branch_filter import get_selected_branch
from utils.auth import require_auth

attendance_bp = Blueprint('attendance', __name__)

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
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if staff_id:
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

        attendance_records = query.order_by('-attendance_date')

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

@attendance_bp.route('/<id>', methods=['GET'])
def get_attendance_record(id):
    """Get a single attendance record by ID"""
    try:
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid attendance ID format'}), 400
        
        attendance = StaffAttendance.objects.get(id=id)
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
def check_in():
    """Staff check-in"""
    try:
        data = request.get_json()

        staff_id = data.get('staff_id')
        if not staff_id or not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        
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
def check_out():
    """Staff check-out"""
    try:
        data = request.get_json()

        staff_id = data.get('staff_id')
        if not staff_id or not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        
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
def mark_attendance():
    """Mark attendance for a staff member (create or update)"""
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
def create_attendance():
    """Create attendance record manually"""
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
def update_attendance(id):
    """Update attendance record"""
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
def delete_attendance(id):
    """Delete attendance record"""
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
def get_staff_attendance(staff_id):
    """Get attendance history for a specific staff member"""
    try:
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        
        try:
            staff = Staff.objects.get(id=staff_id)
        except DoesNotExist:
            return jsonify({'error': 'Staff not found'}), 404

        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        query = StaffAttendance.objects.filter(staff=staff)

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
@require_auth
def get_attendance_summary(current_user=None):
    """Get attendance summary for all staff"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = StaffAttendance.objects
        if branch:
            query = query.filter(branch=branch)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(attendance_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(attendance_date__lte=end)

        # Group by staff
        staff_list = Staff.objects.filter(status='active')

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
