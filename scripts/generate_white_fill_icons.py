#!/usr/bin/env python3
"""
Generate an alternative set of SVG icons with white fills and black borders.

This script writes a collection of simple toolbar icons into an ``icons_white``
directory. Each icon is drawn within a 24×24 coordinate system and uses
a consistent aesthetic: outlines are solid black and closed shapes are
filled white. Because the overall ``svg`` has no fill on its own,
the transparent background allows the host toolbar colour to show through.

The design choices are guided by the requirement that the icons must be
readable on both light and dark backgrounds without dynamically recolouring
via Qt. A white interior bounded by a black stroke meets this goal by
providing contrast on dark themes (white stands out) and legibility on
light themes (the black outline defines the shape).

The icons covered here correspond to the toolbar actions used by
GUI‑Subtrans:

* ``load_subtitles.svg`` – folder with downward arrow.
* ``save_project.svg`` – tray with downward arrow.
* ``start_translating.svg`` – single play triangle.
* ``start_translating_fast.svg`` – fast‑forward (double triangle).
* ``stop_translating.svg`` – stop square.
* ``undo.svg`` – curving left arrow.
* ``redo.svg`` – curving right arrow.
* ``settings.svg`` – gear composed of concentric circles and spokes.
* ``about.svg`` – information symbol inside a circle.
* ``quit.svg`` – doorway with an arrow entering it.
* ``project_settings.svg`` – document with a gear centred inside.

Run this script directly to create the icons.  The output directory will be
created next to the script (``icons_white``).
"""

from pathlib import Path

# Where to write the icons
ICON_DIR = Path(__file__).resolve().parent / "icons_white"


def write_svg(filename: str, elements: str, viewbox: str = "0 0 24 24") -> None:
    """Helper to write a complete SVG file with a standard preamble.

    Each SVG uses the same coordinate system and default stroke settings. A
    blank fill on the root element leaves the background transparent, while
    individual shapes specify their own fill (white) and stroke (black).

    Args:
        filename: Name of the file relative to ``ICON_DIR``.
        elements: Raw SVG child elements as a string.
        viewbox: ViewBox specification for the root <svg>.
    """
    ICON_DIR.mkdir(parents=True, exist_ok=True)
    svg = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        f'<svg viewBox="{viewbox}" width="24" height="24" '
        'fill="none" stroke="black" stroke-width="2" '
        'stroke-linecap="round" stroke-linejoin="round" '
        'xmlns="http://www.w3.org/2000/svg">\n'
        f'{elements}\n'
        '</svg>\n'
    )
    (ICON_DIR / filename).write_text(svg)


def generate_load_subtitles() -> None:
    """Create the 'load subtitles' icon.

    The folder shape has a black outline and white fill. A downward arrow
    composed of three strokes sits above the folder flap. The arrow itself
    does not fill, ensuring it remains a line drawing.
    """
    elements = """
    <!-- Folder body -->
    <path d="M3 8v8a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9h-7l-2-2H5a2 2 0 0 0-2 2z" fill="white" stroke="black"/>
    <!-- Downward arrow -->
    <line x1="12" y1="10" x2="12" y2="15" stroke="black"/>
    <polyline points="9 12 12 15 15 12" fill="none" stroke="black"/>
    """
    write_svg("load_subtitles.svg", elements)


def generate_save_project() -> None:
    """Create the 'save project' icon.

    Draw a tray with a downward arrow.  The tray is a rectangle with
    rounded corners for a friendly appearance.  The arrow is centred
    above the tray.
    """
    elements = """
    <!-- Tray -->
    <rect x="4" y="14" width="16" height="6" rx="2" ry="2" fill="white" stroke="black"/>
    <!-- Downward arrow -->
    <line x1="12" y1="6" x2="12" y2="11" stroke="black"/>
    <polyline points="9 8 12 11 15 8" fill="none" stroke="black"/>
    """
    write_svg("save_project.svg", elements)


def generate_start_translating() -> None:
    """Create the 'start translating' (play) icon.

    A single triangle with white fill and black stroke forms the play
    symbol.
    """
    elements = """
    <polygon points="8 6 17 12 8 18" fill="white" stroke="black"/>
    """
    write_svg("start_translating.svg", elements)


def generate_start_translating_fast() -> None:
    """Create the 'start translating fast' (fast‑forward) icon.

    Two play triangles side by side, each with white fill and black stroke.
    """
    elements = """
    <polygon points="5 6 12 12 5 18" fill="white" stroke="black"/>
    <polygon points="12 6 19 12 12 18" fill="white" stroke="black"/>
    """
    write_svg("start_translating_fast.svg", elements)


def generate_stop_translating() -> None:
    """Create the 'stop translating' icon.

    A square with slightly rounded corners represents the stop symbol.
    """
    elements = """
    <rect x="8" y="8" width="8" height="8" rx="1" ry="1" fill="white" stroke="black"/>
    """
    write_svg("stop_translating.svg", elements)


