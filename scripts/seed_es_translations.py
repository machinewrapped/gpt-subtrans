#!/usr/bin/env python3
"""
Seed Spanish translations into locales/es/LC_MESSAGES/gui-subtrans.po.
- Fills msgstr for empty entries using an expanded exact mapping
- Applies simple regex-based rules for common formatted strings
Note: Only single-line msgid entries are handled.
"""
import os
import re

# Add the parent directory to sys.path so we can import PySubtitle modules
base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

LOCALES_DIR = os.path.join(base_path, 'locales')
ES_PO = os.path.join(LOCALES_DIR, 'es', 'LC_MESSAGES', 'gui-subtrans.po')

MAPPING = {
    # Menus and common
    'File': 'Archivo',
    'Edit': 'Editar',
    'Tools': 'Herramientas',
    'General': 'General',
    'Processing': 'Procesamiento',
    'Advanced': 'Avanzado',
    'Provider Settings': 'Configuración del proveedor',

    # Windows/titles
    'GUI-Subtrans': 'GUI-Subtrans',
    'GUI-Subtrans Settings': 'Configuración de GUI-Subtrans',
    'First Run Options': 'Opciones de primera ejecución',
    'Project Settings': 'Configuración del proyecto',
    'About GUI-Subtrans': 'Acerca de GUI-Subtrans',
    'Main Toolbar': 'Barra de herramientas principal',
    'Project Toolbar': 'Barra de herramientas del proyecto',

    # Settings keys
    'access_key' : 'Clave De Acceso',
    'add_right_to_left_markers' : 'Añadir Marcadores De Derecha A Izquierda',
    'api_base' : 'Base Api',
    'api_key' : 'Clave Api',
    'api_version' : 'Versión Api',
    'autosave' : 'Guardado Automático',
    'aws_region' : 'Región Aws',
    'backoff_time' : 'Tiempo De Espera',
    'break_dialog_on_one_line' : 'Romper Diálogo En Una Línea',
    'break_long_lines' : 'Romper Líneas Largas',
    'convert_wide_dashes' : 'Convertir Guiones Largos',
    'deployment_name' : 'Nombre Despliegue',
    'endpoint' : 'Punto Final',
    'filler_words' : 'Palabras De Relleno',
    'firstrun' : 'Primera Ejecución',
    'free_plan' : 'Plan Gratuito',
    'full_width_punctuation' : 'Puntuación Ancho Completo',
    'include_original' : 'Incluir Original',
    'instruction_file' : 'Archivo Instrucciones',
    'last_used_path' : 'Última Ruta Usada',
    'max_batch_size' : 'Tamaño Máximo Lote',
    'max_characters' : 'Máximo Caracteres',
    'max_completion_tokens' : 'Máximo Tokens Completados',
    'max_context_summaries' : 'Máximo Resúmenes Contexto',
    'max_instruct_tokens' : 'Máximo Tokens Instrucción',
    'max_line_duration' : 'Duración Máxima Línea',
    'max_lines' : 'Máximo Líneas',
    'max_newlines' : 'Máximo Saltos Línea',
    'max_retries' : 'Máximo Reintentos',
    'max_single_line_length' : 'Longitud Máxima Línea Única',
    'max_summary_length' : 'Longitud Máxima Resumen',
    'max_thinking_tokens' : 'Máximo Tokens Pensamiento',
    'max_threads' : 'Máximo Hilos',
    'max_tokens' : 'Máximo Tokens',
    'merge_line_duration' : 'Duración Fusión Línea',
    'min_batch_size' : 'Tamaño Mínimo Lote',
    'min_line_duration' : 'Duración Mínima Línea',
    'min_single_line_length' : 'Longitud Mínima Línea Única',
    'min_split_chars' : 'Mínimo Caracteres División',
    'model' : 'Modelo',
    'normalise_dialog_tags' : 'Normalizar Etiquetas Diálogo',
    'postprocess_translation' : 'Postprocesar Traducción',
    'preprocess_subtitles' : 'Preprocesar Subtítulos',
    'project' : 'Proyecto',
    'prompt' : 'Solicitud',
    'prompt_template' : 'Plantilla Solicitud',
    'provider' : 'Proveedor',
    'provider_settings' : 'Configuración Proveedor',
    'proxy' : 'Proxy',
    'rate_limit' : 'Límite Tasa',
    'reasoning_effort' : 'Esfuerzo Razonamiento',
    'remove_filler_words' : 'Eliminar Palabras De Relleno',
    'retry_on_error' : 'Reintentar En Error',
    'reuse_client' : 'Reutilizar Cliente',
    'save_preprocessed_subtitles' : 'Guardar Subtítulos Preprocesados',
    'scene_threshold' : 'Umbral Escena',
    'secret_access_key' : 'Clave Secreta Acceso',
    'server_address' : 'Dirección Servidor',
    'server_url' : 'Url Servidor',
    'stop_on_error' : 'Detener En Error',
    'substitution_mode' : 'Modo Sustitución',
    'supports_conversation' : 'Soporta Conversación',
    'supports_parallel_threads' : 'Soporta Hilos Paralelos',
    'supports_system_messages' : 'Soporta Mensajes Sistema',
    'target_language' : 'Idioma Destino',
    'temperature' : 'Temperatura',
    'theme' : 'Tema',
    'thinking' : 'Pensando',
    'timeout' : 'Tiempo De Espera',
    'ui_language' : 'Idioma Interfaz',
    'use_httpx' : 'Usar Httpx',
    'version' : 'Versión',
    'whitespaces_to_newline' : 'Espacios A Salto De Línea',
    'write_backup' : 'Escribir Copia Seguridad',
    '{starting} {threaded} translation' : '{Starting} Traducción {Threaded}',

    # Status
    'Ready.': 'Listo.',
    'Performing {action}': 'Realizando {action}',
    '{num} commands in queue.': '{num} órdenes en cola.',
    '{command} undone.': '{command} deshecha.',
    '{command} aborted.': '{command} cancelado.',
    '{command} added to queue.': '{command} añadida a la cola.',
    '{command} started.': '{command} iniciada.',
    '{command} was successful.': '{command} realizada correctamente.',
    '{command} failed.': '{command} falló.',
    'Can undo {command}': 'Se puede deshacer {command}',
    'Can redo {command}': 'Se puede rehacer {command}',

    # Toolbar actions and tooltips
    'Exit Program': 'Salir del programa',
    'Load Subtitles': 'Cargar subtítulos',
    'Save Project': 'Guardar proyecto',
    'Settings': 'Configuración',
    'Start Translating': 'Iniciar traducción',
    'Start Translating Fast': 'Traducción rápida',
    'Stop Translating': 'Detener traducción',
    'Undo': 'Deshacer',
    'Redo': 'Rehacer',
    'About': 'Acerca de',
    'Quit': 'Salir',
    'Load Project/Subtitles (Hold shift to reload subtitles)': 'Cargar proyecto/subtítulos (Mantén Mayús para recargar subtítulos)',
    'Save project (Hold shift to save as...)': 'Guardar proyecto (Mantén Mayús para Guardar como...)',
    'Start Translating (hold shift to retranslate)': 'Iniciar traducción (Mantén Mayús para retraducir)',
    'Start translating on multiple threads (fast but unsafe)': 'Iniciar traducción en varios hilos (rápido pero no seguro)',
    'Stop translation': 'Detener traducción',
    'Undo last action': 'Deshacer última acción',
    'Redo last undone action': 'Rehacer la última acción deshecha',
    'About this program': 'Acerca de este programa',
    'Nothing to undo': 'Nada que deshacer',
    'Nothing to redo': 'Nada que rehacer',
    'Undo {command}': 'Deshacer {command}',
    'Redo {command}': 'Rehacer {command}',

    # Project toolbar
    'Hide/Show Project Options': 'Mostrar/Ocultar opciones del proyecto',

    # File dialogs
    'Open File': 'Abrir archivo',
    'Save Project File': 'Guardar archivo de proyecto',
    'Subtitle files': 'Archivos de subtítulos',
    'All Files': 'Todos los archivos',
    'Subtrans projects': 'Proyectos Subtrans',
    'Text Files (*.txt);;All Files (*))': 'Archivos de texto (*.txt);;Todos los archivos (*))',

    # Selection view buttons
    'Translate Selection': 'Traducir selección',
    'Improve Selection': 'Mejorar selección',
    'Auto-Split Batch': 'Dividir lote automáticamente',
    'Reparse Translation': 'Reanalizar traducción',
    'Split Batch': 'Dividir lote',
    'Split Scene': 'Dividir escena',
    'Merge Lines': 'Combinar líneas',
    'Merge Scenes': 'Combinar escenas',
    'Merge Batches': 'Combinar lotes',
    'Delete Lines': 'Eliminar líneas',
    'Swap Text': 'Intercambiar texto',

    # Project settings panel items
    'Project Settings': 'Configuración del proyecto',
    'Movie Name': 'Nombre de la película',
    'Target Language': 'Idioma objetivo',
    'Add RTL Markers': 'Agregar marcadores RTL',
    'Include Original Text': 'Incluir texto original',
    'Description': 'Descripción',
    'Names': 'Nombres',
    'Substitutions': 'Sustituciones',
    'Substitution Mode': 'Modo de sustitución',
    'Provider': 'Proveedor',
    'Model': 'Modelo',
    'Edit Instructions': 'Editar instrucciones',
    'Copy From Another Project': 'Copiar desde otro proyecto',
    'Select project to copy settings from': 'Selecciona el proyecto del que copiar la configuración',
    'Subtrans Files (*.subtrans);;All Files (*)': 'Archivos Subtrans (*.subtrans);;Todos los archivos (*)',

    # Dialogs common
    'OK': 'Aceptar',
    'Cancel': 'Cancelar',
    'Defaults': 'Predeterminados',

    # First-run options
    'The language of the application interface': 'El idioma de la interfaz de la aplicación',
    'Default language to translate the subtitles to': 'Idioma predeterminado al que traducir los subtítulos',
    'The translation provider to use': 'El proveedor de traducción a utilizar',
    'Customise the appearance of gui-subtrans': 'Personaliza la apariencia de gui-subtrans',

    # Settings dialog help texts
    'The default language to translate the subtitles to': 'El idioma predeterminado al que traducir los subtítulos',
    'The language of the application interface (requires restart)': 'El idioma de la interfaz de la aplicación (requiere reinicio)',
    'Include original text in translated subtitles': 'Incluir el texto original en los subtítulos traducidos',
    'Add RTL markers around translated lines that contain primarily right-to-left script on save': 'Agregar marcadores RTL alrededor de líneas traducidas que contienen principalmente escritura de derecha a izquierda al guardar',
    'Instructions for the translation provider to follow': 'Instrucciones que debe seguir el proveedor de traducción',
    'The (brief) instruction for each batch of subtitles. Some [tags] are automatically filled in': 'La instrucción (breve) para cada lote de subtítulos. Algunas [etiquetas] se rellenan automáticamente',
    'Automatically save the project after each translation batch': 'Guardar automáticamente el proyecto después de cada lote de traducción',
    'Save a backup copy of the project when opening it': 'Guardar una copia de seguridad del proyecto al abrirlo',
    'If true, translations that fail validation will be retried with a note about the error': 'Si es verdadero, las traducciones que fallen la validación se reintentarán con una nota sobre el error',
    'Stop translating if an error is encountered': 'Detener la traducción si ocurre un error',
    'The AI translation service to use': 'El servicio de traducción de IA a utilizar',
    'Preprocess subtitles when they are loaded': 'Preprocesar subtítulos al cargarlos',
    'Postprocess subtitles after translation': 'Posprocesar subtítulos después de la traducción',
    'Save preprocessed subtitles to a separate file': 'Guardar los subtítulos preprocesados en un archivo separado',
    'Maximum duration of a single line of subtitles': 'Duración máxima de una línea de subtítulos',
    'Minimum duration of a single line of subtitles': 'Duración mínima de una línea de subtítulos',
    'Merge lines with a duration less than this with the previous line': 'Unir líneas con una duración menor que esta con la línea anterior',
    'Minimum number of characters to split a line at': 'Número mínimo de caracteres para dividir una línea',
    'Add line breaks to text with dialog markers': 'Agregar saltos de línea al texto con marcas de diálogo',
    'Ensure dialog markers match in multi-line subtitles': 'Asegurar que las marcas de diálogo coincidan en subtítulos de varias líneas',
    'Convert blocks of whitespace and Chinese Commas to newlines': 'Convertir bloques de espacios y comas chinas en nuevas líneas',
    'Ensure full-width punctuation is used in Asian languages': 'Asegurar que se use puntuación de ancho completo en idiomas asiáticos',
    'Convert wide dashes (emdash) to standard dashes': 'Convertir guiones anchos (emdash) a guiones estándar',
    'Add line breaks to long single lines (post-process)': 'Agregar saltos de línea a líneas largas (posprocesado)',
    'Maximum length of a single line of subtitles': 'Longitud máxima de una línea de subtítulos',
    'Minimum length of a single line of subtitles': 'Longitud mínima de una línea de subtítulos',
    'Remove filler_words and filler words from subtitles': 'Eliminar filler_words y muletillas de los subtítulos',
    'Comma-separated list of filler_words to remove': 'Lista separada por comas de filler_words para eliminar',
    'Maximum number of simultaneous translation threads for fast translation': 'Número máximo de hilos simultáneos para traducción rápida',
    'Avoid creating a new batch smaller than this': 'Evitar crear un lote nuevo más pequeño que esto',
    'Divide any batches larger than this into multiple batches': 'Dividir cualquier lote mayor que esto en varios lotes',
    'Consider a new scene to have started after this many seconds without subtitles': 'Considerar que una nueva escena ha comenzado tras estos segundos sin subtítulos',
    'Whether to substitute whole words or partial matches, or choose automatically based on input language': 'Ya sea sustituir palabras completas o coincidencias parciales, o elegir automáticamente según el idioma',
    'Limits the number of scene/batch summaries to include as context with each translation batch': 'Limita el número de resúmenes de escena/lote a incluir como contexto con cada lote de traducción',
    'Maximum length of the context summary to include with each translation batch': 'Longitud máxima del resumen de contexto a incluir con cada lote de traducción',
    'Validator: Maximum number of characters to allow in a single translated line': 'Validador: Número máximo de caracteres permitidos en una sola línea traducida',
    'Validator: Maximum number of newlines to allow in a single translated line': 'Validador: Número máximo de saltos de línea permitidos en una sola línea traducida',

    # New Project Settings
    'Language to translate the subtitles to': 'Idioma al que traducir los subtítulos',
    'AI model to use as the translator': 'Modelo de IA a usar como traductor',
    'Number of seconds gap to consider it a new scene': 'Número de segundos de pausa para considerar una nueva escena',
    'Fewest lines to send in separate batch': 'Menor número de líneas para enviar en lote separado',
    'Most lines to send in each batch': 'Mayor número de líneas para enviar en cada lote',
    'Preprocess subtitles before batching': 'Preprocesar subtítulos antes de agrupar',
    'Detailed instructions for the translator': 'Instrucciones detalladas para el traductor',
    'High-level instructions for the translator': 'Instrucciones de alto nivel para el traductor',

    # About dialog
    'Logo generated with <a href="https://stability.ai/stablediffusion">Stable Diffusion XL</a>': 'Logotipo generado con <a href="https://stability.ai/stablediffusion">Stable Diffusion XL</a>',
    'GUI-Subtrans uses LLMs to translate SRT subtitles into other languages, or to improve the quality of an existing translation.': 'GUI-Subtrans usa LLMs para traducir subtítulos SRT a otros idiomas, o para mejorar la calidad de una traducción existente.',
    'GUI-Subtrans would not work without these libraries:\n': 'GUI-Subtrans no funcionaría sin estas bibliotecas:\n',

    # Messages and status
    'All batches translated': 'Todos los lotes traducidos',
    '{done} of {total} batches translated': '{done} de {total} lotes traducidos',
    '{lines} lines in {batches} batches': '{lines} líneas en {batches} lotes',
    '1 line': '1 línea',
    'Batch {num}': 'Lote {num}',
    'Lines {first}-{last} ({start} -> {end})': 'Líneas {first}-{last} ({start} -> {end})',
    'Scene {num}': 'Escena {num}',
    'User Prompt:\n {text}': 'Solicitud del usuario:\n {text}',
    'Gap: {gap}, Length: {duration}': 'Pausa: {gap}, Duración: {duration}',
    'Length: {duration}': 'Duración: {duration}',
    '{count} lines': '{count} líneas',
    '{count} translated': '{count} traducidas',
    '{count} lines translated': '{count} líneas traducidas',
    '{done} of {total} lines translated': '{done} de {total} líneas traducidas',
    '{lines} lines in {scenes} scenes and {batches} batches': '{lines} líneas en {scenes} escenas y {batches} lotes',

    # Errors, prompts, misc
    'Error': 'Error',
    'Error: {error}': 'Error: {error}',
    'No translation providers available. Please install one or more providers.': 'No hay proveedores de traducción disponibles. Instale uno o más proveedores.',
    'Max batch size is less than min batch size': 'El tamaño máximo de lote es menor que el mínimo',
    'Cannot undo the last command': 'No se puede deshacer la última acción',
    'Error undoing the last command: {error}': 'Error al deshacer la última acción: {error}',
    'Cannot redo the last command': 'No se puede rehacer la última acción',
    'Error redoing the last command: {error}': 'Error al rehacer la última acción: {error}',
    'Nothing to save!': '¡Nada que guardar!',
    'Nothing selected to translate': 'Nada seleccionado para traducir',
    'No scenes selected for translation': 'No hay escenas seleccionadas para traducir',
    'Nothing selected to reparse': 'Nada seleccionado para reanalizar',
    'Unable to preview batches: {error}': 'No se pueden previsualizar los lotes: {error}',
    'Unable to update settings: {error}': 'No se puede actualizar la configuración: {error}',
    'Provider error: {error}': 'Error del proveedor: {error}',
    'Unable to load instructions from {file}: {error}': 'No se pueden cargar instrucciones desde {file}: {error}',
    'Project instructions set from {file}': 'Instrucciones del proyecto establecidas desde {file}',
    'Prompt: {text}': 'Solicitud: {text}',
    'Instructions: {text}': 'Instrucciones: {text}',
    'Translating scene number {scene}': 'Traduciendo la escena número {scene}',
    'Translating scene number {scene} batch {batches}': 'Traduciendo la escena número {scene} lote {batches}',
    'Aborted translation of scene {scene}': 'Traducción de la escena {scene} abortada',
    'Errors: {errors}': 'Errores: {errors}',
    'Errors translating scene {scene} - aborting translation': 'Errores al traducir la escena {scene} - abortando la traducción',
    'Error translating scene {scene}: {error}': 'Error al traducir la escena {scene}: {error}',
    'Unable to translate scene because project is not set on datamodel': 'No se puede traducir la escena porque el proyecto no está establecido en el modelo de datos',
    'Executing LoadSubtitleFile {file}': 'Ejecutando carga de archivo {file}',
    'Unable to load subtitles from {file}': 'No se pueden cargar subtítulos de {file}',
    'Unable to load {file} ({error})': 'No se puede cargar {file} ({error})',
    'Saving backup copy of the project': 'Guardando copia de seguridad del proyecto',
    'Scene {scene} Batch {batch}': 'Escena {scene} Lote {batch}',
    'Scene {scene}, batch {batch}': 'Escena {scene}, lote {batch}',
    'Messages': 'Mensajes',
    'Summary': 'Resumen',
    'Prompt': 'Solicitud',
    'Response': 'Respuesta',
    'Context': 'Contexto',
    'Reasoning': 'Razonamiento',
    'Selection {task_type}': 'Selección {task_type}',
    'Resuming': 'Reanudando',
    'Starting': 'Iniciando',
    'multithreaded': 'multihilo',
    'single threaded': 'de un solo hilo',
    'No subtitles': 'No hay subtítulos',
    'No file path specified': 'No se especificó una ruta de archivo',
    'No lines were deleted': 'No se eliminaron líneas',
    'No deletions to undo': 'No hay eliminaciones que deshacer',
    'Original line {line} not found in batch {batch}': 'Línea original {line} no encontrada en el lote {batch}',
    'Not sure what you just double-clicked on': 'No estoy seguro de qué acabas de hacer doble clic',
    'Please configure the translation provider settings': 'Configura la configuración del proveedor de traducción',
    'Please select a batch to split the scene at': 'Selecciona un lote donde dividir la escena',
    'Please select a line to split the batch at': 'Selecciona una línea donde dividir el lote',
    'Please select a single split point': 'Selecciona un único punto de división',
    'Reparse batches {batches}': 'Reanalizar lotes {batches}',
    'Restoring deleted lines': 'Restaurando líneas eliminadas',
    'Splitting batch {scene} at batch {batch}': 'Dividiendo la escena {scene} en el lote {batch}',
    'Splitting scene {scene} batch: {batch} at line {line}': 'Dividiendo la escena {scene} lote: {batch} en la línea {line}',
    'Unable to reparse batches because project is not set': 'No se pueden reanalizar lotes porque no se ha establecido el proyecto',
    'Unable to merge selection ({selection})': 'No se puede combinar la selección ({selection})',
    'Unable to undo SplitBatchCommand command: {error}': 'No se puede deshacer el comando SplitBatchCommand: {error}',
    'Unable to undo SplitScene command: {error}': 'No se puede deshacer el comando SplitScene: {error}',
    'Unable to create option widget for {key}: {error}': 'No se puede crear el widget de opción para {key}: {error}',
    'Unable to create {provider} provider: {error}': 'No se puede crear el proveedor {provider}: {error}',
    'Project is not valid': 'El proyecto no es válido',
    'Subtitles have not been batched': 'Los subtítulos no han sido agrupados en lotes',
    'Deleting lines {lines}': 'Eliminando líneas {lines}',
    'Batch ({scene},{batch}) not found': 'Lote ({scene},{batch}) no encontrado',
    'Can only autosplit a single batch': 'Solo se puede dividir automáticamente un lote',
    'Can only model subtitle files': 'Solo se pueden procesar archivos de subtítulos',
    'Can only swap text of a single batch': 'Solo se puede intercambiar el texto de un único lote',

    # Untranslated
    'Add RTL markers around translated lines that contain primarily right-to-left script on save': 'Agregar marcadores RTL alrededor de las líneas traducidas que contienen principalmente escritura de derecha a izquierda al guardar',
    'All scenes are fully translated': 'Todas las escenas están completamente traducidas',
    'An Anthropic Claude API key is required to use this provider (https://console.anthropic.com/settings/keys)': 'Se requiere una clave de API de Anthropic Claude para usar este proveedor (https://console.anthropic.com/settings/keys)',
    'Auto-splitting batch {scene} batch {batch}': 'Dividiendo automáticamente el lote {scene} lote {batch}',
    'Cannot delete scenes or batches yet': 'Aún no se pueden eliminar escenas o lotes',
    'Cannot find scene {scene} batch {batch}': 'No se puede encontrar la escena {scene} lote {batch}',
    'Cannot merge less than two scenes': 'No se pueden fusionar menos de dos escenas',
    'Cannot merge lines, some lines are missing': 'No se pueden fusionar líneas, faltan algunas líneas',
    'Cannot merge non-sequential elements': 'No se pueden fusionar elementos no secuenciales',
    'Cannot split scene {scene} because it doesn\'t exist': 'No se puede dividir la escena {scene} porque no existe',
    'Cannot undo merge, scene sizes were not saved': 'No se puede deshacer la fusión, los tamaños de escena no se guardaron',
    'Cannot undo merge, undo data was not saved': 'No se puede deshacer la fusión, los datos de deshacer no se guardaron',
    'CheckProviderSettings: {error}': 'VerificarConfiguraciónProveedor: {error}',
    'Consider a new scene to have started after this many seconds without subtitles': 'Considerar que una nueva escena ha comenzado después de esta cantidad de segundos sin subtítulos',
    'Developed by: MachineWrapped<br>Contact: machinewrapped@gmail.com<br><a href=\"https://github.com/machinewrapped/gpt-subtrans\">GitHub Repository</a><br>Thanks to all contributors and those who have reported issues.': 'Desarrollado por: MachineWrapped<br>Contacto: machinewrapped@gmail.com<br><a href=\"https://github.com/machinewrapped/gpt-subtrans\">Repositorio de GitHub</a><br>Gracias a todos los colaboradores y a quienes han reportado problemas.',
    'Edit data must be a dictionary': 'Los datos de edición deben ser un diccionario',
    'Editing batch ({scene},{batch})': 'Editando lote ({scene},{batch})',
    'Editing line {line}': 'Editando línea {line}',
    'Enable thinking mode for translations': 'Habilitar modo de pensamiento para traducciones',
    'Error reparsing scene {scene} batch {batch}: {error}': 'Error al reanalizar la escena {scene} lote {batch}: {error}',
    'Exiting Program': 'Saliendo del programa',
    'Expected a dictionary, got a {type}': 'Se esperaba un diccionario, se obtuvo un {type}',
    'Expected a patch dictionary': 'Se esperaba un diccionario de parches',
    'Failed to merge lines': 'Fallo al fusionar líneas',
    'GUI-Subtrans is released under the MIT License.\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software.': 'GUI-Subtrans se publica bajo la Licencia MIT.\n\nPor la presente se concede permiso, libre de cargos, a cualquier persona que obtenga una copia de este software y de los archivos de documentación asociados, para tratar el software sin restricción, incluyendo sin limitación los derechos de uso, copia, modificación, fusión, publicación, distribución, sublicencia y/o venta de copias del software.',
    'GUI-Subtrans uses LLMs to translate SRT subtitles into other languages, or to improve the quality of an existing translation.': 'GUI-Subtrans utiliza LLMs para traducir subtítulos SRT a otros idiomas, o para mejorar la calidad de una traducción existente.',
    'GUI-Subtrans would not work without these libraries:\n': 'GUI-Subtrans no funcionaría sin estas bibliotecas:\n',
    'If true, translations that fail validation will be retried with a note about the error': 'Si es verdadero, las traducciones que fallen la validación se reintentarán con una nota sobre el error',
    'Invalid translation provider': 'Proveedor de traducción no válido',
    'Limits the number of scene/batch summaries to include as context with each translation batch': 'Limita el número de resúmenes de escenas/lotes a incluir como contexto con cada lote de traducción',
    'Line item {row} has no line number': 'El elemento de línea {row} no tiene número de línea',
    'Line {line} not found in any batch': 'Línea {line} no encontrada en ningún lote',
    'Line {line} not found in batch ({scene},{batch})': 'Línea {line} no encontrada en el lote ({scene},{batch})',
    'Line {line}: {start} --> {end}': 'Línea {line}: {start} --> {end}',
    'Logo generated with <a href=\"https://stability.ai/stablediffusion\">Stable Diffusion XL</a>': 'Logotipo generado con <a href=\"https://stability.ai/stablediffusion\">Stable Diffusion XL</a>',
    'Maximum length of the context summary to include with each translation batch': 'Longitud máxima del resumen de contexto a incluir con cada lote de traducción',
    'No batches found for lines to merge': 'No se encontraron lotes para fusionar líneas',
    'No lines selected to delete': 'No se seleccionaron líneas para eliminar',
    'No translation providers available. Please install one or more providers.': 'No hay proveedores de traducción disponibles. Instale uno o más proveedores.',
    'Nothing selected to delete': 'Nada seleccionado para eliminar',
    'Nothing selected to merge': 'Nada seleccionado para fusionar',
    'Nothing to translate': 'Nada que traducir',
    'Optional proxy server to use for requests (e.g. https://api.not-anthropic.com/': 'Servidor proxy opcional para usar en las solicitudes (por ejemplo, https://api.not-anthropic.com/',
    'Provider {provider} needs configuring: {message}': 'El proveedor {provider} necesita configuración: {message}',
    'The (brief) instruction for each batch of subtitles. Some [tags] are automatically filled in': 'La instrucción (breve) para cada lote de subtítulos. Algunas [etiquetas] se rellenan automáticamente',
    'The maximum number of tokens to use for thinking': 'El número máximo de tokens a usar para pensar',
    'The maximum number of tokens to use for translations': 'El número máximo de tokens a usar para traducciones',
    'The model to use for translations': 'El modelo a usar para traducciones',
    'The rate limit to use for translations (default 60.0)': 'El límite de velocidad a usar para traducciones (por defecto 60.0)',
    'The temperature to use for translations (default 0.0)': 'La temperatura a usar para traducciones (por defecto 0.0)',
    'Translation provider settings are not valid. Please check the settings.': 'La configuración del proveedor de traducción no es válida. Por favor, revise la configuración.',
    'Unable to edit batch because datamodel is invalid': 'No se puede editar el lote porque el modelo de datos no es válido',
    'Undoing edit batch ({scene},{batch})': 'Deshaciendo edición de lote ({scene},{batch})',
    'Undoing edit line {line}': 'Deshaciendo edición de línea {line}',
    'Updating line {line} with {original} > {translated}': 'Actualizando línea {line} con {original} > {translated}',
    'Updating scene {scene} batch {batch} with {update}': 'Actualizando escena {scene} lote {batch} con {update}',
    'Updating scene {scene} with {update}': 'Actualizando escena {scene} con {update}',
    'User Prompt:\n {text}': 'Mensaje del usuario:\n {text}',
    'Validator: Maximum number of characters to allow in a single translated line': 'Validador: Número máximo de caracteres permitidos en una sola línea traducida',
    'Validator: Maximum number of newlines to allow in a single translated line': 'Validador: Número máximo de saltos de línea permitidos en una sola línea traducida',
    'Whether to substitute whole words or partial matches, or choose automatically based on input language': 'Si sustituir palabras completas o coincidencias parciales, o elegir automáticamente según el idioma de entrada',
    '{starting} {threaded} translation': '{starting} traducción {threaded}',
}

