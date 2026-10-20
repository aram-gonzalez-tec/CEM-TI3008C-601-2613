"""
Validador del sitio antes del traslado a Dash.

Revisa que las páginas HTML y el archivo styles.css cumplan las reglas
del proyecto, y hace una prueba de conversión con html-to-dash.

Uso:
    python validar_sitio.py                 # revisa la carpeta "html"
    python validar_sitio.py mi_carpeta      # revisa otra carpeta

Requisitos:
    pip install beautifulsoup4 html-to-dash

    html-to-dash instala automáticamente dash y dash-svg, que el validador
    usa para la prueba de conversión y para revisar los SVG.

Al terminar, el reporte se guarda en "reporte_validacion.md", dentro de la
carpeta revisada. En VS Code se puede ver con formato con Ctrl + Shift + V
(Cmd + Shift + V en Mac).

Niveles de los hallazgos:
    ERROR  Impide o pone en riesgo la conversión a Dash. Debe corregirse.
    AVISO  No impide la conversión, pero incumple una regla o una
           recomendación del proyecto. Conviene corregirlo.
    INFO   Información útil; no requiere acción.
"""

import io
import logging
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from contextlib import redirect_stderr, redirect_stdout

try:
    from bs4 import BeautifulSoup, Comment, NavigableString, Tag
except ImportError:
    print("Falta la librería beautifulsoup4. Instálala con:")
    print("    pip install beautifulsoup4")
    sys.exit(2)

try:
    from html_to_dash import parse_html
except ImportError:
    parse_html = None

try:
    from dash import dcc, html
except ImportError:
    dcc = html = None

try:
    import dash_svg
except ImportError:
    dash_svg = None

# Evita errores con acentos en consolas de Windows.
try:
    sys.stdout.reconfigure(encoding="utf-8")
except Exception:
    pass


# ---------------------------------------------------------------------------
# Configuración de las reglas
# ---------------------------------------------------------------------------

PAGINA_PRINCIPAL = "index.html"
ARCHIVOS_RESERVADOS = {"header.html", "footer.html"}
PATRON_ARCHIVO = re.compile(r"^[a-z0-9]+(_[a-z0-9]+)*\.html$")
PATRON_ID = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
PREFIJOS_ID = ("kpi-", "grafica-", "tabla-", "entrada-", "boton-",
               "resultado-", "chat-", "reporte-")
CLASES_ACTIVAS = {"activo", "activa", "active", "actual", "current", "seleccionado"}
CONTROLES = ("input", "select", "textarea", "button")
SELECTORES_PERMITIDOS = {":root", "body"}
SELECTORES_TOLERADOS = {"*", "*::before", "*::after", "*:before", "*:after"}


# ---------------------------------------------------------------------------
# Registro de hallazgos
# ---------------------------------------------------------------------------

