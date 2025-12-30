# Branch and Customer Data from MongoDB

## 7 Branch Unique IDs

| Branch Name | Branch ID | City | Customer Count |
|------------|-----------|------|----------------|
| T. Nagar | `694522d4101e4512a09f92b7` | Chennai | 87 |
| Anna Nagar | `694523e1e7624aff7c44993a` | Chennai | 86 |
| Velachery | `694523e1e7624aff7c44993b` | Chennai | 86 |
| Adyar | `694523e1e7624aff7c44993c` | Chennai | 86 |
| Porur | `694523e1e7624aff7c44993d` | Chennai | 86 |
| Chrompet | `694523e1e7624aff7c44993e` | Chennai | 85 |
| Tambaram | `694523e1e7624aff7c44993f` | Chennai | 85 |

**Total Customers: 601** (all properly assigned to branches)

---

## Customer Distribution by Branch

### 1. T. Nagar (ID: `694522d4101e4512a09f92b7`)
- **Total Customers: 87**
- **Sample Customer IDs:**
  - `694008cce260c5846226ad47`
  - `694008cde260c5846226ad4e`
  - `694008cde260c5846226ad55`
  - `694008cde260c5846226ad5c`
  - `694523e3e7624aff7c44994e`
  - ... (82 more)

### 2. Anna Nagar (ID: `694523e1e7624aff7c44993a`)
- **Total Customers: 86**
- **Sample Customers:**
  - Rahul Kumar (ID: `694008cce260c5846226ad48`, Mobile: `9876543211`)
  - Sneha Desai (ID: `694008cde260c5846226ad4f`, Mobile: `9876543218`)
  - Aditya Saxena (ID: `694008cde260c5846226ad56`, Mobile: `9876543225`)
  - Aishwarya Nair (ID: `694008cde260c5846226ad5d`, Mobile: `9876543232`)
  - Kavya Iyer (ID: `694523e3e7624aff7c44994f`, Mobile: `916146505165`)
  - ... (81 more)

### 3. Velachery (ID: `694523e1e7624aff7c44993b`)
- **Total Customers: 86**
- **Sample Customer IDs:**
  - `694008cce260c5846226ad49`
  - `694008cde260c5846226ad50`
  - `694008cde260c5846226ad57`
  - `694008cde260c5846226ad5e`
  - `694523e3e7624aff7c449950`
  - ... (81 more)

### 4. Adyar (ID: `694523e1e7624aff7c44993c`)
- **Total Customers: 86**
- **Sample Customers:**
  - Vikram Singh (ID: `694008cce260c5846226ad4a`, Mobile: `9876543213`)
  - Riya Kapoor (ID: `694008cde260c5846226ad51`, Mobile: `9876543220`)
  - Varun Agarwal (ID: `694008cde260c5846226ad58`, Mobile: `9876543227`)
  - Divya Srinivasan (ID: `694008cde260c5846226ad5f`, Mobile: `9876543234`)
  - Priya Patel (ID: `694523e3e7624aff7c449951`, Mobile: `912452033678`)
  - ... (81 more)

### 5. Porur (ID: `694523e1e7624aff7c44993d`)
- **Total Customers: 86**
- **Sample Customer IDs:**
  - `694008cce260c5846226ad4b`
  - `694008cde260c5846226ad52`
  - `694008cde260c5846226ad59`
  - `694008cde260c5846226ad60`
  - `694523e3e7624aff7c449952`
  - ... (81 more)

### 6. Chrompet (ID: `694523e1e7624aff7c44993e`)
- **Total Customers: 85**
- **Sample Customer IDs:**
  - `694008cde260c5846226ad4c`
  - `694008cde260c5846226ad53`
  - `694008cde260c5846226ad5a`
  - `694523e2e7624aff7c44994c`
  - `694523e3e7624aff7c449953`
  - ... (80 more)

### 7. Tambaram (ID: `694523e1e7624aff7c44993f`)
- **Total Customers: 85**
- **Sample Customer IDs:**
  - `694008cde260c5846226ad4d`
  - `694008cde260c5846226ad54`
  - `694008cde260c5846226ad5b`
  - `694523e2e7624aff7c44994d`
  - `694523e3e7624aff7c449954`
  - ... (80 more)

---

## Verification

✅ **All customers have branch assignments** (0 customers with null branch_id)
✅ **Each branch has unique customers** (no duplicates across branches)
✅ **Total: 601 customers distributed across 7 branches**

---

## Expected Behavior in Customer Lifecycle Report

When you select each branch, you should see:

- **Anna Nagar**: 86 customers (including Rahul Kumar, Sneha Desai, Aditya Saxena, etc.)
- **Adyar**: 86 customers (including Vikram Singh, Riya Kapoor, Varun Agarwal, etc.)
- **T. Nagar**: 87 customers
- **Velachery**: 86 customers
- **Porur**: 86 customers
- **Chrompet**: 85 customers
- **Tambaram**: 85 customers

**Each branch should show DIFFERENT customers, not the same 601 customers!**

