"""
INTERFAZ GRÁFICA DE MICHI (tkinter)
=====================================================

Esta ventana NO reimplementa la lógica del agente: importa y reutiliza
las funciones de funciones.py (que a su vez usa banco_palabras.py).

Qué muestra:
  * Michi dibujado con formas vectoriales (no es un emoji): sus ojos y su
    boca cambian según su estado y parpadea de vez en cuando.
  * Barras de salud, felicidad, comida y energía que se animan al cambiar.
  * La meta activa del agente basado en metas.
  * Un chat con burbujas: las tuyas a la derecha, las de Michi a la izquierda.
  * Botones de respuesta rápida (Sí / No / Bien / Mal...) cuando Michi te
    hace una pregunta.
  * Botones de acción: alimentar, dar cariño, jugar, dormir, hábitos y
    platicar (inicia una charla con Michi).

Como las funciones originales usan print() para "hablar", se redirige
sys.stdout hacia una cola (queue.Queue). La ventana lee esa cola varias
veces por segundo, separa el texto en líneas y las muestra como burbujas.
Funciona igual si el print() viene del hilo del agente o de un botón.

Requiere Python con tkinter (incluido en Windows y macOS; en Linux a
veces hay que instalar el paquete "python3-tk"). No usa librerías externas.
"""

import sys
import time
import queue
import random
import tkinter as tk
from tkinter import font as tkfont

import funciones as fn


# =====================================================================
# REDIRECCIÓN DE LA SALIDA (para reutilizar las funciones tal cual)
# =====================================================================
class ColaDeSalida:
    """Imita a un archivo (.write / .flush) pero guarda el texto en una cola."""

    def __init__(self):
        self.cola = queue.Queue()

    def write(self, texto):
        if texto:
            self.cola.put(texto)
        return len(texto)

    def flush(self):
        pass


cola_salida = ColaDeSalida()


def redirigir_salida():
    sys.stdout = cola_salida


# =====================================================================
# DISEÑO: colores y tipografía
# =====================================================================
# Paleta "noche en el tejado": fondo índigo, pelaje lila, ojos color luna.
BG = "#171a36"             # fondo del chat
PANEL = "#22264d"          # panel izquierdo
ESCENA = "#2c3066"         # círculo detrás de Michi
BURBUJA_MICHI = "#2f3468"
BURBUJA_TU = "#ffd86b"
TEXTO = "#eeeaff"
TEXTO_SUAVE = "#a3a6d6"
TEXTO_OSCURO = "#1b1d3a"
LUNA = "#ffd86b"           # acento principal (ojos de Michi, botón enviar)
MENTA = "#7fe3c4"          # estadística saludable
AMBAR = "#ffd86b"          # estadística en descenso
CORAL = "#ff7a8a"          # estadística crítica
RIEL = "#343a78"           # fondo de las barras
BOTON = "#323872"
BOTON_HOVER = "#444b92"

PELAJE = "#d8d2ff"
PELAJE_SOMBRA = "#8d86d9"
PELAJE_ENFERMO = "#c6e5cf"
PELAJE_MUERTO = "#9aa0b5"
ROSA = "#ff9fb5"
LAGRIMA = "#8fd3ff"

if sys.platform.startswith("win"):
    FUENTE_EMOJI = "Segoe UI Emoji"
elif sys.platform == "darwin":
    FUENTE_EMOJI = "Apple Color Emoji"
else:
    FUENTE_EMOJI = "Noto Color Emoji"


def elegir_fuente():
    """Primera tipografía redondeada/legible disponible en el sistema."""
    disponibles = set(tkfont.families())
    for nombre in ("Nunito", "Quicksand", "Poppins", "Segoe UI", "SF Pro Rounded",
                "Helvetica Neue", "Ubuntu", "DejaVu Sans"):
        if nombre in disponibles:
            return nombre
    return "TkDefaultFont"


def color_segun_valor(valor):
    """Menta si está bien, ámbar si va bajando, coral si es crítico."""
    if valor <= 20:
        return CORAL
    if valor <= 50:
        return AMBAR
    return MENTA


