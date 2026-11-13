"""Página: Tablero.

Los filtros (género y grupo) actualizan los indicadores, las gráficas y la
tabla. La lista de materias decide qué barras se dibujan.
"""

import dash
import dash_ag_grid as dag
import plotly.express as px
from dash import Input, Output, callback, dcc, html

from components.etiquetas import GENEROS, MATERIAS, NIVELES_EDUCATIVOS, PREPARACION, nombre_grupo, opciones
from services import db

dash.register_page(__name__, path="/tablero", name="Tablero")


# =============================================================================
# 1. VALORES INICIALES DE LOS FILTROS
#    Con los callbacks, ya no son fijos: son los valores con los que abre
#    la página. Después, el usuario los cambia con los filtros.
# =============================================================================

GENERO = None                                        # None = todos
GRUPO = None                                         # None = todos
MATERIAS_ELEGIDAS = ["matematicas", "lectura", "escritura"]

COLOR = "#1A63A9"                                    # color principal del diseño
COLORES = {"matematicas": "#1A63A9", "lectura": "#2E9E8F", "escritura": "#E07A2E"}


# =============================================================================
# 2. FUNCIONES QUE CREAN LAS GRÁFICAS
#    Reciben un DataFrame y devuelven una figura de Plotly. Los callbacks
#    las llaman cada vez que cambia un filtro.
# =============================================================================

def aplicar_estilo(figura):
    figura.update_layout(template="plotly_white", height=320,
                         margin={"l": 10, "r": 10, "t": 10, "b": 10},
                         legend_title_text="")
    return figura


def figura_vacia(mensaje):
    """Figura sin datos con un mensaje en el centro."""
    figura = px.scatter()
    figura.update_xaxes(visible=False)
    figura.update_yaxes(visible=False)
    figura.add_annotation(text=mensaje, showarrow=False, font={"size": 16})
    return aplicar_estilo(figura)


def figura_promedios_por_nivel(df, materias):
    if not materias:
        return figura_vacia("Elige al menos una materia")
    df = df.assign(nivel_educativo=df["nivel_educativo"].map(NIVELES_EDUCATIVOS))
    figura = px.bar(
        df, x="nivel_educativo", y=materias,       # una barra por materia elegida
        barmode="group",                           # barras lado a lado
        labels={"nivel_educativo": "Nivel educativo de los padres",
                "value": "Promedio", "variable": "Materia"},
        color_discrete_map=COLORES,
    )
    figura.for_each_trace(lambda barra: barra.update(name=MATERIAS[barra.name]))
    figura.update_yaxes(range=[0, 100])
    return aplicar_estilo(figura)


def figura_lectura_vs_matematicas(df):
    figura = px.scatter(
        df, x="lectura", y="matematicas", color="preparacion",
        labels={"lectura": "Lectura", "matematicas": "Matemáticas",
                "preparacion": "Curso de preparación"},
        color_discrete_map={"completed": "#E07A2E", "none": COLOR},
        opacity=0.6,
    )
    figura.for_each_trace(lambda punto: punto.update(name=PREPARACION[punto.name]))
    return aplicar_estilo(figura)


def figura_distribucion_matematicas(df):
    figura = px.histogram(
        df, x="matematicas", nbins=20,
        labels={"matematicas": "Calificación de matemáticas"},
        color_discrete_sequence=[COLOR],
    )
    figura.update_yaxes(title_text="Estudiantes")
    return aplicar_estilo(figura)


# =============================================================================
# 3. FUNCIÓN QUE CREA UNA TARJETA DE INDICADOR
# =============================================================================

def tarjeta_kpi(etiqueta, id_kpi):
    return html.Article(
        [
            html.P(etiqueta, className="kpi-etiqueta"),
            html.P("—", id=id_kpi, className="kpi-valor"),   # lo llena el callback
        ],
        className="kpi",
    )


# =============================================================================
# 4. LAYOUT
#    Es una FUNCIÓN: Dash la ejecuta cada vez que alguien abre la página, así
#    las opciones de los filtros siempre vienen actualizadas de la base de datos.
#    Los indicadores, gráficas y tabla empiezan vacíos: los callbacks los
#    llenan en cuanto la página se abre.
# =============================================================================

