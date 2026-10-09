"""Modelo de una red dirigida y ponderada.

Este modulo define las clases basicas (Nodo, Arco) y el contenedor Grafo,
acompanado de las validaciones necesarias para construir correctamente la red
que luego procesara el algoritmo de Floyd-Warshall.

La logica esta inspirada en el proyecto de Dijkstra del curso, adaptada a los
requerimientos del proyecto de Floyd: los pesos solo pueden ser estrictamente
positivos (> 0) y las validaciones ya no dependen de un nodo de origen.
"""

from __future__ import annotations


class ErrorGrafo(Exception):
    """Error de dominio lanzado cuando una operacion sobre la red no es valida."""


class Nodo:
    """Vertice de la red. Guarda un identificador, un nombre y su posicion."""

    def __init__(self, id: int, nombre: str, x: float = 0.0, y: float = 0.0):
        self.id = id
        self.nombre = nombre
        self.x = x
        self.y = y

    def etiqueta(self) -> str:
        return self.nombre

    def __repr__(self) -> str:
        return f"Nodo(id={self.id}, nombre={self.nombre!r}, x={self.x:g}, y={self.y:g})"


class Arco:
    """Arco dirigido con un peso asociado. Va de origen hacia destino."""

    def __init__(self, origen: Nodo, destino: Nodo, peso: float):
        self.origen = origen
        self.destino = destino
        self.peso = peso

    def etiqueta(self) -> str:
        return f"{self.origen.nombre}->{self.destino.nombre} ({self.peso:g})"

    def __repr__(self) -> str:
        return f"Arco({self.etiqueta()})"


def validar_peso(valor) -> float:
    """Convierte y valida un peso.

    El proyecto de Floyd solo admite pesos estrictamente positivos. Se rechazan
    valores no numericos, negativos y el cero.
    """
    try:
        peso = float(valor)
    except (TypeError, ValueError):
        raise ErrorGrafo(f"El peso '{valor}' no es un numero valido") from None

    if peso <= 0:
        raise ErrorGrafo(
            f"El peso {peso:g} no es valido: Floyd exige pesos estrictamente positivos (> 0)"
        )
    return peso


