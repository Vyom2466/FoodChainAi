import React, { useState, useEffect } from 'react'
import api from '../services/api'
import { Line, Bar } from 'react-chartjs-2'
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

function Analytics() {
  const [daily, setDaily] = useState([])
  const [topWaste, setTopWaste] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchAnalytics()
  }, [])

  const fetchAnalytics = async () => {
    try {
      const response = await api.get('/api/analytics')
      setDaily(response.data.daily)
      setTopWaste(response.data.top_waste)
      setLoading(false)
    } catch (error) {
      console.error('Error fetching analytics:', error)
      setLoading(false)
    }
  }

  if (loading) {
    return <div className="text-center">Loading...</div>
  }

  const dailyChartData = {
    labels: daily.map((d) => d.date),
    datasets: [
      {
        label: 'Prepared (units)',
        data: daily.map((d) => d.prepared),
        borderColor: 'rgb(37, 99, 235)',
        backgroundColor: 'rgba(37, 99, 235, 0.1)',
        tension: 0.25
      },
      {
        label: 'Sold (units)',
        data: daily.map((d) => d.sold),
        borderColor: 'rgb(16, 185, 129)',
        backgroundColor: 'rgba(16, 185, 129, 0.1)',
        tension: 0.25
      },
      {
        label: 'Waste (units)',
        data: daily.map((d) => d.wasted),
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
      <h3 className="mb-4">Analytics (Last 30 Days)</h3>

      <div className="row g-3">
        <div className="col-lg-12">
          <div className="card">
            <div className="card-body">
              <h5 className="card-title mb-3">Daily Trends</h5>
              <div className="chart-wrapper">
                {daily.length > 0 ? (
                  <Line
                    data={dailyChartData}
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
        </div>

        {topWaste.length > 0 && (
          <div className="col-lg-12">
            <div className="card">
              <div className="card-body">
                <h5 className="card-title mb-3">Top Waste Items</h5>
                <div className="chart-wrapper">
                  <Bar
                    data={wasteChartData}
                    options={{
                      responsive: true,
                      maintainAspectRatio: false,
                      scales: { y: { beginAtZero: true } }
                    }}
                  />
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  )
}

export default Analytics



