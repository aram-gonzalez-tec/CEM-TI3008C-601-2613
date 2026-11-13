"""Encabezado compartido por todas las páginas."""

from dash import dcc, html

# Ruta de cada enlace del menú. app.py los usa para marcar la página activa.
ENLACES = {
    "nav-inicio": "/",
    "nav-tablero": "/tablero",
    "nav-prediccion": "/prediccion",
}

encabezado = html.Header(
    [
        html.P("Desempeño escolar", className="logo"),
        html.Nav(
            [
                # dcc.Link cambia de página sin recargar el navegador.
                dcc.Link("Inicio", href="/", id="nav-inicio", className="nav-enlace"),
                dcc.Link("Tablero", href="/tablero", id="nav-tablero", className="nav-enlace"),
                dcc.Link("Predicción", href="/prediccion", id="nav-prediccion", className="nav-enlace"),
            ],
            className="nav",
        ),
    ],
    className="encabezado",
)
