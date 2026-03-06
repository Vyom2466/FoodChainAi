import React, { useState, useEffect } from 'react'
import api from '../services/api'

function Menu() {
  const [items, setItems] = useState([])
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState({
    name: '',
    category: '',
    price: '',
    shelf_life_days: ''
  })

  useEffect(() => {
    fetchMenu()
  }, [])

  const fetchMenu = async () => {
    try {
      const response = await api.get('/api/menu')
      setItems(response.data.items)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching menu:', error)
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/menu', formData)
      setFormData({ name: '', category: '', price: '', shelf_life_days: '' })
      fetchMenu()
      alert('Menu item added successfully')
    } catch (error) {
      alert(error.response?.data?.error || 'Error adding menu item')
    }
  }

  const handleDeactivate = async (itemId) => {
    if (window.confirm('Are you sure you want to deactivate this item?')) {
      try {
        await api.delete(`/api/menu/${itemId}`)
        fetchMenu()
        alert('Item deactivated')
      } catch (error) {
        alert('Error deactivating item')
      }
    }
  }

  if (loading) {
    return <div className="text-center">Loading...</div>
  }

  return (
    <div>
      <h3 className="mb-4">Menu Management</h3>

      <div className="row">
        <div className="col-lg-5">
          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">Add Menu Item</h5>
              <form onSubmit={handleSubmit}>
                <div className="mb-2">
                  <label className="form-label">Item Name</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.name}
                    onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                    required
                  />
                </div>
                <div className="mb-2">
                  <label className="form-label">Category</label>
                  <input
                    type="text"
                    className="form-control"
                    value={formData.category}
                    onChange={(e) => setFormData({ ...formData, category: e.target.value })}
                  />
                </div>
                <div className="mb-2">
                  <label className="form-label">Price</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={formData.price}
                    onChange={(e) => setFormData({ ...formData, price: e.target.value })}
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Shelf Life (days)</label>
                  <input
                    type="number"
                    className="form-control"
                    value={formData.shelf_life_days}
                    onChange={(e) => setFormData({ ...formData, shelf_life_days: e.target.value })}
                  />
                </div>
                <button type="submit" className="btn btn-primary w-100">
                  Add Item
                </button>
              </form>
            </div>
          </div>
        </div>

        <div className="col-lg-7">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Menu Items</h5>
              {items.length > 0 ? (
                <div className="table-responsive">
                  <table className="table table-striped">
                    <thead>
                      <tr>
                        <th>Name</th>
                        <th>Category</th>
                        <th>Price</th>
                        <th>Shelf Life</th>
                        <th>Actions</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item) => (
                        <tr key={item.id}>
                          <td>{item.name}</td>
                          <td>{item.category || '-'}</td>
                          <td>₹{item.price || 0}</td>
                          <td>{item.shelf_life_days || 0} days</td>
                          <td>
                            <button
                              className="btn btn-sm btn-danger"
                              onClick={() => handleDeactivate(item.id)}
                            >
                              Deactivate
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-muted">No menu items yet. Add your first item!</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Menu



