def resumir_texto(texto):
    palabras = texto.split()
    if not palabras:
        return "- No hay texto para resumir\n- Introduce un texto más largo\n- Vuelve a intentarlo"

    ideas = []
    tamano_bloque = max(1, len(palabras) // 3)

    for indice in range(0, len(palabras), tamano_bloque):
        bloque = palabras[indice:indice + tamano_bloque]
        if bloque:
            ideas.append("- " + " ".join(bloque))
        if len(ideas) == 3:
            break

    while len(ideas) < 3:
        ideas.append("- ")

    return "\n".join(ideas)

if __name__ == "__main__":
    texto = input("Introduce un texto: ")
    resumen = resumir_texto(texto)
    print("\nIdeas principales:")
    print(resumen)