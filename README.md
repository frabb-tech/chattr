# Lebanese Basketball League - Live Data Webapp

A real-time web application that displays live data from the Lebanese Basketball League (LBL) scraped from asia-basket.com.

## 🚀 Features

- **Live Data Updates**: Automatically scrapes and updates data every 5 minutes
- **Multiple Views**: 
  - Upcoming games
  - Recent results with scores
  - Current standings
  - Stats leaders (PPG, RPG, APG, SPG, BPG)
- **Beautiful UI**: Modern, responsive design with smooth animations
- **REST API**: Backend provides JSON endpoints for all data

## 📋 Prerequisites

- Python 3.8 or higher
- A modern web browser (Chrome, Firefox, Safari, Edge)

## 🛠️ Installation & Setup

### Step 1: Install Python Dependencies

```bash
# Install required Python packages
pip install flask flask-cors requests beautifulsoup4 lxml
```

Or using the requirements file:

```bash
pip install -r requirements.txt
```

### Step 2: Start the Backend Server

```bash
# Run the Python scraper/API server
python lbl_scraper.py
```

You should see:
```
==============================================================
Lebanese Basketball League Live Data Scraper
==============================================================

Fetching initial data...
[2025-XX-XX XX:XX:XX] Fetching data from https://www.asia-basket.com/Lebanon/basketball-League-LBL.aspx...
[2025-XX-XX XX:XX:XX] Data updated successfully!
  - Standings: 12 teams
  - Results: 20 games
  - Upcoming: 5 games

Background refresh started (every 5 minutes)

Starting API server on http://localhost:5000
==============================================================
```

### Step 3: Open the Web App

1. Open `lbl-live-connected.html` in your web browser
2. The app will automatically connect to the backend and display live data
3. You'll see a "Connected to Live Data" status indicator when successfully connected

## 📡 API Endpoints

The backend provides the following REST API endpoints:

- `GET /api/data` - Get all league data
- `GET /api/standings` - Get current standings
- `GET /api/results` - Get recent results
- `GET /api/upcoming` - Get upcoming games
- `GET /api/stats` - Get stats leaders
- `POST /api/refresh` - Force a data refresh

### Example API Usage

```bash
# Get all data
curl http://localhost:5000/api/data

# Get just standings
curl http://localhost:5000/api/standings

# Force refresh
curl -X POST http://localhost:5000/api/refresh
```

## 🎨 Features Breakdown

### Backend (lbl_scraper.py)

- **Web Scraping**: Uses BeautifulSoup to parse HTML from asia-basket.com
- **Auto-Refresh**: Background thread updates data every 5 minutes
- **Flask API**: Serves data via REST endpoints
- **CORS Enabled**: Allows frontend to access API from different origin
- **Error Handling**: Gracefully handles network errors and parsing issues

### Frontend (lbl-live-connected.html)

- **Live Updates**: Auto-refreshes from API every 5 minutes
- **Connection Status**: Shows real-time API connection status
- **Manual Refresh**: Button to force data refresh
- **Responsive Design**: Works on desktop, tablet, and mobile
- **Animations**: Smooth transitions and hover effects
- **No Dependencies**: Pure HTML/CSS/JavaScript (no frameworks needed)

## 🔧 Customization

### Change Refresh Interval

**Backend (lbl_scraper.py):**
```python
# Line ~220 - Change 300 to desired seconds
time.sleep(300)  # 300 seconds = 5 minutes
```

**Frontend (lbl-live-connected.html):**
```javascript
// Line ~680 - Change 300000 to desired milliseconds
setInterval(fetchLiveData, 300000);  // 300000 ms = 5 minutes
```

### Change API Port

**Backend:**
```python
# Line ~280 - Change port number
app.run(host='0.0.0.0', port=5000, debug=False)
```

**Frontend:**
```javascript
// Line ~530 - Update API URL
const API_BASE_URL = 'http://localhost:5000/api';
```

