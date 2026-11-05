import time
import threading
import random
import unicodedata
import re
import os
import json
import difflib
from datetime import datetime, date, timedelta
from collections import deque, Counter
from banco_palabras import CONOCIMIENTOS_IA
# CONFIGURACIÓN
# Para pruebas:
# 60 segundos reales = 1 hora para Michi
SEGUNDOS_POR_HORA = 10
# ESTADO DE MICHI
mascota = {
    "nombre": "Michi",
    "salud": 100,
    "felicidad": 80,
    "comida": 100,  # 100 = lleno, 0 = vacío
    "energia": 80,
    "horas_sin_cuidado": 0,
    "horas_sin_carino": 0,
    "viva": True
}
# PERCEPCIÓN
def percibir():
    """
    Michi observa únicamente su estado ACTUAL.
    No recuerda conversaciones anteriores sobre su cuidado
    (aunque sí recuerda, por separado, los últimos temas de
    conversación sobre IA; ver memoria_conversacion más abajo).
    """
    return {
        "salud": mascota["salud"],
        "felicidad": mascota["felicidad"],
        "comida": mascota["comida"],
        "energia": mascota["energia"],
        "horas_sin_cuidado": mascota["horas_sin_cuidado"],
        "horas_sin_carino": mascota["horas_sin_carino"]
    }
# NORMALIZAR TEXTO
def normalizar_texto(texto):
    """
    Convierte el texto a minúsculas y elimina acentos.
    Esto NO hace inteligente a Michi:
    solamente facilita comparar palabras.
    """
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(
        caracter for caracter in texto
        if unicodedata.category(caracter) != "Mn"
    )
    return texto
# ===================================================================
# CONVERSACIÓN MÁS NATURAL: TOLERANCIA A ERRORES DE ESCRITURA
# ===================================================================
# Michi sigue siendo un sistema de reglas, pero ahora entiende mejor
# cómo escribe la gente de verdad: letras alargadas ("holaaaa",
# "cariñooo") y pequeños errores de tipeo ("juguemoss", "carinoo").
def suavizar_texto(texto):
    """Reduce letras repetidas: 'holaaaa' -> 'hola', 'juguemooos' -> 'juguemos'."""
    texto = re.sub(r"([aeiou])\1+", r"\1", texto)       # vocales repetidas
    texto = re.sub(r"([a-z])\1{2,}", r"\1", texto)       # consonantes 3+ veces
    return texto


def palabra_parecida(palabra, mensaje, umbral=0.85):
    """
    True si alguna palabra del mensaje se parece mucho a 'palabra'
    (misma letra inicial y similitud >= umbral). Solo para palabras
    sueltas de 5+ letras, para evitar falsos positivos.
    """
    if " " in palabra or len(palabra) < 5:
        return False
    for w in re.findall(r"[a-z0-9]+", mensaje):
        if (len(w) >= 5 and w[0] == palabra[0] and abs(len(w) - len(palabra)) <= 2
                and difflib.SequenceMatcher(None, w, palabra).ratio() >= umbral):
            return True
    return False


# EXPRESIÓN DE MICHI
def obtener_expresion():
    if mascota["salud"] <= 20:
        return "🤒😿💔 Me siento muuuy mal... necesito que me cuides :((("
    elif mascota["comida"] <= 10:
        return "🥺🍗😿 Tengo muchísima hambre... mi pancita hace miauuuu :((("
    elif mascota["energia"] <= 20:
        return "😴💤🥱 Estoy agotado... apenas puedo mantener los ojitos abiertos"
    elif mascota["felicidad"] <= 20:
        return "😭😿💔 Estoy muuuy triste... te extrañoooo :((((("
    elif mascota["felicidad"] <= 40:
        return "😿🥺 Estoy triste... ¿me das un poquito de cariño?"
    elif mascota["felicidad"] >= 90:
        return "😻🥰✨ ¡Estoy suuuper feliz! ¡Miauuuu!"
    elif mascota["felicidad"] >= 75:
        return "😸❤️🐾 Estoy feliz de estar contigo"
    else:
        return "🐱✨ Estoy tranquilito... miau"

# ===================================================================
# AGENTE BASADO EN METAS
# ===================================================================
# Michi dejó de ser un agente de reflejo simple. Ahora mantiene una
# lista EXPLÍCITA de metas (necesidades que quiere satisfacer), cada
# una con una prioridad. En cada momento, revisa cuáles metas siguen
# sin cumplirse y elige comunicar/perseguir SIEMPRE la de mayor
# urgencia, en vez de reaccionar ciegamente a la última percepción.
#
# Cada tupla es: (nombre_meta, prueba_de_meta_no_cumplida, prioridad, etiqueta_accion)
# A mayor número de prioridad, más urgente es esa meta.
DEFINICION_METAS = [
    ("salud_critica",      lambda p: p["salud"] <= 20,                              10, "PEDIR_CUIDADO"),
    ("comida_urgente",     lambda p: p["comida"] <= 10,                              9, "COMIDA_URGENTE"),
    ("comida_baja",        lambda p: p["comida"] <= 30,                              7, "PEDIR_COMIDA"),
    ("energia_baja",       lambda p: p["energia"] <= 20,                             6, "PEDIR_DESCANSO"),
    ("carino_pendiente",   lambda p: p["horas_sin_carino"] >= 4,                      5, "PEDIR_CARINO"),
    ("atencion_pendiente", lambda p: p["horas_sin_cuidado"] >= 6,                     4, "PEDIR_ATENCION"),
    ("felicidad_baja",     lambda p: p["felicidad"] <= 30,                            3, "ESTAR_TRISTE"),
    ("quiere_jugar",       lambda p: p["energia"] >= 80 and p["felicidad"] >= 70,     1, "QUERER_JUGAR"),
]


def definir_metas(percepcion):
    """
    Devuelve la lista de metas actualmente NO satisfechas, ordenadas
    de mayor a menor prioridad. Esto reemplaza la cadena de if/elif
    de un reflejo simple: en vez de reglas aisladas, ahora hay una
    lista de objetivos explícitos que compiten entre sí.
    """
    metas_pendientes = [
        (nombre, prioridad, etiqueta)
        for nombre, prueba, prioridad, etiqueta in DEFINICION_METAS
        if prueba(percepcion)
    ]
    metas_pendientes.sort(key=lambda meta: -meta[1])
    return metas_pendientes


def seleccionar_accion_por_metas(percepcion):
    """
    El 'cerebro' del agente basado en metas: revisa todas las metas
    no satisfechas y elige la acción asociada a la de MAYOR prioridad.
    Si no hay ninguna meta pendiente, Michi está conforme (TRANQUILO).
    """
    metas = definir_metas(percepcion)
    if not metas:
        return "TRANQUILO"
    _, _, etiqueta_mas_urgente = metas[0]
    return etiqueta_mas_urgente


# ACCIONES DEL AGENTE
# NOTA: las claves de este diccionario ahora coinciden EXACTAMENTE con
# las etiquetas de DEFINICION_METAS (todas con guión bajo). Antes había
# un desajuste entre "PEDIR_CUIDADO" (que devolvía la decisión) y
# "PEDIR CUIDADO" (la clave del diccionario, con espacio), por lo que
# la mayoría de estos mensajes nunca llegaban a imprimirse.
def actuar(accion):
    mensajes = {
        "PEDIR_CUIDADO": [
            "🤒😿 Michi: Dueño-amo... no me siento muy bien :(( ¿me cuidas?",
            "🥺💔 Michi: Necesito un poquito de atención... por favooor.",
            "🐱🤒 Michi: Creo que necesito que me cuides... miauuu :("
        ],
        "COMIDA_URGENTE": [
            "😿🍗 Michi: ¡Dueño-amooo! ¡Tengo muchísima hambre! :(((",
            "🥺🍖 Michi: ¡Miauuuu! Mi pancita está vacía...",
            "😭🍗 Michi: ¡Comida, comida, comida! ¡Por favooor!"
        ],
        "PEDIR_COMIDA": [
            "😋🍗 Michi: Dueño-amo... creo que ya tengo un poquito de hambre.",
            "🐱🍖 Michi: ¿Habrá algo rico para este michito?",
            "🥺🍗 Michi: ¿Me das un poquito de comidita?"
        ],
        "PEDIR_DESCANSO": [
            "😴💤 Michi: Tengo muchísimo sueñito...",
            "🥱🐱 Michi: Dueño-amo... creo que necesito descansar.",
            "😴🛏️ Michi: Mis ojitos ya se están cerrando... zzz..."
        ],
        "PEDIR_CARINO": [
            "🥺❤️ Michi: Dueño-amo... ¿me das un poquito de cariño?",
            "😻💕 Michi: Quierooo mimosssss.",
            "😿🐾 Michi: Hace mucho que no recibo cariño... te extrañoooo :((("
        ],
        "PEDIR_ATENCION": [
            "😾💢 Michi: ¡Oyeee! ¿Ya te olvidaste de mí?",
            "🥺😿 Michi: Hace mucho que no me haces caso...",
            "🐱💔 Michi: Dueño-amo... ¿todavía estás ahí? :("
        ],
        "ESTAR_TRISTE": [
            "😭😿 Michi: Estoy muuuy triste... te extrañoooo :(((((",
            "🥺💔 Michi: Quiero pasar tiempo contigo...",
            "😿🐾 Michi: Hoy mi corazoncito gatuno está triste :((("
        ],
        "QUERER_JUGAR": [
            "🤩🎾 Michi: ¡Dueño-amooo! ¡Quiero jugar!",
            "😸🐾 Michi: ¡Vamos a jugar, vamos, vamos!",
            "😻⚡ Michi: ¡Tengo muchísima energía! ¡Juguemos!"
        ],
        "TRANQUILO": [
            "😸✨ Michi: Todo está bien, dueño-amo.",
            "🐱🐾 Michi: Estoy tranquilito... miau.",
            "😺☀️ Michi: Qué bonito es estar aquí contigo.",
            "🐾😸 Michi: Estoy disfrutando el momento."
        ]
    }
    if accion in mensajes:
        print(random.choice(mensajes[accion]))
        # Si lo que dijo es una petición, recuerda de qué trataba para
        # poder interpretar un "sí" o un "no" como respuesta a ella.
        if accion in TEMA_DE_PREGUNTA:
            recordar_pregunta(TEMA_DE_PREGUNTA[accion])
# PASO DEL TIEMPO
def pasar_una_hora():
    mascota["horas_sin_cuidado"] += 1
    mascota["horas_sin_carino"] += 1
    # Disminuye la comida
    mascota["comida"] -= 10
    # Disminuye la energía
    mascota["energia"] -= 5
    # Si pasa mucho tiempo sin atención, baja la felicidad
    if mascota["horas_sin_cuidado"] >= 4:
        mascota["felicidad"] -= 5
    # Si se queda casi sin comida, afecta la salud
    if mascota["comida"] <= 10:
        mascota["salud"] -= 5
    # Mantener valores entre 0 y 100
    mascota["comida"] = max(0, min(100, mascota["comida"]))
    mascota["felicidad"] = max(0, min(100, mascota["felicidad"]))
    mascota["salud"] = max(0, min(100, mascota["salud"]))
    mascota["energia"] = max(0, min(100, mascota["energia"]))
    mostrar_estadisticas_de_michi()
    revisar_derrota()
def revisar_derrota():
    if mascota["salud"] <= 0:
        mascota["viva"] = False
        print("\n💔😿 Has sido un amo irresponsable, tu Michi ha perdido la vida... Fin del juego.")
    elif mascota["comida"] <= 0:
        mascota["viva"] = False
        print("\n🚨🐾 Tu irresponsabilidad ha provocado que Michi fuera capturado por la perrera y te ha sido confiscado. Si deseas recuperarlo, deberás pagar la multa... Fin del juego.")
    elif mascota["horas_sin_cuidado"] >= 24:
        mascota["viva"] = False
        print("\n😭💔 Tu irresponsabilidad ha obligado a Michi a abandonar el hogar... Fin del juego.")
