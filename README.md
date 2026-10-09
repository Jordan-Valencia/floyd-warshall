# Algoritmo de Floyd-Warshall — Caminos mínimos entre todos los pares

Software para modelar, representar y analizar una **red dirigida y ponderada**
mediante el algoritmo de **Floyd-Warshall**, determinando las distancias
mínimas entre **todos los pares de nodos** y las rutas correspondientes.

## Requisitos

* Python 3.10 o superior.
* No hay dependencias externas: la interfaz usa `tkinter` (incluido con Python).

## Cómo ejecutar

```bash
python main.py
```

## Cómo probar

```bash
python -m pytest
```

El proyecto incluye 94 pruebas (39 de algoritmo y 55 de interfaz) que cubren
las verificaciones exigidas por el proyecto:

1. **Interpretación de la dirección de los arcos** — un arco `A → B` no crea
   `B → A` y la matriz respeta el sentido.
2. **Cálculo correcto de las distancias mínimas** — comparado contra una
   referencia independiente (Bellman-Ford desde cada origen) en redes
   aleatorias.
3. **Rutas alternativas** — se elige el camino de menor peso aun con más saltos.
4. **Nodos sin conexión** — se muestran con `∞` y se informa "no existe camino".
5. **Consistencia** — la representación gráfica, la matriz inicial, las
   iteraciones y los resultados finales coinciden.

## Estructura del código

| Archivo          | Descripción                                                        |
|------------------|--------------------------------------------------------------------|
| `grafo.py`       | Modelo de la red: nodos, arcos y validaciones (peso > 0).          |
| `floyd.py`       | Implementación propia del algoritmo, matrices, iteraciones y rutas.|
| `interfaz.py`    | Interfaz gráfica (diseño de tres zonas).                           |
| `main.py`        | Punto de entrada.                                                  |
| `test_floyd.py`  | Pruebas del algoritmo y del modelo de red.                         |
| `test_interfaz.py` | Pruebas de la interfaz y de la corrección visual.                |

## Uso de la interfaz

* **Panel izquierdo**: renombrar nodos, editar pesos, eliminar elementos,
  navegar las iteraciones, cargar ejemplo, exportar a CSV.
* **Panel central**: red dirigida. Doble clic crea un nodo; arrastrar de un
  nodo a otro crea un arco; doble clic sobre un nodo fija el origen de la
  consulta (Mayús + doble clic fija el destino); clic derecho elimina.
* **Panel derecho**: matrices de **distancias** y **recorridos** con control
  paso a paso (`◀ ▶` o deslizador) desde la matriz inicial hasta la última
  iteración. Las celdas mejoradas en cada iteración se resaltan en verde.
* **Barra inferior**: consulta de la ruta mínima entre un origen y un destino,
  con su distancia total o el mensaje "No existe camino" si corresponde.

## Conceptos clave

* Solo se admiten **pesos estrictamente positivos** (`> 0`).
* La **matriz de distancias** inicia con `0` en la diagonal y `∞` donde no hay
  conexión directa.
* La **matriz de recorridos** guarda el siguiente nodo a visitar para cada par;
  permite reconstruir cada ruta mínima.