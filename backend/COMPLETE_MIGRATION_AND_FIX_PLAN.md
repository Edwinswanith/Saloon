# Complete MongoDB Migration & Route Conversion Plan

## Overview
Execute a complete solution that includes:
1. Converting all remaining SQLAlchemy routes to MongoEngine
2. Fixing migration script issues
3. Clearing MongoDB and performing fresh migration
4. Verifying all 2,097 records migrated successfully

## Current State

### Routes Status
**Converted to MongoEngine** (Working ✓):
- service_routes.py
- staff_routes.py  
- appointment_routes.py
- cash_routes.py
- dashboard_routes.py
- customer_routes.py
- bill_routes.py

**Still Using SQLAlchemy** (Causing 500 errors ✗):
1. product_routes.py - ✗ 500 error
2. package_routes.py - ✗ 500 error (partially converted)
3. prepaid_routes.py - ✗ 500 error  
4. membership_plan_routes.py - ✗ 500 error
5. expense_routes.py
6. asset_routes.py
7. feedback_routes.py
8. lead_routes.py
9. attendance_routes.py
10. loyalty_program_routes.py
11. referral_program_routes.py
12. tax_routes.py
13. manager_routes.py
14. inventory_routes.py
15. report_routes.py
16. client_value_routes.py

### Migration Status
**SQLite Data** (D:\Salon\backend\instance\salon.db):
- 30 tables, 2,097 total records

**MongoDB Data** (Saloon database):
- **Missing**: 129 appointments, 4 packages (actually in migration order), 811 staff_attendance
- **Extra**: Duplicate data from previous migrations
- **Strategy**: Clear all and re-migrate fresh

## Implementation Plan

### Phase 1: Convert Critical Routes (Fix 500 Errors)
Convert the 4 routes causing immediate errors:

#### 1.1 product_routes.py
Changes:
- `from models import db, Product` → `from models import Product, ProductCategory`
- `Product.query` → `Product.objects`
- `ProductCategory.query` → `ProductCategory.objects`
- `db.session.add()` → `.save()`
- `db.session.commit()` → remove
- `db.session.delete()` → `.delete()`
- `get_or_404()` → `objects.get(id=...)` with DoesNotExist
- Add ObjectId validation for IDs
- `int:id` → `<id>` in routes
- Add `from bson import ObjectId`
- Add `from mongoengine.errors import DoesNotExist, ValidationError`

#### 1.2 package_routes.py  
Changes:
- Already partially converted (uses `.objects`)
- Fix ID serialization: `p.id` → `str(p.id)`
- Fix services field (currently JSON, might need ListField)
- Add ObjectId validation
- Fix route parameters from `<int:id>` → `<id>`

#### 1.3 prepaid_routes.py
Changes:
- Same pattern as product_routes.py
- Convert PrepaidPackage and PrepaidGroup models
- Handle customer references properly
- Add ObjectId validation

#### 1.4 membership_plan_routes.py
Changes:
- Convert MembershipPlan and Membership models  
- Same SQLAlchemy → MongoEngine pattern
- Add ObjectId validation

### Phase 2: Fix Migration Script

#### 2.1 Current Issues Analysis
The migration script has `packages` in migration order (line 395), so that's not the issue.

**Real Issues**:
1. **appointments** (0/129 migrated): 
   - Issue: Customers/staff not found in id_mappings
   - Needs better error handling to identify root cause

2. **staff_attendance** (10/821 migrated):
   - Issue: Most records skipped due to invalid staff_id
   - Needs investigation of why staff_id not in id_mappings

3. **packages** (0/4 migrated):
   - In migration order but not showing up
   - Possible model issue or validation error

#### 2.2 Migration Script Fixes

File: `migrate_sqlite_to_mongodb.py`

1. Add debug logging for ID mappings:
```python
# After each independent table migration
print(f"  DEBUG: {table_name} ID mappings: {len(id_mappings[table_name])} entries")
```

2. Improve error handling for appointments:
```python
# Better logging when customer/staff not found
if customer_id not in id_mappings['customers']:
    available_ids = list(id_mappings['customers'].keys())[:5]
    print(f"  Warning: customer_id {customer_id} not in mappings. Available: {available_ids}...")
```

3. Add validation error catching:
```python
try:
    doc.save()
except ValidationError as e:
    print(f"  ValidationError for {table_name} {sqlite_id}: {e}")
    error_count += 1
    continue
```

