import logging
import os

from services.web_fetcher import tokenizar


logger = logging.getLogger(__name__)


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


def dividir_en_frases(texto):
    import re

    frases = re.split(r"(?<=[.!?])\s+", texto.strip())
    logger.info("Texto dividido en frases", extra={"sentence_count": len(frases)})
    logger.debug("Primeras frases detectadas", extra={"sentences_preview": frases[:3]})
    return [frase.strip() for frase in frases if frase.strip()]


def obtener_palabras_clave(texto, limite=6):
    frecuencias = {}
    tokens = tokenizar(texto)
    logger.debug("Tokens generados para palabras clave", extra={"token_count": len(tokens), "tokens_preview": tokens[:15]})

    for palabra in tokens:
        if palabra not in PALABRAS_VACIAS and len(palabra) > 2:
            frecuencias[palabra] = frecuencias.get(palabra, 0) + 1

    palabras_ordenadas = sorted(
        frecuencias.items(),
        key=lambda item: (-item[1], item[0])
    )
    logger.info("Palabras clave calculadas", extra={"keyword_count": min(len(palabras_ordenadas), limite)})
    logger.debug("Ranking de palabras clave", extra={"keywords_ranked": palabras_ordenadas[:limite]})
    return [palabra for palabra, _ in palabras_ordenadas[:limite]]


def puntuar_frase(frase, palabras_clave):
    palabras_frase = tokenizar(frase)
    if not palabras_frase:
        logger.debug("Frase descartada por no contener tokens", extra={"sentence": frase})
        return 0

    coincidencias = sum(1 for palabra in palabras_frase if palabra in palabras_clave)
    bonus_longitud = min(len(palabras_frase) / 12, 1)
    logger.debug(
        "Frase puntuada",
        extra={
            "sentence": frase,
            "sentence_tokens": palabras_frase,
            "matches": coincidencias,
            "length_bonus": bonus_longitud,
        },
    )
    return coincidencias + bonus_longitud


def limpiar_frase(frase):
    frase = frase.strip()
    if not frase:
        return ""
    frase = frase[0].upper() + frase[1:]
    if frase[-1] not in ".!?":
        frase += "."
    logger.debug("Frase limpiada", extra={"clean_sentence": frase})
    return frase


def construir_resumen(frases_destacadas, palabras_clave):
    frases_limpias = [limpiar_frase(frase) for frase in frases_destacadas if limpiar_frase(frase)]
    if not frases_limpias:
        logger.warning("No hay frases limpias para construir el resumen")
        return "No se pudo generar un resumen claro de la pagina."

    temas = ", ".join(palabras_clave[:4]) if palabras_clave else "los puntos principales"
    logger.debug(
        "Construyendo resumen final",
        extra={"clean_sentences": frases_limpias, "topics": temas},
    )

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


def resumir_texto_local(texto):
    texto = texto.strip()
    if not texto:
        logger.warning("Se intento resumir localmente un texto vacio")
        return "No hay contenido suficiente para generar un resumen."

    logger.debug("Texto recibido para resumen local", extra={"text_preview": texto[:500]})

    frases = dividir_en_frases(texto)
    if not frases:
        frases = [texto]
        logger.info("No se detectaron frases; se usara el texto completo")

    palabras_clave = obtener_palabras_clave(texto)
    frases_puntuadas = []

    for indice, frase in enumerate(frases):
        puntuacion = puntuar_frase(frase, palabras_clave)
        frases_puntuadas.append((puntuacion, indice, frase))

    logger.debug("Frases puntuadas", extra={"scored_sentences": frases_puntuadas[:10]})

    mejores_frases = sorted(frases_puntuadas, key=lambda item: (-item[0], item[1]))[:3]
    mejores_frases.sort(key=lambda item: item[1])
    logger.debug("Frases seleccionadas para resumen", extra={"selected_ranked_sentences": mejores_frases})

    frases_destacadas = [frase for _, _, frase in mejores_frases]
    logger.info(
        "Resumen local preparado",
        extra={"selected_sentences": len(frases_destacadas), "keyword_count": len(palabras_clave)},
    )
    return construir_resumen(frases_destacadas, palabras_clave)


def resumir_texto_llm(texto):
    api_key = os.getenv("AZURE_OPENAI_API_KEY")
    base_url = os.getenv("AZURE_OPENAI_BASE_URL")
    deployment = os.getenv("AZURE_OPENAI_CHAT_DEPLOYMENT")

    if not all([api_key, base_url, deployment]):
        logger.info("Configuracion LLM incompleta; se omite resumen con Azure OpenAI")
        logger.debug(
            "Estado de configuracion LLM",
            extra={
                "has_api_key": bool(api_key),
                "has_base_url": bool(base_url),
                "has_deployment": bool(deployment),
            },
        )
        return None

    try:
        from langchain_core.messages import HumanMessage
        from langchain_openai import ChatOpenAI
    except ImportError:
        logger.exception("No se pudieron importar las dependencias de LangChain para el resumen LLM")
        return None

    try:
        logger.info("Invocando resumen con Azure OpenAI", extra={"deployment": deployment})
        logger.debug("Payload enviado al LLM preparado", extra={"text_preview": texto[:1000]})
        cliente = ChatOpenAI(
            model=deployment,
            api_key=api_key,
            base_url=base_url,
            temperature=0.3,
        )
        respuesta = cliente.invoke(
            [HumanMessage(content=(
                "Resume el contenido de esta pagina web en espanol de forma natural y breve. "
                "Devuelve un unico parrafo con los puntos principales o ideas mas destacadas. "
                "No uses listas ni encabezados.\n\n"
                f"Contenido:\n{texto.strip()}"
            ))]
        )
    except Exception:
        logger.exception("Fallo la invocacion al modelo LLM")
        return None

    contenido = respuesta.content.strip() if isinstance(respuesta.content, str) else ""
    if not contenido:
        logger.warning("El modelo LLM devolvio una respuesta vacia")
        return None

    logger.info("Resumen LLM generado correctamente", extra={"summary_length": len(contenido)})
    return contenido


def resumir_texto(texto):
    logger.info("Iniciando proceso de resumen", extra={"text_length": len(texto)})
    logger.debug("Vista previa del texto a resumir", extra={"text_preview": texto[:500]})
    resumen_llm = resumir_texto_llm(texto)
    if resumen_llm:
        logger.info("Se utilizo el resumen generado por LLM")
        return resumen_llm, True

    logger.info("Se utilizara el resumen local como fallback")
    return resumir_texto_local(texto), False