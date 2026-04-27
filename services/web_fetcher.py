import logging
import re
from html import unescape
from urllib.error import HTTPError, URLError
from urllib.parse import urlparse
from urllib.request import Request, urlopen


logger = logging.getLogger(__name__)


def normalizar_url(url):
    logger.debug("URL original recibida", extra={"raw_url": url})
    url = url.strip()
    if not url:
        logger.warning("Se recibio una URL vacia para normalizar")
        return ""

    if not re.match(r"^https?://", url, flags=re.IGNORECASE):
        url = f"https://{url}"
        logger.info("Se anadio esquema por defecto a la URL", extra={"normalized_url": url})

    partes = urlparse(url)
    if not partes.scheme or not partes.netloc:
        logger.warning("La URL no es valida tras la normalizacion", extra={"url": url})
        return ""

    logger.info("URL normalizada correctamente", extra={"url": url})
    return url


def obtener_texto_desde_url(url):
    url = normalizar_url(url)
    if not url:
        return None, "La URL indicada no es valida."

    logger.info("Iniciando descarga de contenido web", extra={"url": url})
    logger.debug("Cabeceras HTTP preparadas para la solicitud", extra={"url": url})

    solicitud = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/135.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "es-ES,es;q=0.9,en;q=0.8",
        },
    )

    try:
        with urlopen(solicitud, timeout=10) as respuesta:
            tipo_contenido = respuesta.headers.get("Content-Type", "")
            logger.info("Respuesta HTTP recibida", extra={"url": url, "content_type": tipo_contenido})
            if "text/html" not in tipo_contenido:
                logger.warning("La respuesta no contiene HTML", extra={"url": url, "content_type": tipo_contenido})
                return None, "La URL no contiene una pagina HTML valida."

            html = respuesta.read().decode("utf-8", errors="ignore")
            logger.info("HTML descargado correctamente", extra={"url": url, "html_length": len(html)})
    except HTTPError as error:
        logger.exception("Error HTTP al descargar la pagina", extra={"url": url, "status_code": error.code})
        return None, f"No se pudo acceder a la pagina. Codigo HTTP: {error.code}"
    except URLError as error:
        motivo = getattr(error, "reason", None)
        logger.exception("Error de conexion al descargar la pagina", extra={"url": url, "reason": str(motivo) if motivo else "unknown"})
        if motivo:
            return None, f"No se pudo conectar con la URL indicada: {motivo}"
        return None, "No se pudo conectar con la URL indicada."
    except ValueError:
        logger.exception("La URL produjo un ValueError durante la descarga", extra={"url": url})
        return None, "La URL indicada no es valida."
    except Exception as error:
        logger.exception("Error inesperado al descargar la pagina", extra={"url": url})
        return None, f"Ha ocurrido un error al descargar la pagina web: {error}"

    texto = extraer_texto_html(html)
    if not texto:
        logger.warning("No se pudo extraer texto util del HTML", extra={"url": url})
        return None, "No se pudo extraer texto util de la pagina."

    logger.info("Texto util extraido del HTML", extra={"url": url, "text_length": len(texto)})
    return texto, None


def extraer_texto_html(html):
    logger.info("Iniciando limpieza de HTML", extra={"html_length": len(html)})
    logger.debug("Vista previa del HTML recibido", extra={"html_preview": html[:500]})
    html = re.sub(r"<script.*?>.*?</script>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<style.*?>.*?</style>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<noscript.*?>.*?</noscript>", " ", html, flags=re.IGNORECASE | re.DOTALL)
    html = re.sub(r"<[^>]+>", " ", html)
    html = unescape(html)
    html = re.sub(r"\s+", " ", html)

    bloques = [bloque.strip() for bloque in re.split(r"(?<=[.!?])\s+", html) if bloque.strip()]
    bloques_validos = [bloque for bloque in bloques if len(tokenizar(bloque)) >= 6]

    logger.info(
        "HTML procesado en bloques de texto",
        extra={"total_blocks": len(bloques), "valid_blocks": len(bloques_validos)},
    )
    logger.debug("Bloques validos extraidos", extra={"valid_blocks_preview": bloques_validos[:5]})

    return " ".join(bloques_validos[:20]).strip()


def tokenizar(texto):
    return re.findall(r"\b\w+\b", texto.lower())