class Reporte:
    def __init__(self):
        self.hallazgos = defaultdict(list)  # archivo -> [(nivel, linea, texto)]

    def agregar(self, archivo, nivel, texto, linea=None):
        self.hallazgos[archivo].append((nivel, linea, texto))

    def error(self, archivo, texto, linea=None):
        self.agregar(archivo, "ERROR", texto, linea)

    def aviso(self, archivo, texto, linea=None):
        self.agregar(archivo, "AVISO", texto, linea)

    def info(self, archivo, texto, linea=None):
        self.agregar(archivo, "INFO", texto, linea)

    def contar(self, nivel):
        return sum(1 for hs in self.hallazgos.values() for h in hs if h[0] == nivel)

    def texto(self):
        orden = {"ERROR": 0, "AVISO": 1, "INFO": 2}
        lineas = []
        for archivo in sorted(self.hallazgos, key=lambda a: (a != "General", a)):
            hs = sorted(self.hallazgos[archivo], key=lambda h: (orden[h[0]], h[1] or 0))
            lineas.append("")
            lineas.append("=" * 70)
            lineas.append(archivo)
            lineas.append("=" * 70)
            for nivel, linea, texto in hs:
                donde = f" (línea {linea})" if linea else ""
                lineas.append(f"[{nivel}]{donde} {texto}")
        e, a = self.contar("ERROR"), self.contar("AVISO")
        lineas.append("")
        lineas.append("-" * 70)
        lineas.append(f"Resumen: {e} error(es), {a} aviso(s).")
        if e == 0:
            lineas.append("El sitio está listo para el traslado a Dash.")
            if a:
                lineas.append("Se recomienda atender también los avisos.")
        else:
            lineas.append("Corrige los errores y vuelve a ejecutar el validador.")
        return "\n".join(lineas)


    def markdown(self, carpeta):
        orden = {"ERROR": 0, "AVISO": 1, "INFO": 2}
        e, a, i = self.contar("ERROR"), self.contar("AVISO"), self.contar("INFO")
        md = ["# Reporte de validación del sitio", ""]
        md.append(f"**Carpeta revisada:** `{carpeta}`  ")
        md.append(f"**Fecha:** {datetime.now():%Y-%m-%d %H:%M}")
        md.append("")
        if e == 0 and a == 0:
            md.append("> ✅ **El sitio está listo para el traslado a Dash.**")
        elif e == 0:
            md.append("> ✅ **El sitio está listo para el traslado a Dash.** "
                      "Se recomienda atender también los avisos.")
        else:
            md.append("> ❌ **El sitio todavía no está listo para el traslado a Dash.** "
                      "Corrige los errores y vuelve a ejecutar el validador.")
        md += ["", "| Nivel | Cantidad | Qué significa |", "|---|---|---|",
               f"| ❌ Errores | {e} | Impiden o ponen en riesgo la conversión. Deben corregirse. |",
               f"| ⚠️ Avisos | {a} | Incumplen una regla o recomendación. Conviene corregirlos. |",
               f"| ℹ️ Información | {i} | Datos útiles; no requieren acción. |", ""]

        archivos = sorted(self.hallazgos, key=lambda x: (x != "General", x))
        md += ["## Resumen por archivo", "", "| Archivo | ❌ Errores | ⚠️ Avisos |", "|---|---|---|"]
        for archivo in archivos:
            hs = self.hallazgos[archivo]
            ne = sum(1 for h in hs if h[0] == "ERROR")
            na = sum(1 for h in hs if h[0] == "AVISO")
            ancla = re.sub(r"[^a-z0-9-]", "", archivo.lower().replace(" ", "-"))
            md.append(f"| [{archivo}](#{ancla}) | {ne} | {na} |")
        md.append("")

        titulos = {"ERROR": "❌ Errores", "AVISO": "⚠️ Avisos", "INFO": "ℹ️ Información"}
        for archivo in archivos:
            hs = sorted(self.hallazgos[archivo], key=lambda h: (orden[h[0]], h[1] or 0))
            md += [f"## {archivo}", ""]
            for nivel in ("ERROR", "AVISO", "INFO"):
                del_nivel = [h for h in hs if h[0] == nivel]
                if not del_nivel:
                    continue
                md += [f"### {titulos[nivel]}", ""]
                for _, linea, texto in del_nivel:
                    donde = f"**Línea {linea}:** " if linea else ""
                    casilla = "- " if nivel == "INFO" else "- [ ] "
                    md.append(f"{casilla}{donde}{a_markdown(texto)}")
                md.append("")
        md += ["---", "",
               "Marca cada casilla al corregir el problema y vuelve a ejecutar "
               "`python validar_sitio.py` para generar un reporte actualizado."]
        return "\n".join(md) + "\n"


def a_markdown(texto):
    """Pone en formato de código las etiquetas HTML para que se vean en Markdown."""
    texto = texto.replace("|", "\\|")
    return re.sub(r"(<[a-zA-Z/][^<>]*>)", r"`\1`", texto)


def linea_de(nodo):
    return getattr(nodo, "sourceline", None)


def describir(tag):
    partes = [tag.name]
    if tag.get("id"):
        partes.append(f'id="{tag["id"]}"')
    if tag.get("class"):
        partes.append(f'class="{" ".join(tag["class"])}"')
    return "<" + " ".join(partes) + ">"


