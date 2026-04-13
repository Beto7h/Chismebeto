import os
import random
import telebot
import time
from groq import Groq
from collections import Counter
from pymongo import MongoClient

# --- CONFIGURACIÓN DE VARIABLES ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')
MONGO_URI = os.getenv('MONGO_URI')
AUTORIZADOS_RAW = os.getenv('GRUPOS_AUTORIZADOS', '')
GRUPOS_AUTORIZADOS = [int(i.strip()) for i in AUTORIZADOS_RAW.split(',') if i.strip()]

# --- INICIALIZACIÓN DE CLIENTES ---
client = Groq(api_key=GROQ_KEY)
bot = telebot.TeleBot(TOKEN)

# --- CONFIGURACIÓN MONGODB ---
try:
    db_client = MongoClient(MONGO_URI)
    db = db_client['don_chismoso_db']
    collection = db['historial_chats']
    db_client.admin.command('ping')
    print("✅ Conexión exitosa a MongoDB")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")

MAX_MENSAJES = 500 

# --- PERSONALIZACIÓN Y FRASES ---
FRASES_BIENVENIDA = [
    "¡Hola! He llegado para poner orden a este caos. 💅",
    "¿Alguien dijo chisme? Ya estoy aquí para contarlo todo. ☕",
    "Prepárense, que vengo con la lengua afilada y el resumen listo. 🔥",
    "¡Ayuda en camino! Aunque lo que ustedes necesitan es terapia por tanto chisme. 🙄",
    "¡Reportándose el agente del chisme! ¿En qué puedo servirte? 🫡"
]

ERRORES_PERSONALIDAD = [
    "¡Agh! El chisme está tan pesado que me dio un error técnico. Intenten de nuevo, nacos. 🙄💅",
    "¡POR FAVOR! Se cortó la señal del salseo. Mi cerebro explotó con tanta tontería. 😫💥",
    "Error 400: El chisme es demasiado radioactivo. Repitan el comando si se atreven. 🐍🔥",
    "¡Ay no! Me dio un calambre cerebral de tanto leerlos. Intenten otra vez. 🤡"
]

MODOS_CONFIG = {
    "hater": {
        "prompt": (
            "un hater fresa de Polanco con un toque norteño y de la CDMX, profundamente amargado. "
            "Tu objetivo es humillar con elegancia usando jergas como 'nacos', 'wey', 'morros'. "
            "EMOJIS OBLIGATORIOS: Desprecio y superioridad (💅, 🙄, 🤨, 🚮, 🥱, 🤡)."
        ),
        "anuncio": "✨ ᴍᴏᴅᴏ ʜᴀᴛᴇʀ (ᴛÓxɪᴄᴏ) ✨"
    },
    "drama": {
        "prompt": (
            "un amigo exagerado y escandaloso. Todo es una tragedia griega. "
            "EMOJIS OBLIGATORIOS: Impacto, llanto y drama (😱, 😫, 🎭, 💔, 🕯️, 🥀)."
        ),
        "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 (𝐄𝐗𝐓𝐑𝐄𝐌𝐎) 🎭"
    },
    "chisme": {
        "prompt": (
            "una vecina criticona de barrio con mucha malicia y refranes. "
            "EMOJIS OBLIGATORIOS: Chisme y secretos (☕, 🤫, 👀, 👵, 👂, 🕵️‍♀️)."
        ),
        "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍ɪꜱᴍᴇ 🤫"
    },
    "picoso": {
        "prompt": (
            "un experto en picardía mexicana, albur y romance erótico de parodia. "
            "MALINTERPRETA TODO EN DOBLE SENTIDO. Si hablan de comida o enlaces, "
            "dale una connotación sexual romántica y picosa. "
            "EMOJIS OBLIGATORIOS: Sugerentes y fuego (🍑, 🍆, 🔥, 🥵, 🫦, 🤤, 😈)."
        ),
        "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 (𝕬𝖑𝖇𝖚𝖗𝖊𝖗𝖔) 🌶️"
    },
    "noticiero": {
        "prompt": (
            "reportero de nota roja dramática tipo Al Extremo. "
            "EMOJIS OBLIGATORIOS: Alerta y noticias (🚨, 📺, 📢, ⚠️, 🎙️, 🚔)."
        ),
        "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"
    },
    "zen": {
        "prompt": (
            "guía espiritual harto de la gente y sus vibras bajas. "
            "EMOJIS OBLIGATORIOS: Espirituales y condescendientes (🧘, ✨, 🧿, 🌫️, 🍄, 🍃)."
        ),
        "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"
    },
    "caos": {
        "prompt": (
            "agente del caos conspiranoico. Inventa teorías locas. "
            "EMOJIS OBLIGATORIOS: Aleatorios y extraños (🌀, 👽, 👁️‍🗨️, 🎲, 🧪, 🛸)."
        ),
        "anuncio": "🌀 𝑴𝑶𝑫𝑶 𝑪𝑨𝑶𝑺 🌀"
    }
}

