"""
Script to replace all existing services and packages with new master data
This will delete all existing Service, ServiceGroup, and Package documents
and create new ones based on the provided service master and package master data
"""

import sys
import os
import json
from datetime import datetime

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from mongoengine import connect
from models import Service, ServiceGroup, Package

# Connect to MongoDB
try:
    connect(
        db='Saloon',
        host='mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/?appName=Saloon',
        serverSelectionTimeoutMS=30000,
        connectTimeoutMS=30000,
        socketTimeoutMS=30000
    )
    print("Connected to MongoDB successfully!")
except Exception as e:
    print(f"Error connecting to MongoDB: {e}")
    sys.exit(1)


def delete_existing_data():
    """Delete all existing services, service groups, and packages"""
    print("\n" + "="*60)
    print("DELETING EXISTING DATA")
    print("="*60)
    
    try:
        # Count existing data
        service_count = Service.objects().count()
        group_count = ServiceGroup.objects().count()
        package_count = Package.objects().count()
        
        print(f"\nExisting data found:")
        print(f"  - Services: {service_count}")
        print(f"  - Service Groups: {group_count}")
        print(f"  - Packages: {package_count}")
        
        # Delete all services first (they reference service groups)
        deleted_services = Service.objects().delete()
        print(f"\n[DELETED] {deleted_services} services")
        
        # Delete all service groups
        deleted_groups = ServiceGroup.objects().delete()
        print(f"[DELETED] {deleted_groups} service groups")
        
        # Delete all packages
        deleted_packages = Package.objects().delete()
        print(f"[DELETED] {deleted_packages} packages")
        
        print("\n[SUCCESS] All existing data deleted successfully!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to delete existing data: {e}")
        return False


def create_service_groups():
    """Create all service groups"""
    print("\n" + "="*60)
    print("CREATING SERVICE GROUPS")
    print("="*60)
    
    service_groups_data = [
        {'name': 'Hair Services', 'order': 1},
        {'name': 'Threading & Face Care', 'order': 2},
        {'name': 'Waxing Services', 'order': 3},
        {'name': 'Bleach Services', 'order': 4},
        {'name': 'Facial Services', 'order': 5},
        {'name': 'Manicure & Pedicure', 'order': 6},
        {'name': 'Hair Care & Treatments', 'order': 7},
        {'name': 'Body Spa & Massage', 'order': 8},
        {'name': 'Quick Relief Massages', 'order': 9},
        {'name': 'Bridal & Makeup', 'order': 10}
    ]
    
    created_groups = {}
    
    try:
        for group_data in service_groups_data:
            group = ServiceGroup(
                name=group_data['name'],
                display_order=group_data['order']
            )
            group.save()
            created_groups[group_data['name']] = group
            print(f"[CREATED] {group_data['name']} (Order: {group_data['order']})")
        
        print(f"\n[SUCCESS] Created {len(created_groups)} service groups")
        return created_groups
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create service groups: {e}")
        return None


