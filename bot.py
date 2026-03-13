import os
import random
import telebot
import google.generativeai as genai
from collections import Counter

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

print("--- INICIANDO EL BOT DE @Beto7h ---")

# Configuración de Seguridad para que Gemini no bloquee el "salseo"
safety_settings = [
    {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
]

genai.configure(api_key=GEMINI_KEY)
# Usamos 'gemini-1.5-flash-latest' para máxima estabilidad
model = genai.GenerativeModel(
    model_name='gemini-1.5-flash-latest',
    safety_settings=safety_settings
)
bot = telebot.TeleBot(TOKEN)

chat_data = {}
MAX_MENSAJES = 500

MODOS_CONFIG = {
    "hater": {"prompt": "Eres un crítico sarcástico. Resume el chat burlándote de los temas y usuarios. Usa 🙄, 💅.", "anuncio": "✨ 𝕸𝖔𝖉𝖔 𝕳𝖆𝖙𝖊𝖗 ✨"},
    "caos": {"prompt": "Eres un agente del caos. Resume con letras raras y muchos emojis 🔥. ¡Sé ruidoso!", "anuncio": "🌀 𝑴𝑶𝑫𝑶 𝑪𝑨𝑶𝑺 🌀"},
    "chisme": {"prompt": "Eres la vecina chismosa. Cuéntame los escándalos y quiénes son los protagonistas. Emojis: ☕, 🤫.", "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍𝖎𝖘𝖒𝖊 🤫"},
    "noticiero": {"prompt": "Reporte de noticias de última hora con titulares dramáticos. Emojis: 🚨, 🎤.", "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"},
    "drama": {"prompt": "Eres un escritor de telenovelas. Resume como una tragedia romántica de traición. Emojis: 💔, 😭.", "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 🎭"},
    "zen": {"prompt": "Eres un maestro de meditación. Resume con mucha paz y armonía. Emojis: 🌿, 🪷.", "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"},
    "picoso": {"prompt": "Eres el rey del 'salseo'. Resume señalando momentos incómodos. Sé provocador. Emojis: 🌶️, 🔥,  popcorn.", "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️"}
}

FRASES_ENTRADA = [
    "He llegado para juzgar sus conversaciones. No esperen piedad. 💅",
    "¡Hola! Soy el que lee todo lo que escriben mientras ustedes no miran. 👁️",
    "¿Buscaban un resumen o una humillación pública? Yo hago ambas. 🤖",
    "Si el chisme fuera electricidad, este grupo sería una central nuclear. ⚡",
    "¡Llegó el jefe! Despejen el área y suelten el veneno. 🐍"
]

def generar_mensaje_pro(saludo):
    """Genera una bienvenida visualmente impactante."""
    msg = f"✨ *{saludo}* ✨\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "Soy *Don Chismoso*, la IA que pone orden (o más caos) a tus grupos. 🤖\n\n"
    msg += "📌 *MODOS DE ANÁLISIS:*\n"
    msg += "• `/hater` ➔ El resumen más amargado 💅\n"
    msg += "• `/picoso` ➔ Salseo y momentos incómodos 🌶️\n"
    msg += "• `/chisme` ➔ Reporte de vecina metiche ☕\n"
    msg += "• `/noticiero` ➔ Titulares de última hora 🚨\n"
    msg += "• `/drama` ➔ Tragedia de telenovela 🎭\n"
    msg += "• `/zen` ➔ Resumen en paz y armonía 🧘\n"
    msg += "• `/resumen` ➔ ¡Sorpresa aleatoria! 🎲\n\n"
    msg += f"💡 **TIP:** Solo leo los últimos {MAX_MENSAJES} mensajes.\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "🎨 *Bot credo por @Beto7h*"
    return msg

@bot.message_handler(content_types=['new_chat_members'])
def auto_welcome(message):
    for user in message.new_chat_members:
        if user.id == bot.get_me().id:
            saludo = random.choice(FRASES_ENTRADA)
            bot.send_message(message.chat.id, generar_mensaje_pro(saludo), parse_mode="Markdown")

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    saludo = random.choice(FRASES_ENTRADA)
    bot.reply_to(message, generar_mensaje_pro(saludo), parse_mode="Markdown")

def generar_resumen_final(message, modo_elegido):
    cid = message.chat.id
    if cid not in chat_data or len(chat_data[cid]) < 5:
        bot.reply_to(message, "Hablen más, mi memoria está vacía. 🥱")
        return
    
    config = MODOS_CONFIG[modo_elegido]
    nombres = [line.split(':')[0] for line in chat_data[cid]]
    conteo = Counter(nombres)
    top = ", ".join([f"{u} ({c})" for u, c in conteo.most_common(5)])
    lista = ", ".join(list(set(nombres)))
    
    bot.send_chat_action(cid, 'typing')
    historial = "\n".join(chat_data[cid])
    
    try:
        prompt = f"{config['prompt']}\n\nActivos: {top}.\nCitar: {lista}.\n\nCHAT:\n{historial}"
        response = model.generate_content(prompt)
        
        # Firma dinámica con el nombre del bot y el pack de stickers
        firma = f"\n\n— *Generado por @{bot.get_me().username}* | [Pack by @dmxsticker_bot]"
        bot.reply_to(message, f"{config['anuncio']}\n\n{response.text}{firma}", parse_mode="Markdown")
        
    except Exception as e:
        print(f"ERROR TÉCNICO GEMINI: {e}")
        bot.reply_to(message, "Hubo un error con Gemini (posible filtro de seguridad o cuota). Intenta de nuevo. ⚠️")

@bot.message_handler(commands=['resumen'])
def cmd_aleatorio(message):
    modo = random.choice(list(MODOS_CONFIG.keys()))
    generar_resumen_final(message, modo)

@bot.message_handler(commands=['hater', 'caos', 'chisme', 'noticiero', 'drama', 'zen', 'picoso'])
def cmd_directos(message):
    # Soporta comandos con @NombreDelBot
    modo = message.text.split()[0].replace('/', '').split('@')[0].lower()
    generar_resumen_final(message, modo)

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    if message.text and not message.text.startswith('/'):
        cid = message.chat.id
        if cid not in chat_data: chat_data[cid] = []
        user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        chat_data[cid].append(f"{user}: {message.text}")
        if len(chat_data[cid]) > MAX_MENSAJES: 
            chat_data[cid].pop(0)

# Eliminar cualquier conexión previa para evitar el Error 409
bot.remove_webhook()
print("Bot listo y escuchando...")
bot.polling(none_stop=True)
