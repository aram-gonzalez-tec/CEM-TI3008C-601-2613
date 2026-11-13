"""
Aplicación principal.

Ejecutar con:
    uv run python app.py
y abrir en el navegador: http://127.0.0.1:8050

Une las partes de la página y marca en el menú la página activa.
Los callbacks de cada página están en su propio archivo de pages/; los del
asistente, en components/asistente.py.
"""

from dash import Dash, Input, Output, dcc, html, page_container

from components.asistente import asistente
from components.encabezado import ENLACES, encabezado
from components.pie import pie

# use_pages=True: Dash busca las páginas en la carpeta pages/
app = Dash(__name__, use_pages=True, title="Desempeño escolar")
server = app.server

app.layout = html.Div([
    dcc.Location(id="url"),     # componente invisible: sabe en qué ruta está el usuario
    encabezado,                 # components/encabezado.py (igual en todas las páginas)
    page_container,             # aquí aparece la página que el usuario está viendo
    pie,                        # components/pie.py (igual en todas las páginas)
    asistente,                  # components/asistente.py: chat flotante, en todas las páginas
])


# Marca en el menú el enlace de la página activa.
# Un Output por cada enlace; se devuelve una clase por cada uno, en el mismo orden.
@app.callback(
    [Output(id_enlace, "className") for id_enlace in ENLACES],
    Input("url", "pathname"),
)
def marcar_pagina_activa(ruta):
    return [
        "nav-enlace nav-enlace-activo" if ruta == destino else "nav-enlace"
        for destino in ENLACES.values()
    ]


if __name__ == "__main__":
    app.run(debug=True)
