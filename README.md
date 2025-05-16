# Cross-Platform Financial App

A cross-platform financial application allowing users to save and manage stock tickers, view in-depth company analyses by strategy (e.g., Piotroski F-Score, Net-Nets), interactive charts, real-time alerts, and curated news/events.

## Core Functionalities

### 1. Ticker Management
- Add, edit, delete, and organize saved stock tickers  
- Search with auto-complete suggestions

### 2. Detailed Ticker View
- **Company Overview:** Profile, sector, market cap, key ratios  
- **Strategy Analysis Sections:**  
  - Piotroski F-Score  
  - Net-Net valuation  
  - Additional metrics (e.g., P/E, ROE)

### 3. Interactive Charts
- Candlestick, line, volume overlays  
- Drawing tools, multiple timeframes, indicators (RSI, MACD)

### 4. Alerts & Notifications
- Criteria builder (price targets, indicator thresholds)  
- Delivery via SMS, email, or Discord webhooks

### 5. News & Events
- Company-specific news feed  
- Upcoming earnings and dividend dates  
- Customizable watchlists for news alerts

---

## Getting Started
1. **Clone the repo:**  
   ```bash
   git clone https://github.com/yourusername/financial-app.git
   ```
2. **Install dependencies:**  
   ```bash
   npm install    # for frontend
   pip install -r requirements.txt  # for backend
   ```
3. **Configure environment variables:**  
   - Create a `.env` file in the project root (see `.env.example`) and fill in your API keys and notification settings.
4. **Run the application:**  
   ```bash
   npm start      # frontend
   flask run      # backend
   ```

## Contributing
Contributions are welcome! Please open issues or submit pull requests for enhancements and bug fixes.

## License
This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.
