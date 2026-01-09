---
name: Password-Based Authentication Implementation
overview: Implement password-based authentication for all users (staff, managers, owners). Add password fields to login UI, enable password validation in backend, and create passwords for all existing users across all branches with secure bcrypt hashing.
todos:
  - id: add-password-field-frontend
    content: Add password input field to Login.jsx for staff login and uncomment password fields for manager and owner login, make all password fields required
    status: pending
  - id: enable-password-validation-backend
    content: Enable password validation in auth_routes.py for all user types (staff, manager, owner), remove password bypass logic, and require password for all login attempts
    status: pending
  - id: create-password-script
    content: Create set_all_user_passwords.py script to generate and set passwords for all staff, managers, and owners across all branches using bcrypt hashing
    status: pending
  - id: run-password-script
    content: Execute the password generation script to set passwords for all existing users in the database
    status: pending
    dependencies:
      - create-password-script
  - id: test-password-login
    content: Test login functionality for staff, managers, and owners with their new passwords to verify authentication works correctly
    status: pending
    dependencies:
      - add-password-field-frontend
      - enable-password-validation-backend
      - run-password-script
---

# Password-Based Authentication Implementation

## Current State Analysis

### Frontend (`frontend/src/components/Login.jsx`)

- Password state variable exists but is not used
- Password field is **commented out** for managers and owners
- **No password field** for staff login
- Password is sent in login request but validation is skipped

### Backend (`backend/routes/auth_routes.py`)

- Staff login: Checks for password_hash, validates if exists, otherwise allows role selection
- Manager/Owner login: Password validation is **disabled** (commented out)
- Password verification utilities exist (`hash_password`, `verify_password`)

### Models

- All models have `password_hash` field:
- `Staff.password_hash` (optional)
- `Manager.password_hash`
- `Owner.password_hash`

### Existing Scripts

- `set_manager_passwords.py` - Sets passwords for managers only
- No scripts for staff or owners

### Database State

- 10 staff members (across 7 branches)
- 7 managers (across branches)
- 1 owner
- 7 branches total

## Implementation Plan

### 1. Update Frontend Login Component (`frontend/src/components/Login.jsx`)

**Changes Required:**

- **Add password field for Staff login** (currently missing)
- **Uncomment and enable password field for Manager login** (lines 475-492)
- **Uncomment and enable password field for Owner login** (lines 514-531)
- Make password field **required** for all user types
- Update form validation to require password
- Remove comment about password being disabled

**Implementation:**

- Add password input field after staff selection dropdown
- Uncomment password fields for manager and owner
- Add `required` attribute to all password inputs
- Update validation logic to check password is provided

### 2. Update Backend Authentication Routes (`backend/routes/auth_routes.py`)

**Changes Required:**

- **Enable password validation for Staff**: Make password required (currently optional if password_hash exists)
- **Enable password validation for Managers**: Uncomment and enable password check (line ~429)
- **Enable password validation for Owners**: Add password check (currently completely skipped at line ~298)
- Remove all "password functionality removed" comments
- Ensure password is required for all login attempts

**Implementation Details:**

- Staff: Require password if password_hash exists, otherwise require password_hash to be set
- Manager: Require password and validate against password_hash
- Owner: Require password and validate against password_hash
- Return appropriate error messages for missing/invalid passwords

### 3. Create Password Generation Script (`backend/set_all_user_passwords.py`)

**Purpose:** Generate and set passwords for all staff, managers, and owners across all branches

**Password Strategy:**

- **Staff**: `staff{branch_name}{number}` (e.g., `staffAdyar1`, `staffT.Nagar2`)
- **Managers**: `manager{branch_name}` (e.g., `managerAdyar`, `managerT.Nagar`)
- **Owners**: `owner123` (common password for all owners)

**Script Features:**

- Connect to MongoDB
- Fetch all branches
- For each branch:
- Get all staff members
- Get all managers assigned to branch
- Get all owners
- Generate passwords based on naming convention
- Hash passwords using `hash_password()` from `utils.auth`
- Update all users with hashed passwords
- Verify passwords were set correctly
- Print summary with credentials for each user

**Output:**

- Display all created passwords organized by branch
- Show login credentials (email/mobile + password) for each user
- Verify all passwords are hashed correctly

### 4. Update Login Validation Logic

**Backend Changes:**

- Staff login: Require password (no more role selection fallback)
- Manager login: Require and validate password
- Owner login: Require and validate password
- Return clear error messages:
- "Password is required"
- "Invalid password"
- "User not found"

**Frontend Changes:**

- Add password validation before form submission
- Show clear error messages for missing passwords
- Ensure password field is visible and required for all user types

## Files to Modify

### Frontend:

1. `frontend/src/components/Login.jsx` - Add password fields and enable validation

### Backend:

1. `backend/routes/auth_routes.py` - Enable password validation for all user types
2. `backend/set_all_user_passwords.py` - **NEW** - Script to create passwords for all users

## Password Generation Rules

### Staff Passwords

- Format: `staff{BranchName}{Number}`
- Examples:
- Adyar branch staff: `staffAdyar1`, `staffAdyar2`, etc.
- T. Nagar branch staff: `staffT.Nagar1`, `staffT.Nagar2`, etc.
- Handle branch names with spaces/special chars (use first word or sanitize)

### Manager Passwords

- Format: `manager{BranchName}`
- Examples:
- Adyar manager: `managerAdyar`
- T. Nagar manager: `managerT.Nagar`

### Owner Passwords

- Format: `owner123` (common for all owners)

## Security Considerations

- All passwords stored as bcrypt hashes (never plain text)
- Use existing `hash_password()` function from `utils.auth`
- Verify passwords after setting using `verify_password()`
- Passwords should be at least 8 characters (current format meets this)
- Consider password complexity requirements for future

## Testing Checklist

- [ ] Staff can log in with password
- [ ] Managers can log in with password
- [ ] Owners can log in with password
- [ ] Invalid passwords are rejected
- [ ] Missing passwords show appropriate error
- [ ] All users have passwords set in database
- [ ] Passwords are hashed (not plain text) in MongoDB
- [ ] Login works for users from different branches
- [ ] Error messages are clear and helpful

## Migration Strategy

1. **Phase 1**: Update frontend to show password fields (but don't require yet)
2. **Phase 2**: Run password generation script to set passwords for all users
3. **Phase 3**: Enable password validation in backend
4. **Phase 4**: Make password required in frontend
5. **Phase 5**: Test login for all user types

## Success Criteria

- All staff, managers, and owners have passwords set in MongoDB
- All passwords are stored as bcrypt hashes
- Password field is visible and required in login UI for all user types
- Password validation works correctly in backend
- Users can successfully log in with their passwords
- Invalid passwords are rejected with clear error messages