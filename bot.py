import os
import random
import telebot
import google.generativeai as genai
from collections import Counter

# --- INICIO DE CONFIGURACIÓN ---
TOKEN = os.getenv('TELEGRAM_TOKEN')
GEMINI_KEY = os.getenv('GEMINI_API_KEY')

# Confirmación en Logs
print("--- INICIANDO EL BOT DE @Beto7h ---")

if not TOKEN or not GEMINI_KEY:
    print("❌ ERROR: Faltan las variables de entorno TELEGRAM_TOKEN o GEMINI_API_KEY")

genai.configure(api_key=GEMINI_KEY)
model = genai.GenerativeModel('gemini-1.5-flash')
bot = telebot.TeleBot(TOKEN)

chat_data = {}
MAX_MENSAJES = 500

MODOS = {
    "hater": "Eres un crítico sarcástico. Resume el chat burlándote de los temas y usuarios. Usa 🙄, 💅.",
    "caos": "Eres un agente del caos. Resume con 𝓁ℯ𝓉𝓇𝒶𝓈 𝓇𝒶𝓇𝒶𝓈 y muchos emojis 🔥. ¡Sé ruidoso!",
    "chisme": "Eres la vecina chismosa. Cuéntame los escándalos y quiénes son los protagonistas. Emojis: ☕, 🤫.",
    "noticiero": "Reporte de noticias de última hora con titulares dramáticos. Emojis: 🚨, 🎤.",
    "drama": "Eres un escritor de telenovelas. Resume como una tragedia romántica de traición. Emojis: 💔, 😭.",
    "zen": "Eres un maestro de meditación. Resume con mucha paz y armonía. Emojis: 🌿, 🪷.",
    "picoso": "Eres el rey del 'salseo'. Tu objetivo es echarle leña al fuego. Resume señalando contradicciones y momentos incómodos. Sé provocador y divertido. Emojis: 🌶️, 🔥, 🍿."
}

MENSAJES_BIENVENIDA = [
    "¿Quién me despertó? Más les vale que el chisme esté bueno... 🙄",
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

@bot.message_handler(commands=['start', 'ayuda'])
def send_help(message):
    print(f"Comando recibido: {message.text} de {message.from_user.first_name}")
    bienvenida = random.choice(MENSAJES_BIENVENIDA)
    texto = f"🤖 **{bienvenida}**\n\nUsa `/resumen [modo]` para analizar el grupo.\n\nModos: `hater`, `caos`, `chisme`, `noticiero`, `drama`, `zen`, `picoso`."
    bot.reply_to(message, texto, parse_mode="Markdown")

@bot.message_handler(func=lambda message: True)
def track_messages(message):
    if message.text and not message.text.startswith('/'):
        cid = message.chat.id
        if cid not in chat_data: chat_data[cid] = []
        user = f"@{message.from_user.username}" if message.from_user.username else message.from_user.first_name
        chat_data[cid].append(f"{user}: {message.text}")
        if len(chat_data[cid]) > MAX_MENSAJES: chat_data[cid].pop(0)

@bot.message_handler(commands=['resumen'])
def make_summary(message):
    print(f"Comando resumen recibido en chat: {message.chat.id}")
    cid = message.chat.id
    if cid not in chat_data or len(chat_data[cid]) < 3:
        bot.reply_to(message, "Hablen un poco más para que tenga material. 🥱")
        return

    nombres_en_chat = [line.split(':')[0] for line in chat_data[cid]]
    conteo = Counter(nombres_en_chat)
    top_usuarios = ", ".join([f"{u} ({c})" for u, c in conteo.most_common(5)])
    lista_para_citar = ", ".join(list(set(nombres_en_chat)))

    args = message.text.split()
    modo_key = args[1].lower() if len(args) > 1 else "hater"
    prompt_personalidad = MODOS.get(modo_key, MODOS["hater"])

    bot.send_chat_action(cid, 'typing')
    historial_completo = "\n".join(chat_data[cid])

    try:
        full_prompt = f"{prompt_personalidad}\n\nActivos: {top_usuarios}.\nCitar: {lista_para_citar}.\n\nCHAT:\n{historial_completo}"
        response = model.generate_content(full_prompt)
        bot.reply_to(message, response.text, parse_mode="Markdown")
    except Exception as e:
        print(f"Error en Gemini: {e}")
        bot.reply_to(message, "Error al generar resumen.")

# Cambio importante aquí para Koyeb
print("Bot listo y escuchando...")
bot.polling(none_stop=True, interval=0, timeout=20)
