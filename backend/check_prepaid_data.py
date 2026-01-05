from mongoengine import connect
from models import PrepaidPackage, PrepaidGroup, Customer

# Connect to MongoDB
connect(host='mongodb+srv://edwin:Edwin006@saloon.8fxk7vz.mongodb.net/Saloon?appName=Saloon')

# Get prepaid data
groups = PrepaidGroup.objects()
packages = PrepaidPackage.objects()

print(f'\n=== PREPAID DATA ANALYSIS ===')
print(f'Total Prepaid Groups: {len(groups)}')
print(f'Total Prepaid Packages: {len(packages)}')

if groups:
    print(f'\nPrepaid Groups:')
    for g in groups:
        print(f'  - ID: {g.id} | Name: {g.name}')

if packages:
    print(f'\nPrepaid Packages:')
    for p in packages:
        try:
            customer_name = f"{p.customer.first_name} {p.customer.last_name}" if p.customer else "No Customer"
            print(f'  - ID: {p.id}')
            print(f'    Name: {p.name}')
            print(f'    Customer: {customer_name}')
            print(f'    Balance: {p.remaining_balance}')
            print(f'    Status: {p.status}')
            print()
        except Exception as e:
            print(f'  - Error reading package: {str(e)}')

# Check if there are packages without customers (available for purchase)
packages_without_customer = PrepaidPackage.objects(customer=None)
print(f'\nPackages Available for Purchase (No Customer): {len(packages_without_customer)}')

# Check active packages
active_packages = PrepaidPackage.objects(status='active')
print(f'Active Packages: {len(active_packages)}')

# Check a specific customer's packages
customers = Customer.objects()[:3]
for customer in customers:
    customer_packages = PrepaidPackage.objects(customer=customer, status='active')
    print(f'\n{customer.first_name} {customer.last_name} has {len(customer_packages)} active prepaid packages')

