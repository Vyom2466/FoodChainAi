import React, { useState, useEffect } from 'react'
import api from '../services/api'
import { Bar } from 'react-chartjs-2'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'

ChartJS.register(CategoryScale, LinearScale, BarElement, Title, Tooltip, Legend)

function Entry() {
  const [items, setItems] = useState([])
  const [records, setRecords] = useState([])
  const [predictions, setPredictions] = useState({})
  const [entrySummary, setEntrySummary] = useState([])
  const [loading, setLoading] = useState(true)
  const [formData, setFormData] = useState({
    date: new Date().toISOString().split('T')[0],
    menu_item_id: '',
    prepared_qty: '',
    sold_qty: '',
    wasted_qty: '',
    reason: ''
  })

  useEffect(() => {
    fetchEntryData()
  }, [])

  const fetchEntryData = async () => {
    try {
      const response = await api.get('/api/entry')
      setItems(response.data.items)
      setRecords(response.data.records)
      setPredictions(response.data.predictions)
      setEntrySummary(response.data.entry_summary)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching entry data:', error)
      setLoading(false)
    }
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    try {
      await api.post('/api/entry', formData)
      setFormData({
        date: new Date().toISOString().split('T')[0],
        menu_item_id: '',
        prepared_qty: '',
        sold_qty: '',
        wasted_qty: '',
        reason: ''
      })
      fetchEntryData()
      alert('Record saved successfully')
    } catch (error) {
      alert(error.response?.data?.error || 'Error saving record')
    }
  }

  if (loading) {
    return <div className="text-center">Loading...</div>
  }

  const chartData = {
    labels: entrySummary.map((e) => e.date),
    datasets: [
      {
        label: 'Prepared (units)',
        data: entrySummary.map((e) => e.prepared),
        backgroundColor: 'rgba(37, 99, 235, 0.6)'
      },
      {
        label: 'Sold (units)',
        data: entrySummary.map((e) => e.sold),
        backgroundColor: 'rgba(16, 185, 129, 0.6)'
      },
      {
        label: 'Waste (units)',
        data: entrySummary.map((e) => e.wasted),
        backgroundColor: 'rgba(239, 68, 68, 0.6)'
      }
    ]
  }

  return (
    <div>
      <h3 className="mb-3">Daily Sales & Waste Entry</h3>
      
      <div className="row g-3">
        <div className="col-lg-5">
          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">Add Record</h5>
              <form onSubmit={handleSubmit}>
                <div className="mb-2">
                  <label className="form-label">Date</label>
                  <input
                    type="date"
                    className="form-control"
                    value={formData.date}
                    onChange={(e) => setFormData({ ...formData, date: e.target.value })}
                    required
                  />
                </div>
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
                  <label className="form-label">Prepared Qty (units)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={formData.prepared_qty}
                    onChange={(e) => setFormData({ ...formData, prepared_qty: e.target.value })}
                    required
                  />
                </div>
                <div className="mb-2">
                  <label className="form-label">Sold Qty (units)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={formData.sold_qty}
                    onChange={(e) => setFormData({ ...formData, sold_qty: e.target.value })}
                    required
                  />
                </div>
                <div className="mb-2">
                  <label className="form-label">Wasted Qty (units)</label>
                  <input
                    type="number"
                    step="0.01"
                    className="form-control"
                    value={formData.wasted_qty}
                    onChange={(e) => setFormData({ ...formData, wasted_qty: e.target.value })}
                    required
                  />
                </div>
                <div className="mb-3">
                  <label className="form-label">Reason (optional)</label>
                  <textarea
                    className="form-control"
                    rows="2"
                    value={formData.reason}
                    onChange={(e) => setFormData({ ...formData, reason: e.target.value })}
                  ></textarea>
                </div>
                <button type="submit" className="btn btn-primary w-100">
                  Save Record
                </button>
              </form>
            </div>
          </div>

          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">AI Suggestions (Based on Inventory Purchases)</h5>
              {Object.keys(predictions).length > 0 ? (
                <div className="table-responsive">
                  <table className="table table-sm align-middle">
                    <thead>
                      <tr>
                        <th>Item</th>
                        <th>Predicted Purchase</th>
                        <th>Suggested Order</th>
                        <th>Season Factor</th>
                      </tr>
                    </thead>
                    <tbody>
                      {items.map((item) => {
                        const pred = predictions[item.id]
                        if (!pred) return null
                        return (
                          <tr key={item.id}>
                            <td>{item.name}</td>
                            <td>
                              {pred.predicted_demand}{' '}
                              <span className="small-muted">units</span>
                            </td>
                            <td>
                              <strong>{pred.suggested_purchase}</strong>{' '}
                              <span className="small-muted">units</span>
                            </td>
                            <td>
                              {pred.season_multiplier > 1 ? (
                                <span className="badge bg-warning">
                                  {pred.season_multiplier}x
                                </span>
                              ) : (
                                <span className="badge bg-secondary">1.0x</span>
                              )}
                            </td>
                          </tr>
                        )
                      })}
                    </tbody>
                  </table>
                  <small className="text-muted">
                    Predictions are based on inventory purchase history and seasonal factors.
                  </small>
                </div>
              ) : (
                <p className="text-muted mb-0">
                  Add inventory purchase records to see predictions.
                </p>
              )}
            </div>
          </div>
        </div>

        <div className="col-lg-7">
          <div className="card mb-3">
            <div className="card-body">
              <h5 className="card-title">Last 7 Days Summary</h5>
              <div className="chart-wrapper">
                {entrySummary.length > 0 ? (
                  <Bar
                    data={chartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: { y: { beginAtZero: true } }
                    }}
                  />
                ) : (
                  <p className="text-muted">No data available</p>
                )}
              </div>
            </div>
          </div>

          <div className="card">
            <div className="card-body">
              <h5 className="card-title">Recent Entries</h5>
              {records.length > 0 ? (
                <div className="table-responsive">
                  <table className="table table-sm table-striped align-middle">
                    <thead>
                      <tr>
                        <th>Date</th>
                        <th>Item</th>
                        <th>Prepared</th>
                        <th>Sold</th>
                        <th>Waste</th>
                      </tr>
                    </thead>
                    <tbody>
                      {records.map((r) => (
                        <tr key={r.id}>
                          <td>{r.date}</td>
                          <td>{r.name}</td>
                          <td>
                            {r.prepared_qty}{' '}
                            <span className="small-muted">units</span>
                          </td>
                          <td>
                            {r.sold_qty}{' '}
                            <span className="small-muted">units</span>
                          </td>
                          <td className="text-danger">
                            {r.wasted_qty}{' '}
                            <span className="small-muted">units</span>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              ) : (
                <p className="text-muted mb-0">No records yet.</p>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default Entry