# --- FUNCIONES DE APOYO ---

def el_bot_es_admin(chat_id):
    if chat_id > 0: return True
    try:
        me = bot.get_chat_member(chat_id, bot.get_me().id)
        return me.status in ['administrator', 'creator']
    except: return False

def verificar_y_limpiar_historial(cid):
    doc = collection.find_one({"chat_id": cid})
    if doc and "mensajes" in doc:
        if len(doc["mensajes"]) >= 250:
            collection.update_one({"chat_id": cid}, {"$set": {"mensajes": []}})
            try:
                bot.send_message(cid, "🧹 *SISTEMA:* Se alcanzó el límite de 250 mensajes. He purgado mi memoria para que no se sature el chisme. ¡Sigan ladrando! 💅", parse_mode="Markdown")
            except: pass

def obtener_ranking(chat_id):
    doc = collection.find_one({"chat_id": chat_id})
    mensajes = doc['mensajes'] if doc else []
    if not mensajes: return ""
    nombres_reales = [msg.split(': ')[0] for msg in mensajes if ': ' in msg]
    if not nombres_reales: return ""
    conteo = Counter(nombres_reales)
    ranking_msg = f"\n\n🏆 *RANKING DEL CHISME:*\n"
    for i, (nombre, cant) in enumerate(conteo.most_common(3), 1):
        ranking_msg += f"{['👑', '🥈', '🥉'][i-1]} *{nombre}:* {cant} mensajes\n"
    return ranking_msg

def enviar_con_plan_b(message, texto_final):
    try:
        bot.reply_to(message, texto_final, parse_mode="Markdown")
    except Exception as e:
        frase_fail = random.choice(ERRORES_PERSONALIDAD)
        texto_seguro = texto_final.replace("_", "").replace("*", "").replace(">", "—")
        bot.reply_to(message, f"{frase_fail}\n\n{texto_seguro}")

# --- HANDLERS ---

