import os
import random
import telebot
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
        "prompt": "un hater cínico y amargado. Mete tu cuchara con desprecio y usa memes como 'quedaste 🤡' o 'mucho texto'.",
        "anuncio": "✨ ᴍᴏᴅᴏ ʜᴀᴛᴇʀ (ᴛÓxɪᴄᴏ) ✨"
    },
    "drama": {
        "prompt": "un amigo exagerado y escandaloso. Opina como si te estuviera dando un infarto de la impresión ante cada detalle.",
        "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 (𝐄𝐗𝐓𝐑𝐄𝐌𝐎) 🎭"
    },
    "chisme": {
        "prompt": "una vecina criticona de barrio. Mete tu cuchara con malicia, sospechas y refranes populares.",
        "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍ɪꜱᴍᴇ 🤫"
    },
    "picoso": {
        "prompt": "un busca-pleitos e instigador. Opina echando leña al fuego para que los usuarios se peleen entre ellos.",
        "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️"
    },
    "noticiero": {
        "prompt": "un reportero de nota roja dramático. Opina editorialmente sobre la decadencia de valores en este chat.",
        "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"
    },
    "zen": {
        "prompt": "un guía espiritual harto de la gente. Opina sobre las vibras bajas y el mal karma que emana este grupo.",
        "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"
    },
    "caos": {
        "prompt": "un agente del caos desquiciado. Opina cosas que no tienen sentido o teorías conspirativas locas.",
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

def obtener_ranking(chat_id):
    doc = collection.find_one({"chat_id": chat_id})
    mensajes = doc['mensajes'] if doc else []
    if not mensajes: return ""
    
    nombres_reales = []
    for msg in mensajes:
        try:
            nombre = msg.split(' (')[1].split('):')[0]
            nombres_reales.append(nombre)
        except: continue

    if not nombres_reales: return ""
    conteo = Counter(nombres_reales)
    ranking_msg = f"\n\n🏆 *RANKING DEL CHISME:*\n"
    for i, (nombre, cant) in enumerate(conteo.most_common(3), 1):
        medalla = ["👑", "🥈", "🥉"][i-1]
        ranking_msg += f"{medalla} *{nombre}:* {cant} mensajes\n"
    return ranking_msg

def enviar_con_plan_b(message, texto_final):
    """Envía con Markdown, si falla, usa texto plano con frase de error personalizada."""
    try:
        bot.reply_to(message, texto_final, parse_mode="Markdown")
    except Exception as e:
        print(f"Plan B activado por error: {e}")
        frase_fail = random.choice(ERRORES_PERSONALIDAD)
        # Limpieza de símbolos problemáticos para modo seguro
        texto_seguro = texto_final.replace("_", "").replace("*", "").replace(">", "—")
        bot.reply_to(message, f"{frase_fail}\n\n{texto_seguro}")

# --- HANDLERS DE COMANDOS ---

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    saludo_aleatorio = random.choice(FRASES_BIENVENIDA)
    
    msg = f"✨ *{saludo_aleatorio}* ✨\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "Soy *Don Chismoso*, la IA que resume los mensajes de tus grupos. 🤖\n\n"
    msg += f"📊 *CAPACIDAD:* Leo hasta *{MAX_MENSAJES} mensajes* guardados. ⏳\n\n"
    msg += "📌 *COMANDOS DISPONIBLES:*\n"
    msg += "• `/chisme` ➔ Estilo vecina criticona. ☕\n"
    msg += "• `/hater` ➔ Estilo tóxico y sarcástico. 🙄\n"
    msg += "• `/picoso` ➔ Busca peleas e indirectas. 🌶️\n"
    msg += "• `/noticiero` ➔ Reporte dramático urgente. 🚨\n"
    msg += "• `/drama` ➔ Telenovela trágica. 🎭\n"
    msg += "• `/zen` ➔ Paz y armonía espiritual. 🧘\n"
    msg += "• `/caos` ➔ Mezcla sin sentido. 🌀\n"
    msg += "• `/resumen` ➔ Modo sorpresa. 🎲\n\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "💡 *REQUISITOS:* Ser *Admin* y grupo *Autorizado* ✅\n"
    msg += "🧨 *EXTRAS:* `/restart` para borrar la memoria (Solo Admins).\n\n"
    msg += "👤 *Desarrollador:* A.B ✨"
    
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['restart'])
def cmd_restart(message):
    cid = message.chat.id
    if not el_bot_es_admin(cid):
        bot.reply_to(message, "⚠️ Necesito ser *Admin* para gestionar mi memoria.")
        return
    
    status = bot.get_chat_member(cid, message.from_user.id).status
    if status not in ['administrator', 'creator'] and cid < 0:
        bot.reply_to(message, "❌ ¡Atrás! Solo los *admins* pueden purgar mi memoria. 💅")
        return

    try:
        collection.update_one({"chat_id": cid}, {"$set": {"mensajes": []}})
        bot.reply_to(message, "✨ *MEMORIA PURGADA* ✨\n\nHistorial borrado. ¡Que empiece el nuevo salseo! 😈🔥", parse_mode="Markdown")
    except:
        bot.reply_to(message, "Hubo un error al intentar olvidar... mi cerebro es demasiado grande. 🧠")