# ---------------------------------------------------------------------------
# Revisión de cada página HTML
# ---------------------------------------------------------------------------

def es_tailwind(tag):
    """Indica si un <script> o <style> sirve para cargar o configurar Tailwind."""
    texto = (tag.get("src") or "") + (tag.string or "")
    tipo = tag.get("type") or ""
    return "tailwind" in texto.lower() or "tailwind" in tipo.lower()


def revisar_head(nombre, soup, reporte, estado):
    head = soup.find("head")
    if not head:
        reporte.aviso(nombre, "La página no tiene <head>.")
        return
    for script in head.find_all("script"):
        if es_tailwind(script):
            estado["usa_tailwind"] = True
        else:
            reporte.error(nombre, "Hay un <script> que no es de Tailwind. "
                          "No se permite JavaScript.", linea_de(script))
    for estilo in head.find_all("style"):
        if es_tailwind(estilo):
            estado["usa_tailwind"] = True
        else:
            reporte.error(nombre, "Hay estilos dentro de una etiqueta <style>. "
                          "Se pierden en la conversión; muévelos a styles.css.",
                          linea_de(estilo))
    for link in head.find_all("link"):
        rel = " ".join(link.get("rel") or [])
        href = link.get("href") or ""
        if "stylesheet" in rel and "fonts.googleapis.com" in href:
            reporte.aviso(nombre, "La fuente se carga con <link> en el <head>, que se "
                          "pierde en la conversión. Usa @import en la primera "
                          "línea de styles.css.", linea_de(link))
        elif "stylesheet" in rel and not href.startswith("http"):
            estado["hojas_locales"].add(href)


def revisar_estructura(nombre, body, reporte):
    if body.attrs:
        atributos = ", ".join(body.attrs)
        reporte.error(nombre, f"La etiqueta <body> tiene atributos ({atributos}). "
                      "Se eliminan en la conversión; define los estilos generales "
                      "con el selector body en styles.css.", linea_de(body))

    hijos = []
    for hijo in body.children:
        if isinstance(hijo, Comment):
            continue
        if isinstance(hijo, NavigableString):
            if hijo.strip():
                reporte.error(nombre, f'Hay texto suelto dentro de <body>: "{hijo.strip()[:40]}". '
                              "Debe ir dentro de header, main o footer.")
            continue
        if isinstance(hijo, Tag):
            if hijo.name == "script":
                if es_tailwind(hijo):
                    continue
                reporte.error(nombre, "Hay un <script> dentro de <body>. "
                              "No se permite JavaScript.", linea_de(hijo))
                continue
            hijos.append(hijo)

    nombres = [h.name for h in hijos]
    if nombres != ["header", "main", "footer"]:
        encontrados = ", ".join(f"<{n}>" for n in nombres) or "ninguno"
        reporte.error(nombre, "El <body> debe contener exactamente <header>, <main> y "
                      f"<footer>, en ese orden. Se encontró: {encontrados}.",
                      linea_de(body))

    # header y footer fuera de su lugar
    for etiqueta in ("header", "footer"):
        for t in body.find_all(etiqueta):
            if t.parent is not body:
                reporte.error(nombre, f"Hay un <{etiqueta}> dentro de {describir(t.parent)}. "
                              "El script de conversión lo eliminaría junto con su "
                              "contenido. Usa un <div> con una clase.", linea_de(t))
    mains = body.find_all("main")
    if len(mains) > 1:
        reporte.error(nombre, "Hay más de un <main> en la página.", linea_de(mains[1]))


