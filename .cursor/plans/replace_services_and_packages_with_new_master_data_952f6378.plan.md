---
name: Replace Services and Packages with New Master Data
overview: Remove all existing services and packages from MongoDB and replace them with the new service master and package master data provided by the user, organized by proper service groups.
todos: []
---

# Replace Services and Packages with New Master Data

## Overview

This plan will completely replace all existing services and packages in MongoDB with the new service master and package master data provided. The data will be organized into proper service groups for better categorization.

## Data Structure Analysis

### Service Groups Needed:

1. **Hair Services** (Hair Cut, Beard & Grooming)
2. **Threading & Face Care** (Threading)
3. **Waxing Services**
4. **Bleach Services**
5. **Facial Services** (Basic, Advanced/Metallic, Luxury)
6. **Manicure & Pedicure**
7. **Hair Care & Treatments**
8. **Body Spa & Massage**
9. **Quick Relief Massages**
10. **Bridal & Makeup**

### Services to Create:

- **Hair Services**: 6 services (3 Hair Cut, 3 Beard & Grooming)
- **Threading**: 4 services
- **Waxing**: 6 services + 2 add-ons (as separate services)
- **Bleach**: 4 services
- **Facials**: 3 Basic, 3 Advanced/Metallic, 2 Luxury = 8 services
- **Manicure & Pedicure**: 6 services (3 Manicure, 3 Pedicure)
- **Hair Care**: 5 services (2 Hair Spa, 3 Hair Treatments)
- **Body Spa**: 2 services (Body Massage, Body Polishing)
- **Quick Relief**: 3 services
- **Bridal & Makeup**: 4 services (2 Makeup, 2 Mehandi)

**Total: ~48 services**

### Packages to Create:

1. **Basic Grooming Package** - ₹999, 30 days (Hair Cut, Beard Trim, Clean-Up)
2. **Spa Relax Package** - ₹2,999, 45 days (Body Massage, Basic Facial, Head Massage)
3. **Pre-Bridal Package** - ₹9,999, 3 months (3 Facials, Full Body Wax, Manicure & Pedicure, Hair Spa)
4. **Full Day Spa Package** - ₹6,999, 1 day (Body Massage, Body Polishing, Spa Facial, Steam & Shower)

## Implementation Plan

### 1. Create Python Script for Data Migration

**File**: `backend/replace_services_packages.py` (NEW)

**Steps**:

1. Connect to MongoDB
2. **Delete all existing data**:

   - Delete all Service documents
   - Delete all ServiceGroup documents
   - Delete all Package documents
   - Print confirmation of deletions

3. **Create Service Groups**:

   - Create 10 service groups with proper display_order
   - Display order: 1-10 based on the order in the master list

4. **Create Services**:

   - For each service category, create all services
   - Link each service to its appropriate ServiceGroup
   - Set price, duration (where specified), status='active'
   - Handle add-ons (Hygienic Wax, Tan Removal) as separate services

5. **Create Packages**:

   - Create 4 packages with proper names, prices, descriptions
   - For each package, find the service IDs by name matching
   - Store service IDs as JSON string in Package.services field
   - Set validity_days based on package (30, 45, 90, 1)
   - Note: Package model uses `services` as StringField (JSON string), not a list

6. **Verification**:

   - Print summary of created service groups, services, and packages
   - Verify package-service associations

### 2. Service Group Creation Details

```python
service_groups = [
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
```

### 3. Service Creation Details

**Hair Services Group**:

- Hair Cut – Basic (₹300, 30 mins)
- Hair Cut – Advanced Styling (₹500, 45 mins)
- Kids Hair Cut (₹200, 20 mins)
- Beard Trim (₹150, 15 mins)
- Beard Styling (₹250, 20 mins)
- Clean Shave (₹200, 20 mins)

**Threading & Face Care Group**:

- Eyebrow (₹50)
- Upper Lip (₹40)
- Chin (₹40)
- Full Face Threading (₹200)

**Waxing Services Group**:

