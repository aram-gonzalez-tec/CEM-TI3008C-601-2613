"""
Asistente flotante (chatbot), disponible en todas las páginas.

Es un botón fijo en la esquina inferior derecha. Al presionarlo, se abre
una ventana de chat. Como está en app.layout, FUERA de page_container, no
se borra al cambiar de página: la conversación continúa.

El historial se guarda en un dcc.Store: un componente invisible que guarda
datos en el navegador. Cada mensaje es {"rol": "usuario"/"asistente", "texto": "..."}.
"""

from dash import Input, Output, State, callback, ctx, dcc, html, no_update

from services import chatbot

BIENVENIDA = {"rol": "asistente",
              "texto": "Hola. Puedo responder preguntas sobre el desempeño de los "
                       "estudiantes. Por ejemplo: ¿qué grupo tiene el promedio más "
                       "alto en matemáticas?"}


def mensaje(texto, de_usuario):
    clase = "mensaje mensaje-usuario" if de_usuario else "mensaje mensaje-asistente"
    return html.Div(texto, className=clase)


def dibujar(historial):
    """Convierte la lista de mensajes en componentes.

    Se dibujan en orden inverso porque la caja usa flex-direction: column-reverse
    (ver styles.css): así el mensaje más reciente queda abajo y la caja se
    mantiene desplazada hasta el final sin código adicional.
    """
    return [mensaje(m["texto"], de_usuario=(m["rol"] == "usuario"))
            for m in reversed(historial)]


asistente = html.Div(
    [
        dcc.Store(id="chat-memoria", data=[BIENVENIDA]),

        # ---------- Ventana del chat (oculta al inicio) ----------
        html.Section(
            [
                html.Div(
                    [
                        html.P("Asistente", className="chat-titulo"),
                        html.Button("×", id="boton-chat-cerrar", className="chat-cerrar",
                                    title="Cerrar"),
                    ],
                    className="chat-cabecera",
                ),
                dcc.Loading(
                    html.Div(dibujar([BIENVENIDA]), id="chat-historial",
                             className="chat-historial"),
                    type="dot",
                    parent_className="chat-cuerpo",
                    delay_show=300,
                    overlay_style={"visibility": "visible", "opacity": 0.6},
                ),
                html.Div(
                    [
                        dcc.Input(
                            id="chat-mensaje",
                            type="text",
                            placeholder="Escribe tu pregunta...",
                            autoComplete="off",
                            className="chat-entrada",
                        ),
                        html.Button("Enviar", id="boton-enviar", className="boton"),
                    ],
                    className="chat-barra",
                ),
            ],
            id="chat-panel",
            className="chat-panel",
        ),

        # ---------- Botón flotante ----------
        html.Button("💬 Asistente", id="boton-chat-abrir", className="chat-boton"),
    ],
    className="chat-flotante",
)


# =============================================================================
# CALLBACKS
# =============================================================================

@callback(
    Output("chat-panel", "className"),
    Input("boton-chat-abrir", "n_clicks"),
    Input("boton-chat-cerrar", "n_clicks"),
    State("chat-panel", "className"),
    prevent_initial_call=True,
)
def abrir_o_cerrar(n_abrir, n_cerrar, clase_actual):
    # ctx.triggered_id dice cuál de los Input disparó el callback
    if ctx.triggered_id == "boton-chat-cerrar":
        return "chat-panel"
    # El botón flotante abre si está cerrado y cierra si está abierto
    if "chat-panel-abierto" in clase_actual:
        return "chat-panel"
    return "chat-panel chat-panel-abierto"


@callback(
    Output("chat-historial", "children"),
    Output("chat-memoria", "data"),
    Output("chat-mensaje", "value"),           # para limpiar el campo
    Input("boton-enviar", "n_clicks"),
    Input("chat-mensaje", "n_submit"),         # n_submit cambia al presionar Enter
    State("chat-mensaje", "value"),
    State("chat-memoria", "data"),
    prevent_initial_call=True,
)
def enviar(n_clicks, n_submit, pregunta, historial):
    # Si el campo está vacío, no se cambia nada
    if not pregunta or not pregunta.strip():
        return no_update, no_update, no_update

    pregunta = pregunta.strip()
    # Se envía el historial SIN la bienvenida, que no es parte de la conversación
    respuesta = chatbot.responder(historial[1:], pregunta)

    historial = historial + [
        {"rol": "usuario", "texto": pregunta},
        {"rol": "asistente", "texto": respuesta},
    ]
    return dibujar(historial), historial, ""