# ===================================================================
# RECONOCIMIENTO DE PATRONES: HÁBITOS DEL DUEÑO
# ===================================================================
# Cada vez que el dueño cuida a Michi (alimentar, dar cariño, jugar o
# hacer dormir), se guarda un registro con:
#   - la hora del reloj real (para saber CUÁNDO suele venir),
#   - la acción realizada (para saber QUÉ hace más),
#   - cuántas horas de Michi habían pasado sin cuidado (para saber
#     CUÁNTO lo deja esperando).
# Con ese historial, Michi busca regularidades usando reglas y umbrales
# simples (por ejemplo: "más de la mitad de las visitas son de noche").
# No predice ni "entiende": solo cuenta y compara. El historial se
# guarda en habitos_michi.json, así que los patrones sobreviven entre
# sesiones y aunque Michi muera.
ARCHIVO_HABITOS = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "habitos_michi.json"
)
MAX_EVENTOS = 500      # solo se conservan los últimos registros
MIN_EVENTOS = 6        # mínimo de cuidados antes de hablar de patrones
UMBRAL_PATRON = 0.5    # un comportamiento es "patrón" si es >= 50% de los casos

historial_cuidados = []
ultimo_aviso = {"clave": None}   # evita repetir el aviso de "es tu hora"

VERBOS_ACCION = {
    "alimentar": "me das de comer",
    "dar_carino": "me das cariño",
    "jugar": "juegas conmigo",
    "descansar": "me mandas a dormir",
}
NUNCA_ACCION = {
    "alimentar": "dado de comer",
    "dar_carino": "dado cariño",
    "jugar": "jugado conmigo",
    "descansar": "mandado a dormir",
}
FRASE_FRANJA = {
    "madrugada": "de madrugada",
    "mañana": "por la mañana",
    "tarde": "por la tarde",
    "noche": "por la noche",
}


def franja_del_dia(hora):
    """Convierte una hora (0-23) en madrugada, mañana, tarde o noche."""
    if hora < 6:
        return "madrugada"
    if hora < 12:
        return "mañana"
    if hora < 19:
        return "tarde"
    return "noche"


def guardar_habitos():
    try:
        with open(ARCHIVO_HABITOS, "w", encoding="utf-8") as archivo:
            json.dump({"eventos": historial_cuidados}, archivo,
                      ensure_ascii=False, indent=1)
    except OSError:
        pass  # si no se puede guardar, Michi sigue funcionando en memoria