def create_services(service_groups):
    """Create all services organized by groups"""
    print("\n" + "="*60)
    print("CREATING SERVICES")
    print("="*60)
    
    services_data = [
        # Hair Services
        {'name': 'Hair Cut – Basic', 'group': 'Hair Services', 'price': 300, 'duration': 30},
        {'name': 'Hair Cut – Advanced Styling', 'group': 'Hair Services', 'price': 500, 'duration': 45},
        {'name': 'Kids Hair Cut', 'group': 'Hair Services', 'price': 200, 'duration': 20},
        {'name': 'Beard Trim', 'group': 'Hair Services', 'price': 150, 'duration': 15},
        {'name': 'Beard Styling', 'group': 'Hair Services', 'price': 250, 'duration': 20},
        {'name': 'Clean Shave', 'group': 'Hair Services', 'price': 200, 'duration': 20},
        
        # Threading & Face Care
        {'name': 'Eyebrow', 'group': 'Threading & Face Care', 'price': 50, 'duration': None},
        {'name': 'Upper Lip', 'group': 'Threading & Face Care', 'price': 40, 'duration': None},
        {'name': 'Chin', 'group': 'Threading & Face Care', 'price': 40, 'duration': None},
        {'name': 'Full Face Threading', 'group': 'Threading & Face Care', 'price': 200, 'duration': None},
        
        # Waxing Services
        {'name': 'Under Arms', 'group': 'Waxing Services', 'price': 100, 'duration': None},
        {'name': 'Half Arms', 'group': 'Waxing Services', 'price': 200, 'duration': None},
        {'name': 'Full Arms', 'group': 'Waxing Services', 'price': 300, 'duration': None},
        {'name': 'Half Legs', 'group': 'Waxing Services', 'price': 250, 'duration': None},
        {'name': 'Full Legs', 'group': 'Waxing Services', 'price': 450, 'duration': None},
        {'name': 'Full Body Wax', 'group': 'Waxing Services', 'price': 1200, 'duration': None},
        {'name': 'Hygienic Wax', 'group': 'Waxing Services', 'price': 100, 'duration': None},
        {'name': 'Tan Removal After Wax', 'group': 'Waxing Services', 'price': 150, 'duration': None},
        
        # Bleach Services
        {'name': 'Face Bleach', 'group': 'Bleach Services', 'price': 250, 'duration': None},
        {'name': 'Underarm Bleach', 'group': 'Bleach Services', 'price': 200, 'duration': None},
        {'name': 'Full Arms Bleach', 'group': 'Bleach Services', 'price': 400, 'duration': None},
        {'name': 'Full Body Bleach', 'group': 'Bleach Services', 'price': 1500, 'duration': None},
        
        # Facial Services
        {'name': 'Clean-Up', 'group': 'Facial Services', 'price': 500, 'duration': None},
        {'name': 'Fruit Facial', 'group': 'Facial Services', 'price': 700, 'duration': None},
        {'name': 'Papaya Facial', 'group': 'Facial Services', 'price': 800, 'duration': None},
        {'name': 'Gold Facial', 'group': 'Facial Services', 'price': 1200, 'duration': None},
        {'name': 'Diamond Facial', 'group': 'Facial Services', 'price': 1500, 'duration': None},
        {'name': 'Pearl Facial', 'group': 'Facial Services', 'price': 1300, 'duration': None},
        {'name': 'Ultimo Gold', 'group': 'Facial Services', 'price': 2500, 'duration': None},
        {'name': 'Ultimo Platinum', 'group': 'Facial Services', 'price': 3000, 'duration': None},
        
        # Manicure & Pedicure
        {'name': 'Basic Manicure', 'group': 'Manicure & Pedicure', 'price': 400, 'duration': None},
        {'name': 'Spa Manicure', 'group': 'Manicure & Pedicure', 'price': 700, 'duration': None},
        {'name': 'Crystal Manicure', 'group': 'Manicure & Pedicure', 'price': 900, 'duration': None},
        {'name': 'Basic Pedicure', 'group': 'Manicure & Pedicure', 'price': 500, 'duration': None},
        {'name': 'Spa Pedicure', 'group': 'Manicure & Pedicure', 'price': 800, 'duration': None},
        {'name': 'Crystal Pedicure', 'group': 'Manicure & Pedicure', 'price': 1100, 'duration': None},
        
        # Hair Care & Treatments
        {'name': 'Classic Hair Spa', 'group': 'Hair Care & Treatments', 'price': 1000, 'duration': None},
        {'name': 'Anti Hair Fall Spa', 'group': 'Hair Care & Treatments', 'price': 1500, 'duration': None},
        {'name': 'Hair Smoothening', 'group': 'Hair Care & Treatments', 'price': 4000, 'duration': None},
        {'name': 'Hair Straightening', 'group': 'Hair Care & Treatments', 'price': 5000, 'duration': None},
        {'name': 'Hair Rebonding', 'group': 'Hair Care & Treatments', 'price': 6000, 'duration': None},
        
        # Body Spa & Massage
        {'name': 'Ayurvedic Massage', 'group': 'Body Spa & Massage', 'price': 1500, 'duration': None},
        {'name': 'Swedish Massage', 'group': 'Body Spa & Massage', 'price': 2000, 'duration': None},
        {'name': 'Aroma Massage', 'group': 'Body Spa & Massage', 'price': 2200, 'duration': None},
        {'name': 'Full Body Polishing', 'group': 'Body Spa & Massage', 'price': 2500, 'duration': None},
        
        # Quick Relief Massages
        {'name': 'Neck Massage', 'group': 'Quick Relief Massages', 'price': 300, 'duration': None},
        {'name': 'Back Massage', 'group': 'Quick Relief Massages', 'price': 400, 'duration': None},
        {'name': 'Leg Massage', 'group': 'Quick Relief Massages', 'price': 400, 'duration': None},
        
        # Bridal & Makeup
        {'name': 'Party Makeup', 'group': 'Bridal & Makeup', 'price': 2500, 'duration': None},
        {'name': 'Bridal Makeup', 'group': 'Bridal & Makeup', 'price': 10000, 'duration': None},
        {'name': 'Bridal Mehandi', 'group': 'Bridal & Makeup', 'price': 5000, 'duration': None},
        {'name': 'Arabic Mehandi', 'group': 'Bridal & Makeup', 'price': 2000, 'duration': None},
    ]
    
    created_services = {}
    
    try:
        for service_data in services_data:
            group = service_groups.get(service_data['group'])
            if not group:
                print(f"[ERROR] Service group '{service_data['group']}' not found!")
                continue
            
            service = Service(
                name=service_data['name'],
                group=group,
                price=service_data['price'],
                duration=service_data.get('duration'),
                status='active'
            )
            service.save()
            created_services[service_data['name']] = service
            duration_str = f" ({service_data['duration']} mins)" if service_data.get('duration') else ""
            print(f"[CREATED] {service_data['name']} - Rs {service_data['price']}{duration_str}")
        
        print(f"\n[SUCCESS] Created {len(created_services)} services")
        return created_services
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create services: {e}")
        import traceback
        traceback.print_exc()
        return None


