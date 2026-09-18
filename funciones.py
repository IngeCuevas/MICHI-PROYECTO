import time
import threading
import random
import unicodedata
import re
from banco_palabras import CONOCIMIENTOS_IA
# CONFIGURACIÓN
# Para pruebas:
# 60 segundos reales = 1 hora para Michi
SEGUNDOS_POR_HORA = 60
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
    No recuerda conversaciones anteriores.
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
# DECISIÓN DEL AGENTE
def decidir(percepcion):
    # REGLAS CONDICIÓN -> ACCIÓN
    if percepcion["salud"] <= 20:
        return "PEDIR_CUIDADO"
    elif percepcion["comida"] <= 10:
        return "COMIDA_URGENTE"
    elif percepcion["comida"] <= 30:
        return "PEDIR_COMIDA"
    elif percepcion["energia"] <= 20:
        return "PEDIR_DESCANSO"
    elif percepcion["horas_sin_carino"] >= 4:
        return "PEDIR_CARINO"
    elif percepcion["horas_sin_cuidado"] >= 6:
        return "PEDIR_ATENCION"
    elif percepcion["felicidad"] <= 30:
        return "ESTAR_TRISTE"
    elif percepcion["energia"] >= 80 and percepcion["felicidad"] >= 70:
        return "QUERER_JUGAR"
    else:
        return "TRANQUILO"
