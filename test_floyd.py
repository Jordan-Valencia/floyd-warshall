"""Pruebas del modelo de red y del algoritmo de Floyd-Warshall.

Cubren las cinco verificaciones que exige el punto 4 del proyecto:

1. Correcta interpretacion de la direccion de los arcos.
2. Calculo correcto de las distancias minimas (contra una referencia
   independiente: Bellman-Ford desde cada origen).
3. Identificacion de rutas alternativas.
4. Tratamiento de nodos sin conexion con determinados sectores.
5. Consistencia entre la red, la matriz inicial y los resultados finales.
"""

import unittest
from math import inf

from floyd import (
    INF,
    construir_matrices,
    floyd_iteraciones,
    floyd_warshall,
    formatear,
)
from grafo import ErrorGrafo, Grafo


def red_dirigida() -> tuple[Grafo, dict]:
    """Red dirigida de ejemplo con rutas alternativas y un ciclo."""
    grafo = Grafo()
    a = grafo.agregar_nodo("A", 100, 100)
    b = grafo.agregar_nodo("B", 300, 100)
    c = grafo.agregar_nodo("C", 200, 300)
    d = grafo.agregar_nodo("D", 400, 300)
    e = grafo.agregar_nodo("E", 300, 420)
    grafo.agregar_arco(a, b, 4)
    grafo.agregar_arco(a, c, 2)
    grafo.agregar_arco(b, c, 5)
    grafo.agregar_arco(b, d, 10)
    grafo.agregar_arco(c, d, 3)
    grafo.agregar_arco(c, e, 8)
    grafo.agregar_arco(d, e, 2)
    grafo.agregar_arco(e, b, 1)
    return grafo, {"A": a, "B": b, "C": c, "D": d, "E": e}


class PruebasValidacionDePesos(unittest.TestCase):
    def setUp(self) -> None:
        self.grafo = Grafo()
        self.a = self.grafo.agregar_nodo("A")
        self.b = self.grafo.agregar_nodo("B")

    def test_peso_positivo_se_acepta(self) -> None:
        arco = self.grafo.agregar_arco(self.a, self.b, 7)
        self.assertEqual(arco.peso, 7.0)

    def test_peso_decimal_se_acepta(self) -> None:
        arco = self.grafo.agregar_arco(self.a, self.b, 2.5)
        self.assertEqual(arco.peso, 2.5)

    def test_peso_cero_se_rechaza(self) -> None:
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(self.a, self.b, 0)

    def test_peso_negativo_se_rechaza(self) -> None:
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(self.a, self.b, -3)

    def test_peso_no_numerico_se_rechaza(self) -> None:
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(self.a, self.b, "mucho")

    def test_autoloop_se_rechaza(self) -> None:
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(self.a, self.a, 5)

    def test_arco_duplicado_se_rechaza(self) -> None:
        self.grafo.agregar_arco(self.a, self.b, 3)
        with self.assertRaises(ErrorGrafo):
            self.grafo.agregar_arco(self.a, self.b, 9)

    def test_modificar_peso_invalido_conserva_el_anterior(self) -> None:
        arco = self.grafo.agregar_arco(self.a, self.b, 3)
        with self.assertRaises(ErrorGrafo):
            self.grafo.modificar_peso(arco, 0)
        self.assertEqual(arco.peso, 3.0)


class PruebasDireccionDeArcos(unittest.TestCase):
    """Punto 4.1: la direccion de los arcos debe interpretarse correctamente."""

    def test_arco_dirigido_no_crea_el_inverso(self) -> None:
        grafo, n = red_dirigida()
        self.assertIsNotNone(grafo.buscar_arco(n["A"], n["B"]))
        self.assertIsNone(grafo.buscar_arco(n["B"], n["A"]))

    def test_matriz_inicial_no_es_simetrica(self) -> None:
        grafo, n = red_dirigida()
        nodos, dist, _ = construir_matrices(grafo)
        i = nodos.index(n["A"])
        j = nodos.index(n["B"])
        self.assertEqual(dist[i][j], 4.0)
        self.assertEqual(dist[j][i], INF)

    def test_arco_inverso_con_peso_distinto_es_independiente(self) -> None:
        grafo = Grafo()
        a = grafo.agregar_nodo("A")
        b = grafo.agregar_nodo("B")
        grafo.agregar_arco(a, b, 3)
        grafo.agregar_arco(b, a, 8)
        resultado = floyd_warshall(grafo)
        self.assertEqual(resultado.distancia(a, b), 3.0)
        self.assertEqual(resultado.distancia(b, a), 8.0)

    def test_distancia_entre_par_solo_usa_el_sentido_correcto(self) -> None:
        grafo = Grafo()
        a = grafo.agregar_nodo("A")
        b = grafo.agregar_nodo("B")
        c = grafo.agregar_nodo("C")
        grafo.agregar_arco(a, b, 1)
        grafo.agregar_arco(c, b, 1)
        resultado = floyd_warshall(grafo)
        self.assertIsNone(resultado.distancia(a, c))
        self.assertIsNone(resultado.distancia(c, a))
        self.assertEqual(resultado.distancia(a, b), 1.0)