def cargar_habitos():
    if not os.path.exists(ARCHIVO_HABITOS):
        return
    try:
        with open(ARCHIVO_HABITOS, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        for e in datos.get("eventos", []):
            if e["accion"] in VERBOS_ACCION:
                date.fromisoformat(e["fecha"])   # valida el formato
                historial_cuidados.append({
                    "accion": e["accion"],
                    "hora": int(e["hora"]),
                    "fecha": e["fecha"],
                    "espera": int(e.get("espera", 0)),
                })
        del historial_cuidados[:-MAX_EVENTOS]
    except (OSError, ValueError, KeyError, TypeError, AttributeError):
        historial_cuidados.clear()   # archivo dañado: empieza sin historial


def registrar_cuidado(accion, momento=None):
    """
    Anota un cuidado del dueño. Se llama al INICIO de alimentar(),
    dar_carino(), jugar() y descansar(), antes de que se reinicie
    horas_sin_cuidado (por eso ese valor es la espera real).
    'momento' solo sirve para hacer pruebas con fechas simuladas.
    """
    momento = momento or datetime.now()
    historial_cuidados.append({
        "accion": accion,
        "hora": momento.hour,
        "fecha": momento.date().isoformat(),
        "espera": mascota["horas_sin_cuidado"],
    })
    del historial_cuidados[:-MAX_EVENTOS]
    guardar_habitos()


def franja_habitual():
    """Franja del día en la que el dueño suele venir, o None si no hay patrón."""
    if len(historial_cuidados) < MIN_EVENTOS:
        return None
    conteo = Counter(franja_del_dia(e["hora"]) for e in historial_cuidados)
    franja, veces = conteo.most_common(1)[0]
    if veces / len(historial_cuidados) >= UMBRAL_PATRON:
        return franja
    return None


def racha_de_dias(hoy):
    """Días consecutivos (hasta hoy o ayer) en los que hubo al menos un cuidado."""
    dias = {date.fromisoformat(e["fecha"]) for e in historial_cuidados}
    dia = hoy if hoy in dias else hoy - timedelta(days=1)
    racha = 0
    while dia in dias:
        racha += 1
        dia -= timedelta(days=1)
    return racha


def analizar_habitos(hoy=None):
    """Devuelve una lista de observaciones (texto). Requiere MIN_EVENTOS registros."""
    hoy = hoy or date.today()
    eventos = historial_cuidados
    n = len(eventos)
    obs = []

    # 1. CUÁNDO: ¿hay una franja horaria dominante?
    franja, veces = Counter(
        franja_del_dia(e["hora"]) for e in eventos).most_common(1)[0]
    if veces / n >= UMBRAL_PATRON:
        obs.append(f"🕐 Sueles venir {FRASE_FRANJA[franja]} "
                   f"({round(100 * veces / n)}% de tus cuidados).")
    else:
        obs.append("🕐 No tienes un horario fijo: me cuidas a distintas horas del día.")

    # 2. QUÉ: ¿hay una acción dominante? ¿alguna que nunca haces?
    acciones = Counter(e["accion"] for e in eventos)
    top, veces = acciones.most_common(1)[0]
    if veces / n >= UMBRAL_PATRON:
        obs.append(f"🎯 Casi siempre {VERBOS_ACCION[top]} "
                   f"({round(100 * veces / n)}% de las veces).")
    else:
        obs.append("🎯 Repartes tus cuidados de forma bastante pareja.")
    if n >= 8:
        nunca = [NUNCA_ACCION[a] for a in VERBOS_ACCION if acciones.get(a, 0) == 0]
        if nunca:
            obs.append("🙀 Nunca me has " + " ni ".join(nunca) + ".")

    # 3. CUÁNTO: ¿qué tanto me dejas esperando?
    espera_media = sum(e["espera"] for e in eventos) / n
    peor = max(e["espera"] for e in eventos)
    if espera_media <= 3:
        obs.append(f"💚 Eres muy atento: me atiendes tras {espera_media:.1f} horas "
                   f"de espera en promedio (la peor fue de {peor}).")
    elif espera_media <= 7:
        obs.append(f"💛 Me atiendes con regularidad: {espera_media:.1f} horas de espera "
                   f"en promedio (la peor fue de {peor}).")
    else:
        obs.append(f"💔 Sueles dejarme esperando mucho: {espera_media:.1f} horas en "
                   f"promedio (la peor fue de {peor}).")

    # 4. CONSTANCIA: días distintos y rachas
    dias = {e["fecha"] for e in eventos}
    obs.append(f"📅 Me has cuidado en {len(dias)} día(s) distinto(s), "
               f"unas {n / len(dias):.1f} veces por día.")
    racha = racha_de_dias(hoy)
    if racha >= 2:
        obs.append(f"🔥 Llevas {racha} días seguidos cuidándome. ¡Gracias!")
    elif hoy.isoformat() not in dias:
        dias_sin_venir = (hoy - max(date.fromisoformat(d) for d in dias)).days
        if dias_sin_venir >= 2:
            obs.append(f"😿 Antes de esta visita pasaron {dias_sin_venir} días "
                       f"sin que me cuidaras.")
    return obs


def mostrar_habitos():
    n = len(historial_cuidados)
    if n < MIN_EVENTOS:
        print(f"🐱🔍 Michi: Todavía te estoy conociendo, amo... llevo {n} "
              f"cuidado(s) anotado(s) y necesito al menos {MIN_EVENTOS} "
              f"para notar patrones.")
        return
    print("\n📈🐱 LO QUE HE NOTADO DE TI, DUEÑO-AMO")
    print(f"   (según tus últimos {n} cuidados)")
    for linea in analizar_habitos():
        print("   • " + linea)


def anticipar_visita():
    """
    Si ya se conoce la franja habitual del dueño y estamos en ella,
    Michi lo espera y lo dice (una vez por franja y por día).
    """
    if not mascota["viva"] or mascota["horas_sin_cuidado"] < 2:
        return
    franja = franja_habitual()
    ahora = datetime.now()
    if franja is None or franja_del_dia(ahora.hour) != franja:
        return
    clave = f"{ahora.date().isoformat()}-{franja}"
    if ultimo_aviso["clave"] == clave:
        return
    ultimo_aviso["clave"] = clave
    print(f"🕐🐾 Michi: Ya es la hora en que sueles venir {FRASE_FRANJA[franja]}... "
          f"¡te estaba esperando, dueño-amo!")


cargar_habitos()

# ALIMENTAR
def alimentar():
    if not mascota["viva"]:
        return
    registrar_cuidado("alimentar")
    mascota["comida"] += 40
    mascota["salud"] += 5
    mascota["horas_sin_cuidado"] = 0
    mascota["comida"] = max(0, min(100, mascota["comida"]))
    mascota["salud"] = min(100, mascota["salud"])
    mensajes = [
        "😻🍗 Michi: ¡Miauuuu! ¡Qué rico! ¡Gracias, dueño-amo!",
        "😋🍖 Michi: ¡Estaba deliciosoooo!",
        "🐱🍗 Michi: ¡Ñam ñam ñam! Mi pancita está feliz.",
        "🥰🐾 Michi: Gracias por alimentarme ❤️"
    ]
    print(random.choice(mensajes))
    mostrar_estadisticas_de_michi()
# DAR CARIÑO
def dar_carino():
    if not mascota["viva"]:
        return
    registrar_cuidado("dar_carino")
    mascota["felicidad"] += 25
    mascota["horas_sin_carino"] = 0
    mascota["horas_sin_cuidado"] = 0
    mascota["felicidad"] = min(100, mascota["felicidad"])
    mensajes = [
        "😻❤️ Michi: ¡Miauuuu! ¡Me encantan tus cariños!",
        "🥰💕 Michi: ¡Eso hizo muy feliz a mi corazoncito!",
        "😸🐾 Michi: ¡Más mimos, más mimos!",
        "❤️🐱 Michi: ¡Te estaba esperando, dueño-amo!"
    ]
    print(random.choice(mensajes))
    mostrar_estadisticas_de_michi()
# JUGAR
def jugar():
    if not mascota["viva"]:
        return
    if mascota["energia"] < 20:
        print("😴💤 Michi: Quiero jugar... pero estoy demasiado cansadito :(")
        return
    registrar_cuidado("jugar")
    mascota["felicidad"] += 15
    mascota["energia"] -= 20
    mascota["comida"] -= 5
    mascota["horas_sin_cuidado"] = 0
    mascota["felicidad"] = min(100, mascota["felicidad"])
    mascota["comida"] = max(0, min(100, mascota["comida"]))
    mascota["energia"] = max(0, mascota["energia"])
    mensajes = [
        "🎾🤩 Michi: ¡Siiii! ¡Qué divertido!",
        "😻🐾 Michi: ¡Me encantó jugar contigo!",
        "😸🎾 Michi: ¡Otra vez, otra vez, otra veeeez!",
        "🐾✨ Michi: ¡Eso estuvo geniaaaal!"
    ]
    print(random.choice(mensajes))
    mostrar_estadisticas_de_michi()
# DESCANSAR
def descansar():
    if not mascota["viva"]:
        return
    registrar_cuidado("descansar")
    mascota["energia"] += 40
    mascota["horas_sin_cuidado"] = 0
    mascota["energia"] = min(100, mascota["energia"])
    mensajes = [
        "😴💤 Michi: Zzzzz... qué rico descansar...",
        "🥱🐱 Michi: Ya me siento mucho mejor.",
        "😸⚡ Michi: ¡Recuperé mi energía!",
        "🐱🛏️ Michi: Cinco minutitos más... zzz..."
    ]
    print(random.choice(mensajes))
    mostrar_estadisticas_de_michi()

# ===================================================================
# El banco de palabras / base de conocimientos de Michi vive ahora en
# banco_palabras.py. Aquí solo lo importamos para poder usarlo.
# ===================================================================
# DETECCIÓN DE PALABRAS Y FRASES
def contiene_alguna(mensaje, opciones):
    """
    Comprueba si el mensaje contiene alguna palabra
    o frase de la lista.
    Seguimos utilizando reglas preestablecidas.
    """
    for opcion in opciones:
        patron = r"\b" + re.escape(suavizar_texto(normalizar_texto(opcion))) + r"\b"
        if re.search(patron, mensaje):
            return True
    return False
# DETECTAR INTENCIÓN DEL USUARIO
def detectar_intencion_ia(mensaje):
    # Quiere un ejemplo
    if contiene_alguna(mensaje, [
        "ejemplo","ejemplos","dame un ejemplo","ponme un ejemplo",
        "caso","casos", "dime ejemplos", "aplicaciones en", "dame aplicaciones",
        "dame aplicaciones", "mas ejemplos", "mas aplicaciones"
    ]):
        return "ejemplo"
    # Quiere una lista
    elif contiene_alguna(mensaje, [
        "cuales son","menciona","mencionalos","lista",
        "enumera","cuantos son"
    ]):
        return "lista"
    # Pregunta qué hace o para qué sirve
    elif contiene_alguna(mensaje, [
        "que hace","para que sirve","como funciona","que funcion tiene",
        "cual es su funcion", "que finalidad", "cual es su proposito"
    ]):
        return "funcion"
    # Por defecto quiere una explicación
    else:
        return "definicion"
# DETECTAR TEMA DE INTELIGENCIA ARTIFICIAL
def detectar_tema_ia(mensaje):
    # IMPORTANTE:
    # Primero buscamos conceptos específicos.
    # Al final dejamos conceptos generales como "agente" o "IA".
    reglas_temas = [
        # MICHI
        (
            "michi_agente",
            [
                "que tipo de agente eres", "que agente eres", "michi que tipo de agente",
                "por que eres agente basado en metas", "michi es agente basado en metas",
                "eres un agente", "que metas tienes", "cuales son tus metas",
                "por que priorizas", "como decides que hacer"
            ]
        ),
        # LOS CUATRO ENFOQUES (filosóficos, Russell y Norvig)
        (
            "cuatro_enfoques",
            [
                "cuatro enfoques", "4 enfoques", "formas de hacer inteligencia artificial",
                "formas de hacer ia", "enfoques de la ia", "enfoques de inteligencia artificial",
                "cuales son los 4 enfoques de la IA"
            ]
        ),
        (
            "pensar_como_humanos",
            [
                "pensar como humanos", "pensar como humano","pensamiento humano"
            ]
        ),
        (
            "actuar_como_humanos",
            [
                "actuar como humanos","actuar como humano","comportarse como humanos", "emular fisicamente al humano"
            ]
        ),
        (
            "pensar_racionalmente",
            [
                "pensar racionalmente","pensamiento racional"
            ]
        ),
        (
            "actuar_racionalmente",
            [
                "actuar racionalmente","accion racional","agente racional"
            ]
        ),
        # ENFOQUES DE CONSTRUCCIÓN (simbólica / conectivista / evolutiva)
        (
            "enfoques_construccion_ia",
            [
                "ia simbolica", "ia conectivista", "ia basada en evolucion",
                "enfoques de construccion", "paradigmas de la ia",
                "tipos de ia segun su construccion", "algoritmos geneticos"
            ]
        ),
        # EVOLUCIÓN / HISTORIA
        (
            "evolucion_ia",
            [
                "evolucion de la ia", "historia de la ia", "hitos de la ia",
                "linea de tiempo de la ia", "cuando se creo la ia",
                "origen de la ia", "conferencia de dartmouth", "mycin"
            ]
        ),
        # MÉTODOS DE APRENDIZAJE
        (
            "metodos_aprendizaje",
            [
                "metodos de aprendizaje", "tipos de aprendizaje",
                "como aprende una ia", "formas de aprendizaje de la ia"
            ]
        ),
        (
            "aprendizaje_supervisado",
            ["aprendizaje supervisado"]
        ),
        (
            "aprendizaje_no_supervisado",
            ["aprendizaje no supervisado"]
        ),
        (
            "aprendizaje_refuerzo",
            ["aprendizaje por refuerzo", "aprendizaje reforzado"]
        ),
        # APLICACIONES E IA GENERATIVA
        (
            "ia_generativa",
            [
                "ia generativa", "dall-e", "dalle", "chatgpt", "gemini",
                "generar imagenes con ia", "generar texto con ia"
            ]
        ),
        (
            "aplicaciones_ia",
            [
                "aplicaciones de la ia", "aplicaciones actuales de la ia",
                "para que se usa la ia", "usos de la ia",
                "asistentes virtuales", "vehiculos autonomos", "diagnostico medico"
            ]
        ),
        # SUBCAMPOS
        (
            "sistemas_expertos",
            ["sistemas expertos", "que es un sistema experto"]
        ),
        (
            "aprendizaje_automatico",
            ["aprendizaje automatico", "machine learning", "que es machine learning"]
        ),
        (
            "subcampos_ia",
            [
                "subcampos de la ia", "campos de la ia", "ramas de la ia",
                "vision por computadora", "procesamiento del lenguaje natural", "pln", "robotica"
            ]
        ),
        # RELACIONES CON OTRAS DISCIPLINAS
        (
            "relaciones_ia_disciplinas",
            [
                "relacion de la ia con otras disciplinas", "disciplinas relacionadas con la ia",
                "ia y la filosofia", "ia y neurociencia", "ia y linguistica",
                "ia y matematicas", "ciencias cognitivas"
            ]
        ),
        # TIPOS DE AGENTES
        (
            "tipos_agentes",
            [
                "tipos de agentes","tipos de agente","clases de agentes","cuatro tipos de agentes","4 tipos de agentes"
            ]
        ),
        (
            "reflejo_simple",
            [
                "agente de reflejo simple","reflejo simple"
            ]
        ),
        (
            "basado_modelos",
            [
                "agente basado en modelos","basado en modelos","agente de modelo"
            ]
        ),
        (
            "basado_metas",
            [
                "agente basado en metas","basado en metas","agente de metas",
                "agente basado en el logro de metas","logro de metas"
            ]
        ),
        (
            "basado_utilidad",
            [
                "agente basado en utilidad","basado en utilidad","agente de utilidad",
                "mejor desempeño","logro del mejor desempeño","agente de mejor desempeño"
            ]
        ),
        (
            "agente_aprende",
            [
                "agente que aprende","agentes que aprenden","agente de aprendizaje"
            ]
        ),
        # ESTRUCTURA Y AMBIENTES DE UN AGENTE
        (
            "estructura_agente",
            [
                "estructura de un agente", "partes de un agente",
                "sensores y actuadores", "funcion de agente",
                "como esta compuesto un agente"
            ]
        ),
        (
            "tipos_ambientes",
            [
                "tipos de ambientes", "tipos de entornos",
                "ambiente estatico", "ambiente dinamico", "entorno observable"
            ]
        ),
        (
            "propiedades_entornos",
            [
                "propiedades de los entornos", "propiedades del entorno",
                "entorno deterministico", "entorno episodico", "entorno semidinamico"
            ]
        ),
        # CONCEPTOS DE AGENTES
        (
            "construccion_agente",
            [
                "como se construye un agente",
                "construir un agente",
                "arquitectura del agente",
                "programa del agente"
            ]
        ),
        (
            "formas_agente",
            [
                "formas de agente",
                "formas de un agente",
                "formas que puede adoptar un agente",
                "agente humano",
                "agente robotico",
                "agente software"
            ]
        ),
        (
            "agente_inteligente",
            [
                "agente inteligente",
                "que es un agente inteligente"
            ]
        ),
        (
            "agente",
            [
                "que es un agente","define agente", "explica agente","agente"
            ]
        ),
        # IA GENERAL
        (
            "facetas",
            [
                "facetas del comportamiento inteligente",
                "facetas de la inteligencia",
                "percibir razonar aprender actuar",
                "capacidades de la inteligencia"
            ]
        ),
        (
            "inteligencia_artificial",
            [
                "inteligencia artificial",
                "que es ia",
                "define ia",
                "explica ia",
                "ia"
            ]
        )
    ]
    for tema, palabras_clave in reglas_temas:
        if contiene_alguna(mensaje, palabras_clave):
            return tema
    return None

# ===================================================================
# MEMORIA CONVERSACIONAL (últimos 3 temas de IA)
# ===================================================================
# Michi ahora recuerda los últimos 3 temas de IA de los que habló.
# Esto le permite responder preguntas de seguimiento como "dame un
# ejemplo" o "cuales son" sin que el usuario tenga que repetir el
# tema cada vez, sin dejar de ser (en esencia) un sistema de reglas:
# no "entiende" el mensaje, solo recuerda cuál fue el último tema
# válido que detectó.
memoria_conversacion = {
    "temas_recientes": deque(maxlen=3)
}


def tema_mas_reciente():
    """Devuelve el último tema de IA tratado, o None si no hay ninguno."""
    if memoria_conversacion["temas_recientes"]:
        return memoria_conversacion["temas_recientes"][-1]
    return None


# RESPONDER PREGUNTAS DE IA
def responder_ia(mensaje):
    tema = detectar_tema_ia(mensaje)
    intencion = detectar_intencion_ia(mensaje)

    # Si el mensaje no menciona ningún tema nuevo, pero sí pide un
    # seguimiento (ejemplo, lista, función) y hay un tema reciente
    # guardado en memoria, reutiliza ese tema. Así Michi mantiene el
    # hilo de la conversación sin necesitar que se repita el tema.
    if tema is None:
        if intencion != "definicion" and tema_mas_reciente() is not None:
            tema = tema_mas_reciente()
        else:
            return None

    # Guarda este tema como el más reciente (la memoria conserva
    # automáticamente solo los últimos 3, gracias al deque).
    memoria_conversacion["temas_recientes"].append(tema)

    informacion = CONOCIMIENTOS_IA[tema]
    # Si existe una respuesta específica
    # para esa intención, la utiliza.
    if intencion in informacion:
        respuestas = informacion[intencion]
    # Si no existe, utiliza la definición.
    elif "definicion" in informacion:
        respuestas = informacion["definicion"]
    # Último respaldo
    else:
        respuestas = [
            "🐱📚 Michi: Conozco ese tema, "
            "pero todavía no sé responder esa pregunta."
        ]
    return random.choice(respuestas)
# ===================================================================
# APRENDIZAJE DE PALABRAS
# ===================================================================
# Michi puede ampliar su vocabulario de dos formas:
#
#  1) A la fuerza: el usuario le enseña con comandos.
#       aprende chido significa felicitacion   (palabra -> categoría)
#       aprende que onda => Todo tranqui, amo  (frase -> respuesta)
#       olvida chido                           (borra lo aprendido)
#       que has aprendido                      (lista lo aprendido)
#
#  2) Preguntando: cuando Michi no entiende una frase corta, en vez de
#     rendirse pregunta "¿qué significa?" y la siguiente respuesta del
#     usuario (una categoría) le enseña la palabra.
#
# Sigue siendo un sistema de reglas: Michi NO comprende el significado,
# solo agrega la palabra a la lista de la categoría indicada. Lo aprendido
# se guarda en vocabulario_michi.json para recordarlo entre sesiones.
ARCHIVO_VOCABULARIO = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "vocabulario_michi.json"
)

# clave interna -> nombre que se le muestra al usuario
NOMBRES_CATEGORIA = {
    "saludo": "saludo",
    "estado": "cómo estás",
    "jugar": "jugar",
    "comida": "comida",
    "carino": "cariño",
    "te_quiero": "te quiero",
    "triste": "tristeza",
    "dormir": "dormir",
    "regano": "regaño",
    "felicitacion": "felicitación",
    "gracias": "gracias",
    "despedida": "despedida",
}

# Nombres alternativos que el usuario puede escribir para cada categoría.
_ALIAS_EXTRA = {
    "saludo": ["saludar", "hola"],
    "estado": ["como estas", "estado"],
    "jugar": ["juego", "jugar"],
    "comida": ["hambre", "comer"],
    "carino": ["mimos", "afecto", "amor"],
    "te_quiero": ["declaracion", "quiero"],
    "triste": ["triste"],
    "dormir": ["descansar", "sueno", "siesta"],
    "regano": ["reprimenda"],
    "felicitacion": ["felicitar", "elogio"],
    "gracias": ["agradecer"],
    "despedida": ["adios", "bye"],
}
ALIAS_CATEGORIA = {}
for _clave, _nombre in NOMBRES_CATEGORIA.items():
    for _alias in [_clave.replace("_", " "), _nombre] + _ALIAS_EXTRA.get(_clave, []):
        ALIAS_CATEGORIA[normalizar_texto(_alias)] = _clave

vocabulario = {
    "palabras": {clave: [] for clave in NOMBRES_CATEGORIA},
    "respuestas": {},
}
# Frase corta que Michi no entendió y sobre la que espera una categoría.
pendiente_aprender = {"frase": None}


