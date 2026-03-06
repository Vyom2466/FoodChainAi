# FoodChain AI - Enhanced Version

A food waste management and inventory prediction system built with React.js frontend and Flask REST API backend.

## Features

### Core Features
- **Dashboard**: View statistics and trends for prepared, sold, and wasted items
- **Menu Management**: Add and manage menu items
- **Daily Entry**: Manual entry of daily sales and waste data
- **Analytics**: 30-day analytics with charts

### Enhanced Features (New)
1. **OTP Verification**: Secure login with OTP verification via email
2. **Seasonal/Festival-Based Predictions**: AI predictions that consider festivals and seasonal demand multipliers
3. **Inventory Purchase Tracking**: Track inventory purchases separately from sales
4. **AI Predictions Based on Inventory**: Predictions now use inventory purchase data (not sold products) to help users order inventory
5. **Billing System Integration**: Automatic data entry when bills are created - no manual entry needed

## Tech Stack

### Frontend
- React 18
- React Router DOM
- Axios for API calls
- Chart.js for data visualization
- Bootstrap 5 for UI

### Backend
- Flask (REST API)
- SQLite Database
- scikit-learn for ML predictions
- Flask-CORS for cross-origin requests

## Setup Instructions

### Prerequisites
- Python 3.8+
- Node.js 16+ and npm

### Backend Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Run the Flask API server:
```bash
python api.py
```

The API will run on `http://localhost:5000`

### Frontend Setup

1. Install Node.js dependencies:
```bash
npm install
```

2. Start the development server:
```bash
npm run dev
```

The frontend will run on `http://localhost:3000`

### Database Initialization

The database is automatically initialized when you first run `api.py`. It includes:
- Demo restaurant account: `demo_rest` / `demo123`
- Admin account: `admin` / `admin123`
- Sample menu items and historical data

## API Endpoints

### Authentication
- `POST /api/login` - Login (returns OTP requirement)
- `POST /api/verify-otp` - Verify OTP and complete login
- `POST /api/register` - Register new restaurant
- `POST /api/logout` - Logout

### Menu
- `GET /api/menu` - Get all menu items
- `POST /api/menu` - Add menu item
- `DELETE /api/menu/:id` - Deactivate menu item

### Daily Entry
- `GET /api/entry` - Get entry data and predictions
- `POST /api/entry` - Save daily record

### Billing Integration
- `POST /api/billing/create` - Create bill and auto-update daily records

### Inventory Purchases
- `GET /api/inventory/purchases` - Get purchase history
- `POST /api/inventory/purchases` - Record inventory purchase

### Analytics
- `GET /api/analytics` - Get 30-day analytics
- `GET /api/dashboard` - Get dashboard statistics

### Predictions
- `GET /api/predictions/:menu_item_id` - Get AI prediction for item (with optional `target_date` query param)

## Key Features Explained

### 1. OTP Verification
- Users must verify their identity with a 6-digit OTP sent to their email
- OTP expires after 10 minutes
- Currently uses console logging (in production, integrate with email service like SendGrid or AWS SES)

### 2. Seasonal Predictions
- System includes predefined festivals and seasons with demand multipliers
- Examples: Diwali (1.5x), Christmas (1.4x), Summer/Winter seasons
- Predictions automatically adjust based on upcoming festivals

### 3. Inventory-Based Predictions
- AI model now uses `inventory_purchases` table data instead of `sold_qty`
- This helps users know how much inventory to order
- Predictions consider:
  - Day of week
  - Weekend vs weekday
  - Month
  - Season/festival multipliers

### 4. Billing Integration
- When a bill is created, sold quantities are automatically added to `daily_records`
- Eliminates manual data entry for sales
- Multiple items can be added to a single bill

## Database Schema

New tables added:
- `inventory_purchases` - Track inventory purchases
- `billing_records` - Store billing information
- `otp_verifications` - OTP management
- `festivals_seasons` - Festival and season definitions with multipliers
- Updated `users` table with `email` and `phone` fields

## Development Notes

- OTP emails are currently logged to console. In production, integrate with an email service.
- The prediction model uses Random Forest Regressor with season/festival features
- CORS is enabled for development
- Session-based authentication (can be extended to JWT)

## Future Enhancements

- SMS OTP support
- Real-time notifications
- Multi-restaurant support with admin dashboard
- Export reports to PDF
- Mobile app support
- Advanced ML models (LSTM for time series)

## License

MIT



