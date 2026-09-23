import time
import threading
import random
import unicodedata
import re
import os
import json
from collections import deque
from banco_palabras import CONOCIMIENTOS_IA
# CONFIGURACIÓN
# Para pruebas:
# 60 segundos reales = 1 hora para Michi
SEGUNDOS_POR_HORA = 3600
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
# ALIMENTAR
def alimentar():
    if not mascota["viva"]:
        return
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
        patron = r"\b" + re.escape(normalizar_texto(opcion)) + r"\b"
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
        if normalizar_texto(palabra) in mensaje:
            return True
    aprendidas = vocabulario["palabras"].get(categoria, [])
    return bool(aprendidas) and contiene_alguna(mensaje, aprendidas)


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

# CONVERSACIÓN POR REFLEJOS
def conversar(mensaje):
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
    # FRASES ENSEÑADAS POR EL USUARIO (tienen prioridad sobre las reglas)
    for frase_aprendida, respuesta_aprendida in vocabulario["respuestas"].items():
        if contiene_alguna(mensaje, [frase_aprendida]):
            print(f"🐱💬 Michi: {respuesta_aprendida}")
            return
    # CONOCIMIENTOS DE INTELIGENCIA ARTIFICIAL
    respuesta_ia = responder_ia(mensaje)
    if respuesta_ia is not None:
        print(respuesta_ia)
        return
    # SALUDOS
    if coincide(mensaje, "saludo", ["hola", "holi", "buenos dias",
                                    "buenas tardes", "buenas noches"]):
        respuestas = [
            "😸🐾 Michi: ¡Miauuuu! ¡Holaaaa, dueño-amo!",
            "🐱❤️ Michi: ¡Hola! Qué bueno verte otra vez.",
            "😻✨ Michi: ¡Te estaba esperando!",
            "😸🎾 Michi: ¡Holaaa! ¿Jugamos?"
        ]
        print(random.choice(respuestas))
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
            "🥰❤️ Michi: ¡Yo también te quiero muchísimo, dueño-amo!",
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
            "😸❤️ Michi: ¡De nada, amo!",
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