# =====================================================================
# ESTADO VISUAL DE MICHI (misma lógica de prioridades que obtener_expresion)
# =====================================================================
def estado_visual():
    """Devuelve el nombre del estado que se dibuja."""
    m = fn.mascota
    if not m["viva"]:
        return "muerto"
    if m["salud"] <= 20:
        return "enfermo"
    if m["comida"] <= 10:
        return "hambre"
    if m["energia"] <= 20:
        return "dormido"
    if m["felicidad"] <= 20:
        return "llorando"
    if m["felicidad"] <= 40:
        return "triste"
    if m["felicidad"] >= 90:
        return "encantado"
    if m["felicidad"] >= 75:
        return "feliz"
    return "normal"


# Cómo se dibuja cada estado: (ojos, boca, extras)
ASPECTO = {
    "normal":    ("abiertos", "sonrisa", ()),
    "feliz":     ("abiertos", "sonrisa", ("mejillas",)),
    "encantado": ("felices", "sonrisa", ("mejillas", "corazones")),
    "triste":    ("tristes", "triste", ()),
    "llorando":  ("tristes", "triste", ("lagrimas",)),
    "dormido":   ("cerrados", "neutra", ("zzz",)),
    "hambre":    ("tristes", "abierta", ()),
    "enfermo":   ("enfermos", "triste", ("sudor",)),
    "muerto":    ("x", "neutra", ()),
}

# Descripciones "amigables" de cada meta (definir_metas devuelve tuplas:
# (nombre_meta, prioridad, etiqueta_accion)).
DESCRIPCIONES_METAS = {
    "salud_critica": "cuidar su salud urgentemente",
    "comida_urgente": "conseguir comida ya mismo",
    "comida_baja": "comer algo pronto",
    "energia_baja": "descansar un poco",
    "carino_pendiente": "recibir cariño",
    "atencion_pendiente": "que le prestes atención",
    "felicidad_baja": "sentirse mejor",
    "quiere_jugar": "jugar contigo",
}


def obtener_texto_meta():
    """Meta que Michi persigue ahora (si funciones.py aún no la define, no rompe)."""
    if not hasattr(fn, "definir_metas"):
        return ""
    metas = fn.definir_metas(fn.percibir())
    if not metas:
        return "Michi está conforme"
    nombre_meta = metas[0][0]
    return "Michi quiere " + DESCRIPCIONES_METAS.get(nombre_meta, nombre_meta)


def opciones_rapidas():
    """
    Botones de respuesta rápida según lo último que Michi preguntó.
    Devuelve una lista de textos (vacía si no hay pregunta abierta).
    """
    if hasattr(fn, "charla") and fn.charla.get("nodo"):
        tipo = fn.CHARLAS[fn.charla["nodo"]]["tipo"]
        if tipo == "emocion":
            return ["Bien", "Más o menos", "Mal"]
        if tipo == "si_no":
            return ["Sí", "No", "Quizás"]
        return []                            # nodo "libre": se escribe a mano
    if hasattr(fn, "pregunta_vigente") and fn.pregunta_vigente():
        return ["Sí", "No", "Quizás"]
    return []


# =====================================================================
# WIDGETS PROPIOS
# =====================================================================
class Boton(tk.Label):
    """
    Botón plano hecho con un Label. Los tk.Button ignoran los colores en
    macOS; este se ve igual en Windows, macOS y Linux.
    """

    def __init__(self, master, texto, comando, fuente, bg=BOTON, hover=BOTON_HOVER,
                 fg=TEXTO, **kw):
        super().__init__(master, text=texto, bg=bg, fg=fg, font=fuente,
                         cursor="hand2", padx=12, pady=8, **kw)
        self._bg, self._hover, self._comando = bg, hover, comando
        self._activo = True
        self.bind("<Enter>", lambda e: self._activo and self.configure(bg=self._hover))
        self.bind("<Leave>", lambda e: self.configure(bg=self._bg))
        self.bind("<ButtonRelease-1>", self._soltar)

    def _soltar(self, evento):
        if self._activo and self._comando:
            self._comando()

    def activar(self, activo):
        self._activo = activo
        self.configure(cursor="hand2" if activo else "arrow",
                    fg=TEXTO if activo else TEXTO_SUAVE)


