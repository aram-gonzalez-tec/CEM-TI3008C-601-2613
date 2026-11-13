"""
Configuración central de la aplicación.

Es el ÚNICO archivo que lee el archivo .env. Los demás archivos importan
de aquí lo que necesitan:

    from config import DB_URL

Las contraseñas y claves NUNCA se escriben en el código: van en el
archivo .env, que no se entrega ni se sube a ningún repositorio.
"""
import os
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

# --- Base de datos -------------------------------------------------------------
# Formato: postgresql+psycopg://usuario:contraseña@servidor:5432/nombre_bd
DB_URL = os.getenv("DB_URL", "").strip()

if not DB_URL:
    raise RuntimeError(
        "Falta DB_URL. Copia .env.example como .env y escribe ahí los datos "
        "de conexión de tu base de datos."
    )

# --- Modelo predictivo -----------------------------------------------------------
RUTA_MODELO = BASE_DIR / "models" / "modelo_calificaciones.joblib"

# --- Chatbot (Gemini) ------------------------------------------------------------
# Si no hay clave, la aplicación funciona, pero el asistente avisa que no
# está configurado.
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "").strip()
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.8-flash").strip()
