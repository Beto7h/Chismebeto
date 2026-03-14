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
    # Prueba de conexión
    db_client.admin.command('ping')
    print("✅ Conexión exitosa a MongoDB")
except Exception as e:
    print(f"❌ Error conectando a MongoDB: {e}")

MAX_MENSAJES = 500 

# --- PERSONALIZACIÓN ---
FRASES_BIENVENIDA = [
    "¡Hola! He llegado para poner orden a este caos. 💅",
    "¿Alguien dijo chisme? Ya estoy aquí para contarlo todo. ☕",
    "¡Llegó el que faltaba! Vamos a ver qué tanto han hablado. 🤖",
    "Prepárense, que vengo con la lengua afilada y el resumen listo. 🔥",
    "¡Hola, hola! Menudo desorden tienen aquí, por suerte ya llegué. ✨",
    "¿Mucho texto? No se preocupen, yo les traigo el salseo resumido. 📖",
    "He vuelto. ¿De qué me he perdido en este nido de chismes? 🤫",
    "¡Ayuda en camino! Aunque lo que ustedes necesitan es terapia por tanto chisme. 🙄",
    "¿Perdido en el salseo? Aquí tienes la guía de supervivencia. 🚩",
    "¡Reportándose el agente del chisme! ¿En qué puedo servirte? 🫡",
    "Pasaba por aquí y olí un salseo de los buenos... ¡Cuenten conmigo! 👃✨",
    "¡Llegó! Menos mal, porque este chat ya parecía un laberinto sin salida. 🌀",
    "¿Me extrañaron? No respondan, ya sé que sin mí no entienden nada. 😎",
    "¡Alto ahí! Dejen de escribir un segundo y miren lo que puedo hacer. 🛑🤖",
    "Vine a leer lo que ustedes no quieren leer. ¡A sus órdenes! 🫡📜"
]

MODOS_CONFIG = {
    "hater": {"prompt": "Crítico sarcástico y amargado. Describe el 'Estado del chat' con desprecio.", "anuncio": "✨ ᴍᴏᴅᴏ ʜᴀᴛᴇʀ ✨"},
    "picoso": {"prompt": "Rey del salseo y peleas. Describe el 'Estado del chat' como un escándalo.", "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️"},
    "chisme": {"prompt": "Vecina chismosa de barrio. Describe el 'Estado del chat' como un rumor de pasillo.", "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍𝖎𝖘𝖒𝖊 🤫"},
    "noticiero": {"prompt": "Reportero de noticias dramáticas. Describe el 'Estado del chat' como un informe civil urgente.", "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"},
    "drama": {"prompt": "Escritor de telenovelas trágicas. Describe el 'Estado del chat' como una tragedia épica.", "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 🎭"},
    "zen": {"prompt": "Guía espiritual y relajado. Describe el 'Estado del chat' como flujo de energía cósmica.", "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"},
    "caos": {"prompt": "Agente del caos total. Describe el 'Estado del chat' como un colapso mental colectivo.", "anuncio": "🌀 𝑴𝑶𝑫𝑶 𝑪𝑨𝑶𝑺 🌀"}
}

# --- FUNCIONES DE PERSISTENCIA (MONGODB) ---

def obtener_historial(chat_id):
    """Recupera la lista de mensajes de la DB para un chat específico"""
    doc = collection.find_one({"chat_id": chat_id})
    return doc['mensajes'] if doc else []

def guardar_mensaje_db(chat_id, texto_formateado):
    """Guarda un mensaje nuevo y mantiene el límite de 500 en la DB"""
    collection.update_one(
        {"chat_id": chat_id},
        {"$push": {"mensajes": {"$each": [texto_formateado], "$slice": -MAX_MENSAJES}}},
        upsert=True
    )

def el_bot_es_admin(chat_id):
    if chat_id > 0: return True
    try:
        me = bot.get_chat_member(chat_id, bot.get_me().id)
        return me.status in ['administrator', 'creator']
    except:
        return False

def obtener_ranking(chat_id):
    mensajes = obtener_historial(chat_id)
    if not mensajes: return ""
    
    nombres_reales = []
    for msg in mensajes:
        try:
            # Extrae el nombre real entre paréntesis
            nombre = msg.split(' (')[1].split('):')[0]
            nombres_reales.append(nombre)
        except:
            continue

    if not nombres_reales: return ""
    conteo = Counter(nombres_reales)
    mas_activo, num_mensajes = conteo.most_common(1)[0]
    
    ranking_msg = f"\n\n🏆 *RANKING DEL CHISME:*\n"
    ranking_msg += f"👑 *El más activo:* {mas_activo} ({num_mensajes} mensajes)\n"
    ranking_msg += f"🔥 _Analizando los últimos {len(mensajes)} mensajes de la DB..._\n"
    return ranking_msg