# Regex-based simple rules for some templated keys
REGEX_RULES = [
    (re.compile(r'^Scene (\{[^}]+\}) Batch (\{[^}]+\})$'), r'Escena \1 Lote \2'),
    (re.compile(r'^Scene (\{[^}]+\}), batch (\{[^}]+\})$'), r'Escena \1, lote \2'),
    (re.compile(r'^Batch (\{[^}]+\})$'), r'Lote \1'),
    (re.compile(r'^Line (\{[^}]+\})$'), r'Línea \1'),
    (re.compile(r'^Deleting lines (.+)$'), r'Eliminando líneas \1'),
    (re.compile(r'^Merging scenes (.+)$'), r'Combinando escenas \1'),
    (re.compile(r'^Merging lines (.+) in batch (.+)$'), r'Combinando líneas \1 en el lote \2'),
    (re.compile(r'^Reparse batches (.+)$'), r'Reanalizar lotes \1'),
    (re.compile(r'^Executing LoadSubtitleFile (.+)$'), r'Ejecutando carga de archivo \1'),
    (re.compile(r'^Lines (\{[^}]+\}) not found in batch (\{[^}]+\})$'), r'Líneas \1 no encontradas en el lote \2'),
]


def seed_entries(po_path: str) -> int:
    if not os.path.exists(po_path):
        raise FileNotFoundError(po_path)

    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated = 0
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')
        if line.startswith('msgid "'):
            # Only handle single-line msgid entries
            if line.endswith('"') and '\\n' not in line:
                msgid = line[len('msgid "'):-1]
                # Find msgstr
                j = i + 1
                while j < len(lines) and not lines[j].startswith('msgstr'):
                    j += 1
                if j < len(lines) and lines[j].strip() == 'msgstr ""':
                    trans = MAPPING.get(msgid)
                    if not trans:
                        # Try regex rules
                        for pattern, repl in REGEX_RULES:
                            if pattern.match(msgid):
                                trans = pattern.sub(repl, msgid)
                                break
                    if trans:
                        lines[j] = f'msgstr "{trans}"\n'
                        updated += 1
        i += 1

    if updated:
        with open(po_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return updated


def main():
    count = seed_entries(ES_PO)
    print(f"Seeded {count} Spanish translations in {ES_PO}")


if __name__ == '__main__':
    main()


