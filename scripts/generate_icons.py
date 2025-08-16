#!/usr/bin/env python3
"""Generate a set of simple SVG icons for the GUI‑Subtrans application.

This script writes a handful of minimalistic, outline‑style icons into a
`./icons` directory in the current working folder.  Each icon is drawn at
24×24 viewbox with a 2 unit stroke width, rounded end caps and joins.  The
icons use the `currentColor` for the stroke which allows them to adapt to
different themes when embedded in a GUI; no fixed colour values are set.

The drawings are deliberately hand‑crafted using basic SVG path commands
instead of relying on any external graphics library.  Each icon is built
from one or more shapes such as lines, polylines, circles and custom paths.

Available icons:

* ``load_subtitles.svg`` – A folder shape with a downward arrow conveying
  the notion of loading/importing subtitles.
* ``save_project.svg`` – A tray with a downward arrow suggesting data being
  stored/saved to disk.
* ``start_translating.svg`` – Two curved arrows forming a loop to hint at
  translation between languages.
* ``start_translating_fast.svg`` – Same as the translation icon but with
  an additional lightning bolt indicating speed.
* ``stop_translating.svg`` – A simple stop symbol drawn as a square.
* ``undo.svg`` – A curved arrow pointing back to the left.
* ``redo.svg`` – A curved arrow pointing forward to the right.
* ``settings.svg`` – A gear with spokes to represent configuration.
* ``about.svg`` – A circle containing an information "i".
* ``quit.svg`` – A door outline with an arrow exiting to the right.
* ``project_settings.svg`` – A document with a small gear to indicate
  settings specific to a project.

To run the generator simply execute this file with Python; the icons will
appear in a directory called ``icons`` in the working directory.
"""

import os
from pathlib import Path

# Directory where icons will be stored
ICON_DIR = Path(__file__).resolve().parent / "icons"


def write_svg(filename: str, elements: str, viewbox: str = "0 0 24 24") -> None:
    """Write a complete SVG file with the provided child elements.

    The wrapper sets up the standard attributes used throughout this icon set:
    a 24×24 viewbox, no fill by default and a stroke that derives from
    ``currentColor`` so that the icon colour can be controlled via CSS.

    Args:
        filename: Name of the file to create inside ``ICON_DIR``.
        elements: A string containing the raw SVG elements (e.g. paths,
            polylines, circles, lines) that make up the icon drawing.
        viewbox: The viewBox attribute for the root SVG element.
    """
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    svg = (
        f'<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg viewBox="{viewbox}" width="24" height="24" '
        f'fill="#ffffff" stroke="currentColor" stroke-width="2" '
        f'stroke-linecap="round" stroke-linejoin="round" '
        f'xmlns="http://www.w3.org/2000/svg">\n'
        f'{elements}\n'
        f'</svg>\n'
    )
    (ICON_DIR / filename).write_text(svg)


def generate_load_subtitles() -> None:
    """Create the 'load subtitles' icon.

    The icon depicts an open folder with a downward arrow entering it.  The
    folder outline consists of a bottom container with a top flap.  The
    arrow is drawn using a vertical line and two diagonal lines for the
    arrow head.
    """
    elements = """
    <!-- Folder body -->
    <path d="M3 8v9a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a1 1 0 0 0-1-1h-7l-2-2H4a1 1 0 0 0-1 1z"/>
    <!-- Downward arrow -->
    <line x1="12" y1="10" x2="12" y2="15"/>
    <polyline points="9 12 12 15 15 12"/>
    """
    write_svg("load_subtitles.svg", elements)


def generate_save_project() -> None:
    """Create the 'save project' icon.

    The icon uses a tray to symbolise a location where data is stored and a
    downward arrow placed above it.  The tray is a rounded rectangle at the
    bottom half of the icon.  The arrow sits centrally above and points
    downward into the tray.
    """
    elements = """
    <!-- Downward arrow -->
    <line x1="12" y1="5" x2="12" y2="12"/>
    <polyline points="9 9 12 12 15 9"/>
    <!-- Tray -->
    <path d="M4 14h16v3a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-3z"/>
    """
    write_svg("save_project.svg", elements)


def generate_start_translating() -> None:
    """Create the 'start translating' icon.

    Two opposing curved arrows describe a loop reminiscent of translation
    between languages.  Each arrow is drawn as a cubic Bézier curve with
    a simple two‑stroke arrow head attached to its end.
    """
    elements = """
    <!-- Upper curved arrow -->
    <path d="M4 13c4-6 12-6 16 0"/>
    <polyline points="18 11 20 13 18 15"/>
    <!-- Lower curved arrow -->
    <path d="M20 11c-4 6-12 6-16 0"/>
    <polyline points="6 13 4 11 6 9"/>
    """
    write_svg("start_translating.svg", elements)


def generate_start_translating_fast() -> None:
    """Create the 'start translating fast' icon.

    This icon builds upon the basic translation icon by overlaying a
    lightning bolt at its centre, hinting at increased speed.  The bolt
    is drawn with sharp angles and fits comfortably inside the swirl of
    arrows.
    """
    elements = """
    <!-- Upper curved arrow -->
    <path d="M4 13c4-6 12-6 16 0"/>
    <polyline points="18 11 20 13 18 15"/>
    <!-- Lower curved arrow -->
    <path d="M20 11c-4 6-12 6-16 0"/>
    <polyline points="6 13 4 11 6 9"/>
    <!-- Lightning bolt -->
    <path d="M12 8l1.5 3h-2l2 3l-3.5-2h2z"/>
    """
    write_svg("start_translating_fast.svg", elements)


