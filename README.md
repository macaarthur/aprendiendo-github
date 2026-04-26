# Mi primer proyecto

Estoy aprendiendo GitHub y programación con IA.

La aplicacion recibe la URL de una pagina web, extrae su texto principal y trata de generar un resumen con un LLM. Si el proceso falla, usa automaticamente el resumen local actual.

El resumen intenta ser mas natural que un simple corte de texto:

1. Descarga el HTML de la pagina
2. Elimina etiquetas y contenido no visible
3. Detecta palabras clave relevantes
4. Puntua las frases segun su relacion con esos temas
5. Construye un resumen mas natural con las ideas principales de la pagina

## Interfaz web

La aplicacion incluye un frontal sencillo con Flask para introducir una URL y ver el resumen en el navegador.

Si el resumen no puede generarse con el LLM por falta de API key, error de red o cualquier otro problema, la interfaz muestra el resumen local y anade la nota: **Texto no generado por un LLM**.

Para ejecutarla:

1. Instala Flask: `pip install flask`
2. Opcionalmente instala OpenAI: `pip install openai`
3. Opcionalmente define `OPENAI_API_KEY`
4. Ejecuta `python main.py`
5. Abre `http://127.0.0.1:5000`
    