- Under Arms (₹100)
- Half Arms (₹200)
- Full Arms (₹300)
- Half Legs (₹250)
- Full Legs (₹450)
- Full Body Wax (₹1,200)
- Hygienic Wax (₹100) - Add-on
- Tan Removal After Wax (₹150) - Add-on

**Bleach Services Group**:

- Face Bleach (₹250)
- Underarm Bleach (₹200)
- Full Arms Bleach (₹400)
- Full Body Bleach (₹1,500)

**Facial Services Group**:

- Clean-Up (₹500)
- Fruit Facial (₹700)
- Papaya Facial (₹800)
- Gold Facial (₹1,200)
- Diamond Facial (₹1,500)
- Pearl Facial (₹1,300)
- Ultimo Gold (₹2,500)
- Ultimo Platinum (₹3,000)

**Manicure & Pedicure Group**:

- Basic Manicure (₹400)
- Spa Manicure (₹700)
- Crystal Manicure (₹900)
- Basic Pedicure (₹500)
- Spa Pedicure (₹800)
- Crystal Pedicure (₹1,100)

**Hair Care & Treatments Group**:

- Classic Hair Spa (₹1,000)
- Anti Hair Fall Spa (₹1,500)
- Hair Smoothening (₹4,000)
- Hair Straightening (₹5,000)
- Hair Rebonding (₹6,000)

**Body Spa & Massage Group**:

- Ayurvedic Massage (₹1,500)
- Swedish Massage (₹2,000)
- Aroma Massage (₹2,200)
- Full Body Polishing (₹2,500)

**Quick Relief Massages Group**:

- Neck Massage (₹300)
- Back Massage (₹400)
- Leg Massage (₹400)

**Bridal & Makeup Group**:

- Party Makeup (₹2,500)
- Bridal Makeup (₹10,000)
- Bridal Mehandi (₹5,000)
- Arabic Mehandi (₹2,000)

### 4. Package Creation Details

**Basic Grooming Package**:

- Price: ₹999
- Validity: 30 days
- Services: "Hair Cut – Basic", "Beard Trim", "Clean Shave"
- Description: "Includes Hair Cut, Beard Trim, and Clean-Up"

**Spa Relax Package**:

- Price: ₹2,999
- Validity: 45 days
- Services: "Ayurvedic Massage" (or any Body Massage), "Clean-Up" (Basic Facial), "Neck Massage" (as Head Massage)
- Description: "Includes Body Massage, Basic Facial, and Head Massage"
- Note: "Head Massage" not in service list - use "Neck Massage" or create "Head Massage" service

**Pre-Bridal Package**:

- Price: ₹9,999
- Validity: 90 days (3 months)
- Services: "Clean-Up" (3x - represented as one), "Full Body Wax", "Basic Manicure", "Basic Pedicure", "Classic Hair Spa"
- Description: "Includes 3 Facials, Full Body Wax, Manicure & Pedicure, and Hair Spa"
- Note: Package model doesn't support quantity per service - will need to document this in description

**Full Day Spa Package**:

- Price: ₹6,999
- Validity: 1 day
- Services: "Ayurvedic Massage", "Full Body Polishing", "Fruit Facial" (as Spa Facial), "Swedish Massage" (as Steam & Shower alternative)
- Description: "Includes Body Massage, Body Polishing, Spa Facial, Steam & Shower"
- Note: "Steam & Shower" not in service list - use closest match or document in description

### 5. Important Notes

- **Service Name Matching**: When creating packages, match service names exactly (case-insensitive)
- **Duration Handling**: Some services don't have duration specified - set to None or reasonable default
- **Package Services Field**: Package.services is a StringField containing JSON string of service IDs
- **Validity Days**: Need to add validity_days field if Package model supports it, or document in description
- **Add-ons**: Treat "Hygienic Wax" and "Tan Removal After Wax" as separate services, not modifiers

### 6. Script Execution

The script should:

1. Ask for confirmation before deleting existing data
2. Show progress for each step
3. Handle errors gracefully
4. Provide detailed summary at the end
5. Verify all data was created correctly

## Expected Outcome

After execution:

- All old services and packages removed
- 10 service groups created
- ~48 services created and properly categorized
- 4 packages created with correct service associations
- Clean, organized service master data matching user's requirements