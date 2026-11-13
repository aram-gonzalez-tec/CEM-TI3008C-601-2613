# Reporte de validación del sitio

**Carpeta revisada:** `html`  
**Fecha:** 2026-10-20 16:44

> ❌ **El sitio todavía no está listo para el traslado a Dash.** Corrige los errores y vuelve a ejecutar el validador.

| Nivel | Cantidad | Qué significa |
|---|---|---|
| ❌ Errores | 5 | Impiden o ponen en riesgo la conversión. Deben corregirse. |
| ⚠️ Avisos | 4 | Incumplen una regla o recomendación. Conviene corregirlos. |
| ℹ️ Información | 2 | Datos útiles; no requieren acción. |

## Resumen por archivo

| Archivo | ❌ Errores | ⚠️ Avisos |
|---|---|---|
| [General](#general) | 1 | 0 |
| [estilos.html](#estiloshtml) | 1 | 0 |
| [index.html](#indexhtml) | 1 | 1 |
| [tableros.html](#tableroshtml) | 2 | 3 |

## General

### ❌ Errores

- [ ] No se encontró la hoja de estilos "/css/main.css".

### ℹ️ Información

- Recordatorio: al trasladar el sitio a Dash, las imágenes y demás archivos propios (logotipos, íconos y, en su caso, el CSS generado con Tailwind) deberán moverse a la carpeta assets y actualizarse sus rutas. Imágenes encontradas: /images/pexels-daredevil-39198817.jpg.
- Páginas revisadas: estilos.html, index.html, tableros.html.

## estilos.html

### ❌ Errores

- [ ] **Línea 9:** El `<body>` debe contener exactamente `<header>`, `<main>` y `<footer>`, en ese orden. Se encontró: `<h1>`, `<h1>`, `<p>`.

## index.html

### ❌ Errores

- [ ] **Línea 8:** El `<body>` debe contener exactamente `<header>`, `<main>` y `<footer>`, en ese orden. Se encontró: `<h1>`, `<h2>`, `<p>`, `<ol>`, `<ul>`, `<table>`, `<figure>`, `<iframe>`, `<ul>`.

### ⚠️ Avisos

- [ ] La conversión eliminará los atributos allowfullscreen, frameborder de html.Iframe.

## tableros.html

### ❌ Errores

- [ ] **Línea 8:** El `<body>` debe contener exactamente `<header>`, `<main>` y `<footer>`, en ese orden. Se encontró: `<header>`.
- [ ] **Línea 24:** Hay un `<footer>` dentro de `<header>`. El script de conversión lo eliminaría junto con su contenido. Usa un `<div>` con una clase.

### ⚠️ Avisos

- [ ] **Línea 16:** El enlace "/index.html" apunta a un archivo .html. Usa la ruta de la página, por ejemplo "/" o "/reportes".
- [ ] **Línea 17:** El enlace "/tableros.html" apunta a un archivo .html. Usa la ruta de la página, por ejemplo "/" o "/reportes".
- [ ] **Línea 18:** El enlace "/predicción.html" apunta a un archivo .html. Usa la ruta de la página, por ejemplo "/" o "/reportes".

---

Marca cada casilla al corregir el problema y vuelve a ejecutar `python validar_sitio.py` para generar un reporte actualizado.