def layout(**kwargs):
    return html.Main(
        [
            html.H1("Desempeño de los estudiantes", className="titulo-pagina"),

            # ---------- Filtros ----------
            html.Section(
                [
                    html.Div([
                        html.Label("Género", htmlFor="entrada-genero", className="etiqueta"),
                        dcc.Dropdown(
                            id="entrada-genero",
                            options=opciones(db.generos(), GENEROS),
                            value=GENERO,
                            placeholder="Todos",
                        ),
                    ], className="campo"),

                    html.Div([
                        html.Label("Grupo", htmlFor="entrada-grupo", className="etiqueta"),
                        dcc.Dropdown(
                            id="entrada-grupo",
                            options=[{"label": nombre_grupo(g), "value": g} for g in db.grupos()],
                            value=GRUPO,
                            placeholder="Todos",
                        ),
                    ], className="campo"),

                    html.Div([
                        html.Label("Materias", htmlFor="entrada-materias", className="etiqueta"),
                        dcc.Dropdown(
                            id="entrada-materias",
                            options=opciones(list(MATERIAS), MATERIAS),
                            value=MATERIAS_ELEGIDAS,
                            multi=True,
                        ),
                    ], className="campo"),
                ],
                className="filtros",
            ),

            # ---------- Indicadores ----------
            html.Section(
                [
                    tarjeta_kpi("Estudiantes", "kpi-estudiantes"),
                    tarjeta_kpi("Promedio de matemáticas", "kpi-promedio-matematicas"),
                    tarjeta_kpi("Promedio de lectura", "kpi-promedio-lectura"),
                    tarjeta_kpi("Aprobados en matemáticas", "kpi-aprobados"),
                ],
                className="kpis",
            ),

            # ---------- Gráficas ----------
            html.Section(
                [
                    html.H2("Promedio por nivel educativo de los padres", className="subtitulo"),
                    dcc.Graph(id="grafica-promedios-nivel", config={"displayModeBar": False}),
                ],
                className="tarjeta",
            ),
            html.Section(
                [
                    html.Div([
                        html.H2("Lectura y matemáticas", className="subtitulo"),
                        dcc.Graph(id="grafica-lectura-matematicas", config={"displayModeBar": False}),
                    ], className="tarjeta"),
                    html.Div([
                        html.H2("Distribución de matemáticas", className="subtitulo"),
                        dcc.Graph(id="grafica-distribucion-matematicas", config={"displayModeBar": False}),
                    ], className="tarjeta"),
                ],
                className="dos-columnas",
            ),

            # ---------- Tabla ----------
            html.Section(
                [
                    html.H2("Estudiantes", className="subtitulo"),
                    dag.AgGrid(
                        id="tabla-estudiantes",
                        rowData=[],                          # lo llena el callback
                        columnDefs=[
                            {"field": "id", "headerName": "Id", "maxWidth": 80},
                            {"field": "genero", "headerName": "Género"},
                            {"field": "grupo", "headerName": "Grupo"},
                            {"field": "nivel_educativo", "headerName": "Nivel educativo", "minWidth": 210},
                            {"field": "preparacion", "headerName": "Preparación"},
                            {"field": "matematicas", "headerName": "Matemáticas"},
                            {"field": "lectura", "headerName": "Lectura"},
                            {"field": "escritura", "headerName": "Escritura"},
                        ],
                        defaultColDef={"sortable": True, "filter": True, "flex": 1},
                        dashGridOptions={"pagination": True, "paginationPageSize": 10,
                                         "domLayout": "autoHeight"},
                    ),
                ],
                className="tarjeta",
            ),
        ],
        className="contenido",
    )


# =============================================================================
# 5. CALLBACKS
#    @callback conecta componentes: cuando cambia un Input, Dash ejecuta la
#    función con los valores nuevos y pone lo que devuelve en los Output,
#    en el MISMO orden.
# =============================================================================

@callback(
    Output("kpi-estudiantes", "children"),
    Output("kpi-promedio-matematicas", "children"),
    Output("kpi-promedio-lectura", "children"),
    Output("kpi-aprobados", "children"),
    Output("grafica-lectura-matematicas", "figure"),
    Output("grafica-distribucion-matematicas", "figure"),
    Output("tabla-estudiantes", "rowData"),
    Input("entrada-genero", "value"),     # "female", "male" o None (todos)
    Input("entrada-grupo", "value"),      # "group A" ... o None (todos)
)
def actualizar_tablero(genero, grupo):
    # 1. Consultar los datos con los filtros elegidos
    indicadores = db.indicadores_generales(genero, grupo)
    notas = db.calificaciones(genero, grupo)
    estudiantes = db.lista_estudiantes(genero, grupo, limite=50)

    # 2. Preparar la tabla con los valores en español
    tabla = estudiantes.assign(
        genero=estudiantes["genero"].map(GENEROS),
        grupo=estudiantes["grupo"].map(nombre_grupo),
        nivel_educativo=estudiantes["nivel_educativo"].map(NIVELES_EDUCATIVOS),
        preparacion=estudiantes["preparacion"].map(PREPARACION),
    )

    # 3. Devolver un valor por cada Output, en el mismo orden
    return (
        f"{indicadores['estudiantes']:,}",
        f"{indicadores['promedio_matematicas']:.1f}",
        f"{indicadores['promedio_lectura']:.1f}",
        f"{indicadores['porcentaje_aprobados']:.0%}",
        figura_lectura_vs_matematicas(notas),
        figura_distribucion_matematicas(notas),
        tabla.to_dict("records"),
    )


@callback(
    Output("grafica-promedios-nivel", "figure"),
    Input("entrada-genero", "value"),
    Input("entrada-grupo", "value"),
    Input("entrada-materias", "value"),   # lista: ["matematicas", "lectura", ...]
)
def actualizar_promedios(genero, grupo, materias):
    promedios = db.promedios_por_nivel_educativo(genero, grupo)
    return figura_promedios_por_nivel(promedios, materias)
