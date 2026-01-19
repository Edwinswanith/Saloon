import React, { useState, useEffect } from 'react'
import {
  FaEdit,
  FaTrash,
  FaPlus,
  FaArrowsAltV,
  FaChevronDown,
  FaCloudUploadAlt,
  FaSearch,
  FaTimes,
} from 'react-icons/fa'
import * as XLSX from 'xlsx'
import './Product.css'
import { showSuccess, showError, showWarning } from '../utils/toast.jsx'
import { useAuth } from '../contexts/AuthContext'
import { apiGet, apiPost, apiPut, apiDelete } from '../utils/api'
import Header from './Header'

const Product = () => {
  const { currentBranch } = useAuth()
  const [searchQuery, setSearchQuery] = useState('')
  const [productCategories, setProductCategories] = useState([])
  const [productsByCategory, setProductsByCategory] = useState({})
  const [expandedCategories, setExpandedCategories] = useState({})
  const [loading, setLoading] = useState(true)
  const [editingProduct, setEditingProduct] = useState(null)
  const [showProductModal, setShowProductModal] = useState(false)
  const [showCategoryModal, setShowCategoryModal] = useState(false)
  const [editingCategory, setEditingCategory] = useState(null)
  const [showImportModal, setShowImportModal] = useState(false)
  const [showCategoryDropdown, setShowCategoryDropdown] = useState(false)
  const [categoryFormData, setCategoryFormData] = useState({ name: '' })
  const [productFormData, setProductFormData] = useState({
    name: '',
    price: '',
    cost: '',
    stock_quantity: '',
    min_stock_level: '',
    sku: '',
    description: '',
    category_id: ''
  })

  useEffect(() => {
    fetchCategories()
  }, [])

  // Listen for branch changes
  useEffect(() => {
    const handleBranchChange = () => {
      console.log('[Product] Branch changed, refreshing categories...')
      fetchCategories()
      setProductsByCategory({}) // Clear products cache
    }
    
    window.addEventListener('branchChanged', handleBranchChange)
    return () => window.removeEventListener('branchChanged', handleBranchChange)
  }, [currentBranch])

  useEffect(() => {
    if (Object.keys(expandedCategories).length > 0) {
      Object.keys(expandedCategories).forEach((categoryId) => {
        if (expandedCategories[categoryId] && !productsByCategory[categoryId]) {
          fetchProductsForCategory(categoryId)
        }
      })
    }
  }, [expandedCategories])

  // Close dropdown when clicking outside
  useEffect(() => {
    const handleClickOutside = (event) => {
      if (showCategoryDropdown && !event.target.closest('.custom-dropdown-wrapper')) {
        setShowCategoryDropdown(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [showCategoryDropdown])

  const fetchCategories = async () => {
    try {
      setLoading(true)
      const response = await apiGet('/api/products/categories')
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const data = await response.json()

      // Backend now returns categories with counts included - no need for N API calls
      const categories = Array.isArray(data) ? data : (data.categories || [])
      console.log(`[Product] Loaded ${categories.length} categories with counts from backend`)

      setProductCategories(categories)
    } catch (error) {
      console.error('Error fetching product categories:', error)
      setProductCategories([])
    } finally {
      setLoading(false)
    }
  }

  const fetchProductsForCategory = async (categoryId) => {
    try {
      const response = await apiGet(`/api/products?category_id=${categoryId}`)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`)
      }
      const responseData = await response.json()
      console.log(`[Product] Products for category ${categoryId} response:`, responseData)
      
      // Backend returns {data: [...], pagination: {...}}
      const productsList = responseData.data || (Array.isArray(responseData) ? responseData : (responseData.products || []))
      console.log(`[Product] Loaded ${productsList.length} products for category ${categoryId}`)
      
      setProductsByCategory((prev) => ({
        ...prev,
        [categoryId]: productsList,
      }))
    } catch (error) {
      console.error(`[Product] Error fetching products for category ${categoryId}:`, error)
      setProductsByCategory((prev) => ({
        ...prev,
        [categoryId]: [],
      }))
    }
  }

  const toggleCategory = (categoryId) => {
    setExpandedCategories((prev) => ({
      ...prev,
      [categoryId]: !prev[categoryId],
    }))
  }

  const handleAddCategory = () => {
    setEditingCategory(null)
    setCategoryFormData({ name: '' })
    setShowCategoryModal(true)
  }

  const handleEditCategory = (category) => {
    setEditingCategory(category)
    setCategoryFormData({ name: category.name })
    setShowCategoryModal(true)
  }

  const handleSaveCategory = async () => {
    if (!categoryFormData.name.trim()) {
      showError('Category name is required')
      return
    }

    try {
      const url = editingCategory 
        ? `/api/products/categories/${editingCategory.id}`
        : `/api/products/categories`

      const response = editingCategory 
        ? await apiPut(url, {
            name: categoryFormData.name.trim(),
            display_order: editingCategory?.display_order || 0
          })
        : await apiPost(url, {
            name: categoryFormData.name.trim(),
            display_order: editingCategory?.display_order || 0
          })

      if (response.ok) {
        const data = await response.json()
        fetchCategories()
        setShowCategoryModal(false)
        setEditingCategory(null)
        setCategoryFormData({ name: '' })
        showSuccess(data.message || (editingCategory ? 'Category updated successfully!' : 'Category added successfully!'))
      } else {
        const errorData = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(errorData.error || `Failed to save category (Status: ${response.status})`)
      }
    } catch (error) {
      console.error('Error saving category:', error)
      showError(`Error saving category: ${error.message}`)
    }
  }

  const handleDeleteCategory = async (categoryId) => {
    if (!window.confirm('Are you sure you want to delete this product category?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/products/categories/${categoryId}`)
      if (response.ok) {
        fetchCategories()
        showSuccess('Category deleted successfully')
      } else {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(error.error || 'Failed to delete product category')
      }
    } catch (error) {
      console.error('Error deleting product category:', error)
      showError(`Error deleting product category: ${error.message}`)
    }
  }

  const handleDeleteProduct = async (productId, categoryId) => {
    if (!window.confirm('Are you sure you want to delete this product?')) {
      return
    }
    try {
      const response = await apiDelete(`/api/products/${productId}`)
      if (response.ok) {
        // Refresh products for this category
        fetchProductsForCategory(categoryId)
        fetchCategories() // To update count
      } else {
        showError('Failed to delete product')
      }
    } catch (error) {
      console.error('Error deleting product:', error)
      showError('Error deleting product')
    }
  }

  const handleEditProduct = (product) => {
    setEditingProduct(product)
    setProductFormData({
      name: product.name || '',
      price: product.price || '',
      cost: product.cost || '',
      stock_quantity: product.stock_quantity || '',
      min_stock_level: product.min_stock_level || '',
      sku: product.sku || '',
      description: product.description || '',
      category_id: product.category_id || product.categoryId || ''
    })
    setShowProductModal(true)
  }

  const handleSaveProduct = async () => {
    if (!productFormData.name.trim()) {
      showError('Product name is required')
      return
    }
    if (!productFormData.category_id) {
      showError('Category is required')
      return
    }
    
    try {
      const url = editingProduct 
        ? `/api/products/${editingProduct.id}`
        : `/api/products`

      const productData = {
        name: productFormData.name.trim(),
        price: parseFloat(productFormData.price) || 0,
        cost: parseFloat(productFormData.cost) || 0,
        stock_quantity: parseInt(productFormData.stock_quantity) || 0,  // Quantity is a number, keep parseInt
        min_stock_level: parseInt(productFormData.min_stock_level) || 0,  // Quantity is a number, keep parseInt
        sku: productFormData.sku || '',
        description: productFormData.description || '',
        category_id: productFormData.category_id,  // MongoDB ObjectId as string
        status: 'active'
      }

      const response = editingProduct 
        ? await apiPut(url, productData)
        : await apiPost(url, productData)

      if (response.ok) {
        const data = await response.json()
        if (productFormData.category_id) {
          fetchProductsForCategory(productFormData.category_id)
        }
        fetchCategories()
        setShowProductModal(false)
        setEditingProduct(null)
        setShowCategoryDropdown(false)
        setProductFormData({
          name: '',
          price: '',
          cost: '',
          stock_quantity: '',
          min_stock_level: '',
          sku: '',
          description: '',
          category_id: ''
        })
        showSuccess(data.message || (editingProduct ? 'Product updated successfully!' : 'Product added successfully!'))
      } else {
        const error = await response.json().catch(() => ({ error: 'Unknown error' }))
        showError(error.error || 'Failed to save product')
      }
    } catch (error) {
      console.error('Error saving product:', error)
      showError(`Error saving product: ${error.message}`)
    }
  }

  const parseFile = async (file) => {
    return new Promise((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = (e) => {
        try {
          const data = e.target.result
          let rows = []

          if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
            // Parse Excel file
            const workbook = XLSX.read(data, { type: 'binary' })
            const sheetName = workbook.SheetNames[0]
            const worksheet = workbook.Sheets[sheetName]
            rows = XLSX.utils.sheet_to_json(worksheet, { header: 1, defval: '' })
          } else {
            // Parse CSV file
            const text = data
            const lines = text.split('\n')
            rows = lines.map(line => {
              // Handle CSV with quoted values
              const values = []
              let current = ''
              let inQuotes = false
              for (let i = 0; i < line.length; i++) {
                const char = line[i]
                if (char === '"') {
                  inQuotes = !inQuotes
                } else if (char === ',' && !inQuotes) {
                  values.push(current.trim())
                  current = ''
                } else {
                  current += char
                }
              }
              values.push(current.trim())
              return values
            })
          }

          resolve(rows)
        } catch (error) {
          reject(error)
        }
      }
      reader.onerror = reject

      if (file.name.endsWith('.xlsx') || file.name.endsWith('.xls')) {
        reader.readAsBinaryString(file)
      } else {
        reader.readAsText(file)
      }
    })
  }

  const handleImportFile = async (e) => {
    const file = e.target.files[0]
    if (!file) return

    try {
      const rows = await parseFile(file)
      if (rows.length < 2) {
        showError('File must contain at least a header row and one data row')
        return
      }

      const headers = rows[0].map(h => String(h).trim().toLowerCase())
      
      // Find column indices
      const nameIdx = headers.findIndex(h => h.includes('name'))
      const categoryIdx = headers.findIndex(h => h.includes('category'))
      const priceIdx = headers.findIndex(h => h.includes('price'))
      const costIdx = headers.findIndex(h => h.includes('cost'))
      const stockIdx = headers.findIndex(h => h.includes('stock'))
      const minStockIdx = headers.findIndex(h => h.includes('min') && h.includes('stock'))
      const skuIdx = headers.findIndex(h => h.includes('sku'))
      const descriptionIdx = headers.findIndex(h => h.includes('description'))

      if (nameIdx === -1 || priceIdx === -1) {
        showError('File must contain Name and Price columns')
        return
      }

      let successCount = 0
      let errorCount = 0

      // Process data rows
      for (let i = 1; i < rows.length; i++) {
        if (!rows[i] || rows[i].length === 0) continue
        
        const values = rows[i]
        const productData = {
          name: String(values[nameIdx] || '').trim(),
          price: parseFloat(values[priceIdx] || '0'),
          cost: costIdx >= 0 ? parseFloat(values[costIdx] || '0') : 0,
          stock_quantity: stockIdx >= 0 ? parseInt(values[stockIdx] || '0') : 0,
          min_stock_level: minStockIdx >= 0 ? parseInt(values[minStockIdx] || '0') : 0,
          sku: skuIdx >= 0 ? String(values[skuIdx] || '').trim() : '',
          description: descriptionIdx >= 0 ? String(values[descriptionIdx] || '').trim() : '',
          category_id: null
        }

        // Find or create category
        if (categoryIdx >= 0 && values[categoryIdx]) {
          const categoryName = String(values[categoryIdx]).trim()
          const existingCategory = productCategories.find(c => c.name.toLowerCase() === categoryName.toLowerCase())
          if (existingCategory) {
            productData.category_id = existingCategory.id
          } else {
            // Create new category
            try {
              const categoryResponse = await apiPost('/api/products/categories', { name: categoryName })
              if (categoryResponse.ok) {
                const categoryData = await categoryResponse.json()
                productData.category_id = categoryData.id || categoryData.data?.id
                // Refresh categories
                fetchCategories()
              }
            } catch (err) {
              console.error(`Error creating category ${i}:`, err)
            }
          }
        }

        if (productData.name && productData.price > 0) {
          try {
            const response = await apiPost('/api/products', productData)
            if (response.ok) {
              successCount++
              // Refresh products if category was specified
              if (productData.category_id) {
                fetchProductsForCategory(productData.category_id)
              }
            } else {
              errorCount++
            }
          } catch (err) {
            console.error(`Error importing product ${i}:`, err)
            errorCount++
          }
        } else {
          errorCount++
        }
      }
      
      if (successCount > 0) {
        showSuccess(`Products imported: ${successCount} successful${errorCount > 0 ? `, ${errorCount} failed` : ''}`)
      } else {
        showError(`Products import failed: ${errorCount} errors`)
      }
      setShowImportModal(false)
      fetchCategories()
    } catch (error) {
      console.error('Error processing import file:', error)
      showError(`Error processing import file: ${error.message}`)
    }
  }

  const filteredCategories = productCategories.filter((cat) =>
    cat.name.toLowerCase().includes(searchQuery.toLowerCase())
  )

  return (
    <div className="product-page">
      <Header title="Products" />
      
      <div className="product-container">
        {/* Product Card */}
        <div className="product-card">
          {/* Search and Action Bar */}
          <div className="product-action-bar">
            <div className="search-wrapper">
              <FaSearch className="search-icon" />
              <input
                type="text"
                className="search-input"
                placeholder="Search products or categories..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
              />
              {searchQuery && (
                <button 
                  className="search-clear"
                  onClick={() => setSearchQuery('')}
                  title="Clear search"
                >
                  <FaTimes />
                </button>
              )}
            </div>
            <div className="action-buttons">
              <button className="action-btn import-btn" onClick={() => setShowImportModal(true)}>
                <FaCloudUploadAlt /> Import Products
              </button>
              <button className="action-btn add-btn" onClick={handleAddCategory}>
                <FaPlus /> Add Product Category
              </button>
            </div>
          </div>

          {/* Product Categories List */}
          <div className="product-categories-list">
            {loading ? (
              <div className="loading-message">Loading product categories...</div>
            ) : filteredCategories.length === 0 ? (
              <div className="empty-message">No product categories found</div>
            ) : (
              filteredCategories.map((category) => (
                <div key={category.id}>
                  <div className="product-category-row">
                    <div className="category-info">
                      <span className="category-name">
                        {category.name} ({category.count})
                      </span>
                    </div>
                    <div className="category-actions">
                      <button 
                        className="icon-btn edit-btn" 
                        title="Edit"
                        onClick={() => handleEditCategory(category)}
                      >
                        <FaEdit />
                      </button>
                      <button
                        className="icon-btn delete-btn"
                        title="Delete"
                        onClick={() => handleDeleteCategory(category.id)}
                      >
                        <FaTrash />
                      </button>
                      <button 
                        className="icon-btn add-btn" 
                        title="Add Product"
                        onClick={() => {
                          setEditingProduct(null)
                          setProductFormData({
                            name: '',
                            price: '',
                            cost: '',
                            stock_quantity: '',
                            min_stock_level: '',
                            sku: '',
                            description: '',
                            category_id: category.id
                          })
                          setShowProductModal(true)
                        }}
                      >
                        <FaPlus />
                      </button>
                      <button className="icon-btn reorder-btn" title="Reorder">
                        <FaArrowsAltV />
                      </button>
                      <button
                        className={`icon-btn expand-btn ${expandedCategories[category.id] ? 'expanded' : ''}`}
                        title="Expand"
                        onClick={() => toggleCategory(category.id)}
                      >
                        <FaChevronDown />
                      </button>
                    </div>
                  </div>
                  {expandedCategories[category.id] && productsByCategory[category.id] && (
                    <div className="products-list">
                      {productsByCategory[category.id].length === 0 ? (
                        <div className="empty-products">No products in this category</div>
                      ) : (
                        <div className="products-grid">
                          {productsByCategory[category.id].map((product) => (
                            <div key={product.id} className="product-item-card">
                              <div className="product-item-header">
                                <span className="product-item-name">{product.name}</span>
                              </div>
                              <div className="product-item-details">
                                <span className="product-item-price">₹{parseFloat(product.price).toLocaleString('en-IN')}</span>
                                {product.stock_quantity !== undefined && (
                                  <span className={`product-item-stock ${product.stock_quantity <= (product.min_stock_level || 0) ? 'low-stock' : ''}`}>
                                    Stock: {product.stock_quantity}
                                  </span>
                                )}
                              </div>
                              <div className="product-item-actions">
                                <button 
                                  className="icon-btn edit-btn" 
                                  title="Edit"
                                  onClick={() => handleEditProduct({ ...product, category_id: category.id })}
                                >
                                  <FaEdit />
                                </button>
                                <button
                                  className="icon-btn delete-btn"
                                  title="Delete"
                                  onClick={() => handleDeleteProduct(product.id, category.id)}
                                >
                                  <FaTrash />
                                </button>
                              </div>
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))
            )}
          </div>
        </div>
      </div>

      {/* Add/Edit Product Category Modal */}
      {showCategoryModal && (
        <div className="modal-overlay" onClick={() => setShowCategoryModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingCategory ? 'Edit Product Category' : 'Add Product Category'}</h2>
            <div className="form-group">
              <label>Category Name *</label>
              <input
                type="text"
                value={categoryFormData.name}
                onChange={(e) => setCategoryFormData({ ...categoryFormData, name: e.target.value })}
                placeholder="Enter category name"
                required
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowCategoryModal(false)}>Cancel</button>
              <button className="btn-save" onClick={handleSaveCategory}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Add/Edit Product Modal */}
      {showProductModal && (
        <div className="modal-overlay" onClick={() => {
          setShowProductModal(false)
          setShowCategoryDropdown(false)
        }}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>{editingProduct ? 'Edit Product' : 'Add Product'}</h2>
            <div className="form-group">
              <label>Product Name *</label>
              <input
                type="text"
                value={productFormData.name}
                onChange={(e) => setProductFormData({ ...productFormData, name: e.target.value })}
                placeholder="Enter product name"
                required
              />
            </div>
            <div className="form-group">
              <label>Category *</label>
              <div className="custom-dropdown-wrapper">
                <button
                  type="button"
                  className="custom-dropdown-toggle"
                  onClick={() => setShowCategoryDropdown(!showCategoryDropdown)}
                >
                  <span>
                    {productFormData.category_id 
                      ? productCategories.find(c => c.id === productFormData.category_id)?.name || 'Select Category'
                      : 'Select Category'
                    }
                  </span>
                  <FaChevronDown className={`dropdown-arrow ${showCategoryDropdown ? 'open' : ''}`} />
                </button>
                {showCategoryDropdown && (
                  <div className="custom-dropdown-menu">
                    <div
                      className={`custom-dropdown-option ${!productFormData.category_id ? 'selected' : ''}`}
                      onClick={() => {
                        setProductFormData({ ...productFormData, category_id: '' })
                        setShowCategoryDropdown(false)
                      }}
                    >
                      Select Category
                    </div>
                    {productCategories.map(cat => (
                      <div
                        key={cat.id}
                        className={`custom-dropdown-option ${productFormData.category_id === cat.id ? 'selected' : ''}`}
                        onClick={() => {
                          setProductFormData({ ...productFormData, category_id: cat.id })
                          setShowCategoryDropdown(false)
                        }}
                      >
                        {cat.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            <div className="form-group">
              <label>Price *</label>
              <input
                type="number"
                step="0.01"
                value={productFormData.price}
                onChange={(e) => setProductFormData({ ...productFormData, price: e.target.value })}
                placeholder="0.00"
                required
              />
            </div>
            <div className="form-group">
              <label>Cost</label>
              <input
                type="number"
                step="0.01"
                value={productFormData.cost}
                onChange={(e) => setProductFormData({ ...productFormData, cost: e.target.value })}
                placeholder="0.00"
              />
            </div>
            <div className="form-group">
              <label>Stock Quantity</label>
              <input
                type="number"
                value={productFormData.stock_quantity}
                onChange={(e) => setProductFormData({ ...productFormData, stock_quantity: e.target.value })}
                placeholder="0"
              />
            </div>
            <div className="form-group">
              <label>Min Stock Level</label>
              <input
                type="number"
                value={productFormData.min_stock_level}
                onChange={(e) => setProductFormData({ ...productFormData, min_stock_level: e.target.value })}
                placeholder="0"
              />
            </div>
            <div className="form-group">
              <label>SKU</label>
              <input
                type="text"
                value={productFormData.sku}
                onChange={(e) => setProductFormData({ ...productFormData, sku: e.target.value })}
                placeholder="Product SKU"
              />
            </div>
            <div className="form-group">
              <label>Description</label>
              <textarea
                value={productFormData.description}
                onChange={(e) => setProductFormData({ ...productFormData, description: e.target.value })}
                placeholder="Enter product description..."
                rows="3"
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => {
                setShowProductModal(false)
                setShowCategoryDropdown(false)
              }}>Cancel</button>
              <button className="btn-save" onClick={handleSaveProduct}>Save</button>
            </div>
          </div>
        </div>
      )}

      {/* Import Products Modal */}
      {showImportModal && (
        <div className="modal-overlay" onClick={() => setShowImportModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h2>Import Products</h2>
            <div className="import-instructions">
              <p>Upload a CSV or Excel file (.csv, .xlsx, .xls) with the following columns:</p>
              <ul>
                <li>Name (required)</li>
                <li>Category (optional - will create if doesn't exist)</li>
                <li>Price (required)</li>
                <li>Cost (optional)</li>
                <li>Stock Quantity (optional)</li>
                <li>Min Stock Level (optional)</li>
                <li>SKU (optional)</li>
                <li>Description (optional)</li>
              </ul>
            </div>
            <div className="form-group">
              <label>Select File</label>
              <input
                type="file"
                accept=".csv,.xlsx,.xls"
                onChange={handleImportFile}
              />
            </div>
            <div className="modal-actions">
              <button className="btn-cancel" onClick={() => setShowImportModal(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}

export default Product

