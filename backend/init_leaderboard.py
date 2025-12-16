"""
Script to initialize Staff Leaderboard table in the database
Run this after adding the StaffLeaderboard model to ensure the table is created
"""

from app import app, db
from models import StaffLeaderboard

def init_leaderboard_table():
    """Create the staff_leaderboard table if it doesn't exist"""
    with app.app_context():
        try:
            # Create all tables (this will create staff_leaderboard if it doesn't exist)
            db.create_all()
            print("Staff Leaderboard table created/verified successfully!")
            
            # Check if table exists
            from sqlalchemy import inspect
            inspector = inspect(db.engine)
            tables = inspector.get_table_names()
            
            if 'staff_leaderboard' in tables:
                print("staff_leaderboard table exists in database")
                
                # Show table structure
                columns = inspector.get_columns('staff_leaderboard')
                print("\nTable structure:")
                for col in columns:
                    print(f"  - {col['name']}: {col['type']}")
            else:
                print("ERROR: staff_leaderboard table not found")
                
        except Exception as e:
            print(f"Error initializing leaderboard table: {str(e)}")

if __name__ == '__main__':
    init_leaderboard_table()

