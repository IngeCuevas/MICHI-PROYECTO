"""
INTERFAZ GRÁFICA DE MICHI (tkinter)
=====================================================

Este archivo NO reimplementa la lógica del agente: importa y reutiliza
directamente las funciones de funciones.py (que a su vez usa el banco
de palabras de banco_palabras.py). Aquí solo se construye una ventana
gráfica que:

  1. Muestra un "avatar" de Michi (un emoji grande) que cambia según
     su estado (salud, felicidad, comida, energía).
  2. Muestra barras de progreso con sus estadísticas.
  3. Muestra la meta activa que el agente basado en metas está
     persiguiendo en este momento.
  4. Ofrece botones para alimentar, dar cariño, jugar y hacer dormir
     a Michi, además de un cuadro de texto para conversar con él.
  5. Mantiene, igual que en consola, un hilo en segundo plano que hace
     avanzar el tiempo automáticamente (ciclo_agente).

Como las funciones originales usan print() para "hablar", en vez de
reescribirlas, aquí se redirige la salida estándar (sys.stdout) hacia
una cola (queue.Queue). La ventana revisa esa cola varias veces por
segundo y muestra los mensajes nuevos en el cuadro de conversación.
Esto funciona sin importar si el print() viene del hilo en segundo
plano o de una acción del usuario.

Requiere: Python con tkinter (viene incluido en la instalación
estándar de Python en Windows/Mac; en Linux a veces hay que instalar
el paquete "python3-tk").
"""

import sys
import queue
import tkinter as tk
from tkinter import ttk, scrolledtext

import funciones as fn


# =====================================================================
# REDIRECCIÓN DE LA SALIDA (para reutilizar las funciones tal cual)
# =====================================================================
class ColaDeSalida:
    """
    Objeto que imita a un archivo (tiene .write y .flush) pero en vez
    de imprimir en la consola, guarda el texto en una cola. Así, todos
    los print() de funciones.py (vengan del hilo del agente o de un
    botón) terminan en un solo lugar que la ventana puede leer.
    """

    def __init__(self):
        self.cola = queue.Queue()

    def write(self, texto):
        if texto:
            self.cola.put(texto)
        return len(texto)

    def flush(self):
        pass


cola_salida = ColaDeSalida()
sys.stdout = cola_salida


# =====================================================================
# AVATAR DE MICHI SEGÚN SU ESTADO
# =====================================================================
def obtener_avatar():
    """
    Devuelve un emoji grande que representa el estado actual de Michi.
    Sigue la misma lógica de prioridades que obtener_expresion(),
    pero solo devuelve el "dibujo", no el texto.
    """
    m = fn.mascota
    if not m["viva"]:
        return "💀"
    if m["salud"] <= 20:
        return "🤒"
    if m["comida"] <= 10:
        return "🥺"
    if m["energia"] <= 20:
        return "😴"
    if m["felicidad"] <= 20:
        return "😭"
    if m["felicidad"] <= 40:
        return "😿"
    if m["felicidad"] >= 90:
        return "😻"
    if m["felicidad"] >= 75:
        return "😸"
    return "🐱"


def color_segun_valor(valor):
    """Verde si está bien, naranja si va bajando, rojo si es crítico."""
    if valor <= 20:
        return "#e74c3c"   # rojo
    if valor <= 50:
        return "#f39c12"   # naranja
    return "#2ecc71"       # verde


# Descripciones "amigables" de cada meta, para mostrar la meta activa
# en un lenguaje más natural que el nombre interno usado en funciones.py
# (definir_metas devuelve tuplas: (nombre_meta, prioridad, etiqueta_accion)).
DESCRIPCIONES_METAS = {
    "salud_critica": "¡cuidar su salud urgentemente!",
    "comida_urgente": "conseguir comida ya mismo",
    "comida_baja": "comer algo pronto",
    "energia_baja": "descansar un poco",
    "carino_pendiente": "recibir cariño",
    "atencion_pendiente": "que le prestes atención",
    "felicidad_baja": "sentirse mejor",
    "quiere_jugar": "jugar contigo",
}


def obtener_texto_meta():
    """
    Consulta las metas insatisfechas de Michi (definidas en
    funciones.py mediante el agente basado en metas) y arma el texto
    que se muestra en la interfaz. Si funciones.py todavía no define
    'definir_metas' (por ejemplo, si no has migrado el agente aún),
    la interfaz sigue funcionando sin romperse.
    """
    if not hasattr(fn, "definir_metas"):
        return ""
    metas = fn.definir_metas(fn.percibir())
    if not metas:
        return "🎯 Sin metas pendientes: Michi está conforme."
    nombre_meta, _, _ = metas[0]
    descripcion = DESCRIPCIONES_METAS.get(nombre_meta, nombre_meta)
    return f"🎯 Meta actual: {descripcion}"


