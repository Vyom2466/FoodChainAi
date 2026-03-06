# Troubleshooting Login and Registration Issues

## Common Issues and Solutions

### 1. "Cannot find module" errors
**Solution**: Run `npm install` to install all dependencies.

### 2. Login/Registration not working

#### Check if Backend is Running
- Make sure `python api.py` is running on port 5000
- You should see output like: `* Running on http://0.0.0.0:5000`

#### Check Browser Console
- Open Developer Tools (F12)
- Go to Console tab
- Look for any error messages
- Check Network tab to see if API requests are being made

#### Check Backend Console
- Look at the terminal where `python api.py` is running
- Check for any error messages
- OTP codes are printed here (e.g., "OTP for demo@example.com: 123456")

### 3. CORS Errors
If you see CORS errors in the browser console:
- Make sure `flask-cors` is installed: `pip install flask-cors`
- Restart the backend server after installing

### 4. Session Cookie Issues
- Clear browser cookies for localhost
- Try using incognito/private browsing mode
- Make sure both frontend (3000) and backend (5000) are running

### 5. OTP Not Received
- Check the backend terminal console for the OTP code
- OTP is printed like: `OTP for email@example.com: 123456`
- The OTP expires after 10 minutes

### 6. Database Issues
If you get database errors:
- Delete `foodchain_ai.db` file
- Restart the backend server to reinitialize the database

### 7. Testing the API Directly

You can test if the API is working using your browser's developer console:

```javascript
// Test login
fetch('http://localhost:5000/api/login', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  credentials: 'include',
  body: JSON.stringify({ username: 'demo_rest', password: 'demo123' })
})
.then(r => r.json())
.then(console.log)
```

### 8. Check API Response

In browser Developer Tools → Network tab:
- Look for `/api/login` or `/api/register` requests
- Click on them to see the request/response
- Check the Status code (200 = success, 400/401 = error)
- Check the Response tab for error messages

### 9. Common Error Messages

- **"Invalid username or password"**: Credentials are wrong or user doesn't exist
- **"Username already taken"**: Registration failed, username exists
- **"OTP has expired"**: OTP is older than 10 minutes
- **"Invalid OTP"**: Wrong OTP code entered
- **"Server error"**: Check backend console for details

### 10. Debug Steps

1. **Check Backend Logs**: Look at the terminal running `python api.py`
2. **Check Browser Console**: F12 → Console tab
3. **Check Network Requests**: F12 → Network tab → Filter by XHR/Fetch
4. **Verify Ports**: 
   - Frontend: http://localhost:3000
   - Backend: http://localhost:5000
5. **Restart Both Servers**: Stop and restart both frontend and backend

## Still Having Issues?

1. Check that all dependencies are installed:
   ```bash
   pip install -r requirements.txt
   npm install
   ```

2. Verify the backend is accessible:
   - Open http://localhost:5000/api/init in browser
   - Should return JSON: `{"message": "Database initialized"}`

3. Check browser console for specific error messages and share them for further debugging.



