import os
import requests
import logging
from flask import Flask
from threading import Thread
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ForceReply
from telegram.ext import (
    Updater, CommandHandler, CallbackQueryHandler, 
    MessageHandler, Filters, ConversationHandler, CallbackContext
)

# ======================
# CONFIG
# ======================
BOT_TOKEN = os.environ.get("BOT_TOKEN")
OWNER_ID = int(os.environ.get("OWNER_ID"))

INJECTOR_URL = "https://codm-injector-panel-4ewn.onrender.com"
SCRIPT_URL = "https://codm-script-k82g.onrender.com"  

# ======================
# STATES FOR CONVERSATION
# ======================
(
    SELECT_ACTION, SELECT_DB, 
    INPUT_REVOKE_KEY, INPUT_RESET_KEY,
    INPUT_CUSTOM_NAME, INPUT_CUSTOM_DURATION, INPUT_CUSTOM_MAX,
    INPUT_DELETE_KEY,
    INPUT_UNREVOKE_KEY  # <--- Idagdag ito
) = range(9)            # <--- Gawing 9

# ======================
# KEEP ALIVE SERVER
# ======================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bot running!"

def keep_alive():
    port = int(os.environ.get("PORT", 10000))
    Thread(target=lambda: app.run(host="0.0.0.0", port=port)).start()

# ======================
# OWNER CHECK
# ======================
def is_owner(update: Update):
    return update.effective_user.id == OWNER_ID

# ======================
# START / MAIN MENU
# ======================
def start(update: Update, context: CallbackContext):
    if not is_owner(update):
        update.message.reply_text("🚫 Access Denied. Private Panel.")
        return ConversationHandler.END

    context.user_data.clear()

    text = """━━━━━━━━━━━━━━━━━━━━━━━━━━━━
          KAZEHAYAMODZ PANEL          
━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[SYSTEM STATUS]
> ALL SYSTEMS OPERATIONAL
> STATUS: ONLINE // SECURE

[CORE SERVICES]
> CODM ADVANCED INJECTOR 
> CODM PREMIUM SCRIPT 

[SECURITY]
> ACCESS LEVEL: RESTRICTED
> MEMBERSHIP: VIP PRIVATE ONLY

━━━━━━━━━━━━━━━━━━━━━━━━━━━━

System Features:
✓ Optimized management interface
✓ Configuration controls
✓ Maintenance automation
✓ Stability monitoring
✓ Performance synchronization

━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Please select an option from the menu Kaze:"""
    
    keyboard = [
        [InlineKeyboardButton("🔑 Generate Key", callback_data="act_gen"), 
         InlineKeyboardButton("🔄 Reset Key", callback_data="act_reset")],
        [InlineKeyboardButton("🚫 Revoke Key", callback_data="act_revoke"), 
         InlineKeyboardButton("🟢 Unrevoke Key", callback_data="act_unrevoke")],
        [InlineKeyboardButton("❌ Delete Key", callback_data="act_delete"),
         InlineKeyboardButton("📊 Stats", callback_data="act_stats")],
        [InlineKeyboardButton("⚡ List Keys", callback_data="act_listact"), 
         InlineKeyboardButton("🔴 Revoked History", callback_data="act_listhist")],
        [InlineKeyboardButton("🔥 Custom Key", callback_data="act_custom")]
    ]
    
    update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SELECT_ACTION

