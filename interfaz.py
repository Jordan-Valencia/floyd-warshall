"""Interfaz grafica del proyecto de Floyd-Warshall.

Diseno de tres zonas (diseno "A" aprobado):

* Panel izquierdo: creacion y edicion de la red, archivo, vista y ayuda.
* Zona central: lienzo con la representacion grafica de la red dirigida.
* Panel derecho: visor de matrices (distancias / recorridos) con un control
  paso a paso que recorre la matriz inicial y cada iteracion k del algoritmo.
* Barra inferior: consulta de la ruta minima entre un origen y un destino.

Toda la interaccion con el algoritmo pasa por ``floyd.py``; este modulo solo se
ocupa de la presentacion, la animacion de las iteraciones y la validacion de
los datos ingresados.
"""

from __future__ import annotations

import string
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from floyd import ResultadoFloyd, floyd_warshall, formatear
from grafo import Arco, ErrorGrafo, Grafo, Nodo

# ---------------------------------------------------------------------------
# Paleta y medidas
# ---------------------------------------------------------------------------
FONDO = "#eef2f7"
FONDO_PANEL = "#f8fafc"
TARJETA = "#ffffff"
CABECERA = "#111827"
CABECERA_TXT = "#f8fafc"
TEXTO = "#0f172a"
TEXTO_SUAVE = "#64748b"
BORDE = "#cbd5e1"

LIENZO_FONDO = "#ffffff"
REJILLA = "#eef2f7"

NODO_RELLENO = "#ffffff"
NODO_BORDE = "#334155"
NODO_ORIGEN = "#2563eb"
NODO_ORIGEN_BORDE = "#1d4ed8"
NODO_DESTINO = "#dc2626"
NODO_DESTINO_BORDE = "#991b1b"
NODO_INTERMEDIO = "#f59e0b"
NODO_INTERMEDIO_BORDE = "#b45309"
NODO_RUTA = "#7c3aed"
NODO_RUTA_BORDE = "#5b21b6"
NODO_INALCANZABLE = "#e2e8f0"
NODO_INALCANZABLE_BORDE = "#94a3b8"

ARCO = "#94a3b8"
ARCO_RUTA = "#7c3aed"

ACENTO = "#2563eb"
ACENTO_HOVER = "#1d4ed8"
ACENTO_2 = "#0d9488"
ACENTO_2_HOVER = "#0f766e"
PELIGRO = "#dc2626"
PELIGRO_HOVER = "#b91c1c"
NEUTRO = "#475569"
NEUTRO_HOVER = "#334155"
MEJORA_FONDO = "#bbf7d0"
MEJORA_TEXTO = "#166534"
INF_TEXTO = "#b91c1c"
DIAGONAL_FONDO = "#e2e8f0"

RADIO_NODO = 24
ANCHO_ARCO = 2
ANCHO_ARCO_RUTA = 5
SEPARACION_ARCOS = 18
UMBRAL_ARRASTRE = 6
REJILLA_PASO = 28
ZOOM_MIN = 0.35
ZOOM_MAX = 3.0
ZOOM_PASO = 1.2

AYUDA = (
    "Doble clic en area vacia: nuevo nodo\n"
    "Arrastre de un nodo a otro: nuevo arco\n"
    "Doble clic en un nodo: fijar origen de la consulta\n"
    "Mayus + doble clic en un nodo: fijar destino\n"
    "Clic en un arco: seleccionarlo / editar peso\n"
    "Clic derecho: eliminar nodo o arco\n"
    "Rueda del raton: acercar / alejar\n"
    "Flechas: mover nodo  |  Supr: borrar"
)