def revisar_contenido(nombre, body, reporte, carpeta, estado_imagenes):
    for form in body.find_all("form"):
        reporte.error(nombre, "Se usa <form>. Reemplázalo por un <div> con las mismas "
                      "clases.", linea_de(form))
    for script in body.find_all("script"):
        if script.parent is not body and not es_tailwind(script):
            reporte.error(nombre, "Hay un <script> dentro del contenido. "
                          "No se permite JavaScript.", linea_de(script))
    for estilo in body.find_all("style"):
        reporte.error(nombre, "Hay una etiqueta <style> dentro de <body>. "
                      "Mueve esos estilos a styles.css.", linea_de(estilo))

    for tag in body.find_all(True):
        if tag.has_attr("style"):
            reporte.error(nombre, f"{describir(tag)} usa el atributo style. "
                          "Mueve ese estilo a una clase en styles.css.", linea_de(tag))
        eventos = [a for a in tag.attrs if a.lower().startswith("on")]
        if eventos:
            reporte.error(nombre, f"{describir(tag)} tiene atributos de JavaScript "
                          f"({', '.join(eventos)}).", linea_de(tag))

    for control in body.find_all(CONTROLES):
        if control.name == "input" and (control.get("type") or "").lower() == "hidden":
            continue
        if not control.get("id"):
            reporte.error(nombre, f"El control <{control.name}> no tiene id. "
                          "Todos los controles necesitan un id único.", linea_de(control))

    locales = []
    for img in body.find_all("img"):
        src = img.get("src") or ""
        if src.startswith(("http://", "https://", "//")):
            reporte.aviso(nombre, f'La imagen "{src[:60]}" es externa. Se recomienda '
                          "descargarla y guardarla junto con el proyecto.", linea_de(img))
        elif src and not src.startswith("data:"):
            locales.append(src)
            ruta = os.path.normpath(os.path.join(carpeta, src.lstrip("/")))
            if not os.path.exists(ruta):
                reporte.aviso(nombre, f'No se encontró la imagen "{src}". Revisa la ruta.',
                              linea_de(img))
    if locales:
        estado_imagenes.update(locales)


def revisar_ids(nombre, body, reporte, ids_contenido):
    vistos = {}
    for tag in body.find_all(id=True):
        valor = tag["id"]
        if valor in vistos:
            reporte.error(nombre, f'El id "{valor}" está repetido en la página '
                          f"(también en la línea {vistos[valor]}).", linea_de(tag))
        else:
            vistos[valor] = linea_de(tag)
        if not PATRON_ID.match(valor):
            reporte.error(nombre, f'El id "{valor}" no sigue la convención: solo '
                          "minúsculas, números y guiones, sin acentos ni espacios.",
                          linea_de(tag))
        elif (not valor.startswith(PREFIJOS_ID)
              and tag.name not in ("header", "nav", "main", "footer")
              and tag.name != "svg" and not tag.find_parent("svg")):
            reporte.aviso(nombre, f'El id "{valor}" no usa un prefijo de la convención '
                          f"({', '.join(PREFIJOS_ID)}). Revisa si corresponde a un "
                          "elemento dinámico.", linea_de(tag))

    main = body.find("main")
    if main:
        for tag in main.find_all(id=True):
            ids_contenido[tag["id"]].append(nombre)


def normalizar(tag):
    """Representación de un elemento sin marcas de página activa ni espacios."""
    copia = BeautifulSoup(str(tag), "html.parser")
    for t in copia.find_all(True):
        if t.get("class"):
            t["class"] = [c for c in t["class"] if c not in CLASES_ACTIVAS]
            if not t["class"]:
                del t["class"]
        if t.has_attr("aria-current"):
            del t["aria-current"]
    return re.sub(r"\s+", " ", str(copia)).strip()


def revisar_navegacion(nombre, body, reporte):
    header = body.find("header")
    if not header:
        return
    for a in header.find_all("a"):
        href = a.get("href") or ""
        if href.endswith(".html"):
            reporte.aviso(nombre, f'El enlace "{href}" apunta a un archivo .html. '
                          'Usa la ruta de la página, por ejemplo "/" o "/reportes".',
                          linea_de(a))
        elif href in ("", "#"):
            reporte.aviso(nombre, f'El enlace "{a.get_text(strip=True)}" no tiene una '
                          "ruta definida.", linea_de(a))


