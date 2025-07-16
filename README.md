# OneSignal Push Notification Sender (Excel Upload)

This app lets you upload an Excel file of OneSignal Player IDs and send a push notification to all users listed.

## Features
- Upload `.xlsx` file with Player IDs (first column)
- Sends push notification to all IDs via OneSignal REST API
- Simple web interface

## Setup
1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```
2. **Configure OneSignal keys:**
   - Open `app.py`
   - Replace `YOUR_ONESIGNAL_APP_ID` and `YOUR_REST_API_KEY` with your actual OneSignal App ID and REST API Key.

3. **Run the app:**
   ```bash
   python app.py
   ```
4. **Open in browser:**
   - Go to [http://localhost:5000](http://localhost:5000)
   - Upload your Excel file and send notifications

## Excel File Format
- First column: Player IDs (no header required, but allowed)
- Example:
  | Player ID         |
  |------------------|
  | 123abc456def789  |
  | abc123xyz456qwe  |

## Files
- `app.py` — Flask backend
- `templates/upload.html` — Upload form (auto-created if missing)
- `requirements.txt` — Dependencies
- `Round1_chessResultsList.xlsx` — Sample Excel file

## Notes
- Make sure your OneSignal account is set up and you have valid Player IDs.
- For large lists, OneSignal may have rate limits. 