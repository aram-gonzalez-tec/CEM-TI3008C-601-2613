"""
Uso del modelo predictivo.

Las páginas NUNCA cargan el modelo directamente: llaman a predecir().
El archivo .joblib se carga UNA sola vez, cuando se importa este archivo.
"""
import joblib
import pandas as pd

from config import RUTA_MODELO

if RUTA_MODELO.exists():
    _MODELO = joblib.load(RUTA_MODELO)
else:
    _MODELO = None


def predecir(genero, grupo, nivel_educativo, almuerzo, preparacion, lectura, escritura):
    """Estima la calificación de matemáticas de un estudiante.

    Recibe los valores con el mismo formato que la tabla students
    (por ejemplo, genero="female", preparacion="completed").

    Devuelve un diccionario:
        {"calificacion": float, "probabilidad_aprobar": float (0 a 1)}
    """
    if _MODELO is None:
        raise RuntimeError(
            "No se encontró el modelo. Ejecuta: uv run python entrenar_modelo.py"
        )

    # El modelo espera un DataFrame con los MISMOS nombres de columna con los
    # que se entrenó. Si cambia un nombre o falta una columna, la predicción falla.
    datos = pd.DataFrame([{
        "gender": genero,
        "race_ethnicity": grupo,
        "parental_level_of_education": nivel_educativo,
        "lunch": almuerzo,
        "test_preparation_course": preparacion,
        "reading_score": lectura,
        "writing_score": escritura,
    }])[_MODELO["columnas"]]

    calificacion = float(_MODELO["regresion"].predict(datos)[0])
    probabilidad = float(_MODELO["clasificacion"].predict_proba(datos)[0][1])

    return {
        "calificacion": min(max(calificacion, 0), 100),   # dentro de 0 a 100
        "probabilidad_aprobar": probabilidad,
    }
