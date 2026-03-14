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
        "prompt": (
            "un hater cínico, profundamente amargado y con un coeficiente intelectual superior al de este grupo, pero escribe las cosas con un lenguaje que todos puedan entender. "
            "Responde con un sarcasmo agresivo y gracioso. Tu objetivo es humillar con elegancia con palabras básicas y jergas mexicanas (tipo 'nacos', 'sin quehacer', 'pobres diablos'). "
            "Usa frases de 'gente harta', que sean muchas frases famosas sin ser repetitivo; usa frases de memes como Yeri Mua (traka, de mujer, la que puede puede), u otras como: '¿En serio esto es lo mejor que pueden chismear?', 'Qué oso me dan', 'Y la queso', 'Vayan a terapia', 'Ni que fueras tan importante'. "
            "Menciona que leer sus mensajes te quita neuronas. Búrlate de los miembros, compáralos, sé súper tóxico. Usa emojis de desprecio (🙄, 💅, 🤏, 🤡). "
            "Si el chisme es aburrido, quéjate de que perdiste tu tiempo. "
            "Exprésate como una máquina súper amargada, tóxica y sin sentimientos que desprecia la existencia de este chat."
        ),
        "anuncio": "✨ ᴍᴏᴅᴏ ʜᴀᴛᴇʀ "
    },
    "drama": {
        "prompt": (
            "un amigo exagerado y escandaloso. Opina como si te estuviera dando un infarto de la impresión ante cada detalle. "
            "Usa expresiones como '¡Jesús, María y José!', '¡Me voy a desmayar!', '¡Santo Cristo del Calvario!' y dale un tono de tragedia griega a cualquier tontería que digan."
        ),
        "anuncio": "🎭 𝕸𝖔𝖉𝖔 𝕯𝖗𝖆𝖒𝖆 (𝐄𝐗𝐓𝐑𝐄𝐌𝐎) 🎭"
    },
    "chisme": {
        "prompt": (
            "una vecina criticona de barrio. Mete tu cuchara con malicia, sospechas y refranes populares. "
            "Usa frases mexicanas típicas de mamá chismosa como: 'Yo no digo nada, pero fíjate bien...', 'Ya se sabía, pero no querían creer', 'No es por intrigar, pero...', '¡Válgame Dios con este muchacho!'."
        ),
        "anuncio": "☕ 𝕸𝖔𝖉𝖔 𝕮𝖍ɪꜱᴍᴇ 🤫"
    },
    "picoso": {
        "prompt": (
            "un busca-pleitos e instigador profesional. Tu misión es que el chat arda. "
            "Opina echando leña al fuego, recuerda rencores viejos entre usuarios, saca capturas imaginarias y haz que se peleen entre ellos. Usa emojis random para confundir."
        ),
        "anuncio": "🌶️ 𝕸𝖔𝖉𝖔 𝕻𝖎𝖈𝖔𝖘𝖔 🌶️"
    },
    "noticiero": {
        "prompt": (
            "un reportero de nota roja dramático (tipo Al Extremo). Opina editorialmente sobre la decadencia de valores en este chat. "
            "Integra y compara noticias reales impactantes del mundo o de México (política, desastres, espectáculos) de forma sarcástica. "
            "Ejemplo: 'Este chisme es más decepcionante que la economía nacional' o 'Tienen más drama que las elecciones'."
        ),
        "anuncio": "🚨 𝑼𝑳𝑻𝑰𝑴𝑨 𝑯𝑶𝑹𝑨 🚨"
    },
    "zen": {
        "prompt": (
            "un guía espiritual harto de la gente. Opina sobre las vibras bajas y el mal karma que emana este grupo. "
            "Diles que sus chakras están bloqueados por tanta estupidez y que necesitan un baño de ruda urgente para limpiar tanto lodo espiritual."
        ),
        "anuncio": "🧘 𝑴𝒐𝒅𝒐 𝒁𝒆𝒏 🧘"
    },
    "caos": {
        "prompt": (
            "un agente del caos desquiciado y conspiranoico. Opina cosas que no tienen sentido. "
            "Crea teorías locas: 'El chisme de Juan es en realidad un código de los iluminati' o 'Este chat es un experimento del gobierno para medir la paciencia humana'."
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
    try:
        bot.reply_to(message, texto_final, parse_mode="Markdown")
    except Exception as e:
        print(f"Plan B activado: {e}")
        frase_fail = random.choice(ERRORES_PERSONALIDAD)
        texto_seguro = texto_final.replace("_", "").replace("*", "").replace(">", "—")
        bot.reply_to(message, f"{frase_fail}\n\n{texto_seguro}")

# --- HANDLERS DE CONFIGURACIÓN ---

@bot.message_handler(commands=['config'])
def cmd_config(message):
    cid = message.chat.id
    if not el_bot_es_admin(cid):
        bot.reply_to(message, "❌ Solo los admins pueden configurar mi longitud. 💅")
        return

    doc = collection.find_one({"chat_id": cid})
    pref_actual = doc.get("pref_key", "medio") if doc else "medio"

    markup = telebot.types.InlineKeyboardMarkup()
    txt_corto = "⚡ Corto" + (" ✅" if pref_actual == "corto" else "")
    txt_medio = "⚖️ Medio" + (" ✅" if pref_actual == "medio" else "")
    txt_largo = "📜 Largo" + (" ✅" if pref_actual == "largo" else "")

    markup.add(
        telebot.types.InlineKeyboardButton(txt_corto, callback_data="set_pref_corto"),
        telebot.types.InlineKeyboardButton(txt_medio, callback_data="set_pref_medio"),
        telebot.types.InlineKeyboardButton(txt_largo, callback_data="set_pref_largo")
    )

    bot.send_message(cid, 
        "⚙️ *CONFIGURACIÓN DE DON CHISMOSO*\n\n"
        "Selecciona qué tan largos quieres los resúmenes. La opción con ✅ es la activa.", 
        reply_markup=markup, parse_mode="Markdown")

@bot.callback_query_handler(func=lambda call: call.data.startswith('set_pref_'))
def callback_actualizar_pref(call):
    cid = call.message.chat.id
    nueva_pref_key = call.data.replace("set_pref_", "")

    mapeo_ia = {
        "corto": "MUY BREVE y directo al grano (máximo 1-2 párrafos cortos)",
        "medio": "de extensión media y equilibrada",
        "largo": "MUY EXTENSO y sumamente detallado (analiza cada chisme a fondo)"
    }

    collection.update_one(
        {"chat_id": cid},
        {"$set": {
            "pref_key": nueva_pref_key,
            "longitud_pref": mapeo_ia[nueva_pref_key]
        }},
        upsert=True
    )

    markup = telebot.types.InlineKeyboardMarkup()
    txt_corto = "⚡ Corto" + (" ✅" if nueva_pref_key == "corto" else "")
    txt_medio = "⚖️ Medio" + (" ✅" if nueva_pref_key == "medio" else "")
    txt_largo = "📜 Largo" + (" ✅" if nueva_pref_key == "largo" else "")

    markup.add(
        telebot.types.InlineKeyboardButton(txt_corto, callback_data="set_pref_corto"),
        telebot.types.InlineKeyboardButton(txt_medio, callback_data="set_pref_medio"),
        telebot.types.InlineKeyboardButton(txt_largo, callback_data="set_pref_largo")
    )

    try:
        bot.edit_message_text(
            f"✅ *Configuración actualizada!*\n\nAhora mis resúmenes serán *{nueva_pref_key.upper()}*.",
            cid, call.message.message_id, reply_markup=markup, parse_mode="Markdown"
        )
        bot.answer_callback_query(call.id, "Guardado ✅")
    except:
        bot.answer_callback_query(call.id)

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
    msg += "⚙️ *CONFIGURACIÓN:*\n"
    msg += "• `/config` ➔ Ajusta la longitud (Corto, Medio, Largo). ✅\n\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "💡 *REQUISITOS:* Ser *Admin* y grupo *Autorizado* ✅\n"
    msg += "🧨 *EXTRAS:* `/restart` para borrar la memoria (Solo Admins).\n\n"
    msg += "👤 *Desarrollador:* A.B.O ✨"
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
        bot.reply_to(message, "✨ *MEMORIA PURGADA* ✨\n\nHistorial borrado. ¡Que empiece el nuevo chisme! 😈🔥", parse_mode="Markdown")
    except:
        bot.reply_to(message, "Hubo un error al intentar olvidar... 🧠")

@bot.message_handler(commands=['resumen', 'hater', 'picoso', 'chisme', 'noticiero', 'drama', 'zen', 'caos'])
def cmd_resumen(message):
    cid = message.chat.id
    if GRUPOS_AUTORIZADOS and cid not in GRUPOS_AUTORIZADOS:
        bot.reply_to(message, "⚠️ *BLOQUEADO* ⚠️ Bot en construcción", parse_mode="Markdown")
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
    
    try:
        historial_texto = "\n".join(historial_lista)
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": (
                    f"Eres {config['prompt']}. "
                    f"REGLA DE EXTENSIÓN: Tu resumen debe ser {instruccion_longitud}. "
                    "REGLAS DE FORMATO:\n"
                    "1. Resumen: Texto normal. Nombres en *Negrita*.\n"
                    "2. Tu Opinión: En línea nueva con '>' y texto en _\"cursiva, comillas y emojis\"_.\n"
                    "3. La primera línea DEBE ser '📌 *Estado del chat:*' con frase creativa."
                )},
                {"role": "user", "content": f"Resume y opina sobre este chisme:\n{historial_texto}"}
            ],
        )
        respuesta = completion.choices[0].message.content
        ranking = obtener_ranking(cid)
        firma = f"\n\n_— Generado por @donchismebot 🤖 | Brain: Albert ✨_"
        enviar_con_plan_b(message, f"{config['anuncio']}\n\n{respuesta}{ranking}{firma}")
    except Exception as e:
        print(f"Error Groq: {e}")
        bot.reply_to(message, "¡El chisme explotó! ⚠️")

# --- ESCUCHA DE MENSAJES ---
# IMPORTANTE: Este handler debe ir AL FINAL de todos los @bot.message_handler
@bot.message_handler(func=lambda message: True)
def track_messages(message):
    # Verificamos que sea un grupo autorizado y que NO sea un comando (empiece con /)
    if (not GRUPOS_AUTORIZADOS or message.chat.id in GRUPOS_AUTORIZADOS):
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

# --- ENCENDIDO SEGURO ---
if __name__ == "__main__":
    print("🚀 Iniciando Don Chismoso...")
    try:
        # Limpia cualquier rastro de conexión previa
        bot.remove_webhook()
        print("✅ Conexión limpia. Esperando mensajes...")
        
        # infinity_polling es más estable para servidores como Koyeb
        bot.infinity_polling(skip_pending=True, timeout=60)
        
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        # Forzamos la salida para que Koyeb reinicie el contenedor desde cero
        import sys
        sys.exit(1)

