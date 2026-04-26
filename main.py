import os
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from flask import Flask, render_template, request


PALABRAS_VACIAS = {
    "a", "al", "algo", "algunas", "algunos", "ante", "antes", "como", "con",
    "contra", "cual", "cuando", "de", "del", "desde", "donde", "dos", "el",
    "ella", "ellas", "ellos", "en", "entre", "era", "erais", "eran", "eras",
    "eres", "es", "esa", "esas", "ese", "eso", "esos", "esta", "estaba",
    "estais", "estamos", "estan", "estar", "estas", "este", "esto", "estos",
    "fue", "fueron", "ha", "habia", "han", "hasta", "hay", "la", "las",
    "le", "les", "lo", "los", "mas", "me", "mi", "mis", "mucho", "muy",
    "no", "nos", "nosotros", "o", "os", "otra", "otro", "para", "pero",
    "poco", "por", "porque", "que", "quien", "se", "si", "sin", "sobre",
    "su", "sus", "tambien", "te", "tenia", "tiene", "todo", "tu", "tus",
    "un", "una", "uno", "unos", "y", "ya"
}


def obtener_texto_desde_url(url):
    solicitud = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    try:
        with urlopen(solicitud, timeout=10) as respuesta:
            tipo_contenido = respuesta.headers.get("Content-Type", "")
            if "text/html" not in tipo_contenido:
                return None, "La URL no contiene una pagina HTML valida."

            html = respuesta.read().decode("utf-8", errors="ignore")
    except HTTPError as error:
        return None, f"No se pudo acceder a la pagina. Codigo HTTP: {error.code}"
    except URLError:
        return None, "No se pudo conectar con la URL indicada."
    except Exception:
        return None, "Ha ocurrido un error al descargar la pagina web."

    texto = extraer_texto_html(html)
    if not texto:
        return None, "No se pudo extraer texto util de la pagina."

    return texto, None


def extraer_texto_html(html):
    html = re.sub(r"<script.*?>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<style.*?>.*?</style>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<noscript.*?>.*?</noscript>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<[^>]+>", " ", html)
    html = unescape(html)
    html = re.sub(r"\s+", " ", html)

    bloques = [bloque.strip() for bloque in re.split(r"(?<=[.!?])\s+", html) if bloque.strip()]
    bloques_validos = [bloque for bloque in bloques if len(tokenizar(bloque)) >= 6]

    return " ".join(bloques_validos[:20]).strip()


def dividir_en_frases(texto):
    frases = re.split(r"(?<=[.!?])\s+", texto.strip())
    return [frase.strip() for frase in frases if frase.strip()]


def tokenizar(texto):
    return re.findall(r"\b\w+\b", texto.lower())


def obtener_palabras_clave(texto, limite=6):
    frecuencias = {}
    for palabra in tokenizar(texto):
        if palabra not in PALABRAS_VACIAS and len(palabra) > 2:
            frecuencias[palabra] = frecuencias.get(palabra, 0) + 1

    palabras_ordenadas = sorted(
        frecuencias.items(),
        key=lambda item: (-item[1], item[0])
    )
    return [palabra for palabra, _ in palabras_ordenadas[:limite]]


def puntuar_frase(frase, palabras_clave):
    palabras_frase = tokenizar(frase)
    if not palabras_frase:
        return 0

    coincidencias = sum(1 for palabra in palabras_frase if palabra in palabras_clave)
    bonus_longitud = min(len(palabras_frase) / 12, 1)
    return coincidencias + bonus_longitud


def limpiar_frase(frase):
    frase = frase.strip()
    if not frase:
        return ""
    frase = frase[0].upper() + frase[1:]
    if frase[-1] not in ".!?":
        frase += "."
    return frase


def construir_resumen(frases_destacadas, palabras_clave):
    frases_limpias = [limpiar_frase(frase) for frase in frases_destacadas if limpiar_frase(frase)]
    if not frases_limpias:
        return "No se pudo generar un resumen claro de la pagina."

    temas = ", ".join(palabras_clave[:4]) if palabras_clave else "los puntos principales"

    if len(frases_limpias) == 1:
        return f"La pagina trata principalmente sobre {temas}. {frases_limpias[0]}"

    if len(frases_limpias) == 2:
        return (
            f"La pagina destaca sobre todo {temas}. "
            f"{frases_limpias[0]} {frases_limpias[1]}"
        )

    return (
        f"La pagina resume principalmente {temas}. "
        f"{frases_limpias[0]} {frases_limpias[1]} {frases_limpias[2]}"
    )


def resumir_texto(texto):
    texto = texto.strip()
    if not texto:
        return "No hay contenido suficiente para generar un resumen."

    frases = dividir_en_frases(texto)
    if not frases:
        frases = [texto]

    palabras_clave = obtener_palabras_clave(texto)
    frases_puntuadas = []

    for indice, frase in enumerate(frases):
        puntuacion = puntuar_frase(frase, palabras_clave)
        frases_puntuadas.append((puntuacion, indice, frase))

    mejores_frases = sorted(frases_puntuadas, key=lambda item: (-item[0], item[1]))[:3]
    mejores_frases.sort(key=lambda item: item[1])

    frases_destacadas = [frase for _, _, frase in mejores_frases]
    return construir_resumen(frases_destacadas, palabras_clave)


def resumir_texto_llm(texto):
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None

    try:
        from openai import OpenAI
    except ImportError:
        return None

    try:
        cliente = OpenAI(api_key=api_key)
        respuesta = cliente.responses.create(
            model="gpt-4.1-mini",
            input=(
                "Resume el contenido de esta pagina web en espanol de forma natural y breve. "
                "Devuelve un unico parrafo con los puntos principales o ideas mas destacadas. "
                "No uses listas ni encabezados.\n\n"
                f"Contenido:\n{texto.strip()}"
            ),
        )
    except Exception:
        return None

    contenido = respuesta.output_text.strip()
    if not contenido:
        return None

    return contenido


def resumir_url(url):
    texto, error = obtener_texto_desde_url(url)
    if error:
        return None, error, False

    resumen_llm = resumir_texto_llm(texto)
    if resumen_llm:
        return resumen_llm, None, True

    resumen_local = resumir_texto(texto)
    return resumen_local, None, False


app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    url = ""
    resumen = None
    error = None
    generado_por_llm = False

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        if not url:
            error = "Introduce una URL valida."
        else:
            resumen, error, generado_por_llm = resumir_url(url)

    return render_template(
        "index.html",
        url=url,
        resumen=resumen,
        error=error,
        generado_por_llm=generado_por_llm,
    )

if __name__ == "__main__":
    app.run(debug=True)