def prueba_conversion(nombre, body, reporte):
    """Repite lo que hace el script de conversión y revisa que funcione."""
    if parse_html is None or dash_svg is None:
        return
    copia = BeautifulSoup(str(body), "html.parser").find("body")
    for t in copia.find_all(["header", "footer"]):
        t.decompose()
    try:
        codigo, mensajes = convertir(str(copia))
    except Exception as e:
        reporte.error(nombre, f"La prueba de conversión falló: {type(e).__name__}: {e}")
        return

    error = ejecutar(codigo)
    if error:
        reporte.error(nombre, "El código que genera la conversión no funciona en Dash "
                      f"({error}). Revisa los elementos de la página.")

    for linea in mensajes:
        etiquetas = re.search(r"Tags\s*:\s*Unsupported \[(.*?)\]", linea)
        atributos = re.search(r"Attrs:\s*Unsupported \[(.*?)\] in (\S+) removed", linea)
        if etiquetas:
            nombres = [n.strip() for n in etiquetas.group(1).split(",")]
            if "input" in nombres:
                reporte.info(nombre, "Los <input> no tienen equivalente en el módulo html "
                             "de Dash y se eliminarán en la conversión. Es lo esperado: "
                             "se reemplazarán a mano por dcc.Input con el mismo id, así "
                             "que verifica que estén registrados en el inventario.")
                nombres.remove("input")
            if nombres:
                reporte.aviso(nombre, "La conversión eliminará estas etiquetas no "
                              f"soportadas: {', '.join(nombres)}.")
        elif atributos:
            componente = atributos.group(2)
            if componente.startswith("dash_svg."):
                continue  # los SVG se revisan por separado, con más detalle
            attrs = [a.strip() for a in atributos.group(1).split(",") if a.strip() != "for"]
            if attrs:
                reporte.aviso(nombre, f"La conversión eliminará los atributos "
                              f"{', '.join(attrs)} de {componente}.")


ATRIBUTOS_SVG_A_CSS = re.compile(r"^(stroke|fill|opacity|stop-|font-|text-|"
                                  r"letter-|dominant-|vector-effect|color)")


def convertir(fragmento):
    """Convierte un fragmento HTML con html-to-dash y devuelve (código, mensajes)."""
    registro = logging.getLogger("html-to-dash")
    capturado = io.StringIO()
    manejador = logging.StreamHandler(capturado)
    manejador.setFormatter(logging.Formatter("%(message)s"))
    anteriores = registro.handlers[:]
    registro.handlers = [manejador]
    try:
        with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
            codigo = parse_html(fragmento, if_return=True, enable_dash_svg=True)
    finally:
        registro.handlers = anteriores
    return codigo, capturado.getvalue().splitlines()


def ejecutar(codigo):
    """Intenta construir los componentes de Dash generados. Devuelve el error o None."""
    if html is None or dash_svg is None or not codigo:
        return None
    try:
        eval(codigo, {"html": html, "dcc": dcc, "dash_svg": dash_svg})
    except Exception as e:
        return f"{type(e).__name__}: {str(e).splitlines()[0][:200]}"
    return None


