# Quick Start Guide - Using New UI Components

## 🎯 Quick Reference

### 1. Toast Notifications (Instead of alert)

```javascript
import { showSuccess, showError, showWarning, showInfo } from '../utils/toast'

// Success
showSuccess('Operation completed successfully!')

// Error
showError('Something went wrong. Please try again.')

// Warning
showWarning('Please fill all required fields')

// Info
showInfo('Processing your request...')
```

---

### 2. Ant Design Modal (Instead of custom modal)

```javascript
import { Modal, Button } from 'antd'

<Modal
  title="Your Modal Title"
  open={showModal}
  onCancel={() => setShowModal(false)}
  footer={[
    <Button key="cancel" onClick={() => setShowModal(false)}>
      Cancel
    </Button>,
    <Button key="submit" type="primary" onClick={handleSubmit}>
      Save
    </Button>,
  ]}
>
  {/* Your form content here */}
</Modal>
```

---

### 3. Ant Design Form

```javascript
import { Form, Input, Select, Button } from 'antd'

<Form layout="vertical">
  <Form.Item label="Name" required>
    <Input placeholder="Enter name" />
  </Form.Item>
  
  <Form.Item label="Status">
    <Select>
      <Select.Option value="active">Active</Select.Option>
      <Select.Option value="inactive">Inactive</Select.Option>
    </Select>
  </Form.Item>
</Form>
```

---

### 4. Ant Design DatePicker (Instead of HTML date input)

```javascript
import { DatePicker } from 'antd'
import dayjs from 'dayjs'

<DatePicker
  format="DD/MM/YYYY"
  value={date ? dayjs(date) : null}
  onChange={(date) => {
    setDate(date ? date.format('YYYY-MM-DD') : '')
  }}
  style={{ width: '100%' }}
/>
```

---

### 5. Ant Design Table (For future use)

```javascript
import { Table } from 'antd'

const columns = [
  { title: 'Name', dataIndex: 'name', key: 'name', sorter: true },
  { title: 'Mobile', dataIndex: 'mobile', key: 'mobile' },
  {
    title: 'Actions',
    key: 'actions',
    render: (_, record) => (
      <>
        <Button onClick={() => handleEdit(record)}>Edit</Button>
        <Button danger onClick={() => handleDelete(record)}>Delete</Button>
      </>
    ),
  },
]

<Table
  columns={columns}
  dataSource={data}
  rowKey="id"
  pagination={{ pageSize: 10 }}
/>
```

---

## 📝 Migration Checklist

When migrating a component:

### Step 1: Add Imports
```javascript
import { Modal, Input, Select, Button, Form, DatePicker } from 'antd'
import { showSuccess, showError, showWarning } from '../utils/toast'
import dayjs from 'dayjs'
```

### Step 2: Replace alert() Calls
- Find all `alert(...)` calls
- Replace with appropriate toast function

### Step 3: Replace Custom Modal
- Remove `.modal-overlay` and `.modal-content` divs
- Use `<Modal>` component
- Set `open`, `onCancel`, `title`, `footer` props

### Step 4: Replace Form Inputs
- HTML `<input>` → Ant Design `<Input>`
- HTML `<select>` → Ant Design `<Select>`
- HTML `<input type="date">` → Ant Design `<DatePicker>`
- HTML `<textarea>` → Ant Design `<TextArea>`

### Step 5: Use Form Layout
- Wrap inputs in `<Form layout="vertical">`
- Use `<Form.Item label="..." required>` for each field

### Step 6: Test
- Test modal open/close
- Test form submission
- Test validation
- Test keyboard shortcuts (ESC)

---

## 🎨 Common Patterns

### Confirmation Dialog
```javascript
import { Modal } from 'antd'

const handleDelete = (id) => {
  Modal.confirm({
    title: 'Confirm Deletion',
    content: 'Are you sure you want to delete this item?',
    okText: 'Yes, Delete',
    okType: 'danger',
    cancelText: 'Cancel',
    onOk: async () => {
      // Delete logic here
      showSuccess('Item deleted successfully')
    },
  })
}
```

### Loading State
```javascript
import { Spin } from 'antd'

{loading ? (
  <Spin tip="Loading..." size="large" />
) : (
  // Your content here
)}
```

### Empty State
```javascript
import { Empty } from 'antd'

{data.length === 0 ? (
  <Empty description="No data available" />
) : (
  // Your data display
)}
```

---

## 🚫 What NOT to Do

❌ Don't use `alert()` anymore  
✅ Use `showSuccess()`, `showError()`, etc.

❌ Don't create custom modals with `.modal-overlay`  
✅ Use Ant Design `<Modal>`

❌ Don't use HTML `<input type="date">`  
✅ Use Ant Design `<DatePicker>`

❌ Don't mix old and new patterns in same component  
✅ Complete migration for each component

❌ Don't forget to test after migration  
✅ Always test thoroughly

---

## 📖 Example: Complete Component Migration

See `frontend/src/components/LeadManagement.jsx` for a complete example of:
- ✅ Toast notifications instead of alert()
- ✅ Ant Design Modal instead of custom modal
- ✅ Ant Design Form with proper layout
- ✅ Ant Design Input, Select, DatePicker, TextArea
- ✅ Proper button styling and actions

---

## 🔗 Useful Links

- **Ant Design Components**: https://ant.design/components/overview/
- **Toast Docs**: https://react-hot-toast.com/
- **Project Documentation**: See `UI_UX_UPGRADE_IMPLEMENTATION.md`
- **Phase 1 Summary**: See `UI_UX_PHASE1_COMPLETE.md`

---

**Last Updated**: December 29, 2025  
**Status**: Ready for use ✅

