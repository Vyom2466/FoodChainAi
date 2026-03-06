import React, { useState, useEffect } from 'react'
import api from '../services/api'
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
} from 'chart.js'
import { Line, Bar } from 'react-chartjs-2'

ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  Title,
  Tooltip,
  Legend
)

function Dashboard() {
  const [stats, setStats] = useState({ prepared: 0, sold: 0, wasted: 0 })
  const [trendData, setTrendData] = useState([])
  const [topWaste, setTopWaste] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchDashboardData()
  }, [])

  const fetchDashboardData = async () => {
    try {
      const response = await api.get('/api/dashboard')
      setStats(response.data.stats)
      setTrendData(response.data.trend_data)
      setTopWaste(response.data.top_waste)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching dashboard data:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center">Loading...</div>
  }

  const chartData = {
    labels: trendData.map((d) => d.date),
    datasets: [
      {
        label: 'Prepared (units)',
        data: trendData.map((d) => d.prepared),
        borderColor: 'rgb(37, 99, 235)',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        tension: 0.25
      },
      {
        label: 'Sold (units)',
        data: trendData.map((d) => d.sold),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.25
      },
      {
        label: 'Waste (units)',
        data: trendData.map((d) => d.wasted),
        borderColor: 'rgb(239, 68, 68)',
        backgroundColor: 'rgba(239, 68, 68, 0.1)',
        tension: 0.25
      }
    ]
  }

  const wasteChartData = {
    labels: topWaste.map((w) => w.name),
    datasets: [
      {
        label: 'Waste (units)',
        data: topWaste.map((w) => w.wasted),
        backgroundColor: 'rgba(239, 68, 68, 0.6)'
      }
    ]
  }

  return (
    <div>
      <h3 className="mb-4">Dashboard</h3>
      
      <div className="row g-3 mb-4">
        <div className="col-md-4">
          <div className="card p-3">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <p className="stat-label mb-1">Prepared (last 7 days)</p>
                <div className="stat-value">
                  {stats.prepared} <span className="small-muted">units</span>
                </div>
              </div>
              <div className="kpi-badge">Total</div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card p-3">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <p className="stat-label mb-1">Sold (last 7 days)</p>
                <div className="stat-value text-success">
                  {stats.sold} <span className="small-muted">units</span>
                </div>
              </div>
              <div className="kpi-badge">Total</div>
            </div>
          </div>
        </div>
        <div className="col-md-4">
          <div className="card p-3">
            <div className="d-flex justify-content-between align-items-center">
              <div>
                <p className="stat-label mb-1">Wasted (last 7 days)</p>
                <div className="stat-value text-danger">
                  {stats.wasted} <span className="small-muted">units</span>
                </div>
              </div>
              <div className="kpi-badge">Total</div>
            </div>
          </div>
        </div>
      </div>

      <div className="row g-3">
        <div className="col-lg-12">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title mb-3">7-Day Trend (All items combined)</h5>
              <div className="chart-wrapper">
                {trendData.length > 0 ? (
                  <Line data={chartData} options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true } }
                  }} />
                ) : (
                  <p className="text-muted">No data available</p>
                )}
              </div>
            </div>
          </div>
        </div>
        
        {topWaste.length > 0 && (
          <div className="col-lg-12">
            <div className="card">
              <div className="card-body">
                <h5 className="card-title mb-3">Top Waste Items</h5>
                <div className="chart-wrapper">
                  <Bar data={wasteChartData} options={{
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: { y: { beginAtZero: true } }
                  }} />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Dashboard