### Phase 3: Clear MongoDB Collections

Create script: `clear_mongodb.py`
```python
from app import app
import mongoengine

with app.app_context():
    db = mongoengine.connection.get_db()
    collections = db.list_collection_names()
    
    print("Clearing MongoDB collections...")
    for collection in collections:
        result = db[collection].delete_many({})
        print(f"  - {collection}: deleted {result.deleted_count} documents")
    
    print("MongoDB cleared successfully!")
```

### Phase 4: Execute Fresh Migration

Steps:
1. Run: `python clear_mongodb.py`
2. Run: `python migrate_sqlite_to_mongodb.py`
3. Monitor output for errors
4. Run: `python compare_migration.py` to verify

Expected output:
```
customers: 26 → 26 ✓
staffs: 11 → 11 ✓
services: 17 → 17 ✓
packages: 4 → 4 ✓
appointments: 129 → 129 ✓
staff_attendance: 821 → 821 ✓
... (all tables match)
Total: 2,097 records migrated
```

### Phase 5: Convert Remaining Routes (Optional)

Convert the other 12 route files using same pattern:
- expense_routes.py
- asset_routes.py
- feedback_routes.py
- lead_routes.py
- attendance_routes.py
- loyalty_program_routes.py
- referral_program_routes.py
- tax_routes.py
- manager_routes.py
- inventory_routes.py
- report_routes.py
- client_value_routes.py

### Phase 6: Verification & Testing

1. **Backend verification**:
   - Run `python compare_migration.py`
   - All counts should match

2. **API testing**:
   - Test all critical endpoints return 200
   - GET /api/products/ 
   - GET /api/packages/
   - GET /api/prepaid/packages
   - GET /api/membership-plans/

3. **Frontend testing**:
   - Clear browser cache/localStorage
   - Refresh page
   - Verify dropdowns show ObjectId strings (not integers)
   - Test creating appointment with new IDs

## Conversion Pattern Reference

### SQLAlchemy → MongoEngine Cheat Sheet

```python
# Imports
- from models import db, Model  
+ from models import Model
+ from mongoengine.errors import DoesNotExist, ValidationError
+ from bson import ObjectId

# Queries
- Model.query.all()
+ Model.objects

- Model.query.filter_by(status='active')
+ Model.objects(status='active')

- Model.query.filter(Model.name.like('%search%'))
+ Model.objects(name__icontains='search')

- Model.query.order_by(Model.name.asc())
+ Model.objects.order_by('name')

- Model.query.get_or_404(id)
+ try: Model.objects.get(id=id)
  except DoesNotExist: return 404

# CRUD Operations
- db.session.add(model)
- db.session.commit()
+ model.save()

- db.session.delete(model)
+ model.delete()

- db.session.rollback()  # Not needed in MongoDB

# Route Parameters
- @bp.route('/<int:id>')
+ @bp.route('/<id>')  # ID is string ObjectId

# ID Handling
- return {'id': model.id}
+ return {'id': str(model.id)}  # Convert ObjectId to string

# Validation
+ if not ObjectId.is_valid(id):
+     return {'error': 'Invalid ID format'}, 400

# Foreign Keys
- model.customer_id = customer_id
+ model.customer = Customer.objects.get(id=customer_id)
```

## Success Criteria

✓ All 16 SQLAlchemy route files converted to MongoEngine
✓ No 500 errors from any API endpoint  
✓ MongoDB has exactly 2,097 records matching SQLite
✓ All appointments (129) migrated
✓ All staff_attendance (821) migrated  
✓ All packages (4) migrated
✓ Frontend works with new ObjectId format
✓ No duplicate data in MongoDB

## Rollback Plan

If anything fails:
1. SQLite database is untouched (source of truth)
2. Can clear MongoDB and retry migration
3. Can revert route files from git if needed
4. No permanent damage possible

## Execution Order

1. **Convert 4 critical routes** (30 mins)
   - Fixes immediate 500 errors
   - App partially functional

2. **Fix migration script** (15 mins)
   - Better logging and error handling

3. **Clear & migrate** (5 mins)
   - Fresh MongoDB with all data

4. **Verify & test** (15 mins)
   - Confirm everything works

5. **Convert remaining routes** (optional, 1-2 hours)
   - Complete the conversion

**Total estimated time**: 1-2 hours for core functionality

