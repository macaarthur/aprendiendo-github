import os
import re


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
    frases = re.split(r"(?<=[.!?])\s+", texto.strip())
    return [frase.strip() for frase in frases if frase.strip()]


def tokenizar(texto):
    return re.findall(r"\b\w+\b", texto.lower())


def resumir_texto_local(texto):
    texto = texto.strip()
    if not texto:
        return "- No hay texto para resumir\n- Introduce un texto más largo\n- Vuelve a intentarlo"

    frases = dividir_en_frases(texto)

    if not frases:
        frases = [texto]

    frecuencias = {}
    for palabra in tokenizar(texto):
        if palabra not in PALABRAS_VACIAS and len(palabra) > 2:
            frecuencias[palabra] = frecuencias.get(palabra, 0) + 1

    puntuaciones = []
    for indice, frase in enumerate(frases):
        palabras_frase = tokenizar(frase)
        puntuacion = sum(
            frecuencias.get(palabra, 0)
            for palabra in palabras_frase
            if palabra not in PALABRAS_VACIAS
        )
        if palabras_frase:
            puntuacion /= len(palabras_frase)
        puntuaciones.append((puntuacion, indice, frase))

    mejores_frases = sorted(puntuaciones, reverse=True)[:3]
    mejores_frases.sort(key=lambda item: item[1])

    ideas = ["- " + frase for _, _, frase in mejores_frases]

    while len(ideas) < 3:
        ideas.append("- ")

    return "\n".join(ideas)


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
                "Resume el siguiente texto en exactamente 3 ideas principales. "
                "Devuelve solo 3 lineas y cada una debe empezar por '- '. "
                "No anadas explicaciones adicionales.\n\n"
                f"Texto:\n{texto.strip()}"
            ),
        )
    except Exception:
        return None

    contenido = respuesta.output_text.strip()
    lineas = [linea.strip() for linea in contenido.splitlines() if linea.strip()]

    if len(lineas) != 3:
        return None

    if not all(linea.startswith("- ") for linea in lineas):
        return None

    return "\n".join(lineas)


def resumir_texto(texto):
    resumen_llm = resumir_texto_llm(texto)
    if resumen_llm:
        return resumen_llm
    return resumir_texto_local(texto)

if __name__ == "__main__":
    texto = input("Introduce un textoo: ")
    resumen = resumir_texto(texto)
    print("\nIdeas principales:")
    print(resumen)