def guardar_vocabulario():
    try:
        with open(ARCHIVO_VOCABULARIO, "w", encoding="utf-8") as archivo:
            json.dump(vocabulario, archivo, ensure_ascii=False, indent=2)
    except OSError:
        print("🐱⚠️ Michi: Aprendí eso, pero no pude guardarlo en el archivo.")


def cargar_vocabulario():
    if not os.path.exists(ARCHIVO_VOCABULARIO):
        return
    try:
        with open(ARCHIVO_VOCABULARIO, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        for clave, lista in datos.get("palabras", {}).items():
            if clave in vocabulario["palabras"]:
                vocabulario["palabras"][clave] = list(lista)
        vocabulario["respuestas"] = dict(datos.get("respuestas", {}))
    except (OSError, ValueError):
        pass  # archivo dañado: Michi empieza sin vocabulario aprendido


def coincide(mensaje, categoria, base):
    """
    True si el mensaje contiene alguna palabra base de la categoría
    (las que ya venían escritas en el código) o alguna que Michi
    haya aprendido para esa categoría.
    """
    for palabra in base:
        if suavizar_texto(normalizar_texto(palabra)) in mensaje:
            return True
    aprendidas = vocabulario["palabras"].get(categoria, [])
    if aprendidas and contiene_alguna(mensaje, aprendidas):
        return True
    # Último recurso: coincidencia aproximada (errores de tipeo leves).
    for palabra in list(base) + aprendidas:
        if palabra_parecida(suavizar_texto(normalizar_texto(palabra)), mensaje):
            return True
    return False


def limpiar_frase(texto):
    return texto.strip().strip("\"'“”«»:.,;!¡?¿ ")


def ensenar_palabra(frase, categoria):
    frase = normalizar_texto(frase)
    # Si la palabra estaba en otra categoría, se corrige (se mueve).
    for lista in vocabulario["palabras"].values():
        if frase in lista:
            lista.remove(frase)
    vocabulario["palabras"][categoria].append(frase)
    guardar_vocabulario()
    print(f"😸📖 Michi: ¡Aprendí! Ahora sé que «{frase}» tiene que ver con "
          f"{NOMBRES_CATEGORIA[categoria]}.")


def listar_categorias():
    return ", ".join(NOMBRES_CATEGORIA.values())


def procesar_aprendizaje(original, mensaje):
    """
    Maneja todo lo relacionado con aprender. Devuelve True si el mensaje
    fue un asunto de aprendizaje (y por tanto ya se respondió), o False
    para que conversar() lo procese normalmente.
    """
    # 1) Michi había preguntado "¿qué significa?" y espera una categoría.
    if pendiente_aprender["frase"] is not None:
        frase = pendiente_aprender["frase"]
        pendiente_aprender["frase"] = None
        if mensaje in ("no", "nada", "cancelar", "paso", "olvidalo"):
            print("🐱🐾 Michi: Está bien, no aprendo nada por ahora.")
            return True
        categoria = ALIAS_CATEGORIA.get(limpiar_frase(mensaje))
        if categoria:
            ensenar_palabra(frase, categoria)
            return True
        # No era una categoría: se trata como un mensaje normal.
        return False

    # 2) aprende ...
    if re.match(r"^aprende\b", mensaje):
        cuerpo = re.sub(r"^\s*aprende\s*:?\s*", "", original, flags=re.IGNORECASE)
        # 2a) frase => respuesta
        if "=>" in cuerpo:
            frase, respuesta = cuerpo.split("=>", 1)
            frase = normalizar_texto(limpiar_frase(frase))
            respuesta = respuesta.strip()
            if frase and respuesta:
                vocabulario["respuestas"][frase] = respuesta
                guardar_vocabulario()
                print(f"😸📖 Michi: ¡Listo! Cuando me digas «{frase}» te responderé eso.")
                return True
        # 2b) palabra significa categoría
        coincidencia = re.match(
            r"^(.+?)\s+(?:significa|quiere decir|es sinonimo de)\s+(.+)$",
            normalizar_texto(cuerpo),
        )
        if coincidencia:
            palabra = limpiar_frase(coincidencia.group(1))
            categoria = ALIAS_CATEGORIA.get(limpiar_frase(coincidencia.group(2)))
            if not palabra or len(palabra.split()) > 4:
                print("🐱❓ Michi: Enséñame frases cortas, de máximo 4 palabras, por favor.")
            elif categoria is None:
                print("🐱❓ Michi: No conozco esa categoría. Las que sé son: "
                      + listar_categorias() + ".")
            else:
                ensenar_palabra(palabra, categoria)
            return True
        print("🐱📖 Michi: Puedes enseñarme así:")
        print("   • aprende <palabra> significa <categoría>")
        print("   • aprende <frase> => <respuesta>")
        print("   Categorías: " + listar_categorias() + ".")
        return True

    # 3) olvida ...
    coincidencia = re.match(r"^(?:olvida|olvidate de|borra)\s+(.+)$", mensaje)
    if coincidencia:
        frase = limpiar_frase(coincidencia.group(1))
        olvidada = False
        for lista in vocabulario["palabras"].values():
            if frase in lista:
                lista.remove(frase)
                olvidada = True
        if frase in vocabulario["respuestas"]:
            del vocabulario["respuestas"][frase]
            olvidada = True
        if olvidada:
            guardar_vocabulario()
            print(f"🐱💭 Michi: Ya olvidé «{frase}».")
        else:
            print(f"🐱❓ Michi: No tenía aprendida «{frase}».")
        return True

    # 4) ¿qué has aprendido?
    if contiene_alguna(mensaje, [
        "que has aprendido", "palabras aprendidas", "que palabras sabes",
        "que palabras te he ensenado", "que te he ensenado"
    ]):
        hay_algo = False
        print("🐱📖 Michi: Esto es lo que me has enseñado:")
        for clave, lista in vocabulario["palabras"].items():
            if lista:
                hay_algo = True
                print(f"   • {NOMBRES_CATEGORIA[clave]}: " + ", ".join(lista))
        for frase, respuesta in vocabulario["respuestas"].items():
            hay_algo = True
            print(f"   • «{frase}» → {respuesta}")
        if not hay_algo:
            print("   Todavía nada... ¡enséñame algo, amo! (escribe: aprende)")
        return True

    return False


cargar_vocabulario()

# ===================================================================
# MEMORIA DEL DUEÑO: nombre y gustos
# ===================================================================
# Michi recuerda lo que le cuentas de ti ("me llamo Ana", "me gusta el
# pollo") y lo usa después. Se guarda en perfil_michi.json. Sigue siendo
# una regla: detecta el patrón de la frase y guarda el texto, sin
# entender su significado.
ARCHIVO_PERFIL = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "perfil_michi.json"
)
perfil = {"nombre": None, "gustos": [], "recuerdos": {}, "preguntados": {}}


def guardar_perfil():
    try:
        with open(ARCHIVO_PERFIL, "w", encoding="utf-8") as archivo:
            json.dump(perfil, archivo, ensure_ascii=False, indent=2)
    except OSError:
        pass


def cargar_perfil():
    if not os.path.exists(ARCHIVO_PERFIL):
        return
    try:
        with open(ARCHIVO_PERFIL, encoding="utf-8") as archivo:
            datos = json.load(archivo)
        perfil["nombre"] = datos.get("nombre") or None
        perfil["gustos"] = [str(g) for g in datos.get("gustos", [])][-30:]
        recuerdos = datos.get("recuerdos", {})
        if isinstance(recuerdos, dict):
            perfil["recuerdos"] = {k: v for k, v in recuerdos.items()
                                   if isinstance(v, dict) and "texto" in v}
        preguntados = datos.get("preguntados", {})
        if isinstance(preguntados, dict):
            perfil["preguntados"] = {k: float(v) for k, v in preguntados.items()
                                     if isinstance(v, (int, float))}
    except (OSError, ValueError, AttributeError):
        pass


def amo():
    """Cómo llama Michi al dueño: por su nombre si lo conoce."""
    return perfil["nombre"] or "dueño-amo"


def saludo_horario():
    franja = franja_del_dia(datetime.now().hour)
    if franja == "mañana":
        return "Buenos días"
    if franja == "tarde":
        return "Buenas tardes"
    return "Buenas noches"


def procesar_perfil(original, mensaje):
    """True si el mensaje trataba del nombre o los gustos del dueño."""
    ms = suavizar_texto(mensaje)

    # "me llamo Ana" / "mi nombre es Ana" / "llámame Ana"
    m = re.search(r"\b(?:me llamo|mi nombre es|ll[aá]mame)\s+(.+?)[\s.!]*$",
                  original, flags=re.IGNORECASE)
    if m:
        nombre = limpiar_frase(m.group(1))
        if not nombre or len(nombre.split()) > 3:
            print("🐱❓ Michi: Miau... dime solo tu nombre, de máximo 3 palabras.")
            return True
        perfil["nombre"] = " ".join(p[:1].upper() + p[1:] for p in nombre.split())
        guardar_perfil()
        print(random.choice([
            f"😻✨ Michi: ¡Mucho gusto, {perfil['nombre']}! Ya me lo aprendí.",
            f"😸🐾 Michi: ¡{perfil['nombre']}! Qué nombre tan bonito, miau.",
            f"🥰📝 Michi: ¡Anotado! De ahora en adelante te diré {perfil['nombre']}.",
        ]))
        return True

    if contiene_alguna(ms, ["como me llamo", "cual es mi nombre", "sabes mi nombre",
                            "recuerdas mi nombre", "sabes como me llamo"]):
        if perfil["nombre"]:
            print(f"😸❤️ Michi: ¡Claro que sí! Te llamas {perfil['nombre']}.")
        else:
            print("🐱❓ Michi: Miau... todavía no sé tu nombre. Dime: «me llamo ...»")
        return True

    # "me gusta el pollo" / "me encantan los gatos"
    m = re.match(r"^me (?:gusta|gustan|encanta|encantan)\s+(.+?)[\s.!]*$", mensaje)
    if m:
        gusto = limpiar_frase(m.group(1))
        if gusto and len(gusto.split()) <= 6:
            if gusto not in perfil["gustos"]:
                perfil["gustos"].append(gusto)
                del perfil["gustos"][:-30]
                guardar_perfil()
            print(random.choice([
                f"😸📝 Michi: ¡Anotado, {amo()}! Recordaré que te gusta «{gusto}».",
                f"🥰🐾 Michi: ¡Qué bien! «{gusto}»... lo guardo en mi cabecita.",
                f"😻✨ Michi: ¿«{gusto}»? ¡Miau! Ahora sé algo más de ti.",
            ]))
            return True

    if contiene_alguna(ms, ["que recuerdas de mi", "que recuerdas sobre mi",
                            "que te he contado", "que te he dicho"]):
        mostrar_recuerdos()
        return True

    if contiene_alguna(ms, ["que me gusta", "que cosas me gustan", "cuales son mis gustos",
                            "que sabes de mis gustos"]):
        if perfil["gustos"]:
            print("😸📖 Michi: Me has contado que te gusta: " + ", ".join(perfil["gustos"]) + ".")
        else:
            print("🐱❓ Michi: Todavía no me has contado qué te gusta. Dime: «me gusta ...»")
        return True

    return False


cargar_perfil()


# ===================================================================
# AFIRMACIONES, NEGACIONES Y DUDAS
# ===================================================================
# Michi reconoce respuestas cortas como "sí", "claro", "no", "ahorita no",
# "quizás"... y las interpreta según lo ÚLTIMO que él pidió o preguntó
# (su "contexto"). Por ejemplo, si Michi dijo "¿me das comidita?" y tú
# respondes "sí", Michi lo toma como aceptar y se alimenta. Si no hay
# pregunta reciente, responde de forma general.
# Además detecta negaciones dentro de frases ("no quiero jugar",
# "no tengo hambre") para no confundirlas con "quiero jugar".
AFIRMACIONES = {
    "si", "sip", "sep", "simon", "claro", "claro que si", "por supuesto",
    "por supuesto que si", "obvio", "obviamente", "dale", "va", "vale", "ok",
    "okay", "okey", "aja", "sale", "andale", "de acuerdo", "correcto",
    "exacto", "afirmativo", "seguro", "esta bien", "con gusto", "desde luego",
    "cierto", "asi es", "yes", "yep", "yeah", "bueno", "si claro", "si quiero",
    "quiero", "claro quiero", "vamos", "hecho", "me parece bien", "buena idea",
    "yo tambien", "igualmente", "si si", "claro si", "si dale", "si va",
}
NEGACIONES = {
    "no", "nop", "nope", "nel", "nones", "nah", "nunca", "jamas", "tampoco",
    "negativo", "para nada", "ni hablar", "ni de broma", "de ninguna manera",
    "claro que no", "por supuesto que no", "no quiero", "no puedo", "no tengo",
    "ahora no", "ahorita no", "todavia no", "aun no", "mejor no", "ya no",
    "no creo", "no por ahora", "no no", "yo tampoco", "hoy no", "ni modo",
    "luego", "despues", "mas tarde", "al rato", "otro dia", "en otro momento",
}
DUDAS = {
    "quiza", "quizas", "tal vez", "talvez", "a lo mejor", "puede ser", "no se",
    "no lo se", "ni idea", "no tengo idea", "depende", "mas o menos", "hmm",
    "mmm", "igual y",
}

