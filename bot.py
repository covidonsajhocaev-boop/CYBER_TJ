
import sqlite3
import logging

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler
)


BOT_TOKEN = "8962916125:AAEYPnI83wmYQs_CfCx9cQsXEq_rjb-mRF8"

ADMIN_ID = 7772351537

DATABASE = "cyber.db"


logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)


logger = logging.getLogger(__name__)


# =========================
# DATABASE
# =========================

def get_db():

    conn = sqlite3.connect(
        DATABASE,
        check_same_thread=False
    )

    conn.row_factory = sqlite3.Row

    return conn


# =========================
# ADMIN CHECK
# =========================

def is_admin(user_id):

    return user_id == ADMIN_ID


# =========================
# START
# =========================

async def start(update: Update, context):

    user = update.effective_user

    if not user:
        return


    if not is_admin(user.id):

        await update.message.reply_text(
            "⛔ Дастрасӣ манъ аст."
        )

        return


    await send_pending_payments(
        update.message
    )


# =========================
# ADMIN
# =========================

async def admin(update: Update, context):

    user = update.effective_user

    if not user:
        return


    if not is_admin(user.id):

        await update.message.reply_text(
            "⛔ Дастрасӣ манъ аст."
        )

        return


    await send_pending_payments(
        update.message
    )


# =========================
# PENDING PAYMENTS
# =========================

async def send_pending_payments(message):

    conn = get_db()


    payments = conn.execute("""
        SELECT *
        FROM payment_requests

        WHERE status = 'pending'

        ORDER BY id DESC
    """).fetchall()


    conn.close()


    if not payments:

        await message.reply_text(
            "📭 Пардохти интизорӣ нест."
        )

        return


    for payment in payments:

        username = (
            payment["username"]
            or "unknown"
        )


        instagram_url = (
            payment["instagram_url"]
            or "-"
        )


        amount = (
            payment["amount"]
            or 10
        )


        text = (

            "🚨 <b>ПАРДОХТИ НАВ</b>\n\n"

            f"🆔 ID: "
            f"<b>#{payment['id']}</b>\n\n"

            f"👤 Корбар: "
            f"<b>@{username}</b>\n\n"

            f"🔗 Instagram:\n"
            f"{instagram_url}\n\n"

            f"💰 Маблағ: "
            f"<b>{amount} сомонӣ</b>\n\n"

            "📌 Status: "
            "<b>⏳ PENDING</b>"
        )


        keyboard = [

            [

                InlineKeyboardButton(
                    "✅ ПАРДОХТ ҚАБУЛ КАРД",
                    callback_data=
                        f"approve_{payment['id']}"
                )

            ],

            [

                InlineKeyboardButton(
                    "❌ ПАРДОХТРО ҚАБУЛ НАКАРД",
                    callback_data=
                        f"reject_{payment['id']}"
                )

            ]

        ]


        await message.reply_text(

            text,

            parse_mode="HTML",

            disable_web_page_preview=True,

            reply_markup=
                InlineKeyboardMarkup(
                    keyboard
                )
        )


# =========================
# BUTTON
# =========================

async def button_handler(
    update: Update,
    context
):

    query = update.callback_query

    user = query.from_user


    if not is_admin(user.id):

        await query.answer(
            "⛔ Дастрасӣ манъ аст.",
            show_alert=True
        )

        return


    data = query.data


    # =========================
    # APPROVE
    # =========================

    if data.startswith(
        "approve_"
    ):

        try:

            payment_id = int(
                data.replace(
                    "approve_",
                    ""
                )
            )

        except ValueError:

            await query.answer(
                "ID нодуруст аст.",
                show_alert=True
            )

            return


        conn = get_db()


        payment = conn.execute("""
            SELECT *
            FROM payment_requests
            WHERE id = ?
        """, (
            payment_id,
        )).fetchone()


        if not payment:

            conn.close()

            await query.answer(
                "❌ Пардохт ёфт нашуд.",
                show_alert=True
            )

            return


        if payment["status"] != "pending":

            conn.close()

            await query.answer(
                "⚠️ Аллакай коркард шудааст.",
                show_alert=True
            )

            return


        # =========================
        # APPROVED
        # =========================

        conn.execute("""
            UPDATE payment_requests

            SET status = 'approved'

            WHERE id = ?
        """, (
            payment_id,
        ))


        conn.commit()

        conn.close()


        await query.answer(
            "✅ Пардохт тасдиқ шуд!"
        )


        # Тугмаҳоро нест мекунем

        await query.edit_message_reply_markup(
            reply_markup=None
        )


        # Паёми админ

        await query.edit_message_text(

            query.message.text

            + "\n\n"

            + "━━━━━━━━━━━━━━━━━━\n"

            + "✅ <b>ПАРДОХТ ҚАБУЛ КАРД</b>\n\n"

            + "👤 Корбар:\n"
            + f"<b>@{payment['username']}</b>\n\n"

            + "💰 "
            + f"<b>{payment['amount']} сомонӣ</b>\n\n"

            + "🔗 Ссылка:\n"
            + f"{payment['instagram_url']}",

            parse_mode="HTML",

            disable_web_page_preview=True
        )


        return


    # =========================
    # REJECT
    # =========================

    if data.startswith(
        "reject_"
    ):

        try:

            payment_id = int(
                data.replace(
                    "reject_",
                    ""
                )
            )

        except ValueError:

            await query.answer(
                "ID нодуруст аст.",
                show_alert=True
            )

            return


        conn = get_db()


        payment = conn.execute("""
            SELECT *
            FROM payment_requests
            WHERE id = ?
        """, (
            payment_id,
        )).fetchone()


        if not payment:

            conn.close()

            await query.answer(
                "❌ Пардохт ёфт нашуд.",
                show_alert=True
            )

            return


        if payment["status"] != "pending":

            conn.close()

            await query.answer(
                "⚠️ Аллакай коркард шудааст.",
                show_alert=True
            )

            return


        # =========================
        # REJECTED
        # =========================

        conn.execute("""
            UPDATE payment_requests

            SET status = 'rejected'

            WHERE id = ?
        """, (
            payment_id,
        ))


        conn.commit()

        conn.close()


        await query.answer(
            "❌ Пардохт рад карда шуд."
        )


        await query.edit_message_reply_markup(
            reply_markup=None
        )


        await query.edit_message_text(

            query.message.text

            + "\n\n"

            + "━━━━━━━━━━━━━━━━━━\n"

            + "❌ <b>ПАРДОХТРО ҚАБУЛ НАКАРД</b>",

            parse_mode="HTML",

            disable_web_page_preview=True
        )


        return


# =========================
# ERROR
# =========================

async def error_handler(
    update,
    context
):

    logger.error(
        "Telegram error:",
        exc_info=context.error
    )


# =========================
# MAIN
# =========================

def main():

    print("")
    print("==============================")
    print("       CYBER TJ BOT")
    print("==============================")
    print("")


    if BOT_TOKEN == "TOKEN-и-НАВИ-ТУ":

        print(
            "❌ BOT_TOKEN-ро гузор!"
        )

        return


    application = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )


    application.add_handler(
        CommandHandler(
            "start",
            start
        )
    )


    application.add_handler(
        CommandHandler(
            "admin",
            admin
        )
    )


    application.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )


    application.add_error_handler(
        error_handler
    )


    print(
        "✅ BOT STARTED..."
    )


    print(
        "👤 ADMIN ID:",
        ADMIN_ID
    )


    print(
        "🗄 DATABASE:",
        DATABASE
    )


    print("")


    application.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":

    main()
