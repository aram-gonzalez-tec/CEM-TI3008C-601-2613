"""
Acceso a la base de datos (tabla students en PostgreSQL).

Las páginas NUNCA escriben SQL: siempre llaman a las funciones de este
archivo. Cada función devuelve lo que necesita un componente:
  - un diccionario  → tarjetas de indicador
  - un DataFrame    → gráficas y tablas
  - una lista       → opciones de una lista desplegable
"""
import pandas as pd
from sqlalchemy import create_engine, text

from config import DB_URL

engine = create_engine(DB_URL, pool_pre_ping=True)


def consultar(sql, parametros=None):
    """Ejecuta una consulta SQL y devuelve el resultado como DataFrame."""
    with engine.connect() as conexion:
        return pd.read_sql(text(sql), conexion, params=parametros or {})


def _agregar_filtros(sql, parametros, genero, grupo):
    """Agrega al SQL los filtros opcionales, solo si el usuario eligió un valor.
    Los valores siempre van como parámetros (:genero, :grupo)."""
    if genero:
        sql += " AND gender = :genero"
        parametros["genero"] = genero
    if grupo:
        sql += " AND race_ethnicity = :grupo"
        parametros["grupo"] = grupo
    return sql


# =============================================================================
# Indicadores: devuelven UN diccionario
# =============================================================================

def indicadores_generales(genero=None, grupo=None):
    """KPIs para las tarjetas del tablero.

    Devuelve un diccionario:
        {"estudiantes": int, "promedio_matematicas": float,
         "promedio_lectura": float, "promedio_escritura": float,
         "porcentaje_aprobados": float}

    porcentaje_aprobados: proporción (0 a 1) con 60 o más en matemáticas.
    """
    sql = """
        SELECT
            COUNT(*)                                        AS estudiantes,
            COALESCE(ROUND(AVG(math_score), 1), 0)          AS promedio_matematicas,
            COALESCE(ROUND(AVG(reading_score), 1), 0)       AS promedio_lectura,
            COALESCE(ROUND(AVG(writing_score), 1), 0)       AS promedio_escritura,
            COALESCE(AVG(CASE WHEN math_score >= 60 THEN 1.0 ELSE 0 END), 0)
                                                            AS porcentaje_aprobados
        FROM students
        WHERE 1 = 1
    """
    parametros = {}
    sql = _agregar_filtros(sql, parametros, genero, grupo)
    return consultar(sql, parametros).to_dict("records")[0]


# =============================================================================
# Gráficas y tablas: devuelven un DataFrame
# =============================================================================

def promedios_por_nivel_educativo(genero=None, grupo=None):
    """Promedio de cada materia según el nivel educativo de los padres.

    Devuelve un DataFrame con las columnas:
        nivel_educativo, matematicas, lectura, escritura
    """
    sql = """
        SELECT
            parental_level_of_education    AS nivel_educativo,
            ROUND(AVG(math_score), 1)      AS matematicas,
            ROUND(AVG(reading_score), 1)   AS lectura,
            ROUND(AVG(writing_score), 1)   AS escritura
        FROM students
        WHERE 1 = 1
    """
    parametros = {}
    sql = _agregar_filtros(sql, parametros, genero, grupo)
    # array_position ordena los niveles de menor a mayor, no alfabéticamente.
    # En SQL, el apóstrofo dentro de un texto se escribe doble: 'associate''s'
    sql += """
        GROUP BY parental_level_of_education
        ORDER BY array_position(
            ARRAY['some high school', 'high school', 'some college',
                  'associate''s degree', 'bachelor''s degree', 'master''s degree'],
            parental_level_of_education)
    """
    return consultar(sql, parametros)


def promedios_por_grupo():
    """Promedio de cada materia por grupo (lo usa el chatbot como contexto).

    Devuelve un DataFrame con las columnas:
        grupo, estudiantes, matematicas, lectura, escritura
    """
    sql = """
        SELECT
            race_ethnicity                 AS grupo,
            COUNT(*)                       AS estudiantes,
            ROUND(AVG(math_score), 1)      AS matematicas,
            ROUND(AVG(reading_score), 1)   AS lectura,
            ROUND(AVG(writing_score), 1)   AS escritura
        FROM students
        GROUP BY race_ethnicity
        ORDER BY race_ethnicity
    """
    return consultar(sql)


def datos_para_modelo():
    """Todas las columnas que usa el modelo predictivo (para entrenarlo).

    Devuelve un DataFrame con las columnas de la tabla, sin el id.
    """
    sql = """
        SELECT gender, race_ethnicity, parental_level_of_education, lunch,
               test_preparation_course, math_score, reading_score, writing_score
        FROM students
    """
    return consultar(sql)


def calificaciones(genero=None, grupo=None):
    """Calificaciones de cada estudiante, para gráficas de dispersión e histogramas.

    Devuelve un DataFrame con las columnas:
        matematicas, lectura, escritura, preparacion
    """
    sql = """
        SELECT
            math_score               AS matematicas,
            reading_score            AS lectura,
            writing_score            AS escritura,
            test_preparation_course  AS preparacion
        FROM students
        WHERE 1 = 1
    """
    parametros = {}
    sql = _agregar_filtros(sql, parametros, genero, grupo)
    return consultar(sql, parametros)


def lista_estudiantes(genero=None, grupo=None, limite=20):
    """Estudiantes con sus datos, para una tabla.

    Devuelve un DataFrame con las columnas:
        id, genero, grupo, nivel_educativo, almuerzo, preparacion,
        matematicas, lectura, escritura
    """
    sql = """
        SELECT
            id,
            gender                       AS genero,
            race_ethnicity               AS grupo,
            parental_level_of_education  AS nivel_educativo,
            lunch                        AS almuerzo,
            test_preparation_course      AS preparacion,
            math_score                   AS matematicas,
            reading_score                AS lectura,
            writing_score                AS escritura
        FROM students
        WHERE 1 = 1
    """
    parametros = {"limite": limite}
    sql = _agregar_filtros(sql, parametros, genero, grupo)
    sql += " ORDER BY id LIMIT :limite"
    return consultar(sql, parametros)


# =============================================================================
# Catálogos para listas desplegables: devuelven una lista
# =============================================================================

def generos():
    sql = "SELECT DISTINCT gender FROM students ORDER BY gender"
    return consultar(sql)["gender"].tolist()


def grupos():
    sql = "SELECT DISTINCT race_ethnicity FROM students ORDER BY race_ethnicity"
    return consultar(sql)["race_ethnicity"].tolist()


def niveles_educativos():
    sql = """
        SELECT parental_level_of_education AS nivel
        FROM students
        GROUP BY parental_level_of_education
        ORDER BY array_position(
            ARRAY['some high school', 'high school', 'some college',
                  'associate''s degree', 'bachelor''s degree', 'master''s degree'],
            parental_level_of_education)
    """
    return consultar(sql)["nivel"].tolist()