# Lo que Michi pidió -> tema del que trata (para interpretar "sí"/"no").
TEMA_DE_PREGUNTA = {
    "COMIDA_URGENTE": "comida", "PEDIR_COMIDA": "comida",
    "PEDIR_DESCANSO": "descanso",
    "PEDIR_CARINO": "carino", "PEDIR_ATENCION": "carino", "ESTAR_TRISTE": "carino",
    "QUERER_JUGAR": "jugar",
    "PEDIR_CUIDADO": "cuidado",
}
VIGENCIA_PREGUNTA = 120      # segundos que una pregunta de Michi sigue "abierta"
contexto_pregunta = {"tema": None, "hora": 0.0}


def recordar_pregunta(tema):
    contexto_pregunta["tema"] = tema
    contexto_pregunta["hora"] = time.time()
    contexto_pregunta["n"] = charla_estado["contador"]   # en qué mensaje se hizo


def pregunta_vigente():
    """Tema de la última pregunta de Michi si todavía está 'abierta', o None."""
    tema = contexto_pregunta["tema"]
    if tema and time.time() - contexto_pregunta["hora"] <= VIGENCIA_PREGUNTA:
        return tema
    return None


def clasificar_respuesta_corta(mensaje):
    """Devuelve 'si', 'no', 'duda' o None, solo para respuestas cortas."""
    # "no michi" / "michi no" son regaños: los maneja su propia regla.
    if re.search(r"\bno michi\b|\bmichi no\b", mensaje):
        return None
    texto = re.sub(r"\b(?:por favor|porfa|porfis|gracias|michi|amo|dueno|pues|ah|eh|oh)\b",
                   " ", mensaje)
    palabras = re.findall(r"[a-z0-9]+", texto)
    if not palabras or len(palabras) > 5:
        return None
    frase = " ".join(palabras)
    if frase in NEGACIONES:
        return "no"
    if frase in AFIRMACIONES:
        return "si"
    if frase in DUDAS:
        return "duda"
    return None


def responder_si_no(mensaje):
    """True si el mensaje era un sí / no / duda y Michi ya respondió."""
    tipo = clasificar_respuesta_corta(mensaje)
    if tipo is None:
        return False
    tema = pregunta_vigente()
    contexto_pregunta["tema"] = None          # la pregunta ya se contestó

    if tipo == "si":
        if tema == "jugar":
            print("🤩🎾 Michi: ¡Síííí! ¡Vamos a jugar!")
            jugar()
        elif tema == "comida":
            print("😻🍗 Michi: ¡Yupiii! ¡Comidita!")
            alimentar()
        elif tema == "carino":
            print("🥰💕 Michi: ¡Siii! Ven, mimos, mimos...")
            dar_carino()
        elif tema == "descanso":
            print("😴💤 Michi: Gracias, amo... me voy a dormir un ratito. zzz...")
            descansar()
        elif tema == "cuidado":
            print("🥺❤️ Michi: Gracias... ojalá me des comida o cariño pronto.")
        else:
            print(random.choice([
                "😸🐾 Michi: ¡Miau! ¿Sí qué? Cuéntame más.",
                "🐱❓ Michi: Me dices que sí... pero no te había preguntado nada :3",
                "😸✨ Michi: ¡Qué bien! Me encanta cuando estás de acuerdo.",
            ]))
    elif tipo == "no":
        if tema == "jugar":
            print(random.choice([
                "😿🎾 Michi: Aww... está bien, jugamos después.",
                "🥺🐾 Michi: Bueno... aquí estaré por si cambias de opinión.",
            ]))
        elif tema == "comida":
            if mascota["comida"] <= 50:
                print("😭🍗 Michi: ¿Nooo? Pero tengo hambre... :(((")
            else:
                print("😸🍗 Michi: Está bien, aguanto un ratito más.")
        elif tema == "carino":
            print("🥺💔 Michi: Oh... bueno. Aquí estaré por si cambias de opinión.")
        elif tema == "descanso":
            print("😾💤 Michi: Pero tengo sueño... bueno, aguanto un poquito más.")
        elif tema == "cuidado":
            print("🥺😿 Michi: Ay... no me siento bien, pero está bien.")
        else:
            print(random.choice([
                "😿🐾 Michi: ¿No? Bueno... está bien.",
                "🐱👍 Michi: Entendido, amo.",
                "🥺🐱 Michi: Ay... bueno, como tú digas.",
            ]))
    else:  # duda
        if tema:
            print("🐱🤔 Michi: Tómate tu tiempo... pero ojalá que sí 🥺")
            recordar_pregunta(tema)            # la pregunta sigue abierta
        else:
            print("🤔🐾 Michi: ¿Quizás? Piénsalo con calma, yo espero aquí.")
    return True


# Temas que Michi reconoce dentro de una frase negada.
TEMAS_NEGABLES = [
    ("jugar", ["jugar", "jugamos", "juguemos", "juego", "pelota", "convivir", "pasar tiempo"]),
    ("comida", ["hambre", "comida", "comer", "alimento", "croquetas", "pollo", "hambriento"]),
    ("carino", ["carino", "mimos", "abrazo", "acariciar", "acaricio", "amor", "afecto"]),
    ("dormir", ["dormir", "duerme", "descansar", "sueno", "siesta", "agotado", "exhausto"]),
    ("triste", ["triste", "tristeza", "llorar", "llorando"]),
    ("te_quiero", ["te quiero", "te amo", "te adoro"]),
]


def responder_negacion_con_tema(original, mensaje):
    """
    Detecta frases negadas sobre un tema ("no quiero jugar", "no tengo
    hambre", "ya no estoy triste") para no responderlas como si fueran
    afirmativas. Las preguntas ("¿no quieres jugar?") se dejan pasar.
    """
    if "?" in original or "¿" in original:
        return False
    if not re.search(r"\b(?:no|nunca|jamas|tampoco)\b", mensaje):
        return False
    if re.search(r"\bno michi\b|\bmichi no\b", mensaje):
        return False                           # regaño: otra regla
    contexto_pregunta["tema"] = None

    if contiene_alguna(mensaje, ["no te vayas", "no te vallas", "no me dejes", "no me abandones"]):
        print(random.choice([
            "🥹❤️ Michi: ¡Me quedo contigo! No me voy a ningún lado.",
            "😻🐾 Michi: Aquí estoy, aquí me quedo. ¡Miau!",
        ]))
        return True

    if contiene_alguna(mensaje, ["no entiendo", "no comprendo", "no entendi"]):
        print("🥺🐱 Michi: Perdón, a veces no me explico bien. ¿Probamos de otra manera?")
        return True

    tema_detectado = None
    for tema, base in TEMAS_NEGABLES:
        if coincide(mensaje, tema, base):
            tema_detectado = tema
            break
    if tema_detectado is None:
        return False

    if tema_detectado == "jugar":
        print(random.choice([
            "😿🎾 Michi: Oh... está bien, no jugamos. Aquí estaré por si cambias de opinión.",
            "🥺🐾 Michi: Entonces jugamos después, ¿sí?",
        ]))
    elif tema_detectado == "comida":
        if mascota["comida"] <= 40:
            print("🥺🍗 Michi: Ah... pues yo sí tengo hambre. ¿Me das un poquito?")
            recordar_pregunta("comida")
        else:
            print("😸🐾 Michi: Entiendo, entonces nada de comida por ahora.")
    elif tema_detectado == "carino":
        print("🥺💔 Michi: Oh... bueno. Sin mimos entonces.")
    elif tema_detectado == "dormir":
        if mascota["energia"] <= 30:
            print("🥱🐱 Michi: Pues yo sí tengo sueño... ¿me dejas dormir un ratito?")
            recordar_pregunta("descanso")
        else:
            print("😸⚡ Michi: Entonces no dormimos. Aquí sigo despierto.")
    elif tema_detectado == "triste":
        print("😸✨ Michi: ¡Qué bueno que no estés triste! Me alegra.")
    else:  # te_quiero
        print("😿💔 Michi: ¿No me quieres? Miau... :(((")
    return True


# ===================================================================
# CHARLAS CON HILO + RECUERDOS QUE MICHI RETOMA
# ===================================================================
# Michi puede iniciar una charla de varios turnos (un "árbol de diálogo"):
# hace una pregunta, interpreta tu respuesta y continúa según lo que
# dijiste. Lo importante que le cuentas se guarda como "recuerdo" en
# perfil_michi.json y, un rato después, Michi lo retoma por su cuenta
# ("antes me contaste que tuviste un mal día... ¿ya estás mejor?").
#
# Sigue siendo un sistema de reglas: todo el contenido está escrito de
# antemano en CHARLAS. Para agregar un tema nuevo basta con añadir nodos.
#
# Tipos de nodo:
#   "emocion"  -> clasifica la respuesta como bien / mal / regular.
#   "si_no"    -> clasifica la respuesta como si / no / duda.
#   "libre"    -> acepta cualquier texto, lo guarda y sigue.
# En "ramas" cada opción es: (siguiente_nodo, [respuestas], contexto).
# "contexto" deja abierta una pregunta de Michi para que un "sí" posterior
# ejecute la acción (por ejemplo "carino" -> Michi recibe cariño).
VIGENCIA_CHARLA = 180            # segundos antes de dar la charla por terminada
COOLDOWN_TEMA = 1800             # no repetir el mismo tema en 30 minutos
SEGUNDOS_ANTES_DE_RETOMAR = 300  # un recuerdo se retoma pasados 5 minutos
PROB_INICIAR_CHARLA = 0.4        # probabilidad de que Michi inicie una charla
MENSAJES_ENTRE_CHARLAS = 3       # mensajes mínimos entre una charla y la siguiente

YO_POR_DEFECTO = [
    "😸🐾 Michi: ¡Yo estoy muy bien, gracias por preguntar! Sigamos con lo tuyo.",
]