class AplicacionFloyd:
    """Ventana principal del software."""

    def __init__(self, raiz: tk.Tk):
        self.raiz = raiz
        self.raiz.title("Floyd-Warshall - Caminos minimos entre todos los pares")
        self.raiz.geometry("1360x860")
        self.raiz.minsize(1120, 720)
        self.raiz.configure(bg=FONDO)

        self.grafo = Grafo()
        self.velocidad = tk.IntVar(value=750)

        # Estado del algoritmo y de la visualizacion.
        self.resultado: ResultadoFloyd | None = None
        self.iteraciones: list = []
        self.indice_iter = 0
        self.modo_matriz = "distancias"

        self.nodo_seleccionado: Nodo | None = None
        self.arco_seleccionado: Arco | None = None
        self.nodo_origen_consulta: Nodo | None = None
        self.nodo_destino_consulta: Nodo | None = None
        self.arcos_consulta: set[int] = set()
        self.nodos_consulta: set[int] = set()
        self.nodo_intermedio_actual: Nodo | None = None

        self._generador_anim = None
        self._id_after = None
        self._animando = False
        self._ignorar_escala = False

        self._presionado: Nodo | None = None
        self._origen_arrastre: Nodo | None = None
        self._destino_arrastre: Nodo | None = None
        self._pos_presion = (0.0, 0.0)
        self._pos_presion_actual = (0.0, 0.0)
        self._movido = False
        self._id_previsualizacion = None
        self._origen_pos = None

        self.zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0

        self.fuente = "Segoe UI"
        self.fuente_mono = "Consolas"
        self.celdas_matriz: list = []

        self._construir_widgets()
        self._enlazar_eventos()
        self.actualizar_estado()
        self.pintar()

    # ==================================================================
    # Construccion de la interfaz
    # ==================================================================
    def _construir_widgets(self) -> None:
        self._construir_cabecera()
        self._construir_franja_estado()

        cuerpo = tk.Frame(self.raiz, bg=FONDO)
        cuerpo.pack(side=tk.TOP, fill=tk.BOTH, expand=True)

        self._construir_panel_izquierdo(cuerpo)
        self._construir_panel_derecho(cuerpo)
        self._construir_lienzo(cuerpo)
        self._construir_pie(cuerpo)

    def _construir_cabecera(self) -> None:
        cabecera = tk.Frame(self.raiz, bg=CABECERA, padx=18, pady=12)
        cabecera.pack(side=tk.TOP, fill=tk.X)

        izquierda = tk.Frame(cabecera, bg=CABECERA)
        izquierda.pack(side=tk.LEFT)
        tk.Label(
            izquierda, text="Floyd-Warshall", bg=CABECERA, fg=CABECERA_TXT,
            font=(self.fuente, 19, "bold"),
        ).pack(side=tk.LEFT)
        tk.Label(
            izquierda, text="Caminos minimos entre todos los pares de nodos",
            bg=CABECERA, fg="#94a3b8", font=(self.fuente, 11),
        ).pack(side=tk.LEFT, padx=(12, 0), pady=6)

        derecha = tk.Frame(cabecera, bg=CABECERA)
        derecha.pack(side=tk.RIGHT)
        self.boton_ejecutar = self._boton(
            derecha, "\u25b6  Ejecutar", self.ejecutar, ACENTO, ACENTO_HOVER,
            "white", grande=True,
        )
        self.boton_reproducir = self._boton(
            derecha, "\u25b6\u25b6  Iteraciones", self.reproducir_iteraciones,
            ACENTO_2, ACENTO_2_HOVER, "white", grande=True,
        )
        self.boton_detener = self._boton(
            derecha, "\u25a0  Detener", self.detener_animacion, NEUTRO,
            NEUTRO_HOVER, "white", grande=True,
        )

    def _construir_franja_estado(self) -> None:
        franja = tk.Frame(self.raiz, bg=TARJETA, padx=18, pady=8,
                          highlightthickness=1, highlightbackground=BORDE)
        franja.pack(side=tk.TOP, fill=tk.X)
        self.etiqueta_estado = tk.Label(
            franja, text="Doble clic en el lienzo para crear el primer nodo.",
            bg=TARJETA, fg=TEXTO, font=(self.fuente, 10), anchor="w",
        )
        self.etiqueta_estado.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.etiqueta_zoom = tk.Label(
            franja, text="Zoom: 100%", bg=TARJETA, fg=TEXTO_SUAVE,
            font=(self.fuente, 9), anchor="e", padx=10,
        )
        self.etiqueta_zoom.pack(side=tk.RIGHT)

        self.etiqueta_info = tk.Label(
            franja, text="Nodos: 0   Arcos: 0", bg=TARJETA, fg=TEXTO_SUAVE,
            font=(self.fuente, 9, "bold"), anchor="e", padx=10,
        )
        self.etiqueta_info.pack(side=tk.RIGHT)

    def _boton(self, padre, texto, comando, color=ACENTO, hover=ACENTO_HOVER,
               fg="white", grande=False, fill=tk.NONE, padx=0, pady=0,
               alineacion="center", lado=None, expandir=False):
        """Boton plano con estados de hover/deshabilitado (reutilizable)."""
        marco = tk.Frame(padre, bg=color, cursor="hand2")
        etiqueta = tk.Label(
            marco, text=texto, bg=color, fg=fg,
            font=(self.fuente, 10 if grande else 9, "bold" if grande else "normal"),
            padx=14 if grande else 11, pady=8 if grande else 7,
            cursor="hand2", anchor=alineacion,
        )
        etiqueta.pack(fill=tk.BOTH, expand=True)
        if lado is not None:
            marco.pack(side=lado, fill=fill, expand=expandir, padx=padx, pady=pady)
        elif fill is not tk.NONE or padx or pady:
            marco.pack(fill=fill, padx=padx, pady=pady)
        else:
            marco.pack(side=tk.LEFT, padx=(0, 8))

        activo = {"on": True}

        def entrar(_e=None):
            if activo["on"]:
                marco.configure(bg=hover)
                etiqueta.configure(bg=hover)

        def salir(_e=None):
            if activo["on"]:
                marco.configure(bg=color)
                etiqueta.configure(bg=color)

        def soltar(_e=None):
            if activo["on"]:
                salir()
                comando()

        for widget in (marco, etiqueta):
            widget.bind("<Button-1>", lambda _e: entrar())
            widget.bind("<ButtonRelease-1>", soltar)
            widget.bind("<Enter>", entrar)
            widget.bind("<Leave>", salir)

        marco._etiqueta = etiqueta
        marco._color = color
        marco._hover = hover
        marco._fg = fg
        marco._activo = activo
        return marco

    # ------------------------------------------------------------------
    # Panel izquierdo
    # ------------------------------------------------------------------
    def _construir_panel_izquierdo(self, contenedor) -> None:
        marco = tk.Frame(contenedor, bg=BORDE, width=290)
        marco.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 1), pady=10)
        marco.pack_propagate(False)

        self._lienzo_panel = tk.Canvas(marco, bg=FONDO_PANEL,
                                       highlightthickness=0, width=288)
        self._scroll_panel = ttk.Scrollbar(marco, orient=tk.VERTICAL,
                                           command=self._lienzo_panel.yview)
        self._scroll_panel.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 2))
        self._lienzo_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        self._lienzo_panel.configure(yscrollcommand=self._scroll_panel.set)

        panel = tk.Frame(self._lienzo_panel, bg=FONDO_PANEL)
        self._ventana_panel = self._lienzo_panel.create_window(
            (0, 0), window=panel, anchor="nw")
        panel.bind(
            "<Configure>",
            lambda _e: self._lienzo_panel.configure(
                scrollregion=self._lienzo_panel.bbox("all")))
        self._lienzo_panel.bind(
            "<Configure>",
            lambda e: self._lienzo_panel.itemconfigure(self._ventana_panel, width=e.width))

        for widget in (self._lienzo_panel, panel):
            widget.bind("<Enter>", lambda _e: self._activar_rueda(True))
            widget.bind("<Leave>", lambda _e: self._activar_rueda(False))
        self.raiz.bind("<MouseWheel>", self._rueda, add="+")

        self._construir_panel_interior(panel)

    def _activar_rueda(self, activo: bool) -> None:
        self._rueda_activa = activo

    def _rueda(self, evento) -> None:
        if getattr(self, "_rueda_activa", False):
            self._lienzo_panel.yview_scroll(-1 * (evento.delta // 120), "units")

    def _construir_panel_interior(self, panel) -> None:
        def seccion(titulo: str) -> None:
            tk.Frame(panel, bg=BORDE, height=1).pack(fill=tk.X, padx=14, pady=6)
            tk.Label(panel, text=titulo.upper(), bg=FONDO_PANEL, fg=TEXTO_SUAVE,
                     font=(self.fuente, 8, "bold"), anchor="w").pack(
                fill=tk.X, padx=14)

        def boton(texto, comando, color=TARJETA, fg=TEXTO, hover="#e2e8f0"):
            return self._boton(panel, texto, comando, color, hover, fg,
                               fill=tk.X, padx=14, pady=1, alineacion="w")

        seccion("Red actual")
        self.etiqueta_red = tk.Label(
            panel, text="Sin nodos", bg=FONDO_PANEL, fg=TEXTO_SUAVE,
            font=(self.fuente, 10, "bold"), anchor="w", wraplength=250)
        self.etiqueta_red.pack(fill=tk.X, padx=14)

        seccion("Seleccion")
        self.etiqueta_seleccion_panel = tk.Label(
            panel, text="Nada seleccionado", bg=FONDO_PANEL, fg=TEXTO_SUAVE,
            font=(self.fuente, 9), anchor="w", wraplength=250, justify="left")
        self.etiqueta_seleccion_panel.pack(fill=tk.X, padx=14)

        seccion("Edicion")
        self.boton_renombrar = boton("Renombrar nodo", self.renombrar_nodo)
        self.boton_peso = boton("Modificar peso del arco", self.modificar_peso)
        self.boton_eliminar_arco = boton("Eliminar arco", self.eliminar_arco)
        self.boton_eliminar_nodo = boton("Eliminar nodo y sus arcos", self.eliminar_nodo)

        seccion("Ejecucion")
        self.boton_ver_inicial = boton("Ver matriz inicial", lambda: self.ir_a_iteracion(0))
        self.boton_ver_final = boton("Ver matriz final", self.ver_matriz_final)
        self.boton_anterior = boton("\u25c0  Iteracion anterior", self.iteracion_anterior)
        self.boton_siguiente = boton("Iteracion siguiente  \u25b6", self.iteracion_siguiente)

        seccion("Animacion")
        marco_velocidad = tk.Frame(panel, bg=FONDO_PANEL)
        marco_velocidad.pack(fill=tk.X, padx=14)
        tk.Label(marco_velocidad, text="Lenta", bg=FONDO_PANEL, fg=TEXTO_SUAVE,
                 font=(self.fuente, 8)).pack(side=tk.LEFT)
        tk.Label(marco_velocidad, text="Rapida", bg=FONDO_PANEL, fg=TEXTO_SUAVE,
                 font=(self.fuente, 8)).pack(side=tk.RIGHT)
        tk.Scale(panel, from_=1600, to=100, orient=tk.HORIZONTAL,
                 variable=self.velocidad, length=250, sliderrelief="flat",
                 bg=FONDO_PANEL, highlightthickness=0, bd=0,
                 command=lambda _v: self._reprogramar_animacion()).pack(
            fill=tk.X, padx=12, pady=6)

        seccion("Vista")
        fila_zoom = tk.Frame(panel, bg=FONDO_PANEL)
        fila_zoom.pack(fill=tk.X, padx=12, pady=1)
        self._boton(fila_zoom, "\u2212", self.alejar, TARJETA, "#e2e8f0", TEXTO,
                    fill=tk.X, padx=(0, 2), lado=tk.LEFT, expandir=True)
        self._boton(fila_zoom, "100%", self.restablecer_zoom, TARJETA, "#e2e8f0",
                    TEXTO, fill=tk.X, padx=2, lado=tk.LEFT, expandir=True)
        self._boton(fila_zoom, "+", self.acercar, TARJETA, "#e2e8f0", TEXTO,
                    fill=tk.X, padx=(2, 0), lado=tk.LEFT, expandir=True)

        seccion("Archivo")
        boton("Cargar red de ejemplo", self.cargar_ejemplo)
        boton("Exportar matrices (CSV)", self.exportar_csv)
        boton("Nueva red (vaciar)", self.nueva_red, TARJETA, PELIGRO, "#fee2e2")

        seccion("Ayuda")
        tk.Label(panel, text=AYUDA, bg=FONDO_PANEL, fg=TEXTO_SUAVE,
                 font=(self.fuente, 8), anchor="w", justify="left").pack(
            fill=tk.X, padx=14, pady=(0, 10))

    # ------------------------------------------------------------------
    # Panel derecho (visor de matrices)
    # ------------------------------------------------------------------
    def _construir_panel_derecho(self, contenedor) -> None:
        tarjeta = tk.Frame(contenedor, bg=TARJETA, width=486,
                           highlightthickness=1, highlightbackground=BORDE)
        tarjeta.pack(side=tk.RIGHT, fill=tk.Y, padx=(0, 10), pady=10)
        tarjeta.pack_propagate(False)

        tk.Label(tarjeta, text="MATRICES DEL ALGORITMO", bg=TARJETA, fg=TEXTO_SUAVE,
                 font=(self.fuente, 8, "bold"), anchor="w", padx=12, pady=8).pack(
            fill=tk.X)

        # Pestanas distancias / recorridos
        pestanas = tk.Frame(tarjeta, bg=TARJETA)
        pestanas.pack(fill=tk.X, padx=12)
        self.boton_modo_distancias = self._boton(
            pestanas, "Distancias", lambda: self.cambiar_modo("distancias"),
            ACENTO, ACENTO_HOVER, "white", fill=tk.X, padx=(0, 3),
            lado=tk.LEFT, expandir=True)
        self.boton_modo_recorridos = self._boton(
            pestanas, "Recorridos", lambda: self.cambiar_modo("recorridos"),
            "#e2e8f0", "#cbd5e1", TEXTO, fill=tk.X, padx=(3, 0),
            lado=tk.LEFT, expandir=True)

        # Control de iteraciones
        control = tk.Frame(tarjeta, bg=TARJETA)
        control.pack(fill=tk.X, padx=12, pady=(10, 0))
        self._boton(control, "\u25c0", self.iteracion_anterior, "#e2e8f0",
                    "#cbd5e1", TEXTO, lado=tk.LEFT, padx=(0, 4))
        self._boton(control, "\u25b6", self.iteracion_siguiente, "#e2e8f0",
                    "#cbd5e1", TEXTO, lado=tk.RIGHT, padx=(4, 0))
        self.etiqueta_iteracion = tk.Label(
            control, text="Sin ejecutar", bg=TARJETA, fg=TEXTO,
            font=(self.fuente, 10, "bold"))
        self.etiqueta_iteracion.pack(side=tk.LEFT, fill=tk.X, expand=True)

        self.escala_iter = tk.Scale(
            tarjeta, from_=0, to=1, orient=tk.HORIZONTAL, resolution=1,
            showvalue=0, state=tk.DISABLED, bg=TARJETA, highlightthickness=0,
            bd=0, sliderrelief="flat", command=lambda v: self.ir_a_iteracion(int(float(v))),
        )
        self.escala_iter.pack(fill=tk.X, padx=12)

        self.descripcion_iteracion = tk.Label(
            tarjeta, text="Ejecute el algoritmo para ver las matrices.",
            bg=TARJETA, fg=TEXTO_SUAVE, font=(self.fuente, 9),
            anchor="w", justify="left", wraplength=460, padx=12, pady=4)
        self.descripcion_iteracion.pack(fill=tk.X)

        # Leyenda
        leyenda = tk.Frame(tarjeta, bg=TARJETA)
        leyenda.pack(fill=tk.X, padx=12)
        tk.Label(leyenda, text=" ", bg=MEJORA_FONDO, padx=6).pack(side=tk.LEFT)
        tk.Label(leyenda, text="celda mejorada en esta iteraci\u00f3n",
                 bg=TARJETA, fg=TEXTO_SUAVE, font=(self.fuente, 8)).pack(
            side=tk.LEFT, padx=(4, 12))
        tk.Label(leyenda, text="\u221e", bg=TARJETA, fg=INF_TEXTO,
                 font=(self.fuente, 9, "bold")).pack(side=tk.LEFT)
        tk.Label(leyenda, text="sin conexion", bg=TARJETA, fg=TEXTO_SUAVE,
                 font=(self.fuente, 8)).pack(side=tk.LEFT, padx=(4, 0))

        # Contenedor de la matriz
        contenedor_matriz = tk.Frame(tarjeta, bg=TARJETA)
        contenedor_matriz.pack(fill=tk.BOTH, expand=True, padx=12, pady=8)
        self._lienzo_matriz = tk.Canvas(contenedor_matriz, bg=TARJETA,
                                        highlightthickness=0)
        scroll_y = ttk.Scrollbar(contenedor_matriz, orient=tk.VERTICAL,
                                 command=self._lienzo_matriz.yview)
        scroll_x = ttk.Scrollbar(contenedor_matriz, orient=tk.HORIZONTAL,
                                 command=self._lienzo_matriz.xview)
        self._lienzo_matriz.configure(yscrollcommand=scroll_y.set,
                                      xscrollcommand=scroll_x.set)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        self._lienzo_matriz.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.contenedor_matriz = tk.Frame(self._lienzo_matriz, bg=TARJETA)
        self._ventana_matriz = self._lienzo_matriz.create_window(
            (0, 0), window=self.contenedor_matriz, anchor="nw")
        self.contenedor_matriz.bind(
            "<Configure>",
            lambda _e: self._lienzo_matriz.configure(
                scrollregion=self._lienzo_matriz.bbox("all")))

    # ------------------------------------------------------------------
    # Lienzo central
    # ------------------------------------------------------------------
    def _construir_lienzo(self, contenedor) -> None:
        marco = tk.Frame(contenedor, bg=BORDE, padx=1, pady=1)
        marco.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(10, 0), pady=10)
        self.lienzo = tk.Canvas(marco, bg=LIENZO_FONDO, highlightthickness=0,
                                cursor="crosshair")
        self.lienzo.pack(fill=tk.BOTH, expand=True)
        self.lienzo.bind("<Configure>", lambda _e: self.pintar())

    # ------------------------------------------------------------------
    # Barra inferior: consulta de ruta
    # ------------------------------------------------------------------
    def _construir_pie(self, contenedor) -> None:
        pie = tk.Frame(self.raiz, bg=FONDO)
        pie.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=(0, 8))

        tarjeta = tk.Frame(pie, bg=TARJETA, highlightthickness=1,
                           highlightbackground=BORDE, padx=12, pady=8)
        tarjeta.pack(fill=tk.X)

        fila = tk.Frame(tarjeta, bg=TARJETA)
        fila.pack(fill=tk.X)

        tk.Label(fila, text="CONSULTA DE RUTA", bg=TARJETA, fg=TEXTO_SUAVE,
                 font=(self.fuente, 8, "bold")).pack(side=tk.LEFT, padx=(0, 12))

        tk.Label(fila, text="Origen:", bg=TARJETA, fg=TEXTO,
                 font=(self.fuente, 10)).pack(side=tk.LEFT)
        self.combo_origen = ttk.Combobox(fila, state="readonly", width=10,
                                         font=(self.fuente, 10))
        self.combo_origen.pack(side=tk.LEFT, padx=(4, 8))

        tk.Label(fila, text="\u2192", bg=TARJETA, fg=TEXTO,
                 font=(self.fuente, 12, "bold")).pack(side=tk.LEFT)

        tk.Label(fila, text="Destino:", bg=TARJETA, fg=TEXTO,
                 font=(self.fuente, 10)).pack(side=tk.LEFT, padx=(8, 0))
        self.combo_destino = ttk.Combobox(fila, state="readonly", width=10,
                                          font=(self.fuente, 10))
        self.combo_destino.pack(side=tk.LEFT, padx=(4, 8))

        self.boton_consultar = self._boton(
            fila, "Consultar ruta", self.consultar_ruta, ACENTO_2,
            ACENTO_2_HOVER, "white")

        self.etiqueta_consulta = tk.Label(
            fila, text="Ejecute el algoritmo y elija un origen y un destino.",
            bg=TARJETA, fg=TEXTO_SUAVE, font=(self.fuente, 10),
            anchor="w", justify="left")
        self.etiqueta_consulta.pack(side=tk.LEFT, fill=tk.X, expand=True,
                                    padx=(14, 0))

    # ==================================================================
    # Eventos
    # ==================================================================
    def _enlazar_eventos(self) -> None:
        self.lienzo.bind("<Double-Button-1>", self.doble_clic)
        self.lienzo.bind("<Button-3>", self.clic_derecho)
        self.lienzo.bind("<ButtonPress-1>", self.presionar)
        self.lienzo.bind("<B1-Motion>", self.arrastrar)
        self.lienzo.bind("<ButtonRelease-1>", self.soltar)
        self.lienzo.bind("<Motion>", self.mover_raton)
        self.lienzo.bind("<MouseWheel>", self._rueda_lienzo)
        self.raiz.bind("<Delete>", lambda _e: self.eliminar_seleccion())
        self.raiz.bind("<Escape>", lambda _e: self.detener_animacion())
        for flecha in ("Left", "Right", "Up", "Down"):
            self.raiz.bind(f"<{flecha}>", lambda _e, f=flecha: self.desplazar(f))
        for secuencia in ("<plus>", "<equal>", "<KP_Add>"):
            self.raiz.bind(secuencia, lambda _e: self.acercar())
        for secuencia in ("<minus>", "<KP_Subtract>"):
            self.raiz.bind(secuencia, lambda _e: self.alejar())
        self.raiz.bind("<Key-0>", lambda _e: self.restablecer_zoom())
        self.raiz.protocol("WM_DELETE_WINDOW", self.cerrar)

    # ==================================================================
    # Zoom
    # ==================================================================
    def _a_pantalla(self, x, y):
        return (x - self._pan_x) * self.zoom, (y - self._pan_y) * self.zoom

    def _a_modelo(self, x, y):
        return x / self.zoom + self._pan_x, y / self.zoom + self._pan_y

    def _actualizar_zoom_label(self) -> None:
        if hasattr(self, "etiqueta_zoom"):
            self.etiqueta_zoom.config(text=f"Zoom: {round(self.zoom * 100)}%")

    def _reset_vista(self) -> None:
        self.zoom = 1.0
        self._pan_x = 0.0
        self._pan_y = 0.0
        self._actualizar_zoom_label()

    def _aplicar_zoom(self, nuevo, foco=None) -> None:
        nuevo = max(ZOOM_MIN, min(ZOOM_MAX, nuevo))
        if abs(nuevo - self.zoom) < 1e-9:
            return
        if foco is None:
            foco = (self.lienzo.winfo_width() / 2, self.lienzo.winfo_height() / 2)
        mx, my = self._a_modelo(foco[0], foco[1])
        self.zoom = nuevo
        self._pan_x = mx - foco[0] / self.zoom
        self._pan_y = my - foco[1] / self.zoom
        self._actualizar_zoom_label()
        self.pintar()

    def acercar(self, foco=None) -> None:
        self._aplicar_zoom(self.zoom * ZOOM_PASO, foco)

    def alejar(self, foco=None) -> None:
        self._aplicar_zoom(self.zoom / ZOOM_PASO, foco)

    def restablecer_zoom(self) -> None:
        self._reset_vista()
        self.pintar()

    def _rueda_lienzo(self, evento) -> str:
        factor = ZOOM_PASO if evento.delta > 0 else 1.0 / ZOOM_PASO
        self._aplicar_zoom(self.zoom * factor, (evento.x, evento.y))
        return "break"

    # ==================================================================
    # Dibujo del lienzo
    # ==================================================================
    def _pintar_rejilla(self) -> None:
        ancho, alto = self.lienzo.winfo_width(), self.lienzo.winfo_height()
        if ancho < 2 or alto < 2:
            return
        paso = REJILLA_PASO * self.zoom
        if paso < 6:
            return
        x = (-self._pan_x * self.zoom) % paso
        while x < ancho:
            self.lienzo.create_line(x, 0, x, alto, fill=REJILLA)
            x += paso
        y = (-self._pan_y * self.zoom) % paso
        while y < alto:
            self.lienzo.create_line(0, y, ancho, y, fill=REJILLA)
            y += paso

    def _posiciones_arcos(self) -> dict[int, dict[str, float]]:
        posiciones: dict[int, dict[str, float]] = {}
        for arco in self.grafo.arcos:
            ax, ay = arco.origen.x, arco.origen.y
            bx, by = arco.destino.x, arco.destino.y
            dx, dy = bx - ax, by - ay
            largo = max((dx * dx + dy * dy) ** 0.5, 1e-6)
            ux, uy = dx / largo, dy / largo

            inverso = self.grafo.buscar_arco(arco.destino, arco.origen)
            lado = 1 if inverso is None else (1 if id(arco) < id(inverso) else -1)

            recorte = max(min(RADIO_NODO + 3, largo / 2 - 1), 0.0)
            axp, ayp = ax + ux * recorte, ay + uy * recorte
            bxp, byp = bx - ux * recorte, by - uy * recorte

            x_medio = (axp + bxp) / 2 + (-uy) * SEPARACION_ARCOS * lado
            y_medio = (ayp + byp) / 2 + ux * SEPARACION_ARCOS * lado
            posiciones[id(arco)] = {
                "ax": axp, "ay": ayp, "bx": bxp, "by": byp,
                "mx": x_medio, "my": y_medio,
            }
        return posiciones

    def pintar(self) -> None:
        self.lienzo.delete("all")
        self._pintar_rejilla()
        posiciones = self._posiciones_arcos()

        for arco in self.grafo.arcos:
            self._pintar_arco(arco, posiciones[id(arco)], id(arco) in self.arcos_consulta)

        for nodo in self.grafo.nodos.values():
            self._pintar_nodo(nodo)

        self._pintar_previsualizacion()

    def _pintar_arco(self, arco, pos, es_consulta: bool) -> None:
        z = self.zoom
        if es_consulta:
            color, ancho = ARCO_RUTA, ANCHO_ARCO_RUTA
        elif self.arco_seleccionado is arco:
            color, ancho = TEXTO, ANCHO_ARCO + 2
        else:
            color, ancho = ARCO, ANCHO_ARCO

        ax, ay = self._a_pantalla(pos["ax"], pos["ay"])
        bx, by = self._a_pantalla(pos["bx"], pos["by"])
        self.lienzo.create_line(
            ax, ay, bx, by, fill=color, width=max(1, int(round(ancho * z))),
            arrow=tk.LAST,
            arrowshape=(max(1, int(11 * z)), max(1, int(12 * z)), max(1, int(5 * z))),
        )

        mx, my = self._a_pantalla(pos["mx"], pos["my"])
        ancho_caja = max(9.0, 19 * z)
        alto_caja = max(7.0, 10 * z)
        self.lienzo.create_rectangle(
            mx - ancho_caja, my - alto_caja, mx + ancho_caja, my + alto_caja,
            fill="white", outline=color if es_consulta else BORDE,
        )
        self.lienzo.create_text(
            mx, my, text=f"{arco.peso:g}", fill=color,
            font=(self.fuente, max(7, round(9 * z)), "bold"),
        )

    def _estilo_nodo(self, nodo: Nodo):
        if self.nodo_origen_consulta is nodo:
            return NODO_ORIGEN, NODO_ORIGEN_BORDE, "white"
        if self.nodo_destino_consulta is nodo:
            return NODO_DESTINO, NODO_DESTINO_BORDE, "white"
        if nodo.id in self.nodos_consulta:
            return NODO_RUTA, NODO_RUTA_BORDE, "white"
        if self.nodo_intermedio_actual is nodo:
            return NODO_INTERMEDIO, NODO_INTERMEDIO_BORDE, "white"
        return NODO_RELLENO, NODO_BORDE, TEXTO

    def _pintar_nodo(self, nodo: Nodo, inalcanzable: bool = False) -> None:
        z = self.zoom
        x, y = self._a_pantalla(nodo.x, nodo.y)
        r = RADIO_NODO * z
        tag = (f"nodo_{nodo.id}",)

        self.lienzo.create_oval(
            x - r + 2 * z, y - r + 3 * z, x + r + 2 * z, y + r + 3 * z,
            fill="#e2e8f0", outline="", tags=tag)

        relleno, borde, texto = self._estilo_nodo(nodo)
        self.lienzo.create_oval(
            x - r, y - r, x + r, y + r, fill=relleno, outline=borde,
            width=max(1, int(round(3 * z))), tags=tag)
        self.lienzo.create_text(
            x, y - 3 * z, text=nodo.nombre, fill=texto,
            font=(self.fuente, max(7, round(11 * z)), "bold"), tags=tag)

        if nodo is self.nodo_seleccionado:
            self.lienzo.create_oval(
                x - r - 6 * z, y - r - 6 * z, x + r + 6 * z, y + r + 6 * z,
                outline=ACENTO, width=max(1, int(round(2 * z))),
                dash=(max(2, round(5 * z)), max(2, round(3 * z))), tags=tag)

    def _pintar_previsualizacion(self) -> None:
        if self._id_previsualizacion is None or self._origen_arrastre is None:
            return
        self.lienzo.delete(self._id_previsualizacion)
        destino = self._destino_arrastre
        x2, y2 = (destino.x, destino.y) if destino else self._pos_presion_actual
        ox, oy = self._a_pantalla(self._origen_arrastre.x, self._origen_arrastre.y)
        px, py = self._a_pantalla(x2, y2)
        z = self.zoom
        self._id_previsualizacion = self.lienzo.create_line(
            ox, oy, px, py, fill=ACENTO, width=max(1, int(round(2 * z))),
            dash=(max(2, round(6 * z)), max(2, round(4 * z))))

    # ==================================================================
    # Interaccion con el lienzo
    # ==================================================================
    def nodo_en(self, x: float, y: float) -> Nodo | None:
        for nodo in self.grafo.nodos.values():
            if (nodo.x - x) ** 2 + (nodo.y - y) ** 2 <= (RADIO_NODO + 4) ** 2:
                return nodo
        return None

    def arco_en(self, x: float, y: float, tolerancia: float | None = None) -> Arco | None:
        if tolerancia is None:
            tolerancia = 9.0 / self.zoom
        mejor, mejor_distancia = None, tolerancia
        for arco in self.grafo.arcos:
            distancia = self.distancia_al_segmento(
                x, y, arco.origen.x, arco.origen.y, arco.destino.x, arco.destino.y)
            if distancia < mejor_distancia:
                mejor, mejor_distancia = arco, distancia
        return mejor

    @staticmethod
    def distancia_al_segmento(px, py, x1, y1, x2, y2) -> float:
        dx, dy = x2 - x1, y2 - y1
        if dx == 0 and dy == 0:
            return ((px - x1) ** 2 + (py - y1) ** 2) ** 0.5
        t = max(0.0, min(1.0, ((px - x1) * dx + (py - y1) * dy) / (dx * dx + dy * dy)))
        return ((px - (x1 + t * dx)) ** 2 + (py - (y1 + t * dy)) ** 2) ** 0.5

    def mover_raton(self, evento) -> None:
        mx, my = self._a_modelo(evento.x, evento.y)
        self._pos_presion_actual = (mx, my)
        if self._origen_arrastre is not None:
            self._destino_arrastre = self.nodo_en(mx, my)
            self._pintar_previsualizacion()

    def presionar(self, evento) -> None:
        if self._animando:
            self.informar("Animacion en curso. Detengala para editar la red.", "error")
            return
        mx, my = self._a_modelo(evento.x, evento.y)
        nodo = self.nodo_en(mx, my)
        self._presionado = nodo
        self._origen_arrastre = nodo
        self._origen_pos = (nodo.x, nodo.y) if nodo is not None else None
        self._destino_arrastre = None
        self._pos_presion = (mx, my)
        self._pos_presion_actual = (mx, my)
        self._movido = False

        if nodo is None:
            self.nodo_seleccionado = None
            self.arco_seleccionado = self.arco_en(mx, my)
            self.actualizar_estado()
            self.pintar()

    def arrastrar(self, evento) -> None:
        if self._presionado is None:
            return
        mx, my = self._a_modelo(evento.x, evento.y)
        self._pos_presion_actual = (mx, my)
        if not self._movido:
            alcance = max(abs(mx - self._pos_presion[0]), abs(my - self._pos_presion[1]))
            if alcance < UMBRAL_ARRASTRE / self.zoom:
                return
            self._movido = True

        destino = self.nodo_en(mx, my)
        self._destino_arrastre = destino
        if destino is not None:
            self._pintar_previsualizacion()
        else:
            self.lienzo.delete(self._id_previsualizacion or "")
            self._id_previsualizacion = None
            self._presionado.x = mx
            self._presionado.y = my
            self.pintar()

    def soltar(self, evento) -> None:
        origen, destino = self._origen_arrastre, self._destino_arrastre
        movido = self._movido
        self.lienzo.delete(self._id_previsualizacion or "")
        self._id_previsualizacion = None
        self._presionado = None
        self._origen_arrastre = None
        self._destino_arrastre = None
        self._movido = False

        if origen is None:
            if not movido and destino is None:
                self.nodo_seleccionado = None
                self.actualizar_estado()
            self.pintar()
            self._origen_pos = None
            return

        if movido and destino is not None and destino is not origen:
            if self._origen_pos is not None:
                origen.x, origen.y = self._origen_pos
            self._origen_pos = None
            self.crear_arco(origen, destino)
            return

        self._origen_pos = None
        if movido:
            self.limpiar_resultados(silencioso=True)
            self.actualizar_estado()
            self.pintar()
            return

        self.nodo_seleccionado = origen
        self.arco_seleccionado = None
        self.actualizar_estado()
        self.pintar()

    def doble_clic(self, evento) -> None:
        if self._animando:
            return
        mx, my = self._a_modelo(evento.x, evento.y)
        nodo = self.nodo_en(mx, my)
        if nodo is not None:
            if evento.state & 0x0001:  # Mayus pulsado
                self.fijar_destino(nodo)
            else:
                self.fijar_origen(nodo)
            return
        if self.arco_en(mx, my) is not None:
            return
        self.crear_nodo(mx, my)

    def clic_derecho(self, evento) -> None:
        if self._animando:
            self.informar("Animacion en curso. Detengala para editar la red.", "error")
            return
        mx, my = self._a_modelo(evento.x, evento.y)
        nodo = self.nodo_en(mx, my)
        if nodo is not None:
            self.eliminar_nodo(nodo)
            return
        arco = self.arco_en(mx, my)
        if arco is not None:
            self.eliminar_arco(arco)

    def desplazar(self, flecha: str) -> None:
        nodo = self.nodo_seleccionado
        if nodo is None or self._animando:
            return
        paso = 8 / self.zoom
        if flecha == "Left":
            nodo.x -= paso
        elif flecha == "Right":
            nodo.x += paso
        elif flecha == "Up":
            nodo.y -= paso
        else:
            nodo.y += paso
        self.limpiar_resultados(silencioso=True)
        self.pintar()

    # ==================================================================
    # Edicion de la red
    # ==================================================================
    def _nombre_automatico(self) -> str:
        usados = {n.nombre for n in self.grafo.nodos.values()}
        for letra in string.ascii_uppercase:
            if letra not in usados:
                return letra
        indice = 1
        while True:
            for letra in string.ascii_uppercase:
                candidato = f"{letra}{indice}"
                if candidato not in usados:
                    return candidato
            indice += 1

    def crear_nodo(self, x: float, y: float) -> None:
        try:
            nodo = self.grafo.agregar_nodo(self._nombre_automatico(), x, y)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        self.nodo_seleccionado = nodo
        self.arco_seleccionado = None
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Nodo '{nodo.nombre}' creado. Arrastre de el para crear un arco.", "ok")

    def crear_arco(self, origen: Nodo, destino: Nodo) -> None:
        peso = simpledialog.askstring(
            "Peso del arco",
            f"Peso del arco  {origen.nombre} \u2192 {destino.nombre}\n"
            "(Floyd exige un numero > 0):",
            parent=self.raiz)
        if peso is None:
            self.informar("Creacion de arco cancelada.", "info")
            self.pintar()
            return
        try:
            arco = self.grafo.agregar_arco(origen, destino, peso)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            self.pintar()
            return
        self.arco_seleccionado = arco
        self.nodo_seleccionado = None
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Arco creado: {arco.etiqueta()}.", "ok")

    def renombrar_nodo(self) -> None:
        nodo = self.nodo_seleccionado
        if nodo is None:
            self.informar("Seleccione primero un nodo.", "error")
            return
        nombre = simpledialog.askstring(
            "Renombrar nodo", "Nuevo nombre:", initialvalue=nodo.nombre,
            parent=self.raiz)
        if not nombre:
            return
        try:
            self.grafo.renombrar_nodo(nodo, nombre)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Nodo renombrado a '{nodo.nombre}'.", "ok")

    def modificar_peso(self) -> None:
        arco = self.arco_seleccionado
        if arco is None:
            self.informar("Seleccione primero un arco: haga clic sobre la linea.", "error")
            return
        peso = simpledialog.askstring(
            "Modificar peso",
            f"Nuevo peso del arco  {arco.origen.nombre} \u2192 {arco.destino.nombre}:",
            initialvalue=f"{arco.peso:g}", parent=self.raiz)
        if peso is None:
            return
        try:
            self.grafo.modificar_peso(arco, peso)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        self.limpiar_resultados(silencioso=True)
        self.pintar()
        self.informar(f"Peso actualizado: {arco.etiqueta()}.", "ok")

    def eliminar_arco(self, arco: Arco | None = None) -> None:
        arco = arco or self.arco_seleccionado
        if arco is None:
            self.informar("Seleccione primero un arco: haga clic sobre la linea.", "error")
            return
        etiqueta = arco.etiqueta()
        try:
            self.grafo.eliminar_arco(arco)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        self.arco_seleccionado = None
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Arco {etiqueta} eliminado.", "ok")

    def eliminar_nodo(self, nodo: Nodo | None = None) -> None:
        nodo = nodo or self.nodo_seleccionado
        if nodo is None:
            self.informar("Seleccione primero un nodo.", "error")
            return
        nombre = nodo.nombre
        try:
            self.grafo.eliminar_nodo(nodo)
        except ErrorGrafo as error:
            self.informar(str(error), "error")
            return
        for atributo in ("nodo_origen_consulta", "nodo_destino_consulta",
                         "nodo_seleccionado"):
            if getattr(self, atributo) is nodo:
                setattr(self, atributo, None)
        self.limpiar_resultados(silencioso=True)
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Nodo '{nombre}' eliminado junto con sus arcos.", "ok")

    def eliminar_seleccion(self) -> None:
        if self.arco_seleccionado is not None:
            self.eliminar_arco()
        elif self.nodo_seleccionado is not None:
            self.eliminar_nodo()

    def fijar_origen(self, nodo: Nodo) -> None:
        self.combo_origen.set(nodo.nombre)
        self.nodo_seleccionado = nodo
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Origen de la consulta: {nodo.nombre}.", "info")

    def fijar_destino(self, nodo: Nodo) -> None:
        self.combo_destino.set(nodo.nombre)
        self.nodo_seleccionado = nodo
        self.actualizar_estado()
        self.pintar()
        self.informar(f"Destino de la consulta: {nodo.nombre}.", "info")

    # ==================================================================
    # Ejecucion del algoritmo
    # ==================================================================
    def ejecutar(self) -> None:
        self.detener_animacion()
        try:
            self.resultado = floyd_warshall(self.grafo)
        except ErrorGrafo as error:
            self.resultado = None
            self.iteraciones = []
            self.pintar_matriz_vacia()
            self.informar(f"No se puede ejecutar Floyd-Warshall: {error}", "error")
            self.pintar()
            return

        self.iteraciones = self.resultado.iteraciones
        self.indice_iter = 0
        self.refrescar_combos()
        self._actualizar_controles_iteracion()
        self.pintar_matriz()
        self.actualizar_estado()
        self.pintar()
        alcanzables = len(self.resultado.nodos) * (len(self.resultado.nodos) - 1) - len(
            self.resultado.pares_inalcanzables())
        total = len(self.resultado.nodos) * (len(self.resultado.nodos) - 1)
        self.informar(
            f"Floyd-Warshall ejecutado: {len(self.resultado.nodos)} nodos, "
            f"{len(self.iteraciones) - 1} iteraciones. Pares alcanzables: "
            f"{alcanzables}/{total}.", "ok")

    def reproducir_iteraciones(self) -> None:
        self.detener_animacion()
        if self.resultado is None:
            self.ejecutar()
            if self.resultado is None:
                return
        self._animando = True
        self.indice_iter = 0
        self._mostrar_iteracion()
        self.actualizar_estado()
        self._id_after = self.raiz.after(max(self.velocidad.get(), 60), self._avanzar_animacion)

    def _avanzar_animacion(self) -> None:
        if not self._animando:
            return
        if self.indice_iter >= len(self.iteraciones) - 1:
            self._animando = False
            self._id_after = None
            self.actualizar_estado()
            self.informar("Iteraciones finalizadas. Esta es la matriz final.", "ok")
            return
        self.indice_iter += 1
        self._mostrar_iteracion()
        self._id_after = self.raiz.after(max(self.velocidad.get(), 60), self._avanzar_animacion)

    def _reprogramar_animacion(self) -> None:
        if self._animando and self._id_after is not None:
            self.raiz.after_cancel(self._id_after)
            self._id_after = self.raiz.after(
                max(self.velocidad.get(), 60), self._avanzar_animacion)

    def detener_animacion(self) -> None:
        self._animando = False
        if self._id_after is not None:
            try:
                self.raiz.after_cancel(self._id_after)
            except tk.TclError:
                pass
            self._id_after = None
        self.actualizar_estado()

    def ver_matriz_final(self) -> None:
        if self.iteraciones:
            self.ir_a_iteracion(len(self.iteraciones) - 1)

    def iteracion_siguiente(self) -> None:
        self.ir_a_iteracion(self.indice_iter + 1)

    def iteracion_anterior(self) -> None:
        self.ir_a_iteracion(self.indice_iter - 1)

    def ir_a_iteracion(self, indice: int) -> None:
        if self._ignorar_escala or not self.iteraciones:
            return
        indice = max(0, min(len(self.iteraciones) - 1, int(indice)))
        self.indice_iter = indice
        if self.escala_iter.cget("state") != tk.DISABLED:
            self._set_escala(indice)
        self._mostrar_iteracion()

    def _set_escala(self, valor: int) -> None:
        self._ignorar_escala = True
        try:
            self.escala_iter.set(valor)
        finally:
            self._ignorar_escala = False

    def _mostrar_iteracion(self) -> None:
        self.pintar_matriz()
        self.nodo_intermedio_actual = (
            self.iteraciones[self.indice_iter].nodo_intermedio
            if self.iteraciones else None)
        if self.iteraciones:
            self.informar(self.iteraciones[self.indice_iter].descripcion(), "info")
        self.pintar()

    def _actualizar_controles_iteracion(self) -> None:
        hay = bool(self.iteraciones)
        self.escala_iter.configure(
            state=tk.NORMAL if hay else tk.DISABLED,
            to=max(0, len(self.iteraciones) - 1))
        if hay:
            self._set_escala(self.indice_iter)

    # ==================================================================
    # Visor de matrices
    # ==================================================================
    def cambiar_modo(self, modo: str) -> None:
        self.modo_matriz = modo
        activo = (ACENTO, ACENTO_HOVER, "white")
        inactivo = ("#e2e8f0", "#cbd5e1", TEXTO)
        estilo_d = activo if modo == "distancias" else inactivo
        estilo_r = activo if modo == "recorridos" else inactivo
        self._reestilizar(self.boton_modo_distancias, estilo_d)
        self._reestilizar(self.boton_modo_recorridos, estilo_r)
        self.pintar_matriz()

    @staticmethod
    def _reestilizar(marco, estilo) -> None:
        color, hover, fg = estilo
        marco._color, marco._hover, marco._fg = color, hover, fg
        marco.configure(bg=color)
        marco._etiqueta.configure(bg=color, fg=fg)

    def pintar_matriz_vacia(self) -> None:
        for widget in self.contenedor_matriz.winfo_children():
            widget.destroy()
        self.celdas_matriz = []
        if hasattr(self, "etiqueta_iteracion"):
            self.etiqueta_iteracion.config(text="Sin ejecutar")
            self.descripcion_iteracion.config(
                text="Ejecute el algoritmo para ver las matrices.")
            self.escala_iter.configure(state=tk.DISABLED, to=0)
            self.escala_iter.set(0)

    def pintar_matriz(self) -> None:
        for widget in self.contenedor_matriz.winfo_children():
            widget.destroy()
        self.celdas_matriz = []

        if not self.iteraciones:
            return

        it = self.iteraciones[self.indice_iter]
        nodos = it.nodos
        n = len(nodos)
        self.etiqueta_iteracion.config(text=it.titulo())
        self.descripcion_iteracion.config(text=it.descripcion())

        mejoradas = {(c.i, c.j) for c in it.cambios}
        encabezado_bg = "#1e293b"
        encabezado_fg = "white"

        # Esquina
        tk.Label(self.contenedor_matriz, text="i \\ j", bg=encabezado_bg,
                 fg=encabezado_fg, font=(self.fuente_mono, 8, "bold"),
                 width=6, padx=2, pady=3, bd=1, relief="solid").grid(
            row=0, column=0, sticky="nsew")

        for j, nodo in enumerate(nodos):
            tk.Label(self.contenedor_matriz, text=nodo.nombre, bg=encabezado_bg,
                     fg=encabezado_fg, font=(self.fuente_mono, 9, "bold"),
                     width=6, padx=2, pady=3, bd=1, relief="solid").grid(
                row=0, column=j + 1, sticky="nsew")

        for i, nodo_i in enumerate(nodos):
            etiqueta_fila = nodo_i.nombre
            tk.Label(self.contenedor_matriz, text=etiqueta_fila, bg=encabezado_bg,
                     fg=encabezado_fg, font=(self.fuente_mono, 9, "bold"),
                     width=6, padx=2, pady=3, bd=1, relief="solid").grid(
                row=i + 1, column=0, sticky="nsew")

            for j, nodo_j in enumerate(nodos):
                if self.modo_matriz == "distancias":
                    valor = it.distancias[i][j]
                    texto = formatear(valor)
                    fg = INF_TEXTO if valor == float("inf") else TEXTO
                    bg = DIAGONAL_FONDO if i == j else TARJETA
                else:
                    siguiente = it.sucesores[i][j]
                    if i == j or siguiente is None:
                        texto, fg = "\u2014", TEXTO_SUAVE
                    else:
                        texto, fg = nodos[siguiente].nombre, TEXTO
                    bg = DIAGONAL_FONDO if i == j else TARJETA

                if (i, j) in mejoradas and self.modo_matriz == "distancias":
                    bg, fg = MEJORA_FONDO, MEJORA_TEXTO

                celda = tk.Label(
                    self.contenedor_matriz, text=texto, bg=bg, fg=fg,
                    font=(self.fuente_mono, 9), width=6, padx=2, pady=3,
                    bd=1, relief="solid")
                celda.grid(row=i + 1, column=j + 1, sticky="nsew")
                self.celdas_matriz.append((i, j, celda))

    # ==================================================================
    # Consulta de ruta
    # ==================================================================
    def refrescar_combos(self) -> None:
        nombres = [n.nombre for n in self.grafo.lista_nodos()]
        self.combo_origen["values"] = nombres
        self.combo_destino["values"] = nombres
        if nombres:
            if self.combo_origen.get() not in nombres:
                self.combo_origen.set(nombres[0])
            if self.combo_destino.get() not in nombres:
                self.combo_destino.set(nombres[-1])

    def consultar_ruta(self) -> None:
        if self.resultado is None:
            self.informar("Ejecute primero el algoritmo de Floyd-Warshall.", "error")
            return
        origen = self.grafo.nodos_por_nombre(self.combo_origen.get())
        destino = self.grafo.nodos_por_nombre(self.combo_destino.get())
        if origen is None or destino is None:
            self.informar("Seleccione un origen y un destino validos.", "error")
            return

        self.nodo_origen_consulta = origen
        self.nodo_destino_consulta = destino

        if origen is destino:
            self.arcos_consulta = set()
            self.nodos_consulta = {origen.id}
            self.etiqueta_consulta.config(
                text=f"{origen.nombre} y {destino.nombre} son el mismo nodo: "
                     "distancia 0.", fg=ACENTO)
            self.pintar()
            return

        distancia = self.resultado.distancia(origen, destino)
        if distancia is None:
            self.arcos_consulta = set()
            self.nodos_consulta = {origen.id, destino.id}
            self.etiqueta_consulta.config(
                text=f"No existe camino de {origen.nombre} a {destino.nombre}.",
                fg=NODO_DESTINO)
            self.informar(
                f"No existe camino entre {origen.nombre} y {destino.nombre}.", "error")
            self.pintar()
            return

        camino = self.resultado.camino(origen, destino)
        arcos = self.resultado.arcos_camino(origen, destino)
        self.arcos_consulta = {id(a) for a in arcos}
        self.nodos_consulta = {n.id for n in camino}
        ruta = "  \u2192  ".join(n.nombre for n in camino)
        pesos = " + ".join(f"{p:g}" for p in self.resultado.suma_camino(origen, destino))
        self.etiqueta_consulta.config(
            text=f"{ruta}     distancia minima = {formatear(distancia)}   "
                 f"({pesos} = {formatear(distancia)})", fg=ACENTO_2)
        self.informar(
            f"Ruta minima {origen.nombre} \u2192 {destino.nombre}: {ruta} "
            f"(total {formatear(distancia)}).", "ok")
        self.pintar()

    # ==================================================================
    # Archivo
    # ==================================================================
    def nueva_red(self) -> None:
        if self.grafo.nodos and not messagebox.askyesno(
                "Nueva red", "Se eliminara la red actual. Continuar?"):
            return
        self.detener_animacion()
        self.grafo.limpiar()
        self._reset_vista()
        for atributo in ("nodo_origen_consulta", "nodo_destino_consulta",
                         "nodo_seleccionado", "arco_seleccionado"):
            setattr(self, atributo, None)
        self.limpiar_resultados(silencioso=True)
        self.refrescar_combos()
        self.etiqueta_consulta.config(
            text="Ejecute el algoritmo y elija un origen y un destino.",
            fg=TEXTO_SUAVE)
        self.actualizar_estado()
        self.pintar()
        self.informar("Lienzo vacio. Doble clic para crear un nodo.", "info")

    def cargar_ejemplo(self) -> None:
        if self.grafo.nodos and not messagebox.askyesno(
                "Red de ejemplo", "Se reemplazara la red actual por el ejemplo. Continuar?"):
            return
        self.detener_animacion()
        self.grafo.limpiar()
        self._reset_vista()
        ancho = max(self.lienzo.winfo_width(), 760)
        alto = max(self.lienzo.winfo_height(), 460)
        cx, cy = ancho / 2, alto / 2
        r = min(ancho * 0.30, alto * 0.34)

        a = self.grafo.agregar_nodo("A", cx - r * 1.5, cy - r * 0.8)
        b = self.grafo.agregar_nodo("B", cx + r * 0.1, cy - r * 1.1)
        c = self.grafo.agregar_nodo("C", cx + r * 1.4, cy - r * 0.5)
        d = self.grafo.agregar_nodo("D", cx + r * 0.7, cy + r * 0.9)
        e = self.grafo.agregar_nodo("E", cx - r * 1.1, cy + r * 0.9)

        self.grafo.agregar_arco(a, b, 4)
        self.grafo.agregar_arco(a, c, 2)
        self.grafo.agregar_arco(b, c, 5)
        self.grafo.agregar_arco(b, d, 10)
        self.grafo.agregar_arco(c, d, 3)
        self.grafo.agregar_arco(c, e, 8)
        self.grafo.agregar_arco(d, e, 2)
        self.grafo.agregar_arco(e, b, 1)

        for atributo in ("nodo_seleccionado", "arco_seleccionado",
                         "nodo_origen_consulta", "nodo_destino_consulta"):
            setattr(self, atributo, None)
        self.limpiar_resultados(silencioso=True)
        self.refrescar_combos()
        self.actualizar_estado()
        self.pintar()
        self.informar(
            "Red de ejemplo cargada (A, B, C, D, E). Pulse 'Ejecutar'.", "ok")

    def exportar_csv(self) -> None:
        if self.resultado is None:
            self.informar("Ejecute Floyd-Warshall antes de exportar.", "error")
            return
        ruta = filedialog.asksaveasfilename(
            title="Guardar matrices", defaultextension=".csv",
            filetypes=[("Archivo CSV", "*.csv")])
        if not ruta:
            return
        nodos = self.resultado.nodos
        with open(ruta, "w", encoding="utf-8", newline="") as archivo:
            archivo.write("MATRIZ DE DISTANCIAS MINIMAS\n")
            archivo.write("," + ",".join(n.nombre for n in nodos) + "\n")
            for i, origen in enumerate(nodos):
                fila = [origen.nombre]
                for j in range(len(nodos)):
                    fila.append(formatear(self.resultado.distancias[i][j]))
                archivo.write(",".join(fila) + "\n")
            archivo.write("\nMATRIZ DE RECORRIDOS\n")
            archivo.write("," + ",".join(n.nombre for n in nodos) + "\n")
            for i, origen in enumerate(nodos):
                fila = [origen.nombre]
                for j in range(len(nodos)):
                    siguiente = self.resultado.sucesores[i][j]
                    fila.append(nodos[siguiente].nombre if siguiente is not None else "-")
                archivo.write(",".join(fila) + "\n")
            archivo.write("\nRUTAS MINIMAS\n")
            archivo.write("origen,destino,distancia_minima,camino\n")
            for origen in nodos:
                for destino in nodos:
                    if origen is destino:
                        continue
                    distancia = self.resultado.distancia(origen, destino)
                    if distancia is None:
                        archivo.write(
                            f"{origen.nombre},{destino.nombre},inf,sin camino\n")
                    else:
                        camino = " -> ".join(
                            n.nombre for n in self.resultado.camino(origen, destino))
                        archivo.write(
                            f"{origen.nombre},{destino.nombre},"
                            f"{formatear(distancia)},{camino}\n")
        self.informar(f"Matrices exportadas en {ruta}", "ok")

    # ==================================================================
    # Estado
    # ==================================================================
    def limpiar_resultados(self, silencioso: bool = False) -> None:
        self.resultado = None
        self.iteraciones = []
        self.indice_iter = 0
        self.arcos_consulta = set()
        self.nodos_consulta = set()
        self.nodo_intermedio_actual = None
        self.pintar_matriz_vacia()
        if hasattr(self, "etiqueta_consulta"):
            self.etiqueta_consulta.config(
                text="Resultados invalidados: ejecute de nuevo el algoritmo.",
                fg=TEXTO_SUAVE)
        if not silencioso:
            self.informar("Resultados limpiados. Vuelva a ejecutar.", "info")
        self.actualizar_estado()

    def actualizar_estado(self) -> None:
        self.etiqueta_info.config(
            text=f"Nodos: {len(self.grafo.nodos)}   Arcos: {len(self.grafo.arcos)}")
        self.etiqueta_red.config(
            text=f"{len(self.grafo.nodos)} nodos, {len(self.grafo.arcos)} arcos",
            fg=TEXTO if self.grafo.nodos else TEXTO_SUAVE)

        if self.arco_seleccionado is not None:
            texto, color = self.arco_seleccionado.etiqueta(), TEXTO
        elif self.nodo_seleccionado is not None:
            texto, color = f"Nodo {self.nodo_seleccionado.nombre}", TEXTO
        else:
            texto, color = "Nada seleccionado", TEXTO_SUAVE
        self.etiqueta_seleccion_panel.config(text=texto, fg=color)

        animando = self._animando
        self._habilitar(self.boton_ejecutar, not animando)
        self._habilitar(self.boton_reproducir, not animando)
        self._habilitar(self.boton_detener, animando)

        self._habilitar(self.boton_peso, self.arco_seleccionado is not None)
        self._habilitar(self.boton_eliminar_arco, self.arco_seleccionado is not None)
        self._habilitar(self.boton_eliminar_nodo, self.nodo_seleccionado is not None)
        self._habilitar(self.boton_renombrar, self.nodo_seleccionado is not None)
        hay = bool(self.iteraciones)
        self._habilitar(self.boton_anterior, hay)
        self._habilitar(self.boton_siguiente, hay)
        self._habilitar(self.boton_ver_inicial, hay)
        self._habilitar(self.boton_ver_final, hay)
        self._habilitar(self.boton_consultar, self.resultado is not None)

    def _habilitar(self, marco, activo: bool) -> None:
        marco._activo["on"] = activo
        if activo:
            color, texto = marco._color, marco._fg
        else:
            color, texto = "#e2e8f0", "#94a3b8"
        marco.configure(bg=color, cursor="hand2" if activo else "arrow")
        marco._etiqueta.configure(bg=color, fg=texto,
                                  cursor="hand2" if activo else "arrow")

    def informar(self, mensaje: str, tipo: str = "info") -> None:
        colores = {
            "info": TEXTO, "ok": "#166534", "error": PELIGRO,
        }
        self.etiqueta_estado.config(text=mensaje, fg=colores.get(tipo, TEXTO))

    def cerrar(self) -> None:
        self.detener_animacion()
        self.raiz.destroy()


def main() -> None:
    raiz = tk.Tk()
    AplicacionFloyd(raiz)
    raiz.mainloop()


if __name__ == "__main__":
    main()