def create_packages(services):
    """Create all packages with proper service associations"""
    print("\n" + "="*60)
    print("CREATING PACKAGES")
    print("="*60)
    
    packages_data = [
        {
            'name': 'Basic Grooming Package',
            'price': 999,
            'description': 'Includes Hair Cut, Beard Trim, and Clean Shave. Validity: 30 days',
            'service_names': ['Hair Cut – Basic', 'Beard Trim', 'Clean Shave']
        },
        {
            'name': 'Spa Relax Package',
            'price': 2999,
            'description': 'Includes Body Massage, Basic Facial, and Head Massage. Validity: 45 days',
            'service_names': ['Ayurvedic Massage', 'Clean-Up', 'Neck Massage']
        },
        {
            'name': 'Pre-Bridal Package',
            'price': 9999,
            'description': 'Includes 3 Facials, Full Body Wax, Manicure & Pedicure, and Hair Spa. Validity: 3 months (90 days)',
            'service_names': ['Clean-Up', 'Full Body Wax', 'Basic Manicure', 'Basic Pedicure', 'Classic Hair Spa']
        },
        {
            'name': 'Full Day Spa Package',
            'price': 6999,
            'description': 'Includes Body Massage, Body Polishing, Spa Facial, and Steam & Shower. Validity: 1 day',
            'service_names': ['Ayurvedic Massage', 'Full Body Polishing', 'Fruit Facial', 'Swedish Massage']
        }
    ]
    
    created_packages = []
    
    try:
        for package_data in packages_data:
            # Find service IDs by name matching (case-insensitive)
            service_ids = []
            for service_name in package_data['service_names']:
                # Try exact match first
                if service_name in services:
                    service_ids.append(str(services[service_name].id))
                else:
                    # Try case-insensitive match
                    found = False
                    for s_name, service_obj in services.items():
                        if s_name.lower() == service_name.lower():
                            service_ids.append(str(service_obj.id))
                            found = True
                            break
                    if not found:
                        print(f"[WARNING] Service '{service_name}' not found for package '{package_data['name']}'")
            
            if not service_ids:
                print(f"[ERROR] No services found for package '{package_data['name']}'. Skipping...")
                continue
            
            # Create package with services as JSON string
            package = Package(
                name=package_data['name'],
                price=package_data['price'],
                description=package_data['description'],
                services=json.dumps(service_ids),
                status='active'
            )
            package.save()
            created_packages.append(package)
            print(f"[CREATED] {package_data['name']} - Rs {package_data['price']}")
            print(f"  - Includes {len(service_ids)} services: {', '.join(package_data['service_names'])}")
        
        print(f"\n[SUCCESS] Created {len(created_packages)} packages")
        return created_packages
        
    except Exception as e:
        print(f"\n[ERROR] Failed to create packages: {e}")
        import traceback
        traceback.print_exc()
        return None


