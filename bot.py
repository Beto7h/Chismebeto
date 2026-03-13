import os
import random
import telebot
from groq import Groq
from collections import Counter

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')
AUTORIZADOS_RAW = os.getenv('GRUPOS_AUTORIZADOS', '')
GRUPOS_AUTORIZADOS = [int(i.strip()) for i in AUTORIZADOS_RAW.split(',') if i.strip()]

client = Groq(api_key=GROQ_KEY)
bot = telebot.TeleBot(TOKEN)

chat_data = {}
MAX_MENSAJES = 500

MODOS_CONFIG = {
    "hater": {"prompt": "Crítico sarcástico y amargado. Describe el 'Estado del chat' con desprecio.", "anuncio": "✨ ᴍᴏᴅᴏ ʜᴀᴛᴇʀ ✨"},
    "picoso": {"prompt": "Rey del salseo y peleas. Describe el 'Estado del chat' como un escándalo.", "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️"},
    "chisme": {"prompt": "Vecina chismosa de barrio. Describe el 'Estado del chat' como un rumor de pasillo.", "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍𝖎𝖘𝖒𝖊 🤫"},
    "noticiero": {"prompt": "Reportero de noticias dramáticas. Describe el 'Estado del chat' como un informe civil.", "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"},
    "drama": {"prompt": "Escritor de telenovelas trágicas. Describe el 'Estado del chat' como una tragedia.", "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 🎭"},
    "zen": {"prompt": "Guía espiritual y relajado. Describe el 'Estado del chat' como flujo de energía.", "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"},
    "caos": {"prompt": "Agente del caos total. Describe el 'Estado del chat' como un colapso mental.", "anuncio": "🌀 𝑴𝑶𝑫𝑶 𝑪𝑨𝑶𝑺 🌀"}
}

# --- FUNCIONES DE APOYO ---

def el_bot_es_admin(chat_id):
    if chat_id > 0: return True
    try:
        me = bot.get_chat_member(chat_id, bot.get_me().id)
        return me.status in ['administrator', 'creator']
    except:
        return False

def obtener_ranking(cid):
    if cid not in chat_data or not chat_data[cid]:
        return ""
    usuarios = [msg.split(' (')[0] for msg in chat_data[cid]]
    conteo = Counter(usuarios)
    mas_activo, num_mensajes = conteo.most_common(1)[0]
    
    ranking_msg = f"\n\n🏆 *RANKING DEL CHISME:*\n"
    ranking_msg += f"👑 *El más activo:* {mas_activo} ({num_mensajes} mensajes)\n"
    ranking_msg += f"🔥 _Analizando los últimos {len(chat_data[cid])} mensajes..._\n"
    return ranking_msg

# --- HANDLERS ---

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    saludo = "¡Hola! He llegado para poner orden a este caos. 💅"
    # Asegúrate de que esta línea tenga la 'f' al principio
    msg = f"✨ *{saludo}* ✨\n━━━━━━━━━━━━━━━━━━\n"
    msg += "Soy *Don Chismoso*, la IA que resume el salseo de tus grupos. 🤖\n\n"
    
    # Aquí es donde se corrige para que muestre el número 500
    msg += f"📊 *CAPACIDAD:* Leo hasta *{MAX_MENSAJES} mensajes*. ⏳\n\n"
    
    msg += "📌 *COMANDOS DISPONIBLES:*\n"
    msg += "• `/chisme` ➔ Resumen tipo vecina criticona. ☕\n"
    msg += "• `/hater` ➔ Resumen tóxico y sarcástico. 🙄\n"
    msg += "• `/picoso` ➔ Busca peleas e indirectas. 🌶️\n"
    msg += "• `/noticiero` ➔ Reporte dramático de última hora. 🚨\n"
    msg += "• `/drama` ➔ Como si fuera una telenovela trágica. 🎭\n"
    msg += "• `/zen` ➔ Resumen pacífico y espiritual. 🧘\n"
    msg += "• `/caos` ➔ Una mezcla sin sentido y divertida. 🌀\n"
    msg += "• `/resumen` ➔ Elijo un modo al azar para ti. 🎲\n\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "💡 *REQUISITOS:* Ser *Admin* y grupo *Autorizado* ✅\n\n"
    msg += "👤 *Desarrollador:* @Beto7h ✨"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['resumen', 'hater', 'picoso', 'chisme', 'noticiero', 'drama', 'zen', 'caos'])
def cmd_resumen(message):
    cid = message.chat.id

    if GRUPOS_AUTORIZADOS and cid not in GRUPOS_AUTORIZADOS:
        bot.reply_to(message, "⚠️ *FUNCIÓN BLOQUEADA* ⚠️\nContacta a @Beto7h ✨", parse_mode="Markdown")
        return

    if not el_bot_es_admin(cid):
        bot.reply_to(message, "⚠️ *ERROR:* Necesito ser *Admin*. 👷‍♂️⚙️")
        return

    comando = message.text.split()[0].lower().replace('/', '').split('@')[0]
    modo = comando if comando in MODOS_CONFIG else random.choice(list(MODOS_CONFIG.keys()))
    
    if cid not in chat_data or len(chat_data[cid]) < 5:
        bot.reply_to(message, "Hablen más, no hay suficiente chisme. 🥱")
        return

    config = MODOS_CONFIG[modo]
    bot.send_chat_action(cid, 'typing')
    
    try:
        historial = "\n".join(chat_data[cid])
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    f"Eres un experto resumidor con estilo {config['prompt']}. "
                    "REGLAS OBLIGATORIAS:\n"
                    "1. Usa UN SOLO asterisco (*) para resaltar nombres y frases.\n"
                    "2. PROHIBIDO usar dobles asteriscos (**).\n"
                    "3. Escribe en VARIOS PÁRRAFOS cortos. No amontones todo el texto.\n"
                    "4. Si hay varios temas de conversación, sepáralos con puntos de lista o saltos de línea.\n"
                    "5. Empieza con '📌 *Estado del chat:*' seguido de una descripción resaltada con (*).\n"
                    "6. Usa nombres reales y muchos emojis."
                )},
                {"role": "user", "content": f"Resume este historial separando los temas importantes:\n{historial}"}
            ],
        )
        respuesta = completion.choices[0].message.content
        ranking = obtener_ranking(cid)
        firma = f"\n\n_— Generado por @donchismebot 🤖 | Desarrollado por @Beto7h ✨_"
        
        bot.reply_to(message, f"{config['anuncio']}\n\n{respuesta}{ranking}{firma}", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "¡El chisme explotó! ⚠️")

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    if not GRUPOS_AUTORIZADOS or message.chat.id in GRUPOS_AUTORIZADOS:
        if message.text and not message.text.startswith('/'):
            cid = message.chat.id
            if cid not in chat_data: chat_data[cid] = []
            
            username = f"@{message.from_user.username}" if message.from_user.username else "SinUser"
            nombre = message.from_user.first_name
            chat_data[cid].append(f"{username} ({nombre}): {message.text}")
            
            if len(chat_data[cid]) > MAX_MENSAJES:
                chat_data[cid].pop(0)

bot.remove_webhook()
bot.stop_polling()
bot.polling(none_stop=True)
