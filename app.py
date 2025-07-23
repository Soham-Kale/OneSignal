from flask import Flask, request, render_template, redirect, url_for, jsonify
from flask_cors import CORS
import pandas as pd
import requests
import json
import os

app = Flask(__name__)
CORS(app)

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

IN_APP_STORAGE = "in_app_notifications.json"
if not os.path.exists(IN_APP_STORAGE):
    with open(IN_APP_STORAGE, 'w') as f:
        json.dump([], f)

# OneSignal credentials
ONESIGNAL_APP_ID = "6f4012a8-c2b4-4e39-afcf-bcf4b29fabd9"
ONESIGNAL_API_KEY = "os_v2_app_n5abfkgcwrhdtl6pxt2lfh5l3hvd5qzyhpsuukek4qpyq34bkvnwjimrkctb7ebmcjl5gz5oi7z2ynuxxhfc6ngfc4w7csads2uy3ai"

@app.route('/')
def index():
    return render_template('upload.html')

@app.route('/api/upload', methods=['POST'])
def upload():
    if 'file' not in request.files:
        return "❌ No file part in the request.", 400
    file = request.files['file']
    if file.filename == '':
        return "❌ No selected file.", 400

    filepath = os.path.join(UPLOAD_FOLDER, file.filename)
    file.save(filepath)

    df_all = pd.read_excel(filepath, header=None)

    # Detect round number and start row
    round_number = "Unknown"
    start_row_index = None
    for i in range(len(df_all)):
        row_values = [str(cell) for cell in df_all.iloc[i].values if pd.notnull(cell)]
        if any("Bo." in val for val in row_values):
            start_row_index = i
            break
        for val in row_values:
            if "Round" in val:
                round_number = val.strip()

    if start_row_index is None:
        return "❌ 'Bo.' header not found in Excel file.", 400

    df = pd.read_excel(filepath, skiprows=start_row_index)
    df.columns = df.columns.str.strip()

    # Detect 'Group' columns (usually 'Group' and 'Group.1')
    group_cols = [col for col in df.columns if col.startswith("Group")]

    if len(group_cols) != 2 or not all(col in df.columns for col in ['Bo.', 'White', 'Black']):
        return "❌ Required columns missing or 'Group' columns not found.", 400

    # Rename both Group columns
    df = df.rename(columns={
        group_cols[0]: 'White-UserName',
        group_cols[1]: 'Black-UserName'
    })

    required_columns = ['Bo.', 'White-UserName', 'White', 'Black-UserName', 'Black']
    df = df[required_columns]

    notifications_sent = 0
    errors = []

    with open(IN_APP_STORAGE, 'r') as f:
        in_app_data = json.load(f)

    for _, row in df.iterrows():
        board_number = str(row['Bo.']).strip()
        white_id = str(row['White-UserName']).strip()
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

            message = f"{round_number} | Your match with {opponent} on board {board_number}."

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {ONESIGNAL_API_KEY}"
            }

            payload = {
                'app_id': ONESIGNAL_APP_ID,
                'include_player_ids': ['114df19b-f623-437b-9de2-dd786ed96dd3'],  # Replace with actual player ID logic
                "contents": {"en": message},
                "headings": {"en": "Chess Match Update"},
                'category': 'card',
                'url': 'https://dev.uinsports.com/postcard/500'
            }

            try:
                response = requests.post("https://onesignal.com/api/v1/notifications",
                                         headers=headers,
                                         data=json.dumps(payload))
                res_data = response.json()

                if response.status_code == 200:
                    notifications_sent += 1
                else:
                    errors.append(f"{user_id}: {res_data.get('errors', [response.text])[0]}")
            except Exception as e:
                errors.append(f"{user_id}: Exception - {str(e)}")

            # In-app notification save
            in_app_data.append({
                "user_id": user_id,
                "message": message,
                "board": board_number,
                "opponent": opponent
            })

    with open(IN_APP_STORAGE, 'w') as f:
        json.dump(in_app_data, f, indent=2)

    if errors:
        return f"✅ Sent: {notifications_sent}<br>❌ Errors:<br>" + "<br>".join(errors), 207
    return redirect(url_for('get_notifications'))

@app.route('/notifications')
def get_notifications():
    url = f"https://onesignal.com/api/v1/notifications?app_id={ONESIGNAL_APP_ID}"
    headers = {
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
        "Content-Type": "application/json"
    }

    try:
        response = requests.get(url, headers=headers)
        data = response.json()
        notifications = data.get("notifications", [])

        with open(IN_APP_STORAGE, "r") as f:
            notifications_data = json.load(f)

        parsed_notifications = []
        for n in notifications_data:
            parsed_notifications.append({
                "user_id": n.get("user_id", "Unknown"),
                "message": n.get("message", "No message"),
                "board": n.get("board", ""),
                "opponent": n.get("opponent", ""),
                "is_read": n.get("is_read", False)
            })

        return render_template("notifications.html", notifications=parsed_notifications)

    except Exception as e:
        return f"❌ Error reading in_app_notifications.json: {str(e)}", 500

@app.route("/send_notification", methods=["POST"])
def send_notification():
    message = request.json.get("message", "Default message")

    headers = {
        "Content-Type": "application/json; charset=utf-8",
        "Authorization": f"Basic {ONESIGNAL_API_KEY}",
    }

    payload = {
        "app_id": ONESIGNAL_APP_ID,
        "filters": [{"field": "tag", "key": "user_id", "relation": "=", "value": "123"}],
        'include_player_ids': ['114df19b-f623-437b-9de2-dd786ed96dd3'],
        "contents": {"en": message},
        "data": {"custom": "data"},
        "target_channel": "in_app",
    }

    response = requests.post("https://onesignal.com/api/v1/notifications",
        headers=headers,
        data=json.dumps(payload)
    )

    if response.status_code == 200:
        return jsonify({"success": True})
    else:
        return jsonify({"error": response.json()}), 500

if __name__ == '__main__':
    app.run(debug=True)