# --- HANDLERS DE COMANDOS ---

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    saludo_aleatorio = random.choice(FRASES_BIENVENIDA)
    
    msg = f"✨ *{saludo_aleatorio}* ✨\n━━━━━━━━━━━━━━━━━━\n"
    msg += "Soy *Don Chismoso*, la IA que resume el salseo de tus grupos. 🤖\n\n"
    msg += f"📊 *CAPACIDAD:* Leo hasta *{MAX_MENSAJES} mensajes* guardados en los grupos. ⏳\n\n"
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
    msg += "💡 *REQUISITOS:* Ser *Admin* y grupo *Autorizado* ✅\n\n"
    msg += "👤 *Desarrollador:* Albert ✨"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['resumen', 'hater', 'picoso', 'chisme', 'noticiero', 'drama', 'zen', 'caos'])
def cmd_resumen(message):
    cid = message.chat.id
    if GRUPOS_AUTORIZADOS and cid not in GRUPOS_AUTORIZADOS:
        bot.reply_to(message, "⚠️ *FUNCIÓN BLOQUEADA* ⚠️\nBot aun en construcción ✨", parse_mode="Markdown")
        return
    if not el_bot_es_admin(cid):
        bot.reply_to(message, "⚠️ *ERROR:* Necesito ser *Admin*. 👷‍♂️⚙️")
        return

    comando = message.text.split()[0].lower().replace('/', '').split('@')[0]
    modo = comando if comando in MODOS_CONFIG else random.choice(list(MODOS_CONFIG.keys()))
    
    # Obtener historial desde MongoDB
    historial_lista = obtener_historial(cid)
    
    if len(historial_lista) < 5:
        bot.reply_to(message, "Hablen más, no hay suficiente chisme en la base de datos. 🥱")
        return

    config = MODOS_CONFIG[modo]
    bot.send_chat_action(cid, 'typing')
    
    try:
        historial_texto = "\n".join(historial_lista)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    f"Eres un experto resumidor con estilo {config['prompt']}. "
                    "REGLAS OBLIGATORIAS:\n"
                    "1. Usa UN SOLO asterisco (*) para resaltar nombres y frases.\n"
                    "2. PROHIBIDO usar (**).\n"
                    "3. Escribe en VARIOS PÁRRAFOS cortos. No amontones el texto.\n"
                    "4. Usa nombres reales (están entre paréntesis).\n"
                    "5. La primera línea DEBE ser '📌 *Estado del chat:*' seguida de una descripción CREATIVA basada en los mensajes, resaltada con (*).\n"
                    "6. Usa muchísimos emojis y jerga coloquial."
                )},
                {"role": "user", "content": f"Resume este historial separando temas:\n{historial_texto}"}
            ],
        )
        respuesta = completion.choices[0].message.content
        ranking = obtener_ranking(cid)
        firma = f"\n\n_— Generado por @donchismebot 🤖 | Desarrollado por ᴀʟʙᴇʀᴛ ✨_"
        bot.reply_to(message, f"{config['anuncio']}\n\n{respuesta}{ranking}{firma}", parse_mode="Markdown")
    except Exception as e:
        print(f"Error Groq: {e}")
        bot.reply_to(message, "¡El chisme explotó! ⚠️")

# --- ESCUCHA DE MENSAJES ---

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    # Verificamos si el chat está autorizado
    if not GRUPOS_AUTORIZADOS or message.chat.id in GRUPOS_AUTORIZADOS:
        # Solo guardamos texto que no sea un comando
        if message.text and not message.text.startswith('/'):
            cid = message.chat.id
            username = f"@{message.from_user.username}" if message.from_user.username else "SinUser"
            nombre = message.from_user.first_name
            
            texto_formateado = f"{username} ({nombre}): {message.text}"
            
            # Guardamos directamente en MongoDB
            guardar_mensaje_db(cid, texto_formateado)

# --- INICIO DEL BOT ---
if __name__ == "__main__":
    print("🤖 Don Chismoso está activo y conectado a la DB...")
    bot.remove_webhook()
    bot.polling(none_stop=True)