def revisar_svg(nombre, body, reporte):
    """Convierte cada SVG por separado y explica qué se perdería en Dash."""
    if parse_html is None or dash_svg is None:
        return
    for numero, svg in enumerate(body.find_all("svg"), 1):
        ln = linea_de(svg)
        donde = f"El SVG número {numero} (dentro de {describir(svg.parent)})"
        try:
            codigo, mensajes = convertir(f"<div>{svg}</div>")
        except Exception as e:
            reporte.error(nombre, f"{donde} no se pudo convertir: {type(e).__name__}: {e}", ln)
            continue
        error = ejecutar(codigo)
        if error:
            reporte.error(nombre, f"{donde} genera código que Dash no acepta ({error}). "
                          "Guárdalo como archivo .svg y muéstralo con <img>.", ln)
            continue

        a_css, sin_solucion, etiquetas = set(), set(), set()
        for m in mensajes:
            t = re.search(r"Tags\s*:\s*Unsupported \[(.*?)\]", m)
            a = re.search(r"Attrs:\s*Unsupported \[(.*?)\] in (\S+) removed", m)
            if t:
                etiquetas.update(x.strip() for x in t.group(1).split(","))
            elif a:
                for attr in (x.strip() for x in a.group(1).split(",")):
                    if ATRIBUTOS_SVG_A_CSS.match(attr):
                        a_css.add(attr)
                    else:
                        sin_solucion.add(attr)

        if etiquetas or sin_solucion:
            perdido = sorted(etiquetas | sin_solucion)
            reporte.error(nombre, f"{donde} usa elementos o atributos que Dash no puede "
                          f"conservar ({', '.join(perdido)}), por lo que el gráfico se verá "
                          "incompleto o no aparecerá. Por ejemplo, los degradados pierden "
                          "sus colores y los íconos con <use> no se muestran. Guarda el SVG "
                          "como archivo .svg y muéstralo con <img src=\"assets/nombre.svg\">.", ln)
        if a_css:
            reporte.aviso(nombre, f"{donde} perderá en la conversión los atributos "
                          f"{', '.join(sorted(a_css))}, por lo que su apariencia cambiará "
                          "(por ejemplo, líneas más delgadas). Muévelos a una clase en "
                          "styles.css y asigna esa clase al SVG; por ejemplo: "
                          "`.icono { stroke-width: 2; stroke-linecap: round; }`", ln)
        if not (etiquetas or sin_solucion or a_css):
            reporte.info(nombre, f"{donde} se convertirá correctamente con dash-svg.", ln)


# ---------------------------------------------------------------------------
# Revisión del CSS
# ---------------------------------------------------------------------------

def quitar_comentarios(css):
    # Reemplaza los comentarios por espacios, conservando los saltos de línea
    # para que los números de línea sigan siendo correctos.
    return re.sub(r"/\*.*?\*/", lambda m: re.sub(r"[^\n]", " ", m.group()), css, flags=re.S)


def bloques_css(css, inicio=0, fin=None):
    """Recorre el CSS y devuelve (prelude, cuerpo, posición) de cada bloque."""
    fin = len(css) if fin is None else fin
    i = inicio
    prelude_inicio = inicio
    while i < fin:
        c = css[i]
        if c == ";":
            yield css[prelude_inicio:i].strip(), None, prelude_inicio
            prelude_inicio = i + 1
        elif c == "{":
            nivel, j = 1, i + 1
            while j < fin and nivel:
                if css[j] == "{":
                    nivel += 1
                elif css[j] == "}":
                    nivel -= 1
                j += 1
            yield css[prelude_inicio:i].strip(), (i + 1, j - 1), prelude_inicio
            i = j
            prelude_inicio = j
            continue
        i += 1


def selector_permitido(selector):
    """Devuelve None si el selector cumple la regla, o el motivo si no."""
    s = selector.strip()
    if s in SELECTORES_PERMITIDOS:
        return None
    if s in SELECTORES_TOLERADOS:
        return "tolerado"
    if ">" in s:
        return "usa un selector de hijo directo (>)"
    if "+" in s or "~" in s:
        return "usa un selector de hermanos (+ o ~)"
    if "#" in s:
        return "usa un selector de id"
    if "[" in s:
        return "usa un selector de atributo"
    for parte in s.split():
        base = re.sub(r"::?[a-zA-Z-]+(\([^)]*\))?", "", parte)  # quita pseudo-clases
        if not base:
            continue  # por ejemplo ":hover" suelto
        if not base.startswith("."):
            etiqueta = re.match(r"[a-zA-Z][\w-]*", base)
            return f'incluye el selector de etiqueta "{etiqueta.group() if etiqueta else base}"'
    return None


