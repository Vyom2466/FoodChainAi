import React, { useState, useEffect } from 'react'
import api from '../services/api'

function InventoryPurchases() {
  const [items, setItems] = useState([])
  const [purchases, setPurchases] = useState([])
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState({
    menu_item_id: '',
    purchase_date: new Date().toISOString().split('T')[0],
    quantity: '',
    unit_price: '',
    supplier: '',
    notes: ''
  })

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    try {
      const [itemsRes, purchasesRes] = await Promise.all([
        api.get('/api/menu'),
        api.get('/api/inventory/purchases')
      ])
      setItems(itemsRes.data.items)
      setPurchases(purchasesRes.data.purchases)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching data:', error)
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/inventory/purchases', formData)
      setFormData({
        menu_item_id: '',
        purchase_date: new Date().toISOString().split('T')[0],
        quantity: '',
        unit_price: '',
        supplier: '',
        notes: ''
      })
      fetchData()
      alert('Inventory purchase recorded successfully')
    } catch (error) {
      alert(error.response?.data?.error || 'Error recording purchase')
    }
  }

  if (loading) {
    return <div className="text-center">Loading...</div>
  }

  return (
    <div>
      <h3 className="mb-4">Inventory Purchases</h3>
      
      <div className="alert alert-info">
        <strong>Note:</strong> Record your inventory purchases here. The AI prediction model 
        uses this data (not sold products) to suggest future inventory orders based on seasons 
        and festivals.
      </div>

      <div className="row">
        <div className="col-lg-5">
          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">Record Purchase</h5>
              <form onSubmit={handleSubmit}>
                <div className="mb-2">
                  <label className="form-label">Menu Item</label>
                  <select
                    className="form-select"
                    value={formData.menu_item_id}
                    onChange={(e) => setFormData({ ...formData, menu_item_id: e.target.value })}
                    required
                  >
                    <option value="">Select item</option>
                    {items.map((item) => (
                      <option key={item.id} value={item.id}>
                        {item.name}
                      </option>
                    ))}
                  </select>
                </div>
                <div className="mb-2">
                  <label className="form-label">Purchase Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={formData.purchase_date}
                    onChange={(e) => setFormData({ ...formData, purchase_date: e.target.value })}
                    required
                  />
                </div>
                <div className="mb-2">
                  <label className="form-label">Quantity</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={formData.quantity}
                    onChange={(e) => setFormData({ ...formData, quantity: e.target.value })}
                    required
                  />
                </div>
                <div className="mb-2">
                  <label className="form-label">Unit Price</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={formData.unit_price}
                    onChange={(e) => setFormData({ ...formData, unit_price: e.target.value })}
                  />
                </div>
                <div className="mb-2">
                  <label className="form-label">Supplier (optional)</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.supplier}
                    onChange={(e) => setFormData({ ...formData, supplier: e.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Notes (optional)</label>
                  <textarea
                    className="form-control"
                    rows="2"
                    value={formData.notes}
                    onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
                  ></textarea>
                </div>
                <button type="submit" className="btn btn-primary w-100">
                  Record Purchase
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="col-lg-7">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Recent Purchases</h5>
              {purchases.length > 0 ? (
                <div className="table-responsive">
                  <table className="table table-striped">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Item</th>
                        <th>Quantity</th>
                        <th>Unit Price</th>
                        <th>Total</th>
                        <th>Supplier</th>
                      </tr>
                    </thead>
                    <tbody>
                      {purchases.map((purchase) => (
                        <tr key={purchase.id}>
                          <td>{purchase.purchase_date}</td>
                          <td>{purchase.menu_item_name}</td>
                          <td>{purchase.quantity}</td>
                          <td>₹{purchase.unit_price || 0}</td>
                          <td>₹{((purchase.quantity || 0) * (purchase.unit_price || 0)).toFixed(2)}</td>
                          <td>{purchase.supplier || '-'}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-muted">No purchases recorded yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default InventoryPurchases



