"""
Chatbot con la API de Gemini.

Las páginas NUNCA llaman a Gemini directamente: llaman a responder().

El historial de la conversación lo guarda la página (en un dcc.Store) y se
envía completo en cada pregunta, porque Gemini no recuerda los mensajes
anteriores por su cuenta. Cada mensaje es un diccionario:
    {"rol": "usuario" o "asistente", "texto": "..."}
"""
from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL
from services import db

# El cliente se crea una sola vez. Sin clave, el asistente avisa que no está listo.
_cliente = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

# Solo se envían los últimos mensajes, para no mandar conversaciones enormes
MAX_MENSAJES_HISTORIAL = 20

INSTRUCCIONES = """
Eres el asistente de una aplicación que analiza el desempeño escolar de
1,000 estudiantes en matemáticas, lectura y escritura (calificaciones de 0 a 100;
se aprueba con 60 o más).

Reglas:
- Responde en español, de forma breve y clara (máximo 4 oraciones).
- Usa SOLO los datos que aparecen abajo. Si la pregunta no se puede responder
  con ellos, dilo y sugiere qué sí puedes responder.
- No inventes cifras. Cuando des un número, di de qué grupo o categoría es.
- Los valores de los datos están en inglés: tradúcelos al responder
  (female = mujeres, male = hombres, completed = completó el curso de preparación).

DATOS:
"""


def _contexto():
    """Resume los datos de la base para que Gemini pueda responder sobre ellos."""
    generales = db.indicadores_generales()
    por_genero = {g: db.indicadores_generales(genero=g) for g in db.generos()}
    preparacion = (db.calificaciones()
                     .groupby("preparacion")[["matematicas", "lectura", "escritura"]]
                     .mean().round(1))

    partes = [
        f"Indicadores generales: {generales}",
        f"Indicadores por género: {por_genero}",
        "Promedios por grupo:\n" + db.promedios_por_grupo().to_csv(index=False),
        "Promedios por nivel educativo de los padres:\n"
        + db.promedios_por_nivel_educativo().to_csv(index=False),
        "Promedios según el curso de preparación:\n" + preparacion.to_csv(),
    ]
    return "\n\n".join(partes)


def responder(historial, pregunta):
    """Envía la pregunta a Gemini junto con el historial y devuelve la respuesta.

    historial: lista de mensajes anteriores [{"rol": ..., "texto": ...}, ...]
    pregunta:  texto que escribió el usuario
    Devuelve:  el texto de la respuesta
    """
    if _cliente is None:
        return ("El asistente no está configurado: falta GEMINI_API_KEY en el "
                "archivo .env.")

    # Gemini usa los roles "user" y "model"
    mensajes = [
        types.Content(
            role="user" if m["rol"] == "usuario" else "model",
            parts=[types.Part(text=m["texto"])],
        )
        for m in historial[-MAX_MENSAJES_HISTORIAL:]
    ]
    mensajes.append(types.Content(role="user", parts=[types.Part(text=pregunta)]))

    try:
        respuesta = _cliente.models.generate_content(
            model=GEMINI_MODEL,
            contents=mensajes,
            config=types.GenerateContentConfig(
                system_instruction=INSTRUCCIONES + _contexto(),
            ),
        )
        return respuesta.text or "No obtuve una respuesta. Intenta de nuevo."
    except Exception as error:
        # El detalle va a la terminal; al usuario se le muestra un mensaje claro
        print(f"[chatbot] Error al llamar a Gemini: {error}")
        if "NOT_FOUND" in str(error):
            print("[chatbot] El modelo ya no está disponible. Cambia GEMINI_MODEL en el "
                  "archivo .env por el modelo que indica el mensaje.")
        return ("No pude comunicarme con el asistente en este momento. "
                "Revisa tu conexión a internet y tu clave de Gemini.")