def revisar_css(nombre, ruta, reporte, usa_tailwind):
    try:
        with open(ruta, encoding="utf8") as f:
            original = f.read()
    except UnicodeDecodeError:
        with open(ruta, encoding="latin-1") as f:
            original = f.read()
    css = quitar_comentarios(original)

    def linea(pos):
        while pos < len(css) and css[pos].isspace():
            pos += 1
        return css.count("\n", 0, pos) + 1

    hubo_regla = False
    tolerados_avisados = False

    def recorrer(inicio, fin, dentro_de=""):
        nonlocal hubo_regla, tolerados_avisados
        for prelude, cuerpo, pos in bloques_css(css, inicio, fin):
            if not prelude:
                continue
            ln = linea(pos)
            if prelude.startswith("@import"):
                if hubo_regla:
                    reporte.error(nombre, "@import debe ir al inicio del archivo, antes "
                                  "de cualquier regla; de lo contrario se ignora.", ln)
                continue
            if prelude.startswith("@tailwind") or prelude.startswith("@apply"):
                continue
            hubo_regla = True
            if prelude.startswith(("@media", "@supports", "@layer", "@container")):
                if cuerpo:
                    recorrer(cuerpo[0], cuerpo[1], prelude)
                continue
            if prelude.startswith("@"):
                continue  # @font-face, @keyframes, etc.
            if cuerpo is None:
                continue
            for selector in prelude.split(","):
                motivo = selector_permitido(selector)
                if motivo == "tolerado":
                    if not tolerados_avisados:
                        reporte.info(nombre, f'El selector "{selector.strip()}" (por ejemplo, '
                                     "para box-sizing) se tolera; no afecta la conversión.", ln)
                        tolerados_avisados = True
                elif motivo:
                    reporte.error(nombre, f'El selector `{selector.strip()}` {motivo}. '
                                  "Usa solo clases (excepto :root y body).", ln)
            # colores escritos directamente fuera de :root
            if prelude.strip() != ":root" and not usa_tailwind:
                declaraciones = css[cuerpo[0]:cuerpo[1]]
                if re.search(r"#[0-9a-fA-F]{3,8}\b|rgba?\(|hsla?\(", declaraciones):
                    reporte.aviso(nombre, f'La regla "{prelude[:50]}" escribe un color '
                                  "directamente. Usa una variable con var().", ln)

    recorrer(0, len(css))

    if not usa_tailwind and ":root" not in css:
        reporte.aviso(nombre, "No se encontraron variables en :root para los colores "
                      "y las fuentes.")
    if "fonts.googleapis.com" in css and not css.lstrip().startswith("@import"):
        reporte.error(nombre, "El @import de Google Fonts debe estar en la primera línea.")


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------

