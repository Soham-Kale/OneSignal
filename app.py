from flask import Flask, request, render_template
import pandas as pd
import requests
import json
import os

app = Flask(__name__)
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

ONESIGNAL_APP_ID = "6f4012a8-c2b4-4e39-afcf-bcf4b29fabd9"
ONESIGNAL_API_KEY = "os_v2_app_n5abfkgcwrhdtl6pxt2lfh5l3hvd5qzyhpsuukek4qpyq34bkvnwjimrkctb7ebmcjl5gz5oi7z2ynuxxhfc6ngfc4w7csads2uy3ai"

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "❌ No file part in the request.", 400
    file = request.files['file']
    if file.filename == '':
        return "❌ No selected file.", 400
    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    try:
        df = pd.read_excel(filepath)
        df.columns = df.columns.str.strip()
        required_columns = ['Bo.', 'White-Username', 'White', 'Black-UserName', 'Black']
        for col in required_columns:
            if col not in df.columns:
                return f"❌ Missing required column: {col}", 400
        df = df[required_columns]
    except Exception as e:
        return f"❌ Error reading Excel file: {str(e)}", 400

    notifications_sent = 0
    errors = []

    for _, row in df.iterrows():
        board_number = str(row['Bo.']).strip()
        white_id = str(row['White-Username']).strip()
        black_id = str(row['Black-UserName']).strip()
        white_opponent = str(row['Black']).strip()
        black_opponent = str(row['White']).strip()

        users = [
            (white_id, white_opponent),
            (black_id, black_opponent)
        ]

        for user_id, opponent in users:
            if not user_id:
                continue

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {ONESIGNAL_API_KEY}"
            }

            payload = {
                'app_id': ONESIGNAL_APP_ID,
                'include_player_ids': ['114df19b-f623-437b-9de2-dd786ed96dd3'], 
                "contents": {
                    "en": f"Your match with {opponent} on board {board_number}."
                },
                "headings": {
                    "en": "Chess Match Update"
                },
                'category': 'card',
                'url': 'https://dev.uinsports.com/postcard/500'
            }

            try:
                response = requests.post(
                    "https://onesignal.com/api/v1/notifications",
                    headers=headers,
                    data=json.dumps(payload)
                )
                print("OneSignal Response:", response.status_code, response.json())
                response_data = response.json()

                if response.status_code == 200:
                    notifications_sent += 1
                    print(f"✅ Sent to {user_id}")
                else:
                    error_msg = response_data.get('errors', [response.text])[0]
                    errors.append(f"{user_id} → {response.status_code}: {error_msg}")
            except Exception as e:
                errors.append(f"{user_id} → Exception: {str(e)}")

    if errors:
        return f"✅ Notifications sent: {notifications_sent}.<br>❌ Errors:<br>" + "<br>".join(errors), 207
    return f"✅ Notifications sent to all unique players! Total: {notifications_sent}"

if __name__ == '__main__':
    app.run(debug=True)