CHARLAS = {
    # ---------------- tema: cómo te fue hoy ----------------
    "dia": {
        "tipo": "emocion",
        "pregunta": ["🐱💭 Michi: Oye, ¿cómo te fue hoy?",
                     "😸🐾 Michi: Cuéntame, ¿cómo va tu día?"],
        "yo": ["😸 Michi: ¡El mío va genial! Más ahora que platico contigo. Pero cuéntame de ti."],
        "ramas": {
            "bien": ("dia_bien", ["😻✨ Michi: ¡Qué bueno, me alegra mucho!",
                                  "😸🎉 Michi: ¡Miau! Eso me pone feliz."], None),
            "mal": ("dia_mal", ["😿💔 Michi: Ay, lo siento mucho...",
                                "🥺🐾 Michi: Uy... ven, aquí estoy contigo."], None),
            "regular": ("dia_regular", ["🐱💭 Michi: Mmm, un día normalito."], None),
        },
        "defecto": "regular",
    },
    "dia_bien": {
        "tipo": "libre", "guardar": "mejor_momento",
        "pregunta": ["😸 Michi: ¿Y qué fue lo mejor de tu día?"],
        "yo": ["😻 Michi: Lo mejor de mi día es que estás aquí. ¿Y el tuyo?"],
        "respuesta": ["😻✨ Michi: «{texto}»... ¡qué bonito! Lo voy a recordar.",
                      "😸🐾 Michi: ¡Wow, «{texto}»! Me encanta que me cuentes estas cosas."],
        "cierre": ["🎾 Michi: ¿Jugamos un ratito para celebrar?"],
        "contexto": "jugar",
    },
    "dia_mal": {
        "tipo": "libre", "guardar": "motivo_mal_dia", "cierre_siempre": True,
        "pregunta": ["🥺 Michi: ¿Qué pasó?"],
        "yo": ["🐱 Michi: Yo estoy bien, ¡pero ahora me preocupas tú! ¿Qué pasó?"],
        "respuesta": ["😿 Michi: «{texto}»... suena pesado. Gracias por contármelo."],
        "cierre": ["🥺💕 Michi: ¿Quieres un poquito de cariño?"],
        "contexto": "carino",
    },
    "dia_regular": {
        "tipo": "si_no",
        "pregunta": ["🐱❓ Michi: ¿Hay algo que te preocupe?"],
        "yo": ["😸 Michi: Yo estoy tranquilo, soy un gato. ¿Y tú, hay algo que te preocupe?"],
        "ramas": {
            "si": ("preocupa", ["🥺 Michi: Ay..."], None),
            "duda": ("preocupa", ["🐱 Michi: Si algo te da vueltas en la cabeza, puedes contármelo."], None),
            "no": (None, ["😸 Michi: Bueno, a veces los días son así. ¡Seguro mañana será mejor!"], None),
        },
    },
    "preocupa": {
        "tipo": "libre", "guardar": "preocupacion", "cierre_siempre": True,
        "pregunta": ["🥺 Michi: ¿Qué es lo que te preocupa?"],
        "yo": ["🐱 Michi: A mí solo me preocupa quedarme sin croquetas. ¿Qué te preocupa a ti?"],
        "respuesta": ["🥺💕 Michi: Gracias por confiarme eso. Aquí estoy contigo, siempre."],
        "cierre": ["🥺💕 Michi: ¿Quieres un poquito de cariño?"],
        "contexto": "carino",
    },

    # ---------------- tema: comida ----------------
    "comida": {
        "tipo": "si_no",
        "pregunta": ["😸🍗 Michi: ¿Ya comiste hoy?"],
        "yo": ["😋 Michi: ¡Yo siempre tengo hambre! Croquetas, croquetas... ¿Y tú ya comiste?"],
        "ramas": {
            "si": ("comida_que", ["😸 Michi: ¡Qué bueno, hay que cuidarse!"], None),
            "no": (None, ["😿🍗 Michi: ¡Ay no! Ve a comer algo, ¿sí? Me preocupo por ti."], None),
            "duda": (None, ["🐱 Michi: Acuérdate de comer algo rico, ¿sí?"], None),
        },
    },
    "comida_que": {
        "tipo": "libre", "guardar": "ultima_comida",
        "pregunta": ["😋 Michi: ¿Y qué comiste?"],
        "yo": ["😸🍗 Michi: Yo comería pollo todo el día. ¿Y tú qué comiste?"],
        "respuesta": ["😻🍗 Michi: «{texto}»... ¡suena delicioso! Lo recordaré.",
                      "😋 Michi: Mmm, «{texto}». ¡Qué rico!"],
    },

    # ---------------- tema: sueño ----------------
    "sueno": {
        "tipo": "si_no",
        "pregunta": ["😴 Michi: ¿Dormiste bien anoche?"],
        "yo": ["😸💤 Michi: ¡Yo duermo muchísimo! Soy un gato. ¿Y tú dormiste bien?"],
        "ramas": {
            "si": (None, ["😸💤 Michi: ¡Qué bueno! Dormir bien es súper importante."], None),
            "no": ("sueno_mal", ["😿 Michi: Ay, qué mal..."], None),
            "duda": (None, ["🐱 Michi: A veces cuesta saberlo, ¿verdad?"], None),
        },
    },
    "sueno_mal": {
        "tipo": "libre", "guardar": "sueno",
        "pregunta": ["🥱 Michi: ¿Cuántas horas dormiste, más o menos?"],
        "yo": ["😸💤 Michi: Yo duermo como 16 horas. ¿Y tú cuántas dormiste?"],
        "respuesta": ["😿💤 Michi: Gracias por contarme. Intenta descansar hoy, ¿sí? "
                      "A mí me encantan las siestas."],
    },

    # ---------------- tema: pasatiempos ----------------
    "pasatiempo": {
        "tipo": "libre", "guardar": "gusto",
        "pregunta": ["😸 Michi: ¿Qué te gusta hacer en tu tiempo libre?"],
        "yo": ["😸🎾 Michi: A mí me gusta jugar con la pelota y dormir siestas. ¿Y a ti?"],
        "respuesta": ["😸📝 Michi: «{texto}»... ¡suena genial! Lo guardo en mi cabecita.",
                      "😻🐾 Michi: ¡Qué bien! «{texto}». Me gusta conocer tus cosas."],
    },

    # ---------------- tema: tu nombre ----------------
    "nombre": {
        "tipo": "libre", "guardar": "nombre",
        "pregunta": ["😸❓ Michi: Por cierto... ¡todavía no sé cómo te llamas! ¿Cómo te digo?"],
        "yo": ["😸 Michi: Yo soy Michi, ¡el gato más guapo del mundo! ¿Y tú cómo te llamas?"],
        "respuesta": ["😻✨ Michi: ¡Mucho gusto, {texto}! Ya me lo aprendí."],
    },

    # ---------------- seguimientos (Michi retoma un recuerdo) ----------------
    "seg_mal": {
        "tipo": "si_no",
        "pregunta": ["🐱💭 Michi: Oye, antes me contaste que tuviste un mal día («{texto}»). "
                     "¿Ya estás mejor?"],
        "ramas": {
            "si": (None, ["😻✨ Michi: ¡Me alegra muchísimo!"], None),
            "no": (None, ["🥺💕 Michi: Ay... ven. ¿Quieres un poquito de cariño?"], "carino"),
            "duda": (None, ["🐱 Michi: Poco a poco, ¿sí? Aquí estoy."], None),
        },
    },
    "seg_mejor": {
        "tipo": "si_no",
        "pregunta": ["😸💭 Michi: Me quedé pensando en que lo mejor de tu día fue «{texto}». "
                     "¿Te pasó algo así de bueno otra vez?"],
        "ramas": {
            "si": (None, ["😻 Michi: ¡Genial! Los buenos momentos hay que coleccionarlos."], None),
            "no": (None, ["😸 Michi: Ya vendrán más, ¡seguro!"], None),
            "duda": (None, ["🐱 Michi: Bueno, ¡ojalá que sí!"], None),
        },
    },
    "seg_preocupa": {
        "tipo": "si_no",
        "pregunta": ["🐱💭 Michi: Oye, antes me dijiste que te preocupaba «{texto}». "
                     "¿Ya se arregló algo?"],
        "ramas": {
            "si": (None, ["😻 Michi: ¡Qué alivio!"], None),
            "no": (None, ["🥺💕 Michi: Ánimo... estoy contigo. ¿Quieres un poquito de cariño?"], "carino"),
            "duda": (None, ["🐱 Michi: Ve con calma, un paso a la vez."], None),
        },
    },
    "seg_comida": {
        "tipo": "si_no",
        "pregunta": ["😋 Michi: Antes me dijiste que comiste «{texto}». ¿Ya volviste a comer algo?"],
        "ramas": {
            "si": (None, ["😸 Michi: ¡Bien! Hay que cuidarse."], None),
            "no": (None, ["😿🍗 Michi: ¡No te olvides de comer, eh!"], None),
            "duda": (None, ["🐱 Michi: Acuérdate de comer algo, ¿sí?"], None),
        },
    },
    "seg_gusto": {
        "tipo": "si_no",
        "pregunta": ["😸💭 Michi: Me acuerdo que te gusta «{texto}». ¿Pudiste disfrutarlo hoy?"],
        "ramas": {
            "si": (None, ["😻 Michi: ¡Qué bien! Me alegra."], None),
            "no": (None, ["😿 Michi: Ay... ojalá puedas pronto."], None),
            "duda": (None, ["🐱 Michi: Bueno, ¡que lo disfrutes cuando puedas!"], None),
        },
    },
}

# Recuerdo guardado -> nodo con el que Michi lo retoma.
SEGUIMIENTOS = {
    "motivo_mal_dia": "seg_mal",
    "mejor_momento": "seg_mejor",
    "preocupacion": "seg_preocupa",
    "ultima_comida": "seg_comida",
}
TEMAS_NUEVOS = ("dia", "comida", "sueno", "pasatiempo")
ETIQUETAS_RECUERDO = {
    "mejor_momento": "Lo mejor de tu día",
    "motivo_mal_dia": "Un mal día que tuviste",
    "preocupacion": "Algo que te preocupaba",
    "ultima_comida": "Lo último que comiste",
    "sueno": "Sobre tu sueño",
}

# Estado de la charla actual.
charla = {"nodo": None, "datos": {}, "hora": 0.0, "fallos": 0}
charla_estado = {"contador": 0, "ultimo_fin": 0}

FRASES_PEDIR_CHARLA = {
    "hablemos", "platiquemos", "charlemos", "conversemos", "platicame",
    "platica", "charla", "habla", "platicamos", "quiero hablar",
    "quiero platicar", "quiero charlar", "vamos a platicar", "vamos a hablar",
    "vamos a charlar", "tengo ganas de platicar", "de que hablamos",
    "de que quieres hablar", "dime algo", "cuentame algo", "preguntame algo",
    "preguntame", "hazme preguntas",
}
SALIDAS_DE_CHARLA = ["adios", "bye", "nos vemos", "hasta luego", "me voy", "me tengo que ir",
                     "cambiemos de tema", "dejemos de hablar", "ya no quiero hablar", "basta"]
NO_QUIERE_CONTAR = {
    "nada", "nada importante", "olvidalo", "ya no importa", "luego te cuento",
    "no quiero hablar de eso", "no quiero contarte", "prefiero no decir",
    "ninguno", "ninguna",
}

BIEN = {"bien", "genial", "excelente", "chido", "padre", "increible", "super", "feliz",
        "contento", "contenta", "buenisimo", "mejor", "maravilloso", "perfecto",
        "bonito", "divertido", "productivo", "fantastico", "estupendo", "bueno", "buen"}
MAL = {"mal", "horrible", "pesimo", "terrible", "cansado", "cansada", "estresado",
       "estresada", "triste", "agotado", "agotada", "fatal", "pesado", "pesada",
       "feo", "fea", "fatigado", "harto", "harta", "enfermo", "enferma", "mala",
       "malo", "deprimido", "ansioso", "ansiosa", "agobiado", "agobiada", "caotico"}
REGULAR_FRASES = ["mas o menos", "ni bien ni mal", "asi asi", "ahi va", "normalito",
                  "normal", "regular", "pasable", "maso", "tranquilo", "tranquila"]


def clasificar_emocion(mensaje):
    """Devuelve 'bien', 'mal', 'regular' o None según cómo describe su día."""
    palabras = re.findall(r"[a-z0-9]+", mensaje)
    texto = " ".join(palabras)
    if any(f in texto for f in REGULAR_FRASES):
        return "regular"
    hay_negacion = "no" in palabras or "nada" in palabras or "nunca" in palabras
    bien = bool(set(palabras) & BIEN)
    mal = bool(set(palabras) & MAL)
    if hay_negacion and bien and not mal:
        return "regular"                    # "no muy bien", "no tan bien"
    if hay_negacion and mal and not bien:
        return "regular"                    # "nada mal", "no estuvo mal"
    if mal:
        return "mal"
    if bien:
        return "bien"
    return None


def clasificar_si_no_flexible(mensaje):
    """Como clasificar_respuesta_corta, pero acepta 'sí, pero poquito' o 'no, para nada'."""
    exacto = clasificar_respuesta_corta(mensaje)
    if exacto:
        return exacto
    if re.search(r"\bno michi\b|\bmichi no\b", mensaje):
        return None
    palabras = re.findall(r"[a-z0-9]+", mensaje)
    if not palabras:
        return None
    if palabras[0] in ("si", "claro", "aja", "sip", "simon", "obvio", "dale", "yes"):
        return "si"
    if palabras[0] in ("no", "nop", "nel", "nunca", "jamas", "tampoco"):
        return "no"
    if palabras[0] in ("quiza", "quizas", "talvez") or mensaje.startswith("tal vez"):
        return "duda"
    return None


def limpiar_respuesta_libre(original):
    """'pues comí tacos' -> 'tacos' (quita arranques comunes para repetirlo bien)."""
    base = limpiar_frase(original)[:80]
    texto = base
    patron = (r"^(?:me gustan|me gusta|me encantan|me encanta|lo mejor fue|pues|yo|me|"
              r"comi|comí|desayune|desayuné|almorce|almorcé|cene|cené|fue|fueron|"
              r"tome|tomé|hoy|ahorita)\s+")
    anterior = None
    while anterior != texto:
        anterior = texto
        texto = re.sub(patron, "", texto, flags=re.IGNORECASE)
    return texto.strip() or base


