"""
Textos en español para los valores de la base de datos.

La tabla guarda los valores en inglés ("female", "some college"). La
aplicación los muestra en español, pero las funciones de db.py y el modelo
siguen recibiendo el valor original. Para eso, las opciones de los
controles usan "label" (lo que ve el usuario) y "value" (el valor real).
"""

GENEROS = {"female": "Mujer", "male": "Hombre"}

NIVELES_EDUCATIVOS = {
    "some high school": "Preparatoria incompleta",
    "high school": "Preparatoria",
    "some college": "Universidad incompleta",
    "associate's degree": "Técnico superior",
    "bachelor's degree": "Licenciatura",
    "master's degree": "Maestría",
}

ALMUERZO = {"standard": "Estándar", "free/reduced": "Gratuito o reducido"}

PREPARACION = {"completed": "Completado", "none": "No tomado"}

MATERIAS = {"matematicas": "Matemáticas", "lectura": "Lectura", "escritura": "Escritura"}


def nombre_grupo(valor):
    """'group A' -> 'Grupo A'"""
    return valor.replace("group", "Grupo")


def opciones(valores, textos):
    """Convierte una lista de valores en opciones para un control de dcc.

    opciones(["female", "male"], GENEROS)
    -> [{"label": "Mujer", "value": "female"}, {"label": "Hombre", "value": "male"}]
    """
    return [{"label": textos.get(valor, valor), "value": valor} for valor in valores]
