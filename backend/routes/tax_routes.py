from flask import Blueprint, request, jsonify
from models import db, TaxSettings, TaxSlab
from datetime import datetime

tax_bp = Blueprint('tax', __name__)

# Tax Settings Routes
@tax_bp.route('/settings', methods=['GET'])
def get_tax_settings():
    """Get tax settings"""
    try:
        settings = TaxSettings.get_settings()
        return jsonify({
            'gstNumber': settings.gst_number or '',
            'servicePricingType': settings.service_pricing_type,
            'productPricingType': settings.product_pricing_type,
            'prepaidPricingType': settings.prepaid_pricing_type
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tax_bp.route('/settings', methods=['PUT'])
def update_tax_settings():
    """Update tax settings"""
    try:
        settings = TaxSettings.get_settings()
        data = request.json
        
        if 'gstNumber' in data:
            settings.gst_number = data['gstNumber'] or ''
        if 'servicePricingType' in data:
            pricing_type = data['servicePricingType'].lower()
            if pricing_type not in ['inclusive', 'exclusive']:
                return jsonify({'error': 'Pricing type must be "inclusive" or "exclusive"'}), 400
            settings.service_pricing_type = pricing_type
        if 'productPricingType' in data:
            pricing_type = data['productPricingType'].lower()
            if pricing_type not in ['inclusive', 'exclusive']:
                return jsonify({'error': 'Pricing type must be "inclusive" or "exclusive"'}), 400
            settings.product_pricing_type = pricing_type
        if 'prepaidPricingType' in data:
            pricing_type = data['prepaidPricingType'].lower()
            if pricing_type not in ['inclusive', 'exclusive']:
                return jsonify({'error': 'Pricing type must be "inclusive" or "exclusive"'}), 400
            settings.prepaid_pricing_type = pricing_type
        
        settings.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'message': 'Tax settings updated successfully',
            'gstNumber': settings.gst_number,
            'servicePricingType': settings.service_pricing_type,
            'productPricingType': settings.product_pricing_type,
            'prepaidPricingType': settings.prepaid_pricing_type
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

# Tax Slab Routes
@tax_bp.route('/slabs', methods=['GET'])
def get_tax_slabs():
    """Get all tax slabs"""
    try:
        status = request.args.get('status', 'all')
        
        query = TaxSlab.query
        
        if status != 'all':
            query = query.filter_by(status=status)
        
        slabs = query.order_by(TaxSlab.created_at.desc()).all()
        
        return jsonify({
            'slabs': [{
                'id': s.id,
                'name': s.name,
                'rate': s.rate,
                'applyToServices': s.apply_to_services,
                'applyToProducts': s.apply_to_products,
                'applyToPrepaid': s.apply_to_prepaid,
                'status': s.status
            } for s in slabs]
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tax_bp.route('/slabs/<int:slab_id>', methods=['GET'])
def get_tax_slab(slab_id):
    """Get single tax slab"""
    try:
        slab = TaxSlab.query.get_or_404(slab_id)
        return jsonify({
            'id': slab.id,
            'name': slab.name,
            'rate': slab.rate,
            'applyToServices': slab.apply_to_services,
            'applyToProducts': slab.apply_to_products,
            'applyToPrepaid': slab.apply_to_prepaid,
            'status': slab.status
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@tax_bp.route('/slabs', methods=['POST'])
def create_tax_slab():
    """Create new tax slab"""
    try:
        data = request.json
        
        # Validate required fields
        if not data.get('name'):
            return jsonify({'error': 'Tax name is required'}), 400
        if data.get('rate') is None:
            return jsonify({'error': 'Tax rate is required'}), 400
        
        rate = float(data['rate'])
        if rate < 0 or rate > 100:
            return jsonify({'error': 'Tax rate must be between 0 and 100'}), 400
        
        slab = TaxSlab(
            name=data.get('name'),
            rate=rate,
            apply_to_services=bool(data.get('applyToServices', False)),
            apply_to_products=bool(data.get('applyToProducts', False)),
            apply_to_prepaid=bool(data.get('applyToPrepaid', False)),
            status=data.get('status', 'active')
        )
        
        db.session.add(slab)
        db.session.commit()
        
        return jsonify({
            'id': slab.id,
            'message': 'Tax slab created successfully'
        }), 201
    except ValueError as e:
        return jsonify({'error': 'Invalid rate value'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tax_bp.route('/slabs/<int:slab_id>', methods=['PUT'])
def update_tax_slab(slab_id):
    """Update tax slab"""
    try:
        slab = TaxSlab.query.get_or_404(slab_id)
        data = request.json
        
        if 'name' in data:
            slab.name = data['name']
        if 'rate' in data:
            rate = float(data['rate'])
            if rate < 0 or rate > 100:
                return jsonify({'error': 'Tax rate must be between 0 and 100'}), 400
            slab.rate = rate
        if 'applyToServices' in data:
            slab.apply_to_services = bool(data['applyToServices'])
        if 'applyToProducts' in data:
            slab.apply_to_products = bool(data['applyToProducts'])
        if 'applyToPrepaid' in data:
            slab.apply_to_prepaid = bool(data['applyToPrepaid'])
        if 'status' in data:
            slab.status = data['status']
        
        slab.updated_at = datetime.utcnow()
        db.session.commit()
        
        return jsonify({'message': 'Tax slab updated successfully'})
    except ValueError as e:
        return jsonify({'error': 'Invalid rate value'}), 400
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@tax_bp.route('/slabs/<int:slab_id>', methods=['DELETE'])
def delete_tax_slab(slab_id):
    """Delete tax slab (soft delete)"""
    try:
        slab = TaxSlab.query.get_or_404(slab_id)
        slab.status = 'inactive'
        slab.updated_at = datetime.utcnow()
        db.session.commit()
        return jsonify({'message': 'Tax slab deleted successfully'})
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

