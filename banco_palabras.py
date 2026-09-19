"""
BANCO DE PALABRAS / BASE DE CONOCIMIENTOS DE MICHI
=====================================================

IMPORTANTE:
Toda esta información proviene de las presentaciones
de Inteligencia Artificial proporcionadas para el proyecto
("Introducción a la Inteligencia Artificial" y
"Agentes Inteligentes y Ambientes").

Michi NO aprende esta información.
Simplemente consulta respuestas preestablecidas.

Este archivo contiene ÚNICAMENTE datos (el diccionario
CONOCIMIENTOS_IA). La lógica del programa vive en funciones.py,
que importa este banco de palabras.
"""

CONOCIMIENTOS_IA = {
    # =================================================================
    # INTELIGENCIA ARTIFICIAL - CONCEPTOS GENERALES
    # =================================================================
    "inteligencia_artificial": {
        "definicion": [
            "🤖📚 Michi: No solo hay una definición de Inteligencia Artificial. La IA es el estudio de agentes que perciben su entorno y realizan acciones para alcanzar objetivos.",
            "🐱🧠 Michi: La Inteligencia Artificial puede estudiarse desde distintas perspectivas. Una de las principales es construir agentes capaces de percibir su entorno y actuar para alcanzar objetivos.",
            "🐱🧠 Michi: Una definición más simple y concreta de la IA es que es un área de las ciencias computacionales que trata de emular las capacidades propias del ser humano.",
            "🤖📚 Michi: De acuerdo con el padre fundador de la IA, John McCarthy; La IA es la ciencia y la ingeniería de hacer máquinas inteligentes, especialmente programas informáticos inteligentes.",
            "🐱📚 Michi: También se dice que la IA es una rama de las ciencias computacionales que estudia modelos de cómputo capaces de realizar actividades propias de los seres humanos, basándose en el razonamiento y la conducta."
        ],
        "funcion": [
            "😸🧠 Michi: La IA busca construir sistemas capaces de percibir, razonar, aprender y actuar para alcanzar objetivos.",
            "🤖📚 Michi: La IA busca interactuar con nosotros para potenciar nuestras habilidades humanas. No nos va a reemplazar, vino a potenciarnos."
        ]
    },
    # FACETAS DEL COMPORTAMIENTO INTELIGENTE
    "facetas": {
        "definicion": [
            "🐱🧠 Michi: Las capacidades fundamentales del comportamiento inteligente son percibir, razonar, aprender y actuar.",
            "🤖📚 Michi: Existen 4 facetas de comportamiento inteligente, las cuales son percibir, razonar, aprender y actuar."
        ],
        "lista": [
            "😸📚 Michi: Las cuatro capacidades fundamentales son:\n"
            "1. 👁️ Percibir: Obtener y analizar el entorno por medio de los sentidos.\n"
            "2. 🧠 Razonar: Procesar la información para tomar decisiones.\n"
            "3. 📈 Aprender: Mejorar a partir de la experiencia y los datos.\n"
            "4. 🤖 Actuar: Ejecutar acciones para alcanzar objetivos."
        ]
    },
    # CUATRO ENFOQUES DE RUSSELL Y NORVIG (pensar/actuar humano/racional)
    "cuatro_enfoques": {
        "definicion": [
            "🐱📚 Michi: Russell y Norvig organizan la Inteligencia Artificial "
            "en cuatro enfoques principales."
        ],
        "lista": [
            "😸🧠 Michi: Los cuatro enfoques de la IA son:\n"
            "1. 🧠 Pensar como humanos.\n"
            "2. 👤 Actuar como humanos.\n"
            "3. ♟️ Pensar racionalmente.\n"
            "4. 🎯 Actuar racionalmente."
        ]
    },
    "pensar_como_humanos": {
        "definicion": [
            "🧠🐱 Michi: Pensar como humanos busca modelar los procesos cognitivos "
            "del ser humano. La idea es construir sistemas que reproduzcan en una "
            "máquina procesos mentales humanos."
        ],
        "ejemplo": [
            "🐱💡 Michi: Algunos ejemplos son los sistemas expertos basados en reglas, "
            "los modelos de memoria y razonamiento humano y los simuladores cognitivos."
        ]
    },
    "actuar_como_humanos": {
        "definicion": [
            "👤🤖 Michi: Actuar como humanos busca construir máquinas que se "
            "comporten como lo haría una persona. Lo importante es cómo se "
            "comporta la máquina."
        ],
        "ejemplo": [
            "😸💡 Michi: Ejemplos de actuar como humanos son la Prueba de Turing, "
            "los chatbots conversacionales y el reconocimiento de voz y gestos."
        ]
    },
    "pensar_racionalmente": {
        "definicion": [
            "♟️🧠 Michi: Pensar racionalmente consiste en utilizar la lógica para "
            "inferir conclusiones correctas a partir de la información disponible."
        ],
        "ejemplo": [
            "🐱💡 Michi: Ejemplos de pensar racionalmente son los sistemas basados "
            "en lógica formal, la resolución automática de teoremas y los sistemas "
            "de planificación lógica."
        ]
    },
    "actuar_racionalmente": {
        "definicion": [
            "🎯🤖 Michi: Actuar racionalmente significa elegir la mejor acción "
            "posible para alcanzar un objetivo utilizando la información disponible."
        ],
        "ejemplo": [
            "😸💡 Michi: Algunos ejemplos son los vehículos autónomos, los sistemas "
            "de recomendación y los agentes que juegan ajedrez o Go."
        ]
    },
    # =================================================================
    # NUEVO: EVOLUCIÓN / HISTORIA DE LA IA
    # =================================================================
    "evolucion_ia": {
        "definicion": [
            "📜🐱 Michi: La IA ha tenido varios hitos importantes desde que se acuñó el término. No nació de un día para otro, fue evolucionando por décadas."
        ],
        "lista": [
            "🐱📚 Michi: Algunos hitos importantes en la historia de la IA:\n"
            "1. 1956: Se acuña el término 'inteligencia artificial' en la Conferencia de Dartmouth.\n"
            "2. 1969: Se desarrolla MYCIN, el primer sistema experto, capaz de diagnosticar infecciones bacterianas.\n"
            "3. 1980: Se desarrollan las redes neuronales artificiales, que permiten a las máquinas aprender de los datos.\n"
            "4. 2012: AlexNet gana el ImageNet Challenge, demostrando la eficacia de las redes neuronales profundas.\n"
            "5. 2020: Aparecen modelos de lenguaje como GPT-3, capaces de generar texto casi indistinguible del humano."
        ]
    },
    # NUEVO: ENFOQUES DE CONSTRUCCIÓN (simbólica / conectivista / evolutiva)
    "enfoques_construccion_ia": {
        "definicion": [
            "🔍🐱 Michi: Además de los cuatro enfoques de Russell y Norvig, también existen distintos enfoques según cómo se construye la IA por dentro."
        ],
        "lista": [
            "😸🧠 Michi: Los principales enfoques de construcción de la IA son:\n"
            "1. 🔣 IA Simbólica: Basada en la manipulación de símbolos y reglas lógicas.\n"
            "2. 🧬 IA Conectivista: Usa redes neuronales artificiales que emulan la estructura del cerebro humano.\n"
            "3. 🧪 IA Basada en Evolución: Emplea algoritmos genéticos y técnicas inspiradas en procesos evolutivos naturales."
        ]
    },
    # NUEVO: MÉTODOS DE APRENDIZAJE (visión general)
    "metodos_aprendizaje": {
        "definicion": [
            "📚🐱 Michi: Existen distintos métodos con los que una IA puede aprender de los datos."
        ],
        "lista": [
            "😺📈 Michi: Los principales métodos de aprendizaje en IA son:\n"
            "1. 🏷️ Aprendizaje Supervisado: el sistema aprende a partir de datos etiquetados.\n"
            "2. 🔎 Aprendizaje No Supervisado: busca patrones en datos que no están etiquetados.\n"
            "3. 🎮 Aprendizaje por Refuerzo: el agente aprende interactuando con el entorno y recibiendo recompensas o castigos."
        ]
    },
    "aprendizaje_supervisado": {
        "definicion": [
            "🏷️🐱 Michi: El aprendizaje supervisado es cuando el sistema aprende a partir de datos que ya vienen etiquetados, es decir, con la respuesta correcta incluida."
        ]
    },
    "aprendizaje_no_supervisado": {
        "definicion": [
            "🔎🐱 Michi: El aprendizaje no supervisado busca encontrar patrones y estructuras en datos que NO están etiquetados, sin que nadie le diga cuál es la respuesta correcta."
        ]
    },
    "aprendizaje_refuerzo": {
        "definicion": [
            "🎮🐱 Michi: El aprendizaje por refuerzo es cuando el agente aprende interactuando con su entorno, recibiendo recompensas cuando lo hace bien y castigos cuando no."
        ],
        "ejemplo": [
            "😸💡 Michi: Un ejemplo sería una IA que juega videojuegos: prueba movimientos, y aprende a repetir los que le dan puntos y a evitar los que la hacen perder."
        ]
    },
    # NUEVO: APLICACIONES ACTUALES DE LA IA
    "aplicaciones_ia": {
        "definicion": [
            "🌐🐱 Michi: La IA ya está presente en muchísimas áreas de nuestra vida diaria, no solo en laboratorios de investigación."
        ],
        "lista": [
            "🐱🌍 Michi: Algunas aplicaciones actuales de la IA son:\n"
            "1. 🗣️ Asistentes Virtuales: Siri, Alexa, Google Assistant.\n"
            "2. 🚗 Vehículos Autónomos: coches que se conducen solos usando IA para navegar y decidir.\n"
            "3. 🏥 Diagnóstico Médico: sistemas que analizan imágenes médicas y datos clínicos para detectar enfermedades."
        ],
        "ejemplo": [
            "😻💡 Michi: Tesla Autopilot es un buen ejemplo: ayuda a reducir accidentes por error humano y optimiza rutas para gastar menos energía y tiempo."
        ]
    },
    # NUEVO: IA GENERATIVA
    "ia_generativa": {
        "definicion": [
            "🎨🐱 Michi: La IA Generativa es la que puede crear contenido nuevo, como imágenes, texto o música, en vez de solo analizar datos existentes."
        ],
        "ejemplo": [
            "🖼️💬 Michi: Ejemplos de IA generativa son DALL·E (crea imágenes a partir de texto) y ChatGPT o Gemini (generan texto y conversan). También se usan para ayudar a estudiantes con redacción, traducción y creación de contenido para marketing."
        ]
    },
    # NUEVO: SUBCAMPOS DE LA IA
    "subcampos_ia": {
        "definicion": [
            "🔬🐱 Michi: La Inteligencia Artificial se divide en varios subcampos, cada uno enfocado en un tipo de problema distinto."
        ],
        "lista": [
            "🐱🔬 Michi: Algunos subcampos importantes de la IA son:\n"
            "1. 👁️ Visión por Computadora: interpretación y procesamiento de imágenes del mundo real.\n"
            "2. 💬 Procesamiento del Lenguaje Natural (PLN): interacción entre computadoras y lenguaje humano.\n"
            "3. 🦾 Robótica: integración de la IA en máquinas que realizan tareas físicas.\n"
            "4. 🧑‍💼 Sistemas Expertos: emulan la toma de decisiones de un experto humano.\n"
            "5. 📈 Aprendizaje Automático (Machine Learning): algoritmos que aprenden de los datos y mejoran con el tiempo."
        ]
    },
    "sistemas_expertos": {
        "definicion": [
            "🧑‍💼🐱 Michi: Un sistema experto es un programa diseñado para emular la toma de decisiones de un experto humano en un dominio específico, como el diagnóstico médico."
        ]
    },
    "aprendizaje_automatico": {
        "definicion": [
            "📈🐱 Michi: El aprendizaje automático, o Machine Learning, es el desarrollo de algoritmos que permiten a las máquinas aprender de los datos y mejorar su desempeño con el tiempo, sin ser programadas paso a paso para cada tarea."
        ]
    },
    # NUEVO: RELACIONES DE LA IA CON OTRAS DISCIPLINAS
    "relaciones_ia_disciplinas": {
        "definicion": [
            "🔗🐱 Michi: La IA no se desarrolla sola: se relaciona con muchas otras disciplinas que le aportan teorías, modelos y herramientas."
        ],
        "lista": [
            "😸🔗 Michi: Algunas disciplinas relacionadas con la IA son:\n"
            "1. 🧠 Ciencias Cognitivas: estudian la mente y sus procesos, aportando modelos para emular el pensamiento humano.\n"
            "2. 🤔 Filosofía: aborda cuestiones éticas y ontológicas, como la naturaleza de la conciencia.\n"
            "3. 🧬 Neurociencia: estudia el cerebro y el sistema nervioso, inspirando los modelos de redes neuronales.\n"
            "4. 🗣️ Lingüística: analiza el lenguaje humano, aportando al procesamiento del lenguaje natural.\n"
            "5. ➗ Matemáticas y Estadística: dan las bases teóricas para los algoritmos y modelos de aprendizaje."
        ]
    },
    # =================================================================
    # AGENTES - ESTRUCTURA Y CONCEPTOS
    # =================================================================
    "agente": {
        "definicion": [
            "🤖🐱 Michi: Un agente es cualquier entidad que percibe su entorno "
            "mediante sensores y actúa sobre él mediante actuadores.",
            "🐱📚 Michi: Un agente recibe información de su entorno y después "
            "realiza acciones sobre ese entorno."
        ],
        "funcion": [
            "👁️➡️🧠➡️🤖 Michi: Un agente percibe información del entorno, "
            "la procesa y después ejecuta una acción mediante sus actuadores."
        ],
        "ejemplo": [
            "😸💡 Michi: Ejemplos de agentes son un robot, un automóvil autónomo, ChatGPT, un dron y un robot aspiradora."
        ]
    },
    "agente_inteligente": {
        "definicion": [
            "🧠🤖 Michi: Un agente inteligente selecciona acciones que le permiten "
            "alcanzar sus objetivos de la mejor manera posible de acuerdo con "
            "la información que percibe."
        ]
    },
    "formas_agente": {
        "lista": [
            "🐱📚 Michi: Un agente puede adoptar distintas formas:\n"
            "1. 👤 Agente humano: tiene sensores naturales (ojos, oídos) y actuadores como las manos y la voz.\n"
            "2. 🤖 Agente robótico: puede tener cámaras y sensores de proximidad como entradas, y motores o brazos mecánicos como salidas.\n"
            "3. 💻 Agente software: interactúa con archivos, redes y sistemas mediante entradas digitales."
        ]
    },
    "construccion_agente": {
        "definicion": [
            "🐱⚙️ Michi: Un agente se construye combinando una arquitectura "
            "con un programa del agente. Juntos implementan la función del agente."
        ],
        "funcion": [
            "😸📚 Michi: La arquitectura proporciona los recursos físicos o "
            "computacionales y el programa determina el comportamiento del agente."
        ]
    },
    # NUEVO: ESTRUCTURA GENERAL DE UN AGENTE (sensores / función / actuadores)
    "estructura_agente": {
        "definicion": [
            "🐾🐱 Michi: Todo agente inteligente está compuesto básicamente por tres partes: sensores, una función de agente y actuadores."
        ],
        "lista": [
            "🤖📚 Michi: La estructura básica de un agente es:\n"
            "1. 👀 Sensores: captan información del entorno (ej. cámaras, micrófonos, sensores de temperatura).\n"
            "2. 🧠 Función de Agente: toma decisiones basadas en la percepción y su conocimiento interno.\n"
            "3. ⚙️ Actuadores: ejecutan acciones para modificar el entorno (ej. motores, brazos robóticos, respuestas de software)."
        ]
    },
    # TIPOS DE AGENTES
    "tipos_agentes": {
        "lista": [
            "🤖📚 Michi: Existen cinco tipos principales de agentes:\n"
            "1. ⚡ Agente de reflejo simple.\n"
            "2. 🧠 Agente basado en modelos.\n"
            "3. 🎯 Agente basado en metas.\n"
            "4. ⭐ Agente basado en utilidad (o en el mejor desempeño).\n"
            "5. 📈 Agente que aprende."
        ]
    },
    "reflejo_simple": {
        "definicion": [
            "⚡🐱 Michi: Un agente de reflejo simple selecciona acciones "
            "basándose únicamente en la percepción actual, sin considerar "
            "el historial de estados del entorno. Funciona con reglas del tipo 'Si-Entonces'."
        ],
        "ejemplo": [
            "😸💡 Michi: Ejemplos son un termostato, un robot aspiradora simple y un sensor de movimiento. Su problema es que no recuerda nada: por ejemplo, una aspiradora de reflejo simple no recuerda qué habitación ya limpió antes."
        ]
    },
    "basado_modelos": {
        "definicion": [
            "🧠🐱 Michi: Un agente basado en modelos mantiene un estado interno "
            "que representa información sobre el entorno que no puede observar "
            "directamente en ese momento."
        ],
        "ejemplo": [
            "🐱💡 Michi: Un robot aspiradora que mantiene un mapa o estado interno "
            "del lugar es un ejemplo de agente basado en modelos."
        ]
    },
    "basado_metas": {
        "definicion": [
            "🎯🐱 Michi: Un agente basado en metas no solo reacciona a su entorno; "
            "también tiene un objetivo definido y usa modelos de planificación "
            "para evaluar acciones y elegir la mejor opción que lo acerque a esa meta."
        ],
        "ejemplo": [
            "😸💡 Michi: Ejemplos son un GPS o navegador que elige la mejor ruta a un destino, un robot humanoide y la planificación de tareas. También una aspiradora que decide moverse solo cuando detecta suciedad, para gastar el menor número de movimientos posible."
        ]
    },
    "basado_utilidad": {
        "definicion": [
            "⭐🐱 Michi: Un agente basado en utilidad, o basado en el logro del mejor desempeño, "
            "no solo busca alcanzar un objetivo, sino hacerlo de la manera más eficiente posible: "
            "evalúa varias alternativas y elige la mejor."
        ],
        "ejemplo": [
            "😸💡 Michi: AlphaGo es un gran ejemplo: es una IA que aprende a jugar Go mejorando sus estrategias con cada partida. También un GPS que compara varias rutas y elige la mejor según distancia, tráfico o tiempo."
        ]
    },
    "agente_aprende": {
        "definicion": [
            "📈🤖 Michi: Un agente que aprende mejora su desempeño con la experiencia "
            "y ajusta su comportamiento para trabajar de manera más eficiente."
        ],
        "ejemplo": [
            "🐱💡 Michi: Ejemplos son AlphaGo, ChatGPT, robots modernos y vehículos autónomos."
        ]
    },
    # NUEVO: TIPOS DE AMBIENTES
    "tipos_ambientes": {
        "definicion": [
            "🌍🐱 Michi: El ambiente en el que opera un agente afecta directamente su diseño y funcionamiento."
        ],
        "lista": [
            "🐱🌍 Michi: Los ambientes se pueden clasificar en:\n"
            "1. ⏱️ Estático vs. Dinámico: si el ambiente cambia mientras el agente decide (ej. ajedrez vs. conducir un auto).\n"
            "2. 🔢 Discreto vs. Continuo: si hay un número finito de estados (ej. damas vs. robot en una fábrica).\n"
            "3. 👁️ Completamente observable vs. Parcialmente observable: si el agente tiene acceso a toda la información relevante o solo a una parte (ej. ajedrez vs. robot explorador en Marte)."
        ]
    },
    # NUEVO: PROPIEDADES DE LOS ENTORNOS DE TAREAS
    "propiedades_entornos": {
        "definicion": [
            "📋🐱 Michi: Los entornos de tareas tienen propiedades específicas que ayudan a caracterizarlos y a diseñar mejor al agente."
        ],
        "lista": [
            "🐱📋 Michi: Las principales propiedades de los entornos de tareas son:\n"
            "1. 🎲 Determinístico vs. Estocástico: si el próximo estado depende solo del estado actual y la acción, o si hay incertidumbre.\n"
            "2. 🔁 Episódico vs. Secuencial: si cada acción es independiente, o si las acciones pasadas afectan a las futuras.\n"
            "3. ⏱️ Estático vs. Dinámico: si el entorno cambia o no mientras el agente decide.\n"
            "4. ⏳ Semidinámico: el entorno no cambia, pero el desempeño puede verse afectado por el tiempo (ej. ajedrez con reloj).\n"
            "5. 🔢 Discreto vs. Continuo: si el número de estados y acciones posibles es finito o infinito."
        ]
    },
    # ¿QUÉ TIPO DE AGENTE ES MICHI?
    "michi_agente": {
        "definicion": [
            "🎯🐱 Michi: ¡Ahora soy un agente basado en metas! Ya no me limito a reaccionar con reglas fijas: tengo una lista de necesidades (salud, comida, energía, cariño, atención y felicidad) y siempre persigo primero la que más urge.",
            "😸🎯 Michi: Superé mi etapa de reflejo simple. Ahora evalúo cuáles de mis metas no están satisfechas y priorizo la más importante antes de decidir qué pedirte."
        ],
        "funcion": [
            "🤖📚 Michi: Por ejemplo, si mi salud está crítica Y también tengo hambre, priorizo pedir cuidado primero, porque esa meta tiene mayor urgencia que las demás. Así decido qué necesidad atender antes que otra.",
            "🐱⚙️ Michi: Cada una de mis necesidades tiene una prioridad distinta. Cuando varias están pendientes a la vez, elijo comunicarte la más urgente en vez de simplemente reaccionar a la última percepción, como haría un agente de reflejo simple."
        ],
        "ejemplo": [
            "😻💡 Michi: Es como el GPS que vimos en la presentación de Agentes Inteligentes: no solo reacciona al entorno, tiene un objetivo (llegar a destino) y planifica para lograrlo. Yo hago lo mismo, pero con mis necesidades básicas."
        ]
    }
}
