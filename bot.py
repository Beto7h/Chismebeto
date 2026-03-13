import os
import random
import telebot
from groq import Groq
from collections import Counter

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')
# IDs de grupos VIP en Koyeb separados por comas (Ej: -100123,-100456)
AUTORIZADOS_RAW = os.getenv('GRUPOS_AUTORIZADOS', '')
GRUPOS_AUTORIZADOS = [int(i.strip()) for i in AUTORIZADOS_RAW.split(',') if i.strip()]

client = Groq(api_key=GROQ_KEY)
bot = telebot.TeleBot(TOKEN)

chat_data = {}
MAX_MENSAJES = 500

MODOS_CONFIG = {
    "hater": {"prompt": "Crítico sarcástico. Usa **NEGRITAS**, *cursivas* y MUCHOS EMOJIS 🙄💅. MAYÚSCULAS para lo más tonto.", "anuncio": "✨ 𝕸𝖔𝖉𝖔 𝕳𝖆𝖙𝖊𝖗 ✨"},
    "picoso": {"prompt": "Rey del salseo. Busca peleas e indirectas. Usa **NEGRITAS**, *cursivas* y MUCHOS EMOJIS 🌶️🔥.", "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️"},
    "chisme": {"prompt": "Vecina chismosa. Usa **NEGRITA** para nombres y *cursivas* para rumores. MUCHOS EMOJIS ☕🤫.", "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍𝖎𝖘𝖒𝖊 🤫"},
    "noticiero": {"prompt": "Noticiero dramático. **NEGRITA** en titulares y MAYÚSCULAS en 'ÚLTIMA HORA'. MUCHOS EMOJIS 🚨🎤.", "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"},
    "drama": {"prompt": "Escritor de novelas. **NEGRITA** en traiciones y *cursivas* en lamentos. MUCHOS EMOJIS 💔😭.", "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 🎭"},
    "zen": {"prompt": "Guía espiritual. **NEGRITA** en sabiduría y *cursivas* en paz. MUCHOS EMOJIS 🌿🪷.", "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"},
    "caos": {"prompt": "Agente del caos. Mezcla todo: **NEGRITAS**, *cursivas* y MAYÚSCULAS. MUCHOS EMOJIS 🌀🤡.", "anuncio": "🌀 𝑴𝑶𝑫𝑶 𝑪𝑨𝑶𝑺 🌀"}
}

# --- FUNCIONES DE APOYO ---

def el_bot_es_admin(chat_id):
    """Verifica si el bot tiene rango de admin en el grupo."""
    if chat_id > 0: return True
    try:
        me = bot.get_chat_member(chat_id, bot.get_me().id)
        return me.status in ['administrator', 'creator']
    except:
        return False

def obtener_ranking(cid):
    """Calcula quién ha enviado más mensajes en el bloque actual."""
    if cid not in chat_data or not chat_data[cid]:
        return ""
    
    # Extraer nombres (están guardados como 'Nombre: mensaje')
    usuarios = [msg.split(':')[0] for msg in chat_data[cid]]
    conteo = Counter(usuarios)
    
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
    msg += "Soy **Don Chismoso**, la IA diseñada para analizar y resumir tus grupos con diferentes personalidades. 🤖\n\n"
    msg += "📊 **CAPACIDAD DE LECTURA:**\n"
    msg += f"Puedo leer hasta **{MAX_MENSAJES} mensajes como máximo**. ¡Si el chisme es largo, solo recordaré lo más reciente! 🧠⏳\n\n"
    msg += "📌 **COMANDOS Y FUNCIONES:**\n"
    msg += "• `/hater` ➔ El Crítico sarcástico 🙄\n"
    msg += "• `/picoso` ➔ El Salseo picante 🌶️\n"
    msg += "• `/chisme` ➔ La Vecina chismosa ☕\n"
    msg += "• `/noticiero` ➔ Titulares de impacto 🚨\n"
    msg += "• `/drama` ➔ Telenovela trágica 🎭\n"
    msg += "• `/zen` ➔ Paz y armonía 🧘\n"
    msg += "• `/resumen` ➔ Modo sorpresa 🎲\n\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "💡 **REQUISITOS:**\n1. Ser **Administrador** 👷‍♂️\n2. Grupo **Autorizado** ✅\n\n"
    msg += "👤 **Creador y Desarrollador:** @Beto7h ✨"
    bot.reply_to(message, msg, parse_mode="Markdown")

@bot.message_handler(commands=['resumen', 'hater', 'picoso', 'chisme', 'noticiero', 'drama', 'zen', 'caos'])
def cmd_resumen(message):
    cid = message.chat.id

    # 1. ¿EL GRUPO ES VIP?
    if GRUPOS_AUTORIZADOS and cid not in GRUPOS_AUTORIZADOS:
        bot.reply_to(message, (
            "⚠️ **FUNCIÓN BLOQUEADA** ⚠️\n\nEste grupo no está autorizado para generar resúmenes.\n"
            "Contacta al creador: @Beto7h ✨"
        ), parse_mode="Markdown")
        return

    # 2. ¿EL BOT ES ADMIN?
    if not el_bot_es_admin(cid):
        bot.reply_to(message, "⚠️ **¡ERROR!** Necesito ser **Administrador** para leer los mensajes. 👷‍♂️⚙️")
        return

    # Selección de modo
    comando = message.text.split()[0].replace('/', '').split('@')[0].lower()
    modo = comando if comando in MODOS_CONFIG else random.choice(list(MODOS_CONFIG.keys()))
    
    if cid not in chat_data or len(chat_data[cid]) < 5:
        bot.reply_to(message, "Hablen más, no tengo suficiente chisme todavía. 🥱")
        return

    config = MODOS_CONFIG[modo]
    bot.send_chat_action(cid, 'typing')
    
    try:
        historial = "\n".join(chat_data[cid])
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": config['prompt']},
                {"role": "user", "content": f"Resume este chat con negritas, cursivas y muchos emojis:\n{historial}"}
            ],
        )
        respuesta = completion.choices[0].message.content
        ranking = obtener_ranking(cid)
        firma = f"\n\n_— Generado por @donchismebot 🤖 | Desarrollado por @Beto7h ✨_"
        
        bot.reply_to(message, f"{config['anuncio']}\n\n{respuesta}{ranking}{firma}", parse_mode="Markdown")
    except Exception as e:
        bot.reply_to(message, "¡El chisme explotó! Intenta de nuevo más tarde. ⚠️")

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    """Guarda mensajes solo si el grupo es VIP para ahorrar memoria."""
    if not GRUPOS_AUTORIZADOS or message.chat.id in GRUPOS_AUTORIZADOS:
        if message.text and not message.text.startswith('/'):
            cid = message.chat.id
            if cid not in chat_data: chat_data[cid] = []
            
            user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
            chat_data[cid].append(f"{user}: {message.text}")
            
            if len(chat_data[cid]) > MAX_MENSAJES:
                chat_data[cid].pop(0)

bot.remove_webhook()
bot.polling(none_stop=True)
