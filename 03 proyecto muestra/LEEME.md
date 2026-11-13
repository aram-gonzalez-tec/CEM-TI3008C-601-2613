# Desempeño escolar · Aplicación de ejemplo en Dash

Aplicación de ejemplo completa, con la misma estructura que su proyecto: encabezado y pie compartidos, tres páginas, un asistente flotante disponible en todas ellas, y servicios para la base de datos, el modelo predictivo y el chatbot. Todas las páginas funcionan con callbacks. Úsenla para seguir la explicación y como referencia al construir sus propias páginas.

Usa la tabla `students`, creada a partir de `exams.csv` (1,000 estudiantes con sus calificaciones de matemáticas, lectura y escritura).

## Preparar la base de datos (en pgAdmin)

La carpeta `sql/` tiene dos archivos que se ejecutan en orden en la herramienta de consultas de pgAdmin (**Tools > Query Tool**). Cada archivo explica sus pasos al inicio.

1. **`1_crear_base_prueba.sql`**, con la base `postgres` seleccionada: crea la base de datos `prueba`. Después, clic derecho en **Databases > Refresh** para verla.
2. **`2_crear_tabla_students.sql`**, con la base **`prueba`** seleccionada: crea la tabla `students` con su columna `id` y carga los 1,000 estudiantes. Al final debe mostrar `filas_cargadas = 1000`.

El segundo archivo se puede ejecutar varias veces: borra la tabla y la vuelve a crear, sin duplicar datos.

Error frecuente: si al ejecutar el paso 2 aparece la tabla en la base `postgres`, la herramienta de consultas se abrió sobre la base equivocada. Revisen que la pestaña diga `prueba`.

**Alternativa con Python:** `uv run python cargar_csv.py` crea la tabla y carga `sql/exams.csv` en la base que indique su `.env`.

## Ejecutar

1. Copien `.env.example` con el nombre `.env` y escriban:
   - su usuario y contraseña de PostgreSQL (la base ya dice `prueba`);
   - su clave de Gemini en `GEMINI_API_KEY`. Sin clave, la aplicación funciona, pero el asistente avisa que no está configurado.
2. Enciendan su contenedor de Docker.
3. Desde una terminal abierta en esta carpeta:

```
uv sync
uv run python app.py
```

El modelo ya viene entrenado en `models/`. Para volver a entrenarlo con los datos de su base: `uv run python entrenar_modelo.py`.

Y abran en el navegador: http://127.0.0.1:8050

## Archivos

```
estudiantes_app/
├── app.py                  # une encabezado + página activa + pie
├── config.py               # lee el archivo .env (base de datos, Gemini, modelo)
├── entrenar_modelo.py      # entrena el modelo y lo guarda en models/
├── cargar_csv.py           # alternativa en Python para cargar el CSV
├── .env.example            # plantilla del .env
├── models/
│   └── modelo_calificaciones.joblib
├── components/
│   ├── encabezado.py       # menú con dcc.Link (y sus id para marcar la página activa)
│   ├── asistente.py        # chat flotante: botón, ventana y sus callbacks
│   ├── pie.py
│   └── etiquetas.py        # textos en español para los valores de la tabla
├── pages/
│   ├── index.py            # Inicio: tarjetas de acceso
│   ├── tablero.py          # filtros que actualizan indicadores, gráficas y tabla
│   └── prediccion.py       # formulario con los controles más comunes + modelo
├── services/
│   ├── db.py               # consultas a la tabla students
│   ├── prediction.py       # carga el .joblib y hace predicciones
│   └── chatbot.py          # envía las preguntas a Gemini
├── sql/
│   ├── 1_crear_base_prueba.sql     # paso 1 en pgAdmin
│   ├── 2_crear_tabla_students.sql  # paso 2 en pgAdmin
│   └── exams.csv                   # datos originales
└── assets/
    └── styles.css          # Dash lo carga automáticamente
```

## Qué ver en cada archivo

