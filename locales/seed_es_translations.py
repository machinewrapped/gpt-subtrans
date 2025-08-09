#!/usr/bin/env python3
"""
Seed Spanish translations into locales/es/LC_MESSAGES/gui-subtrans.po.
- Fills msgstr for empty entries using an expanded exact mapping
- Applies simple regex-based rules for common formatted strings
Note: Only single-line msgid entries are handled.
"""
import os
import re

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ES_PO = os.path.join(BASE_DIR, 'es', 'LC_MESSAGES', 'gui-subtrans.po')


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

    # Settings dialog help texts (selection)
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
    'Number of times to retry a failed translation before giving up': 'Número de reintentos antes de abandonar una traducción fallida',
    'Seconds to wait before retrying a failed translation': 'Segundos de espera antes de reintentar una traducción fallida',

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
    'GUI-Subtrans is released under the MIT License.\n\nPermission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files, to deal in the software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the software.': 'GUI-Subtrans se publica bajo la licencia MIT.\n\nPor la presente se concede permiso, libre de cargos, a cualquier persona que obtenga una copia de este software y archivos de documentación asociados, para tratar el software sin restricción, incluyendo sin limitación los derechos de usar, copiar, modificar, fusionar, publicar, distribuir, sublicenciar y/o vender copias del software.',
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
}

# Regex-based simple rules for some templated keys
REGEX_RULES = [
    (re.compile(r'^Scene (\{[^}]+\})$'), r'Escena \1'),
    (re.compile(r'^Batch (\{[^}]+\})$'), r'Lote \1'),
    (re.compile(r'^Line (\{[^}]+\})$'), r'Línea \1'),
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