def pide_charla(mensaje):
    texto = re.sub(r"\b(?:michi|porfa|por favor|un rato|un poco|tantito|ahora|conmigo|ya|pues)\b",
                   " ", mensaje)
    return " ".join(re.findall(r"[a-z0-9]+", texto)) in FRASES_PEDIR_CHARLA


def en_cooldown(tema):
    return time.time() - perfil["preguntados"].get(tema, 0) < COOLDOWN_TEMA


def registrar_recuerdo(clave, texto):
    perfil["recuerdos"][clave] = {"texto": texto, "ts": time.time(), "retomado": False}
    guardar_perfil()


def terminar_charla():
    charla["nodo"] = None
    charla_estado["ultimo_fin"] = charla_estado["contador"]


def hacer_pregunta(nodo_id, datos):
    charla.update(nodo=nodo_id, datos=datos, hora=time.time(), fallos=0)
    plantilla = random.choice(CHARLAS[nodo_id]["pregunta"])
    print(plantilla.format(texto=datos.get("texto", "")))


def avanzar_charla(siguiente, datos, cierre=None, contexto=None):
    """Pasa al siguiente nodo, o cierra la charla (con pregunta final opcional)."""
    if siguiente:
        hacer_pregunta(siguiente, datos)
        return
    terminar_charla()
    if cierre:
        print(random.choice(cierre))
    if contexto:
        recordar_pregunta(contexto)


def elegir_inicio(forzar=False):
    """Decide de qué hablar: primero retoma recuerdos, luego temas nuevos."""
    ahora = time.time()
    pendientes = [(k, r) for k, r in perfil["recuerdos"].items()
                  if k in SEGUIMIENTOS and not r.get("retomado")
                  and ahora - r.get("ts", 0) >= SEGUNDOS_ANTES_DE_RETOMAR]
    if pendientes:
        clave, recuerdo = random.choice(pendientes)
        recuerdo["retomado"] = True
        guardar_perfil()
        return SEGUIMIENTOS[clave], {"texto": recuerdo["texto"]}
    if not perfil["nombre"] and (forzar or not en_cooldown("nombre")):
        return "nombre", {"texto": ""}
    opciones = [(t, {"texto": ""}) for t in TEMAS_NUEVOS if forzar or not en_cooldown(t)]
    if perfil["gustos"] and (forzar or not en_cooldown("seg_gusto")):
        opciones.append(("seg_gusto", {"texto": random.choice(perfil["gustos"])}))
    return random.choice(opciones) if opciones else None


def iniciar_charla(forzar=False):
    elegido = elegir_inicio(forzar)
    if elegido is None:
        return False
    nodo_id, datos = elegido
    perfil["preguntados"][nodo_id] = time.time()
    guardar_perfil()
    hacer_pregunta(nodo_id, datos)
    return True


def responder_pide_charla(mensaje):
    if not pide_charla(mensaje):
        return False
    print(random.choice(["😸🐾 Michi: ¡Siii, platiquemos!",
                         "😻✨ Michi: ¡Me encanta platicar contigo!"]))
    iniciar_charla(forzar=True)
    return True


def sale_de_charla(original, mensaje):
    """True si el mensaje no es una respuesta a la charla (pregunta, despedida, comando)."""
    if "?" in original or "¿" in original:
        return True
    if mensaje.startswith(("aprende", "olvida", "borra")):
        return True
    if re.search(r"\bno michi\b|\bmichi no\b|\bmal michi\b", mensaje):
        return True
    if pide_charla(mensaje):
        return True
    return contiene_alguna(mensaje, SALIDAS_DE_CHARLA)


def continuar_charla(original, mensaje):
    """True si el mensaje era la respuesta a la charla en curso."""
    nodo_id = charla["nodo"]
    if not nodo_id:
        return False
    if time.time() - charla["hora"] > VIGENCIA_CHARLA:
        terminar_charla()
        return False
    nodo = CHARLAS[nodo_id]
    datos = charla["datos"]

    # "¿y tú?": Michi contesta lo suyo y sigue esperando la respuesta.
    if contiene_alguna(mensaje, ["y tu", "y tu que", "y a ti", "tu que", "y tu como"]):
        print(random.choice(nodo.get("yo", YO_POR_DEFECTO)))
        charla["hora"] = time.time()
        return True
    if sale_de_charla(original, mensaje):
        terminar_charla()
        return False

    # El dueño no quiere contar / no sabe: Michi lo respeta.
    if (mensaje in NO_QUIERE_CONTAR
            or (nodo["tipo"] == "libre" and clasificar_respuesta_corta(mensaje) in ("no", "duda"))):
        print("🐱💕 Michi: Está bien, no pasa nada. Aquí estaré cuando quieras contarme.")
        if nodo.get("cierre_siempre"):
            avanzar_charla(None, datos, nodo.get("cierre"), nodo.get("contexto"))
        else:
            terminar_charla()
        return True

    if nodo["tipo"] == "libre":
        guardar = nodo.get("guardar")
        if guardar == "nombre":
            m = re.search(r"\b(?:me llamo|mi nombre es|ll[aá]mame|soy)\s+(.+?)[\s.!]*$",
                          original, flags=re.IGNORECASE)
            nombre = limpiar_frase(m.group(1) if m else original)
            if not nombre or len(nombre.split()) > 3:
                charla["fallos"] += 1
                if charla["fallos"] >= 2:
                    terminar_charla()
                    return False
                print("🐱❓ Michi: Miau... dime solo tu nombre, de máximo 3 palabras.")
                return True
            perfil["nombre"] = " ".join(p[:1].upper() + p[1:] for p in nombre.split())
            guardar_perfil()
            datos["texto"] = perfil["nombre"]
        else:
            datos["texto"] = limpiar_respuesta_libre(original)
            if guardar == "gusto":
                if datos["texto"] not in perfil["gustos"]:
                    perfil["gustos"].append(datos["texto"])
                    del perfil["gustos"][:-30]
                    guardar_perfil()
            elif guardar:
                registrar_recuerdo(guardar, datos["texto"])
        print(random.choice(nodo["respuesta"]).format(texto=datos["texto"]))
        avanzar_charla(nodo.get("siguiente"), datos, nodo.get("cierre"), nodo.get("contexto"))
        return True

    # Nodos "emocion" y "si_no": se clasifica la respuesta y se sigue la rama.
    if nodo["tipo"] == "emocion":
        clave = clasificar_emocion(mensaje)
    else:
        clave = clasificar_si_no_flexible(mensaje)
    if clave not in nodo["ramas"]:
        clave = nodo.get("defecto")
    if clave is None:
        charla["fallos"] += 1
        if charla["fallos"] >= 2 or len(mensaje.split()) > 8:
            terminar_charla()
            return False
        print("🐱❓ Michi: Miau, ¿eso fue un sí o un no?")
        return True
    siguiente, respuestas, contexto = nodo["ramas"][clave]
    print(random.choice(respuestas).format(texto=datos.get("texto", "")))
    avanzar_charla(siguiente, datos, None, contexto)
    return True


def mostrar_recuerdos():
    """Lo que Michi recuerda del dueño (comando: '¿qué recuerdas de mí?')."""
    lineas = []
    if perfil["nombre"]:
        lineas.append(f"• Te llamas {perfil['nombre']}.")
    if perfil["gustos"]:
        lineas.append("• Te gusta: " + ", ".join(perfil["gustos"]) + ".")
    for clave, etiqueta in ETIQUETAS_RECUERDO.items():
        if clave in perfil["recuerdos"]:
            lineas.append(f"• {etiqueta}: «{perfil['recuerdos'][clave]['texto']}».")
    if not lineas:
        print("🐱❓ Michi: Todavía no me has contado mucho de ti. "
              "Di «platiquemos» y te hago preguntas.")
        return
    print("😸📖 Michi: Esto es lo que recuerdo de ti:\n" + "\n".join(lineas))


