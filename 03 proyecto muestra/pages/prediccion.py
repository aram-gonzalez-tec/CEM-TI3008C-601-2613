"""Página: Predicción (formulario del modelo).

Muestra los controles de dcc más comunes en un formulario para estimar la
calificación de matemáticas de un estudiante. Al presionar el botón, un
callback lee los controles, revisa los datos y llama al modelo.
"""

import dash
from dash import Input, Output, State, callback, dcc, html

from components.etiquetas import ALMUERZO, GENEROS, NIVELES_EDUCATIVOS, nombre_grupo, opciones
from services import db, prediction

dash.register_page(__name__, path="/prediccion", name="Predicción")


# Función para no repetir la etiqueta en cada campo del formulario
def campo(etiqueta, id_control, control, ayuda=None):
    return html.Div(
        [
            html.Label(etiqueta, htmlFor=id_control, className="etiqueta"),
            control,
            html.P(ayuda, className="ayuda") if ayuda else None,
        ],
        className="campo",
    )


# =============================================================================
# LAYOUT (función: las opciones de las listas se consultan al abrir la página)
# =============================================================================

def layout(**kwargs):
    formulario = html.Section(
        [
            html.H2("Datos del estudiante", className="subtitulo"),

            # ---------- 1. Texto: dcc.Input type="text" ----------
            campo("Nombre del estudiante", "entrada-nombre", dcc.Input(
                id="entrada-nombre",
                type="text",
                placeholder="Opcional",
            ), ayuda="Solo para identificar la predicción; el modelo no lo usa."),

            # ---------- 2. Una opción visible: dcc.RadioItems ----------
            campo("Género", "entrada-genero", dcc.RadioItems(
                id="entrada-genero",
                options=opciones(db.generos(), GENEROS),   # label: "Mujer", value: "female"
                value="female",
                inline=True,
                className="opciones",
            )),

            # ---------- 3. Una opción de una lista: dcc.Dropdown ----------
            campo("Grupo", "entrada-grupo", dcc.Dropdown(
                id="entrada-grupo",
                options=[{"label": nombre_grupo(g), "value": g} for g in db.grupos()],
                placeholder="Elige un grupo",
            )),

            campo("Nivel educativo de los padres", "entrada-nivel-educativo", dcc.Dropdown(
                id="entrada-nivel-educativo",
                options=opciones(db.niveles_educativos(), NIVELES_EDUCATIVOS),
                placeholder="Elige un nivel",
            )),

            # ---------- 4. Otra opción visible: dcc.RadioItems ----------
            campo("Tipo de almuerzo", "entrada-almuerzo", dcc.RadioItems(
                id="entrada-almuerzo",
                options=opciones(["standard", "free/reduced"], ALMUERZO),
                value="standard",
                inline=True,
                className="opciones",
            )),

            # ---------- 5. Casillas: dcc.Checklist ----------
            # Su value siempre es una lista: ["completed"] si está marcada, [] si no.
            campo("Curso de preparación", "entrada-preparacion", dcc.Checklist(
                id="entrada-preparacion",
                options=[{"label": "Completó el curso de preparación", "value": "completed"}],
                value=[],
                className="opciones",
            )),

            # ---------- 6. Número: dcc.Input type="number" ----------
            # Si el valor está fuera de min y max, value llega como None.
            campo("Calificación de lectura", "entrada-lectura", dcc.Input(
                id="entrada-lectura",
                type="number",
                min=0, max=100, step=1,
                value=70,
            ), ayuda="De 0 a 100."),

            # ---------- 7. Número en un rango: dcc.Slider ----------
            campo("Calificación de escritura", "entrada-escritura", dcc.Slider(
                id="entrada-escritura",
                min=0, max=100, step=1,
                value=70,
                marks={n: str(n) for n in range(0, 101, 20)},
            )),

            # ---------- 8. Fecha: dcc.DatePickerSingle ----------
            campo("Fecha de la evaluación", "entrada-fecha", dcc.DatePickerSingle(
                id="entrada-fecha",
                date="2025-06-15",                 # usa "date", no "value"
                display_format="DD/MM/YYYY",
                first_day_of_week=1,
            )),

            # ---------- 9. Texto largo: dcc.Textarea ----------
            campo("Observaciones", "entrada-observaciones", dcc.Textarea(
                id="entrada-observaciones",
                placeholder="Opcional",
                rows=3,
                className="control",
            )),

            # ---------- 10. Botón: html.Button ----------
            html.Button("Estimar calificación", id="boton-predecir", className="boton"),
        ],
        className="tarjeta formulario",
    )

    resultado = html.Section(
        [
            html.H2("Resultado", id="resultado-titulo", className="subtitulo"),
            html.P("Calificación estimada en matemáticas", className="kpi-etiqueta"),
            html.P("—", id="resultado-calificacion", className="resultado-valor"),
            html.P("Probabilidad de aprobar (60 o más)", className="kpi-etiqueta"),
            html.P("—", id="resultado-probabilidad", className="resultado-valor"),
            html.P("Llena el formulario y presiona «Estimar calificación».",
                   id="resultado-mensaje", className="ayuda"),
        ],
        className="tarjeta resultado",
    )

    return html.Main(
        [
            html.H1("Estimación de la calificación de matemáticas", className="titulo-pagina"),
            html.Div([formulario, resultado], className="formulario-y-resultado"),
        ],
        className="contenido",
    )


# =============================================================================
# CALLBACK
#   Input: el botón (n_clicks cambia cada vez que se presiona).
#   State: los controles. Se leen al presionar el botón, pero cambiarlos
#          NO ejecuta el callback (por eso no son Input).
# =============================================================================

@callback(
    Output("resultado-titulo", "children"),
    Output("resultado-calificacion", "children"),
    Output("resultado-probabilidad", "children"),
    Output("resultado-mensaje", "children"),
    Input("boton-predecir", "n_clicks"),
    State("entrada-nombre", "value"),
    State("entrada-genero", "value"),
    State("entrada-grupo", "value"),
    State("entrada-nivel-educativo", "value"),
    State("entrada-almuerzo", "value"),
    State("entrada-preparacion", "value"),     # lista
    State("entrada-lectura", "value"),
    State("entrada-escritura", "value"),
    State("entrada-fecha", "date"),            # "date", no "value"
    prevent_initial_call=True,                 # no se ejecuta al abrir la página
)
def estimar(n_clicks, nombre, genero, grupo, nivel, almuerzo, preparacion,
            lectura, escritura, fecha):
    titulo = f"Resultado: {nombre}" if nombre else "Resultado"

    # 1. Revisar los datos antes de llamar al modelo
    faltan = []
    if not grupo:
        faltan.append("el grupo")
    if not nivel:
        faltan.append("el nivel educativo de los padres")
    if lectura is None:
        faltan.append("una calificación de lectura entre 0 y 100")
    if faltan:
        return titulo, "—", "—", "Falta " + ", ".join(faltan) + "."

    # 2. Convertir los controles al formato que espera el modelo
    preparacion = "completed" if "completed" in preparacion else "none"

    # 3. Llamar al modelo (a través del servicio)
    try:
        resultado = prediction.predecir(genero, grupo, nivel, almuerzo,
                                        preparacion, lectura, escritura)
    except RuntimeError as error:
        return titulo, "—", "—", str(error)

    # 4. Dar formato a los resultados
    mensaje = f"Evaluación del {fecha[8:10]}/{fecha[5:7]}/{fecha[:4]}." if fecha else ""
    return (
        titulo,
        f"{resultado['calificacion']:.0f}",
        f"{resultado['probabilidad_aprobar']:.0%}",
        mensaje,
    )