class PruebasDistanciasMinimas(unittest.TestCase):
    """Punto 4.2: calculo correcto de las distancias minimas."""

    def setUp(self) -> None:
        self.grafo, self.n = red_dirigida()
        self.resultado = floyd_warshall(self.grafo)

    def test_diagonal_del_resultado_es_cero(self) -> None:
        for nodo in self.resultado.nodos:
            self.assertEqual(self.resultado.distancia(nodo, nodo), 0.0)

    def test_distancias_conocidas(self) -> None:
        n = self.n
        esperado = {
            ("A", "B"): 4.0,
            ("A", "C"): 2.0,
            ("A", "D"): 5.0,
            ("A", "E"): 7.0,
            ("B", "D"): 8.0,
            ("D", "B"): 3.0,
            ("E", "B"): 1.0,
        }
        for (o, d), valor in esperado.items():
            self.assertEqual(self.resultado.distancia(n[o], n[d]), valor, f"{o}->{d}")

    def test_distancias_coinciden_con_referencia_bellman_ford(self) -> None:
        for origen in self.resultado.nodos:
            esperado = self._bellman_ford(self.grafo, origen)
            for destino in self.resultado.nodos:
                obtenido = self.resultado.distancia(origen, destino)
                referencia = esperado[destino.id]
                if referencia == inf:
                    self.assertIsNone(obtenido, f"{origen.nombre}->{destino.nombre}")
                else:
                    self.assertAlmostEqual(
                        obtenido, referencia, places=9,
                        msg=f"{origen.nombre}->{destino.nombre}")

    def test_distancias_coinciden_en_redes_aleatorias(self) -> None:
        import random
        for semilla in range(40):
            rnd = random.Random(semilla)
            grafo = Grafo()
            nodos = [grafo.agregar_nodo(f"N{i}") for i in range(rnd.randint(2, 7))]
            for o in nodos:
                for d in nodos:
                    if o is not d and rnd.random() < 0.4:
                        grafo.agregar_arco(o, d, rnd.randint(1, 30))
            if not grafo.arcos:
                continue
            resultado = floyd_warshall(grafo)
            for o in nodos:
                esperado = self._bellman_ford(grafo, o)
                for d in nodos:
                    obtenido = resultado.distancia(o, d)
                    referencia = esperado[d.id]
                    if referencia == inf:
                        self.assertIsNone(obtenido)
                    else:
                        self.assertAlmostEqual(obtenido, referencia, places=9)

    @staticmethod
    def _bellman_ford(grafo: Grafo, origen) -> dict[int, float]:
        distancias = {n.id: inf for n in grafo.nodos.values()}
        distancias[origen.id] = 0.0
        for _ in range(len(grafo.nodos) - 1):
            cambio = False
            for arco in grafo.arcos:
                if distancias[arco.origen.id] == inf:
                    continue
                nuevo = distancias[arco.origen.id] + arco.peso
                if nuevo < distancias[arco.destino.id]:
                    distancias[arco.destino.id] = nuevo
                    cambio = True
            if not cambio:
                break
        return distancias


class PruebasRutasAlternativas(unittest.TestCase):
    """Punto 4.3: identificar rutas alternativas y elegir la mas corta."""

    def setUp(self) -> None:
        self.grafo, self.n = red_dirigida()
        self.resultado = floyd_warshall(self.grafo)

    def test_elige_la_ruta_mas_barata_entre_varias(self) -> None:
        # A->D directa no existe; A->B->D = 14 y A->C->D = 5.
        camino = [x.nombre for x in self.resultado.camino(self.n["A"], self.n["D"])]
        self.assertEqual(camino, ["A", "C", "D"])
        self.assertEqual(self.resultado.distancia(self.n["A"], self.n["D"]), 5.0)

    def test_ruta_alternativa_con_mas_saltos_pero_menor_peso(self) -> None:
        # A->E: A->C->E = 10 frente a A->C->D->E = 7.
        camino = [x.nombre for x in self.resultado.camino(self.n["A"], self.n["E"])]
        self.assertEqual(camino, ["A", "C", "D", "E"])
        self.assertEqual(self.resultado.distancia(self.n["A"], self.n["E"]), 7.0)

    def test_suma_de_pesos_del_camino_igual_a_la_distancia(self) -> None:
        for o in self.resultado.nodos:
            for d in self.resultado.nodos:
                if o is d:
                    continue
                distancia = self.resultado.distancia(o, d)
                if distancia is None:
                    continue
                suma = sum(self.resultado.suma_camino(o, d))
                self.assertAlmostEqual(suma, distancia, places=9,
                                       msg=f"{o.nombre}->{d.nombre}")

    def test_los_arcos_del_camino_existen_en_la_red(self) -> None:
        camino = self.resultado.camino(self.n["A"], self.n["E"])
        for k in range(len(camino) - 1):
            self.assertIsNotNone(
                self.grafo.buscar_arco(camino[k], camino[k + 1]))


