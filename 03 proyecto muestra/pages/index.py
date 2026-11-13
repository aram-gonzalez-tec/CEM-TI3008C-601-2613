"""Página: Inicio."""

import dash
from dash import dcc, html

dash.register_page(__name__, path="/", name="Inicio")


def acceso(titulo, descripcion, ruta):
    return dcc.Link(
        [html.H2(titulo, className="subtitulo"), html.P(descripcion)],
        href=ruta,
        className="tarjeta acceso",
    )


layout = html.Main(
    [
        html.Section(
            [
                html.H1("Desempeño escolar", className="titulo-pagina"),
                html.P("Analiza las calificaciones de 1,000 estudiantes y estima la "
                       "calificación de matemáticas. ¿Tienes una pregunta? Usa el "
                       "botón del asistente, abajo a la derecha.",
                       className="texto-grande"),
            ],
            className="hero",
        ),
        html.Section(
            [
                acceso("Tablero", "Indicadores y gráficas por grupo y género.", "/tablero"),
                acceso("Predicción", "Calificación estimada en matemáticas.", "/prediccion"),
            ],
            className="dos-columnas",
        ),
    ],
    className="contenido",
)
