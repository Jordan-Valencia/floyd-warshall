"""Implementacion propia del algoritmo de Floyd-Warshall.

Calcula las distancias minimas entre TODOS los pares de nodos de una red
dirigida y ponderada, y reconstruye la ruta asociada a cada par.

El algoritmo se implementa explicitamente (triple bucle sobre los nodos
intermedios k). No se usa ninguna libreria que entregue las distancias
minimas ya calculadas.

Estructuras de datos
--------------------
Las matrices se manejan como listas de listas alineadas con el orden de
insercion de los nodos (``Grafo.lista_nodos``):

* ``distancias[i][j]``: distancia minima conocida de i a j. Vale ``INF`` si no
  hay conexion y ``0`` en la diagonal principal.
* ``sucesores[i][j]``: indice del siguiente nodo a visitar para ir de i a j
  (matriz de recorridos). Vale ``None`` si no hay camino.
"""

from __future__ import annotations

from math import inf
from typing import Iterator

from grafo import Arco, ErrorGrafo, Grafo, Nodo

INF = inf
TOLERANCIA = 1e-12


def formatear(valor: float) -> str:
    """Devuelve 'inf' (infinito) o el numero sin ceros decimales sobrantes."""
    if valor == INF:
        return "\u221e"
    return f"{valor:g}"


class Cambio:
    """Registro de una mejora de distancia dentro de una iteracion."""

    def __init__(
        self,
        i: int,
        j: int,
        origen: Nodo,
        destino: Nodo,
        via: Nodo,
        distancia_previa: float,
        distancia_nueva: float,
    ):
        self.i = i
        self.j = j
        self.origen = origen
        self.destino = destino
        self.via = via
        self.distancia_previa = distancia_previa
        self.distancia_nueva = distancia_nueva

    def texto(self) -> str:
        return (
            f"{self.origen.nombre}\u2192{self.destino.nombre}: "
            f"{formatear(self.distancia_previa)} \u2192 {formatear(self.distancia_nueva)} "
            f"usando {self.via.nombre}"
        )

    def __repr__(self) -> str:
        return f"Cambio({self.texto()!r})"


class Iteracion:
    """Estado de las matrices en un paso del algoritmo.

    ``k`` vale -1 para la matriz inicial y 0..n-1 para cada nodo intermedio
    evaluado. Las matrices son copias independientes de ese instante.
    """

    def __init__(
        self,
        k: int,
        nodo_intermedio: Nodo | None,
        distancias: list[list[float]],
        sucesores: list[list[int | None]],
        cambios: list[Cambio],
        nodos: list[Nodo],
    ):
        self.k = k
        self.nodo_intermedio = nodo_intermedio
        self.distancias = [fila[:] for fila in distancias]
        self.sucesores = [fila[:] for fila in sucesores]
        self.cambios = cambios
        self.nodos = nodos

    @property
    def es_inicial(self) -> bool:
        return self.k < 0

    def titulo(self) -> str:
        if self.es_inicial:
            return "Matriz inicial"
        return f"Iteraci\u00f3n k = {self.k + 1}  (nodo {self.nodo_intermedio.nombre})"

    def descripcion(self) -> str:
        if self.es_inicial:
            return (
                "Matriz de distancias construida directamente de los arcos. "
                "La diagonal es 0 y \u221e indica ausencia de conexion directa."
            )
        if not self.cambios:
            return (
                f"Al usar {self.nodo_intermedio.nombre} como nodo intermedio no "
                "se mejoro ninguna distancia."
            )
        return (
            f"Al usar {self.nodo_intermedio.nombre} como nodo intermedio se "
            f"mejoraron {len(self.cambios)} distancia(s)."
        )

    def __repr__(self) -> str:
        return f"Iteracion(k={self.k}, mejoras={len(self.cambios)})"