class BarraEstado(tk.Canvas):
    """Barra redondeada que se desliza suavemente hacia su valor objetivo."""

    ALTO = 12

    def __init__(self, master, fondo):
        super().__init__(master, height=self.ALTO, bg=fondo, highlightthickness=0, bd=0)
        self.valor = 0.0
        self.objetivo = 0
        self.color = MENTA
        self._sucio = True
        self.bind("<Configure>", lambda e: self._dibujar())

    def fijar(self, objetivo, color):
        if objetivo != self.objetivo or color != self.color:
            self.objetivo, self.color, self._sucio = objetivo, color, True

    def paso(self):
        """Avanza un poco hacia el objetivo (se llama desde el ciclo de animación)."""
        if self.valor == self.objetivo and not self._sucio:
            return
        diferencia = self.objetivo - self.valor
        self.valor += diferencia if abs(diferencia) <= 3 else (3 if diferencia > 0 else -3)
        self._dibujar()

    def _pastilla(self, x1, x2, color):
        y1, y2 = 0, self.ALTO
        r = (y2 - y1) / 2
        if x2 - x1 <= 2 * r:
            self.create_oval(x1, y1, x1 + 2 * r, y2, fill=color, outline="")
            return
        self.create_oval(x1, y1, x1 + 2 * r, y2, fill=color, outline="")
        self.create_oval(x2 - 2 * r, y1, x2, y2, fill=color, outline="")
        self.create_rectangle(x1 + r, y1, x2 - r, y2, fill=color, outline="")

    def _dibujar(self):
        ancho = self.winfo_width()
        if ancho <= 4:
            return
        self._sucio = False
        self.delete("all")
        self._pastilla(0, ancho, RIEL)
        if self.valor > 0:
            self._pastilla(0, max(self.ALTO, ancho * self.valor / 100), self.color)


