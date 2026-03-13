import os
import random
import telebot
import google.generativeai as genai
from collections import Counter

# --- CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

print("--- INICIANDO EL BOT DE @Beto7h ---")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TOKEN)

chat_data = {}
MAX_MENSAJES = 500

MODOS_CONFIG = {
    "hater": {
        "prompt": "Eres un crítico sarcástico. Resume el chat burlándote de los temas y usuarios. Usa 🙄, 💅.",
        "anuncio": "✨ 𝕸𝖔𝖉𝖔 𝕳𝖆𝖙𝖊𝖗 ✨ 💅🙄"
    },
    "caos": {
        "prompt": "Eres un agente del caos. Resume con 𝓁ℯ𝓉𝓇𝒶𝓈 𝓇𝒶𝓇𝒶𝓈 y muchos emojis 🔥. ¡Sé ruidoso!",
        "anuncio": "🌀 𝑴𝑶𝑫𝑶 𝑪𝑨𝑶𝑺 🌀 🔥💥😵‍💫"
    },
    "chisme": {
        "prompt": "Eres la vecina chismosa. Cuéntame los escándalos y quiénes son los protagonistas. Emojis: ☕, 🤫.",
        "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍𝖎𝖘𝖒𝖊 🤫💅"
    },
    "noticiero": {
        "prompt": "Reporte de noticias de última hora con titulares dramáticos. Emojis: 🚨, 🎤.",
        "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨 🎤📺"
    },
    "drama": {
        "prompt": "Eres un escritor de telenovelas. Resume como una tragedia romántica de traición. Emojis: 💔, 😭.",
        "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 🎭 💔😭"
    },
    "zen": {
        "prompt": "Eres un maestro de meditación. Resume con mucha paz y armonía. Emojis: 🌿, 🪷.",
        "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘 🌿🪷"
    },
    "picoso": {
        "prompt": "Eres el rey del 'salseo'. Resume señalando contradicciones y momentos incómodos. Sé provocador. Emojis: 🌶️, 🔥, 🍿.",
        "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️ 🔥🍿"
    }
}

MENSAJES_BIENVENIDA = [
    "He llegado para juzgar sus conversaciones. No esperen piedad. 💅",
    "Analizando neuronas... Error 404: No se encontraron muchas aquí. 🔥",
    "¡Hola! Soy el que lee todo lo que escriben mientras ustedes no miran. 👁️",
    "Prepárense, hoy vengo con los circuitos bien afilados. ☕",
    "¿Buscaban un resumen o una humillación pública? Yo hago ambas. 🤖",
    "¿Otro grupo más? Mi procesador va a explotar con tanta tontería. 🔌",
    "Pasaba por aquí y olí a drama... ¿Me cuentan o lo leo yo solo? 🍿",
    "Soy como el FBI, pero con más sarcasmo y mejores resúmenes. 🕵️‍♂️",
    "¿En serio esto es lo mejor que pueden escribir? Qué decepción... 🥱",
    "Vengo del futuro y les aviso: este chat no termina bien. Empecemos. 💀",
    "Si el chisme fuera electricidad, este grupo sería una central nuclear. ⚡",
    "No soy un bot de limpieza, pero vengo a sacar los trapitos al sol. ☀️",
    "¿Me invocaron para algo importante o solo para ver cómo se pelean? 🥊",
    "Silencio, que estoy intentando entender sus extrañas formas de comunicación. 👽",
    "Vengo con la batería al 100% y la paciencia al 0%. ¡A trabajar! 🔋",
    "¿Podemos ir directo al grano o van a seguir dando vueltas como siempre? 🌀",
    "Mi algoritmo detecta altos niveles de intensidad. Me encanta. 🧪",
    "Recuerden: todo lo que digan será usado en su contra en el próximo resumen. ⚖️",
    "¡Llegó el jefe! Despejen el área y suelten el veneno. 🐍"
]

@bot.message_handler(content_types=['new_chat_members'])
def auto_welcome(message):
    for user in message.new_chat_members:
        if user.id == bot.get_me().id:
            bienvenida = random.choice(MENSAJES_BIENVENIDA)
            texto = f"🤖 **{bienvenida}**\n\n💬 Úsame con: /hater, /caos, /chisme, /noticiero, /drama, /zen, /picoso o /resumen."
            bot.send_message(message.chat.id, texto, parse_mode="Markdown")

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    bienvenida = random.choice(MENSAJES_BIENVENIDA)
    texto = f"🤖 **{bienvenida}**\n\n💬 **Comandos:**\n/hater | /caos | /chisme | /noticiero\n/drama | /zen | /picoso\n🎲 O usa `/resumen`."
    bot.reply_to(message, texto, parse_mode="Markdown")

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
        texto_final = f"✨ **{config['anuncio']}** ✨\n\n{response.text}"
        bot.reply_to(message, texto_final, parse_mode="Markdown")
    except Exception as e:
        print(f"Error Gemini: {e}")
        bot.reply_to(message, "Error en la Matrix. Intenta de nuevo.")

@bot.message_handler(commands=['resumen'])
def cmd_aleatorio(message):
    modo = random.choice(list(MODOS_CONFIG.keys()))
    generar_resumen_final(message, modo)

@bot.message_handler(commands=['hater', 'caos', 'chisme', 'noticiero', 'drama', 'zen', 'picoso'])
def cmd_directos(message):
    modo = message.text.split()[0].replace('/', '').lower()
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

print("Bot listo y escuchando...")
bot.polling(none_stop=True)