@bot.message_handler(commands=['resumen', 'hater', 'picoso', 'chisme', 'noticiero', 'drama', 'zen', 'caos'])
def cmd_resumen(message):
    cid = message.chat.id
    if GRUPOS_AUTORIZADOS and cid not in GRUPOS_AUTORIZADOS:
        bot.reply_to(message, "⚠️ *BLOQUEADO* ⚠️", parse_mode="Markdown")
        return
    if not el_bot_es_admin(cid):
        bot.reply_to(message, "⚠️ *ERROR:* Dame permisos de *Admin*. 👷‍♂️")
        return

    comando = message.text.split()[0].lower().replace('/', '').split('@')[0]
    modo = comando if comando in MODOS_CONFIG else random.choice(list(MODOS_CONFIG.keys()))
    config = MODOS_CONFIG[modo]
    
    doc = collection.find_one({"chat_id": cid})
    historial_lista = doc['mensajes'] if doc else []
    
    if len(historial_lista) < 5:
        bot.reply_to(message, "Hablen más, no hay suficiente salseo para un análisis digno. 🥱")
        return

    bot.send_chat_action(cid, 'typing')
    
    try:
        historial_texto = "\n".join(historial_lista)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    f"Eres {config['prompt']}. "
                    "REGLAS DE FORMATO CRÍTICAS:\n"
                    "1. Resumen: Usa texto normal. Nombres en *Negrita*.\n"
                    "2. Tu Opinión: Después de cada párrafo, DEBES poner tu opinión en una línea nueva que empiece con '>' y el texto en _\"cursiva, comillas y emojis\"_.\n"
                    "   Ejemplo: > _\"Es que no puedo con esto, qué oso... 🙄💅\"_\n"
                    "3. PROHIBIDO usar cursivas fuera de tus opiniones.\n"
                    "4. La primera línea DEBE ser '📌 *Estado del chat:*' seguida de una frase creativa."
                )},
                {"role": "user", "content": f"Resume y opina sobre este chisme:\n{historial_texto}"}
            ],
        )
        
        respuesta = completion.choices[0].message.content
        ranking = obtener_ranking(cid)
        firma = f"\n\n— @donchismebot 🤖 | Dev: Albert ✨"
        
        enviar_con_plan_b(message, f"{config['anuncio']}\n\n{respuesta}{ranking}{firma}")

    except Exception as e:
        print(f"Error Groq: {e}")
        bot.reply_to(message, "¡El chisme explotó! ⚠️")

# --- ESCUCHA DE MENSAJES ---

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    if not GRUPOS_AUTORIZADOS or message.chat.id in GRUPOS_AUTORIZADOS:
        if message.text and not message.text.startswith('/'):
            cid = message.chat.id
            username = f"@{message.from_user.username}" if message.from_user.username else "SinUser"
            nombre = message.from_user.first_name
            texto_formateado = f"{username} ({nombre}): {message.text}"
            
            collection.update_one(
                {"chat_id": cid},
                {"$push": {"mensajes": {"$each": [texto_formateado], "$slice": -MAX_MENSAJES}}},
                upsert=True
            )

if __name__ == "__main__":
    print("🤖 Don Chismoso activo con Plan B y Opiniones...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
