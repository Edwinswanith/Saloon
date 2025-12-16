"""
Script to add the MembershipPlan table to existing database
Run this once to add the new table without losing existing data
"""
from app import app
from models import db, MembershipPlan
from sqlalchemy import inspect, text

def add_membership_plan_table():
    with app.app_context():
        inspector = inspect(db.engine)
        tables = inspector.get_table_names()
        
        if 'membership_plans' not in tables:
            print("Creating membership_plans table...")
            MembershipPlan.__table__.create(db.engine)
            print("✓ membership_plans table created successfully!")
        else:
            print("✓ membership_plans table already exists")
        
        # Also add plan_id column to memberships table if it doesn't exist
        try:
            # Check if plan_id column exists in memberships table
            columns = [col['name'] for col in inspector.get_columns('memberships')]
            if 'plan_id' not in columns:
                print("Adding plan_id column to memberships table...")
                with db.engine.connect() as conn:
                    conn.execute(text('ALTER TABLE memberships ADD COLUMN plan_id INTEGER'))
                    conn.execute(text('CREATE INDEX IF NOT EXISTS ix_memberships_plan_id ON memberships(plan_id)'))
                    conn.commit()
                print("✓ plan_id column added successfully!")
            else:
                print("✓ plan_id column already exists in memberships table")
        except Exception as e:
            print(f"Note: {e}")
            print("This is okay if the column already exists or table structure is different")

if __name__ == '__main__':
    add_membership_plan_table()

