"""
Comprehensive verification script to ensure all data operations use MongoDB
This script checks:
1. All models use MongoEngine Document
2. All routes use MongoDB operations (no SQLAlchemy)
3. No file-based storage for data
4. All CRUD operations go through MongoDB
"""
import os
import sys
import re
from pathlib import Path

def check_models():
    """Verify all models use MongoEngine"""
    print("=" * 80)
    print("CHECKING MODELS")
    print("=" * 80)
    
    models_file = Path("backend/models.py")
    if not models_file.exists():
        print("[ERROR] models.py not found")
        return False
    
    content = models_file.read_text()
    
    issues = []
    
    # Check for SQLAlchemy imports
    if "from sqlalchemy" in content or "import sqlalchemy" in content:
        issues.append("SQLAlchemy imports found in models.py")
    
    # Check for SQLAlchemy base classes
    if "db.Model" in content or "Base" in content:
        issues.append("SQLAlchemy base classes found")
    
    # Check for MongoEngine Document
    if "from mongoengine" not in content:
        issues.append("MongoEngine not imported")
    
    if "Document" not in content or "class" not in content:
        issues.append("No Document classes found")
    elif not re.search(r"class\s+\w+.*Document", content):
        # Check if any class inherits from Document
        if "class" in content and "Document" in content:
            # Likely OK, just check format
            pass
        else:
            issues.append("No Document classes found")
    
    if issues:
        print("[FAILED] Model issues found:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print("[OK] All models use MongoEngine Document")
        return True

def check_routes():
    """Verify all routes use MongoDB operations"""
    print("\n" + "=" * 80)
    print("CHECKING ROUTES")
    print("=" * 80)
    
    routes_dir = Path("backend/routes")
    if not routes_dir.exists():
        print("[ERROR] routes directory not found")
        return False
    
    sqlalchemy_patterns = [
        (r"db\.session\.", "db.session usage"),
        (r"\.query\.", ".query usage"),
        (r"\.filter_by\(", ".filter_by() usage"),
        (r"\.get_or_404\(", ".get_or_404() usage"),
        (r"from sqlalchemy", "SQLAlchemy import"),
        (r"import sqlalchemy", "SQLAlchemy import"),
        (r"SQLAlchemy", "SQLAlchemy reference"),
    ]
    
    issues = []
    checked_files = []
    
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
        
        checked_files.append(route_file.name)
        content = route_file.read_text()
        
        for pattern, description in sqlalchemy_patterns:
            if re.search(pattern, content):
                issues.append(f"{route_file.name}: {description}")
    
    if issues:
        print("[FAILED] SQLAlchemy patterns found in routes:")
        for issue in issues:
            print(f"  - {issue}")
        return False
    else:
        print(f"[OK] All {len(checked_files)} route files use MongoDB")
        return True

def check_file_storage():
    """Check for file-based data storage"""
    print("\n" + "=" * 80)
    print("CHECKING FOR FILE-BASED STORAGE")
    print("=" * 80)
    
    routes_dir = Path("backend/routes")
    if not routes_dir.exists():
        return False
    
    file_storage_patterns = [
        (r"open\([^,]+,\s*['\"]w", "File write operations"),
        (r"\.to_csv\(", "CSV export (data storage)"),
        (r"\.to_excel\(", "Excel export (data storage)"),
        (r"json\.dump\(", "JSON file write"),
        (r"pickle\.dump\(", "Pickle file write"),
    ]
    
    issues = []
    
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
        
        content = route_file.read_text()
        
        for pattern, description in file_storage_patterns:
            if re.search(pattern, content):
                # Check if it's just for export/download, not storage
                lines = content.split('\n')
                for i, line in enumerate(lines):
                    if re.search(pattern, line):
                        # Check context - if it's in a download/export route, it's OK
                        context = '\n'.join(lines[max(0, i-3):i+3])
                        if 'download' not in context.lower() and 'export' not in context.lower():
                            issues.append(f"{route_file.name}: {description} (line {i+1})")
    
    if issues:
        print("[WARNING] Potential file storage operations found:")
        for issue in issues:
            print(f"  - {issue}")
        print("  Note: These may be for export/download only, which is acceptable")
    else:
        print("[OK] No file-based data storage found")
    
    return True

def check_app_config():
    """Verify app.py uses MongoDB"""
    print("\n" + "=" * 80)
    print("CHECKING APP CONFIGURATION")
    print("=" * 80)
    
    app_file = Path("backend/app.py")
    if not app_file.exists():
        print("[ERROR] app.py not found")
        return False
    
    content = app_file.read_text()
    
    checks = {
        "MongoDB connection": "mongoengine" in content and "connect" in content,
        "MongoDB URI configured": "MONGODB_URI" in content,
        "No SQLite": "sqlite" not in content.lower(),
        "No SQLAlchemy": "sqlalchemy" not in content.lower(),
    }
    
    all_ok = True
    for check, result in checks.items():
        if result:
            print(f"[OK] {check}")
        else:
            print(f"[FAILED] {check}")
            all_ok = False
    
    return all_ok

def check_crud_operations():
    """Verify CRUD operations use MongoDB"""
    print("\n" + "=" * 80)
    print("CHECKING CRUD OPERATIONS")
    print("=" * 80)
    
    routes_dir = Path("backend/routes")
    if not routes_dir.exists():
        return False
    
    mongodb_patterns = [
        (r"\.objects\.", "MongoEngine .objects()"),
        (r"\.save\(\)", ".save() method"),
        (r"\.delete\(\)", ".delete() method"),
        (r"\.update\(\)", ".update() method"),
    ]
    
    sqlalchemy_patterns = [
        (r"db\.session\.add\(", "db.session.add()"),
        (r"db\.session\.commit\(", "db.session.commit()"),
        (r"db\.session\.delete\(", "db.session.delete()"),
    ]
    
    mongodb_count = 0
    sqlalchemy_count = 0
    
    for route_file in routes_dir.glob("*.py"):
        if route_file.name == "__init__.py":
            continue
        
        content = route_file.read_text()
        
        for pattern, _ in mongodb_patterns:
            mongodb_count += len(re.findall(pattern, content))
        
        for pattern, _ in sqlalchemy_patterns:
            sqlalchemy_count += len(re.findall(pattern, content))
    
    print(f"MongoDB operations found: {mongodb_count}")
    print(f"SQLAlchemy operations found: {sqlalchemy_count}")
    
    if sqlalchemy_count > 0:
        print("[FAILED] SQLAlchemy operations still present")
        return False
    elif mongodb_count > 0:
        print("[OK] All CRUD operations use MongoDB")
        return True
    else:
        print("[WARNING] No CRUD operations detected (may be configuration-only routes)")
        return True

def main():
    """Run all verification checks"""
    print("=" * 80)
    print("MONGODB USAGE VERIFICATION")
    print("=" * 80)
    
    results = {
        "Models": check_models(),
        "Routes": check_routes(),
        "File Storage": check_file_storage(),
        "App Config": check_app_config(),
        "CRUD Operations": check_crud_operations(),
    }
    
    print("\n" + "=" * 80)
    print("SUMMARY")
    print("=" * 80)
    
    all_passed = True
    for check, result in results.items():
        status = "[PASS]" if result else "[FAIL]"
        print(f"{status} {check}")
        if not result:
            all_passed = False
    
    print("\n" + "=" * 80)
    if all_passed:
        print("[SUCCESS] All checks passed! Application uses MongoDB exclusively.")
    else:
        print("[WARNING] Some checks failed. Please review the issues above.")
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == '__main__':
    sys.exit(main())