# ACCIONES DEL AGENTE
def actuar(accion):
    mensajes = {
        "PEDIR CUIDADO": [
            "🤒😿 Michi: Dueño-amo... no me siento muy bien :(( ¿me cuidas?",
            "🥺💔 Michi: Necesito un poquito de atención... por favooor.",
            "🐱🤒 Michi: Creo que necesito que me cuides... miauuu :("
        ],
        "COMIDA URGENTE": [
            "😿🍗 Michi: ¡Dueño-amooo! ¡Tengo muchísima hambre! :(((",
            "🥺🍖 Michi: ¡Miauuuu! Mi pancita está vacía...",
            "😭🍗 Michi: ¡Comida, comida, comida! ¡Por favooor!"
        ],
        "PEDIR COMIDA": [
            "😋🍗 Michi: Dueño-amo... creo que ya tengo un poquito de hambre.",
            "🐱🍖 Michi: ¿Habrá algo rico para este michito?",
            "🥺🍗 Michi: ¿Me das un poquito de comidita?"
        ],
        "PEDIR DESCANSO": [
            "😴💤 Michi: Tengo muchísimo sueñito...",
            "🥱🐱 Michi: Dueño-amo... creo que necesito descansar.",
            "😴🛏️ Michi: Mis ojitos ya se están cerrando... zzz..."
        ],
        "PEDIR CARINO": [
            "🥺❤️ Michi: Dueño-amo... ¿me das un poquito de cariño?",
            "😻💕 Michi: Quierooo mimosssss.",
            "😿🐾 Michi: Hace mucho que no recibo cariño... te extrañoooo :((("
        ],
        "PEDIR ATENCION": [
            "😾💢 Michi: ¡Oyeee! ¿Ya te olvidaste de mí?",
            "🥺😿 Michi: Hace mucho que no me haces caso...",
            "🐱💔 Michi: Dueño-amo... ¿todavía estás ahí? :("
        ],
        "ESTAR TRISTE": [
            "😭😿 Michi: Estoy muuuy triste... te extrañoooo :(((((",
            "🥺💔 Michi: Quiero pasar tiempo contigo...",
            "😿🐾 Michi: Hoy mi corazoncito gatuno está triste :((("
        ],
        "QUERER JUGAR": [
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
                "por que eres reflejo simple", "michi es reflejo simple", "eres un agente"
            ]
        ),
        # LOS CUATRO ENFOQUES
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
                "agente basado en metas","basado en metas","agente de metas"
            ]
        ),
        (
            "basado_utilidad",
            [
                "agente basado en utilidad","basado en utilidad","agente de utilidad"
            ]
        ),
        (
            "agente_aprende",
            [
                "agente que aprende","agentes que aprenden","agente de aprendizaje"
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
# RESPONDER PREGUNTAS DE IA
def responder_ia(mensaje):
    tema = detectar_tema_ia(mensaje)
    # Si no detectó ningún tema de IA
    if tema is None:
        return None
    intencion = detectar_intencion_ia(mensaje)
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
# CONVERSACIÓN POR REFLEJOS
def conversar(mensaje):
    """
    Michi NO comprende lenguaje natural.
    Solamente:
    1. recibe el mensaje actual,
    2. busca palabras o frases,
    3. aplica una regla,
    4. responde inmediatamente.
    Por eso sigue funcionando como agente de reflejo simple.
    """
    mensaje = normalizar_texto(mensaje)
    # CONOCIMIENTOS DE INTELIGENCIA ARTIFICIAL
    respuesta_ia = responder_ia(mensaje)
    if respuesta_ia is not None:
        print(respuesta_ia)
        return
    # SALUDOS
    if any(palabra in mensaje for palabra in ["hola", "holi", "buenos dias",
                                               "buenas tardes", "buenas noches"]):
        respuestas = [
            "😸🐾 Michi: ¡Miauuuu! ¡Holaaaa, dueño-amo!",
            "🐱❤️ Michi: ¡Hola! Qué bueno verte otra vez.",
            "😻✨ Michi: ¡Te estaba esperando!",
            "😸🎾 Michi: ¡Holaaa! ¿Jugamos?"
        ]
        print(random.choice(respuestas))
    # ¿CÓMO ESTÁS?
    elif any(frase in mensaje for frase in [
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
    elif any(palabra in mensaje for palabra in [
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
    elif any(palabra in mensaje for palabra in [
        "hambre","comida","comer","alimento","croquetas","pollo", "hambriento"
    ]):
        if mascota["comida"] <= 20:
            print("😭🍗 Michi: ¡SÍÍÍ! ¡Tengo muchísima hambreeeee! :(((")
        elif mascota["comida"] <= 50:
            print("🥺🍖 Michi: Un poquito de comida no estaría nada mal...")
        else:
            print("😸🐾 Michi: Estoy bien por ahora, mi pancita está contenta.")
    # CARIÑO
    elif any(palabra in mensaje for palabra in [
        "carino","mimos","abrazo","acariciar","acaricio","amor", "afecto"
    ]):
        respuestas = [
            "😻❤️ Michi: ¡Siiii! ¡Quiero muchos mimos!",
            "🥰🐾 Michi: Ven, amo... aquí cerquita.",
            "😸💕 Michi: ¡Acaríciame! ¡Miauuu!"
        ]
        print(random.choice(respuestas))
    # TE QUIERO
    elif any(frase in mensaje for frase in [
        "te quiero","te amo","te adoro"
    ]):
        respuestas = [
            "🥰❤️ Michi: ¡Yo también te quiero muchísimo, dueño-amo!",
            "😻💕 Michi: ¡Miauuuu! ¡Me haces muy feliz!",
            "🐱❤️✨ Michi: Mi corazoncito gatuno está feliz."
        ]
        print(random.choice(respuestas))
    # TRISTE
    elif any(palabra in mensaje for palabra in [
        "triste","tristeza","llorar","llorando"
    ]):
        if mascota["felicidad"] <= 40:
            print("😭😿💔 Michi: Sí... estoy muuuy triste. Quédate conmigo :(((((")
        else:
            print("😸❤️ Michi: Ahora no estoy triste. Estoy feliz de estar contigo.")
    # DORMIR / DESCANSAR
    elif any(palabra in mensaje for palabra in [
        "dormir","duerme","descansar","sueno","siesta", "agotado", "débil", "exhausto"
    ]):
        if mascota["energia"] <= 40:
            print("😴💤 Michi: Siii... una siestita suena perfecta... zzz...")
        else:
            print("😸⚡ Michi: Todavía tengo energía, dueño-amo. ¡No tengo sueño!")
    # NO / REGAÑO
    elif any(frase in mensaje for frase in [
        "no michi","michi no","portate bien","mal michi", "estuvo mal eso Michi", "Obedeceme"
    ]):
        respuestas = [
            "🥺🐱 Michi: Perdóooon... no lo vuelvo a hacer :(",
            "😿🐾 Michi: Miau... intentaré portarme mejor.",
            "🥺💔 Michi: No te enojes conmigo, dueño-amo..."
        ]
        print(random.choice(respuestas))
    # FELICITACIONES
    elif any(frase in mensaje for frase in [
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
    elif "gracias" in mensaje:
        respuestas = [
            "😸❤️ Michi: ¡De nada, amo!",
            "🐱🐾 Michi: ¡Miauuu! Para eso estoy.",
            "🥰 Michi: ¡Siempre!"
        ]
        print(random.choice(respuestas))
    # DESPEDIDA
    elif any(palabra in mensaje for palabra in [
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
    decision = decidir(percepcion)
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
    print(f"🤖 Reflejo actual: {decision}")
    print("=" * 46)
# CICLO AUTOMÁTICO DEL AGENTE
def ciclo_agente():
    while mascota["viva"]:
        time.sleep(SEGUNDOS_POR_HORA)
        pasar_una_hora()
        if mascota["viva"]:
            percepcion = percibir()
            decision = decidir(percepcion)
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