### Modify Color Scheme

Edit CSS variables in the HTML file:
```css
:root {
    --primary: #FF4500;      /* Main accent color */
    --secondary: #1a1a2e;    /* Dark secondary */
    --accent: #FFD700;       /* Gold accent */
    --bg-dark: #0f0f1e;      /* Background */
    --bg-card: #16162a;      /* Card background */
}
```

## 📊 Data Structure

The API returns data in the following format:

```json
{
  "standings": [
    {
      "rank": 1,
      "team": "Al Riyadi",
      "wins": 8,
      "losses": 0
    }
  ],
  "results": [
    {
      "date": "Dec 22",
      "homeTeam": "Antonine",
      "homeScore": 80,
      "awayTeam": "Beirut C.",
      "awayScore": 74
    }
  ],
  "upcoming": [
    {
      "date": "Dec 23, 2025",
      "homeTeam": "Al Riyadi",
      "awayTeam": "Homentmen",
      "time": "TBD"
    }
  ],
  "stats_leaders": {
    "ppg": [
      {
        "player": "Tray JACKSON",
        "team": "Beirut C.",
        "value": 29.8
      }
    ]
  },
  "last_updated": "2025-02-11T12:00:00"
}
```

## 🐛 Troubleshooting

### "Connection Error" / "Disconnected" Status

**Problem**: Frontend can't connect to backend

**Solutions**:
1. Make sure the backend is running (`python lbl_scraper.py`)
2. Check if port 5000 is available (not used by another app)
3. Verify the API_BASE_URL in the HTML matches your backend URL
4. Check browser console for CORS errors

### "Failed to load data" in Backend

**Problem**: Backend can't scrape asia-basket.com

**Solutions**:
1. Check your internet connection
2. Verify the website is accessible: https://www.asia-basket.com/Lebanon/basketball-League-LBL.aspx
3. Website structure may have changed - scraper might need updates
4. Check if you're being rate-limited (wait a few minutes)

### Empty Data / No Results

**Problem**: Backend runs but returns empty arrays

**Solutions**:
1. The website structure may have changed
2. Check the scraper parsing logic in `lbl_scraper.py`
3. Try accessing the website directly to see if data is available
4. Look at backend console logs for parsing errors

## 🚀 Deployment Options

### Option 1: Local Network

Keep the setup as-is. Access from other devices on your network:
```
http://[YOUR-LOCAL-IP]:5000
```

### Option 2: Deploy Backend to Cloud

**Using Heroku:**
1. Add `Procfile`: `web: python lbl_scraper.py`
2. Deploy to Heroku
3. Update frontend `API_BASE_URL` to your Heroku URL

**Using Railway/Render:**
1. Push code to GitHub
2. Connect repository to Railway/Render
3. Set start command: `python lbl_scraper.py`
4. Update frontend API URL

### Option 3: Static Frontend + Serverless Backend

- Host HTML on Netlify/Vercel
- Deploy backend as AWS Lambda or Google Cloud Function
- Use API Gateway to expose endpoints

## 📝 Notes

- **Rate Limiting**: The scraper is set to refresh every 5 minutes to avoid overloading asia-basket.com
- **Data Accuracy**: Data is as accurate as the source website
- **Real-time**: Data is "near real-time" - updated every 5 minutes, not instant
- **Dependencies**: Minimal dependencies for easier maintenance

## 📄 License

This project is for educational purposes. Respect asia-basket.com's terms of service and don't overload their servers.

## 🤝 Contributing

To improve the scraper:
1. Update parsing logic in `scrape_*` functions
2. Add new endpoints in the Flask app
3. Add new UI sections in the frontend
4. Enhance error handling

## 📞 Support

If you encounter issues:
1. Check the troubleshooting section above
2. Look at backend console logs
3. Check browser console for frontend errors
4. Verify the source website hasn't changed structure

---

**Enjoy your live Lebanese Basketball League webapp! 🏀**