| Archivo | Qué muestra |
|---|---|
| `services/db.py` | Funciones de los tres tipos: indicadores (diccionario), gráficas y tablas (DataFrame) y catálogos (lista). Los filtros opcionales de género y grupo se agregan con una función auxiliar. |
| `services/prediction.py` | El `.joblib` se carga una sola vez. `predecir()` arma un DataFrame con los mismos nombres de columna del entrenamiento. |
| `services/chatbot.py` | Llamada a Gemini con instrucciones, un resumen de los datos de la base como contexto y el historial de la conversación. Si falla, devuelve un mensaje claro en lugar de un error. |
| `app.py` | Un callback que marca en el menú la página activa, con `dcc.Location`. |
| `pages/tablero.py` | Dos callbacks: los filtros actualizan los indicadores, las gráficas y la tabla; la lista de materias decide qué barras se dibujan. |
| `pages/prediccion.py` | Un callback con `State`: lee todos los controles al presionar el botón, revisa los datos, los convierte al formato del modelo y muestra el resultado. |
| `components/asistente.py` | El chat flotante. Está en `app.layout`, fuera de `page_container`, así que aparece en todas las páginas y la conversación sigue al cambiar de página. Un callback lo abre y lo cierra; otro guarda el historial en un `dcc.Store`, llama al chatbot y limpia el campo. Se puede enviar con el botón o con Enter. |
| `components/etiquetas.py` | Cómo mostrar en español los valores que la tabla guarda en inglés, con `label` y `value`. |

## Los callbacks

Un callback conecta componentes: cuando cambia un **Input**, Dash ejecuta la función y pone lo que devuelve en los **Output**, en el mismo orden.

```python
@callback(
    Output("kpi-estudiantes", "children"),     # dónde se muestra el resultado
    Input("entrada-genero", "value"),          # qué dispara el callback
)
def actualizar(genero):                        # recibe el value del Input
    indicadores = db.indicadores_generales(genero)
    return f"{indicadores['estudiantes']:,}"   # va al Output
```

| Concepto | Para qué sirve | Dónde verlo |
|---|---|---|
| `Input` | Cada cambio ejecuta el callback | Filtros del tablero |
| `State` | Se lee al ejecutar, pero cambiarlo **no** ejecuta el callback | Campos del formulario de predicción |
| Varios `Output` | La función devuelve un valor por cada uno, en el mismo orden | `actualizar_tablero` |
| `prevent_initial_call=True` | No se ejecuta al abrir la página, solo al presionar el botón | Predicción y asistente |
| `ctx.triggered_id` | Dice cuál de varios Input disparó el callback | Abrir y cerrar el asistente |
| `n_submit` | Cambia cuando se presiona Enter en un `dcc.Input` | Enviar un mensaje al asistente |
| `no_update` | Deja un Output como estaba | Asistente, si el mensaje está vacío |
| `dcc.Store` | Guarda datos en el navegador entre una ejecución y otra | Historial del asistente |
| `dcc.Location` | Da la ruta actual de la página | Menú en `app.py` |
| Componentes fuera de `page_container` | Se muestran en todas las páginas y no se reinician al navegar | Asistente en `app.py` |
| `layout` como función | Las opciones se consultan cada vez que se abre la página, y la aplicación inicia aunque la base no responda | `tablero.py` y `prediccion.py` |

En las páginas y en `components/` se usa `@callback` (importado de `dash`); en `app.py`, `@app.callback`. Hacen lo mismo.

Para que el tablero cargue con datos, sus callbacks **sí** se ejecutan al abrir la página: los indicadores y las gráficas empiezan vacíos y se llenan en cuanto la página aparece.

## Valores en inglés, textos en español

La tabla guarda `"female"`, `"some college"`, `"completed"`. La aplicación los muestra en español, pero los controles conservan el valor original, que es el que reciben las funciones de `db.py` y el modelo:

```python
from components.etiquetas import GENEROS, opciones

dcc.RadioItems(
    id="entrada-genero",
    options=opciones(db.generos(), GENEROS),
    # → [{"label": "Mujer", "value": "female"}, {"label": "Hombre", "value": "male"}]
)
```

Esto importa para el modelo: si se entrenó con `"female"`, debe recibir `"female"`, no `"Mujer"`.

## Cómo usarlo en su proyecto