class GatoCanvas(tk.Canvas):
    """Michi dibujado con formas: ojos, boca y extras cambian según su estado."""

    ANCHO, ALTO = 280, 250

    def __init__(self, master, fondo):
        super().__init__(master, width=self.ANCHO, height=self.ALTO, bg=fondo,
                        highlightthickness=0, bd=0)
        self._firma = None

    def dibujar(self, estado, ojos_cerrados):
        """Redibuja solo si algo cambió (evita parpadeos molestos)."""
        firma = (estado, ojos_cerrados)
        if firma == self._firma:
            return
        self._firma = firma
        self.delete("all")
        ojos, boca, extras = ASPECTO[estado]
        if ojos_cerrados and ojos in ("abiertos", "tristes"):
            ojos = "cerrados"
        pelaje = {"enfermo": PELAJE_ENFERMO, "muerto": PELAJE_MUERTO}.get(estado, PELAJE)

        # escena: una "luna" detrás de Michi
        self.create_oval(20, 14, 260, 246, fill=ESCENA, outline="")
        # cuerpo, orejas y cabeza
        self.create_oval(72, 178, 208, 270, fill=pelaje, outline=PELAJE_SOMBRA, width=2)
        self.create_polygon(68, 100, 80, 28, 128, 66, fill=pelaje, outline=PELAJE_SOMBRA, width=2)
        self.create_polygon(212, 100, 200, 28, 152, 66, fill=pelaje, outline=PELAJE_SOMBRA, width=2)
        self.create_polygon(82, 88, 88, 48, 112, 70, fill=ROSA, outline="")
        self.create_polygon(198, 88, 192, 48, 168, 70, fill=ROSA, outline="")
        self.create_oval(55, 55, 225, 205, fill=pelaje, outline=PELAJE_SOMBRA, width=2)

        if "mejillas" in extras:
            self.create_oval(72, 140, 104, 160, fill="#ffb3c6", outline="")
            self.create_oval(176, 140, 208, 160, fill="#ffb3c6", outline="")

        self._ojo(105, 118, ojos, izquierdo=True)
        self._ojo(175, 118, ojos, izquierdo=False)
        self.create_polygon(133, 142, 147, 142, 140, 152, fill=ROSA, outline=TEXTO_OSCURO)
        self._boca(boca)

        # bigotes
        for dy, dy2 in ((-6, -2), (6, 6), (18, 12)):
            self.create_line(62, 152 + dy, 94, 152 + dy2, fill=PELAJE_SOMBRA, width=2)
            self.create_line(218, 152 + dy, 186, 152 + dy2, fill=PELAJE_SOMBRA, width=2)

        self._extras(extras)

    # ---- partes del dibujo ----
    def _ojo(self, cx, cy, tipo, izquierdo):
        if tipo == "abiertos":
            self.create_oval(cx - 17, cy - 17, cx + 17, cy + 17, fill=LUNA, outline=TEXTO_OSCURO, width=2)
            self.create_oval(cx - 6, cy - 13, cx + 6, cy + 13, fill=TEXTO_OSCURO, outline="")
            self.create_oval(cx + 3, cy - 10, cx + 9, cy - 4, fill="white", outline="")
        elif tipo == "tristes":
            self.create_oval(cx - 15, cy - 15, cx + 15, cy + 15, fill=LUNA, outline=TEXTO_OSCURO, width=2)
            self.create_oval(cx - 8, cy - 11, cx + 8, cy + 11, fill=TEXTO_OSCURO, outline="")
            self.create_oval(cx - 2, cy - 8, cx + 5, cy - 1, fill="white", outline="")
            # ceja inclinada hacia el centro (aspecto preocupado)
            if izquierdo:
                self.create_line(cx - 18, cy - 26, cx + 12, cy - 18, fill=TEXTO_OSCURO, width=3)
            else:
                self.create_line(cx + 18, cy - 26, cx - 12, cy - 18, fill=TEXTO_OSCURO, width=3)
        elif tipo == "felices":
            self.create_arc(cx - 16, cy - 14, cx + 16, cy + 18, start=20, extent=140,
                            style="arc", outline=TEXTO_OSCURO, width=4)
        elif tipo == "cerrados":
            self.create_arc(cx - 16, cy - 18, cx + 16, cy + 10, start=200, extent=140,
                            style="arc", outline=TEXTO_OSCURO, width=4)
        elif tipo == "enfermos":
            self.create_line(cx - 15, cy, cx - 8, cy - 7, cx, cy, cx + 8, cy - 7, cx + 15, cy,
                            fill=TEXTO_OSCURO, width=4, smooth=True)
        elif tipo == "x":
            self.create_line(cx - 12, cy - 12, cx + 12, cy + 12, fill=TEXTO_OSCURO, width=4)
            self.create_line(cx - 12, cy + 12, cx + 12, cy - 12, fill=TEXTO_OSCURO, width=4)

    def _boca(self, tipo):
        if tipo == "sonrisa":
            self.create_arc(122, 144, 141, 166, start=200, extent=140, style="arc",
                            outline=TEXTO_OSCURO, width=3)
            self.create_arc(139, 144, 158, 166, start=200, extent=140, style="arc",
                            outline=TEXTO_OSCURO, width=3)
        elif tipo == "triste":
            self.create_arc(122, 160, 141, 182, start=20, extent=140, style="arc",
                            outline=TEXTO_OSCURO, width=3)
            self.create_arc(139, 160, 158, 182, start=20, extent=140, style="arc",
                            outline=TEXTO_OSCURO, width=3)
        elif tipo == "abierta":
            self.create_oval(131, 156, 149, 178, fill="#7a2f48", outline=TEXTO_OSCURO, width=2)
        else:  # neutra
            self.create_line(140, 152, 140, 160, fill=TEXTO_OSCURO, width=3)
            self.create_line(128, 162, 152, 162, fill=TEXTO_OSCURO, width=3)

    def _extras(self, extras):
        if "lagrimas" in extras:
            self.create_oval(108, 140, 118, 158, fill=LAGRIMA, outline="")
            self.create_oval(168, 140, 178, 158, fill=LAGRIMA, outline="")
        if "sudor" in extras:
            self.create_polygon(196, 66, 190, 80, 202, 80, fill=LAGRIMA, outline="", smooth=True)
        if "zzz" in extras:
            for x, y, tam in ((214, 56, 14), (234, 38, 18), (252, 18, 22)):
                self.create_text(x, y, text="z", fill=TEXTO, font=("Georgia", tam, "bold italic"))
        if "corazones" in extras:
            for x, y, tam in ((40, 50, 16), (240, 70, 20), (52, 120, 12)):
                self.create_text(x, y, text="♥", fill=CORAL, font=("Arial", tam))