# CONVERSACIÓN POR REFLEJOS
def _conversar_reglas(mensaje):
    """
    Michi NO comprende lenguaje natural.
    Solamente:
    1. recibe el mensaje actual,
    2. busca palabras o frases,
    3. aplica una regla,
    4. responde inmediatamente.
    La única excepción es responder_ia(), que puede apoyarse en el
    último tema recordado (ver memoria_conversacion) para dar
    continuidad a preguntas de seguimiento sobre IA.
    """
    original = mensaje
    mensaje = normalizar_texto(mensaje)
    # APRENDIZAJE: comandos de enseñanza y respuesta a "¿qué significa?"
    if procesar_aprendizaje(original, mensaje):
        return
    # PERFIL DEL DUEÑO: nombre y gustos
    if procesar_perfil(original, mensaje):
        return
    # A partir de aquí se ignoran letras alargadas ("holaaaa" -> "hola").
    mensaje = suavizar_texto(mensaje)
    # FRASES ENSEÑADAS POR EL USUARIO (tienen prioridad sobre las reglas)
    for frase_aprendida, respuesta_aprendida in vocabulario["respuestas"].items():
        if contiene_alguna(mensaje, [frase_aprendida]):
            print(f"🐱💬 Michi: {respuesta_aprendida}")
            return
    # CHARLA EN CURSO: si Michi te hizo una pregunta de su charla, esto es la respuesta
    if continuar_charla(original, mensaje):
        return
    # "platiquemos", "hablemos"...: Michi inicia una charla
    if responder_pide_charla(mensaje):
        return
    # SÍ / NO / QUIZÁS (respuestas cortas, según lo último que Michi pidió)
    if responder_si_no(mensaje):
        return
    # PATRONES: lo que Michi ha notado de los hábitos del dueño
    if contiene_alguna(mensaje, [
        "patrones", "habitos", "que has notado", "como te cuido",
        "como te he cuidado", "que sabes de mi", "como soy como dueno"
    ]):
        mostrar_habitos()
        return
    # CONOCIMIENTOS DE INTELIGENCIA ARTIFICIAL
    respuesta_ia = responder_ia(mensaje)
    if respuesta_ia is not None:
        print(respuesta_ia)
        return
    # NEGACIONES DENTRO DE UNA FRASE ("no quiero jugar", "no tengo hambre")
    if responder_negacion_con_tema(original, mensaje):
        return
    # SALUDOS
    if coincide(mensaje, "saludo", ["hola", "holi", "buenos dias",
                                    "buenas tardes", "buenas noches"]):
        respuestas = [
            f"😸🐾 Michi: ¡Miauuuu! ¡Holaaaa, {amo()}!",
            f"😸☀️ Michi: ¡{saludo_horario()}, {amo()}!",
            "🐱❤️ Michi: ¡Hola! Qué bueno verte otra vez.",
            "😻✨ Michi: ¡Te estaba esperando!",
            "😸🎾 Michi: ¡Holaaa! ¿Jugamos?"
        ]
        elegida = random.choice(respuestas)
        print(elegida)
        if "¿Jugamos?" in elegida:
            recordar_pregunta("jugar")
    # ¿CÓMO ESTÁS?
    elif coincide(mensaje, "estado", [
        "como estas","como te sientes","estas bien","todo bien", "te sientes bien",
        "que tal", "te encuentras bien"
    ]):
        if mascota["salud"] <= 30:
            print("🤒😿 Michi: No me siento muy bien, amo... :(((")
        elif mascota["felicidad"] <= 30:
            print("😭💔 Michi: Estoy muuuy triste... te extrañoooo :(((((")
        elif mascota["comida"] <= 30:
            print("🥺🍗 Michi: Estoy bien... pero mi pancita tiene mucha hambre.")
        elif mascota["energia"] <= 20:
            print("😴💤 Michi: Estoy cansadísimo... zzz...")
        else:
            print("😸❤️✨ Michi: ¡Estoy muy bien! ¡Más ahora que estás aquí!")
    # JUGAR
    elif coincide(mensaje, "jugar", [
        "jugar","jugamos","juguemos","juego","pelota","convivir", "pasar tiempo"
    ]):
        if mascota["energia"] >= 60:
            respuestas = [
                "🤩🎾 Michi: ¡SIIII, amo! ¡Quiero jugar!",
                "😸🐾 Michi: ¡Sí, sí, sí! ¡Vamos a jugar!",
                "😻⚡ Michi: ¡Me encantaría! ¡Tengo mucha energía!",
                "😻🎾 Michi: ¡Me encanta pasar tiempo contigo!"
            ]
        elif mascota["energia"] >= 20:
            respuestas = [
                "😸🎾 Michi: Sí, amo, me gustaría jugar un ratito.",
                "🐱🐾 Michi: ¡Claro! Pero no demasiado, ¿sí?",
                "🥰🎾 Michi: Contigo siempre quiero jugar.",
                "🐱🐾 Michi: Si quiero, pero estoy un poco cansado, amo"
            ]
        else:
            respuestas = [
                "😴💤 Michi: Quiero jugar contigo... pero estoy muuuuy cansado.",
                "🥱🐱 Michi: ¿Podemos jugar después de una siestita?",
                "😿💤 Michi: Mi cuerpo dice jugar... pero mis ojitos dicen zzz...",
                "😴💤 Michi: Estoy muy cansado amo, mejor cuando descanse"
            ]
        print(random.choice(respuestas))
    # COMIDA / HAMBRE
    elif coincide(mensaje, "comida", [
        "hambre","comida","comer","alimento","croquetas","pollo", "hambriento"
    ]):
        if mascota["comida"] <= 20:
            print("😭🍗 Michi: ¡SÍÍÍ! ¡Tengo muchísima hambreeeee! :(((")
        elif mascota["comida"] <= 50:
            print("🥺🍖 Michi: Un poquito de comida no estaría nada mal...")
        else:
            print("😸🐾 Michi: Estoy bien por ahora, mi pancita está contenta.")
    # CARIÑO
    elif coincide(mensaje, "carino", [
        "carino","mimos","abrazo","acariciar","acaricio","amor", "afecto"
    ]):
        respuestas = [
            "😻❤️ Michi: ¡Siiii! ¡Quiero muchos mimos!",
            "🥰🐾 Michi: Ven, amo... aquí cerquita.",
            "😸💕 Michi: ¡Acaríciame! ¡Miauuu!"
        ]
        print(random.choice(respuestas))
    # TE QUIERO
    elif coincide(mensaje, "te_quiero", [
        "te quiero","te amo","te adoro"
    ]):
        respuestas = [
            f"🥰❤️ Michi: ¡Yo también te quiero muchísimo, {amo()}!",
            "😻💕 Michi: ¡Miauuuu! ¡Me haces muy feliz!",
            "🐱❤️✨ Michi: Mi corazoncito gatuno está feliz."
        ]
        print(random.choice(respuestas))
    # TRISTE
    elif coincide(mensaje, "triste", [
        "triste","tristeza","llorar","llorando"
    ]):
        if mascota["felicidad"] <= 40:
            print("😭😿💔 Michi: Sí... estoy muuuy triste. Quédate conmigo :(((((")
        else:
            print("😸❤️ Michi: Ahora no estoy triste. Estoy feliz de estar contigo.")
    # DORMIR / DESCANSAR
    elif coincide(mensaje, "dormir", [
        "dormir","duerme","descansar","sueno","siesta", "agotado", "débil", "exhausto"
    ]):
        if mascota["energia"] <= 40:
            print("😴💤 Michi: Siii... una siestita suena perfecta... zzz...")
        else:
            print("😸⚡ Michi: Todavía tengo energía, dueño-amo. ¡No tengo sueño!")
    # NO / REGAÑO
    elif coincide(mensaje, "regano", [
        "no michi","michi no","portate bien","mal michi", "estuvo mal eso Michi", "Obedeceme"
    ]):
        respuestas = [
            "🥺🐱 Michi: Perdóooon... no lo vuelvo a hacer :(",
            "😿🐾 Michi: Miau... intentaré portarme mejor.",
            "🥺💔 Michi: No te enojes conmigo, dueño-amo..."
        ]
        print(random.choice(respuestas))
    # FELICITACIONES
    elif coincide(mensaje, "felicitacion", [
        "bien hecho","muy bien","buen michi","eres bueno", "estoy orgulloso",
        "me haces muy feliz", "el mejor de todos"
    ]):
        respuestas = [
            "😻✨ Michi: ¿De verdad? ¡Miauuuu! ❤️",
            "😸🐾 Michi: ¡Soy un buen michi!",
            "🥰🏆 Michi: ¡Gracias, amo! Me esforcé mucho."
        ]
        print(random.choice(respuestas))
    # GRACIAS
    elif coincide(mensaje, "gracias", ["gracias"]):
        respuestas = [
            f"😸❤️ Michi: ¡De nada, {amo()}!",
            "🐱🐾 Michi: ¡Miauuu! Para eso estoy.",
            "🥰 Michi: ¡Siempre!"
        ]
        print(random.choice(respuestas))
    # DESPEDIDA
    elif coincide(mensaje, "despedida", [
        "adios","bye","nos vemos","hasta luego", "te veo luego", "me tengo que ir"
    ]):
        respuestas = [
            "😿🐾 Michi: ¿Ya te vas? Te voy a extrañaaaar :(((",
            "🥺❤️ Michi: Está bien... pero vuelve pronto, amo.",
            "🐱👋 Michi: ¡Miauuu! ¡Nos vemos pronto!"
        ]
        print(random.choice(respuestas))
    # NO ENTENDIÓ
    else:
        # Si es una frase corta, Michi pregunta para aprenderla.
        if 0 < len(mensaje.split()) <= 3:
            pendiente_aprender["frase"] = mensaje
            print(f"🐱❓ Michi: Miau... no conozco «{original.strip()}». ¿Me enseñas qué significa?")
            print("   Respóndeme con una categoría (" + listar_categorias() + ") o escribe 'no'.")
            return
        respuestas = [
            "🐱❓ Michi: Miau... no entendí muy bien.",
            "🤔🐾 Michi: ¿Me lo dices de otra manera?",
            "🥺🐱 Michi: Todavía no conozco esas palabras...",
            "😸❤️ Michi: No entendí, pero sigo aquí contigo.",
            "😸🐾 Michi: Mis creadores aun no me enseñan esas palabras. Lo siento"
        ]
        print(random.choice(respuestas))
# Probabilidad de que Michi, tras responder, mencione por su cuenta una
# necesidad importante (hambre, cansancio, falta de cariño...).
PROB_COMENTARIO_ESTADO = 0.35


def conversar(mensaje):
    """
    Punto de entrada de la conversación. Aplica las reglas y, a veces,
    Michi añade por iniciativa propia lo que más necesita en ese momento
    (su meta más urgente), para que la charla se sienta menos mecánica.
    """
    _conversar_reglas(mensaje)
    if not mascota["viva"] or pendiente_aprender["frase"] is not None:
        return
    if normalizar_texto(mensaje).startswith(("aprende", "olvida", "borra")):
        return
    charla_estado["contador"] += 1
    if random.random() < PROB_COMENTARIO_ESTADO:
        metas = definir_metas(percibir())
        if metas and metas[0][1] >= 5:      # solo necesidades importantes
            actuar(metas[0][2])
            return
    # Si no hay nada urgente, a veces Michi inicia una charla con hilo.
    # Una pregunta que el dueño ignoró durante varios mensajes ya no cuenta como abierta.
    pregunta_abierta = (pregunta_vigente() is not None and
                        charla_estado["contador"] - contexto_pregunta.get("n", 0) < MENSAJES_ENTRE_CHARLAS)
    if (charla["nodo"] is None and not pregunta_abierta
            and charla_estado["contador"] - charla_estado["ultimo_fin"] >= MENSAJES_ENTRE_CHARLAS
            and random.random() < PROB_INICIAR_CHARLA):
        contexto_pregunta["tema"] = None
        iniciar_charla()


# ESTADÍSTICAS VISUALES DE MICHI
def mostrar_estadisticas_de_michi():
    def barra(valor):
        llenos = valor // 10
        vacios = 10 - llenos
        return "█" * llenos + "░" * vacios
    print("\n📊 ESTADÍSTICAS DE MICHI")
    print(f"❤️ Salud:      [{barra(mascota['salud'])}] {mascota['salud']}/100")
    print(f"😊 Felicidad:  [{barra(mascota['felicidad'])}] {mascota['felicidad']}/100")
    print(f"🍗 Comida:     [{barra(mascota['comida'])}] {mascota['comida']}/100")
    print(f"⚡ Energía:    [{barra(mascota['energia'])}] {mascota['energia']}/100")
# MOSTRAR ESTADO
def mostrar_estado():
    percepcion = percibir()
    metas = definir_metas(percepcion)
    if metas:
        _, _, decision = metas[0]
        resumen_metas = ", ".join(nombre for nombre, _, _ in metas)
    else:
        decision = "TRANQUILO"
        resumen_metas = "ninguna, Michi está conforme"
    print("\n" + "=" * 46)
    print("🐱✨ ESTADO DE MICHI ✨🐱")
    print("=" * 46)
    print(f"🐾 Nombre: {mascota['nombre']}")
    print(f"🎭 Expresión: {obtener_expresion()}")
    print(f"❤️ Salud: {mascota['salud']}/100")
    print(f"😊 Felicidad: {mascota['felicidad']}/100")
    print(f"🍗 Comida: {mascota['comida']}/100")
    print(f"⚡ Energía: {mascota['energia']}/100")
    print(f"🕐 Horas sin cuidado: {mascota['horas_sin_cuidado']}")
    print(f"💕 Horas sin cariño: {mascota['horas_sin_carino']}")
    print(f"🎯 Metas pendientes: {resumen_metas}")
    print(f"🤖 Acción prioritaria: {decision}")
    print("=" * 46)
# CICLO AUTOMÁTICO DEL AGENTE
def ciclo_agente():
    while mascota["viva"]:
        time.sleep(SEGUNDOS_POR_HORA)
        pasar_una_hora()
        if mascota["viva"]:
            percepcion = percibir()
            decision = seleccionar_accion_por_metas(percepcion)
            print("\n\n⏰🐾 Ha pasado una hora para Michi...")
            actuar(decision)
            anticipar_visita()
# PROGRAMA DE CONSOLA (solo corre si se ejecuta este archivo directamente)
#
# Se protege con "if __name__ == '__main__':" para que este archivo se
# pueda IMPORTAR de forma segura desde otros programas (por ejemplo,
# interfaz_grafica.py) sin que se dispare automáticamente el hilo del
# agente ni el menú de consola.
def iniciar_hilo_agente():
    """Crea y arranca el hilo del ciclo automático del agente."""
    hilo = threading.Thread(target=ciclo_agente, daemon=True)
    hilo.start()
    return hilo
def ejecutar_menu_consola():
    """Corre el menú interactivo por consola (modo texto original)."""
    print("\n🐱✨ ¡Bienvenido a tu mascota virtual Michi! ✨🐱")
    print("Puedes interactuar con él usando números o simplemente escribirle.")
    print("Ejemplos:")
    print("  Tú: ¿Quieres jugar?")
    print("  Tú: Michi, ¿tienes hambre?")
    print("  Tú: Te quiero")
    print("  Tú: ¿Cómo estás?")
    print("  Tú: aprende chido significa felicitacion   (¡enséñale palabras!)")
    print("  Tú: ¿qué patrones has notado en mí?")
    print("\nEscribe 'menu' cuando quieras ver las opciones.\n")
    while mascota["viva"]:
        print("\n¿Qué quieres hacer?")
        print("1. 👀 Ver estado")
        print("2. 🍗 Alimentar")
        print("3. ❤️ Dar cariño")
        print("4. 🎾 Jugar")
        print("5. 😴 Mandar a dormir a Michi")
        print("6. 🗣️ Hablar con Michi")
        print("7. 🚪 Salir")
        print("💬 O escribe directamente cualquier frase.")
        opcion = input("\nTú: ").strip()
        opcion_normalizada = normalizar_texto(opcion)
        if opcion_normalizada == "1":
            mostrar_estado()
        elif opcion_normalizada == "2":
            alimentar()
        elif opcion_normalizada == "3":
            dar_carino()
        elif opcion_normalizada == "4":
            jugar()
        elif opcion_normalizada == "5":
            descansar()
        elif opcion_normalizada == "6":
            mensaje = input("🗣️ Tú: ")
            conversar(mensaje)
        elif opcion_normalizada == "7":
            print("\n🐱👋 Michi: ¡Miauu! Te voy a extrañar, dueño-amo ❤️")
            break
        elif opcion_normalizada == "menu":
            continue
        else:
            # Cualquier texto que no sea una opción se toma como conversación.
            conversar(opcion)
    print("\n🐾 Programa terminado.")
if __name__ == "__main__":
    iniciar_hilo_agente()
    ejecutar_menu_consola()