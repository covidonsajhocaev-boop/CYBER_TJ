
from flask import Flask, render_template, request, jsonify
import sqlite3
import requests
import json

app = Flask(__name__)

DATABASE = "cyber.db"

# ==================================================
# TELEGRAM SETTINGS
# ==================================================

BOT_TOKEN = "8962916125:AAEYPnI83wmYQs_CfCx9cQsXEq_rjb-mRF8"
ADMIN_ID = 7772351537


# ==================================================
# DATABASE
# ==================================================

def get_db():

    conn = sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


def create_tables():

    conn = get_db()

    conn.execute("""
        CREATE TABLE IF NOT EXISTS payment_requests (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            username TEXT,

            instagram_url TEXT,

            plan TEXT,

            amount INTEGER,

            status TEXT DEFAULT 'pending',

            created_at
            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    """)

    conn.commit()

    conn.close()


# ==================================================
# SEND PAYMENT TO TELEGRAM ADMIN
# ==================================================

def send_payment_to_admin(
    payment_id,
    username,
    instagram_url,
    amount
):

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN нест."
        )

        return False


    if BOT_TOKEN == "TOKEN-и-НАВИ-ТУ":

        print(
            "❌ Дар main.py BOT_TOKEN гузошта нашудааст."
        )

        return False


    text = f"""
🚨 <b>ПАРДОХТИ НАВ</b>

🆔 ID:
<b>#{payment_id}</b>

👤 Instagram:
<b>@{username}</b>

🔗 Ссылка:
{instagram_url}

💰 Маблағ:
<b>{amount} сомонӣ</b>

📌 Status:
<b>⏳ PENDING</b>

⚠️ Пардохти 10 сомониро дар Душанбе Сити санҷед.
"""


    keyboard = {

        "inline_keyboard": [

            [

                {
                    "text":
                        "✅ ПАРДОХТ ҚАБУЛ КАРД",

                    "callback_data":
                        f"approve_{payment_id}"
                }

            ],

            [

                {
                    "text":
                        "❌ ПАРДОХТРО ҚАБУЛ НАКАРД",

                    "callback_data":
                        f"reject_{payment_id}"
                }

            ]

        ]

    }


    url = (
        "https://api.telegram.org/"
        f"bot{BOT_TOKEN}/sendMessage"
    )


    try:

        response = requests.post(

            url,

            data={

                "chat_id":
                    ADMIN_ID,

                "text":
                    text,

                "parse_mode":
                    "HTML",

                "disable_web_page_preview":
                    True,

                "reply_markup":
                    json.dumps(
                        keyboard
                    )

            },

            timeout=10
        )


        print(
            "Telegram:",
            response.status_code
        )

        print(
            response.text
        )


        return response.ok


    except Exception as e:

        print(
            "Telegram error:",
            e
        )

        return False


# ==================================================
# HOME
# ==================================================

# ==================================================
# PASSWORD SECURITY
# ==================================================

@app.route("/password")
def password():
    return render_template("password.html")


# ==================================================
# HOME
# ==================================================

@app.route("/")
def index():

    return render_template(
        "index.html"
    )


# ==================================================
# INSTAGRAM PAGE
# ==================================================

@app.route(
    "/instagram",
    methods=["GET", "POST"]
)
def instagram():

    # ------------------------------------------
    # GET
    # ------------------------------------------

    if request.method == "GET":

        return render_template(
            "instagram.html",
            result=None
        )


    # ------------------------------------------
    # POST
    # ------------------------------------------

    instagram_url = request.form.get(
        "instagram_url",
        ""
    ).strip()


    if not instagram_url:

        return render_template(

            "instagram.html",

            result={

                "type":
                    "error",

                "message":
                    "Instagram link-ро ворид кунед."

            }
        )


    # ------------------------------------------
    # USERNAME
    # ------------------------------------------

    username = (

        instagram_url
        .rstrip("/")
        .split("/")[-1]

    )


    if username.startswith("@"):

        username = username[1:]


    # ------------------------------------------
    # RESULT
    # ------------------------------------------

    result = {

        "type":
            "demo",

        "username":
            username,

        "url":
            instagram_url

    }


    return render_template(

        "instagram.html",

        result=result

    )


# ==================================================
# CREATE PAYMENT
# ==================================================