def main():
    carpeta = sys.argv[1] if len(sys.argv) > 1 else "html"
    if not os.path.isdir(carpeta):
        print(f'No se encontró la carpeta "{carpeta}".')
        print("Uso: python validar_sitio.py [carpeta_con_las_paginas]")
        sys.exit(2)

    reporte = Reporte()
    estado = {"usa_tailwind": False, "hojas_locales": set()}
    archivos = sorted(f for f in os.listdir(carpeta) if f.lower().endswith(".html"))

    if not archivos:
        print(f'La carpeta "{carpeta}" no contiene archivos .html.')
        sys.exit(2)

    # Nombres de archivo
    if PAGINA_PRINCIPAL not in archivos:
        reporte.error("General", f"No existe {PAGINA_PRINCIPAL}. La página principal "
                      "debe llamarse así.")
    for archivo in archivos:
        if archivo in ARCHIVOS_RESERVADOS:
            reporte.error("General", f'"{archivo}" es un nombre reservado por el script '
                          "de conversión. Cámbiale el nombre o elimínalo.")
        elif not PATRON_ARCHIVO.match(archivo):
            reporte.error("General", f'El nombre "{archivo}" no sigue la convención: '
                          "minúsculas, sin acentos ni espacios, con guion bajo entre palabras.")

    paginas = [a for a in archivos if a not in ARCHIVOS_RESERVADOS]
    ids_contenido = defaultdict(list)
    imagenes = set()
    encabezados, pies = {}, {}

    for archivo in paginas:
        with open(os.path.join(carpeta, archivo), encoding="utf8") as f:
            soup = BeautifulSoup(f.read(), "html.parser")
        body = soup.find("body")
        if not body:
            reporte.error(archivo, "La página no tiene <body>.")
            continue
        revisar_head(archivo, soup, reporte, estado)
        revisar_estructura(archivo, body, reporte)
        revisar_contenido(archivo, body, reporte, carpeta, imagenes)
        revisar_ids(archivo, body, reporte, ids_contenido)
        revisar_navegacion(archivo, body, reporte)
        prueba_conversion(archivo, body, reporte)
        h = body.find("header", recursive=False)
        p = body.find("footer", recursive=False)
        if h:
            encabezados[archivo] = normalizar(h)
        if p:
            pies[archivo] = normalizar(p)
        revisar_svg(archivo, body, reporte)

    # Encabezado y pie idénticos a los de index.html
    for nombre_parte, partes in (("encabezado (<header>)", encabezados), ("pie de página (<footer>)", pies)):
        base = partes.get(PAGINA_PRINCIPAL)
        if base is None:
            continue
        for archivo, valor in partes.items():
            if archivo != PAGINA_PRINCIPAL and valor != base:
                reporte.aviso(archivo, f"El {nombre_parte} es distinto al de {PAGINA_PRINCIPAL}. "
                              "En Dash solo se conservará el de la página principal.")

    # id repetidos entre páginas (solo contenido de <main>)
    for valor, donde in ids_contenido.items():
        unicos = sorted(set(donde))
        if len(unicos) > 1:
            reporte.error("General", f'El id "{valor}" se repite en varias páginas: '
                          f"{', '.join(unicos)}. Cada id debe ser único en toda la aplicación.")

    # CSS
    hojas = estado["hojas_locales"] or {"styles.css"}
    for hoja in sorted(hojas):
        ruta = os.path.normpath(os.path.join(carpeta, hoja))
        if os.path.exists(ruta):
            revisar_css(os.path.basename(ruta), ruta, reporte, estado["usa_tailwind"])
        else:
            reporte.error("General", f'No se encontró la hoja de estilos "{hoja}".')

    # Información general
    if estado["usa_tailwind"]:
        reporte.info("General", "El sitio usa Tailwind CSS. Recuerda documentar cómo "
                     "funcionará en Dash: el CSS generado con su herramienta en assets, "
                     "o la URL del CDN, además de la configuración del tema.")
    if imagenes:
        reporte.info("General", "Recordatorio: al trasladar el sitio a Dash, las imágenes "
                     "y demás archivos propios (logotipos, íconos y, en su caso, el CSS "
                     "generado con Tailwind) deberán moverse a la carpeta assets y "
                     "actualizarse sus rutas. Imágenes encontradas: "
                     + ", ".join(sorted(imagenes)) + ".")
    if parse_html is None:
        reporte.aviso("General", "No se hizo la prueba de conversión ni la revisión de "
                      "los SVG porque falta html-to-dash. Instálalo con: "
                      "pip install html-to-dash")
    elif dash_svg is None:
        reporte.error("General", "Falta la librería dash-svg, que el script de conversión "
                      "necesita para convertir los SVG. Por eso no se hizo la prueba de "
                      "conversión ni la revisión de los SVG. Instálala con: "
                      "pip install dash-svg")
    elif html is None:
        reporte.aviso("General", "Falta la librería dash, por lo que no se pudo comprobar "
                      "que el código convertido funcione en Dash. Instálala con: "
                      "pip install dash")
    reporte.info("General", f"Páginas revisadas: {', '.join(paginas)}.")

    print(reporte.texto())
    ruta_md = os.path.join(carpeta, "reporte_validacion.md")
    with open(ruta_md, "w", encoding="utf8") as f:
        f.write(reporte.markdown(carpeta))
    print(f'\nReporte guardado en "{ruta_md}".')
    print("En VS Code, ábrelo y presiona Ctrl + Shift + V (Cmd + Shift + V en Mac) "
          "para verlo con formato.")
    sys.exit(1 if reporte.contar("ERROR") else 0)


if __name__ == "__main__":
    main()