class PruebasNodosDesconectados(unittest.TestCase):
    """Punto 4.4: nodos sin conexion con sectores de la red."""

    def test_nodo_aislado_es_inalcanzable_en_ambos_sentidos(self) -> None:
        grafo, n = red_dirigida()
        f = grafo.agregar_nodo("F")
        resultado = floyd_warshall(grafo)
        for nodo in resultado.nodos:
            if nodo is f:
                continue
            self.assertIsNone(resultado.distancia(nodo, f))
            self.assertIsNone(resultado.distancia(f, nodo))
        self.assertEqual(resultado.camino(n["A"], f), [])
        self.assertEqual(resultado.camino(f, f), [f])

    def test_pares_inalcanzables_se_reportan(self) -> None:
        grafo, n = red_dirigida()
        f = grafo.agregar_nodo("F")
        resultado = floyd_warshall(grafo)
        pares = resultado.pares_inalcanzables()
        esperados = {
            (o, d)
            for i, o in enumerate(resultado.nodos)
            for j, d in enumerate(resultado.nodos)
            if i != j and resultado.distancias[i][j] == INF
        }
        self.assertEqual(set(pares), esperados)
        self.assertIn((n["A"], f), pares)
        self.assertIn((f, n["A"]), pares)
        self.assertTrue(all(o is not d for o, d in pares))

    def test_sector_desconectado_entre_dos_componentes(self) -> None:
        grafo = Grafo()
        a = grafo.agregar_nodo("A")
        b = grafo.agregar_nodo("B")
        c = grafo.agregar_nodo("C")
        d = grafo.agregar_nodo("D")
        grafo.agregar_arco(a, b, 1)
        grafo.agregar_arco(c, d, 1)
        resultado = floyd_warshall(grafo)
        self.assertEqual(resultado.distancia(a, b), 1.0)
        self.assertEqual(resultado.distancia(c, d), 1.0)
        self.assertIsNone(resultado.distancia(a, c))
        self.assertIsNone(resultado.distancia(b, d))

    def test_formatear_infinito(self) -> None:
        self.assertEqual(formatear(INF), "\u221e")


class PruebasMatricesIniciales(unittest.TestCase):
    """Punto 2 y 4.5: representacion matricial y consistencia."""

    def test_diagonal_inicial_es_cero(self) -> None:
        grafo, _ = red_dirigida()
        nodos, dist, _ = construir_matrices(grafo)
        for i in range(len(nodos)):
            self.assertEqual(dist[i][i], 0.0)

    def test_celdas_sin_conexion_inician_en_infinito(self) -> None:
        grafo = Grafo()
        a = grafo.agregar_nodo("A")
        b = grafo.agregar_nodo("B")
        grafo.agregar_nodo("C")
        grafo.agregar_arco(a, b, 1)
        nodos, dist, suc = construir_matrices(grafo)
        i = nodos.index(a)
        j = nodos.index(b)
        self.assertEqual(dist[i][j], 1.0)
        self.assertEqual(dist[j][i], INF)
        self.assertIsNone(suc[j][i])

    def test_cada_arco_aparece_en_la_matriz_inicial(self) -> None:
        grafo, _ = red_dirigida()
        nodos, dist, _ = construir_matrices(grafo)
        for arco in grafo.arcos:
            i = nodos.index(arco.origen)
            j = nodos.index(arco.destino)
            self.assertEqual(dist[i][j], arco.peso, arco.etiqueta())

    def test_matriz_inicial_de_matriz_de_recorridos(self) -> None:
        grafo, n = red_dirigida()
        nodos, _, suc = construir_matrices(grafo)
        i = nodos.index(n["A"])
        j = nodos.index(n["B"])
        self.assertEqual(suc[i][j], j)
        self.assertIsNone(suc[j][i])

    def test_resultado_final_es_menor_o_igual_que_la_inicial(self) -> None:
        grafo, _ = red_dirigida()
        nodos, dist_inicial, _ = construir_matrices(grafo)
        resultado = floyd_warshall(grafo)
        for i in range(len(nodos)):
            for j in range(len(nodos)):
                if dist_inicial[i][j] == INF:
                    continue
                final = resultado.distancias[i][j]
                self.assertIsNotNone(final)
                self.assertLessEqual(final, dist_inicial[i][j] + 1e-9)


