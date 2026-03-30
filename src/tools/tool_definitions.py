"""
Schemas de todas las herramientas del agente en formato Anthropic.
Se pasa directamente a la API de Anthropic en agent_loop.py.
"""

# fmt: off

TOOLS_DOCUMENTOS = [
    {"name": "generar_excel",
     "description": "Genera un archivo Excel (.xlsx) con datos tabulares. Devuelve la ruta del archivo generado.",
     "input_schema": {"type": "object", "required": ["nombreArchivo", "columnas", "filas"], "properties": {
         "nombreArchivo": {"type": "string", "description": "Nombre del archivo sin extensión"},
         "hoja": {"type": "string", "description": "Nombre de la hoja (default: Datos)"},
         "columnas": {"type": "array", "items": {"type": "string"}, "description": "Nombres de columnas"},
         "filas": {"type": "array", "items": {"type": "array"}, "description": "Filas de datos"}}}},
    {"name": "generar_word",
     "description": "Genera un documento Word (.docx) formal. Tipos: oficio, circular, acta, respuesta, general.",
     "input_schema": {"type": "object", "required": ["nombreArchivo", "titulo", "contenido"], "properties": {
         "nombreArchivo": {"type": "string"}, "titulo": {"type": "string"}, "contenido": {"type": "string"},
         "tipoDocumento": {"type": "string", "enum": ["oficio", "circular", "acta", "respuesta", "general"]},
         "metadatos": {"type": "object", "description": "Datos: expediente, destinatario, numero, fecha, firmante"}}}},
    {"name": "analizar_documento",
     "description": "Analiza el contenido de un documento previamente subido (PDF, Word, CSV, TXT).",
     "input_schema": {"type": "object", "required": ["contenido", "instruccion"], "properties": {
         "contenido": {"type": "string"}, "instruccion": {"type": "string"},
         "formatoSalida": {"type": "string", "enum": ["texto_libre", "bullet_points", "tabla", "json"]}}}},
    {"name": "analizar_excel_basico",
     "description": "Analiza una hoja de Excel exportada como texto con totales, promedios y observaciones.",
     "input_schema": {"type": "object", "required": ["nombreHoja", "datos"], "properties": {
         "nombreHoja": {"type": "string"}, "datos": {"type": "string"}, "instruccion": {"type": "string"}}}},
    {"name": "analizar_excel_avanzado",
     "description": "Análisis estadístico completo de un archivo Excel subido: suma, promedio, min, max por columna.",
     "input_schema": {"type": "object", "required": ["nombreArchivo"], "properties": {
         "nombreArchivo": {"type": "string"}, "instruccion": {"type": "string"}}}},
    {"name": "analizar_imagen",
     "description": "Analiza imágenes y PDFs escaneados usando visión artificial. Puede extraer texto de documentos escaneados, interpretar gráficos, leer formularios y describir contenido visual. Usarlo cuando el usuario suba una imagen o un PDF que no tiene texto digital.",
     "input_schema": {"type": "object", "required": ["archivo"], "properties": {
         "archivo": {"type": "string", "description": "Nombre del archivo subido"},
         "instruccion": {"type": "string", "description": "Qué analizar (opcional, default: análisis completo)"}}}},
]

TOOLS_BUSQUEDA = [
    {"name": "buscar_web",
     "description": "Busca información en la web. Devuelve título, fragmento y URL de resultados relevantes.",
     "input_schema": {"type": "object", "required": ["query"], "properties": {
         "query": {"type": "string"}, "maxResultados": {"type": "number", "description": "Máx resultados (default 5, máx 10)"}}}},
    {"name": "buscar_normativa",
     "description": "Busca leyes, decretos y resoluciones en Infoleg y SAIJ.",
     "input_schema": {"type": "object", "required": ["query"], "properties": {
         "query": {"type": "string"}, "organismo": {"type": "string", "description": "Filtro por organismo (opcional)"}}}},
    {"name": "buscar_ordenanzas",
     "description": "Busca ordenanzas municipales del Partido de Escobar.",
     "input_schema": {"type": "object", "required": ["query"], "properties": {
         "query": {"type": "string", "description": "Tema o número de ordenanza"}}}},
]

TOOLS_PRESENTACIONES = [
    {"name": "generar_presentacion",
     "description": "Genera presentación profesional con Gamma AI. Formatos: presentacion, documento, pagina.",
     "input_schema": {"type": "object", "required": ["titulo", "contenido"], "properties": {
         "titulo": {"type": "string"}, "contenido": {"type": "string"},
         "formato": {"type": "string", "enum": ["presentacion", "documento", "pagina"]}}}},
]

TOOLS_GOOGLE = [
    {"name": "leer_gmail",
     "description": "Lee los últimos emails no leídos de Gmail del usuario.",
     "input_schema": {"type": "object", "required": [], "properties": {
         "cantidad": {"type": "number", "description": "Cantidad (máx 20, default 5)"}}}},
    {"name": "enviar_gmail",
     "description": "Envía un email desde Gmail. Pedí siempre confirmación antes de enviar.",
     "input_schema": {"type": "object", "required": ["para", "asunto", "cuerpo"], "properties": {
         "para": {"type": "string"}, "asunto": {"type": "string"}, "cuerpo": {"type": "string"}}}},
    {"name": "leer_calendar",
     "description": "Lista los próximos eventos del calendario del usuario.",
     "input_schema": {"type": "object", "required": [], "properties": {
         "dias": {"type": "number", "description": "Días hacia adelante (máx 60, default 7)"}}}},
    {"name": "crear_evento",
     "description": "Crea un evento en el calendario. Formato fecha YYYY-MM-DD, hora HH:MM.",
     "input_schema": {"type": "object", "required": ["titulo", "fecha", "hora"], "properties": {
         "titulo": {"type": "string"}, "fecha": {"type": "string"}, "hora": {"type": "string"},
         "duracionMinutos": {"type": "number"}, "descripcion": {"type": "string"}}}},
    {"name": "buscar_drive",
     "description": "Busca archivos en Google Drive por nombre o contenido.",
     "input_schema": {"type": "object", "required": ["query"], "properties": {
         "query": {"type": "string", "description": "Término de búsqueda"}}}},
]

# fmt: on

TOOLS = TOOLS_DOCUMENTOS + TOOLS_BUSQUEDA + TOOLS_PRESENTACIONES + TOOLS_GOOGLE
