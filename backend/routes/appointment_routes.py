from flask import Blueprint, request, jsonify
from models import Appointment, Customer, Staff, Service
from datetime import datetime, date, time, timedelta
from mongoengine.errors import DoesNotExist, ValidationError
from bson import ObjectId
from utils.branch_filter import get_selected_branch
from utils.auth import require_auth

appointment_bp = Blueprint('appointment', __name__)

@appointment_bp.route('/appointments', methods=['GET'])
@require_auth
def get_appointments(current_user=None):
    """Get all appointments with optional filters"""
    try:
        # Query parameters
        customer_id = request.args.get('customer_id', type=str)
        staff_id = request.args.get('staff_id', type=str)
        status = request.args.get('status')
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Appointment.objects
        if branch:
            query = query.filter(branch=branch)

        # Apply filters
        if customer_id:
            if ObjectId.is_valid(customer_id):
                try:
                    customer = Customer.objects.get(id=customer_id)
                    query = query.filter(customer=customer)
                except (DoesNotExist, ValidationError):
                    pass
        if staff_id:
            if ObjectId.is_valid(staff_id):
                try:
                    staff = Staff.objects.get(id=staff_id)
                    query = query.filter(staff=staff)
                except (DoesNotExist, ValidationError):
                    pass
        if status:
            query = query.filter(status=status)
        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(appointment_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(appointment_date__lte=end)

        appointments = query.order_by('-appointment_date', '-start_time')

        result = []
        for a in appointments:
            try:
                service_name = None
                if a.service:
                    service_name = a.service.name
                
                result.append({
                    'id': str(a.id),
                    'customer_id': str(a.customer.id) if a.customer else None,
                    'customer_name': f"{a.customer.first_name} {a.customer.last_name}" if a.customer else None,
                    'customer_mobile': a.customer.mobile if a.customer else None,
                    'staff_id': str(a.staff.id) if a.staff else None,
                    'staff_name': f"{a.staff.first_name} {a.staff.last_name}" if a.staff else None,
                    'service_id': str(a.service.id) if a.service else None,
                    'service_name': service_name,
                    'appointment_date': a.appointment_date.isoformat() if a.appointment_date else None,
                    'start_time': a.start_time if a.start_time else None,  # Already a string
                    'end_time': a.end_time if a.end_time else None,  # Already a string
                    'status': a.status,
                    'notes': a.notes,
                    'created_at': a.created_at.isoformat() if a.created_at else None
                })
            except Exception as e:
                # Skip appointments with errors but log them
                print(f"Error processing appointment {a.id}: {str(e)}")
                continue
        
        return jsonify(result)
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments/<id>', methods=['GET'])
@require_auth
def get_appointment(id, current_user=None):
    """Get a single appointment by ID"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid appointment ID format'}), 400
        appointment = Appointment.objects.get(id=id)
        
        # Get service name safely
        service_name = None
        if appointment.service:
            service_name = appointment.service.name
        
        return jsonify({
            'id': str(appointment.id),
            'customer_id': str(appointment.customer.id) if appointment.customer else None,
            'customer_name': f"{appointment.customer.first_name} {appointment.customer.last_name}" if appointment.customer else None,
            'customer_mobile': appointment.customer.mobile if appointment.customer else None,
            'staff_id': str(appointment.staff.id) if appointment.staff else None,
            'staff_name': f"{appointment.staff.first_name} {appointment.staff.last_name}" if appointment.staff else None,
            'service_id': str(appointment.service.id) if appointment.service else None,
            'service_name': service_name,
            'appointment_date': appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            'start_time': appointment.start_time if appointment.start_time else None,  # Already a string
            'end_time': appointment.end_time if appointment.end_time else None,  # Already a string
            'status': appointment.status,
            'notes': appointment.notes,
            'created_at': appointment.created_at.isoformat() if appointment.created_at else None,
            'updated_at': appointment.updated_at.isoformat() if appointment.updated_at else None
        })
    except DoesNotExist:
        return jsonify({'error': 'Appointment not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments', methods=['POST'])
@require_auth
def create_appointment(current_user=None):
    """Create a new appointment"""
    try:
        data = request.get_json()
        
        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        if not branch:
            return jsonify({'error': 'Branch is required'}), 400
        
        # Validate required fields
        if not data.get('customer_id') or not data.get('staff_id') or not data.get('appointment_date') or not data.get('start_time'):
            return jsonify({'error': 'Missing required fields: customer_id, staff_id, appointment_date, and start_time are required'}), 400

        # Validate and get customer and staff references
        if not ObjectId.is_valid(data['customer_id']):
            return jsonify({'error': f"Invalid customer ID format: {data['customer_id']}"}), 400
        if not ObjectId.is_valid(data['staff_id']):
            return jsonify({'error': f"Invalid staff ID format: {data['staff_id']}"}), 400
        
        try:
            customer = Customer.objects.get(id=data['customer_id'])
        except DoesNotExist:
            return jsonify({'error': 'Customer not found'}), 400
        except ValidationError:
            return jsonify({'error': 'Invalid customer ID format'}), 400
        
        try:
            staff = Staff.objects.get(id=data['staff_id'])
        except DoesNotExist:
            return jsonify({'error': 'Staff not found'}), 400
        except ValidationError:
            return jsonify({'error': 'Invalid staff ID format'}), 400

        # Parse date and time - handle both HH:MM and HH:MM:SS formats
        appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()
        
        # Parse time - store as string (HH:MM:SS format)
        time_str = data['start_time']
        if '.' in time_str:
            time_str = time_str.split('.')[0]
        if len(time_str) == 5:  # HH:MM format
            start_time = time_str + ':00'  # Convert to HH:MM:SS
        else:  # HH:MM:SS format
            start_time = time_str

        # Calculate end_time if service is provided
        end_time = None
        service = None
        if data.get('service_id'):
            if ObjectId.is_valid(data['service_id']):
                try:
                    service = Service.objects.get(id=data['service_id'])
                except (DoesNotExist, ValidationError):
                    pass
            else:
                return jsonify({'error': f"Invalid service ID format: {data['service_id']}"}), 400
        
        if 'end_time' in data and data['end_time']:
            end_time_str = data['end_time']
            if '.' in end_time_str:
                end_time_str = end_time_str.split('.')[0]
            if len(end_time_str) == 5:  # HH:MM format
                end_time = end_time_str + ':00'
            else:  # HH:MM:SS format
                end_time = end_time_str
        elif data.get('service_id') and service and service.duration:
            # Calculate end time based on service duration
            start_datetime = datetime.strptime(start_time, '%H:%M:%S')
            end_datetime = start_datetime + timedelta(minutes=service.duration)
            end_time = end_datetime.strftime('%H:%M:%S')

        # Check for conflicts
        # Convert start_time to time object for comparison
        start_time_obj = datetime.strptime(start_time, '%H:%M:%S').time()
        conflicts = Appointment.objects(
            staff=staff,
            appointment_date=appointment_date,
            start_time=start_time,
            status__in=['confirmed', 'completed']
        )
        
        if conflicts.count() > 0:
            return jsonify({'error': 'This time slot is already booked for the selected staff'}), 400

        appointment = Appointment(
            customer=customer,
            staff=staff,
            service=service,
            branch=branch,
            appointment_date=appointment_date,
            start_time=start_time,  # Store as string
            end_time=end_time,  # Store as string
            status=data.get('status', 'confirmed'),
            notes=data.get('notes')
        )
        appointment.save()
        
        # Get service name safely
        service_name = service.name if service else None

        return jsonify({
            'id': str(appointment.id),
            'message': 'Appointment created successfully',
            'customer_id': str(appointment.customer.id) if appointment.customer else None,
            'customer_name': f"{appointment.customer.first_name} {appointment.customer.last_name}" if appointment.customer else None,
            'staff_id': str(appointment.staff.id) if appointment.staff else None,
            'staff_name': f"{appointment.staff.first_name} {appointment.staff.last_name}" if appointment.staff else None,
            'service_id': str(appointment.service.id) if appointment.service else None,
            'service_name': service_name,
            'appointment_date': appointment.appointment_date.isoformat() if appointment.appointment_date else None,
            'start_time': appointment.start_time,  # Already a string
            'end_time': appointment.end_time,  # Already a string
            'status': appointment.status,
            'notes': appointment.notes
        }), 201
    except ValueError as e:
        return jsonify({'error': f'Invalid date or time format: {str(e)}'}), 400
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments/<id>', methods=['PUT'])
@require_auth
def update_appointment(id, current_user=None):
    """Update an appointment"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid appointment ID format'}), 400
        appointment = Appointment.objects.get(id=id)
        data = request.get_json()

        # Update date and time if provided
        if 'appointment_date' in data:
            appointment.appointment_date = datetime.strptime(data['appointment_date'], '%Y-%m-%d').date()

        if 'start_time' in data:
            time_str = data['start_time']
            if '.' in time_str:
                time_str = time_str.split('.')[0]
            if len(time_str) == 5:  # HH:MM format
                appointment.start_time = time_str + ':00'
            else:
                appointment.start_time = time_str

        if 'end_time' in data:
            if data['end_time']:
                end_time_str = data['end_time']
                if '.' in end_time_str:
                    end_time_str = end_time_str.split('.')[0]
                if len(end_time_str) == 5:  # HH:MM format
                    appointment.end_time = end_time_str + ':00'
                else:
                    appointment.end_time = end_time_str
            else:
                appointment.end_time = None

        if 'customer_id' in data:
            if not ObjectId.is_valid(data['customer_id']):
                return jsonify({'error': 'Invalid customer ID format'}), 400
            try:
                appointment.customer = Customer.objects.get(id=data['customer_id'])
            except DoesNotExist:
                return jsonify({'error': 'Customer not found'}), 400
            except ValidationError:
                return jsonify({'error': 'Invalid customer ID format'}), 400

        if 'staff_id' in data:
            if not ObjectId.is_valid(data['staff_id']):
                return jsonify({'error': 'Invalid staff ID format'}), 400
            try:
                appointment.staff = Staff.objects.get(id=data['staff_id'])
            except DoesNotExist:
                return jsonify({'error': 'Staff not found'}), 400
            except ValidationError:
                return jsonify({'error': 'Invalid staff ID format'}), 400

        if 'service_id' in data:
            if data['service_id']:
                if not ObjectId.is_valid(data['service_id']):
                    return jsonify({'error': 'Invalid service ID format'}), 400
                try:
                    appointment.service = Service.objects.get(id=data['service_id'])
                except DoesNotExist:
                    return jsonify({'error': 'Service not found'}), 400
                except ValidationError:
                    return jsonify({'error': 'Invalid service ID format'}), 400
            else:
                appointment.service = None

        appointment.status = data.get('status', appointment.status)
        appointment.notes = data.get('notes', appointment.notes)
        appointment.updated_at = datetime.utcnow()
        appointment.save()

        return jsonify({
            'id': str(appointment.id),
            'message': 'Appointment updated successfully'
        })
    except DoesNotExist:
        return jsonify({'error': 'Appointment not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments/<id>', methods=['DELETE'])
@require_auth
def cancel_appointment(id, current_user=None):
    """Cancel an appointment"""
    try:
        # Validate ObjectId format
        if not ObjectId.is_valid(id):
            return jsonify({'error': 'Invalid appointment ID format'}), 400
        appointment = Appointment.objects.get(id=id)
        appointment.status = 'cancelled'
        appointment.updated_at = datetime.utcnow()
        appointment.save()

        return jsonify({'message': 'Appointment cancelled successfully'})
    except DoesNotExist:
        return jsonify({'error': 'Appointment not found'}), 404
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments/calendar', methods=['GET'])
@require_auth
def get_calendar_view(current_user=None):
    """Get appointments for calendar view"""
    try:
        # Query parameters
        view_type = request.args.get('view', 'week')  # day, week, month
        target_date = request.args.get('date')
        staff_id = request.args.get('staff_id', type=str)

        if target_date:
            target = datetime.strptime(target_date, '%Y-%m-%d').date()
        else:
            target = date.today()

        # Calculate date range based on view type
        if view_type == 'day':
            start_date = target
            end_date = target
        elif view_type == 'week':
            # Get start of week (Monday)
            start_date = target - timedelta(days=target.weekday())
            end_date = start_date + timedelta(days=6)
        else:  # month
            # Get first and last day of month
            start_date = target.replace(day=1)
            next_month = target.replace(day=28) + timedelta(days=4)
            end_date = next_month - timedelta(days=next_month.day)

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Appointment.objects(
            appointment_date__gte=start_date,
            appointment_date__lte=end_date
        )
        if branch:
            query = query.filter(branch=branch)

        if staff_id:
            try:
                staff = Staff.objects.get(id=staff_id)
                query = query.filter(staff=staff)
            except DoesNotExist:
                pass

        appointments = query.order_by('appointment_date', 'start_time')

        result_appointments = []
        for a in appointments:
            try:
                service_name = None
                if a.service:
                    service_name = a.service.name
                
                result_appointments.append({
                    'id': str(a.id),
                    'customer_name': f"{a.customer.first_name} {a.customer.last_name}" if a.customer else None,
                    'customer_mobile': a.customer.mobile if a.customer else None,
                    'staff_name': f"{a.staff.first_name} {a.staff.last_name}" if a.staff else None,
                    'service_name': service_name,
                    'appointment_date': a.appointment_date.isoformat() if a.appointment_date else None,
                    'start_time': a.start_time if a.start_time else None,  # Already a string
                    'end_time': a.end_time if a.end_time else None,  # Already a string
                    'status': a.status,
                    'notes': a.notes
                })
            except Exception as e:
                print(f"Error processing appointment {a.id}: {str(e)}")
                continue

        return jsonify({
            'view_type': view_type,
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'appointments': result_appointments
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments/available-slots', methods=['GET'])
def get_available_slots():
    """Get available time slots for a staff on a specific date"""
    try:
        staff_id = request.args.get('staff_id', type=str)
        target_date = request.args.get('date')
        service_id = request.args.get('service_id', type=str)

        if not staff_id or not target_date:
            return jsonify({'error': 'staff_id and date are required'}), 400

        target = datetime.strptime(target_date, '%Y-%m-%d').date()

        # Get service duration if provided
        service_duration = 30  # default 30 minutes
        if service_id:
            if ObjectId.is_valid(service_id):
                try:
                    service = Service.objects.get(id=service_id)
                    if service and service.duration:
                        service_duration = service.duration
                except (DoesNotExist, ValidationError):
                    pass

        # Validate and get staff
        if not ObjectId.is_valid(staff_id):
            return jsonify({'error': 'Invalid staff ID format'}), 400
        
        try:
            staff = Staff.objects.get(id=staff_id)
        except DoesNotExist:
            return jsonify({'error': 'Staff not found'}), 400
        except ValidationError:
            return jsonify({'error': 'Invalid staff ID format'}), 400

        # Get existing appointments for this staff on this date
        existing_appointments = Appointment.objects(
            staff=staff,
            appointment_date=target,
            status__in=['confirmed', 'completed']
        ).order_by('start_time')

        # Define working hours (9 AM to 9 PM)
        work_start = time(9, 0)
        work_end = time(21, 0)

        # Generate all possible slots (every 30 minutes)
        slots = []
        current_time = datetime.combine(target, work_start)
        end_datetime = datetime.combine(target, work_end)

        while current_time < end_datetime:
            slot_time = current_time.time()

            # Check if this slot conflicts with existing appointments
            is_available = True
            slot_time_str = slot_time.strftime('%H:%M:%S')
            for appt in existing_appointments:
                appt_start = datetime.strptime(appt.start_time, '%H:%M:%S').time() if isinstance(appt.start_time, str) else appt.start_time
                appt_end = (datetime.combine(target, appt_start) + timedelta(minutes=service_duration)).time()
                if appt_start <= slot_time < appt_end:
                    is_available = False
                    break

            slots.append({
                'time': slot_time_str,
                'available': is_available
            })

            current_time += timedelta(minutes=30)

        return jsonify({
            'date': target.isoformat(),
            'staff_id': str(staff.id),
            'slots': slots
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@appointment_bp.route('/appointments/stats', methods=['GET'])
@require_auth
def get_appointment_stats(current_user=None):
    """Get appointment statistics"""
    try:
        start_date = request.args.get('start_date')
        end_date = request.args.get('end_date')

        # Get branch for filtering
        branch = get_selected_branch(request, current_user)
        query = Appointment.objects
        if branch:
            query = query.filter(branch=branch)

        if start_date:
            start = datetime.strptime(start_date, '%Y-%m-%d').date()
            query = query.filter(appointment_date__gte=start)
        if end_date:
            end = datetime.strptime(end_date, '%Y-%m-%d').date()
            query = query.filter(appointment_date__lte=end)

        appointments = list(query)

        total = len(appointments)
        completed = len([a for a in appointments if a.status == 'completed'])
        confirmed = len([a for a in appointments if a.status == 'confirmed'])
        cancelled = len([a for a in appointments if a.status == 'cancelled'])
        no_show = len([a for a in appointments if a.status == 'no-show'])

        return jsonify({
            'total_appointments': total,
            'completed': completed,
            'confirmed': confirmed,
            'cancelled': cancelled,
            'no_show': no_show,
            'completion_rate': (completed / total * 100) if total > 0 else 0
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500
