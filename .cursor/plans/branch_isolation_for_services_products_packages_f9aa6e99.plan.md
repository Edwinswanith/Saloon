---
name: Branch Isolation for Services Products Packages
overview: Ensure that services, products, and packages are branch-specific. Add branch fields to models, update API routes to filter and assign branches, and ensure frontend sends branch information in requests.
todos:
  - id: add-branch-to-models
    content: Add branch ReferenceField to Service, Product, and Package models in backend/models.py
    status: pending
  - id: update-service-routes
    content: Update service_routes.py to filter by branch in GET routes and assign branch in POST/PUT routes
    status: pending
    dependencies:
      - add-branch-to-models
  - id: update-product-routes
    content: Update product_routes.py to filter by branch in GET routes and assign branch in POST/PUT routes
    status: pending
    dependencies:
      - add-branch-to-models
  - id: update-package-routes
    content: Update package_routes.py to filter by branch in GET routes and assign branch in POST/PUT routes
    status: pending
    dependencies:
      - add-branch-to-models
  - id: verify-frontend-branch-context
    content: Verify frontend components (Service.jsx, Product.jsx, Package.jsx) properly send branch context or rely on backend branch detection
    status: pending
    dependencies:
      - update-service-routes
      - update-product-routes
      - update-package-routes
  - id: test-branch-isolation
    content: Test that creating/updating services/products/packages in one branch does not affect other branches
    status: pending
    dependencies:
      - verify-frontend-branch-context
---

# Branch Isolation for Services, Products, and Packages

## Problem Statement

Currently, services, products, and packages are global/shared across all branches. When a user adds a service, product, or package, it affects all branches instead of just the selected branch. Each branch must have its own unique services, products, and packages.

## Root Cause Analysis

### Current Issues:

1. **Models lack branch fields**: `Service`, `Product`, and `Package` models don't have `branch` ReferenceField
2. **GET routes don't filter by branch**: All routes return all items regardless of branch
3. **POST routes don't assign branch**: When creating items, branch is not set
4. **PUT routes don't maintain branch**: Updates don't ensure branch isolation
5. **Frontend doesn't send branch**: Frontend forms don't include branch_id in API requests

## Solution Overview

### 1. Update Models (`backend/models.py`)

- Add `branch = ReferenceField('Branch')` to `Service` model
- Add `branch = ReferenceField('Branch')` to `Product` model  
- Add `branch = ReferenceField('Branch')` to `Package` model
- Make branch required for all three models (or handle None for backward compatibility)

### 2. Update API Routes - Services (`backend/routes/service_routes.py`)

- **GET `/api/services`**: Filter by branch using `get_selected_branch()` and `filter_by_branch()`
- **POST `/api/services`**: Assign branch from `get_selected_branch()` when creating
- **PUT `/api/services/<id>`**: Ensure branch is maintained (don't allow changing branch)
- **GET `/api/services/<id>`**: Verify branch access

### 3. Update API Routes - Products (`backend/routes/product_routes.py`)

- **GET `/api/products`**: Filter by branch using `get_selected_branch()` and `filter_by_branch()`
- **POST `/api/products`**: Assign branch from `get_selected_branch()` when creating
- **PUT `/api/products/<id>`**: Ensure branch is maintained
- **GET `/api/products/<id>`**: Verify branch access

### 4. Update API Routes - Packages (`backend/routes/package_routes.py`)

- **GET `/api/packages`**: Filter by branch using `get_selected_branch()` and `filter_by_branch()`
- **POST `/api/packages`**: Assign branch from `get_selected_branch()` when creating
- **PUT `/api/packages/<id>`**: Ensure branch is maintained
- **GET `/api/packages/<id>`**: Verify branch access

### 5. Update Frontend Components

- **Service.jsx**: Ensure API calls include `X-Branch-Id` header (if needed) or rely on backend branch detection
- **Product.jsx**: Ensure API calls include branch context
- **Package.jsx**: Ensure API calls include branch context
- **QuickSale.jsx**: Verify fetched services/products/packages are branch-filtered

### 6. Data Migration Consideration

- Existing services/products/packages without branch will need branch assignment
- Consider creating a migration script to assign existing items to a default branch
- Or handle None branch gracefully during transition period

## Implementation Details

### Branch Filtering Pattern

Use the existing `branch_filter.py` utilities:

```python
from utils.branch_filter import get_selected_branch, filter_by_branch

# In GET routes:
branch = get_selected_branch(request, current_user)
query = Service.objects(status='active')
if branch:
    query = filter_by_branch(query, branch)
```

### Branch Assignment Pattern

```python
# In POST routes:
branch = get_selected_branch(request, current_user)
if not branch:
    return jsonify({'error': 'Branch is required'}), 400

service = Service(
    name=data.get('name'),
    branch=branch,  # Assign branch
    # ... other fields
)
```

## Files to Modify

### Backend:

1. `backend/models.py` - Add branch fields to Service, Product, Package models
2. `backend/routes/service_routes.py` - Add branch filtering and assignment
3. `backend/routes/product_routes.py` - Add branch filtering and assignment
4. `backend/routes/package_routes.py` - Add branch filtering and assignment

### Frontend:

1. `frontend/src/components/Service.jsx` - Verify branch context (may not need changes if backend handles it)
2. `frontend/src/components/Product.jsx` - Verify branch context
3. `frontend/src/components/Package.jsx` - Verify branch context
4. `frontend/src/components/QuickSale.jsx` - Verify branch filtering works

## Testing Checklist

- [ ] Create service in Branch A, verify it only appears in Branch A
- [ ] Create product in Branch B, verify it only appears in Branch B
- [ ] Create package in Branch C, verify it only appears in Branch C
- [ ] Switch branches and verify items are isolated
- [ ] Update service/product/package and verify branch is maintained
- [ ] Verify Owner can see items from all branches (if needed)
- [ ] Verify Staff/Manager only see items from their branch

## Migration Strategy

1. Add branch field to models (make it optional initially for backward compatibility)
2. Update all routes to handle branch
3. Create migration script to assign existing items to default branch
4. Make branch required after migration

## Success Criteria

- Each branch has its own isolated services, products, and packages
- Creating items in one branch doesn't affect other branches
- GET requests return only items for the selected branch
- POST requests assign items to the correct branch
- PUT requests maintain branch isolation
- Staff/Manager users only see items from their assigned branch
- Owner users can see items from all branches (or filtered by selected branch)