# =====================================================================
# VENTANA PRINCIPAL
# =====================================================================
class VentanaMichi:
    def __init__(self, root):
        self.root = root
        self.root.title("🐱 Michi - Mascota Virtual")
        self.root.geometry("560x780")
        self.root.minsize(480, 700)
        self.root.configure(bg="#fdf6ec")

        self.estilo = ttk.Style()
        try:
            self.estilo.theme_use("clam")
        except tk.TclError:
            pass
        for nombre in ("Salud", "Felicidad", "Comida", "Energia"):
            self.estilo.configure(
                f"{nombre}.Horizontal.TProgressbar",
                troughcolor="#eee2d3",
                bordercolor="#eee2d3",
                background="#2ecc71",
                thickness=18,
            )

        self._crear_avatar()
        self._crear_barras()
        self._crear_botones()
        self._crear_chat()

        self.root.protocol("WM_DELETE_WINDOW", self._cerrar)

        # Arranca el hilo del agente (idéntico al de la consola) y
        # empieza a revisar la cola de mensajes.
        fn.iniciar_hilo_agente()
        self._log("🐱✨ ¡Bienvenido a tu mascota virtual Michi! ✨🐱")
        self._log("Usa los botones o escríbele algo en el cuadro de abajo.\n")
        self._refrescar()
        self._procesar_cola()

    # -----------------------------------------------------------------
    # CONSTRUCCIÓN DE WIDGETS
    # -----------------------------------------------------------------
    def _crear_avatar(self):
        marco = tk.Frame(self.root, bg="#fdf6ec")
        marco.pack(pady=(14, 4))

        self.lbl_avatar = tk.Label(
            marco, text="🐱", font=("Segoe UI Emoji", 90), bg="#fdf6ec"
        )
        self.lbl_avatar.pack()

        self.lbl_nombre = tk.Label(
            marco, text=fn.mascota["nombre"],
            font=("Segoe UI", 18, "bold"), bg="#fdf6ec", fg="#4a3f35"
        )
        self.lbl_nombre.pack()

        self.lbl_expresion = tk.Label(
            marco, text="", font=("Segoe UI", 11), bg="#fdf6ec",
            fg="#6b5d4f", wraplength=480, justify="center"
        )
        self.lbl_expresion.pack(pady=(2, 0))

        # Label de la meta activa del agente basado en metas.
        self.lbl_meta = tk.Label(
            marco, text="", font=("Segoe UI", 9, "italic"),
            bg="#fdf6ec", fg="#8a7a68"
        )
        self.lbl_meta.pack(pady=(2, 0))

    def _crear_barras(self):
        marco = tk.Frame(self.root, bg="#fdf6ec")
        marco.pack(fill="x", padx=24, pady=8)

        self.barras = {}
        self.valores = {}
        datos = [
            ("salud", "❤️ Salud", "Salud"),
            ("felicidad", "😊 Felicidad", "Felicidad"),
            ("comida", "🍗 Comida", "Comida"),
            ("energia", "⚡ Energía", "Energia"),
        ]
        for clave, etiqueta, estilo in datos:
            fila = tk.Frame(marco, bg="#fdf6ec")
            fila.pack(fill="x", pady=3)

            tk.Label(
                fila, text=etiqueta, width=12, anchor="w",
                font=("Segoe UI", 10), bg="#fdf6ec", fg="#4a3f35"
            ).pack(side="left")

            barra = ttk.Progressbar(
                fila, style=f"{estilo}.Horizontal.TProgressbar",
                maximum=100, value=0
            )
            barra.pack(side="left", fill="x", expand=True, padx=6)
            self.barras[clave] = barra

            valor_lbl = tk.Label(
                fila, text="0/100", width=7, font=("Segoe UI", 9),
                bg="#fdf6ec", fg="#4a3f35"
            )
            valor_lbl.pack(side="left")
            self.valores[clave] = valor_lbl

        self.lbl_horas = tk.Label(
            marco, text="", font=("Segoe UI", 9, "italic"),
            bg="#fdf6ec", fg="#8a7a68"
        )
        self.lbl_horas.pack(pady=(4, 0))

    def _crear_botones(self):
        marco = tk.Frame(self.root, bg="#fdf6ec")
        marco.pack(pady=8)

        estilo_boton = {
            "font": ("Segoe UI", 10), "width": 14, "bd": 0,
            "bg": "#ffe4c4", "activebackground": "#ffd39b",
            "relief": "flat", "cursor": "hand2"
        }

        self.botones_accion = []
        acciones = [
            ("👀 Ver estado", self._ver_estado),
            ("🍗 Alimentar", self._alimentar),
            ("❤️ Dar cariño", self._dar_carino),
            ("🎾 Jugar", self._jugar),
            ("😴 Dormir", self._descansar),
        ]
        for i, (texto, comando) in enumerate(acciones):
            btn = tk.Button(marco, text=texto, command=comando, **estilo_boton)
            btn.grid(row=i // 3, column=i % 3, padx=5, pady=5)
            self.botones_accion.append(btn)

    def _crear_chat(self):
        marco = tk.Frame(self.root, bg="#fdf6ec")
        marco.pack(fill="both", expand=True, padx=14, pady=(6, 10))

        self.log = scrolledtext.ScrolledText(
            marco, height=12, wrap="word", font=("Segoe UI", 10),
            bg="white", fg="#333333", state="disabled", bd=1, relief="solid"
        )
        self.log.pack(fill="both", expand=True)

        marco_entrada = tk.Frame(self.root, bg="#fdf6ec")
        marco_entrada.pack(fill="x", padx=14, pady=(0, 14))

        self.entrada = tk.Entry(marco_entrada, font=("Segoe UI", 11))
        self.entrada.pack(side="left", fill="x", expand=True, ipady=5)
        self.entrada.bind("<Return>", lambda evento: self._hablar())

        self.btn_hablar = tk.Button(
            marco_entrada, text="🗣️ Hablar", font=("Segoe UI", 10),
            bg="#a3d9a5", activebackground="#8cc98e", bd=0,
            relief="flat", cursor="hand2", command=self._hablar
        )
        self.btn_hablar.pack(side="left", padx=(8, 0))

    # -----------------------------------------------------------------
    # ACCIONES DE LOS BOTONES (usan las funciones de funciones.py)
    # -----------------------------------------------------------------
    def _ver_estado(self):
        fn.mostrar_estado()

    def _alimentar(self):
        fn.alimentar()

    def _dar_carino(self):
        fn.dar_carino()

    def _jugar(self):
        fn.jugar()

    def _descansar(self):
        fn.descansar()

    def _hablar(self):
        texto = self.entrada.get().strip()
        if not texto:
            return
        self.entrada.delete(0, "end")
        print(f"\n🗣️ Tú: {texto}")
        fn.conversar(texto)

    def _cerrar(self):
        self.root.destroy()

    # -----------------------------------------------------------------
    # ACTUALIZACIÓN VISUAL
    # -----------------------------------------------------------------
    def _log(self, texto):
        self.log.configure(state="normal")
        self.log.insert("end", texto + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def _refrescar(self):
        m = fn.mascota

        self.lbl_avatar.configure(text=obtener_avatar())
        self.lbl_expresion.configure(text=fn.obtener_expresion())
        self.lbl_meta.configure(text=obtener_texto_meta())

        for clave in ("salud", "felicidad", "comida", "energia"):
            valor = m[clave]
            self.barras[clave]["value"] = valor
            self.valores[clave].configure(text=f"{valor}/100")
            estilo = clave.capitalize() if clave != "energia" else "Energia"
            self.estilo.configure(
                f"{estilo}.Horizontal.TProgressbar",
                background=color_segun_valor(valor)
            )

        self.lbl_horas.configure(
            text=(f"🕐 Horas sin cuidado: {m['horas_sin_cuidado']}   "
                  f"💕 Horas sin cariño: {m['horas_sin_carino']}")
        )

        if not m["viva"]:
            for boton in self.botones_accion:
                boton.configure(state="disabled")
            self.btn_hablar.configure(state="disabled")
            self.entrada.configure(state="disabled")

    def _procesar_cola(self):
        hubo_mensajes = False
        try:
            while True:
                texto = cola_salida.cola.get_nowait()
                self.log.configure(state="normal")
                self.log.insert("end", texto)
                self.log.configure(state="disabled")
                hubo_mensajes = True
        except queue.Empty:
            pass
        if hubo_mensajes:
            self.log.see("end")
        self._refrescar()
        self.root.after(150, self._procesar_cola)


# =====================================================================
# PUNTO DE ENTRADA
# =====================================================================
if __name__ == "__main__":
    ventana_raiz = tk.Tk()
    app = VentanaMichi(ventana_raiz)
    ventana_raiz.mainloop()