@app.route(
    "/instagram/payment",
    methods=["POST"]
)
def instagram_payment():

    username = request.form.get(
        "username",
        ""
    ).strip()


    instagram_url = request.form.get(
        "instagram_url",
        ""
    ).strip()


    # Ҳамеша 10 сомонӣ

    amount = 10


    # ------------------------------------------
    # CHECK USERNAME
    # ------------------------------------------

    if not username:

        return jsonify({

            "success":
                False,

            "message":
                "Instagram username ёфт нашуд."

        }), 400


    # ------------------------------------------
    # CHECK LINK
    # ------------------------------------------

    if not instagram_url:

        return jsonify({

            "success":
                False,

            "message":
                "Instagram link ёфт нашуд."

        }), 400


    # ------------------------------------------
    # DATABASE
    # ------------------------------------------

    conn = get_db()

    cursor = conn.cursor()


    cursor.execute("""

        INSERT INTO payment_requests (

            username,

            instagram_url,

            plan,

            amount,

            status

        )

        VALUES (?, ?, ?, ?, ?)

    """, (

        username,

        instagram_url,

        "INSTAGRAM",

        amount,

        "pending"

    ))


    payment_id = cursor.lastrowid


    conn.commit()

    conn.close()


    # ------------------------------------------
    # SEND TELEGRAM
    # ------------------------------------------

    telegram_sent = send_payment_to_admin(

        payment_id,

        username,

        instagram_url,

        amount

    )


    print("")
    print("==============================")
    print("NEW PAYMENT")
    print("==============================")
    print(
        "ID:",
        payment_id
    )
    print(
        "USERNAME:",
        username
    )
    print(
        "LINK:",
        instagram_url
    )
    print(
        "AMOUNT:",
        amount
    )
    print(
        "TELEGRAM:",
        telegram_sent
    )
    print("==============================")
    print("")


    # ------------------------------------------
    # RESPONSE
    # ------------------------------------------

    return jsonify({

        "success":
            True,

        "payment_id":
            payment_id,

        "amount":
            amount,

        "message":
            "Пардохт ба админ фиристода шуд."

    })


# ==================================================
# PAYMENT STATUS
# ==================================================

@app.route(
    "/instagram/payment/status/<int:payment_id>"
)
def payment_status(payment_id):

    conn = get_db()


    payment = conn.execute("""

        SELECT *

        FROM payment_requests

        WHERE id = ?

    """, (

        payment_id,

    )).fetchone()


    conn.close()


    # ------------------------------------------
    # NOT FOUND
    # ------------------------------------------

    if not payment:

        return jsonify({

            "success":
                False,

            "status":
                "not_found"

        }), 404


    # ------------------------------------------
    # RESPONSE
    # ------------------------------------------

    return jsonify({

        "success":
            True,

        "status":
            payment["status"],

        "payment_id":
            payment["id"],

        "username":
            payment["username"],

        "instagram_url":
            payment["instagram_url"],

        "amount":
            payment["amount"]

    })


# ==================================================
# IMPORTANT:
# NO /instagram/full/<id>
# NO PRO REDIRECT
# ==================================================


# ==================================================
# 404
# ==================================================

@app.errorhandler(404)
def page_not_found(error):

    return """

    <!DOCTYPE html>

    <html>

    <head>

        <meta charset="UTF-8">

        <meta
            name="viewport"
            content="width=device-width,
                     initial-scale=1.0"
        >

        <title>404</title>

        <style>

            body {

                background:#09090f;

                color:white;

                font-family:Arial;

                text-align:center;

                padding:50px 20px;

            }

            a {

                display:inline-block;

                margin-top:20px;

                padding:14px 22px;

                border-radius:15px;

                background:#7c3aed;

                color:white;

                text-decoration:none;

            }

        </style>

    </head>

    <body>

        <h1>404</h1>

        <p>
            Саҳифа ёфт нашуд.
        </p>

        <a href="/">
            🏠 Ба саҳифаи асосӣ
        </a>

    </body>

    </html>

    """, 404


# ==================================================
# START SERVER
# ==================================================

if __name__ == "__main__":

    create_tables()


    print("")
    print("==============================")
    print("       CYBER TJ")
    print("==============================")
    print("")
    print(
        "SERVER:"
        " http://127.0.0.1:5000"
    )
    print("")
    print(
        "💰 INSTAGRAM PAYMENT:"
        " 10 сомонӣ"
    )
    print(
        "🔓 PRO:"
        " OFF"
    )
    print(
        "🔗 RESULT:"
        " Instagram link only"
    )
    print("")


    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True

    )
