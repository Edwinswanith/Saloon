---
name: Replace Customers with Excel Data
overview: Delete all existing customers from MongoDB and replace them with data from CustomerList.xls, using Mobile Number as the primary unique identifier. The codebase already supports mobile as the primary key, so minimal code changes are needed.
todos:
  - id: create-import-script
    content: Create replace_customers_from_excel.py script with Excel parsing, data validation, backup creation, and customer import functionality
    status: completed
  - id: handle-duplicates
    content: Implement duplicate mobile number detection and handling (skip duplicates, log warnings)
    status: completed
    dependencies:
      - create-import-script
  - id: validate-data
    content: "Add data validation: skip empty mobiles, handle empty names, normalize mobile format"
    status: completed
    dependencies:
      - create-import-script
  - id: test-import
    content: Test script with sample data, verify MongoDB import, check for errors
    status: completed
    dependencies:
      - create-import-script
      - handle-duplicates
      - validate-data
  - id: verify-functionality
    content: After import, verify customer search, bill creation, and application functionality work correctly
    status: completed
    dependencies:
      - test-import
---

# Replace All Customers with Excel Dataset

## Overview

Replace all 609 existing customers with ~24,208 customers from `CustomerList.xls`, using Mobile Number as the unique identifier. The Customer model already uses `mobile` as `required=True, unique=True`, so the application structure is already compatible.

## Current State Analysis

**Customer Model** (`backend/models.py`):

- `mobile = StringField(required=True, unique=True)` - Already primary identifier
- `email = StringField(max_length=100)` - Optional, not used for lookups
- All customer queries use mobile or name, never email

**Data Quality Issues in Excel**:

- Some rows have empty customer names
- Some rows have empty mobile numbers (must skip)
- Duplicate mobile numbers exist (e.g., 9940170965, 8939622319, 7502719527)
- Format: Customer Name (tab) Mobile Number (tab) Membership Type (tab) Membership Number

## Implementation Plan

### 1. Create Customer Import Script

**File**: `backend/replace_customers_from_excel.py`

**Features**:

- Parse Excel/TSV file (tab-separated format)
- Validate and clean data:
                                - Skip rows with empty mobile numbers
                                - Handle empty customer names (default to "Customer")
                                - Track and skip duplicate mobile numbers (keep first occurrence)
                                - Normalize mobile numbers (remove spaces, validate format)
- Create backup of existing customers before deletion
- Delete all existing customers
- Import new customers with:
                                - Mobile as unique identifier
                                - Split customer name into first_name/last_name
                                - Assign all to default branch (get first active branch or create "T. Nagar")
                                - Set default values: source='Walk-in', total_spent=0, total_visits=0
                                - Store membership info (has_membership flag, membership_number) - can be stored in a note field or tracked separately

**Data Handling**:

- Membership Type: "yes" → has_membership=True, "no" → has_membership=False
- Membership Number: Store for future use (could add membership_number field or use notes)
- Handle edge cases: empty names, invalid mobiles, duplicates

### 2. Handle Dependencies

**Broken References** (will occur after deletion):

- 1,352+ bills will have broken customer references
- 821+ appointments will have broken customer references  
- 21+ memberships will have broken customer references
- Prepaid packages, feedbacks, leads, WhatsApp messages

**Options**:

- Option A: Delete all dependent records (bills, appointments, memberships)
- Option B: Leave broken references (they'll show as null/empty in UI)
- Option C: Create a mapping script to update references (if mobile numbers match)

**Recommendation**: Document the impact and let user decide. The script will warn about this.

### 3. No Code Changes Required

The application already:

- Uses mobile as primary identifier in Customer model
- Searches customers by mobile (not email) in `customer_routes.py`
- Frontend handles optional email fields gracefully
- All customer lookups use mobile or ObjectId, never email

**Verification Points**:

- `backend/routes/customer_routes.py`: Search uses `Q(mobile__icontains=query)`
- `backend/routes/bill_routes.py`: Customers identified by ID, not email
- Frontend components: Email is optional, mobile is primary

### 4. Script Execution Flow

```
1. Connect to MongoDB
2. Parse Excel file (24,208 rows)
3. Validate data:
   - Count total rows
   - Count rows with valid mobile numbers
   - Identify duplicate mobile numbers
   - Show sample data (first 5 customers)
4. Create backup of existing 609 customers
5. Get default branch (first active branch or create one)
6. Ask for final confirmation
7. Delete all existing customers
8. Import new customers:
   - Track seen mobile numbers to skip duplicates
   - Create Customer objects with mobile as unique key
   - Assign to default branch
   - Set default values
9. Report summary:
   - Total imported
   - Skipped (duplicates, invalid)
   - Errors encountered
```

### 5. Error Handling

- Skip rows with empty/invalid mobile numbers
- Skip duplicate mobile numbers (log which ones)
- Handle MongoDB connection errors
- Validate mobile number format (10 digits, optional country code)
- Handle branch assignment failures

### 6. Membership Data Storage

Since the Customer model doesn't have membership_number field, options:

- **Option A**: Add `membership_number` field to Customer model (requires model change)
- **Option B**: Store in a separate collection mapping mobile → membership_number
- **Option C**: Store as note/comment field (if exists)
- **Option D**: Store membership info separately for future use

**Recommendation**: For now, just track `has_membership` flag. Can add membership_number field later if needed.

## Files to Create/Modify

1. **Create**: `backend/replace_customers_from_excel.py` - Main import script
2. **Optional**: Add `membership_number` field to Customer model if membership tracking is needed

## Execution Steps

1. Review and understand the data loss implications
2. Run script: `python backend/replace_customers_from_excel.py --file customer_list/CustomerList.xls --confirm`
3. Verify import success
4. Test application functionality (customer search, bill creation)
5. Handle broken references in bills/appointments (delete or update)

## Risks and Warnings

- **Data Loss**: All customer history (total_spent, total_visits) will be lost
- **Broken References**: Bills, appointments, memberships will have null customer references
- **No Rollback**: Deletion is permanent (backup created but manual restore needed)
- **Duplicate Handling**: Duplicate mobile numbers in Excel will be skipped (first occurrence kept)

## Success Criteria

- All valid customers from Excel imported successfully
- Mobile numbers are unique in database
- Customer search by mobile works correctly
- Bills can be created with new customers
- Application continues to function without errors