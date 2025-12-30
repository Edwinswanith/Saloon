# Manager & Owner Password Feature

## Current Status: **DISABLED** (Paused)

The password requirement for manager and owner login is currently **disabled**. Both managers and owners can log in without entering a password. The password field is completely hidden from the login UI.

## How to Re-enable Password Requirement

### Option 1: Environment Variable (Recommended)
Set the environment variable `MANAGER_PASSWORD_REQUIRED=true` before starting the server:

**Windows (PowerShell):**
```powershell
$env:MANAGER_PASSWORD_REQUIRED="true"
python app.py
```

**Windows (CMD):**
```cmd
set MANAGER_PASSWORD_REQUIRED=true
python app.py
```

**Linux/Mac:**
```bash
export MANAGER_PASSWORD_REQUIRED=true
python app.py
```

### Option 2: Direct Code Change
Edit `backend/routes/auth_routes.py` and change line 21:

```python
# Change from:
MANAGER_PASSWORD_REQUIRED = os.environ.get('MANAGER_PASSWORD_REQUIRED', 'false').lower() == 'true'

# To:
MANAGER_PASSWORD_REQUIRED = True  # Enable password requirement
```

## What Happens When Re-enabled

1. **Backend**: Both managers and owners will be required to enter a password during login
2. **Frontend**: The password field will need to be uncommented in `Login.jsx` for both manager and owner sections
3. **Validation**: Password will be verified against the stored hash in MongoDB

## Current Behavior (Password Disabled)

- **Managers** can log in with just their email/mobile and branch selection
- **Owners** can log in with just their email address
- Password field is **completely hidden** from the UI (commented out in code)
- Password validation is skipped in the backend for both managers and owners
- Login history logs indicate "Password validation skipped (feature disabled)"

## Notes

- All manager passwords are still stored in MongoDB (hashed with bcrypt)
- Password: `manager123` for all managers (set via `set_manager_passwords.py`)
- When re-enabled, managers and owners can use their existing passwords
- The feature flag affects both **managers** and **owners**
- To re-enable in frontend: Uncomment the password field sections in `Login.jsx` (lines ~454-470 for managers, ~493-510 for owners)

## Testing

To test password functionality when re-enabled:
1. Set `MANAGER_PASSWORD_REQUIRED=true`
2. Restart the backend server
3. Try logging in as a manager:
   - Without password: Should fail
   - With wrong password: Should fail
   - With correct password (`manager123`): Should succeed

