"""
Carga el archivo sql/exams.csv en la tabla students de PostgreSQL.

Ejecutar desde la carpeta del proyecto:
    uv run python cargar_csv.py              # carga los datos
    uv run python cargar_csv.py --reemplazar # borra los datos actuales y vuelve a cargar

Qué hace:
  1. Se conecta con la URL de DB_URL del archivo .env (a través de config.py).
  2. Crea la tabla students si no existe, con su columna id autoincrementable.
  3. Lee el CSV y cambia los nombres de las columnas al formato de la tabla:
     "math score" -> math_score, "race/ethnicity" -> race_ethnicity
  4. Inserta las filas. El id lo asigna PostgreSQL.

Por seguridad, si la tabla ya tiene datos, no carga nada (para no duplicar
filas) a menos que se use --reemplazar.
"""
import re
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL

try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass

CARPETA = Path(__file__).resolve().parent
ARCHIVO_CSV = CARPETA / "sql" / "exams.csv"
TABLA = "students"
REEMPLAZAR = "--reemplazar" in sys.argv

CREAR_TABLA = """
    CREATE TABLE IF NOT EXISTS students (
        id                           SERIAL PRIMARY KEY,
        gender                       VARCHAR(10),
        race_ethnicity               VARCHAR(20),
        parental_level_of_education  VARCHAR(50),
        lunch                        VARCHAR(20),
        test_preparation_course      VARCHAR(20),
        math_score                   INTEGER,
        reading_score                INTEGER,
        writing_score                INTEGER
    )
"""

COLUMNAS = [
    "gender", "race_ethnicity", "parental_level_of_education", "lunch",
    "test_preparation_course", "math_score", "reading_score", "writing_score",
]


def nombre_de_columna(nombre):
    """'race/ethnicity' -> 'race_ethnicity', 'math score' -> 'math_score'"""
    return re.sub(r"[^a-z0-9]+", "_", nombre.strip().lower()).strip("_")


def detener(mensaje):
    print(f"\n✗ {mensaje}")
    sys.exit(1)


def main():
    # --- 1. Leer el CSV ------------------------------------------------------
    if not ARCHIVO_CSV.exists():
        detener(f"No se encontró el archivo {ARCHIVO_CSV}")

    df = pd.read_csv(ARCHIVO_CSV)
    df.columns = [nombre_de_columna(c) for c in df.columns]

    faltan = [c for c in COLUMNAS if c not in df.columns]
    if faltan:
        detener(f"Al CSV le faltan las columnas: {', '.join(faltan)}")
    df = df[COLUMNAS]
    print(f"CSV leído: {len(df):,} filas.")

    # --- 2. Conectar, crear la tabla y cargar ---------------------------------
    engine = create_engine(DB_URL)
    try:
        # engine.begin(): si algo falla, se deshace todo y la tabla queda como estaba
        with engine.begin() as conexion:
            conexion.execute(text(CREAR_TABLA))
            filas_actuales = conexion.execute(text("SELECT COUNT(*) FROM students")).scalar()

            if filas_actuales and not REEMPLAZAR:
                detener(
                    f"La tabla {TABLA} ya tiene {filas_actuales:,} filas. No se cargó nada "
                    "para no duplicarlas.\n  Para borrarlas y volver a cargar, usa:\n"
                    "  uv run python cargar_csv.py --reemplazar"
                )
            if filas_actuales:
                # Borra las filas y reinicia el id en 1
                conexion.execute(text("TRUNCATE TABLE students RESTART IDENTITY"))
                print(f"Se borraron las {filas_actuales:,} filas anteriores.")

            df.to_sql(TABLA, conexion, if_exists="append", index=False)
            total = conexion.execute(text("SELECT COUNT(*) FROM students")).scalar()
    except Exception as error:
        detener("No se pudo cargar el archivo. Revisa que el contenedor de Docker esté "
                "encendido y que DB_URL sea correcta.\n  Mensaje original: "
                + str(getattr(error, "orig", error)).strip().splitlines()[0])

    print(f"\n✓ Tabla {TABLA}: {total:,} filas cargadas.")
    with engine.connect() as conexion:
        muestra = pd.read_sql(text("SELECT * FROM students ORDER BY id LIMIT 3"), conexion)
    print("\nPrimeras filas:")
    print(muestra.to_string(index=False))


if __name__ == "__main__":
    main()
