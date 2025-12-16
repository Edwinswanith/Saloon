# MongoDB Migration Guide

This document outlines the key changes when migrating from SQLAlchemy to MongoDB (MongoEngine).

## Key Differences

### 1. Queries
- SQLAlchemy: `Model.query.filter_by(...).all()`
- MongoDB: `Model.objects.filter(...)`

### 2. Get by ID
- SQLAlchemy: `Model.query.get(id)` or `Model.query.get_or_404(id)`
- MongoDB: `Model.objects.get(id=id)` (raises DoesNotExist exception)

### 3. Save/Update
- SQLAlchemy: `db.session.add(obj); db.session.commit()`
- MongoDB: `obj.save()` (no session needed)

### 4. Delete
- SQLAlchemy: `db.session.delete(obj); db.session.commit()`
- MongoDB: `obj.delete()`

### 5. Relationships
- SQLAlchemy: Automatic lazy loading with `backref`
- MongoDB: Use `obj.reload()` to fetch referenced documents, or `ReferenceField` automatically resolves

### 6. Pagination
- SQLAlchemy: `query.paginate(page=1, per_page=10)`
- MongoDB: `query.skip((page-1)*per_page).limit(per_page)`

### 7. Filters
- SQLAlchemy: `Model.field.like('%text%')`, `Model.field >= value`
- MongoDB: `Model.objects.filter(field__icontains='text')`, `Model.objects.filter(field__gte=value)`

### 8. Aggregations
- SQLAlchemy: `db.session.query(func.sum(...))`
- MongoDB: Use aggregation pipeline or calculate in Python

### 9. Embedded Documents
- SQLAlchemy: Separate table with foreign key
- MongoDB: Embedded documents in parent document (e.g., BillItemEmbedded in Bill)

### 10. Transactions
- SQLAlchemy: `db.session.commit()` / `db.session.rollback()`
- MongoDB: Use MongoDB transactions (4.0+) or handle errors individually

## Common Patterns

### Pattern 1: Basic Query
```python
# SQLAlchemy
customers = Customer.query.filter_by(status='active').all()

# MongoDB
customers = Customer.objects.filter(status='active')
```

### Pattern 2: Get Single Document
```python
# SQLAlchemy
customer = Customer.query.get(customer_id)

# MongoDB
try:
    customer = Customer.objects.get(id=customer_id)
except Customer.DoesNotExist:
    return jsonify({'error': 'Not found'}), 404
```

### Pattern 3: Update Document
```python
# SQLAlchemy
customer.name = 'New Name'
db.session.commit()

# MongoDB
customer.name = 'New Name'
customer.save()
```

### Pattern 4: Reference Field Loading
```python
# SQLAlchemy - automatic
bill.customer.first_name

# MongoDB - may need reload
bill.customer.reload()  # If needed
bill.customer.first_name
```

### Pattern 5: Date Filtering
```python
# SQLAlchemy
query.filter(Bill.bill_date >= start_date)

# MongoDB
query.filter(bill_date__gte=start_date)
```

### Pattern 6: OR Conditions
```python
# SQLAlchemy
from sqlalchemy import or_
query.filter(or_(Model.field1 == value1, Model.field2 == value2))

# MongoDB
from mongoengine import Q
query.filter(Q(field1=value1) | Q(field2=value2))
```

## Status
- ✅ Models converted
- ✅ app.py updated
- ✅ customer_routes.py converted
- ✅ bill_routes.py converted
- ⏳ Remaining routes need conversion