def generate_undo() -> None:
    """Create the 'undo' icon.

    A stylised left‑curving arrow is drawn as a closed shape filled with
    white and outlined in black.  The right side of the shape curves
    inward using a quadratic Bézier curve, evoking the notion of
    reversing or going back.
    """
    # Draw the undo symbol as a circle with a curved arrow inside. The circle
    # provides the required border and fill; the arrow consists of a curved
    # path and an arrow head drawn with a polyline.
    elements = """
    <circle cx="12" cy="12" r="10" fill="white" stroke="black"/>
    <path d="M15 9a5 5 0 1 0 0 6" fill="none" stroke="black"/>
    <polyline points="13 9 15 9 15 11" fill="none" stroke="black"/>
    """
    write_svg("undo.svg", elements)


def generate_redo() -> None:
    """Create the 'redo' icon.

    Mirror of the undo symbol: a right‑curving arrow drawn as a closed
    shape with white fill and black outline.
    """
    # Mirror of the undo symbol: a circle with a curved arrow bending right.
    elements = """
    <circle cx="12" cy="12" r="10" fill="white" stroke="black"/>
    <path d="M9 9a5 5 0 1 1 0 6" fill="none" stroke="black"/>
    <polyline points="11 9 9 9 9 11" fill="none" stroke="black"/>
    """
    write_svg("redo.svg", elements)


def generate_settings() -> None:
    """Create the 'settings' icon.

    A gear shape comprised of an outer ring and a smaller inner ring, both
    filled white, surrounded by eight spokes.  The spokes are drawn as
    simple lines radiating from the centre.
    """
    # Spoke end coordinates relative to centre (12,12)
    spokes = [
        ((12, 3), (12, 6)),    # North
        ((12, 18), (12, 21)),  # South
        ((3, 12), (6, 12)),    # West
        ((18, 12), (21, 12)),  # East
        ((17.07, 6.93), (18.49, 5.51)),  # NE
        ((17.07, 17.07), (18.49, 18.49)),# SE
        ((6.93, 17.07), (5.51, 18.49)),  # SW
        ((6.93, 6.93), (5.51, 5.51)),    # NW
    ]
    lines_svg = "\n".join(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black"/>'
        for (x1, y1), (x2, y2) in spokes
    )
    elements = f"""
    <circle cx="12" cy="12" r="9" fill="white" stroke="black"/>
    <circle cx="12" cy="12" r="3" fill="white" stroke="black"/>
    {lines_svg}
    """
    write_svg("settings.svg", elements)


def generate_about() -> None:
    """Create the 'about' icon.

    The familiar information symbol: a white filled circle with a black
    outline surrounds a vertical bar and dot.
    """
    elements = """
    <!-- Outer circle -->
    <circle cx="12" cy="12" r="10" fill="white" stroke="black"/>
    <!-- Body of the i -->
    <line x1="12" y1="10" x2="12" y2="16" stroke="black"/>
    <!-- Dot of the i -->
    <circle cx="12" cy="7" r="1" fill="black" stroke="black"/>
    """
    write_svg("about.svg", elements)


def generate_quit() -> None:
    """Create the 'quit' icon.

    Depict a doorway with a left‑pointing arrow entering it.  The door
    occupies the left portion of the icon and is drawn as a rounded
    rectangle with a white fill and black stroke.  The arrow to the
    right is a closed shape with white fill and black outline.
    """
    # The exit icon shows a full door with an arrow pointing into it.
    # The doorframe occupies the left side; the arrow head and tail are
    # drawn as a closed polygon on the right, pointing leftwards so
    # that it appears to enter the door.
    elements = """
    <!-- Doorframe -->
    <rect x="3" y="4" width="14" height="16" rx="1" ry="1" fill="white" stroke="black"/>
    <!-- Arrow entering the door: rectangular tail plus triangular head -->
    <path d="M22 10 L19 10 L17 12 L19 14 L22 14 Z" fill="white" stroke="black"/>
    """
    write_svg("quit.svg", elements)


def generate_project_settings() -> None:
    """Create the 'project settings' icon.

    A document outline with a centred gear overlay.  The document has a
    folded corner drawn with white fill and black outline.  The gear
    mirrors the settings icon: an outer ring, inner ring and spokes.
    """
    # Gear spokes for the small gear within the document
    spokes = [
        ((12, 11), (12, 12.5)),    # North
        ((12, 17), (12, 18.5)),    # South
        ((10.5, 14), (9, 14)),    # West
        ((13.5, 14), (15, 14)),   # East
        ((13.06, 12.94), (14.25, 11.75)),  # NE
        ((13.06, 15.06), (14.25, 16.25)),  # SE
        ((10.94, 15.06), (9.75, 16.25)),   # SW
        ((10.94, 12.94), (9.75, 11.75)),   # NW
    ]
    lines_svg = "\n".join(
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="black"/>'
        for (x1, y1), (x2, y2) in spokes
    )
    elements = f"""
    <!-- Document with folded corner -->
    <path d="M4 4h10l6 6v10H4z" fill="white" stroke="black"/>
    <polyline points="14 4 14 10 20 10" fill="none" stroke="black"/>
    <!-- Gear inside document -->
    <circle cx="12" cy="14" r="3" fill="white" stroke="black"/>
    <circle cx="12" cy="14" r="1" fill="white" stroke="black"/>
    {lines_svg}
    """
    write_svg("project_settings.svg", elements)


def main() -> None:
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