class PanelChat(tk.Frame):
    """Zona de mensajes con burbujas y desplazamiento."""

    MAX_MENSAJES = 150

    def __init__(self, master, fuente, fuente_pequena):
        super().__init__(master, bg=BG)
        self.fuente, self.fuente_pequena = fuente, fuente_pequena
        self.filas = []
        self.etiquetas = []                       # burbujas, para ajustar su ancho
        self.ancho_burbuja = 380

        self.lienzo = tk.Canvas(self, bg=BG, highlightthickness=0, bd=0)
        self.barra = tk.Scrollbar(self, orient="vertical", command=self.lienzo.yview)
        self.lienzo.configure(yscrollcommand=self.barra.set)
        self.barra.pack(side="right", fill="y")
        self.lienzo.pack(side="left", fill="both", expand=True)

        self.interior = tk.Frame(self.lienzo, bg=BG)
        self.ventana = self.lienzo.create_window((0, 0), window=self.interior, anchor="nw")
        self.interior.bind("<Configure>",
                        lambda e: self.lienzo.configure(scrollregion=self.lienzo.bbox("all")))
        self.lienzo.bind("<Configure>", self._ajustar_ancho)
        self.lienzo.bind("<Enter>", self._enlazar_rueda)

    def _ajustar_ancho(self, evento):
        self.lienzo.itemconfigure(self.ventana, width=evento.width)
        self.ancho_burbuja = max(200, int(evento.width * 0.66))
        for etiqueta in self.etiquetas:
            etiqueta.configure(wraplength=self.ancho_burbuja)

    def _enlazar_rueda(self, _evento):
        self.lienzo.bind_all("<MouseWheel>", self._rueda)
        self.lienzo.bind_all("<Button-4>", self._rueda)
        self.lienzo.bind_all("<Button-5>", self._rueda)

    def _rueda(self, evento):
        if getattr(evento, "num", 0) == 4:
            paso = -1
        elif getattr(evento, "num", 0) == 5:
            paso = 1
        else:
            paso = -1 if evento.delta > 0 else 1
        self.lienzo.yview_scroll(paso, "units")

    def agregar(self, rol, texto, emoji=None):
        """rol: 'michi' (izquierda), 'tu' (derecha) o 'nota' (centrada, discreta)."""
        fila = tk.Frame(self.interior, bg=BG)
        fila.pack(fill="x", padx=14, pady=4)
        if rol == "nota":
            etiqueta = tk.Label(fila, text=texto, bg=BG, fg=TEXTO_SUAVE, font=self.fuente_pequena,
                                wraplength=self.ancho_burbuja + 120, justify="center")
            etiqueta.pack()
        elif rol == "michi":
            tk.Label(fila, text=emoji or "🐱", bg=BG, font=(FUENTE_EMOJI, 16)).pack(
                side="left", anchor="n", padx=(0, 8))
            etiqueta = tk.Label(fila, text=texto, bg=BURBUJA_MICHI, fg=TEXTO, font=self.fuente,
                                wraplength=self.ancho_burbuja, justify="left", padx=14, pady=9)
            etiqueta.pack(side="left", anchor="n")
        else:
            etiqueta = tk.Label(fila, text=texto, bg=BURBUJA_TU, fg=TEXTO_OSCURO, font=self.fuente,
                                wraplength=self.ancho_burbuja, justify="left", padx=14, pady=9)
            etiqueta.pack(side="right", anchor="n")
        self.etiquetas.append(etiqueta)
        self.filas.append(fila)
        while len(self.filas) > self.MAX_MENSAJES:
            self.filas.pop(0).destroy()
            self.etiquetas.pop(0)
        self.after_idle(self._al_final)

    def _al_final(self):
        self.lienzo.update_idletasks()
        self.lienzo.yview_moveto(1.0)


