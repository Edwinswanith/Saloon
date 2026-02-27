"""
WhatsApp Business API integration service
Phase 4: Customer Lifecycle + WhatsApp Integration
"""
import requests
import os
import base64
from datetime import datetime
from models import WhatsAppMessage

# WhatsApp Business API configuration - read from environment variables
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"  # Meta WhatsApp Cloud API
WHATSAPP_API_TOKEN = os.environ.get('WHATSAPP_API_TOKEN')
WHATSAPP_PHONE_NUMBER_ID = os.environ.get('WHATSAPP_PHONE_NUMBER_ID')

def send_whatsapp_message(customer, message_text, template=None, image_data=None, image_mime_type=None):
    """
    Send a WhatsApp message to a customer (text or image with caption)
    
    Args:
        customer: Customer document object
        message_text: Message text to send (caption if image is provided)
        template: WhatsAppTemplate document (optional)
        image_data: Base64 encoded image data (optional)
        image_mime_type: MIME type of image, e.g. 'image/jpeg' (optional)
    
    Returns:
        dict: Response with delivery status and message_id
    """
    try:
        # Check if customer has given consent
        if not customer.whatsapp_consent:
            return {
                'success': False,
                'error': 'Customer has not given WhatsApp consent',
                'delivery_status': 'failed'
            }
        
        # Replace {customer_name} placeholder with actual customer name
        customer_name = f"{customer.first_name or ''} {customer.last_name or ''}".strip() or 'Valued Customer'
        message_text = message_text.replace('{customer_name}', customer_name)
        
        # Check if API credentials are configured
        if not WHATSAPP_API_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
            # Dev mode: simulate success
            print(f"[WHATSAPP DEV MODE] Would send to {customer.mobile}: {message_text[:50]}...")
            return {
                'success': True,
                'message_id': f'msg_{datetime.utcnow().timestamp()}',
                'delivery_status': 'sent',
                'note': 'Dev mode: API credentials not configured. Set WHATSAPP_API_TOKEN and WHATSAPP_PHONE_NUMBER_ID environment variables.'
            }
        
        # Format phone number (remove + and spaces)
        phone_number = customer.mobile.replace('+', '').replace(' ', '').replace('-', '')
        
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_TOKEN}',
            'Content-Type': 'application/json'
        }
        
        # Build payload based on whether we have an image
        if image_data and image_mime_type:
            # Send image with caption
            # First, upload image to get media ID (simplified - in production, use proper media upload endpoint)
            # For now, we'll send image as base64 in the message
            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': phone_number,
                'type': 'image',
                'image': {
                    'link': None,  # Would use uploaded media URL in production
                    'caption': message_text[:1024] if message_text else None
                }
            }
            # Note: In production, you'd need to upload the image first via the media API
            # and use the returned media_id. For now, this is a placeholder structure.
        else:
            # Send text message
            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': phone_number,
                'type': 'text',
                'text': {
                    'body': message_text
                }
            }
        
        if template:
            # Use template message format
            payload = {
                'messaging_product': 'whatsapp',
                'recipient_type': 'individual',
                'to': phone_number,
                'type': 'template',
                'template': {
                    'name': template.name,
                    'language': {'code': 'en'},
                    'components': []
                }
            }
        
        response = requests.post(
            f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages",
            headers=headers,
            json=payload,
            timeout=30
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'success': True,
                'message_id': data.get('messages', [{}])[0].get('id'),
                'delivery_status': 'sent'
            }
        else:
            error_text = response.text
            print(f"[WHATSAPP API ERROR] Status {response.status_code}: {error_text}")
            return {
                'success': False,
                'error': error_text,
                'delivery_status': 'failed'
            }
        
    except Exception as e:
        print(f"[WHATSAPP ERROR] {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'delivery_status': 'failed'
        }

def update_message_delivery_status(message_id, status, delivery_timestamp=None):
    """
    Update the delivery status of a WhatsApp message
    
    Args:
        message_id: WhatsApp message ID
        status: Delivery status ('sent', 'delivered', 'failed', 'read')
        delivery_timestamp: When message was delivered (optional)
    
    Returns:
        bool: True if updated successfully
    """
    try:
        message = WhatsAppMessage.objects(message_id=message_id).first()
        if message:
            message.delivery_status = status
            if delivery_timestamp:
                message.delivery_timestamp = delivery_timestamp
            message.save()
            return True
        return False
    except Exception as e:
        print(f"Error updating message status: {e}")
        return False

def check_message_delivery_status(message_id):
    """
    Check the delivery status of a WhatsApp message via API
    
    Args:
        message_id: WhatsApp message ID
    
    Returns:
        dict: Delivery status information
    """
    try:
        # Placeholder: Replace with actual API call
        """
        headers = {
            'Authorization': f'Bearer {WHATSAPP_API_TOKEN}'
        }
        
        response = requests.get(
            f"{WHATSAPP_API_URL}/{message_id}",
            headers=headers
        )
        
        if response.status_code == 200:
            data = response.json()
            return {
                'status': data.get('status'),
                'timestamp': data.get('timestamp')
            }
        """
        
        # Placeholder implementation
        return {
            'status': 'delivered',
            'timestamp': datetime.utcnow().isoformat(),
            'note': 'This is a placeholder. Replace with actual API call.'
        }
    except Exception as e:
        return {
            'status': 'unknown',
            'error': str(e)
        }

