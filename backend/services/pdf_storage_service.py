"""
PDF Storage Service using MongoDB GridFS
Handles saving, retrieving, and deleting invoice PDFs from GridFS
"""
from gridfs import GridFS
from pymongo import MongoClient
from bson import ObjectId
from datetime import datetime
import os
import logging

logger = logging.getLogger(__name__)

# Get MongoDB connection from environment
MONGODB_URI = os.environ.get('MONGODB_URI', 'mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon')
MONGODB_DB = os.environ.get('MONGODB_DB', 'Saloon_prod')

# Global GridFS instance (will be initialized on first use)
_gridfs_instance = None
_db_instance = None


def get_gridfs():
    """Get or create GridFS instance"""
    global _gridfs_instance, _db_instance
    
    if _gridfs_instance is None:
        try:
            # Parse database name from URI or use default
            client = MongoClient(MONGODB_URI)
            _db_instance = client[MONGODB_DB]
            _gridfs_instance = GridFS(_db_instance, collection='invoice_pdfs')
            logger.info(f"GridFS initialized for database: {MONGODB_DB}")
        except Exception as e:
            logger.error(f"Error initializing GridFS: {str(e)}")
            raise
    
    return _gridfs_instance


def save_pdf_to_gridfs(pdf_bytes, bill_id, invoice_number, bill_number, bill_date=None):
    """
    Save PDF to GridFS
    
    Args:
        pdf_bytes: PDF file as bytes
        bill_id: Bill document ID (string or ObjectId)
        invoice_number: Invoice number for reference
        bill_number: Bill number for filename
        bill_date: Bill date (optional, for metadata)
    
    Returns:
        ObjectId: GridFS file ID
    """
    try:
        gridfs = get_gridfs()
        
        # Convert bill_id to ObjectId if it's a string
        if isinstance(bill_id, str):
            bill_id = ObjectId(bill_id)
        
        # Create filename
        filename = f"invoice_{bill_number}_{str(bill_id)}.pdf"
        
        # Prepare metadata
        metadata = {
            'bill_id': str(bill_id),
            'invoice_number': invoice_number,
            'bill_number': bill_number,
            'generated_at': datetime.utcnow().isoformat(),
            'bill_date': bill_date.isoformat() if bill_date else None
        }
        
        # Save to GridFS
        file_id = gridfs.put(
            pdf_bytes,
            filename=filename,
            content_type='application/pdf',
            metadata=metadata
        )
        
        logger.info(f"PDF saved to GridFS: file_id={file_id}, bill_id={bill_id}, filename={filename}")
        return file_id
        
    except Exception as e:
        logger.error(f"Error saving PDF to GridFS: {str(e)}")
        raise


def get_pdf_from_gridfs(file_id):
    """
    Retrieve PDF from GridFS
    
    Args:
        file_id: GridFS file ID (string or ObjectId)
    
    Returns:
        bytes: PDF file as bytes, or None if not found
    """
    try:
        gridfs = get_gridfs()
        
        # Convert file_id to ObjectId if it's a string
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)
        
        # Check if file exists
        if not gridfs.exists(file_id):
            logger.warning(f"PDF not found in GridFS: file_id={file_id}")
            return None
        
        # Retrieve file
        grid_file = gridfs.get(file_id)
        pdf_bytes = grid_file.read()
        
        logger.info(f"PDF retrieved from GridFS: file_id={file_id}, size={len(pdf_bytes)} bytes")
        return pdf_bytes
        
    except Exception as e:
        logger.error(f"Error retrieving PDF from GridFS: {str(e)}")
        return None


def delete_pdf_from_gridfs(file_id):
    """
    Delete PDF from GridFS
    
    Args:
        file_id: GridFS file ID (string or ObjectId)
    
    Returns:
        bool: True if deleted, False if not found
    """
    try:
        gridfs = get_gridfs()
        
        # Convert file_id to ObjectId if it's a string
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)
        
        # Check if file exists
        if not gridfs.exists(file_id):
            logger.warning(f"PDF not found in GridFS for deletion: file_id={file_id}")
            return False
        
        # Delete file
        gridfs.delete(file_id)
        
        logger.info(f"PDF deleted from GridFS: file_id={file_id}")
        return True
        
    except Exception as e:
        logger.error(f"Error deleting PDF from GridFS: {str(e)}")
        return False


def get_pdf_metadata(file_id):
    """
    Get PDF metadata from GridFS
    
    Args:
        file_id: GridFS file ID (string or ObjectId)
    
    Returns:
        dict: Metadata dictionary, or None if not found
    """
    try:
        gridfs = get_gridfs()
        
        # Convert file_id to ObjectId if it's a string
        if isinstance(file_id, str):
            file_id = ObjectId(file_id)
        
        # Check if file exists
        if not gridfs.exists(file_id):
            return None
        
        # Get file info
        grid_file = gridfs.get(file_id)
        return {
            'filename': grid_file.filename,
            'length': grid_file.length,
            'upload_date': grid_file.upload_date,
            'content_type': grid_file.content_type,
            'metadata': grid_file.metadata or {}
        }
        
    except Exception as e:
        logger.error(f"Error getting PDF metadata from GridFS: {str(e)}")
        return None

