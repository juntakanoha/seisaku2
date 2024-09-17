from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime, timedelta
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # セッション用の秘密鍵を設定


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/reserve", methods=["GET", "POST"])
def reserve():
    if request.method == "POST":
        name = request.form["name"]
        date = request.form["date"]
        time = request.form["time"]
        contact = request.form["contact"]
        child_name = request.form["child_name"]
        child_age = request.form["child_age"]
        symptoms = request.form["symptoms"]

        # 入力値の検証
        if not all([name, date, time, contact, child_name, child_age, symptoms]):
            flash('すべての項目を入力してください。', 'error')
            return redirect(url_for('reserve'))

        # 日付と時間の検証
        try:
            datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            flash('無効な日付または時間です。', 'error')
            return redirect(url_for('reserve'))
# 予約時間の重複チェック
        if is_time_slot_available(date, time):
            conn = sqlite3.connect("pediatric_reservations.db")
            c = conn.cursor()
            c.execute(
                "INSERT INTO reservations (name, date, time, contact, child_name, child_age, symptoms) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (name, date, time, contact, child_name, child_age, symptoms),
            )
            conn.commit()
            conn.close()

            send_line_notify(f"小児科予約が完了しました！\n保護者名: {name}\n子供の名前: {child_name}\n子供の年齢: {child_age}\n日付: {date}\n時間: {time}\n症状: {symptoms}\n連絡先: {contact}")

            flash('予約が完了しました！', 'success')
            return redirect(url_for('index'))
        else:
            flash('指定された時間は既に予約されています。別の時間を選択してください。', 'error')
            return redirect(url_for('reserve'))

    return render_template("reserve.html")


def is_time_slot_available(date, time):
    conn = sqlite3.connect("pediatric_reservations.db")
    c = conn.cursor()

    # 予約時間の30分前から30分後までの範囲をチェック
    check_time = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
    start_time = (check_time - timedelta(minutes=30)).strftime("%H:%M")
    end_time = (check_time + timedelta(minutes=30)).strftime("%H:%M")

    c.execute("""
        SELECT COUNT(*) FROM reservations
        WHERE date = ? AND time BETWEEN ? AND ?
    """, (date, start_time, end_time))

    count = c.fetchone()[0]
    conn.close()

    return count == 0


def send_line_notify(message):
    line_notify_token = '3AYdw085usXI9vcXmWhsKQjosA82sQmroBNM8cgdGjn'
    line_notify_api = 'https://notify-api.line.me/api/notify'
    headers = {'Authorization': f'Bearer {line_notify_token}'}
    data = {'message': message}
    requests.post(line_notify_api, headers=headers, data=data)


def init_db():
    conn = sqlite3.connect("pediatric_reservations.db")
    c = conn.cursor()
    c.execute(
        """CREATE TABLE IF NOT EXISTS reservations
                 (id INTEGER PRIMARY KEY, name TEXT, date TEXT, time TEXT, contact TEXT, child_name TEXT, child_age TEXT, symptoms TEXT)"""
    )
    conn.commit()
    conn.close()


if __name__ == "__main__":
    init_db()
    app.run(debug=True)
