import logging

from flask import Flask, render_template, request

import config
from services.summarizer import resumir_texto
from services.web_fetcher import obtener_texto_desde_url


config.configure_logging()

app = Flask(__name__)
logger = logging.getLogger(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    url = ""
    resumen = None
    error = None
    generado_por_llm = False

    logger.info("Procesando peticion", extra={"method": request.method, "path": request.path})

    if request.method == "POST":
        url = request.form.get("url", "").strip()
        logger.info("URL recibida para resumir", extra={"url": url})
        if not url:
            error = "Introduce una URL valida."
            logger.warning("Peticion rechazada por URL vacia")
        else:
            texto, error = obtener_texto_desde_url(url)
            if not error and texto:
                logger.info("Texto extraido correctamente", extra={"url": url, "text_length": len(texto)})
                resumen, generado_por_llm = resumir_texto(texto)
                logger.info(
                    "Resumen generado",
                    extra={
                        "url": url,
                        "generated_by_llm": generado_por_llm,
                        "summary_length": len(resumen) if resumen else 0,
                    },
                )
            else:
                logger.warning("No se pudo obtener texto desde la URL", extra={"url": url, "error": error})

    return render_template(
        "index.html",
        url=url,
        resumen=resumen,
        error=error,
        generado_por_llm=generado_por_llm,
    )


if __name__ == "__main__":
    logger.info("Arrancando aplicacion Flask")
    app.run(debug=True)
