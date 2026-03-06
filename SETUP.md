# Quick Setup Guide

## Prerequisites
- Python 3.8+ installed
- Node.js 16+ and npm installed

## Step-by-Step Setup

### 1. Install Backend Dependencies
```bash
pip install -r requirements.txt
```

### 2. Install Frontend Dependencies
```bash
npm install
```

### 3. Start Backend Server
Open Terminal 1:
```bash
python api.py
```
The API will start on http://localhost:5000

**Note:** On first run, the database will be initialized with:
- Admin account: `admin` / `admin123`
- Demo restaurant: `demo_rest` / `demo123`
- Sample menu items and historical data

### 4. Start Frontend Server
Open Terminal 2:
```bash
npm run dev
```
The frontend will start on http://localhost:3000

### 5. Access the Application
- Open your browser and go to: http://localhost:3000
- Login with demo account: `demo_rest` / `demo123`
- Check the backend terminal (Terminal 1) for the OTP code
- Enter the OTP to complete login

## OTP Testing
During development, OTP codes are printed to the console. Check Terminal 1 (where `api.py` is running) for the OTP.

Example output:
```
OTP for demo@example.com: 123456
```

## Troubleshooting

### Port Already in Use
If port 5000 is busy:
- Change port in `api.py`: `app.run(debug=True, host='0.0.0.0', port=5001)`
- Update `vite.config.js` proxy target to `http://localhost:5001`

If port 3000 is busy:
- Vite will automatically use the next available port

### Database Issues
Delete `foodchain_ai.db` and restart `api.py` to reinitialize the database.

### CORS Errors
Make sure `flask-cors` is installed and the backend is running.

### Module Not Found Errors
- Backend: Make sure you're in a virtual environment with all packages installed
- Frontend: Run `npm install` again

## Production Deployment Notes

1. **Environment Variables**: Move sensitive data to `.env` file
2. **Secret Key**: Change `app.secret_key` in `api.py`
3. **Email Service**: Integrate real email service for OTP (SendGrid, AWS SES, etc.)
4. **Database**: Consider migrating to PostgreSQL for production
5. **HTTPS**: Use HTTPS in production
6. **Build**: Run `npm run build` to create production build



