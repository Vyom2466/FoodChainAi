import React, { useState, useEffect } from 'react'
import api from '../services/api'

function BillingIntegration() {
  const [items, setItems] = useState([])
  const [billItems, setBillItems] = useState([{ menu_item_id: '', quantity: '', unit_price: '' }])
  const [billDate, setBillDate] = useState(new Date().toISOString().split('T')[0])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchMenuItems()
  }, [])

  const fetchMenuItems = async () => {
    try {
      const response = await api.get('/api/menu')
      setItems(response.data.items)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching menu items:', error)
      setLoading(false)
    }
  }

  const addBillItem = () => {
    setBillItems([...billItems, { menu_item_id: '', quantity: '', unit_price: '' }])
  }

  const removeBillItem = (index) => {
    setBillItems(billItems.filter((_, i) => i !== index))
  }

  const updateBillItem = (index, field, value) => {
    const updated = [...billItems]
    updated[index][field] = value
    
    // Auto-fill price from menu item
    if (field === 'menu_item_id') {
      const item = items.find(i => i.id === parseInt(value))
      if (item && item.price) {
        updated[index].unit_price = item.price
      }
    }
    
    setBillItems(updated)
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    
    const validItems = billItems.filter(item => 
      item.menu_item_id && item.quantity && item.unit_price
    )
    
    if (validItems.length === 0) {
      alert('Please add at least one item to the bill')
      return
    }

    try {
      const response = await api.post('/api/billing/create', {
        bill_date: billDate,
        items: validItems.map(item => ({
          menu_item_id: parseInt(item.menu_item_id),
          quantity: parseFloat(item.quantity),
          unit_price: parseFloat(item.unit_price)
        }))
      })
      
      alert(`Bill created successfully! Total: ₹${response.data.total_amount.toFixed(2)}\nData entry has been automatically updated.`)
      
      // Reset form
      setBillItems([{ menu_item_id: '', quantity: '', unit_price: '' }])
      setBillDate(new Date().toISOString().split('T')[0])
    } catch (error) {
      alert(error.response?.data?.error || 'Error creating bill')
    }
  }

  const calculateTotal = () => {
    return billItems.reduce((sum, item) => {
      if (item.quantity && item.unit_price) {
        return sum + (parseFloat(item.quantity) * parseFloat(item.unit_price))
      }
      return sum
    }, 0)
  }

  if (loading) {
    return <div className="text-center">Loading...</div>
  }

  return (
    <div>
      <h3 className="mb-4">Billing System Integration</h3>
      
      <div className="alert alert-info">
        <strong>Note:</strong> When you create a bill here, the sold quantities are automatically 
        updated in the daily records. This eliminates the need for manual data entry.
      </div>

      <div className="card">
        <div className="card-body">
          <h5 className="card-title mb-4">Create Bill</h5>
          
          <form onSubmit={handleSubmit}>
            <div className="mb-3">
              <label className="form-label">Bill Date</label>
              <input
                type="date"
                className="form-control"
                value={billDate}
                onChange={(e) => setBillDate(e.target.value)}
                required
              />
            </div>

            <div className="mb-3">
              <label className="form-label">Bill Items</label>
              {billItems.map((item, index) => (
                <div key={index} className="row g-2 mb-2 align-items-end">
                  <div className="col-md-4">
                    <label className="form-label small">Menu Item</label>
                    <select
                      className="form-select form-select-sm"
                      value={item.menu_item_id}
                      onChange={(e) => updateBillItem(index, 'menu_item_id', e.target.value)}
                      required
                    >
                      <option value="">Select item</option>
                      {items.map((menuItem) => (
                        <option key={menuItem.id} value={menuItem.id}>
                          {menuItem.name} (₹{menuItem.price || 0})
                        </option>
                      ))}
                    </select>
                  </div>
                  <div className="col-md-2">
                    <label className="form-label small">Quantity</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-control form-control-sm"
                      value={item.quantity}
                      onChange={(e) => updateBillItem(index, 'quantity', e.target.value)}
                      required
                    />
                  </div>
                  <div className="col-md-2">
                    <label className="form-label small">Unit Price</label>
                    <input
                      type="number"
                      step="0.01"
                      className="form-control form-control-sm"
                      value={item.unit_price}
                      onChange={(e) => updateBillItem(index, 'unit_price', e.target.value)}
                      required
                    />
                  </div>
                  <div className="col-md-2">
                    <label className="form-label small">Subtotal</label>
                    <input
                      type="text"
                      className="form-control form-control-sm"
                      value={
                        item.quantity && item.unit_price
                          ? `₹${(parseFloat(item.quantity) * parseFloat(item.unit_price)).toFixed(2)}`
                          : '₹0.00'
                      }
                      readOnly
                    />
                  </div>
                  <div className="col-md-2">
                    {billItems.length > 1 && (
                      <button
                        type="button"
                        className="btn btn-danger btn-sm w-100"
                        onClick={() => removeBillItem(index)}
                      >
                        Remove
                      </button>
                    )}
                  </div>
                </div>
              ))}
              
              <button
                type="button"
                className="btn btn-secondary btn-sm"
                onClick={addBillItem}
              >
                + Add Item
              </button>
            </div>

            <div className="mb-3">
              <div className="card bg-light">
                <div className="card-body">
                  <div className="d-flex justify-content-between align-items-center">
                    <h5 className="mb-0">Total Amount:</h5>
                    <h4 className="mb-0 text-primary">₹{calculateTotal().toFixed(2)}</h4>
                  </div>
                </div>
              </div>
            </div>

            <button type="submit" className="btn btn-primary w-100">
              Create Bill & Update Records
            </button>
          </form>
        </div>
      </div>
    </div>
  )
}

export default BillingIntegration