def generate_stop_translating() -> None:
    """Create the 'stop translating' icon.

    A simple stop symbol represented by a square positioned centrally
    within the icon's view box.  Unlike the other icons, the square
    employs a filled colour via the stroke attribute (with the rest of
    the icon having no fill) to stand out clearly.
    """
    elements = """
    <rect x="8" y="8" width="8" height="8" stroke="currentColor" fill="currentColor"/>
    """
    write_svg("stop_translating.svg", elements)


def generate_undo() -> None:
    """Create the 'undo' icon.

    The design uses a left facing arrow with a trailing curved path to
    evoke the notion of reversing an action.  A polyline forms the arrow
    head and a quadratic curve produces the sweeping motion.
    """
    elements = """
    <!-- Arrow head -->
    <polyline points="9 9 4 12 9 15"/>
    <!-- Sweeping curve -->
    <path d="M4 12h7a5 5 0 0 1 5 5"/>
    """
    write_svg("undo.svg", elements)


def generate_redo() -> None:
    """Create the 'redo' icon.

    A mirrored counterpart to the undo icon: the arrow head points to the
    right and the sweeping curve travels in the opposite direction.  The
    polyline and path are flipped horizontally.
    """
    elements = """
    <!-- Arrow head -->
    <polyline points="15 9 20 12 15 15"/>
    <!-- Sweeping curve -->
    <path d="M20 12h-7a5 5 0 0 0-5 5"/>
    """
    write_svg("redo.svg", elements)


def generate_settings() -> None:
    """Create the 'settings' icon.

    A minimalist gear is constructed from a small central circle and eight
    spokes extending outward at cardinal and intercardinal points.  This
    abstract representation conveys the idea of configuration and settings
    without requiring intricate geometry.
    """
    # Coordinates for spokes at 45° increments around the gear
    spokes = [
        ((12, 3), (12, 5)),    # North
        ((12, 19), (12, 21)),  # South
        ((3, 12), (5, 12)),    # West
        ((19, 12), (21, 12)),  # East
        ((17.07, 6.93), (18.49, 5.51)),  # NE
        ((17.07, 17.07), (18.49, 18.49)),# SE
        ((6.93, 17.07), (5.51, 18.49)),  # SW
        ((6.93, 6.93), (5.51, 5.51)),    # NW
    ]
    # Build individual line elements for each spoke
    lines_svg = "\n".join(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}"/>'
        for (x1, y1), (x2, y2) in spokes
    )
    # Central circle
    elements = f"""
    <circle cx="12" cy="12" r="3"/>
    {lines_svg}
    """
    write_svg("settings.svg", elements)


def generate_about() -> None:
    """Create the 'about' icon.

    An information symbol: a circle encloses a vertical bar and a dot
    forming the letter 'i'.  The outer circle ensures the icon is
    recognisable at small sizes.
    """
    elements = """
    <!-- Outer circle -->
    <circle cx="12" cy="12" r="10"/>
    <!-- Body of the i -->
    <line x1="12" y1="10" x2="12" y2="16"/>
    <!-- Dot of the i -->
    <circle cx="12" cy="7" r="1" fill="currentColor"/>
    """
    write_svg("about.svg", elements)


def generate_quit() -> None:
    """Create the 'quit' icon.

    A doorway with an arrow pointing out of it symbolises the act of
    exiting the application.  The door is a tall rectangle with a gap on
    the left to indicate an open door, and the arrow points rightwards
    through the opening.
    """
    # The doorway is drawn as an open U‑shaped path rather than a closed
    # rectangle so that the left side remains open (conveying the sense of
    # leaving the application).  The arrow points rightwards through the
    # opening.
    elements = """
    <!-- Doorframe (open on the left) -->
    <path d="M6 3h8a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6"/>
    <!-- Exit arrow -->
    <line x1="14" y1="12" x2="20" y2="12"/>
    <polyline points="18 10 20 12 18 14"/>
    """
    write_svg("quit.svg", elements)


def generate_project_settings() -> None:
    """Create the 'project settings' icon.

    Combines a document outline with a small gear to denote settings
    associated with a specific project or file.  The document has a
    folded corner on the top right, and the gear sits partially over the
    bottom right of the page.
    """
    # Gear for bottom right: small circle with four spokes
    gear_elements = """
    <circle cx="16" cy="18" r="2"/>
    <line x1="16" y1="14.5" x2="16" y2="13.5"/>
    <line x1="16" y1="22.5" x2="16" y2="21.5"/>
    <line x1="13.5" y1="18" x2="14.5" y2="18"/>
    <line x1="18.5" y1="18" x2="19.5" y2="18"/>
    """
    elements = f"""
    <!-- Document outline with folded corner -->
    <path d="M4 3h8l6 6v12H4z"/>
    <polyline points="12 3 12 9 18 9"/>
    <!-- Small gear on the document corner -->
    {gear_elements}
    """
    write_svg("project_settings.svg", elements)


def main() -> None:
    """Generate all icons and save them to disk."""
    generate_load_subtitles()
    generate_save_project()
    generate_start_translating()
    generate_start_translating_fast()
    generate_stop_translating()
    generate_undo()
    generate_redo()
    generate_settings()
    generate_about()
    generate_quit()
    generate_project_settings()


if __name__ == "__main__":
    main()