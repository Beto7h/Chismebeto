import os
import random
import telebot
from groq import Groq
from collections import Counter

# --- CONFIGURACIÓN ---
# Asegúrate de tener estas variables en Koyeb: TELEGRAM_TOKEN y GROQ_API_KEY
TOKEN = os.getenv('TELEGRAM_TOKEN')
GROQ_KEY = os.getenv('GROQ_API_KEY')

print("--- INICIANDO DON CHISMOSO (LLAMA 3 / GROQ) ---")

client = Groq(api_key=GROQ_KEY)
bot = telebot.TeleBot(TOKEN)

chat_data = {}
MAX_MENSAJES = 500

# Modos de resumen adaptados a Llama 3
MODOS_CONFIG = {
    "hater": {"prompt": "Eres un crítico sarcástico. Resume el chat burlándote de los usuarios. Usa 🙄, 💅.", "anuncio": "✨ 𝕸𝖔𝖉𝖔 𝕳𝖆𝖙𝖊𝖗 ✨"},
    "picoso": {"prompt": "Eres el rey del salseo. Resume señalando momentos incómodos y chismes picantes. Usa 🌶️, 🔥.", "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️"},
    "chisme": {"prompt": "Eres una vecina chismosa. Cuéntame los chismes calientes del grupo. Usa ☕, 🤫.", "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍𝖎𝖘𝖒𝖊 🤫"},
    "noticiero": {"prompt": "Eres un presentador de noticias dramático. Resume con titulares impactantes. Usa 🚨, 🎤.", "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"},
    "drama": {"prompt": "Eres escritor de telenovelas. Resume el chat como una tragedia llena de traición. Usa 💔, 😭.", "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 🎭"},
    "zen": {"prompt": "Eres un guía espiritual. Resume el chat con mucha paz y vibras positivas. Usa 🌿, 🪷.", "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"},
    "caos": {"prompt": "Eres un agente del caos. Resume de forma loca, con emojis extraños y frases raras. Usa 🌀, 🤡.", "anuncio": "🌀 𝑴𝑶𝑫𝑶 𝑪𝑨𝑶𝑺 🌀"}
}

FRASES_ENTRADA = [
    "He llegado para juzgar sus conversaciones. No esperen piedad. 💅",
    "¡Hola! Soy el que lee todo lo que escriben mientras ustedes no miran. 👁️",
    "¿Buscaban un resumen o una humillación pública? Yo hago ambas. 🤖",
    "Si el chisme fuera electricidad, este grupo sería una central nuclear. ⚡",
    "¡Llegó el jefe! Despejen el área y suelten el veneno. 🐍"
]

def generar_mensaje_pro(saludo):
    """Formato de bienvenida exacto solicitado por el usuario."""
    msg = f"✨ **{saludo}** ✨\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "Soy **Don Chismoso**, la IA que pone orden (o más caos) a tus grupos. 🤖\n\n"
    msg += "📌 **MODOS DE ANÁLISIS:**\n"
    msg += "• `/hater` ➔ El resumen más amargado 💅\n"
    msg += "• `/picoso` ➔ Salseo y momentos incómodos 🌶️\n"
    msg += "• `/chisme` ➔ Reporte de vecina metiche ☕\n"
    msg += "• `/noticiero` ➔ Titulares de última hora 🚨\n"
    msg += "• `/drama` ➔ Tragedia de telenovela 🎭\n"
    msg += "• `/zen` ➔ Resumen en paz y armonía 🧘\n"
    msg += "• `/resumen` ➔ ¡Sorpresa aleatoria! 🎲\n\n"
    msg += f"💡 **TIP:** Solo leo los últimos {MAX_MENSAJES} mensajes.\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "🎨 **Generado por @Beto7h**"
    return msg

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    saludo = random.choice(FRASES_ENTRADA)
    bot.reply_to(message, generar_mensaje_pro(saludo), parse_mode="Markdown")

@bot.message_handler(content_types=['new_chat_members'])
def auto_welcome(message):
    for user in message.new_chat_members:
        if user.id == bot.get_me().id:
            saludo = random.choice(FRASES_ENTRADA)
            bot.send_message(message.chat.id, generar_mensaje_pro(saludo), parse_mode="Markdown")

def generar_resumen_final(message, modo_elegido):
    cid = message.chat.id
    if cid not in chat_data or len(chat_data[cid]) < 5:
        bot.reply_to(message, "Hablen más, mi memoria de chismes está vacía. 🥱")
        return
    
    config = MODOS_CONFIG[modo_elegido]
    historial = "\n".join(chat_data[cid])
    
    bot.send_chat_action(cid, 'typing')
    
    try:
        # Llamada a Groq usando Llama 3
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": config['prompt']},
                {"role": "user", "content": f"Resume este chat de Telegram de forma entretenida:\n{historial}"}
            ],
        )
        respuesta_ia = completion.choices[0].message.content
        
        # Firma personalizada según tus instrucciones
        firma = f"\n\n— *Generado por @{bot.get_me().username}* | [Pack by @dmxsticker_bot]"
        bot.reply_to(message, f"{config['anuncio']}\n\n{respuesta_ia}{firma}", parse_mode="Markdown")
        
    except Exception as e:
        print(f"ERROR EN GROQ: {e}")
        bot.reply_to(message, "¡El chisme explotó! Groq está saturado, intenta en un momento. ⚠️")

@bot.message_handler(commands=['resumen'])
def cmd_aleatorio(message):
    modo = random.choice(list(MODOS_CONFIG.keys()))
    generar_resumen_final(message, modo)

@bot.message_handler(commands=['hater', 'picoso', 'chisme', 'noticiero', 'drama', 'zen', 'caos'])
def cmd_directos(message):
    modo = message.text.split()[0].replace('/', '').split('@')[0].lower()
    generar_resumen_final(message, modo)

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    if message.text and not message.text.startswith('/'):
        cid = message.chat.id
        if cid not in chat_data: chat_data[cid] = []
        
        user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        chat_data[cid].append(f"{user}: {message.text}")
        
        # Mantener solo los últimos 500 mensajes
        if len(chat_data[cid]) > MAX_MENSAJES: 
            chat_data[cid].pop(0)

# Limpiar webhooks y arrancar
bot.remove_webhook()
bot.polling(none_stop=True)