class Grafo:
    """Red dirigida y ponderada compuesta por nodos y arcos."""

    def __init__(self):
        self.nodos: dict[int, Nodo] = {}
        self.arcos: list[Arco] = []
        self._siguiente_id = 1

    # ------------------------------------------------------------------
    # Nodos
    # ------------------------------------------------------------------
    def agregar_nodo(self, nombre: str | None = None, x: float = 0.0, y: float = 0.0) -> Nodo:
        if nombre is None or str(nombre).strip() == "":
            nombre = f"N{self._siguiente_id}"
        nombre = str(nombre).strip()

        if any(n.nombre == nombre for n in self.nodos.values()):
            raise ErrorGrafo(f"Ya existe un nodo llamado '{nombre}'.")

        nodo = Nodo(self._siguiente_id, nombre, float(x), float(y))
        self.nodos[nodo.id] = nodo
        self._siguiente_id += 1
        return nodo

    def mover_nodo(self, nodo: Nodo, x: float, y: float) -> None:
        self._exigir_nodo(nodo)
        nodo.x = float(x)
        nodo.y = float(y)

    def renombrar_nodo(self, nodo: Nodo, nombre: str) -> None:
        self._exigir_nodo(nodo)
        nuevo = str(nombre).strip()
        if nuevo == "":
            raise ErrorGrafo("El nombre del nodo no puede estar vacio.")
        if any(n is not nodo and n.nombre == nuevo for n in self.nodos.values()):
            raise ErrorGrafo(f"Ya existe un nodo llamado '{nuevo}'.")
        nodo.nombre = nuevo

    def eliminar_nodo(self, nodo: Nodo) -> None:
        self._exigir_nodo(nodo)
        self.arcos = [a for a in self.arcos if a.origen is not nodo and a.destino is not nodo]
        del self.nodos[nodo.id]

    # ------------------------------------------------------------------
    # Arcos
    # ------------------------------------------------------------------
    def agregar_arco(self, origen: Nodo, destino: Nodo, peso) -> Arco:
        self._exigir_nodo(origen, "origen")
        self._exigir_nodo(destino, "destino")

        if origen is destino:
            raise ErrorGrafo(
                f"No se puede crear un arco de '{origen.nombre}' hacia si mismo."
            )

        peso = validar_peso(peso)

        if self.buscar_arco(origen, destino) is not None:
            raise ErrorGrafo(
                f"Ya existe el arco {origen.nombre}->{destino.nombre}. "
                "Modifique su peso en lugar de duplicarlo."
            )

        arco = Arco(origen, destino, peso)
        self.arcos.append(arco)
        return arco

    def buscar_arco(self, origen: Nodo, destino: Nodo) -> Arco | None:
        for arco in self.arcos:
            if arco.origen is origen and arco.destino is destino:
                return arco
        return None

    def modificar_peso(self, arco: Arco, peso) -> None:
        if arco not in self.arcos:
            raise ErrorGrafo("El arco indicado no pertenece a la red actual.")
        self.buscar_arco(arco.origen, arco.destino).peso = validar_peso(peso)

    def eliminar_arco(self, arco: Arco) -> None:
        if arco not in self.arcos:
            raise ErrorGrafo("El arco indicado no pertenece a la red actual.")
        self.arcos.remove(arco)

    # ------------------------------------------------------------------
    # Consultas
    # ------------------------------------------------------------------
    def adyacentes(self, nodo: Nodo) -> list[Arco]:
        return [a for a in self.arcos if a.origen is nodo]

    def incidentes(self, nodo: Nodo) -> list[Arco]:
        return [a for a in self.arcos if a.destino is nodo]

    def nodos_por_nombre(self, nombre: str) -> Nodo | None:
        for nodo in self.nodos.values():
            if nodo.nombre == nombre:
                return nodo
        return None

    def lista_nodos(self) -> list[Nodo]:
        """Nodos en el orden de insercion (define el orden de las matrices)."""
        return list(self.nodos.values())

    def peso_total(self) -> float:
        return sum(a.peso for a in self.arcos)

    # ------------------------------------------------------------------
    # Validacion para Floyd
    # ------------------------------------------------------------------
    def validar_para_floyd(self) -> list[str]:
        """Devuelve una lista de problemas que impiden ejecutar Floyd.

        Floyd-Warshall calcula distancias entre todos los pares; por eso no
        necesita un nodo de origen, pero si una red con nodos y arcos.
        """
        problemas: list[str] = []

        if not self.nodos:
            problemas.append("La red no contiene nodos.")
            return problemas

        if not self.arcos:
            problemas.append("La red no contiene arcos.")

        for arco in self.arcos:
            if arco.peso <= 0:
                problemas.append(
                    f"El arco {arco.etiqueta()} tiene un peso no positivo."
                )

        return list(dict.fromkeys(problemas))

    # ------------------------------------------------------------------
    # Utilidades internas
    # ------------------------------------------------------------------
    def _exigir_nodo(self, nodo: Nodo, rol: str = "nodo") -> None:
        if not isinstance(nodo, Nodo):
            raise ErrorGrafo(f"El {rol} indicado no es valido.")
        if nodo.id not in self.nodos or self.nodos[nodo.id] is not nodo:
            raise ErrorGrafo(
                f"El {rol} '{getattr(nodo, 'nombre', nodo)}' no existe en la red."
            )

    def limpiar(self) -> None:
        self.nodos.clear()
        self.arcos.clear()
        self._siguiente_id = 1

    def __repr__(self) -> str:
        return f"<Grafo nodos={len(self.nodos)} arcos={len(self.arcos)}>"
