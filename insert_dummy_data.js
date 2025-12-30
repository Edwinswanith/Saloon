// MongoDB Shell Script to Insert Dummy Authentication Data
// Run this in MongoDB Compass or mongosh

// Switch to Saloon database
use('Saloon');

// Clear existing staff and managers (CAUTION!)
print("Clearing existing staffs and managers...");
db.staffs.deleteMany({});
db.managers.deleteMany({});
print("✓ Cleared\n");

// Insert Staff Members
print("Inserting staff members...");
db.staffs.insertMany([
  {
    mobile: "9876543210",
    first_name: "Rajesh",
    last_name: "Kumar",
    email: "rajesh@salon.com",
    salary: 25000,
    commission_rate: 10.0,
    status: "active",
    role: "staff",
    password_hash: null,
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    mobile: "9876543211",
    first_name: "Priya",
    last_name: "Sharma",
    email: "priya@salon.com",
    salary: 28000,
    commission_rate: 12.0,
    status: "active",
    role: "staff",
    password_hash: null,
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    mobile: "9876543212",
    first_name: "Amit",
    last_name: "Patel",
    email: "amit@salon.com",
    salary: 30000,
    commission_rate: 15.0,
    status: "active",
    role: "manager",
    // Password: manager123 (hashed with bcrypt)
    password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND2hq9SJmGLO",
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    mobile: "9876543213",
    first_name: "Sneha",
    last_name: "Reddy",
    email: "sneha@salon.com",
    salary: 22000,
    commission_rate: 8.0,
    status: "active",
    role: "staff",
    password_hash: null,
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    mobile: "9876543214",
    first_name: "Vikram",
    last_name: "Singh",
    email: "vikram@salon.com",
    salary: 26000,
    commission_rate: 10.0,
    status: "active",
    role: "staff",
    password_hash: null,
    is_active: true,
    created_at: new Date(),
    updated_at: new Date()
  }
]);
print("✓ Inserted 5 staff members\n");

// Insert Managers
print("Inserting managers...");
db.managers.insertMany([
  {
    first_name: "Arun",
    last_name: "Mehta",
    email: "arun@salon.com",
    mobile: "9876543220",
    salon: "Glamour Salon - Main Branch",
    // Password: manager123 (hashed with bcrypt)
    password_hash: "$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewY5ND2hq9SJmGLO",
    role: "manager",
    permissions: [],
    is_active: true,
    status: "active",
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    first_name: "Kavita",
    last_name: "Desai",
    email: "kavita@salon.com",
    mobile: "9876543221",
    salon: "Glamour Salon - Main Branch",
    // Password: manager456 (hashed with bcrypt)
    password_hash: "$2b$12$8Wqo3PDBkZF8qNXyZqU0/.ZhPCxPU7LqPzY0Bw3yPL6aPqR0fJmXy",
    role: "manager",
    permissions: [],
    is_active: true,
    status: "active",
    created_at: new Date(),
    updated_at: new Date()
  },
  {
    first_name: "Rahul",
    last_name: "Chopra",
    email: "owner@salon.com",
    mobile: "9876543230",
    salon: "Glamour Salon - All Branches",
    // Password: owner123 (hashed with bcrypt)
    password_hash: "$2b$12$vN7dPQ8yXqU2cTxZnP7Ohe.fMQwGp1YqL5Jz8vY3nK9sW4Rm6Xu1u",
    role: "owner",
    permissions: [],
    is_active: true,
    status: "active",
    created_at: new Date(),
    updated_at: new Date()
  }
]);
print("✓ Inserted 3 managers (including 1 owner)\n");

// Verify insertion
print("=".repeat(60));
print("VERIFICATION:");
print("=".repeat(60));
print("Staff count:", db.staffs.countDocuments());
print("Manager count:", db.managers.countDocuments());

print("\n" + "=".repeat(60));
print("TEST ACCOUNTS CREATED:");
print("=".repeat(60));

print("\n📋 STAFF (No Password - Role Selection):");
print("-".repeat(60));
db.staffs.find({password_hash: null}).forEach(staff => {
  print(`  • ${staff.first_name} ${staff.last_name}`);
  print(`    Mobile: ${staff.mobile}`);
  print(`    Role: ${staff.role}\n`);
});

print("\n📋 STAFF WITH PASSWORD:");
print("-".repeat(60));
db.staffs.find({password_hash: {$ne: null}}).forEach(staff => {
  print(`  • ${staff.first_name} ${staff.last_name}`);
  print(`    Mobile: ${staff.mobile}`);
  print(`    Password: manager123`);
  print(`    Role: ${staff.role}\n`);
});

print("\n📋 MANAGERS:");
print("-".repeat(60));
db.managers.find({role: "manager"}).forEach(manager => {
  print(`  • ${manager.first_name} ${manager.last_name}`);
  print(`    Email: ${manager.email}`);
  if (manager.email === "arun@salon.com") print(`    Password: manager123`);
  if (manager.email === "kavita@salon.com") print(`    Password: manager456`);
  print("");
});

print("\n📋 OWNER:");
print("-".repeat(60));
db.managers.find({role: "owner"}).forEach(owner => {
  print(`  • ${owner.first_name} ${owner.last_name}`);
  print(`    Email: ${owner.email}`);
  print(`    Password: owner123`);
  print("");
});

print("\n" + "=".repeat(60));
print("✅ DUMMY DATA INSERTED SUCCESSFULLY!");
print("=".repeat(60));

print("\nYou can now test login with:");
print("  Staff: Select 'Rajesh Kumar' → Role: staff → Sign In");
print("  Manager: arun@salon.com / manager123");
print("  Owner: owner@salon.com / owner123");
print("");
