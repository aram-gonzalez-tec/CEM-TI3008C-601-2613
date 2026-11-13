"""Pie de página compartido por todas las páginas."""

from dash import html

pie = html.Footer(
    html.P("Proyecto de Analítica de datos · Datos: exams.csv", className="pie-texto"),
    className="pie",
)
