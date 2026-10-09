"""Pruebas de la interfaz grafica del proyecto de Floyd-Warshall.

Combinan verificaciones de correccion funcional con comprobaciones de que la
interfaz es visualmente correcta: controles visibles, nada recortado, matrices
renderizadas, flechas que apuntan al destino y resaltado de las mejoras.
"""

import gc
import tkinter as tk
import unittest
from unittest.mock import patch

from interfaz import MEJORA_FONDO, AplicacionFloyd

DIALOGO = "tkinter.simpledialog.askstring"


class PruebaInterfaz(unittest.TestCase):
    """Suite que reutiliza UNA sola ventana Tk.

    En Windows, crear y destruir un interprete Tcl/Tk por cada prueba es
    inestable (falla con ``tcl_findLibrary``). Para que la suite sea
    reproducible, la ventana se crea una vez y entre pruebas se reconstruye
    la aplicacion sobre el mismo ``Tk``.
    """

    raiz = None
    CLAVES_RAIZ = (
        "<Delete>", "<Escape>", "<Left>", "<Right>", "<Up>", "<Down>",
        "<plus>", "<equal>", "<KP_Add>", "<minus>", "<KP_Subtract>",
        "<Key-0>", "<MouseWheel>",
    )

    @classmethod
    def setUpClass(cls) -> None:
        cls.raiz = tk.Tk()
        cls.raiz.geometry("1360x860")
        cls.raiz.update_idletasks()

    @classmethod
    def tearDownClass(cls) -> None:
        try:
            cls.raiz.destroy()
        except tk.TclError:
            pass

    def setUp(self) -> None:
        self._limpiar_ventana()
        self.raiz.geometry("1360x860")
        self.raiz.deiconify()
        self.raiz.state("normal")
        self.app = AplicacionFloyd(self.raiz)
        self.raiz.update_idletasks()
        self.raiz.update()

    def tearDown(self) -> None:
        app = getattr(self, "app", None)
        if app is not None:
            app.detener_animacion()
        self._limpiar_ventana()
        self.app = None
        gc.collect()

    @classmethod
    def _limpiar_ventana(cls) -> None:
        for clave in cls.CLAVES_RAIZ:
            try:
                cls.raiz.unbind(clave)
            except tk.TclError:
                pass
        cls.raiz.unbind_all("<Motion>")
        for hijo in cls.raiz.winfo_children():
            hijo.destroy()
        cls.raiz.update_idletasks()

    # ------------------------------------------------------------------
    # Utilidades
    # ------------------------------------------------------------------
    @staticmethod
    def _evento(x, y, state=0):
        evento = tk.Event()
        evento.x = int(x)
        evento.y = int(y)
        evento.delta = 0
        evento.state = state
        return evento

    def _doble_clic(self, x, y, state=0):
        self.app.doble_clic(self._evento(x, y, state))

    def _arrastrar_de_a(self, origen, destino, peso="5"):
        with patch(DIALOGO, return_value=peso):
            self.app.presionar(self._evento(origen.x, origen.y))
            self.app.arrastrar(self._evento(destino.x, destino.y))
            self.app.soltar(self._evento(destino.x, destino.y))

    def _red(self):
        """Red A->B (1), B->C (5), A->C (10); A->C optimo = A->B->C = 6."""
        self._doble_clic(140, 140)
        self._doble_clic(460, 140)
        self._doble_clic(300, 380)
        a, b, c = (self.app.grafo.nodos[i] for i in (1, 2, 3))
        self._arrastrar_de_a(a, b, "1")
        self._arrastrar_de_a(b, c, "5")
        self._arrastrar_de_a(a, c, "10")
        return a, b, c

    def _celda(self, i, j):
        for (fila, col, etiqueta) in self.app.celdas_matriz:
            if fila == i and col == j:
                return etiqueta
        raise AssertionError(f"no existe la celda {i},{j}")

    # ------------------------------------------------------------------
    # Verificacion visual
    # ------------------------------------------------------------------
    def test_los_botones_principales_son_visibles_y_clicables(self) -> None:
        for nombre in ("boton_ejecutar", "boton_reproducir", "boton_detener"):
            boton = getattr(self.app, nombre)
            self.assertTrue(boton.winfo_ismapped(), nombre)
            self.assertGreater(boton.winfo_height(), 10, nombre)

    def test_ningun_control_queda_fuera_de_la_ventana(self) -> None:
        limite_arriba = self.raiz.winfo_rooty()
        limite_abajo = limite_arriba + self.raiz.winfo_height()
        recortados = []

        def revisar(widget):
            if widget is self.app._lienzo_panel:
                return
            if widget.winfo_ismapped():
                alto = widget.winfo_height()
                if alto:
                    y = widget.winfo_rooty()
                    if y < limite_arriba - 2 or y + alto > limite_abajo + 2:
                        recortados.append((widget.winfo_class(), y, alto))
            for hijo in widget.winfo_children():
                revisar(hijo)

        revisar(self.raiz)
        self.assertEqual(recortados, [], f"controles recortados: {recortados}")

    def test_el_panel_lateral_tiene_scroll(self) -> None:
        bbox = self.app._lienzo_panel.bbox("all")
        self.assertIsNotNone(bbox)
        self.assertGreater(bbox[3], self.app._lienzo_panel.winfo_height())

    def test_las_tres_zonas_existen(self) -> None:
        self.assertTrue(self.app.lienzo.winfo_ismapped())
        self.assertTrue(self.app._lienzo_matriz.winfo_ismapped())
        self.assertTrue(self.app.combo_origen.winfo_ismapped())
        self.assertTrue(self.app.combo_destino.winfo_ismapped())

    def test_el_lienzo_dibuja_la_red(self) -> None:
        self._red()
        self.app.pintar()
        self.assertGreater(len(self.app.lienzo.find_all()), 0)

    def test_las_flechas_de_los_arcos_apuntan_al_destino(self) -> None:
        self._red()
        posiciones = self.app._posiciones_arcos()
        for arco in self.app.grafo.arcos:
            pos = posiciones[id(arco)]
            self.assertLess(
                self._dist(pos["bx"], pos["by"], arco.destino.x, arco.destino.y),
                self._dist(pos["bx"], pos["by"], arco.origen.x, arco.origen.y),
                f"flecha de {arco.etiqueta()}")

    def test_la_matriz_se_renderiza_con_todas_las_celdas(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        n = len(self.app.grafo.nodos)
        self.assertEqual(len(self.app.celdas_matriz), n * n)

    def test_la_matriz_inicial_muestra_infinito_sin_conexion(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        res = self.app.resultado
        ib = res.indice_de(b)
        ia = res.indice_de(a)
        self.assertEqual(self._celda(ib, ia).cget("text"), "\u221e")

    def test_la_diagonal_de_la_matriz_es_cero(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        res = self.app.resultado
        for nodo in self.app.grafo.lista_nodos():
            i = res.indice_de(nodo)
            self.assertEqual(self._celda(i, i).cget("text"), "0")

    # ------------------------------------------------------------------
    # Creacion y edicion de la red
    # ------------------------------------------------------------------
    def test_doble_clic_en_area_vacia_crea_un_nodo(self) -> None:
        self._doble_clic(300, 200)
        self.assertEqual(len(self.app.grafo.nodos), 1)
        nodo = next(iter(self.app.grafo.nodos.values()))
        self.assertEqual((nodo.x, nodo.y), (300, 200))

    def test_los_nodos_se_nombran_con_letras(self) -> None:
        for x in (120, 300, 480):
            self._doble_clic(x, 200)
        nombres = sorted(n.nombre for n in self.app.grafo.nodos.values())
        self.assertEqual(nombres, ["A", "B", "C"])

    def test_doble_clic_sobre_un_nodo_no_crea_otro(self) -> None:
        self._red()
        a = self.app.grafo.nodos[1]
        self._doble_clic(a.x, a.y)
        self.assertEqual(len(self.app.grafo.nodos), 3)

    def test_arrastrar_de_un_nodo_a_otro_crea_un_arco(self) -> None:
        self._doble_clic(140, 140)
        self._doble_clic(460, 140)
        a, b = self.app.grafo.nodos[1], self.app.grafo.nodos[2]
        self._arrastrar_de_a(a, b, "7")
        arco = self.app.grafo.buscar_arco(a, b)
        self.assertIsNotNone(arco)
        self.assertEqual(arco.peso, 7.0)

    def test_arco_dirigido_no_crea_el_inverso(self) -> None:
        self._doble_clic(140, 140)
        self._doble_clic(460, 140)
        a, b = self.app.grafo.nodos[1], self.app.grafo.nodos[2]
        self._arrastrar_de_a(a, b, "7")
        self.assertIsNone(self.app.grafo.buscar_arco(b, a))

    def test_peso_cero_se_rechaza(self) -> None:
        self._doble_clic(140, 140)
        self._doble_clic(460, 140)
        a, b = self.app.grafo.nodos[1], self.app.grafo.nodos[2]
        self._arrastrar_de_a(a, b, "0")
        self.assertIsNone(self.app.grafo.buscar_arco(a, b))
        self.assertIn("positivo", self.app.etiqueta_estado.cget("text"))

    def test_peso_negativo_se_rechaza(self) -> None:
        self._doble_clic(140, 140)
        self._doble_clic(460, 140)
        a, b = self.app.grafo.nodos[1], self.app.grafo.nodos[2]
        self._arrastrar_de_a(a, b, "-3")
        self.assertIsNone(self.app.grafo.buscar_arco(a, b))

    def test_peso_invalido_se_rechaza(self) -> None:
        self._doble_clic(140, 140)
        self._doble_clic(460, 140)
        a, b = self.app.grafo.nodos[1], self.app.grafo.nodos[2]
        self._arrastrar_de_a(a, b, "mucho")
        self.assertIsNone(self.app.grafo.buscar_arco(a, b))

    def test_cancelar_el_dialogo_no_crea_arco(self) -> None:
        self._doble_clic(140, 140)
        self._doble_clic(460, 140)
        a, b = self.app.grafo.nodos[1], self.app.grafo.nodos[2]
        with patch(DIALOGO, return_value=None):
            self.app.presionar(self._evento(a.x, a.y))
            self.app.arrastrar(self._evento(b.x, b.y))
            self.app.soltar(self._evento(b.x, b.y))
        self.assertIsNone(self.app.grafo.buscar_arco(a, b))

    def test_arco_duplicado_se_rechaza(self) -> None:
        a, b, c = self._red()
        self._arrastrar_de_a(a, b, "9")
        self.assertEqual(self.app.grafo.buscar_arco(a, b).peso, 1.0)
        self.assertIn("Ya existe", self.app.etiqueta_estado.cget("text"))

    def test_clic_simple_sobre_nodo_lo_selecciona(self) -> None:
        self._red()
        b = self.app.grafo.nodos[2]
        self.app.presionar(self._evento(b.x, b.y))
        self.app.soltar(self._evento(b.x, b.y))
        self.assertIs(self.app.nodo_seleccionado, b)

    def test_doble_clic_sobre_nodo_fija_el_origen_de_consulta(self) -> None:
        self._red()
        c = self.app.grafo.nodos[3]
        self._doble_clic(c.x, c.y)
        self.assertEqual(self.app.combo_origen.get(), "C")

    def test_mayus_doble_clic_fija_el_destino(self) -> None:
        self._red()
        c = self.app.grafo.nodos[3]
        self._doble_clic(c.x, c.y, state=0x0001)
        self.assertEqual(self.app.combo_destino.get(), "C")

    def test_clic_derecho_elimina_un_nodo_y_sus_arcos(self) -> None:
        a, b, c = self._red()
        self.app.clic_derecho(self._evento(a.x, a.y))
        self.assertNotIn(a.id, self.app.grafo.nodos)
        self.assertTrue(all(arco.origen is not a and arco.destino is not a
                            for arco in self.app.grafo.arcos))

    def test_clic_derecho_elimina_un_arco(self) -> None:
        a, b, c = self._red()
        self.app.clic_derecho(self._evento((a.x + b.x) / 2, (a.y + b.y) / 2))
        self.assertIsNone(self.app.grafo.buscar_arco(a, b))

    def test_modificar_peso_del_arco_seleccionado(self) -> None:
        a, b, c = self._red()
        arco = self.app.grafo.buscar_arco(a, b)
        self.app.arco_seleccionado = arco
        with patch(DIALOGO, return_value="11"):
            self.app.modificar_peso()
        self.assertEqual(arco.peso, 11.0)

    def test_renombrar_nodo(self) -> None:
        a, b, c = self._red()
        self.app.nodo_seleccionado = a
        with patch(DIALOGO, return_value="Inicio"):
            self.app.renombrar_nodo()
        self.assertEqual(a.nombre, "Inicio")

    def test_renombrar_a_un_nombre_existente_se_rechaza(self) -> None:
        a, b, c = self._red()
        self.app.nodo_seleccionado = a
        with patch(DIALOGO, return_value="B"):
            self.app.renombrar_nodo()
        self.assertEqual(a.nombre, "A")

    # ------------------------------------------------------------------
    # Ejecucion e iteraciones
    # ------------------------------------------------------------------
    def test_ejecutar_calcula_las_distancias(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.assertIsNotNone(self.app.resultado)
        self.assertEqual(self.app.resultado.distancia(a, b), 1.0)
        self.assertEqual(self.app.resultado.distancia(a, c), 6.0)

    def test_ejecutar_genera_matriz_inicial_mas_una_por_nodo(self) -> None:
        self._red()
        self.app.ejecutar()
        self.assertEqual(len(self.app.iteraciones), len(self.app.grafo.nodos) + 1)
        self.assertTrue(self.app.iteraciones[0].es_inicial)
        self.assertEqual(self.app.indice_iter, 0)

    def test_la_etiqueta_de_iteracion_se_actualiza(self) -> None:
        self._red()
        self.app.ejecutar()
        self.assertIn("inicial", self.app.etiqueta_iteracion.cget("text").lower())
        self.app.ver_matriz_final()
        self.assertIn("Iteraci", self.app.etiqueta_iteracion.cget("text"))

    def test_navegar_entre_iteraciones(self) -> None:
        self._red()
        self.app.ejecutar()
        self.app.iteracion_siguiente()
        self.assertEqual(self.app.indice_iter, 1)
        self.app.iteracion_anterior()
        self.assertEqual(self.app.indice_iter, 0)

    def test_navegar_no_se_sale_de_los_limites(self) -> None:
        self._red()
        self.app.ejecutar()
        self.app.ir_a_iteracion(-5)
        self.assertEqual(self.app.indice_iter, 0)
        self.app.ir_a_iteracion(999)
        self.assertEqual(self.app.indice_iter, len(self.app.iteraciones) - 1)

    def test_ver_matriz_final_muestra_las_distancias_optimas(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.app.ver_matriz_final()
        res = self.app.resultado
        self.assertEqual(self._celda(res.indice_de(a), res.indice_de(c)).cget("text"), "6")

    def test_las_celdas_mejoradas_se_resaltan(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        indices_con_cambios = [
            k for k, it in enumerate(self.app.iteraciones) if it.cambios]
        self.assertTrue(indices_con_cambios, "el ejemplo debe producir mejoras")
        self.app.ir_a_iteracion(indices_con_cambios[0])
        celdas_verdes = [
            lbl for (_i, _j, lbl) in self.app.celdas_matriz
            if lbl.cget("bg") == MEJORA_FONDO]
        self.assertTrue(celdas_verdes)

    def test_modo_recorridos_muestra_el_siguiente_nodo(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.app.ver_matriz_final()
        self.app.cambiar_modo("recorridos")
        res = self.app.resultado
        self.assertEqual(
            self._celda(res.indice_de(a), res.indice_de(c)).cget("text"), "B")

    def test_modo_recorridos_inicial_muestra_el_sucesor_directo(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.app.cambiar_modo("recorridos")
        res = self.app.resultado
        self.assertEqual(
            self._celda(res.indice_de(a), res.indice_de(c)).cget("text"), "C")
        self.assertEqual(
            self._celda(res.indice_de(b), res.indice_de(a)).cget("text"), "\u2014")

    def test_cambiar_de_modo_es_reversible(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.app.cambiar_modo("recorridos")
        self.app.cambiar_modo("distancias")
        res = self.app.resultado
        self.assertEqual(self._celda(res.indice_de(a), res.indice_de(b)).cget("text"), "1")

    def test_ejecutar_sin_red_avisa(self) -> None:
        self.app.ejecutar()
        self.assertIsNone(self.app.resultado)
        self.assertIn("No se puede ejecutar", self.app.etiqueta_estado.cget("text"))

    def test_ejecutar_red_sin_arcos_avisa(self) -> None:
        self._doble_clic(140, 140)
        self._doble_clic(460, 140)
        self.app.ejecutar()
        self.assertIsNone(self.app.resultado)

    # ------------------------------------------------------------------
    # Consulta de ruta
    # ------------------------------------------------------------------
    def test_consulta_muestra_la_ruta_minima_y_su_distancia(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.app.combo_origen.set("A")
        self.app.combo_destino.set("C")
        self.app.consultar_ruta()
        texto = self.app.etiqueta_consulta.cget("text")
        self.assertIn("A", texto)
        self.assertIn("B", texto)
        self.assertIn("C", texto)
        self.assertIn("6", texto)

    def test_consulta_resalta_los_arcos_de_la_ruta(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.app.combo_origen.set("A")
        self.app.combo_destino.set("C")
        self.app.consultar_ruta()
        self.assertEqual(len(self.app.arcos_consulta), 2)

    def test_consulta_sin_camino_avisa(self) -> None:
        a, b, c = self._red()
        self._doble_clic(820, 620)
        self.app.ejecutar()
        self.app.combo_origen.set("A")
        self.app.combo_destino.set("D")
        self.app.consultar_ruta()
        self.assertIn("No existe camino", self.app.etiqueta_consulta.cget("text"))

    def test_consulta_mismo_nodo_da_distancia_cero(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.app.combo_origen.set("A")
        self.app.combo_destino.set("A")
        self.app.consultar_ruta()
        self.assertIn("distancia 0", self.app.etiqueta_consulta.cget("text"))

    def test_consulta_sin_ejecutar_avisa(self) -> None:
        self._red()
        self.app.consultar_ruta()
        self.assertIn("Ejecute primero", self.app.etiqueta_estado.cget("text"))

    def test_editar_la_red_invalida_los_resultados(self) -> None:
        a, b, c = self._red()
        self.app.ejecutar()
        self.assertIsNotNone(self.app.resultado)
        self._doble_clic(820, 620)
        self.assertIsNone(self.app.resultado)
        self.assertEqual(self.app.celdas_matriz, [])

    # ------------------------------------------------------------------
    # Animacion
    # ------------------------------------------------------------------
    def test_reproducir_iteraciones_termina_en_la_matriz_final(self) -> None:
        import time
        a, b, c = self._red()
        self.app.velocidad.set(50)
        self.app.reproducir_iteraciones()
        limite = time.time() + 8
        while self.app._animando and time.time() < limite:
            self.raiz.update()
            time.sleep(0.005)
        self.assertFalse(self.app._animando, "la animacion no termino")
        self.assertEqual(self.app.indice_iter, len(self.app.iteraciones) - 1)

    def test_detener_animacion(self) -> None:
        a, b, c = self._red()
        self.app.velocidad.set(1000)
        self.app.reproducir_iteraciones()
        self.app.detener_animacion()
        self.assertFalse(self.app._animando)
        self.assertIsNone(self.app._id_after)

    def test_durante_la_animacion_no_se_edita_la_red(self) -> None:
        a, b, c = self._red()
        self.app.velocidad.set(800)
        self.app.reproducir_iteraciones()
        self.assertTrue(self.app._animando)
        nodos_antes = len(self.app.grafo.nodos)
        self._doble_clic(820, 620)
        self.assertEqual(len(self.app.grafo.nodos), nodos_antes)
        self.app.detener_animacion()

    # ------------------------------------------------------------------
    # Archivo y estado de botones
    # ------------------------------------------------------------------
    def test_cargar_ejemplo(self) -> None:
        self.app.cargar_ejemplo()
        self.assertEqual(len(self.app.grafo.nodos), 5)
        self.app.ejecutar()
        self.assertIsNotNone(self.app.resultado)

    def test_nueva_red_vacia_todo(self) -> None:
        self.app.cargar_ejemplo()
        with patch("tkinter.messagebox.askyesno", return_value=True):
            self.app.nueva_red()
        self.assertEqual(len(self.app.grafo.nodos), 0)
        self.assertIsNone(self.app.resultado)

    def test_exportar_csv(self) -> None:
        import csv
        import os
        import tempfile

        a, b, c = self._red()
        self.app.ejecutar()
        ruta = os.path.join(tempfile.gettempdir(), "floyd_export_prueba.csv")
        with patch("tkinter.filedialog.asksaveasfilename", return_value=ruta):
            self.app.exportar_csv()
        with open(ruta, encoding="utf-8", newline="") as archivo:
            contenido = archivo.read()
        os.remove(ruta)
        self.assertIn("MATRIZ DE DISTANCIAS MINIMAS", contenido)
        self.assertIn("MATRIZ DE RECORRIDOS", contenido)
        self.assertIn("A -> B -> C", contenido)

    def test_exportar_sin_resultado_avisa(self) -> None:
        with patch("tkinter.filedialog.asksaveasfilename") as dialogo:
            self.app.exportar_csv()
            dialogo.assert_not_called()

    def test_los_botones_se_deshabilitan_cuando_corresponde(self) -> None:
        self.app.actualizar_estado()
        self.assertFalse(self.app.boton_peso._activo["on"])
        self.assertFalse(self.app.boton_consultar._activo["on"])
        self._red()
        a = self.app.grafo.nodos[1]
        self.app.nodo_seleccionado = a
        self.app.actualizar_estado()
        self.assertTrue(self.app.boton_renombrar._activo["on"])

    def test_el_boton_consultar_se_habilita_al_ejecutar(self) -> None:
        self._red()
        self.app.ejecutar()
        self.assertTrue(self.app.boton_consultar._activo["on"])

    def test_zoom_acerca_y_aleja(self) -> None:
        self._doble_clic(300, 200)
        nodo = next(iter(self.app.grafo.nodos.values()))
        antes = self.app._a_pantalla(nodo.x, nodo.y)
        self.app.acercar(foco=(300, 200))
        self.assertGreater(self.app.zoom, 1.0)
        despues = self.app._a_pantalla(nodo.x, nodo.y)
        self.assertAlmostEqual(despues[0], antes[0], delta=1.0)
        self.app.restablecer_zoom()
        self.assertEqual(self.app.zoom, 1.0)

    @staticmethod
    def _dist(x1, y1, x2, y2):
        return ((x1 - x2) ** 2 + (y1 - y2) ** 2) ** 0.5


if __name__ == "__main__":
    unittest.main(verbosity=2)
