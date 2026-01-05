#!/usr/bin/env python3
"""
Script to add services to existing packages in MongoDB
"""
from mongoengine import connect
from models import Package, Service
import json

# Connect to MongoDB
MONGODB_URI = "mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/Saloon?appName=Saloon"

def populate_package_services():
    """Add services to packages"""
    
    print("\n" + "="*60)
    print("ADDING SERVICES TO PACKAGES")
    print("="*60)
    
    try:
        # Connect to MongoDB
        connect(host=MONGODB_URI)
        print("\n[SUCCESS] Connected to MongoDB")
        
        # Get all services
        services = Service.objects()
        print(f"\n[INFO] Found {len(services)} services in database")
        
        if len(services) == 0:
            print("[ERROR] No services found! Please add services first.")
            return False
        
        # Display available services
        print("\nAvailable Services:")
        service_dict = {}
        for i, service in enumerate(services, 1):
            print(f"  {i}. {service.name} - Rs {service.price} ({service.duration} min)")
            service_dict[service.name.lower()] = str(service.id)
        
        # Get all packages
        packages = Package.objects()
        print(f"\n[INFO] Found {len(packages)} packages")
        
        if len(packages) == 0:
            print("[ERROR] No packages found!")
            return False
        
        # Define package-service mappings
        package_mappings = {
            'beauty essentials': ['haircut (women)', 'facial', 'manicure'],
            'bridal special': ['haircut (women)', 'hair color', 'hair spa', 'facial', 'makeup'],
            'hair care combo': ['haircut (women)', 'hair spa', 'hair oil treatment'],
            'spa relaxation': ['hair spa', 'facial', 'head massage']
        }
        
        updated_count = 0
        
        for package in packages:
            package_name_lower = package.name.lower()
            
            # Find matching services
            service_ids = []
            
            if package_name_lower in package_mappings:
                # Use predefined mapping
                for service_name in package_mappings[package_name_lower]:
                    if service_name in service_dict:
                        service_ids.append(service_dict[service_name])
            else:
                # For unmapped packages, add some default services
                # Add first 3 services as default
                service_ids = [str(s.id) for s in services[:3]]
            
            # Update package
            if service_ids:
                package.services = json.dumps(service_ids)
                package.save()
                print(f"\n[UPDATED] {package.name}")
                print(f"  - Added {len(service_ids)} services")
                updated_count += 1
            else:
                print(f"\n[SKIPPED] {package.name} - No matching services found")
        
        print("\n" + "="*60)
        print("SUMMARY")
        print("="*60)
        print(f"Total Packages: {len(packages)}")
        print(f"Updated Packages: {updated_count}")
        print(f"Skipped Packages: {len(packages) - updated_count}")
        
        # Verify the updates
        print("\n" + "="*60)
        print("VERIFICATION")
        print("="*60)
        
        packages = Package.objects()
        for package in packages:
            service_ids = json.loads(package.services) if package.services else []
            print(f"\n{package.name} (Rs {package.price}):")
            print(f"  - Service IDs: {len(service_ids)}")
            
            # Fetch and display service details
            for service_id in service_ids:
                try:
                    service = Service.objects.get(id=service_id)
                    print(f"    * {service.name} - Rs {service.price} ({service.duration} min)")
                except:
                    print(f"    * [ERROR] Service {service_id} not found")
        
        print("\n" + "="*60)
        print("[SUCCESS] Package services updated successfully!")
        print("="*60 + "\n")
        
        return True
        
    except Exception as e:
        print(f"\n[ERROR] Failed to update packages: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = populate_package_services()
    if not success:
        print("\n[FAILED] Please check the errors above and try again.")
    else:
        print("\n[COMPLETE] You can now see services in the Package List dropdown!")

