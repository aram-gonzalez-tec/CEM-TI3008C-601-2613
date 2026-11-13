"""
Entrena el modelo de ejemplo y lo guarda en models/modelo_calificaciones.joblib.

Ejecutar desde la carpeta del proyecto (con la base de datos encendida):
    uv run python entrenar_modelo.py

El modelo estima, a partir de los datos de un estudiante:
  - su calificación de matemáticas (regresión lineal);
  - la probabilidad de que apruebe matemáticas, con 60 o más (regresión logística).

En su proyecto, el modelo lo entrenan en su notebook. Lo que importa para la
aplicación es el archivo .joblib y la lista exacta de columnas que espera.
"""
import joblib
from sklearn.compose import ColumnTransformer
from sklearn.linear_model import LinearRegression, LogisticRegression
from sklearn.metrics import accuracy_score, mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder

from config import RUTA_MODELO
from services import db

# Columnas que recibe el modelo, en este orden
CATEGORICAS = ["gender", "race_ethnicity", "parental_level_of_education",
               "lunch", "test_preparation_course"]
NUMERICAS = ["reading_score", "writing_score"]
COLUMNAS = CATEGORICAS + NUMERICAS


def pipeline(estimador):
    """Convierte las columnas de texto en columnas numéricas y aplica el estimador."""
    preparacion = ColumnTransformer([
        ("categoricas", OneHotEncoder(handle_unknown="ignore"), CATEGORICAS),
        ("numericas", "passthrough", NUMERICAS),
    ])
    return Pipeline([("preparacion", preparacion), ("modelo", estimador)])


def main():
    df = db.datos_para_modelo()
    X = df[COLUMNAS]
    y_calificacion = df["math_score"]
    y_aprueba = (df["math_score"] >= 60).astype(int)

    X_ent, X_prueba, yc_ent, yc_prueba, ya_ent, ya_prueba = train_test_split(
        X, y_calificacion, y_aprueba, test_size=0.2, random_state=42)

    regresion = pipeline(LinearRegression()).fit(X_ent, yc_ent)
    clasificacion = pipeline(LogisticRegression(max_iter=1000)).fit(X_ent, ya_ent)

    print("Evaluación con el 20% de los datos que el modelo no vio:")
    print(f"  Calificación: R² = {r2_score(yc_prueba, regresion.predict(X_prueba)):.2f}, "
          f"error promedio = {mean_absolute_error(yc_prueba, regresion.predict(X_prueba)):.1f} puntos")
    print(f"  Aprobar:      exactitud = {accuracy_score(ya_prueba, clasificacion.predict(X_prueba)):.0%}")

    # Se vuelve a entrenar con todos los datos antes de guardar
    regresion.fit(X, y_calificacion)
    clasificacion.fit(X, y_aprueba)

    RUTA_MODELO.parent.mkdir(exist_ok=True)
    joblib.dump(
        {"regresion": regresion, "clasificacion": clasificacion, "columnas": COLUMNAS},
        RUTA_MODELO,
    )
    print(f"\n✓ Modelo guardado en {RUTA_MODELO.relative_to(RUTA_MODELO.parent.parent)}")


if __name__ == "__main__":
    main()
