# Resumen de paginas web

Aplicacion web en Flask para introducir una URL, extraer el contenido textual principal de la pagina y generar un resumen en espanol. El sistema intenta usar Azure OpenAI v1 a traves de LangChain cuando hay configuracion disponible y, si no, aplica un resumen local determinista como mecanismo de fallback.

## Objetivo tecnico

El proyecto esta pensado como una base sencilla para evolucionar hacia un pipeline de procesamiento de contenido web. La separacion actual permite trabajar de forma independiente en tres capas:

1. Ingesta de contenido desde una URL
2. Normalizacion y extraccion de texto util
3. Generacion de resumen con estrategia dual: LLM o heuristica local

## Flujo de ejecucion

1. El usuario envia una URL desde la interfaz web.
2. `app.py` valida la entrada y delega la descarga a `services/web_fetcher.py`.
3. El fetcher normaliza la URL, realiza la peticion HTTP y filtra contenido HTML no util.
4. `services/summarizer.py` intenta resumir con Azure OpenAI mediante LangChain si existe la configuracion necesaria.
5. Si el LLM no esta disponible o falla, se genera un resumen local basado en frases relevantes y palabras clave.
6. La vista muestra el resultado y marca si el texto fue generado por LLM o por fallback local.

## Arquitectura actual

- `app.py`: capa de presentacion y orquestacion de la peticion web.
- `services/web_fetcher.py`: normalizacion de URL, descarga HTTP y extraccion basica de texto desde HTML.
- `services/summarizer.py`: tokenizacion, deteccion de palabras clave, puntuacion de frases y generacion de resumen.
- `templates/index.html`: interfaz HTML renderizada por Flask.
- `static/styles.css`: estilos visuales de la aplicacion.

## Estrategia de resumen

El resumen local no hace una simple truncacion del texto. En su lugar:

1. Divide el contenido en frases.
2. Calcula frecuencias de palabras relevantes excluyendo stopwords.
3. Puntua cada frase segun coincidencias con palabras clave y longitud.
4. Selecciona las frases mejor valoradas manteniendo el orden original.
5. Construye un texto final mas natural con una introduccion sintetica.

Cuando hay acceso a Azure OpenAI, el sistema usa LangChain para producir un resumen mas fluido. Si la llamada falla por red, credenciales o dependencia ausente, el flujo cae automaticamente al resumen local.

## Requisitos

- Python 3.10 o superior recomendado.
- Flask.
- Azure OpenAI y LangChain solo si se quiere activar el resumen con LLM.

## Configuracion

Variables de entorno opcionales:

- `AZURE_OPENAI_API_KEY`: clave de acceso a Azure OpenAI.
- `AZURE_OPENAI_BASE_URL`: endpoint base del recurso Azure OpenAI con sufijo `/openai/v1/`.
- `AZURE_OPENAI_CHAT_DEPLOYMENT`: nombre del deployment del modelo de chat.
- `LOG_LEVEL`: nivel de logging de la aplicacion. Por defecto `INFO`.

Las variables globales del proyecto se cargan desde [config.py](config.py), que a su vez lee el archivo `.env` al arrancar la aplicacion.

Si prefieres no definirla en el sistema, puedes crear un archivo `.env` en la raiz del proyecto con este contenido:

```env
AZURE_OPENAI_API_KEY=tu_clave_aqui
AZURE_OPENAI_BASE_URL=https://tu-recurso.openai.azure.com/openai/v1/
AZURE_OPENAI_CHAT_DEPLOYMENT=tu_deployment
```

Con la API `v1` de Azure OpenAI ya no hace falta definir `api-version` en variables de entorno. La configuracion recomendada por Microsoft y LangChain es usar `ChatOpenAI` con `base_url` apuntando a `https://tu-recurso.openai.azure.com/openai/v1/`.

## Ejecucion local

1. Instala dependencias: `pip install -r requirements.txt`
2. Opcionalmente define las variables de Azure OpenAI en el sistema o en `.env`
3. Ejecuta `python app.py`
4. Abre `http://127.0.0.1:5000`

## Logging y trazabilidad

La aplicacion registra trazas en consola usando el modulo `logging` de Python. Se cubren estos puntos del flujo:

1. Entrada de peticiones HTTP y URL recibida.
2. Normalizacion de URL y descarga del HTML.
3. Validacion del tipo de contenido y extraccion de texto util.
4. Decision entre resumen con LLM o fallback local.
5. Errores de red, importacion de dependencias y fallos inesperados.

Puedes ajustar el nivel de detalle con `LOG_LEVEL=DEBUG`, `INFO`, `WARNING` o `ERROR`.

## Limitaciones actuales

- La extraccion HTML es heuristica y no usa un parser semantico avanzado.
- No hay persistencia de historico ni almacenamiento de resultados.
- No existe control de concurrencia, cache ni cola de trabajos.
- El resumen local depende de reglas simples y puede degradarse en paginas muy largas o con HTML complejo.

## Evolucion prevista

- Sustituir la extraccion HTML por un parser mas robusto.
- Añadir limpieza de contenido principal, metadatos y deteccion de idioma.
- Introducir tests unitarios para fetcher, tokenizacion y resumen local.
- Separar configuracion en variables de entorno y archivo de settings.
- Añadir cache de respuestas para URLs repetidas.
- Exponer una API JSON ademas de la interfaz web.
- Registrar trazas y errores con logging estructurado.

## Arquitectura objetivo

La evolucion natural del proyecto es convertirlo en un servicio de analisis de contenido web con una separacion mas clara entre capas:

- Capa de entrada: interfaz web y futura API JSON.
- Capa de dominio: normalizacion de URL, extraccion de contenido, resumen y reglas de negocio.
- Capa de infraestructura: cliente HTTP, integracion con LLM, cache y logging.
- Capa de presentacion: templates, estilos y respuestas estructuradas para el usuario.

Este enfoque facilita sustituir componentes sin reescribir el flujo completo. Por ejemplo, el extractor HTML puede cambiarse por una libreria mas robusta, o el motor de resumen puede evolucionar a una estrategia basada en prompts, embeddings o modelos locales.

## Decisiones de diseno

- Se prioriza un fallback local para que la aplicacion siga siendo util sin dependencias externas.
- La logica de resumen esta aislada en `services/summarizer.py` para facilitar pruebas y sustitucion.
- La extraccion de texto se mantiene simple por ahora para reducir complejidad y dependencias.
- La integracion con Azure OpenAI mediante LangChain es opcional y no bloquea el funcionamiento basico.
- La salida se orienta a un resumen breve y legible, no a una extraccion exhaustiva del contenido.

## Estructura del proyecto

- `app.py`: punto de entrada Flask y coordinacion del flujo.
- `services/web_fetcher.py`: descarga de la pagina y extraccion de texto.
- `services/summarizer.py`: resumen local, resumen con Azure OpenAI mediante LangChain y fallback.
- `templates/index.html`: interfaz web.
- `static/styles.css`: estilos visuales.
    