# =====================================================================
# VENTANA PRINCIPAL
# =====================================================================
class VentanaMichi:
    PLACEHOLDER = "Escríbele a Michi…"

    def __init__(self, root):
        self.root = root
        self.root.title("Michi, tu mascota virtual")
        self.root.geometry("1000x700")
        self.root.minsize(840, 620)
        self.root.configure(bg=BG)

        familia = elegir_fuente()
        self.f_nombre = (familia, 22, "bold")
        self.f_texto = (familia, 11)
        self.f_pequena = (familia, 9)
        self.f_boton = (familia, 10, "bold")
        self.f_entrada = (familia, 12)

        self._resto = ""                          # línea a medias de la salida
        self._opciones_actuales = None
        self._ojos_cerrados_hasta = 0.0
        self._proximo_parpadeo = time.time() + random.uniform(2.5, 6)
        self._hay_placeholder = True

        self._crear_panel_izquierdo()
        self._crear_panel_chat()
        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)

        # Arranca el hilo del agente (igual que en consola) y el ciclo de la ventana.
        fn.iniciar_hilo_agente()
        self.chat.agregar("nota", "Escríbele algo a Michi o toca Platicar para que te haga preguntas.")
        self.chat.agregar("michi", "¡Hola! Soy Michi. ¿Jugamos o platicamos?", "😸🐾")
        self._ciclo()

    # -----------------------------------------------------------------
    # CONSTRUCCIÓN
    # -----------------------------------------------------------------
    def _crear_panel_izquierdo(self):
        izq = tk.Frame(self.root, bg=PANEL, width=340)
        izq.pack(side="left", fill="y")
        izq.pack_propagate(False)

        self.gato = GatoCanvas(izq, PANEL)
        self.gato.pack(pady=(18, 0))

        tk.Label(izq, text=fn.mascota["nombre"], bg=PANEL, fg=TEXTO,
                font=self.f_nombre).pack(pady=(4, 0))
        self.lbl_expresion = tk.Label(izq, text="", bg=PANEL, fg=TEXTO_SUAVE, font=self.f_texto,
                                    wraplength=300, justify="center")
        self.lbl_expresion.pack(pady=(2, 8))
        self.lbl_meta = tk.Label(izq, text="", bg=BOTON, fg=LUNA, font=self.f_pequena,
                                wraplength=290, padx=12, pady=5)
        self.lbl_meta.pack(pady=(0, 12))

        barras = tk.Frame(izq, bg=PANEL)
        barras.pack(fill="x", padx=22)
        self.barras, self.valores = {}, {}
        for clave, etiqueta in (("salud", "❤️  Salud"), ("felicidad", "😊  Felicidad"),
                                ("comida", "🍗  Comida"), ("energia", "⚡  Energía")):
            fila = tk.Frame(barras, bg=PANEL)
            fila.pack(fill="x", pady=5)
            tk.Label(fila, text=etiqueta, bg=PANEL, fg=TEXTO, font=self.f_texto,
                    width=11, anchor="w").pack(side="left")
            barra = BarraEstado(fila, PANEL)
            barra.pack(side="left", fill="x", expand=True, padx=6)
            valor = tk.Label(fila, text="0", bg=PANEL, fg=TEXTO_SUAVE, font=self.f_pequena,
                            width=4, anchor="e")
            valor.pack(side="left")
            self.barras[clave], self.valores[clave] = barra, valor

        self.lbl_horas = tk.Label(izq, text="", bg=PANEL, fg=TEXTO_SUAVE, font=self.f_pequena,
                                wraplength=300, justify="center")
        self.lbl_horas.pack(pady=(6, 10))

        rejilla = tk.Frame(izq, bg=PANEL)
        rejilla.pack(fill="x", padx=18, pady=(0, 14))
        acciones = [
            ("Alimentar", fn.alimentar), ("Dar cariño", fn.dar_carino), ("Jugar", fn.jugar),
            ("Dormir", fn.descansar), ("Hábitos", fn.mostrar_habitos), ("Platicar", self._platicar),
        ]
        self.botones_accion = []
        for i, (texto, comando) in enumerate(acciones):
            destacado = texto == "Platicar"
            boton = Boton(rejilla, texto, lambda c=comando: self._accion(c), self.f_boton,
                        bg=LUNA if destacado else BOTON,
                        hover="#ffe699" if destacado else BOTON_HOVER,
                        fg=TEXTO_OSCURO if destacado else TEXTO)
            boton.grid(row=i // 3, column=i % 3, padx=4, pady=4, sticky="ew")
            self.botones_accion.append(boton)
        for columna in range(3):
            rejilla.columnconfigure(columna, weight=1, uniform="acciones")

    def _crear_panel_chat(self):
        der = tk.Frame(self.root, bg=BG)
        der.pack(side="left", fill="both", expand=True)

        self.chat = PanelChat(der, self.f_texto, self.f_pequena)
        self.chat.pack(fill="both", expand=True, pady=(10, 0))

        self.fila_opciones = tk.Frame(der, bg=BG)       # se muestra solo si Michi pregunta
        self.fila_entrada = tk.Frame(der, bg=BG)
        self.fila_entrada.pack(fill="x", padx=14, pady=(8, 14))

        self.entrada = tk.Entry(self.fila_entrada, font=self.f_entrada, bg=PANEL, fg=TEXTO_SUAVE,
                                insertbackground=TEXTO, relief="flat", bd=0,
                                highlightthickness=2, highlightbackground=PANEL,
                                highlightcolor=LUNA)
        self.entrada.pack(side="left", fill="x", expand=True, ipady=9)
        self.entrada.insert(0, self.PLACEHOLDER)
        self.entrada.bind("<FocusIn>", self._quitar_placeholder)
        self.entrada.bind("<FocusOut>", self._poner_placeholder)
        self.entrada.bind("<Return>", lambda e: self._enviar())

        self.btn_enviar = Boton(self.fila_entrada, "Enviar", self._enviar, self.f_boton,
                                bg=LUNA, hover="#ffe699", fg=TEXTO_OSCURO)
        self.btn_enviar.pack(side="left", padx=(8, 0))

    # -----------------------------------------------------------------
    # ENTRADA DE TEXTO
    # -----------------------------------------------------------------
    def _quitar_placeholder(self, _evento=None):
        if self._hay_placeholder:
            self.entrada.delete(0, "end")
            self.entrada.configure(fg=TEXTO)
            self._hay_placeholder = False

    def _poner_placeholder(self, _evento=None):
        if not self.entrada.get().strip():
            self.entrada.delete(0, "end")
            self.entrada.insert(0, self.PLACEHOLDER)
            self.entrada.configure(fg=TEXTO_SUAVE)
            self._hay_placeholder = True

    def _enviar(self):
        if self._hay_placeholder:
            return
        texto = self.entrada.get().strip()
        if not texto:
            return
        self.entrada.delete(0, "end")
        self._enviar_texto(texto)

    def _enviar_texto(self, texto):
        """Muestra tu mensaje y se lo pasa a Michi (también lo usan las respuestas rápidas)."""
        if not fn.mascota["viva"]:
            return
        self.chat.agregar("tu", texto)
        fn.conversar(texto)
        self._refrescar()

    # -----------------------------------------------------------------
    # ACCIONES
    # -----------------------------------------------------------------
    def _accion(self, funcion):
        if fn.mascota["viva"]:
            funcion()
            self._refrescar()

    def _platicar(self):
        fn.conversar("platiquemos")

    def _cerrar(self):
        self.root.destroy()

    # -----------------------------------------------------------------
    # SALIDA DE FUNCIONES.PY -> BURBUJAS
    # -----------------------------------------------------------------
    def _mostrar_linea(self, linea):
        linea = linea.strip()
        if not linea:
            return
        # Las barras de texto de funciones.py ya se ven en el panel izquierdo.
        if "ESTADÍSTICAS DE MICHI" in linea or "█" in linea or "░" in linea:
            return
        indice = linea.find("Michi:")
        if indice != -1:
            self.chat.agregar("michi", linea[indice + 6:].strip(), linea[:indice].strip() or "🐱")
        else:
            self.chat.agregar("nota", linea)

    def _procesar_cola(self):
        texto = ""
        try:
            while True:
                texto += cola_salida.cola.get_nowait()
        except queue.Empty:
            pass
        if texto:
            self._resto += texto
            *lineas, self._resto = self._resto.split("\n")
            for linea in lineas:
                self._mostrar_linea(linea)
        elif self._resto.strip():                 # línea sin salto final: se muestra igual
            self._mostrar_linea(self._resto)
            self._resto = ""

    # -----------------------------------------------------------------
    # ACTUALIZACIÓN VISUAL
    # -----------------------------------------------------------------
    def _actualizar_opciones(self):
        opciones = opciones_rapidas() if fn.mascota["viva"] else []
        if opciones == self._opciones_actuales:
            return
        self._opciones_actuales = opciones
        for hijo in self.fila_opciones.winfo_children():
            hijo.destroy()
        if not opciones:
            self.fila_opciones.pack_forget()
            return
        for texto in opciones:
            Boton(self.fila_opciones, texto, lambda t=texto: self._enviar_texto(t),
                self.f_boton).pack(side="left", padx=(0, 8))
        self.fila_opciones.pack(fill="x", padx=14, pady=(8, 0), before=self.fila_entrada)

    def _refrescar(self):
        m = fn.mascota
        self.lbl_expresion.configure(text=fn.obtener_expresion())
        self.lbl_meta.configure(text=obtener_texto_meta())
        for clave in ("salud", "felicidad", "comida", "energia"):
            valor = m[clave]
            self.barras[clave].fijar(valor, color_segun_valor(valor))
            self.valores[clave].configure(text=str(valor))
        self.lbl_horas.configure(
            text=f"Horas sin cuidado: {m['horas_sin_cuidado']}   ·   "
                f"Horas sin cariño: {m['horas_sin_carino']}")
        self._actualizar_opciones()

        if not m["viva"]:
            for boton in self.botones_accion:
                boton.activar(False)
            self.btn_enviar.activar(False)
            self.entrada.configure(state="disabled")

    def _ciclo(self):
        """Se ejecuta ~10 veces por segundo: mensajes, barras y parpadeo."""
        self._procesar_cola()
        self._refrescar()
        for barra in self.barras.values():
            barra.paso()

        ahora = time.time()
        if ahora >= self._proximo_parpadeo:
            self._ojos_cerrados_hasta = ahora + 0.15
            self._proximo_parpadeo = ahora + random.uniform(2.5, 6)
        self.gato.dibujar(estado_visual(), ahora < self._ojos_cerrados_hasta)

        self.root.after(100, self._ciclo)


# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================
def main():
    redirigir_salida()
    try:                                          # nitidez en pantallas de alta resolución (Windows)
        import ctypes
        ctypes.windll.shcore.SetProcessDpiAwareness(1)
    except Exception:
        pass
    raiz = tk.Tk()
    VentanaMichi(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()