class PruebasTrazabilidadIteraciones(unittest.TestCase):
    """Punto 3: procedimiento iterativo y matrices por iteracion."""

    def setUp(self) -> None:
        self.grafo, self.n = red_dirigida()
        self.resultado = floyd_warshall(self.grafo)

    def test_hay_una_iteracion_por_nodo_mas_la_inicial(self) -> None:
        self.assertEqual(len(self.resultado.iteraciones), len(self.grafo.nodos) + 1)
        self.assertTrue(self.resultado.iteraciones[0].es_inicial)

    def test_la_ultima_iteracion_coincide_con_el_resultado_final(self) -> None:
        ultima = self.resultado.iteraciones[-1]
        self.assertEqual(ultima.distancias, self.resultado.distancias)
        self.assertEqual(ultima.sucesores, self.resultado.sucesores)

    def test_las_distancias_nunca_aumentan_entre_iteraciones(self) -> None:
        previa = self.resultado.iteraciones[0]
        for actual in self.resultado.iteraciones[1:]:
            for i in range(len(actual.nodos)):
                for j in range(len(actual.nodos)):
                    self.assertLessEqual(
                        actual.distancias[i][j], previa.distancias[i][j] + 1e-9)
            previa = actual

    def test_cada_mejora_reportada_es_real(self) -> None:
        previa = self.resultado.iteraciones[0]
        for actual in self.resultado.iteraciones[1:]:
            k = actual.k
            for cambio in actual.cambios:
                self.assertLess(
                    cambio.distancia_nueva, cambio.distancia_previa)
                self.assertAlmostEqual(
                    cambio.distancia_nueva,
                    previa.distancias[cambio.i][k] + previa.distancias[k][cambio.j],
                    places=9)
                self.assertAlmostEqual(
                    actual.distancias[cambio.i][cambio.j],
                    cambio.distancia_nueva, places=9)
            previa = actual

    def test_cambios_reportados_cubren_todas_las_celdas_que_bajan(self) -> None:
        for indice in range(1, len(self.resultado.iteraciones)):
            previa = self.resultado.iteraciones[indice - 1]
            actual = self.resultado.iteraciones[indice]
            reportadas = {(c.i, c.j) for c in actual.cambios}
            for i in range(len(actual.nodos)):
                for j in range(len(actual.nodos)):
                    bajo = actual.distancias[i][j] < previa.distancias[i][j] - 1e-9
                    self.assertEqual(bajo, (i, j) in reportadas,
                                     f"celda {i},{j} en iteracion {actual.k}")

    def test_generador_de_iteraciones_equivale_al_resultado(self) -> None:
        generadas = list(floyd_iteraciones(self.grafo))
        self.assertEqual(len(generadas), len(self.resultado.iteraciones))
        for a, b in zip(generadas, self.resultado.iteraciones):
            self.assertEqual(a.k, b.k)
            self.assertEqual(a.distancias, b.distancias)


class PruebasValidacionEjecucion(unittest.TestCase):
    def test_red_vacia_no_se_puede_ejecutar(self) -> None:
        grafo = Grafo()
        with self.assertRaises(ErrorGrafo):
            floyd_warshall(grafo)
        self.assertTrue(grafo.validar_para_floyd())

    def test_red_sin_arcos_no_se_puede_ejecutar(self) -> None:
        grafo = Grafo()
        grafo.agregar_nodo("A")
        grafo.agregar_nodo("B")
        with self.assertRaises(ErrorGrafo):
            floyd_warshall(grafo)
        self.assertTrue(any("arcos" in p for p in grafo.validar_para_floyd()))

    def test_generador_valida_la_red(self) -> None:
        with self.assertRaises(ErrorGrafo):
            list(floyd_iteraciones(Grafo()))

    def test_red_valida_no_reporta_problemas(self) -> None:
        grafo, _ = red_dirigida()
        self.assertEqual(grafo.validar_para_floyd(), [])


if __name__ == "__main__":
    unittest.main(verbosity=2)