- Copien solo las partes que necesiten (un control, una gráfica, la función `campo`), no los archivos completos: su diseño ya tiene su propia estructura y sus clases.
- Para tener el asistente en su aplicación, copien `components/asistente.py`, agréguenlo a `app.layout` como en `app.py` y copien de `styles.css` la sección "Asistente flotante".
- Conserven los `id` de su diseño: `entrada-`, `boton-`, `kpi-`, `grafica-`, `tabla-`, `resultado-`, `chat-`.

## Los controles de `dcc`

La última columna es lo que recibe el callback cuando lee el control.

| Necesito que el usuario... | Control | Propiedad con el valor | El callback recibe |
|---|---|---|---|
| Escriba un texto corto | `dcc.Input(type="text")` | `value` | Texto. Si está vacío: `None` o `""` |
| Escriba un número | `dcc.Input(type="number")` | `value` | Número (`int` o `float`), o `None` |
| Escriba un texto largo | `dcc.Textarea` | `value` | Texto. Si está vacío: `None` o `""` |
| Elija una opción de una lista larga | `dcc.Dropdown` | `value` | El `value` de la opción, o `None` |
| Elija varias opciones de una lista | `dcc.Dropdown(multi=True)` | `value` | Lista, por ejemplo `["Norte", "Centro"]` |
| Elija una opción entre pocas, todas visibles | `dcc.RadioItems` | `value` | El `value` de la opción |
| Marque varias opciones visibles | `dcc.Checklist` | `value` | Lista (vacía si no marcó nada) |
| Elija un número en un rango | `dcc.Slider` | `value` | Número |
| Elija un rango de números | `dcc.RangeSlider` | `value` | Lista de dos números, por ejemplo `[3, 8]` |
| Elija una fecha | `dcc.DatePickerSingle` | **`date`** | Texto con formato `"2025-03-15"` |
| Elija un periodo | `dcc.DatePickerRange` | **`start_date`** y **`end_date`** | Dos textos con formato `"2025-03-15"` |
| Ejecute una acción | `html.Button` | `n_clicks` | Número de veces que se ha presionado |

**Una casilla como sí/no:** un `dcc.Checklist` con una sola opción entrega `["completed"]` si está marcada o `[]` si no. El callback lo convierte en el valor del modelo: `"completed" if "completed" in valor else "none"`.

**Dropdown, RadioItems o Checklist:** si hay más de 5 o 6 opciones, o vienen de la base de datos, usen `dcc.Dropdown`. Si son pocas y fijas, `dcc.RadioItems` (una) o `dcc.Checklist` (varias) dejan todas a la vista.

**Opciones con `label` y `value`:** cuando lo que ve el usuario es distinto de lo que necesita la función o el modelo:

```python
options=[
    {"label": "Estándar", "value": "standard"},             # label: lo que ve el usuario
    {"label": "Gratuito o reducido", "value": "free/reduced"},  # value: lo que recibe el callback
]
```

### Dos controles que no aparecen en el ejemplo

```python
# Rango de números
dcc.RangeSlider(
    id="entrada-rango-matematicas",
    min=0, max=100, step=5,
    value=[60, 100],                     # inicio y fin
    marks={0: "0", 60: "60", 100: "100"},
)

# Periodo de fechas
dcc.DatePickerRange(
    id="entrada-periodo",
    start_date="2025-01-01",
    end_date="2025-03-31",
    display_format="DD/MM/YYYY",
    first_day_of_week=1,
)
```

## Estilos

- Todas las reglas de `styles.css` usan clases, como en sus diseños.
- Los controles de Dash 4 (`dcc.Input`, `dcc.Dropdown`, `dcc.Slider`, el calendario) ya traen su propio estilo. No hace falta darles una clase.
- Para cambiar el color de los controles (slider, casillas, opciones, calendario) basta una variable en `:root`:

  ```css
  :root {
    --Dash-Fill-Interactive-Strong: #1a63a9;
  }
  ```

- Los `dcc.Input` numéricos muestran botones **−** y **+**: es el diseño de Dash 4.
- El asistente flotante está a 80 px del borde inferior para no quedar debajo del menú de Dash, que en modo `debug=True` ocupa la esquina inferior derecha. Para la presentación, con `debug=False`, se puede bajar a 24 px en la regla `.chat-flotante`.