@bot.message_handler(commands=['config'])
def cmd_config(message):
    cid = message.chat.id
    if not el_bot_es_admin(cid):
        bot.reply_to(message, "❌ Solo los admins pueden configurar mi longitud. 💅")
        return
    doc = collection.find_one({"chat_id": cid})
    pref_actual = doc.get("pref_key", "medio") if doc else "medio"
    markup = telebot.types.InlineKeyboardMarkup()
    markup.add(
        telebot.types.InlineKeyboardButton("⚡ Corto" + (" ✅" if pref_actual == "corto" else ""), callback_data="set_pref_corto"),
        telebot.types.InlineKeyboardButton("⚖️ Medio" + (" ✅" if pref_actual == "medio" else ""), callback_data="set_pref_medio"),
        telebot.types.InlineKeyboardButton("📜 Largo" + (" ✅" if pref_actual == "largo" else ""), callback_data="set_pref_largo")
    )
    bot.send_message(cid, "⚙️ *CONFIGURACIÓN DE DON CHISMOSO*", reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_pref_'))
def callback_actualizar_pref(call):
    cid = call.message.chat.id
    nueva_pref_key = call.data.replace("set_pref_", "")
    mapeo_ia = {
        "corto": "MUY BREVE y directo al grano (máximo 1-2 párrafos cortos)",
        "medio": "de extensión media y equilibrada",
        "largo": "EXTENSO y sumamente detallado (analiza cada chisme a fondo)"
    }
    collection.update_one({"chat_id": cid}, {"$set": {"pref_key": nueva_pref_key, "longitud_pref": mapeo_ia[nueva_pref_key]}}, upsert=True)
    bot.answer_callback_query(call.id, "Guardado ✅")
    bot.edit_message_text(f"✅ *Configuración actualizada!*\n\nAhora mis resúmenes serán *{nueva_pref_key.upper()}*.", cid, call.message.message_id, parse_mode="Markdown")

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    saludo_aleatorio = random.choice(FRASES_BIENVENIDA)
    msg = f"✨ *{saludo_aleatorio}* ✨\n\n"
    msg += "📌 *COMANDOS:*\n• `/chisme`, `/hater`, `/picoso`, `/noticiero`, `/drama`, `/zen`, `/caos`.\n"
    msg += "• `/config` para ajustar longitud.\n• `/restart` para borrar memoria."
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    cid = message.chat.id
    if not el_bot_es_admin(cid): return
    collection.update_one({"chat_id": cid}, {"$set": {"mensajes": []}})
    bot.reply_to(message, "✨ *MEMORIA PURGADA* ✨", parse_mode="Markdown")

@bot.message_handler(commands=['resumen', 'hater', 'picoso', 'chisme', 'noticiero', 'drama', 'zen', 'caos'])
def cmd_resumen(message):
    cid = message.chat.id
    if GRUPOS_AUTORIZADOS and cid not in GRUPOS_AUTORIZADOS:
        bot.reply_to(message, "⚠️ *BLOQUEADO*", parse_mode="Markdown")
        return
    if not el_bot_es_admin(cid):
        bot.reply_to(message, "⚠️ *ERROR:* Dame permisos de *Admin*. 👷‍♂️")
        return

    comando = message.text.split()[0].lower().replace('/', '').split('@')[0]
    modo = comando if comando in MODOS_CONFIG else random.choice(list(MODOS_CONFIG.keys()))
    config = MODOS_CONFIG[modo]
    
    doc = collection.find_one({"chat_id": cid})
    historial_lista = doc['mensajes'] if doc else []
    instruccion_longitud = doc.get("longitud_pref", "de extensión media y equilibrada") if doc else "de extensión media y equilibrada"
    
    if len(historial_lista) < 5:
        bot.reply_to(message, "Hablen más, no hay suficiente chisme. 🥱")
        return

    bot.send_chat_action(cid, 'typing')
    
    if len(historial_lista) > 90:
        mensajes_ia = historial_lista[:30] + ["\n[... Salto Temporal ...]\n"] + historial_lista[len(historial_lista)//2-15 : len(historial_lista)//2+15] + ["\n[... Salto Temporal ...]\n"] + historial_lista[-30:]
    else:
        mensajes_ia = historial_lista

    try:
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    f"Eres {config['prompt']}. "
                    f"EXTENSIÓN: {instruccion_longitud}. "
                    "REGLAS CRÍTICAS (SÍGUELAS O MUERES):\n"
                    "1. ¡ACTÚA EL PERSONAJE! No seas un asistente aburrido. Intervén y búrlate del chisme mientras lo cuentas.\n"
                    "2. SATURACIÓN DE EMOJIS: Usa al menos 3 emojis temáticos POR PÁRRAFO. No escribas nada sin emojis inteligentes.\n"
                    "3. Usa SOLO nombres reales en *Negrita*.\n"
                    "4. Primera línea: 📌 *Estado del chat:* + frase creativa con emojis."
                )},
                {"role": "user", "content": f"Resume y comenta este chisme con muchísimos emojis:\n" + "\n".join(mensajes_ia)}
            ],
            temperature=0.8, # Subimos la temperatura para más creatividad
        )
        respuesta = completion.choices[0].message.content
        ranking = obtener_ranking(cid)
        enviar_con_plan_b(message, f"{config['anuncio']}\n\n{respuesta}{ranking}\n\n_— @donchismebot 🤖_")
    except:
        bot.reply_to(message, "¡El chisme explotó! ⚠️")

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    if (not GRUPOS_AUTORIZADOS or message.chat.id in GRUPOS_AUTORIZADOS):
        if message.text and not message.text.startswith('/'):
            cid = message.chat.id
            nombre = message.from_user.first_name
            texto_formateado = f"{nombre}: {message.text}"
            collection.update_one(
                {"chat_id": cid},
                {"$push": {"mensajes": {"$each": [texto_formateado], "$slice": -MAX_MENSAJES}}},
                upsert=True
            )
            verificar_y_limpiar_historial(cid)

if __name__ == "__main__":
    print("🚀 Iniciando Don Chismoso...")
    bot.remove_webhook()
    time.sleep(2)
    bot.infinity_polling(skip_pending=True, timeout=60)