# ======================
# ACTION HANDLER
# ======================
def handle_action(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    action = query.data.replace("act_", "")
    context.user_data["action"] = action  
    
    keyboard = [
        [InlineKeyboardButton("🔥 CODM INJECTOR", callback_data="db_injector")],
        [InlineKeyboardButton("🔥 CODM SCRIPT", callback_data="db_script")],
        [InlineKeyboardButton("⬅️ BACK", callback_data="back_main")]
    ]
    
    query.edit_message_text("🗂 **Select Database:**", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
    return SELECT_DB

# ======================
# DATABASE HANDLER
# ======================
def handle_db(update: Update, context: CallbackContext):
    query = update.callback_query
    query.answer()
    
    if query.data == "back_main":
        try: query.message.delete()
        except: pass
        
        keyboard = [
            [InlineKeyboardButton("🔑 Generate Key", callback_data="act_gen"), InlineKeyboardButton("🔄 Reset Key", callback_data="act_reset")],
            [InlineKeyboardButton("🚫 Revoke Key", callback_data="act_revoke"), InlineKeyboardButton("🗑️ Delete Key", callback_data="act_delete")],
            [InlineKeyboardButton("🟢 Unrevoked Keys", callback_data="act_listact"), InlineKeyboardButton("🔴 Revoked History", callback_data="act_listhist")],
            [InlineKeyboardButton("📊 Stats", callback_data="act_stats"), InlineKeyboardButton("🔥 Custom Key", callback_data="act_custom")]
        ]
        context.bot.send_message(chat_id=query.message.chat_id, text="🎮 **KAZE CENTRAL CONTROL PANEL**\n\nPumili ng aksyon sa ibaba:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return SELECT_ACTION

    db_choice = query.data.replace("db_", "")
    context.user_data["db"] = db_choice
    context.user_data["panel_url"] = INJECTOR_URL if db_choice == "injector" else SCRIPT_URL
    
    action = context.user_data.get("action")
    panel_url = context.user_data.get("panel_url")
    db_name = "CODM INJECTOR" if db_choice == "injector" else "CODM SCRIPT"

    try: query.message.delete()
    except: pass

    # ---- FLOW 1: GENERATE KEY ----
    if action == "gen":
        keyboard = [
            [InlineKeyboardButton("1 Day", callback_data="dur_1d"), InlineKeyboardButton("3 Days", callback_data="dur_3d")],
            [InlineKeyboardButton("7 Days", callback_data="dur_7d"), InlineKeyboardButton("30 Days", callback_data="dur_30d")],
            [InlineKeyboardButton("Lifetime", callback_data="dur_lifetime")]
        ]
        context.bot.send_message(chat_id=query.message.chat_id, text=f"🔑 **[{db_name}]**\nSelect Key Duration:", reply_markup=InlineKeyboardMarkup(keyboard), parse_mode="Markdown")
        return SELECT_DB

    # ---- FLOW 2: REVOKE KEY (DISABLE ONLY) ----
    elif action == "revoke":
        context.bot.send_message(chat_id=query.message.chat_id, text=f"🚫 **Database:** {db_name}\n\n➡️ **Enter key to REVOKE (Disable Only):**", reply_markup=ForceReply(selective=True), parse_mode="Markdown")
        return INPUT_REVOKE_KEY

    # ---- FLOW 3: DELETE KEY (PERMANENT ERASE) ----
    elif action == "delete":
        context.bot.send_message(chat_id=query.message.chat_id, text=f"🗑️ **Database:** {db_name}\n\n➡️ **Enter key to DELETE (Permanently Remove):**", reply_markup=ForceReply(selective=True), parse_mode="Markdown")
        return INPUT_DELETE_KEY

    # ---- FLOW 4: RESET KEY ----
    elif action == "reset":
        context.bot.send_message(chat_id=query.message.chat_id, text=f"🔰 **Database:** {db_name}\n\n➡️ **Enter key to reset:**", reply_markup=ForceReply(selective=True), parse_mode="Markdown")
        return INPUT_RESET_KEY

    # ---- NEW FLOW: UNREVOKE KEY ----
    elif action == "unrevoke":
        context.bot.send_message(chat_id=query.message.chat_id, text=f"🟢 **Database:** {db_name}\n\n➡️ **Enter key to UNREVOKE (Make Active Again):**", reply_markup=ForceReply(selective=True), parse_mode="Markdown")
        return INPUT_UNREVOKE_KEY

    # ---- FLOW 5: LIST UNREVOKED / HISTORY KEYS ----
    elif action in ["listact", "listhist"]:
        try:
            target_status = "active" if action == "listact" else "revoked"
            headers = {"Accept": "application/json", "User-Agent": "Mozilla/5.0"}
            response = requests.get(f"{panel_url}/list?status={target_status}", headers=headers, timeout=30)
            
            if response.status_code != 200:
                context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Server returned status code {response.status_code}")
                return ConversationHandler.END
                
            r = response.json()
            
            if not isinstance(r, list) or len(r) == 0:
                header_title = "ACTIVE (UNREVOKED)" if target_status == "active" else "REVOKED HISTORY"
                context.bot.send_message(chat_id=query.message.chat_id, text=f"📋 **[{db_name} - {header_title}]**\nNo keys found.")
                return ConversationHandler.END
            
            if target_status == "active":
                msg = f"🟢 **ACTIVE / UNREVOKED KEYS [{db_name}]**\n\n"
            else:
                msg = f"🔴 **REVOKED KEYS HISTORY [{db_name}]**\n\n"
            
            valid_count = 0
            for k in r:
                if valid_count >= 20:
                    break
                    
                if not isinstance(k, dict):
                    continue
                    
                key_code = k.get('key') or k.get('key_code')
                if not key_code:
                    continue  
                    
                device_info = k.get('device') or 'None'
                max_slots = k.get('max_devices') or k.get('max') or 1
                
                msg += f"`{key_code}` | Dev: {device_info} (Max: {max_slots})\n"
                valid_count += 1
                
            if valid_count == 0:
                context.bot.send_message(chat_id=query.message.chat_id, text=f"📋 **[{db_name}]**\nNo valid keys could be processed.")
            else:
                context.bot.send_message(chat_id=query.message.chat_id, text=msg, parse_mode="Markdown")
            
        except Exception as e:
            print(f"🔴 CRITICAL LIST ERROR FOR {db_name}: {e}")
            context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Failed to fetch keys from {db_name} server.")
            
        return ConversationHandler.END

    # ---- FLOW 6: STATS ----
    elif action == "stats":
        try:
            r = requests.get(f"{panel_url}/stats", timeout=15).json()
            msg = f"📊 **PANEL STATISTICS [{db_name}]**\n\nTotal Keys: {r['total_keys']}\nActive Keys: {r['active_keys']}\nExpired Keys: {r['expired_keys']}"
            context.bot.send_message(chat_id=query.message.chat_id, text=msg, parse_mode="Markdown")
        except:
            context.bot.send_message(chat_id=query.message.chat_id, text="❌ Failed to fetch stats.")
        return ConversationHandler.END

    # ---- FLOW 7: CUSTOM KEY ----
    elif action == "custom":
        context.bot.send_message(chat_id=query.message.chat_id, text=f"🔰 **Database:** {db_name}\n\n➡️ **Enter Custom Name:**", reply_markup=ForceReply(selective=True), parse_mode="Markdown")
        return INPUT_CUSTOM_NAME

    # Standard Duration Handler
    if query.data.startswith("dur_"):
        duration = query.data.replace("dur_", "")
        try:
            token = requests.get(f"{panel_url}/token", timeout=15).json().get("token")
            r = requests.get(f"{panel_url}/getkey?token={token}&src=bot&duration={duration}", timeout=15).json()
            key = r.get("key", "ERROR")
            
            msg = f"🔑 **KEY GENERATED**\n━━━━━━━━━━━━━━━━━━━━\n🔰 DB: `{db_name}`\n🔑 KEY: `{key}`\n⏳ EXPIRATION: `{duration}`\n🚫 SLOTS: 1 Device\n━━━━━━━━━━━━━━━━━━━━"
            context.bot.send_message(chat_id=query.message.chat_id, text=msg, parse_mode="Markdown")
        except Exception as e:
            context.bot.send_message(chat_id=query.message.chat_id, text=f"❌ Error Generating Key: {e}")
        return ConversationHandler.END

# ======================
# EXECUTE FUNCTIONS
# ======================
def execute_revoke(update: Update, context: CallbackContext):
    key = update.message.text.strip()
    panel_url = context.user_data.get("panel_url")
    db_choice = context.user_data.get("db")
    db_name = "CODM INJECTOR" if db_choice == "injector" else "CODM SCRIPT"

    try:
        r = requests.get(f"{panel_url}/revoke?key={key}", timeout=15)
        if r.status_code == 200:
            update.message.reply_text(f"🚫 **KEY REVOKED**\n\n**Database:** {db_name}\n**Key:** `{key}`\n**Status:** DISABLED (Nasa History pa rin)", parse_mode="Markdown")
        else:
            update.message.reply_text(f"❌ Failed to revoke. Key `{key}` might not exist on {db_name}.", parse_mode="Markdown")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
    return ConversationHandler.END

def execute_unrevoke(update: Update, context: CallbackContext):
    key = update.message.text.strip()
    panel_url = context.user_data.get("panel_url")
    db_choice = context.user_data.get("db")
    db_name = "CODM INJECTOR" if db_choice == "injector" else "CODM SCRIPT"

    try:
        r = requests.get(f"{panel_url}/unrevoke?key={key}", timeout=15)
        if r.status_code == 200:
            update.message.reply_text(f"🟢 **KEY UNREVOKED**\n\n**Database:** {db_name}\n**Key:** `{key}`\n**Status:** ACTIVE AGAIN (Magagamit na uli!)", parse_mode="Markdown")
        else:
            update.message.reply_text(f"❌ Failed to unrevoke. Key `{key}` not found on {db_name}.", parse_mode="Markdown")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
    return ConversationHandler.END

def execute_delete(update: Update, context: CallbackContext):
    key = update.message.text.strip()
    panel_url = context.user_data.get("panel_url")
    db_choice = context.user_data.get("db")
    db_name = "CODM INJECTOR" if db_choice == "injector" else "CODM SCRIPT"

    try:
        r = requests.get(f"{panel_url}/delete?key={key}", timeout=15)
        if r.status_code == 200:
            update.message.reply_text(f"🗑️ **KEY PERMANENTLY DELETED**\n\n**Database:** {db_name}\n**Key:** `{key}`\n**Status:** REMOVED FROM DATABASE\n\n👉 Pwede mo na ulit gamitin ang pangalan na ito sa Custom Key!", parse_mode="Markdown")
        else:
            update.message.reply_text(f"❌ Failed to delete. Key `{key}` not found on {db_name}.", parse_mode="Markdown")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
    return ConversationHandler.END

def execute_reset(update: Update, context: CallbackContext):
    key = update.message.text.strip()
    panel_url = context.user_data.get("panel_url")
    db_choice = context.user_data.get("db")
    db_name = "CODM INJECTOR" if db_choice == "injector" else "CODM SCRIPT"

    try:
        r = requests.get(f"{panel_url}/reset?key={key}", timeout=15)
        if r.status_code == 200:
            update.message.reply_text(f"🔄 **KEY DEVICE RESET**\n\n**Database:** {db_name}\n**Key:** `{key}`\n**Status:** UNLOCKED", parse_mode="Markdown")
        else:
            update.message.reply_text(f"❌ Failed to reset. Key `{key}` not found on {db_name}.", parse_mode="Markdown")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
    return ConversationHandler.END

# ======================
# EXECUTE CUSTOM KEY (3-STEPS FLOW)
# ======================
def execute_custom_name(update: Update, context: CallbackContext):
    context.user_data["custom_name"] = update.message.text.strip()
    update.message.reply_text("➡️ **Enter Duration (e.g., 1d, 7d, 30d, lifetime):**", reply_markup=ForceReply(selective=True), parse_mode="Markdown")
    return INPUT_CUSTOM_DURATION

def execute_custom_duration(update: Update, context: CallbackContext):
    context.user_data["custom_duration"] = update.message.text.strip()
    update.message.reply_text("➡️ **Enter Max Devices / Slots (e.g., 1, 5, 9999):**", reply_markup=ForceReply(selective=True), parse_mode="Markdown")
    return INPUT_CUSTOM_MAX

def execute_custom_max(update: Update, context: CallbackContext):
    max_dev = update.message.text.strip()
    name = context.user_data.get("custom_name")
    duration = context.user_data.get("custom_duration")
    panel_url = context.user_data.get("panel_url")
    db_choice = context.user_data.get("db")
    db_name = "CODM INJECTOR" if db_choice == "injector" else "CODM SCRIPT"

    try:
        r = requests.get(f"{panel_url}/customkey?name={name}&duration={duration}&max={max_dev}", timeout=15)
        if r.status_code == 200:
            key_data = r.json()
            generated_key = key_data.get("key")
            
            msg = f"🎁 **CUSTOM KEY CREATED**\n━━━━━━━━━━━━━━━━━━━━\n🔰 DB: `{db_name}`\n🔑 KEY: `{generated_key}`\n⏳ DURATION: `{duration}`\n🚫 SLOTS: {max_dev} Device(s)\n━━━━━━━━━━━━━━━━━━━━"
            update.message.reply_text(msg, parse_mode="Markdown")
        else:
            update.message.reply_text("❌ Failed to create custom key. Name might already exist.")
    except Exception as e:
        update.message.reply_text(f"❌ Error: {e}")
    return ConversationHandler.END

def cancel(update: Update, context: CallbackContext):
    update.message.reply_text("❌ Process cancelled.")
    return ConversationHandler.END

# ======================
# ERROR LOGGING & HANDLING
# ======================
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

def error_handler(update: Update, context: CallbackContext):
    logger.warning(f'Update "{update}" caused error "{context.error}"')
    if "Timed out" in str(context.error):
        return
        
# ======================
# MAIN FUNCTION
# ======================
def main():
    updater = Updater(BOT_TOKEN, use_context=True)
    dp = updater.dispatcher

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            SELECT_ACTION: [CallbackQueryHandler(handle_action, pattern="^act_")],
            SELECT_DB: [
                CallbackQueryHandler(handle_db, pattern="^db_"),
                CallbackQueryHandler(handle_db, pattern="^dur_"),
                CallbackQueryHandler(handle_db, pattern="^back_main")
            ],
            INPUT_REVOKE_KEY: [MessageHandler(Filters.text & ~Filters.command, execute_revoke)],
            INPUT_DELETE_KEY: [MessageHandler(Filters.text & ~Filters.command, execute_delete)],
            INPUT_UNREVOKE_KEY: [MessageHandler(Filters.text & ~Filters.command, execute_unrevoke)], # <--- Idagdag itong linya!
            INPUT_RESET_KEY: [MessageHandler(Filters.text & ~Filters.command, execute_reset)],
            INPUT_CUSTOM_NAME: [MessageHandler(Filters.text & ~Filters.command, execute_custom_name)],
            INPUT_CUSTOM_DURATION: [MessageHandler(Filters.text & ~Filters.command, execute_custom_duration)],
            INPUT_CUSTOM_MAX: [MessageHandler(Filters.text & ~Filters.command, execute_custom_max)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )

    dp.add_handler(conv_handler)
    dp.add_error_handler(error_handler)

    updater.start_polling()
    updater.idle()
    
if __name__ == "__main__":
    keep_alive()
    main()