class ResultadoFloyd:
    """Resultado completo del algoritmo para todos los pares de nodos."""

    def __init__(
        self,
        grafo: Grafo,
        nodos: list[Nodo],
        distancias: list[list[float]],
        sucesores: list[list[int | None]],
        iteraciones: list[Iteracion],
    ):
        self.grafo = grafo
        self.nodos = nodos
        self.distancias = distancias
        self.sucesores = sucesores
        self.iteraciones = iteraciones
        self.indice = {nodo.id: k for k, nodo in enumerate(nodos)}

    # ------------------------------------------------------------------
    # Consultas por nodo
    # ------------------------------------------------------------------
    def indice_de(self, nodo: Nodo) -> int:
        return self.indice[nodo.id]

    def distancia(self, origen: Nodo, destino: Nodo) -> float | None:
        valor = self.distancias[self.indice_de(origen)][self.indice_de(destino)]
        return None if valor == INF else valor

    def alcanzable(self, origen: Nodo, destino: Nodo) -> bool:
        return self.distancia(origen, destino) is not None

    def camino(self, origen: Nodo, destino: Nodo) -> list[Nodo]:
        """Ruta minima de origen a destino. Lista vacia si no hay conexion."""
        i = self.indice_de(origen)
        j = self.indice_de(destino)
        if self.distancias[i][j] == INF:
            return []
        if i == j:
            return [origen]

        camino: list[Nodo] = [origen]
        actual = i
        for _ in range(len(self.nodos)):
            siguiente = self.sucesores[actual][j]
            if siguiente is None:
                return []
            actual = siguiente
            camino.append(self.nodos[actual])
            if actual == j:
                return camino
        return []

    def arcos_camino(self, origen: Nodo, destino: Nodo) -> list[Arco]:
        camino = self.camino(origen, destino)
        arcos: list[Arco] = []
        for k in range(len(camino) - 1):
            arco = self.grafo.buscar_arco(camino[k], camino[k + 1])
            if arco is not None:
                arcos.append(arco)
        return arcos

    def suma_camino(self, origen: Nodo, destino: Nodo) -> list[float]:
        """Pesos de los arcos que forman la ruta minima (para mostrar la suma)."""
        return [a.peso for a in self.arcos_camino(origen, destino)]

    def pares_inalcanzables(self) -> list[tuple[Nodo, Nodo]]:
        """Pares (origen, destino) distintos sin conexion."""
        pares: list[tuple[Nodo, Nodo]] = []
        for i, origen in enumerate(self.nodos):
            for j, destino in enumerate(self.nodos):
                if i != j and self.distancias[i][j] == INF:
                    pares.append((origen, destino))
        return pares

    def __repr__(self) -> str:
        return (
            f"ResultadoFloyd(nodos={len(self.nodos)}, "
            f"iteraciones={len(self.iteraciones)})"
        )


def construir_matrices(
    grafo: Grafo,
) -> tuple[list[Nodo], list[list[float]], list[list[int | None]]]:
    """Construye la matriz inicial de distancias y la de recorridos.

    - Las distancias empiezan en infinito; la diagonal en 0.
    - Cada arco i->j fija distancias[i][j] = peso y sucesores[i][j] = j.
    - La matriz respeta la direccion: no se agrega el arco simetrico.
    """
    nodos = grafo.lista_nodos()
    n = len(nodos)
    indice = {nodo.id: k for k, nodo in enumerate(nodos)}

    distancias = [[INF] * n for _ in range(n)]
    sucesores: list[list[int | None]] = [[None] * n for _ in range(n)]

    for i in range(n):
        distancias[i][i] = 0.0
        sucesores[i][i] = i

    for arco in grafo.arcos:
        i = indice[arco.origen.id]
        j = indice[arco.destino.id]
        if arco.peso < distancias[i][j]:
            distancias[i][j] = arco.peso
            sucesores[i][j] = j

    return nodos, distancias, sucesores


def _ejecutar_floyd(
    grafo: Grafo,
) -> tuple[list[Nodo], list[list[float]], list[list[int | None]], list[Iteracion]]:
    """Ejecuta Floyd-Warshall y devuelve matrices finales e iteraciones."""
    nodos, distancias, sucesores = construir_matrices(grafo)
    n = len(nodos)

    iteraciones: list[Iteracion] = [
        Iteracion(-1, None, distancias, sucesores, [], nodos)
    ]

    for k in range(n):
        cambios: list[Cambio] = []
        nodo_k = nodos[k]
        for i in range(n):
            if distancias[i][k] == INF:
                continue
            for j in range(n):
                if distancias[k][j] == INF:
                    continue
                candidato = distancias[i][k] + distancias[k][j]
                if candidato < distancias[i][j] - TOLERANCIA:
                    cambios.append(
                        Cambio(
                            i, j, nodos[i], nodos[j], nodo_k,
                            distancias[i][j], candidato,
                        )
                    )
                    distancias[i][j] = candidato
                    sucesores[i][j] = sucesores[i][k]
        iteraciones.append(
            Iteracion(k, nodo_k, distancias, sucesores, cambios, nodos)
        )

    return nodos, distancias, sucesores, iteraciones


def floyd_warshall(grafo: Grafo) -> ResultadoFloyd:
    """Ejecuta Floyd-Warshall validando antes la red."""
    problemas = grafo.validar_para_floyd()
    if problemas:
        raise ErrorGrafo(" ".join(problemas))

    nodos, distancias, sucesores, iteraciones = _ejecutar_floyd(grafo)
    return ResultadoFloyd(grafo, nodos, distancias, sucesores, iteraciones)


def floyd_iteraciones(grafo: Grafo) -> Iterator[Iteracion]:
    """Genera la matriz inicial y la matriz resultante de cada iteracion k."""
    problemas = grafo.validar_para_floyd()
    if problemas:
        raise ErrorGrafo(" ".join(problemas))

    _, _, _, iteraciones = _ejecutar_floyd(grafo)
    for iteracion in iteraciones:
        yield iteracion