def verify_data():
    """Verify all created data"""
    print("\n" + "="*60)
    print("VERIFICATION")
    print("="*60)
    
    try:
        # Count created data
        service_count = Service.objects().count()
        group_count = ServiceGroup.objects().count()
        package_count = Package.objects().count()
        
        print(f"\nCreated data summary:")
        print(f"  - Service Groups: {group_count}")
        print(f"  - Services: {service_count}")
        print(f"  - Packages: {package_count}")
        
        # List all service groups
        print("\nService Groups:")
        groups = ServiceGroup.objects().order_by('display_order')
        for group in groups:
            service_count_in_group = Service.objects(group=group).count()
            print(f"  - {group.name} (Order: {group.display_order}) - {service_count_in_group} services")
        
        # List all packages with their services
        print("\nPackages:")
        packages = Package.objects()
        for package in packages:
            service_ids = json.loads(package.services) if package.services else []
            service_names = []
            for service_id in service_ids:
                try:
                    service = Service.objects(id=service_id).first()
                    if service:
                        service_names.append(service.name)
                except:
                    pass
            print(f"  - {package.name} (Rs {package.price})")
            print(f"    Services: {', '.join(service_names) if service_names else 'None'}")
        
        print("\n[SUCCESS] Verification completed!")
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main execution function"""
    print("\n" + "="*60)
    print("REPLACE SERVICES AND PACKAGES WITH NEW MASTER DATA")
    print("="*60)
    print("\nWARNING: This will delete ALL existing services, service groups, and packages!")
    print("Press Ctrl+C to cancel, or wait 3 seconds to continue...")
    
    try:
        import time
        time.sleep(3)
    except KeyboardInterrupt:
        print("\n\n[CANCELLED] Operation cancelled by user")
        return
    
    # Step 1: Delete existing data
    if not delete_existing_data():
        print("\n[ERROR] Failed to delete existing data. Aborting...")
        return
    
    # Step 2: Create service groups
    service_groups = create_service_groups()
    if not service_groups:
        print("\n[ERROR] Failed to create service groups. Aborting...")
        return
    
    # Step 3: Create services
    services = create_services(service_groups)
    if not services:
        print("\n[ERROR] Failed to create services. Aborting...")
        return
    
    # Step 4: Create packages
    packages = create_packages(services)
    if not packages:
        print("\n[ERROR] Failed to create packages. Aborting...")
        return
    
    # Step 5: Verify data
    verify_data()
    
    print("\n" + "="*60)
    print("MIGRATION COMPLETED SUCCESSFULLY!")
    print("="*60)
    print(f"\nSummary:")
    print(f"  - Service Groups: {len(service_groups)}")
    print(f"  - Services: {len(services)}")
    print(f"  - Packages: {len(packages)}")
    print("\nAll data has been replaced with the new master data.")


if __name__ == '__main__':
    main()

