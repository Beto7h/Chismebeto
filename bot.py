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
    "hater": {"prompt": "Crítico sarcástico. Usa **NEGRITAS**, *cursivas* y MUCHOS EMOJIS 🙄💅. Usa solo nombres (no @). Describe el 'Estado del chat' con desprecio.", "anuncio": "✨ 𝕸𝖔𝖉𝖔 𝕳𝖆𝖙𝖊𝖗 ✨"},
    "picoso": {"prompt": "Rey del salseo. Busca peleas. Usa **NEGRITAS**, *cursivas* y MUCHOS EMOJIS 🌶️🔥. Usa solo nombres (no @). Describe el 'Estado del chat' como algo escandaloso.", "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️"},
    "chisme": {"prompt": "Vecina chismosa. Usa **NEGRITA** para nombres y *cursivas* para rumores. MUCHOS EMOJIS ☕🤫. Describe el 'Estado del chat' como un rumor de barrio.", "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍𝖎𝖘𝖒𝖊 🤫"},
    "noticiero": {"prompt": "Noticiero dramático. **NEGRITA** en titulares. MUCHOS EMOJIS 🚨🎤. Usa solo nombres (no @). Describe el 'Estado del chat' como un reporte de situación civil.", "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"},
    "drama": {"prompt": "Escritor de novelas. **NEGRITA** en traiciones. MUCHOS EMOJIS 💔😭. Usa solo nombres (no @). Describe el 'Estado del chat' como el clima de una tragedia.", "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 🎭"},
    "zen": {"prompt": "Guía espiritual. **NEGRITA** en sabiduría. MUCHOS EMOJIS 🌿🪷. Usa solo nombres (no @). Describe el 'Estado del chat' como un flujo de energía.", "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"},
    "caos": {"prompt": "Agente del caos. Mezcla todo con MUCHOS EMOJIS 🌀🤡. Usa solo nombres (no @). Describe el 'Estado del chat' como un colapso mental.", "anuncio": "🌀 𝑴𝑶𝑫𝑶 𝑪𝑨𝑶𝑺 🌀"}
}

# --- FUNCIONES DE APOYO ---

def el_bot_es_admin(chat_id):
    if chat_id > 0: return True
    try:
        me = bot.get_chat_member(chat_id, bot.get_me().id)
        return me.status in ['administrator', 'creator']
    except: return False

def obtener_ranking(cid):
    if cid not in chat_data or not chat_data[cid]: return ""
    # En el ranking sí mantenemos el @username para identificar
    usuarios_con_arroba = [msg.split(' (')[0] for msg in chat_data[cid]]
    conteo = Counter(usuarios_con_arroba)
    mas_activo, num_mensajes = conteo.most_common(1)[0]
    
    ranking_msg = f"\n\n🏆 **RANKING DEL CHISME:**\n"
    ranking_msg += f"👑 **El más activo:** {mas_activo} ({num_mensajes} mensajes)\n"
    ranking_msg += f"🔥 *Analizando los últimos {len(chat_data[cid])} mensajes...*\n"
    return ranking_msg

# --- HANDLERS ---

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    saludo = "¡Hola! He llegado para poner orden a este caos. 💅"
    msg = f"✨ **{saludo}** ✨\n━━━━━━━━━━━━━━━━━━\n"
    msg += "Soy **Don Chismoso**, la IA diseñada para analizar y resumir tus grupos. 🤖\n\n"
    msg += f"📊 **CAPACIDAD:** Leo hasta **{MAX_MENSAJES} mensajes**. 🧠⏳\n\n"
    msg += "📌 **MODOS:** `/hater`, `/picoso`, `/chisme`, `/noticiero`, `/drama`, `/zen`, `/resumen`\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "👤 **Creador y Desarrollador:** @Beto7h ✨"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['resumen', 'hater', 'picoso', 'chisme', 'noticiero', 'drama', 'zen', 'caos'])
def cmd_resumen(message):
    cid = message.chat.id
    if GRUPOS_AUTORIZADOS and cid not in GRUPOS_AUTORIZADOS:
        bot.reply_to(message, "⚠️ **FUNCIÓN BLOQUEADA** ⚠️\nContacta al creador: @Beto7h ✨")
        return

    if not el_bot_es_admin(cid):
        bot.reply_to(message, "⚠️ **¡ERROR!** Necesito ser **Administrador** para leer mensajes. 👷‍♂️⚙️")
        return

    comando = message.text.split()[0].replace('/', '').split('@')[0].lower()
    modo = comando if comando in MODOS_CONFIG else random.choice(list(MODOS_CONFIG.keys()))
    
    if cid not in chat_data or len(chat_data[cid]) < 5:
        bot.reply_to(message, "Hablen más, no tengo suficiente chisme todavía. 🥱")
        return

    config = MODOS_CONFIG[modo]
    bot.send_chat_action(cid, 'typing')
    
    try:
        # Enviamos los mensajes a la IA aclarando que use solo nombres para el resumen
        historial = "\n".join(chat_data[cid])
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": f"{config['prompt']}\nIMPORTANTE: No menciones @usernames en el cuerpo del resumen, usa solo el nombre de la persona. Incluye una sección al inicio llamada '📌 Estado del chat:' que describa el ambiente con el estilo del modo elegido."},
                {"role": "user", "content": f"Resume este chat:\n{historial}"}
            ],
        )
        respuesta = completion.choices[0].message.content
        ranking = obtener_ranking(cid)
        firma = f"\n\n_— Generado por @donchismebot 🤖 | Desarrollado por @Beto7h ✨_"
        
        bot.reply_to(message, f"{config['anuncio']}\n\n{respuesta}{ranking}{firma}", parse_mode="Markdown")
    except Exception:
        bot.reply_to(message, "¡El chisme explotó! Intenta más tarde. ⚠️")

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    if not GRUPOS_AUTORIZADOS or message.chat.id in GRUPOS_AUTORIZADOS:
        if message.text and not message.text.startswith('/'):
            cid = message.chat.id
            if cid not in chat_data: chat_data[cid] = []
            
            # Guardamos el Username para el ranking y el Nombre para la IA
            username = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            nombre_real = message.from_user.first_name
            
            # Formato: "@usuario (Nombre): mensaje" para que la IA sepa qué nombre usar
            chat_data[cid].append(f"{username} ({nombre_real}): {message.text}")
            
            if len(chat_data[cid]) > MAX_MENSAJES:
                chat_data[cid].pop(0)

bot.remove_webhook()
bot.polling(none_stop=True)
