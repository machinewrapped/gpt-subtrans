#!/usr/bin/env python3
"""
Seed a subset of Spanish translations into locales/es/LC_MESSAGES/gui-subtrans.po
for the most visible UI strings. Only updates empty msgstr for exact single-line
msgid matches.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ES_PO = os.path.join(BASE_DIR, 'es', 'LC_MESSAGES', 'gui-subtrans.po')


MAPPING = {
    'File': 'Archivo',
    'Edit': 'Editar',
    'Tools': 'Herramientas',
    'First Run Options': 'Opciones de primera ejecución',
    'GUI-Subtrans Settings': 'Configuración de GUI-Subtrans',
    'Ready.': 'Listo.',
    'Performing {action}': 'Realizando {action}',
    'About GUI-Subtrans': 'Acerca de GUI-Subtrans',
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
    'Copy From Another Project': 'Copiar desde otro proyecto',
    'Select project to copy settings from': 'Selecciona el proyecto del que copiar la configuración',
    'Subtrans Files (*.subtrans);;All Files (*)': 'Archivos Subtrans (*.subtrans);;Todos los archivos (*)',
    'Edit Instructions': 'Editar instrucciones',
    'Load Instructions': 'Cargar instrucciones',
    'Save Instructions': 'Guardar instrucciones',
    'Defaults': 'Predeterminados',
    'OK': 'Aceptar',
    'Cancel': 'Cancelar',
    'Prompt for each translation request': 'Solicitud para cada petición de traducción',
    'Type of response expected for each line (must match the example format)': 'Tipo de respuesta esperada para cada línea (debe coincidir con el formato del ejemplo)',
    'System instructions for the translator': 'Instrucciones del sistema para el traductor',
    'Supplementary instructions when retrying': 'Instrucciones suplementarias al reintentar',
    'Logo generated with <a href="https://stability.ai/stablediffusion">Stable Diffusion XL</a>': 'Logotipo generado con <a href="https://stability.ai/stablediffusion">Stable Diffusion XL</a>',
    'Scene {num}': 'Escena {num}',
    'Lines {first}-{last} ({start} -> {end})': 'Líneas {first}-{last} ({start} -> {end})',
    'All batches translated': 'Todos los lotes traducidos',
    '{done} of {total} batches translated': '{done} de {total} lotes traducidos',
    '{lines} lines in {batches} batches': '{lines} líneas en {batches} lotes',
    '1 line': '1 línea',
    'Error': 'Error',
    'No translation providers available. Please install one or more providers.': 'No hay proveedores de traducción disponibles. Instale uno o más proveedores.',
}


def seed_simple_entries(po_path: str) -> int:
    if not os.path.exists(po_path):
        raise FileNotFoundError(po_path)

    with open(po_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    updated = 0
    i = 0
    while i < len(lines):
        line = lines[i].rstrip('\n')
        if line.startswith('msgid "') and line.endswith('"') and '\\n' not in line:
            msgid = line[len('msgid "'):-1]
            if msgid in MAPPING:
                # Find the immediate msgstr line (assumes standard layout)
                j = i + 1
                while j < len(lines) and not lines[j].startswith('msgstr'):
                    j += 1
                if j < len(lines) and lines[j].strip() == 'msgstr ""':
                    trans = MAPPING[msgid]
                    lines[j] = f'msgstr "{trans}"\n'
                    updated += 1
                    i = j
        i += 1

    if updated:
        with open(po_path, 'w', encoding='utf-8') as f:
            f.writelines(lines)

    return updated


def main():
    count = seed_simple_entries(ES_PO)
    print(f"Seeded {count} Spanish translations in {ES_PO}")


if __name__ == '__main__':
    main()


