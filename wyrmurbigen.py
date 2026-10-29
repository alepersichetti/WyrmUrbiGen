#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WyrmUrbiGen v0.2.0 - random villages, boroughs, walled cities, castles and
fortresses for OSR games, all in ASCII.

Sibling of WyrmHex (hexcrawl maps) and WyrmDelve (dungeons). It draws the plan
of a settlement with letters and symbols, like an old roguelike, numbers every
building, and writes a key (a TXT file and a PDF file, like WyrmDelve's) with the
history, the government and factions, the inhabitants of every building with
OSR stats, rumours and events, and:

  * a place of rest for adventurers: inns, healers, smiths, horses, retainers
    and mercenaries for hire, prices in gold pieces;
  * a place of adventure, in ruins (long abandoned, full of monsters, with a
    layered history: founding, height, fall and the stories after it) or
    inhabited and threatened (brigands, a cult, plague, a curse, orcs, a beast,
    a necromancer, something from the water, a dragon, a mine, a feud), with
    wandering monsters, monsters and clues in the buildings and treasure, using
    WyrmDelve's bestiary and its Old-School Essentials treasure tables.

It is a fantasy generator: no real places, families, saints or religions.
Names of places, people and gods are built from real particles of eleven
languages, and every settlement worships five gods of its own.

The plan follows real medieval and Renaissance town planning:
  Early Middle Ages  patched walls and palisades, motte-and-bailey castles,
                     Roman castra, crooked streets, the lord's timber hall;
  Late Middle Ages   stone walls with towers, communal squares and town halls,
                     tower houses, planned new towns on a grid, friaries along
                     the walls, concentric castles with a keep;
  Renaissance        bastioned "Italian trace" walls, radial ideal cities,
                     star forts, palaces, loggias, powder magazines.
Every settlement sits on plains, hills, mountains, in a forest, a swamp, on the
coast, on a river or on a lake, and the land shapes walls, streets and trades.

Prints on A4, A3, A2 or A1 at 600 dpi (PNG or PDF); the best paper is
suggested. Five colour schemes, two of them in full colour on white or black,
like WyrmHex. --ascii-only uses keyboard characters only,
like WyrmHex; the .txt maps always do.

Output goes to settlements_generated/<seed>/ next to this file (or --output):
  <seed>_referee.png/.txt   referee's map: building numbers and list, secrets
  <seed>_players.png/.txt   the same map and list without the secrets
  <seed>_key.txt            the whole key as plain text
  <seed>_key.pdf            the key as an A4 PDF file (Sebaldus-Gotisch headings,
                            Crimson Text), with the referee's map inside

Place names sound like one of eleven languages (medieval Italian, Old English,
Renaissance English, Scottish Gaelic, Tolkienesque, Persian and Arabesque,
Byzantine Greek, German, French, Danish and Swedish, Russian and Baltic) or a
mix of them all, in one of five tones (fair, homely, stately, grim, eerie):
millions of names for each, from the roots in data/names.json.

The seed (e.g. C2-B-R-A2R-DE4-K7Q2MB = type+size, era, terrain,
purpose+danger+state, names+tone, code) holds the whole settlement: the same seed
always gives the same one. Seeds without names+tone, made by older versions,
still work and keep their medieval Italian names.

Usage. Every option has an Italian and an English name, use whichever:
  python wyrmurbigen.py                              interactive
  python wyrmurbigen.py --tipo citta --epoca basso   / --type city --era late
  python wyrmurbigen.py --terreno costa              / --terrain coast
  python wyrmurbigen.py --scopo avventura --pericolo 3   / --purpose adventure --danger 3
  python wyrmurbigen.py --dimensione 3               / --size 3
  python wyrmurbigen.py --nomi tedesco --tono cupo    / --names german --tone grim
  python wyrmurbigen.py --seme C2-B-R-A2R-DE4-K7Q2MB / --seed C2-B-R-A2R-DE4-K7Q2MB
  python wyrmurbigen.py --solo-ascii --formato A3 --pdf
  python wyrmurbigen.py --help
Parameters you leave out are chosen at random.

Code and comments are in English, the UI is Italian or English. The words the
settlements are made of are data, in the JSON files of the data folder.
"""

import argparse
import heapq
import json
import math
import os
import random
import re
import sys
import textwrap
import time
import zlib
from collections import Counter, deque

try:                                    # menus: without asciimatics the questions are numbered
    from asciimatics.event import KeyboardEvent, MouseEvent
    from asciimatics.exceptions import ResizeScreenError
    from asciimatics.screen import Screen
except ImportError:
    Screen = None

try:
    from PIL import Image, ImageDraw, ImageFont
    from PIL.PngImagePlugin import PngInfo
except ImportError:
    sys.exit("Manca la libreria Pillow. Installala con:  pip install -r requirements.txt\n"
             "Pillow is missing. Install it with:   pip install -r requirements.txt")

Image.MAX_IMAGE_PIXELS = None           # A1 at 600 dpi: our own maps, no bomb check


# What is where in this file, section by section (search for "# --- name ---"):
#   settings, language       constants, data loading, the Italian and English texts (TEXTS, tr, pick)
#   console output, tables   the progress log; the JSON tables of the data folder
#   dice, seed               dice rolls; reading and writing seeds, random parameters
#   names                    place names and people's names in eleven languages and five tones
#   the plan ... the layouts the map: land, outline, walls and gates, streets, buildings, fields; the layout of
#                            each type and era (build_town, build_ward, build_motte)
#   the people ... hooks     the settlement on the map: names, history, government, inhabitants, demography,
#                            economy; in a place of adventure the threat, monsters and treasure; rumours and events
#   fonts and glyphs         the symbols of the map and their fallbacks, the ASCII canvas
#   legend and page, paper   legend, building index and title around the map; the best paper and layout
#   rendering and saving     the image at 600 dpi, colours, PNG and PDF maps
#   the key, the PDF file    the key as blocks, then as text and as a PDF file
#   files ... questions      output folders; welcome screen, menus and questions
#   main                     main() and make(): one settlement from settings to key

# --- settings ---

VERSION = "0.2.0"
PROGRAM = "WyrmUrbiGen"
DPI = 600
MARGIN_MM = 10.0
MAX_CHAR_MM = 3.2           # cap on A4; bigger sheets scale it up
GOOD_CHAR_MM = 1.3          # readable
SMALL_CHAR_MM = 1.1         # too small below this
PAPERS = {"A4": (210, 297), "A3": (297, 420), "A2": (420, 594), "A1": (594, 841)}
SETTINGS_KEY = "wyrmurbigen-settings"

# (ink, paper) in RGB, as in WyrmDelve
COLOR_SCHEMES = {
    1: ((0, 0, 0), (255, 255, 255)),          # black symbols on white
    2: ((255, 255, 255), (72, 156, 214)),     # white symbols on light blue
    3: ((255, 255, 255), (0, 0, 0)),          # white symbols on black
}
# Colour maps, as in WyrmHex: 4 on white, 5 on black. Keys are canvas tags (what
# a symbol is) and "bg:" fills (the ground under it); anything without its own
# colour is drawn in "ink". The one-colour schemes above are drawn in grayscale.
MONO = {"mode": "L", "paper": 255, "ink": 0}
PALETTES = {
    4: {"mode": "RGB", "paper": (255, 255, 255), "ink": (25, 25, 25),
        "stone": (70, 72, 82), "wood": (125, 80, 35), "door": (25, 25, 25), "number": (160, 30, 30),
        "rubble": (125, 115, 105), "wall": (100, 96, 92), "tower": (60, 56, 52), "palisade": (125, 85, 40),
        "gate": (190, 35, 35), "entrance": (190, 35, 35), "ditch": (150, 120, 80), "water": (30, 100, 200),
        "bridge": (120, 80, 40), "mound": (130, 85, 25), "street": (130, 130, 130), "road": (150, 110, 60),
        "garden": (60, 150, 60), "grave": (110, 110, 110), "well": (30, 100, 200), "fountain": (30, 100, 200),
        "stall": (180, 125, 25), "plough": (150, 110, 50), "sown": (175, 150, 30), "pasture": (90, 160, 70),
        "orchard": (40, 130, 60), "forest": (25, 125, 45), "tree": (25, 125, 45), "hill": (130, 85, 25), "mount": (105, 90, 80),
        "shroom": (100, 60, 80), "rock": (110, 98, 86), "magma": (205, 70, 20), "moss": (90, 140, 60),
        "bg:rock": (226, 220, 210),
        "reed": (118, 30, 95), "secret": (200, 0, 130),
        # fills, light enough for the symbols on top
        "bg:water": (180, 211, 236), "bg:street": (242, 238, 228), "bg:stone": (222, 222, 226),
        "bg:wood": (242, 226, 196)},
    5: {"mode": "RGB", "paper": (12, 12, 16), "ink": (230, 230, 225),
        "stone": (190, 195, 210), "wood": (215, 160, 95), "door": (230, 230, 225), "number": (255, 120, 100),
        "rubble": (150, 140, 130), "wall": (165, 160, 155), "tower": (215, 210, 205), "palisade": (200, 140, 75),
        "gate": (235, 75, 65), "entrance": (235, 75, 65), "ditch": (170, 140, 95), "water": (80, 150, 255),
        "bridge": (200, 145, 85), "mound": (215, 165, 80), "street": (120, 120, 125), "road": (190, 145, 90),
        "garden": (90, 200, 100), "grave": (160, 160, 165), "well": (80, 150, 255), "fountain": (80, 150, 255),
        "stall": (235, 195, 95), "plough": (205, 160, 85), "sown": (225, 200, 80), "pasture": (120, 200, 100),
        "orchard": (70, 190, 90), "forest": (60, 190, 80), "tree": (60, 190, 80), "hill": (215, 165, 80), "mount": (195, 180, 165),
        "shroom": (176, 140, 168), "rock": (170, 155, 140), "magma": (255, 120, 40), "moss": (120, 190, 90),
        "reed": (195, 105, 165), "secret": (255, 80, 200),
        # only the water is filled, as WyrmHex's sea on black
        "bg:water": (18, 42, 82)},
}

MONO_FONTS = [
    ("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
     "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"),
    (("/System/Library/Fonts/Menlo.ttc", 0), ("/System/Library/Fonts/Menlo.ttc", 1)),   # macOS
    ("C:/Windows/Fonts/consola.ttf", "C:/Windows/Fonts/consolab.ttf"),       # Windows
    ("/usr/share/fonts/truetype/liberation/LiberationMono-Regular.ttf",
     "/usr/share/fonts/truetype/liberation/LiberationMono-Bold.ttf"),
]

# Letters are about twice as tall as wide: shapes are drawn for the eye, so a
# round wall is twice as wide in letters as it is tall. Distances in "visual
# units" count a row as 1 and a column as 1/2.
ASPECT = 2.0

# settlement radius in rows of letters, from the smallest to the biggest population of each type
RADIUS = {"village": (8, 12), "town": (12, 17), "city": (21, 24), "bigcity": (25, 33), "castle": (11, 15),
          "fortress": (13, 18)}
# castles and fortresses: metres in a row of letters (a column is half of it); towns get theirs from the population
WARD_ROW_M = {"castle": 3.0, "fortress": 4.5}
DANGERS = (1, 2, 3, 4)
DANGER_HD = {1: "1-2", 2: "3-4", 3: "5-7", 4: "8+"}
DANGER_LEVEL = {1: 1, 2: 3, 3: 5, 4: 7}      # the dungeon level whose unguarded treasure fits
BUILDING_ALIAS = {"bigcity": "city"}          # a big city has every building a city has


def mm(value):
    """Millimetres to pixels at the print resolution (DPI)."""
    return value / 25.4 * DPI



# --- language ---
# Everything the user reads is (it, en). LANG is set once at startup, from the
# first question or from --lingua/--language.
LANGUAGES = ("it", "en")
LANG = "it"

TEXTS = {
    # console: general
    "done": ("Completato in {s:.1f} s.", "Done in {s:.1f} s."),
    "interrupted": ("\n\nInterrotto.", "\n\nStopped."),
    "invalid_value": ("    Valore non valido, riprova.", "    Invalid value, try again."),
    "value_range": ("    Il valore deve essere tra {lo} e {hi}.", "    The value must be between {lo} and {hi}."),
    "choice": ("Scelta", "Choice"),
    "menu_keys": ("↑ ↓ scegli   ·   Invio conferma   ·   oppure premi il numero",
                  "↑ ↓ move   ·   Enter confirms   ·   or press the number"),
    "menu_keys_multi": ("↑ ↓ scegli   ·   Spazio segna o toglie   ·   Invio conferma",
                        "↑ ↓ move   ·   Space ticks or unticks   ·   Enter confirms"),
    "menu_none": ("nessuno", "none"),
    "type_keys": ("Scrivi   ·   ⌫ cancella   ·   Esc svuota   ·   Invio conferma",
                  "Type   ·   ⌫ deletes   ·   Esc clears   ·   Enter confirms"),
    "at_random": ("A caso", "At random"),
    # welcome
    "welcome_subtitle": ("generatore di villaggi, paesi, città, castelli e fortezze per campagne OSR",
                         "village, town, city, castle and fortress generator for OSR campaigns"),
    "welcome_q": ("Cosa vuoi fare?", "What do you want to do?"),
    "mode_random": ("Un insediamento casuale", "A random settlement"),
    "mode_params": ("Scelgo io: scopo, tipo, popolazione, epoca, terreno", "I'll choose: purpose, type, population, era, terrain"),
    "mode_rebuild": ("Rifaccio un insediamento dal suo seme", "Rebuild a settlement from its seed"),
    "enter_accepts": ("  Il castellano apre le porte... (Invio accetta il valore tra parentesi)\n",
                      "  The castellan opens the gates... (Enter accepts the value in brackets)\n"),
    "ask_seed": ("  Seme dell'insediamento (è anche il nome della sua cartella, es. {example}): ",
                 "  Seed of the settlement (it is also the name of its folder, e.g. {example}): "),
    "seed_invalid": ("    Questo seme non è valido: controlla di averlo scritto bene (es. {example}).",
                     "    This seed is not valid: check that you typed it correctly (e.g. {example})."),
    # questions
    "q_purpose": ("L'insediamento è un luogo di riposo per gli avventurieri o un luogo d'avventura?",
                  "Is the settlement a place of rest for adventurers, or a place of adventure?"),
    "purpose_rest_menu": ("Luogo di riposo", "Place of rest"),
    "purpose_adventure_menu": ("Luogo d'avventura", "Place of adventure"),
    "purpose_rest_hint": ("locande, guaritori, botteghe, mercenari, prezzi, voci e agganci",
                          "inns, healers, shops, mercenaries, prices, rumours and hooks"),
    "purpose_adventure_hint": ("una minaccia, mostri erranti, mostri e tesori negli edifici (da WyrmDelve)",
                               "a threat, wandering monsters, monsters and treasure in the buildings (from WyrmDelve)"),
    "q_type": ("Che tipo di insediamento? (la popolazione segue Medieval Demographics Made Easy)",
               "What kind of settlement? (population as in Medieval Demographics Made Easy)"),
    "q_pop": ("Abitanti ({lo}-{hi})", "Inhabitants ({lo}-{hi})"),
    "q_era": ("Epoca: a quale architettura e urbanistica si ispira?", "Era: which architecture and town planning?"),
    "q_terrain": ("Dove si trova?", "Where does it stand?"),
    "q_names": ("A che lingua somigliano i nomi dei luoghi?", "Which language do the place names sound like?"),
    "q_tone": ("Che tono hanno i nomi?", "What tone do the names have?"),
    "q_people": ("Che nomi hanno le persone?", "What names do the people have?"),
    "people_places": ("come i luoghi (la stessa lingua)", "like the places (the same language)"),
    "people_fantasy": ("fantasy: desinenze mescolate da tutte le lingue", "fantasy: endings mixed from all languages"),
    "people_places_hint": ("nomi e cognomi nella lingua dei nomi dei luoghi", "first and family names in the place names' language"),
    "q_danger": ("Quanto è pericoloso?", "How dangerous is it?"),
    "q_state": ("In che stato è?", "What state is it in?"),
    "state_ruin_menu": ("In rovina", "In ruins"),
    "state_ruin_hint": ("abbandonato da tempo, popolato da mostri, con una storia a strati",
                        "long abandoned, full of monsters, with a layered history"),
    "state_threat_menu": ("Abitato e minacciato", "Inhabited and threatened"),
    "state_threat_hint": ("la gente vive ancora qui: briganti, culti, peste, faide, un drago...",
                          "people still live here: brigands, cults, plague, feuds, a dragon..."),
    "danger_1": ("1 · per personaggi di livello 1-2", "1 · for characters of level 1-2"),
    "danger_2": ("2 · per personaggi di livello 3-4", "2 · for characters of level 3-4"),
    "danger_3": ("3 · per personaggi di livello 5-7", "3 · for characters of level 5-7"),
    "danger_4": ("4 · per personaggi di livello 8 e oltre", "4 · for characters of level 8 and up"),
    "colors_intro": ("Combinazione di colori della mappa:", "Map colour scheme:"),
    "color_name_1": ("nero su bianco (per stampare)", "black on white (for printing)"),
    "color_name_2": ("bianco su celeste", "white on light blue"),
    "color_name_3": ("bianco su nero (per lo schermo)", "white on black (for screens)"),
    "color_name_4": ("a colori su bianco", "colour on white"),
    "color_name_5": ("a colori su nero (per lo schermo)", "colour on black (for screens)"),
    "ascii_intro": ("Simboli della mappa:", "Map symbols:"),
    "again_q": ("Vuoi generare lo stesso insediamento anche con altri colori o stili?",
                "Make the same settlement again in other colours or styles?"),
    "again_no": ("no, ho finito", "no, I'm done"),
    "again_yes": ("sì: scelgo colori, simboli, formato e file", "yes: I'll choose colours, symbols, paper and files"),
    "info_again": ("Stesso seme {s}: le mappe nuove hanno {t} nel nome, quelle di prima restano",
                   "Same seed {s}: the new maps have {t} in their names, the earlier ones stay"),
    "ascii_no": ("simboli come ▓ █ ≈ ♣ ╔═╗ (consigliato)", "symbols such as ▓ █ ≈ ♣ ╔═╗ (suggested)"),
    "ascii_yes": ("solo i caratteri base della tastiera, come WyrmHex (# @ ~ T)", "keyboard characters only, like WyrmHex (# @ ~ T)"),
    "name_intro": ("Nome sulla mappa:", "Name on the map:"),
    "name_random": ("quello dell'insediamento, generato a caso", "the settlement's own, made at random"),
    "name_mine": ("lo scrivo io", "I'll type it"),
    "name_none": ("nessun nome", "no name"),
    "q_name": ("  Nome della mappa: ", "  Map name: "),
    "name_empty": ("    Scrivi un nome.", "    Type a name."),
    "content_intro": ("Cosa vuoi nella chiave e nel PDF?", "What do you want in the key and the PDF?"),
    "content_story": ("storia: storia stratificata, fazioni, economia, voci ed eventi",
                      "story: layered history, factions, economy, rumours and events"),
    "content_people": ("abitanti: un PNG per ogni edificio, con statistiche OSR", "people: an NPC for every building, with OSR stats"),
    "content_monsters": ("mostri: mostri erranti, mostri e indizi negli edifici", "monsters: wandering monsters, monsters and clues in the buildings"),
    "content_treasure": ("tesori: monete, gemme, gioielli e oggetti magici", "treasure: coins, gems, jewellery and magic items"),
    "content_intrigue": ("intrighi: i PNG che contano, con storia, motivazioni e legami; le fazioni e le loro radici",
                         "intrigue: the NPCs who matter, with story, motives and ties; the factions and their roots"),
    "content_help": ("    Scrivi i numeri che vuoi, separati da virgole (es. 1,2); 0 = solo l'elenco degli edifici.",
                     "    Type the numbers you want, separated by commas (e.g. 1,2); 0 = only the list of buildings."),
    "optional_help": ("    Scrivi i numeri che vuoi, separati da virgole (es. 1,2); 0 = nessuno.",
                      "    Type the numbers you want, separated by commas (e.g. 1,2); 0 = none."),
    "units_intro": ("Unità di misura:", "Units:"),
    "units_imperial": ("imperiale (piedi)", "imperial (feet)"),
    "units_metric": ("metrica (metri)", "metric (metres)"),
    "output_intro": ("Che file vuoi?", "Which files do you want?"),
    "output_png": ("mappe in PNG e chiave in un file PDF, separati", "PNG maps and the key in a PDF file, apart"),
    "output_pdf": ("mappe in PDF e chiave in un file PDF, separati", "PDF maps and the key in a PDF file, apart"),
    "output_single": ("un unico file PDF: le due mappe e poi la chiave", "one single PDF file: the two maps, then the key"),
    "paper_choice": ("  Scegli il formato (premi Invio per quello consigliato).",
                     "  Choose the format (press Enter for the suggested one)."),
    "q_paper": ("  Formato di stampa (A4, A3, A2, A1) [{default}]: ", "  Print format (A4, A3, A2, A1) [{default}]: "),
    "paper_q": ("Formato di stampa delle mappe:", "Print format of the maps:"),
    "menu_letters": ("caratteri da {mm:.2f} mm", "{mm:.2f} mm letters"),
    "paper_retry": ("    Scrivi A4, A3, A2 oppure A1.", "    Type A4, A3, A2 or A1."),
    # checks
    "err_pop": ("Un {t} ha da {lo} a {hi} abitanti.", "A {t} has {lo} to {hi} inhabitants."),
    "err_danger": ("Il pericolo va da 1 a 4.", "Danger goes from 1 to 4."),
    "err_danger_rest": ("Un luogo di riposo ha pericolo 0.", "A place of rest has danger 0."),
    "err_seed": ("Seme non valido: {s}", "Invalid seed: {s}"),
    "err_choice": ("«{s}» non è un valore valido per {w}", "“{s}” is not a valid value for {w}"),
    "err_content": ("«{s}» non è una scelta valida: usa mappa, tutto, oppure storia, abitanti, mostri, tesori separati da virgole",
                    "“{s}” is not a valid choice: use map, all, or story, people, monsters, treasure separated by commas"),
    "err_no_font": ("Nessun font monospazio trovato: controlla che la cartella fonts sia accanto a wyrmurbigen.py, "
                    "oppure indica un file .ttf con --font.",
                    "No monospaced font found: check that the fonts folder is next to wyrmurbigen.py, "
                    "or give a .ttf file with --font."),
    "err_size": ("{path}: {size} non è un foglio A4, A3, A2 o A1 a 600 dpi", "{path}: {size} is not an A4, A3, A2 or A1 sheet at 600 dpi"),
    "err_pdf_fonts": ("ERRORE: manca il font {f} nella cartella {d}, quindi il PDF non viene creato (le mappe e la chiave .txt sì).",
                       "ERROR: the font {f} is missing from {d}, so the PDF is not made (the maps and the .txt key are)."),
    "err_no_fpdf": ("ERRORE: manca la libreria fpdf2, quindi il PDF non viene creato. Scrivi: pip install -r requirements.txt",
                    "ERROR: the fpdf2 library is missing, so the PDF is not made. Type: pip install -r requirements.txt"),
    "err_old_fpdf": ("ERRORE: è installata la vecchia libreria «fpdf» {v} al posto di «fpdf2». Scrivi: pip uninstall -y fpdf fpdf2  "
                     "e poi: pip install -r requirements.txt",
                     "ERROR: the old «fpdf» library {v} is installed instead of «fpdf2». Type: pip uninstall -y fpdf fpdf2  "
                     "and then: pip install -r requirements.txt"),
    "err_pdf": ("ERRORE: il PDF non è stato creato: {e}", "ERROR: the PDF was not made: {e}"),
    "warn_no_monsters": ("Manca data/monsters.json (o è rovinato): niente mostri", "data/monsters.json is missing (or broken): no monsters"),
    "warn_no_treasure": ("Manca data/treasure.json (o è rovinato): niente tesori", "data/treasure.json is missing (or broken): no treasure"),
    "warn_tiny": ("Caratteri molto piccoli: scegli un formato più grande se puoi.", "Very small letters: choose a bigger format if you can."),
    "warn_missing_glyphs": ("Il font non ha questi glifi, sostituiti con ASCII: {g}", "The font lacks these symbols, replaced with ASCII: {g}"),
    # steps
    "step_settings": ("Impostazioni", "Settings"),
    "info_seed": ("Seme: {s}", "Seed: {s}"),
    "info_names": ("Nomi: {s}, tono {t} (circa {m} di combinazioni)", "Names: {s}, {t} tone (about {m} combinations)"),
    "millions": ("{n} milioni", "{n} million"),
    "billions": ("{n} miliardi", "{n} billion"),
    "info_names_old": ("Nomi: italiano medievale, come nei semi di vecchio tipo", "Names: medieval Italian, as in older seeds"),
    "info_people": ("Persone: {w} (circa {m} nomi maschili, {f} femminili e {c} cognomi)",
                    "People: {w} (about {m} male and {f} female first names, {c} family names)"),
    "people_w_places": ("come i luoghi, {s}", "like the places, {s}"),
    "people_w_fantasy": ("fantasy, desinenze mescolate", "fantasy, mixed endings"),
    "info_what": ("{t} di {n} abitanti, {e}, {g}", "{t} of {n} people, {e}, {g}"),
    "info_folder": ("Cartella: {folder}", "Folder: {folder}"),
    "step_map": ("Mappa: terreno, mura, porte, strade, edifici", "Map: land, walls, gates, streets, buildings"),
    "info_map": ("{w} x {h} caratteri, {b} edifici numerati, {g} porte", "{w} x {h} letters, {b} numbered buildings, {g} gates"),
    "info_missing": ("{n} edifici previsti dalla popolazione non hanno trovato posto: restano nella demografia",
                     "{n} buildings the population calls for found no room: they stay in the demographics"),
    "step_people": ("Storia, governo, abitanti", "History, government, inhabitants"),
    "info_threat": ("Minaccia: {t} (covo: n. {n})", "Threat: {t} (lair: no. {n})"),
    "step_paper": ("Formato di stampa", "Print format"),
    "info_paper_intro": ("La mappa occupa {nc} x {nr} caratteri. Formati possibili:", "The map takes {nc} x {nr} letters. Possible formats:"),
    "info_paper_option": ("{paper}  {o:<11}  caratteri da {mm:.2f} mm   {v}{note}", "{paper}  {o:<9}  {mm:.2f} mm letters   {v}{note}"),
    "v_good": ("leggibile", "readable"),
    "v_small": ("piccolo", "small"),
    "v_too_small": ("troppo piccolo", "too small"),
    "suggested": ("   <- consigliato", "   <- suggested"),
    "orientation_portrait": ("verticale", "portrait"),
    "orientation_landscape": ("orizzontale", "landscape"),
    "info_sheet": ("Foglio {paper} {o} ({w} x {h} px a {dpi} dpi), caratteri da {mm:.2f} mm",
                   "{paper} sheet, {o} ({w} x {h} px at {dpi} dpi), {mm:.2f} mm letters"),
    "step_maps": ("Mappe dell'arbitro e dei giocatori ({paper}, {dpi} dpi)", "Referee's and players' maps ({paper}, {dpi} dpi)"),
    "step_key": ("Chiave e file PDF", "Key and PDF file"),
    "saved": ("Salvate: {a}  +  {b}", "Saved: {a}  +  {b}"),
    "saved_txt": ("Salvata: {a}", "Saved: {a}"),
    "saved_key": ("Chiave: {a}", "Key: {a}"),
    "saved_pdf": ("File PDF: {a}", "PDF file: {a}"),
    "saved_pdf_maps": ("File PDF unico (mappe e chiave): {a}", "Single PDF file (maps and key): {a}"),
    "pb_drawing": ("disegno", "drawing"),
    "pb_saving": ("salvataggio", "saving"),
    "pb_done": ("fatto", "done"),
    # map page
    "subtitle": ("Seme {seed} · {t} di {n} abitanti · {e} · {b} edifici", "Seed {seed} · {t} of {n} people · {e} · {b} buildings"),
    "players_title": ("{t} — mappa dei giocatori", "{t} — players' map"),
    "players_title_plain": ("Mappa dei giocatori", "Players' map"),
    "lg_stone": ("edificio in pietra", "stone building"),
    "lg_wood": ("in legno o graticcio", "timber or half-timbered"),
    "lg_door": ("porta", "door"),
    "lg_number": ("numero dell'edificio", "building number"),
    "lg_buildings": ("Edifici", "Buildings"),
    "bolpo": ("Bolpo ama Pisa", "Bolpo loves Pisa"),
    "bolpo_again": ("Bolpo ama ancora Pisa", "Bolpo still loves Pisa"),
    "info_index_side": ("Elenco degli edifici accanto alla mappa: così i caratteri sono più grandi",
                        "Building list beside the map: the letters come out bigger"),
    "info_index_under": ("Elenco degli edifici sotto la mappa: così i caratteri sono più grandi",
                         "Building list under the map: the letters come out bigger"),
    "ix_lair": ("covo: {d}", "lair: {d}"),
    "ix_tunnel": ("qui comincia la galleria segreta", "the secret tunnel starts here"),
    "ix_secrets": ("Segreti:", "Secrets:"),
    "lg_ruin": ("macerie", "rubble"),
    "lg_brambles": ("rovi ed erbacce", "brambles and weeds"),
    "lg_wall": ("mura", "walls"),
    "lg_tower": ("torre o bastione", "tower or bastion"),
    "lg_palisade": ("palizzata", "palisade"),
    "lg_gate": ("porta della città", "town gate"),
    "lg_gate_tag": ("ingresso", "entrance"),
    "lg_ditch": ("fossato asciutto", "dry ditch"),
    "lg_water": ("acqua", "water"),
    "lg_bridge": ("ponte o molo", "bridge or pier"),
    "lg_mound": ("terrapieno", "earth mound"),
    "lg_street": ("strada, piazza, cortile", "street, square, yard"),
    "lg_road": ("strada di campagna", "country road"),
    "lg_garden": ("orti e cortili", "gardens and yards"),
    "lg_grave": ("cimitero", "graveyard"),
    "lg_well": ("pozzo", "well"),
    "lg_fountain": ("fontana", "fountain"),
    "lg_stall": ("banco del mercato", "market stall"),
    "lg_plough": ("campo arato", "ploughed field"),
    "lg_sown": ("campo seminato", "sown field"),
    "lg_pasture": ("prato e pascolo", "meadow and pasture"),
    "lg_orchard": ("frutteto o oliveto", "orchard or olive grove"),
    "lg_forest": ("bosco", "woods"),
    "lg_shroom": ("funghi giganti", "giant mushrooms"),
    "lg_grown": ("cresciuto in un fungo, o in legno", "grown in a mushroom, or timber"),
    "q_optional": ("Vuoi aggiungere terreni speciali? (nessuno: i terreni di sempre)",
                   "Do you want to add special terrains? (none: the usual terrains)"),
    "opt_fungus": ("Foreste di funghi giganti: ispirate a Morrowind",
                   "Giant mushroom forests: inspired by Morrowind"),
    "opt_underground": ("Sottosuolo: città sotterranee di nani e altri popoli, ispirate a Dwarf Fortress",
                        "Underground: cities below, of dwarves and other folk, inspired by Dwarf Fortress"),
    "q_folk": ("Chi ci vive?", "Who lives there?"),
    "h_underground": ("aggiunge il sottosuolo (città sotterranee) ai terreni che il caso può scegliere",
                      "adds the underground (cities below) to the terrains chance may pick"),
    "h_folk": ("chi vive nel sottosuolo: nani, coboldi, goblin, gnomi, trogloditi, elfi, talpa, funghi, serpente, "
               "automi, pallidi", "who lives below: dwarves, kobolds, goblins, gnomes, troglodytes, elves, mole, fungus, "
               "serpent, automata, pale"),
    "lg_rock": ("parete di roccia", "rock face"),
    "lg_magma": ("magma", "magma"),
    "lg_moss": ("muschio delle caverne", "cave moss"),
    "lg_carved": ("scavato nella roccia", "carved into the rock"),
    "carved": ("roccia", "rock-cut"),
    "key_folk": ("Chi ci vive: {f}.", "Who lives here: {f}."),
    "h_fungus": ("aggiunge le foreste di funghi giganti ai terreni che il caso può scegliere",
                 "adds giant mushroom forests to the terrains chance may pick"),
    "grown": ("fungo", "mushroom"),
    "lg_hill": ("colline", "hills"),
    "lg_mount": ("montagne", "mountains"),
    "lg_cliff": ("dirupi", "cliffs"),
    "perched": ("Arroccato su uno sperone: dirupi tutt'intorno, tranne verso {d}, da dove si sale con strade a "
                "tornanti; dentro, le vie più ripide sono gradinate e la cima è del castello o del tempio.",
                "Perched on a spur: cliffs all round but to the {d}, where roads climb in hairpin bends; inside, the "
                "steepest lanes are flights of steps and the top belongs to the castle or the temple."),
    "lg_stairs": ("gradinata", "steps"),
    "lg_reed": ("canneto", "reeds"),
    "lg_secret": ("postierla segreta (solo arbitro)", "secret postern (referee only)"),
    "lg_tunnel": ("galleria segreta (solo arbitro)", "secret tunnel (referee only)"),
    "lg_scale": ("Scala:", "Scale:"),
    "lg_row": (" (una riga = {r} {u})", " (one row = {r} {u})"),
    # key
    "key_seed": ("Seme", "Seed"),
    "key_pop": ("{n} abitanti", "{n} inhabitants"),
    "key_names": ("Nomi: {s}, tono {t}", "Names: {s}, {t} tone"),
    "key_people": ("Persone: {w}", "People: {w}"),
    "key_scale": ("Scala: una riga di caratteri = {r} {u}, una colonna = metà", "Scale: one row of letters = {r} {u}, one column = half"),
    "purpose_rest": ("Luogo di riposo per gli avventurieri", "Place of rest for adventurers"),
    "purpose_adventure": ("Luogo d'avventura, pericolo {d}", "Place of adventure, danger {d}"),
    "state_ruin": ("in rovina", "in ruins"),
    "state_threat": ("abitato e minacciato", "inhabited and threatened"),
    "key_pop_ruin": ("{n} abitanti all'apogeo, oggi nessuno", "{n} inhabitants at its height, none today"),
    "gods": ("Vi si venerano {g}.", "Its people worship {g}."),
    "gods_ruin": ("Vi si veneravano {g}.", "Its people worshipped {g}."),
    "events_ruin": ("Eventi tra le rovine (d6)", "Events in the ruins (d6)"),
    "hooks_ruin": ("Agganci: chi manda i personaggi (d4)", "Hooks: who sends the characters (d4)"),
    "trace": ("Traccia del passato: {t}.", "A trace of the past: {t}."),
    "h_history": ("Storia", "History"),
    "h_threat": ("La minaccia: {t}", "The threat: {t}"),
    "threat_villain": ("Chi c'è dietro: {v}", "Who is behind it: {v}"),
    "threat_boss": ("Chi comanda: {b} Usa le statistiche del mostro più forte dei mostri erranti, con il doppio dei "
                    "PF.", "Who rules here: {b} Use the stats of the strongest wandering monster, with double hp."),
    "clock_title": ("Se nessuno interviene (un passo ogni 1d4 giorni)", "If nobody steps in (one step every 1d4 days)"),
    "key_wander": ("Mostri erranti (d6, ogni 2 turni di notte, ogni ora di giorno: 1 su d6)",
                   "Wandering monsters (d6; every 2 turns at night, every hour by day: 1 in 6)"),
    "wander_dwellers": ("la minaccia in persona, in giro per le strade", "the threat itself, roaming the streets"),
    "danger_tag": ("pericolo {d}, DV ~{hd}", "danger {d}, HD ~{hd}"),
    "h_government": ("Governo e fazioni", "Government and factions"),
    "lives_in": ("risiede al n. {n}", "lives at no. {n}"),
    "faction": ("{n}. Scopo: {g}. Guida: {l}.", "{n}. Goal: {g}. Led by {l}."),
    "h_lore": ("Voci ed eventi", "Rumours and events"),
    "faction_rival": (" Rivale: {r}.", " Rival: {r}."),
    "npc_line": ("{h} ({s}): {t}; vuole {w}; segreto: {x}.", "{h} ({s}): {t}; wants {w}; secret: {x}."),
    "household": (" In casa vivono {n} persone.", " {n} people live here."),
    "block_line": ("{p} abitanti in {d} case e botteghe: soprattutto {t}.", "{p} people in {d} houses and shops: mostly {t}."),
    "block_head": ("La persona più in vista: ", "The best-known person: "),
    "secret_use": ("Segreto: in realtà è il {x}.", "Secret: it is really the {x}."),
    "seat_of": ("Qui risiede {r}.", "{r} resides here."),
    "services": ("Servizi: ", "Services: "),
    "tunnel_here": ("Da qui parte la galleria segreta che esce oltre le mura (░ sulla mappa dell'arbitro).",
                    "The secret tunnel leaving past the walls starts here (░ on the referee's map)."),
    "abandoned": ("Abbandonato: porte sfondate, nessuno ci vive più.", "Abandoned: doors broken in, nobody lives here any more."),
    "ruined": ("In rovina: tetto crollato, macerie (∴ sulla mappa).", "In ruins: the roof has fallen in, rubble (∴ on the map)."),
    "room_monsters": ("Mostri: {m}.", "Monsters: {m}."),
    "room_lair": ("Covo: {m}.", "Lair: {m}."),
    "room_clue": ("Indizio: {c} (dal n. {r}).", "Clue: {c} (from no. {r})."),
    "room_treasure": ("Tesoro{v}: {x}; {w}.", "Treasure{v}: {x}; {w}."),
    "treasure_value": (" ({v} mo)", " ({v} gp)"),
    "treasure_gems": ("{n} gemme", "{n} gems"),
    "treasure_gems_one": ("1 gemma", "1 gem"),
    "treasure_jewellery": ("{n} gioielli", "{n} pieces of jewellery"),
    "treasure_jewellery_one": ("1 gioiello", "1 piece of jewellery"),
    "h_demography": ("Demografia", "Demographics"),
    "demo_main": ("{p} abitanti su {a} ettari ({d} per ettaro), in circa {w} abitazioni; sulla mappa {b} edifici numerati: "
                  "nei luoghi grandi ogni riquadro è un gruppo di case o un isolato.",
                  "{p} people on {a} hectares ({d} per hectare), in about {w} dwellings; on the map {b} numbered buildings: "
                  "in big places every box is a group of houses or a block."),
    "demo_people": ("Famiglie nobili: {n}. Avvocati e notai: {l}. Religiosi: {c}, di cui sacerdoti: {pr}; luoghi di culto: {w}. "
                    "Guardie e birri: {g}{slack}. Animali: {li}, per due terzi pollame.",
                    "Noble households: {n}. Lawyers: {l}. Clergy: {c}, of whom priests: {pr}; places of worship: {w}. "
                    "Guards and watchmen: {g}{slack}. Livestock: {li}, two thirds of it fowl."),
    "slack": (" (poche: la città è trascurata)", " (few: a slack town)"),
    "demo_shops": ("Botteghe e mestieri: ", "Shops and trades: "),
    "demo_maybe": ("Forse (probabilità che ce ne sia uno): ", "Maybe (chance there is one): "),
    "demo_note": ("Le botteghe sono tutte in città; sulla mappa ci sono le {n} più importanti.",
                  "Every shop is in town; the map shows the {n} most important ones."),
    "demo_ward": ("Guarnigione: {g}. Famiglia del signore, servi e artigiani: {s}. Cavalli: {h}. Altri animali: {l}.",
                  "Garrison: {g}. The lord's family, servants and craftsmen: {s}. Horses: {h}. Other livestock: {l}."),
    "h_economy": ("Contado ed economia", "Countryside and economy"),
    "eco_region": ("Il contado è {r}: nell'esagono di 6 miglia attorno vivono circa {n} contadini, in {v} villaggi.",
                   "The country around is {r}: about {n} peasants live in the surrounding 6-mile hex, in {v} villages."),
    "eco_revenue": ("Rendita netta del signore: {m} mo al mese ({y} mo all'anno){t}.",
                    "The lord's net revenue: {m} gp a month ({y} gp a year){t}."),
    "eco_troubled": (", già divisa per {d} per i tempi difficili", ", already divided by {d} for the troubled times"),
    "eco_offers": ("Proprietà in vendita", "Property for sale"),
    "eco_cost": (" ({c} mo)", " ({c} gp)"),
    "eco_people": ("Con {n} {w}.", "With {n} {w}."),
    "eco_seller": ("Vende: {s}.", "Seller: {s}."),
    "eco_rules": ("La terra di rado si vende, più spesso si eredita, si dona o si conquista. In tempi di peste, guerra o "
                  "carestia ogni rendita si dimezza; in tempi di vero caos si divide per 10. Chi imbroglia sulle tasse tiene "
                  "un altro {c}% della rendita, finché un signore attento non controlla i conti.",
                  "Land is rarely sold, it is more often inherited, given or seized. In times of plague, war or famine "
                  "every income is halved; in truly chaotic times it is divided by 10. Whoever cheats on taxes keeps "
                  "another {c}% of the income, until a careful lord audits the books."),
    "h_services": ("Servizi per gli avventurieri", "Services for adventurers"),
    "mercenaries": ("Mercenari e seguaci (paga al mese)", "Mercenaries and followers (monthly wage)"),
    "merc_row": ("{n} {name}, {w} mo al mese ({s})", "{n} {name}, {w} gp a month ({s})"),
    "hirelings": ("Avventurieri da assoldare", "Adventurers for hire"),
    "hireling_pay": (" Chiede 25 mo al mese e mezza parte del bottino.", " Asks 25 gp a month and half a share of the loot."),
    "hooks": ("Lavori e agganci (d4)", "Jobs and hooks (d4)"),
    "rumours": ("Voci (d10; V vera, F falsa, ½ in parte vera: solo per l'arbitro)",
                "Rumours (d10; T true, F false, ½ partly true: referee only)"),
    "true": ("V", "T"),
    "false": ("F", "F"),
    "partial": ("½: {x}", "½: {x}"),
    "named_after": ("Il nome ricorda {x} ({w}).", "Named after {x} ({w})."),
    "named_trait": ("Il nome viene da {x}.", "The name comes from {x}."),
    "h_notables": ("Chi conta", "Who matters"),
    "h_notables_ruin": ("Chi conta intorno alle rovine", "Who matters around the ruins"),
    "h_factions": ("Le fazioni", "The factions"),
    "h_factions_ruin": ("Le fazioni intorno alle rovine", "The factions around the ruins"),
    "nb_story": ("Storia: {x}", "Story: {x}"),
    "nb_want": ("Vuole {x}.", "Wants {x}."),
    "nb_secret": ("Segreto: {x}.", "Secret: {x}."),
    "nb_bonds": ("Legami: {x}.", "Ties: {x}."),
    "nb_hook": ("Ai personaggi: {x}.", "For the characters: {x}."),
    "nb_leads": ("Guida {f}.", "Leads {f}."),
    "fa_about": ("Chi sono: {x}; {p}.", "Who they are: {x}; {p}."),
    "fa_goal": ("Vogliono {x}.", "They want {x}."),
    "fa_root": ("Tutto nasce da {s} ({w}).", "It all goes back to {s} ({w})."),
    "fa_how": ("Come: {x}; {y}.", "How: {x}; {y}."),
    "fa_hq": ("Sede: {x}.", "Base: {x}."),
    "fa_camp": ("Accampati: {x}.", "Camped in: {x}."),
    "fa_leader": ("Guida: {x}.", "Led by {x}."),
    "fa_rival": ("Rivali: {x}, {r}.", "Rivals: {x}, {r}."),
    "fa_ally": ("Alleati: {x}, {r}.", "Allies: {x}, {r}."),
    "events": ("Eventi durante il soggiorno (d6)", "Events during the stay (d6)"),
    "h_walls": ("Mura, porte e segreti", "Walls, gates and secrets"),
    "walls_stone": ("Mura di pietra", "Stone walls"),
    "walls_palisade": ("Palizzata di tronchi", "A log palisade"),
    "walls_none": ("Nessuna cinta: si entra da ogni strada.", "No walls: every road leads in."),
    "moat_water": (", con un fossato pieno d'acqua.", ", with a water-filled moat."),
    "moat_dry": (", con un fossato asciutto.", ", with a dry ditch."),
    "postern": ("Postierle segrete nelle mura: {n} ($ sulla mappa dell'arbitro).", "Secret posterns in the walls: {n} ($ on the referee's map)."),
    "tunnel": ("Galleria segreta dal n. {n} ({t}) fino a oltre le mura (░ sulla mappa dell'arbitro).",
               "Secret tunnel from no. {n} ({t}) to beyond the walls (░ on the referee's map)."),
    "harbour": ("Un molo (=) per le barche: si arriva e si parte anche dall'acqua.", "A pier (=) for boats: you can come and go by water too."),
    "h_buildings": ("Gli edifici", "The buildings"),
    "outside_walls": ("Fuori le mura", "Outside the walls"),
    "outskirts": ("Nei dintorni", "Around"),
    "stone": ("pietra", "stone"),
    "wood": ("legno", "timber"),
    "ref_no": ("n.", "no."),
    # help
    "h_description": ("WyrmUrbiGen: genera villaggi, paesi, città, castelli e fortezze per giochi OSR, in ASCII come un "
                      "roguelike, con abitanti, mostri e tesori. Mappe PNG o PDF a 600 dpi + TXT, chiave in TXT e in un file PDF.",
                      "WyrmUrbiGen: makes villages, towns, cities, castles and fortresses for OSR games, in ASCII like a "
                      "roguelike, with inhabitants, monsters and treasure. 600 dpi PNG or PDF maps + TXT, key as TXT and as a PDF file."),
    "h_epilog": ("Senza opzioni parte la modalità interattiva. I parametri non indicati sono scelti a caso.",
                 "Without options the interactive mode starts. Parameters you leave out are chosen at random."),
    "h_language": ("lingua dei testi: it o en", "language of the texts: it or en"),
    "h_type": ("villaggio, paese, citta, grande, castello, fortezza (o 1-6)", "village, town, city, bigcity, castle, fortress (or 1-6)"),
    "h_pop": ("numero di abitanti (sceglie anche il tipo, se manca)", "number of inhabitants (also picks the type, if missing)"),
    "h_era": ("alto (medioevo), basso (medioevo), rinascimento (o 1-3)", "early, late, renaissance (or 1-3)"),
    "h_terrain": ("pianura, collina, montagna, foresta, palude, costa, fiume, lago, funghi, sottosuolo (o 1-10)",
                  "plains, hills, mountains, forest, swamp, coast, river, lake, mushrooms, underground (or 1-10)"),
    "h_purpose": ("riposo o avventura", "rest or adventure"),
    "h_danger": ("pericolo del luogo d'avventura, da 1 a 4", "danger of the place of adventure, 1 to 4"),
    "h_state": ("stato del luogo d'avventura: rovina (in rovina, mostri e storia a strati) o abitato (abitato e "
                "minacciato)", "state of the place of adventure: ruin (in ruins, monsters and a layered history) or "
                "inhabited (inhabited and threatened)"),
    "h_names": ("lingua dei nomi dei luoghi: italiano, antico (Old English), rinascimentale, gaelico, tolkien, "
                "persiano, bizantino, tedesco, francese, danese, russo, misto (o 1-12)",
                "language of the place names: italian, old english, renaissance, gaelic, tolkien, persian, byzantine, "
                "german, french, danish, russian, mixed (or 1-12)"),
    "h_tone": ("tono dei nomi: luminoso, rustico, solenne, cupo, arcano (o 1-5)",
               "tone of the names: fair, homely, stately, grim, eerie (or 1-5)"),
    "h_people": ("nomi delle persone: luoghi (come i nomi dei luoghi), fantasy (desinenze mescolate da tutte le lingue) "
                 "oppure una lingua: italiano, antico, rinascimentale, gaelico, tolkien, persiano, bizantino, tedesco, "
                 "francese, danese, russo, misto",
                 "people's names: places (like the place names), fantasy (endings mixed from all languages) or a "
                 "language: italian, old english, renaissance, gaelic, tolkien, persian, byzantine, german, french, "
                 "danish, russian, mixed"),
    "h_seed": ("seme completo (es. C9500-B-R-A2R-DE4-K7Q2MB) per rifare un insediamento",
               "full seed (e.g. C9500-B-R-A2R-DE4-K7Q2MB) to rebuild a settlement"),
    "h_colors": ("1 nero su bianco (default), 2 bianco su celeste, 3 bianco su nero, 4 a colori su bianco, 5 a colori su nero",
                 "1 black on white (default), 2 white on light blue, 3 white on black, 4 colour on white, 5 colour on black"),
    "h_format": ("formato di stampa; senza, viene suggerito e chiesto", "print format; without it, it is suggested and asked"),
    "h_png": ("mappe in PNG e chiave in un file PDF a parte (di base)", "PNG maps and the key in a separate PDF file (the default)"),
    "h_pdf": ("mappe in PDF e chiave in un file PDF a parte", "PDF maps and the key in a separate PDF file"),
    "h_single": ("un unico file PDF con le mappe e la chiave", "one single PDF file with the maps and the key"),
    "h_title": ("titolo della mappa (default: il nome dell'insediamento)", "map title (default: the settlement's name)"),
    "h_no_title": ("mappa senza nome", "map without a name"),
    "h_content": ("cosa mettere nella chiave: storia, abitanti, mostri, tesori, intrighi, anche insieme separati da virgole; "
                  "mappa = solo l'elenco degli edifici; tutto = tutto (di base)",
                  "what to put in the key: story, people, monsters, treasure, intrigue, also together separated by commas; "
                  "map = only the list of buildings; all = everything (the default)"),
    "h_units": ("unità: imperiale o metrica (di base metrica in italiano, imperiale in inglese)",
                "units: imperial or metric (by default imperial in English, metric in Italian)"),
    "h_ascii": ("solo caratteri base della tastiera, come WyrmHex", "only basic keyboard characters, like WyrmHex"),
    "h_font": ("file .ttf monospazio da usare", "monospaced .ttf font file to use"),
    "h_output": ("cartella in cui salvare (default: settlements_generated accanto allo script)",
                 "folder to save into (default: settlements_generated next to the script)"),
}



def tr(key, **values):
    """The text `key` in the current language, filled in with `values`."""
    text = TEXTS[key][LANGUAGES.index(LANG)]
    return text.format(**values) if values else text


def pick(pair):
    """The current language's half of an (it, en) pair."""
    return pair[LANGUAGES.index(LANG)]


def fmt(pair, **values):
    """Fill in both halves of an (it, en) pair: tuple values give each language its own word; the Italian half gets
    its prepositions and articles right around the names (contract_it)."""
    out = tuple(t.format(**{k: (v[i] if isinstance(v, tuple) else v) for k, v in values.items()})
                for i, t in enumerate(pair))
    return (contract_it(out[0]),) + out[1:]


def sentence(text):
    """The text as a sentence: a capital letter first, a full stop at the end (unless it has one)."""
    text = capitalized(text.strip())
    return text if text[-1:] in ".!?»\"" else text + "."


def capitalized(text):
    """The text with its first letter in upper case (the rest untouched, unlike str.capitalize)."""
    return text[:1].upper() + text[1:] if text else text


ARTICLES = {"la": "lla", "le": "lle", "il": "l", "lo": "llo", "i": "i", "gli": "gli", "l'": "ll'"}
PREPOSITIONS = {"da": "da", "di": "de", "a": "a", "in": "ne", "su": "su"}


def contract_it(text):
    """Italian grammar around a filled-in name: a preposition glued to the article after it ("da la Torre" ->
    "dalla Torre"), "ad" before an a ("a Arnaldo" -> "ad Arnaldo"), and "gli" before s + consonant, z, x, gn, ps
    or a vowel ("dei Schneider" -> "degli Schneider", "i Ursini" -> "gli Ursini")."""
    def glue(m):
        """One preposition and article, glued, keeping a capital letter."""
        word = PREPOSITIONS[m.group(1).lower()] + ARTICLES[m.group(2)]
        return (capitalized(word) if m.group(1)[0].isupper() else word) + m.group(3)
    text = re.sub(r"\b(da|di|a|in|su|Da|Di|A|In|Su) (la|le|il|lo|gli|i|l')( |(?<=')|$)", glue, text)
    text = re.sub(r"\b(A|a) (?=[Aa])", r"\1d ", text)
    return re.sub(r"\b(de|ne|a|da|su|De|Ne|A|Da|Su|)i (?=[Ss][^aeiouyAEIOUY ]|[ZzXx]|Gn|Ps|[AEIOUaeiouÆØÅ])", r"\1gli ",
                  text)


def normalize_language(value):
    """Map "1", "it", "italiano"... to "it" (same for "en"). None if unknown."""
    value = (value or "").strip().lower()
    if value in ("1", "it", "ita", "italiano", "italian"):
        return "it"
    if value in ("2", "en", "eng", "english", "inglese"):
        return "en"
    return None


def language_from_options(argv):
    """Peek at --lingua/--language before argparse runs, so that --help is in the right language too."""
    global LANG
    for i, arg in enumerate(argv):
        for name in ("--lingua", "--language"):
            if arg == name and i + 1 < len(argv):
                LANG = normalize_language(argv[i + 1]) or LANG
            elif arg.startswith(name + "="):
                LANG = normalize_language(arg.split("=", 1)[1]) or LANG


def number(n):
    """An integer with thousands separators: 1.234 in Italian, 1,234 in English."""
    text = f"{n:,}"
    return text.replace(",", ".") if LANG == "it" else text


# --- console output ---
def bar(fraction, cells):
    """A text progress bar of `cells` cells for a fraction from 0 to 1: [███░░░]."""
    full = round(max(0.0, min(1.0, fraction)) * cells)
    return "[" + "█" * full + "░" * (cells - full) + "]"


class LiveBar:
    """Progress bar that keeps redrawing the same line. Silent when stdout isn't a tty."""

    def __init__(self):
        """A bar that redraws itself on one line, only on a real terminal."""
        self.live = sys.stdout.isatty()
        self.shown = None

    def update(self, fraction, label):
        """Show `fraction` done with a `label`; redraw only when something changed."""
        percent = int(fraction * 100)
        if self.live and (percent, label) != self.shown:
            self.shown = (percent, label)
            line = f"        {bar(fraction, 30)} {percent:>3}%  {label:<14}"
            if SCREEN["open"] is not None:
                SCREEN["live"] = line
                draw_console()
            else:
                print("\r" + line, end="", flush=True)

    def finish(self):
        """Fill the bar and end its line."""
        if self.live:
            SCREEN["live"] = None
            if SCREEN["open"] is not None:
                console(f"        {bar(1, 30)} 100%  {tr('pb_done'):<14}")
            else:
                print(f"\r        {bar(1, 30)} 100%  {tr('pb_done'):<14}")


class Log:

    """The console log of a run: numbered steps with a bar, then info, warnings and errors under each."""
    def __init__(self, total_steps):
        """A log of `total_steps` steps; the clock starts now."""
        self.total_steps, self.step_number, self.start_time = total_steps, 0, time.perf_counter()

    def step(self, message):
        """Start the next step: its bar, its number and what it does."""
        self.step_number += 1
        progress = bar(self.step_number / self.total_steps, self.total_steps)
        console(f"\n{progress} {self.step_number:>2}/{self.total_steps}  {message}")

    def info(self, message):
        """A line of information under the current step."""
        console(f"        · {message}")

    def warn(self, message):
        """A warning: something is missing or poor, but the run goes on."""
        console(f"        ! {message}")

    def error(self, message):
        """An error: a part (such as the PDF file) could not be made."""
        console(f"        ✗ {message}")

    def done(self):
        """The last line: how long the whole run took."""
        console("\n" + tr("done", s=time.perf_counter() - self.start_time))


# --- tables ---
# The words the settlements are made of live in the JSON files of the data
# folder, next to this file. Every text there is {"it": ..., "en": ...}; here
# it becomes (it, en).
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OPTIONAL_DATA = ("monsters.json", "clues.json", "treasure.json")    # from WyrmDelve: without them, no monsters or treasure
REQUIRED = ("settlement_types", "eras", "terrains", "name_styles", "name_tones", "name_forms", "god_roots",
            "god_domains", "god_titles", "signs", "gates", "quarters", "history", "situations",
            "events", "hooks", "dungeons", "ruin_history", "ruin_events", "ruin_hooks", "buildings", "bynames",
            "trades", "traits", "wants", "secrets", "rulers", "guilds", "classes", "spells", "retainers",
            "demographics", "economy", "ages", "strata_events", "npc_hooks", "legacies", "kin", "relic_things", "relic_qualities", "ruin_layers",
            "trades_pl", "origins", "rises", "bonds", "bond_reasons", "faction_kinds", "emblem_nouns",
            "emblem_colours", "faction_assets", "faction_powers", "faction_rivalry", "faction_alliance",
            "rumor_sources", "rumor_verbs", "rumor_contents", "rumor_twists", "rumor_kits", "noble_houses",
            "founding_marks", "height_marks", "place_traits")


def from_json(value):
    """JSON as read from data/: every {"it": ..., "en": ...} becomes an (it, en) pair, at any depth."""
    if isinstance(value, dict) and set(value) == {"it", "en"}:
        return value["it"], value["en"]
    if isinstance(value, dict):
        return {k: from_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [from_json(v) for v in value]
    return value


def read_json(path):
    """Read one data file; leave with a bilingual message if it is missing or broken."""
    name = os.path.relpath(path, HERE)
    try:
        with open(path, encoding="utf-8") as f:
            return from_json(json.load(f))
    except OSError:
        sys.exit(f"Non riesco a leggere {name} / Cannot read {name}")
    except ValueError as e:
        sys.exit(f"C'è un errore nel file {name} / There is a mistake in {name}:\n  {e}")


def load_tables(folder=DATA):
    """All the required tables of the data folder merged into one dict (the optional WyrmDelve files are read
    apart); leave if the folder or a table is missing."""
    if not os.path.isdir(folder):
        sys.exit("Manca la cartella data: mettila nella stessa cartella di wyrmurbigen.py.\n"
                 "The data folder is missing: put it in the same folder as wyrmurbigen.py.")
    tables = {}
    for name in sorted(os.listdir(folder)):
        if name.endswith(".json") and name not in OPTIONAL_DATA:
            new = read_json(os.path.join(folder, name))
            twice = sorted(set(new) & set(tables))
            if twice:
                sys.exit(f"Tabelle ripetute in / Tables repeated in {name}: {', '.join(twice)}")
            tables.update(new)
    missing = [k for k in REQUIRED if k not in tables]
    if missing:
        sys.exit(f"Nella cartella data mancano / The data folder lacks: {', '.join(missing)}")
    return tables


def load_optional(path, keys=()):
    """An optional table file: {} when it is missing, broken or lacks one of `keys`."""
    try:
        with open(path, encoding="utf-8") as f:
            tables = from_json(json.load(f))
    except (OSError, ValueError):
        return {}
    return tables if isinstance(tables, dict) and all(k in tables for k in keys) else {}


def add_underground(tables):
    """data/underground.json: the underground settlements. Its terrain (optional, like the giant mushroom forests)
    goes among the terrains with its folk and caverns; "extend" adds entries to the other tables in their own
    formats, "allow" opens existing ones to the underground and "deny" keeps some out of it. Without the file,
    there is no underground terrain."""
    u = tables.get("underground")
    if not u:
        return
    tables["terrains"] = tables["terrains"] + [dict(u["terrain"], folks=u["folks"], caverns=u["caverns"])]
    tables["economy"]["terrain_region"]["underground"] = u["region"]
    for key, items in u["extend"].items():
        tables[key] = tables[key] + items
    for key, names in u["allow"].items():       # by id, or by a trade's masculine Italian name
        for item in tables[key]:
            if item.get("terrains") and (item.get("id") or item.get("m", ("",))[0]) in names:
                item["terrains"] = list(item["terrains"]) + ["underground"]
    for key, names in u["deny"].items():
        for item in tables[key]:
            if item.get("id") in names:
                item["deny"] = list(item.get("deny", [])) + ["underground"]


TABLES = load_tables()
add_underground(TABLES)
TYPES = TABLES["settlement_types"]
TYPE = {t["id"]: t for t in TYPES}
TYPE_BY_CODE = {t["code"]: t["id"] for t in TYPES}
ERAS = TABLES["eras"]
ERA = {e["id"]: e for e in ERAS}
ERA_BY_CODE = {e["code"]: e["id"] for e in ERAS}
TERRAINS = TABLES["terrains"]
TERRAIN = {t["id"]: t for t in TERRAINS}
TERRAIN_BY_CODE = {t["code"]: t["id"] for t in TERRAINS}
FOLKS = TERRAIN["underground"]["folks"] if "underground" in TERRAIN else []     # who lives below
FOLK = {f["id"]: f for f in FOLKS}
FOLK_BY_CODE = {f["code"]: f["id"] for f in FOLKS}
NAME_STYLES = TABLES["name_styles"]
NAME_STYLE = {n["id"]: n for n in NAME_STYLES}
NAME_STYLE_BY_CODE = {n["code"]: n["id"] for n in NAME_STYLES}
NAME_TONES = TABLES["name_tones"]
NAME_TONE = {t["id"]: t for t in NAME_TONES}
NAME_TONE_BY_CODE = {t["code"]: t["id"] for t in NAME_TONES}
BUILDINGS = TABLES["buildings"]
BUILDING = {b["id"]: b for b in BUILDINGS}
SITUATIONS = TABLES["situations"]
DEMOGRAPHICS = TABLES["demographics"]
ECONOMY = TABLES["economy"]

# monsters, clues and treasure are WyrmDelve's tables (treasure: Old-School
# Essentials, Open Game Content, see LICENSE-OGL.txt)
MONSTERS = [m for m in load_optional(os.path.join(DATA, "monsters.json")).get("monsters", [])
            if m.get("name") and m.get("text")]
CLUES = {k: v for k, v in load_optional(os.path.join(DATA, "clues.json")).get("clues", {}).items() if v}
TREASURE = load_optional(os.path.join(DATA, "treasure.json"),
                         ("coins", "coin_value", "room_chance", "types", "gems", "jewellery", "magic_types", "magic",
                          "unguarded", "hiding"))


def type_name(kind):
    """The name of a settlement type (village, town...) in the current language."""
    return pick(TYPE[kind]["name"])


def building_type(kind):
    """The settlement type whose buildings a settlement uses (a big city uses the city's)."""
    return BUILDING_ALIAS.get(kind, kind)


def allowed_in(where, kind):
    """A data entry listed for some settlement types: is `kind` one of them?"""
    return kind in where or building_type(kind) in where


# --- dice ---
def roll(dice, rng):
    """"2d6", "1d4+1", "3", "0" -> a number."""
    dice = str(dice).strip().lower()
    m = re.fullmatch(r"(\d+)d(\d+)([+-]\d+)?", dice)
    if not m:
        return int(dice or 0)
    n, sides, plus = int(m.group(1)), int(m.group(2)), int(m.group(3) or 0)
    return sum(rng.randint(1, sides) for _ in range(n)) + plus


def span(text):
    """"1-3" -> (1, 3); "2" -> (2, 2)."""
    text = str(text)
    if "-" in text:
        a, b = text.split("-", 1)
        return int(a), int(b)
    return int(text), int(text)


# --- seed ---
# TYPE+POPULATION-ERA-TERRAIN-PURPOSE+DANGER[+STATE]-NAMES+TONE[+PEOPLE]-CODE, e.g.
# C9500-B-R-A2R-DE4-K7Q2MB: a city of 9,500 people, Late Middle Ages, on a river,
# a place of adventure of danger 2, in ruins (R; T: inhabited and threatened),
# grim German names. PEOPLE: none for people named like the places, X for
# fantasy names (mixed endings), or the code of another language (DE4NO: Danish
# and Swedish people). CODE = 6 symbols, 30 random bits. Older seeds have no
# STATE (any threat, ruins included) and may have no NAMES+TONE part: their place
# names are the medieval Italian ones of old, their people's names Italian too.
SEED_SYMBOLS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"   # no I, L, O, U: too easy to misread
CODE_LENGTH = 6
PURPOSES = ("rest", "adventure")
STATES = ("ruin", "threat")     # a place of adventure: in ruins and full of monsters, or inhabited and threatened
STATE_CODES = {"ruin": "R", "threat": "T"}


def new_number():
    """A fresh random seed number, CODE_LENGTH symbols long."""
    return int.from_bytes(os.urandom(4), "big") % (len(SEED_SYMBOLS) ** CODE_LENGTH)


def to_code(n):
    """A seed number written with the SEED_SYMBOLS alphabet (base 32, no I, L, O, U)."""
    out = []
    for _ in range(CODE_LENGTH):
        n, r = divmod(n, len(SEED_SYMBOLS))
        out.append(SEED_SYMBOLS[r])
    return "".join(reversed(out))


def from_code(text):
    """The number of a seed code, forgiving O for 0 and I or L for 1; None if it is not a code."""
    text = text.strip().upper().replace("O", "0").replace("I", "1").replace("L", "1")
    if len(text) != CODE_LENGTH or any(c not in SEED_SYMBOLS for c in text):
        return None
    n = 0
    for c in text:
        n = n * len(SEED_SYMBOLS) + SEED_SYMBOLS.index(c)
    return n


def make_seed(p):
    """The seed text of a settlement: TYPE+POP-ERA-TERRAIN-PURPOSE+DANGER[+STATE][-NAMES+TONE[+PEOPLE]]-CODE."""
    purpose = "A" if p["purpose"] == "adventure" else "R"
    state = STATE_CODES.get(p.get("state"), "")
    people = p.get("people") or "places"
    people = "" if people == "places" else "X" if people == "fantasy" else NAME_STYLE[people]["code"]
    names = f"{NAME_STYLE[p['names']]['code']}{NAME_TONE[p['tone']]['code']}{people}-" if p.get("names") else ""
    terrain = TERRAIN[p["terrain"]]["code"] + (FOLK[p["folk"]]["code"] if p["terrain"] == "underground" else "")
    return (f"{TYPE[p['type']]['code']}{p['pop']}-{ERA[p['era']]['code']}-{terrain}-"
            f"{purpose}{p['danger']}{state}-{names}{to_code(p['number'])}")


def read_seed(text):
    """The parameters held in a seed text (the inverse of make_seed), or None if it is not valid. Older seeds
    without the names part are still read."""
    parts = (text or "").strip().upper().replace(" ", "").split("-")
    names = tone = people = None
    if len(parts) == 6:             # with the names part: style, tone, people (none: like the places)
        m = re.fullmatch(r"([A-Z]{2})(\d)([A-Z]{1,2})?", parts[4])
        if not m:
            return None
        names, tone = NAME_STYLE_BY_CODE.get(m.group(1)), NAME_TONE_BY_CODE.get(m.group(2))
        people = {None: "places", "X": "fantasy"}.get(m.group(3)) or NAME_STYLE_BY_CODE.get(m.group(3))
        if None in (names, tone, people):
            return None
        del parts[4]
    if len(parts) != 5 or len(parts[0]) < 2 or len(parts[3]) not in (2, 3):
        return None
    state = {"R": "ruin", "T": "threat", "": None}.get(parts[3][2:])
    if parts[3][2:] and (state is None or parts[3][0] != "A"):
        return None
    kind, era, terrain = TYPE_BY_CODE.get(parts[0][0]), ERA_BY_CODE.get(parts[1]), TERRAIN_BY_CODE.get(parts[2][:1])
    folk = FOLK_BY_CODE.get(parts[2][1:]) if terrain == "underground" else None
    if (terrain == "underground") != (folk is not None) or (folk is None and len(parts[2]) != 1):
        return None
    purpose = {"A": "adventure", "R": "rest"}.get(parts[3][0])
    n = from_code(parts[4])
    if None in (kind, era, terrain, purpose, n) or not parts[0][1:].isdigit() or not parts[3][1].isdigit():
        return None
    p = {"type": kind, "pop": int(parts[0][1:]), "era": era, "terrain": terrain, "purpose": purpose,
         "danger": int(parts[3][1]), "state": state, "names": names, "tone": tone, "people": people, "number": n}
    if folk:
        p["folk"] = folk
    return None if check_params(p) else p


def example_seed():
    """A seed shown in questions and help as an example."""
    return "C9500-B-R-A2R-DE4-K7Q2MB"


def check_params(p):
    """Error message, or None if the parameters are fine."""
    lo, hi = TYPE[p["type"]]["pop"]
    if not lo <= p["pop"] <= hi:
        return tr("err_pop", t=type_name(p["type"]), lo=number(lo), hi=number(hi))
    if p["purpose"] == "adventure" and p["danger"] not in DANGERS:
        return tr("err_danger")
    if p["purpose"] == "rest" and p["danger"] != 0:
        return tr("err_danger_rest")
    return None


def random_pop(kind, rng):
    """A population for this type: usually in its typical range, sometimes anywhere in it."""
    lo, hi = TYPE[kind]["pop"]
    a, b = TYPE[kind]["typical"]
    if rng.random() < 0.75:
        lo, hi = a, b
    # log-uniform: small places are more common than big ones
    value = math.exp(rng.uniform(math.log(lo), math.log(hi)))
    step = 10 if value < 2000 else 100 if value < 20000 else 1000
    return int(max(lo, min(hi, round(value / step) * step)))


OPTIONAL_SHARE = 1 / 3      # with optional terrains asked for, how often chance picks one of them


def random_params(n, fixed=None):
    """Random parameters from the seed number; `fixed` ones are kept as they are. The optional terrains (giant
    mushroom forests, the underground) are drawn only when asked for (fixed["fungus"], fixed["underground"]):
    without them, the same seed number gives the same place as ever. Below, a folk too."""
    fixed = dict(fixed or {})
    r = random.Random(f"wyrmurbigen-params-{n}")
    p = {"type": r.choices([t["id"] for t in TYPES], weights=[5, 4, 2, 1, 3, 2][:len(TYPES)])[0],
         "era": r.choice([e["id"] for e in ERAS]),
         "terrain": r.choice([t["id"] for t in TERRAINS if not t.get("optional")]),
         "purpose": r.choice(PURPOSES)}
    optional = [t["id"] for t in TERRAINS if t.get("optional") and fixed.get(t["id"])]
    if optional and r.random() < OPTIONAL_SHARE:
        p["terrain"] = r.choice(optional)
    p.update({k: v for k, v in fixed.items() if k in ("type", "era", "terrain", "purpose")})
    if p["terrain"] == "underground":
        p["folk"] = fixed.get("folk") or r.choices([f["id"] for f in FOLKS], weights=[f["weight"] for f in FOLKS])[0]
    p["pop"] = fixed.get("pop") or random_pop(p["type"], r)
    if p["purpose"] == "adventure":
        p["danger"] = fixed.get("danger") or r.choices(DANGERS, weights=[4, 4, 3, 1])[0]
    else:
        p["danger"] = 0
    p["names"] = fixed.get("names") or r.choice([n["id"] for n in NAME_STYLES])
    p["tone"] = fixed.get("tone") or r.choice([t["id"] for t in NAME_TONES])
    p["people"] = fixed.get("people") or r.choices(PEOPLE_MODES, weights=[3, 1])[0]
    # a city of adventure is a ruin; a smaller place is one a third of the time, else inhabited and threatened
    p["state"] = None
    if p["purpose"] == "adventure":
        p["state"] = fixed.get("state") or ("ruin" if p["type"] in ("city", "bigcity") or r.random() < 1 / 3
                                            else "threat")
    p["number"] = n
    return p


def type_span(p):
    """Where the population sits in its type's range, 0 to 1 (on a log scale)."""
    lo, hi = TYPE[p["type"]]["pop"]
    return max(0.0, min(1.0, math.log(p["pop"] / lo) / math.log(hi / lo)))


# --- names ---
# Place names are built from the roots in data/names.json: a style (a language
# they sound like) and a tone. A name is a form such as "word start middle end":
# word and after are whole words before and after it, start + middle + end are
# syllables or name elements joined into one word.
TONE_BIAS = 0.6         # how often a root comes from the tone's own list
VOWELS = set("aeiouyàáâäåæéèêëíìîïóòôöøúùûü")


def draw_root(rng, style, slot, tone):
    """A root for one slot of a name (start, middle, end, word, after): from the tone's own list TONE_BIAS of the
    time, else from the common one."""
    table = style["roots"].get(slot, {})
    common, toned = table.get("all", []), table.get(tone, [])
    if toned and (not common or rng.random() < TONE_BIAS):
        return rng.choice(toned)
    return rng.choice(common)


def join_roots(left, right):
    """Glue two roots, without stutters: Linden + en -> Linden, Novo + ovo -> Novovo."""
    if len(left) >= 2 and right[:2].lower() == left[-2:].lower():
        right = right[2:]
    elif left and right and right[0].lower() == left[-1].lower() and right[0].lower() in VOWELS:
        right = right[1:]
    return left + right


def styled_name(rng, names, tone, simple=False):
    """A place name in a style and tone: a weighted form (start end, word start middle end...), roots drawn for each
    of its slots, glued and capitalised. The mix takes every root from a language of its own; `simple` leaves out
    the words before and after (home towns)."""
    style = NAME_STYLE[names]
    if style.get("mix"):            # every root from a language of its own
        styles = [n for n in NAME_STYLES if not n.get("mix")]
        first, last = rng.choice(styles), rng.choice(styles)
        pick_from = {"word": first, "start": first, "middle": rng.choice(styles), "end": last, "after": last}
    else:
        pick_from = dict.fromkeys(("word", "start", "middle", "end", "after"), style)
    forms = [f for f in TABLES["name_forms"] if not simple or "word" not in f[0] and "after" not in f[0]]
    form = rng.choices([f for f, _ in forms], weights=[w for _, w in forms])[0].split()
    for _ in range(20):             # no root twice, as in Liliensteinstein or Fairmead Mead
        roots = {slot: draw_root(rng, pick_from[slot], slot, tone) for slot in form}
        bare = [r.lower().strip("-' ").split()[-1] for r in roots.values()]
        if not any(i != k and len(x) >= 3 and x in y for i, x in enumerate(bare) for k, y in enumerate(bare)):
            break
    core = roots["start"]
    for slot in ("middle", "end"):
        if slot in roots:
            core = join_roots(core, roots[slot])
    core = re.sub(r"(.)\1\1+", r"\1\1", core, flags=re.IGNORECASE)
    core = core[:1].upper() + core[1:]
    if "word" in roots:
        word = roots["word"]
        core = word + core if word[-1] in "-'" else f"{word} {core}"
    if "after" in roots:
        after = roots["after"]
        core = core + after if after[0] == "-" else f"{core} {after}"
    return core


def place_name(rng, used=None, names=None, tone=None):
    """A place name in the style and tone of `names` and `tone`; without them,
    the medieval Italian names of the older seeds, made as they always were."""
    used = used if used is not None else set()
    while True:
        if names:
            name = styled_name(rng, names, tone)
        else:
            roots = NAME_STYLES[0]["roots"]
            name = rng.choice(roots["start"]["all"]) + rng.choice(roots["end"]["all"])
        if name not in used:
            used.add(name)
            return name


def name_combinations(names, tone):
    """How many different names a style and tone can make (roughly: a few
    syllables may glue into the same word)."""
    style = NAME_STYLE[names]
    styles = [n for n in NAME_STYLES if not n.get("mix")] if style.get("mix") else [style]

    def size(slot):
        """How many different roots a slot has in this tone (the common ones and the tone's)."""
        return len({w for s in styles for key in ("all", tone) for w in s["roots"].get(slot, {}).get(key, [])})
    return sum(math.prod(size(slot) for slot in form.split()) for form, _ in TABLES["name_forms"])


def round_millions(n):
    """12,345,678 -> "12 milioni" / "12 million"; from a billion up, billions."""
    key, n = ("billions", n / 1e9) if n >= 1e9 else ("millions", n / 1e6)
    return tr(key, n=number(round(n)) if n >= 10 else f"{n:.1f}".replace(".", "," if LANG == "it" else "."))


def name_examples(names, tone, count=3):
    """A few sample place names of a style and tone, the same every time (for the menus)."""
    rng = random.Random(f"wyrmurbigen-examples-{names}-{tone}")
    used = set()
    return [place_name(rng, used, names, tone) for _ in range(count)]


# People's names follow the place names' language (or another, or a fantasy mix
# of endings: the "people" setting). They are all made up, like the places: a
# beginning plus an ending from the roots of a language, real particles that
# make a real name only by chance (about a thousand first names and a thousand
# family names per language). The settlement's generator draws the kind of name
# (with a father's name, a family, a home town, a byname); the name itself
# comes from a generator of its own, keyed by the settlement and by the person's
# turn. A settlement has a dozen families and a dozen towns around it, so the
# same ones come back in its buildings, factions, history and rumours.
PEOPLE_MODES = ("places", "fantasy")
FAMILIES_PER_PLACE = 12
TOWNS_NEARBY = 12


class NameBook(set):
    """The names already given in a settlement, and how to make new ones."""

    def __init__(self, p=None):
        """An empty book for the settlement of parameters `p`; `count` numbers the people as they are named, so each
        gets a generator of its own."""
        super().__init__()
        p = p or {}
        self.p, self.count = p, 0


def name_style(p):
    """(style, tone) of a settlement's names; older seeds without them: medieval Italian, homely."""
    return p.get("names") or "italian", p.get("tone") or "homely"


def people_style(p, r):
    """(style, fantasy): whose people's names to use; for the mix, one drawn by r."""
    people = p.get("people") or "places"
    style = NAME_STYLE[name_style(p)[0] if people in PEOPLE_MODES else people]
    if style.get("mix"):
        style = r.choice([n for n in NAME_STYLES if not n.get("mix")])
    return style, people == "fantasy"


def built_name(r, style, part, fantasy):
    """A beginning of the style and an ending of it (fantasy: of any language)."""
    start = r.choice(style["people"]["roots"][part + "_start"])
    ends = style["people"]["roots"][part + "_end"]
    if fantasy:     # an ending of any language; with a vowel, or Hug + n would make Hugn
        ends = [e for e in r.choice([n for n in NAME_STYLES if n.get("people")])["people"]["roots"][part + "_end"]
                if VOWELS & set(e.lower())]
    name = re.sub(r"(.)\1\1+", r"\1\1", join_roots(start, r.choice(ends)))
    return name if name.startswith("al-") else name[:1].upper() + name[1:]


def feminine(style, family):
    """A family name for a woman: NicLeoid, Komnene, Ivanova, Radvilaite."""
    sid = style["id"]
    if sid == "gaelic" and family.startswith("Mac"):
        return "Nic" + family[3:]
    if sid == "byzantine":
        for end, fem in (("opoulos", "opoulina"), ("enos", "ene"), ("os", "ina"), ("es", "issa"), ("as", "aina"),
                         ("is", "ina")):
            if family.endswith(end):
                return family[:-len(end)] + fem
    if sid == "slavic":
        for end, fem in (("sky", "skaya"), ("skoy", "skaya"), ("aitis", "aite"), ("as", "aite"), ("is", "aite"),
                         ("ys", "yte"), ("ov", "ova"), ("ev", "eva"), ("in", "ina"), ("yn", "yna")):
            if family.endswith(end):
                return family[:-len(end)] + fem
    return family


def family_of(r, style, gender, fantasy):
    """A family name built from the style's roots; for a woman in its feminine form."""
    family = built_name(r, style, "fam", fantasy)
    return feminine(style, family) if gender == "f" else family


def patronymic(father, gender):
    """Slavic and Baltic: Ivan -> Ivanovich/Ivanovna, Andrei -> Andreevich,
    Nikita -> Nikitich, Algirdas -> Algirdaitis/Algirdaite."""
    if father[-2:] in ("as", "is", "us"):
        return father[:-2] + ("aite" if gender == "f" else "aitis")
    if father[-1] in "ai" and father[-2:] != "ai":
        stem, end = (father[:-1], ("ichna", "ich")) if father[-1] == "a" else (father[:-1], ("evna", "evich"))
        return stem + end[gender != "f"]
    return father + ("ovna" if gender == "f" else "ovich")


def styled_person(book, gender, kind, j):
    """(it, en): a person's name in the settlement's way, of kind father/family/place/by (j: the byname's index)."""
    p = book.p
    r = random.Random(f"wyrmurbigen-person-{p['number']}-{book.count}")
    style, fantasy = people_style(p, r)
    first = built_name(r, style, gender, fantasy)
    if kind == "by":
        by = TABLES["bynames"][j]
        return f"{first} {by[0]}", f"{first} {by[1]}"
    form = style["people"]["forms"][kind]
    form = form[gender] if isinstance(form, dict) else form
    form = form if isinstance(form, tuple) else (form, form)
    father = built_name(r, style, "m", fantasy)
    values = {"first": first, "father": father, "family": family_of(r, style, gender, fantasy),
              "patronymic": patronymic(father, gender)}
    if "{place}" in form[0]:
        values["place"] = styled_name(r, *name_style(p), simple=True)
    out = []
    for text in fmt(form, **values):
        text = re.sub(r"(.)\1\1+", r"\1\1", text)              # Magnus + sson -> Magnusson
        if style["id"] == "french":
            text = re.sub(r"\b(de) ([AEIOUYÉÈaeiouyh])", r"d'\2", text)
        out.append(text)
    return tuple(out)


def person_name(rng, gender, used):
    """(it, en): a first name and a father's name, a family, a home town or a byname, made up in the settlement's
    way; `used` is the settlement's NameBook, so nobody gets a name already given."""
    for _ in range(50):
        style = rng.random()
        kind = "father" if style < 0.3 else "family" if style < 0.6 else "place" if style < 0.8 else "by"
        j = rng.randrange(len(TABLES["bynames"])) if kind == "by" else None
        used.count += 1
        name = styled_person(used, gender, kind, j)
        if name[0] not in used:
            break
    used.add(name[0])
    return name


LOCAL_FAMILIES = 0.25       # the share of great families named in the people's own way; the rest are noble mixes


def noble_name(r):
    """A great family's name: the root of one noble house of Europe or Byzantium and the ending of another (or the
    same): Komnen + aldi, Visc + enos, Arpad + ville."""
    houses = TABLES["noble_houses"]
    root, end = r.choice(r.choice(houses)["roots"]), r.choice(r.choice(houses)["ends"])
    name = re.sub(r"(.)\1\1+", r"\1\1", join_roots(root, end))
    return name[:1].upper() + name[1:]


def family_name(rng, p, key="family"):
    """One of the settlement's FAMILIES_PER_PLACE great families: a mix of the roots of the noble houses or, now and
    then, a name made up in its people's way."""
    j = rng.randrange(FAMILIES_PER_PLACE)
    r = random.Random(f"wyrmurbigen-{key}-{p['number']}-{j}")
    if r.random() >= LOCAL_FAMILIES:
        return noble_name(r)
    style, fantasy = people_style(p, r)
    return family_of(r, style, "m", fantasy)


def town_name(rng, p):
    """One of the TOWNS_NEARBY towns around (a home town, a gate's destination), in the settlement's language."""
    j = rng.randrange(TOWNS_NEARBY)
    return styled_name(random.Random(f"wyrmurbigen-town-{p['number']}-{j}"), *name_style(p), simple=True)


def people_counts(p):
    """About how many first names (m, f) and families the people's names can have."""
    styles = [n for n in NAME_STYLES if n.get("people")]
    people = p.get("people") or "places"
    sid = name_style(p)[0] if people in PEOPLE_MODES else people
    chosen = styles if NAME_STYLE[sid].get("mix") else [NAME_STYLE[sid]]

    def count(part):
        """First or family names of one kind: beginnings x endings."""
        total = 0
        for style in chosen:
            ends = sum(len(n["people"]["roots"][part + "_end"]) for n in styles) if people == "fantasy" else \
                len(style["people"]["roots"][part + "_end"])
            total += len(style["people"]["roots"][part + "_start"]) * ends
        return total
    return count("m"), count("f"), count("fam")


def people_words(p):
    """How the people are named, in words, for the log and the key."""
    people = p.get("people") or "places"
    if people == "places":
        return tr("people_w_places", s=pick(NAME_STYLE[p["names"]]["name"]))
    return tr("people_w_fantasy") if people == "fantasy" else pick(NAME_STYLE[people]["name"])


def people_examples(p, count=3):
    """A few sample people's names for the menu of the people setting (always the same)."""
    book = NameBook(dict(p, number=f"examples-{p.get('people')}"))
    rng = random.Random(f"wyrmurbigen-people-examples-{p.get('people')}")
    return [pick(person_name(rng, g, book)) for g in "mfm"[:count]]


# The gods: no real religion, but a small pantheon of made-up gods for every
# settlement, the same for a seed. Their names are built from the divine roots
# of data/names.json; each is a god or goddess of a domain (data/settlements.json),
# one of them of the land around when it has one (the sea on the coast...).
GODS_PER_PLACE = 5
_PANTHEONS = {}


def pantheon(p):
    """The gods of a settlement: [{"name", "gender", "domain"}], the patron first."""
    key = (p["number"], p["terrain"])
    if key not in _PANTHEONS:
        r = random.Random(f"wyrmurbigen-gods-{p['number']}")
        roots = TABLES["god_roots"]
        local = [d for d in TABLES["god_domains"] if p["terrain"] in d.get("terrains", ())]
        common = [d for d in TABLES["god_domains"] if not d.get("terrains")]
        domains = ([r.choice(local)] if local else []) + r.sample(common, GODS_PER_PLACE - (1 if local else 0))
        r.shuffle(domains)
        gods, names = [], set()
        for d in domains:
            while True:
                gender = r.choice("mf")
                name = join_roots(r.choice(roots["start"]), r.choice(roots[gender + "_end"])).capitalize()
                if name not in names:
                    break
            names.add(name)
            gods.append({"name": name, "gender": gender, "domain": d["name"]})
        _PANTHEONS[key] = gods
    return _PANTHEONS[key]


def god_name(rng, p):
    """(it, en): one of the settlement's gods, for a temple, a gate, a confraternity..."""
    god = pantheon(p)[rng.randrange(GODS_PER_PLACE)]
    return god["name"], god["name"]


def gods_text(p):
    """(it, en): the pantheon in words: Orsaldra, goddess of the harvest; Velmor, god of storms..."""
    out = []
    for lang in (0, 1):
        out.append("; ".join(f"{g['name']}, {TABLES['god_titles'][g['gender']][lang]} {g['domain'][lang]}"
                             for g in pantheon(p)))
    return tuple(out)


class Deck:
    """Draws without repeats until the deck is empty, then reshuffles."""

    def __init__(self, items, rng):
        """A deck of `items`, shuffled with `rng` when it is first drawn from."""
        self.items, self.rng, self.pool = list(items), rng, []

    def draw(self):
        """The next item; when the deck is empty, it is reshuffled."""
        if not self.pool:
            self.pool = list(self.items)
            self.rng.shuffle(self.pool)
        return self.pool.pop()



# --- the plan ---
# The map is a grid of letters. Every cell has a ground (grass, a field, trees,
# hills, mountains, reeds, water) and, on top of it, what people built: streets,
# squares, walls, towers, gates, ditches, bridges, buildings, gardens.
STREET, SQUARE, ROAD, YARD = "street", "square", "road", "yard"
WALL, TOWER, GATE, PALISADE = "wall", "tower", "gate", "palisade"
DITCH, MOAT, BRIDGE, PIER = "ditch", "moat", "bridge", "pier"
GARDEN, GRAVE, MOUND, BLDG = "garden", "grave", "mound", "building"
OPEN = {STREET, SQUARE, ROAD, YARD, PIER}
FORT = {WALL, TOWER, GATE, PALISADE}
DIRS4 = ((1, 0), (-1, 0), (0, 1), (0, -1))
STEPS8 = [(dx, dy, math.hypot(dx / ASPECT, dy)) for dx in (-1, 0, 1) for dy in (-1, 0, 1) if dx or dy]
INF = float("inf")


def vdist(x0, y0, x1, y1):
    """Distance as the eye sees it: a row is 1, a column 1/2."""
    return math.hypot((x1 - x0) / ASPECT, y1 - y0)


class Building:

    """A building on the map: its kind (from buildings.json), rectangle, door, stone or timber, and what is filled
    in later (number, quarter, NPC, title...)."""
    def __init__(self, kind, x0, y0, w, h, door, stone, outside=False):
        """A building of `kind` in the rectangle x0, y0, w, h, with its door cell."""
        self.kind, self.x0, self.y0, self.w, self.h = kind, x0, y0, w, h
        self.door, self.stone, self.outside = door, stone, outside
        self.number, self.quarter, self.ruined = 0, 0, False
        self.uid = None

    def cells(self):
        """All the cells of the building's rectangle."""
        return [(x, y) for y in range(self.y0, self.y0 + self.h) for x in range(self.x0, self.x0 + self.w)]

    def centre(self):
        """The centre of the rectangle (may fall between cells)."""
        return self.x0 + (self.w - 1) / 2, self.y0 + (self.h - 1) / 2

    @property
    def id(self):
        """The id of the building's kind (inn, church...)."""
        return self.kind["id"]


class Plan:

    """The map being built, as grids of W x H letters: ground (grass, water, trees...), cell (what is built: walls,
    streets, buildings...), inside (within the walls), bmap (which building), tex (random texture), plus
    buildings, gates, features and secrets."""
    def __init__(self, W, H, rng):
        """An empty plan of W x H letters: all grass, nothing built; `rng` makes the texture."""
        self.W, self.H = W, H
        self.ground = [["grass"] * W for _ in range(H)]
        self.cell = [[None] * W for _ in range(H)]
        self.inside = [[False] * W for _ in range(H)]
        self.bmap = [[-1] * W for _ in range(H)]
        self.tex = [[rng.random() for _ in range(W)] for _ in range(H)]
        self.buildings = []
        self.feat = {}              # (x, y) -> well, fountain, stall, tree, statue
        self.gates = []             # {"angle", "cells", "inner", "outer", "letter"}
        self.secret = set()         # posterns: $ on the referee's map
        self.tunnel = set()         # secret tunnel: ░ on the referee's map
        self.tunnel_from = None     # the building the tunnel starts from
        self.main = set()           # main street cells
        self.cx = self.cy = self.R = 0
        self.walled = False
        self.wall_kind = None       # "stone", "palisade" or None
        self.moat = None            # "water", "dry" or None
        self.water = False          # any water on the map
        self.harbour = False
        self.quarters = 1           # walled towns: one quarter for every gate
        self.layout = ""            # how the streets were laid out (for the key)
        self.row_m = 5.0            # metres in a row of letters
        self.height = None          # mountains: 0 to 1, highest at the summit (see perched)
        self.approach = None        # mountains: the angle of the one easy way up
        self.stairs = set()         # mountains: street cells too steep for a cart

    def ok(self, x, y):
        """Whether x, y is on the map."""
        return 0 <= x < self.W and 0 <= y < self.H

    def is_water(self, x, y):
        """Whether the ground at x, y is water (sea, lake, river)."""
        return self.ground[y][x] == "water"


def smoothstep(t):
    """The smooth 0-1 easing curve 3t² - 2t³."""
    return t * t * (3 - 2 * t)


def noise_grid(W, H, rng, scale):
    """Smooth value noise in 0..1, with features about `scale` rows across."""
    sx, sy = scale * ASPECT, scale
    gw, gh = int(W / sx) + 3, int(H / sy) + 3
    pts = [[rng.random() for _ in range(gw)] for _ in range(gh)]
    out = [[0.0] * W for _ in range(H)]
    for y in range(H):
        fy = y / sy
        iy, ty = int(fy), smoothstep(fy - int(fy))
        for x in range(W):
            fx = x / sx
            ix, tx = int(fx), smoothstep(fx - int(fx))
            a = pts[iy][ix] * (1 - tx) + pts[iy][ix + 1] * tx
            b = pts[iy + 1][ix] * (1 - tx) + pts[iy + 1][ix + 1] * tx
            out[y][x] = a * (1 - ty) + b * ty
    return out


def distance_field(plan, sources, passable=None, limit=None):
    """Visual distance from the nearest source, over the cells `passable` allows."""
    W, H = plan.W, plan.H
    dist = [[INF] * W for _ in range(H)]
    heap = []
    for x, y in sources:
        if plan.ok(x, y):
            dist[y][x] = 0.0
            heap.append((0.0, x, y))
    heapq.heapify(heap)
    while heap:
        d, x, y = heapq.heappop(heap)
        if d > dist[y][x] or (limit is not None and d > limit):
            continue
        for dx, dy, c in STEPS8:
            nx, ny = x + dx, y + dy
            if not (0 <= nx < W and 0 <= ny < H) or (passable and not passable(nx, ny)):
                continue
            nd = d + c
            if nd < dist[ny][nx]:
                dist[ny][nx] = nd
                heapq.heappush(heap, (nd, nx, ny))
    return dist


def route(plan, start, is_goal, cost, target=None):
    """Cheapest 4-way path from start to a goal cell; cost(x, y) None = blocked.
    A step across costs 1/2 (a column), a step down 1 (a row)."""
    sx, sy = start
    best = {start: 0.0}
    came = {}
    heap = [(0.0, 0.0, sx, sy)]
    while heap:
        _, g, x, y = heapq.heappop(heap)
        if g > best.get((x, y), INF):
            continue
        if is_goal(x, y) and (x, y) != start:
            path = [(x, y)]
            while (x, y) in came:
                x, y = came[(x, y)]
                path.append((x, y))
            return path[::-1]
        for dx, dy in DIRS4:
            nx, ny = x + dx, y + dy
            if not plan.ok(nx, ny):
                continue
            c = cost(nx, ny)
            if c is None:
                continue
            ng = g + c * (1 / ASPECT if dx else 1.0)
            if ng < best.get((nx, ny), INF):
                best[(nx, ny)] = ng
                came[(nx, ny)] = (x, y)
                h = vdist(nx, ny, *target) * 0.5 if target else 0.0
                heapq.heappush(heap, (ng + h, ng, nx, ny))
    return None


def carve(plan, path, kind, wide=True, over=(None,), mark=None):
    """Lay a street (or a road...) along a path; vertical stretches get two
    columns, so they look as wide as the horizontal ones."""
    for k, (x, y) in enumerate(path):
        cells = [(x, y)]
        if wide:
            prev = path[k - 1] if k else None
            nxt = path[k + 1] if k + 1 < len(path) else None
            if (prev and prev[0] == x) or (nxt and nxt[0] == x):
                cells.append((x + 1, y))
        for cx, cy in cells:
            if plan.ok(cx, cy) and plan.cell[cy][cx] in over:
                if plan.is_water(cx, cy) and kind in (ROAD, STREET):
                    plan.cell[cy][cx] = BRIDGE
                else:
                    plan.cell[cy][cx] = kind
                if mark is not None:
                    mark.add((cx, cy))


def ray(cx, cy, angle, t):
    """The point t visual units from (cx, cy) along `angle`, in letters."""
    return cx + math.cos(angle) * t * ASPECT, cy + math.sin(angle) * t


# --- the land around ---
def environment(plan, p, rng, reach):
    """Water, woods, hills and mountains around the settlement. `reach` is how
    far (visual units) the settlement goes from its centre: water and woods
    stay beyond it."""
    W, H, cx, cy, R = plan.W, plan.H, plan.cx, plan.cy, plan.R
    terrain = p["terrain"]
    # two noise layers: n1 for broad shapes, n2 for fine detail
    n1 = noise_grid(W, H, rng, max(4.0, R * 0.6))
    n2 = noise_grid(W, H, rng, 3.0)
    plan.n1, plan.n2 = n1, n2
    ground, tex = plan.ground, plan.tex
    plan.water_side = None
    # the sea: everything beyond a wavy line on one side
    if terrain == "coast":
        side = rng.choice(((0, 1), (0, -1), (1, 0), (-1, 0)))
        plan.water_side = side
        d0 = reach * rng.uniform(0.95, 1.1)
        for y in range(H):
            for x in range(W):
                proj = (x - cx) / ASPECT * side[0] + (y - cy) * side[1]
                wobble = (n1[y][x] - 0.5) * R * 0.45 + (n2[y][x] - 0.5) * 1.6
                if proj > d0 + wobble:
                    ground[y][x] = "water"
    # a lake: a wobbly disc just beyond the settlement
    elif terrain == "lake":
        angle = rng.uniform(0, 2 * math.pi)
        radius = R * rng.uniform(1.0, 1.5)
        lx, ly = ray(cx, cy, angle, reach + radius * 0.85)
        plan.water_side = (round(math.cos(angle)), round(math.sin(angle)))
        for y in range(H):
            for x in range(W):
                if vdist(x, y, lx, ly) < radius * (0.8 + 0.4 * n1[y][x]):
                    ground[y][x] = "water"
    # a river: a meandering band across or down the map, just outside the settlement
    elif terrain == "river":
        across = rng.random() < 0.65 or H < 30           # the river runs across the map
        side = rng.choice((-1, 1))
        off = reach * rng.uniform(1.0, 1.12) * side
        amp, per, phase = rng.uniform(1.0, 2.5), rng.uniform(0.03, 0.06), rng.uniform(0, 2 * math.pi)
        half = rng.uniform(1.0, 1.5)
        plan.water_side = (0, side) if across else (side, 0)
        for y in range(H):
            for x in range(W):
                if across:
                    centre = cy + off + amp * math.sin(x * per + phase) + (n1[y][x] - 0.5) * 2
                    near = abs(y - centre) <= half
                else:
                    centre = cx + (off + amp * math.sin(y * per * 2 + phase) + (n1[y][x] - 0.5) * 2) * ASPECT
                    near = abs(x - centre) / ASPECT <= half
                if near:
                    ground[y][x] = "water"
    if terrain == "mountains":
        perched(plan, rng)
    for y in range(H):
        for x in range(W):
            if ground[y][x] == "water":
                continue
            # the rest of the land by terrain, thicker the farther from the centre
            d = vdist(x, y, cx, cy)
            a, b, t = n1[y][x], n2[y][x], tex[y][x]
            if terrain == "swamp":
                if d > reach * 1.15 and b > 0.64:
                    ground[y][x] = "water"
                elif d > reach * 1.05 and a > 0.4 and t < 0.45:
                    ground[y][x] = "reed"
            elif terrain == "fungus":
                # giant mushrooms in groves all round, a few lone ones close to the houses
                clearing = reach * (1.35 + 0.5 * a)
                if d > clearing and t < 0.78:
                    ground[y][x] = "shroom"
                elif d > reach * 1.05 and b > 0.74 and t < 0.45:
                    ground[y][x] = "shroom"
            elif terrain == "forest":
                clearing = reach * (1.45 + 0.5 * a)
                if d > clearing and t < 0.8:
                    ground[y][x] = "tree"
                elif d > reach * 1.15 and b > 0.78 and t < 0.5:
                    ground[y][x] = "tree"
            elif terrain == "hills":
                if d > reach * 1.25 and b > 0.5 and t < 0.32:
                    ground[y][x] = "hill"
                elif reach * 1.05 < d < reach * 1.3 and t < 0.18:
                    ground[y][x] = "hill"          # the slopes of the settlement's own hill
                elif d > reach * 1.3 and a > 0.72 and t < 0.45:
                    ground[y][x] = "tree"
            elif terrain == "mountains":
                # the valley below the way up stays open: hills and woods, no peaks
                down = abs(math.remainder(math.atan2(y - cy, (x - cx) / ASPECT) - plan.approach, 2 * math.pi)) < 0.8
                if d > reach * 1.35 and a > 0.56 and t < 0.6 and not down:
                    ground[y][x] = "mount"
                elif d > reach * 1.15 and a > 0.44 and t < 0.32:
                    ground[y][x] = "hill"
                elif d > reach * 1.2 and b > 0.7 and t < 0.45:
                    ground[y][x] = "tree"
            else:
                if d > reach * 1.2 and b > 0.8 and t < 0.35:
                    ground[y][x] = "tree"          # copses and hedgerows
    plan.water = any(ground[y][x] == "water" for y in range(H) for x in range(W))


def perched(plan, rng):
    """A mountain settlement sits on a spur: the summit a little off the centre, on the far side from the one easy
    way up (plan.approach, an angle); plan.height, 0 to 1, falls from the summit, faster and faster towards the
    valleys. plan.grade is how steep the slope is just outside the settlement (for roads and stairs)."""
    a = rng.uniform(0, 2 * math.pi)
    plan.approach = a
    sx, sy = ray(plan.cx, plan.cy, a + math.pi, plan.R * 0.45)
    plan.summit = (sx, sy)
    far = max(vdist(x, y, sx, sy) for x in (0, plan.W - 1) for y in (0, plan.H - 1))
    plan.height = [[1 - (vdist(x, y, sx, sy) / far) ** 1.6 + (plan.n1[y][x] - 0.5) * 0.06 for x in range(plan.W)]
                   for y in range(plan.H)]
    d = plan.R * 1.3
    plan.grade = 1.6 * d ** 0.6 / far ** 1.6


# --- shapes ---
def to_letters(cx, cy, vx, vy):
    """A point at offset vx, vy from cx, cy, in letters: x is stretched by ASPECT, since a letter is twice as tall
    as it is wide."""
    return cx + vx * ASPECT, cy + vy


def blob_shape(cx, cy, R, rng, n=24, wobble=0.12, stretch=1.0, angle=0.0):
    """A rounded, wobbly outline of radius R around cx, cy (n points): a few random harmonics, optionally stretched
    along `angle`."""
    harmonics = [(k, rng.uniform(0, wobble / math.sqrt(k)), rng.uniform(0, 2 * math.pi)) for k in (2, 3, 4, 5)]
    pts = []
    for i in range(n):
        a = 2 * math.pi * i / n
        r = R * (1 + sum(amp * math.cos(k * a + ph) for k, amp, ph in harmonics))
        vx, vy = r * math.cos(a), r * math.sin(a)
        if stretch != 1.0:
            ca, sa = math.cos(angle), math.sin(angle)
            u, v = vx * ca + vy * sa, -vx * sa + vy * ca
            u, v = u * stretch, v / math.sqrt(stretch)
            vx, vy = u * ca - v * sa, u * sa + v * ca
        pts.append(to_letters(cx, cy, vx, vy))
    return pts


def polygon_shape(cx, cy, R, n, rng, jitter=0.12, rotate=None):
    """A polygon of n corners around cx, cy, each a little off by `jitter` (towers on a wall)."""
    rot = rng.uniform(0, 2 * math.pi) if rotate is None else rotate
    pts = []
    for i in range(n):
        a = rot + 2 * math.pi * i / n + rng.uniform(-jitter, jitter) * math.pi / n
        r = R * rng.uniform(1 - jitter, 1 + jitter)
        pts.append(to_letters(cx, cy, r * math.cos(a), r * math.sin(a)))
    return pts


def rect_shape(cx, cy, hx, hy):
    """hx, hy: half sides in visual units."""
    return [to_letters(cx, cy, -hx, -hy), to_letters(cx, cy, hx, -hy), to_letters(cx, cy, hx, hy),
            to_letters(cx, cy, -hx, hy)]


def bastioned_shape(cx, cy, R, n, rng, rotate=None):
    """A regular polygon with an arrow-head bastion on every corner (the
    'Italian trace' of Renaissance fortification)."""
    rot = rng.uniform(0, 2 * math.pi) if rotate is None else rotate
    base = [(R * math.cos(rot + 2 * math.pi * i / n), R * math.sin(rot + 2 * math.pi * i / n)) for i in range(n)]
    edge = math.dist(base[0], base[1])
    b = edge * 0.2
    out = []
    for i, v in enumerate(base):
        prev, nxt = base[i - 1], base[(i + 1) % n]
        up = ((prev[0] - v[0]) / edge, (prev[1] - v[1]) / edge)
        un = ((nxt[0] - v[0]) / edge, (nxt[1] - v[1]) / edge)
        o = (-(up[0] + un[0]), -(up[1] + un[1]))
        ol = math.hypot(*o) or 1
        o = (o[0] / ol, o[1] / ol)
        f1 = (v[0] + up[0] * b, v[1] + up[1] * b)
        f2 = (v[0] + un[0] * b, v[1] + un[1] * b)
        s1 = (f1[0] + o[0] * b * 0.55, f1[1] + o[1] * b * 0.55)
        s2 = (f2[0] + o[0] * b * 0.55, f2[1] + o[1] * b * 0.55)
        tip = (v[0] + o[0] * b * 1.5, v[1] + o[1] * b * 1.5)
        out += [f1, s1, tip, s2, f2]
    return [to_letters(cx, cy, x, y) for x, y in out], [to_letters(cx, cy, *v) for v in base]


def clip_to_land(plan, pts, margin=1.6):
    """Pull every corner back toward the centre where water or the map edge would cut it."""
    out = []
    for px, py in pts:
        dx, dy = (px - plan.cx) / ASPECT, py - plan.cy
        full = math.hypot(dx, dy)
        if full == 0:
            out.append((px, py))
            continue
        angle = math.atan2(dy, dx)
        t, last = 0.0, 0.0
        while t <= full + margin:
            x, y = ray(plan.cx, plan.cy, angle, t)
            ix, iy = int(x), int(y)
            if not (2 <= ix < plan.W - 3 and 2 <= iy < plan.H - 2) or plan.is_water(ix, iy):
                break
            last = t
            t += 0.25
        r = min(full, max(2.0, last - margin)) if last < full + margin else full
        out.append(ray(plan.cx, plan.cy, angle, r))
    return out


def point_in_polygon(x, y, pts):
    """Whether the point x, y is inside the polygon (even-odd ray casting)."""
    inside = False
    j = len(pts) - 1
    for i in range(len(pts)):
        xi, yi = pts[i]
        xj, yj = pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi + 1e-12) + xi:
            inside = not inside
        j = i
    return inside


def polygon_mask(plan, pts):
    """The set of cells whose centre is inside the polygon."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    mask = set()
    for y in range(max(0, int(min(ys)) - 1), min(plan.H, int(max(ys)) + 2)):
        for x in range(max(0, int(min(xs)) - 1), min(plan.W, int(max(xs)) + 2)):
            if point_in_polygon(x + 0.5, y + 0.5, pts):
                mask.add((x, y))
    return mask


def clean_mask(plan, mask, bank=1.2):
    """No water inside, a strip of bank between walls and water, nothing on the
    map edge; keep the part around the centre."""
    water = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.is_water(x, y)]
    near = distance_field(plan, water, limit=bank + 1) if water else None
    keep = {(x, y) for x, y in mask
            if 2 <= x < plan.W - 3 and 2 <= y < plan.H - 2 and (near is None or near[y][x] > bank)}
    if not keep:
        return keep
    start = min(keep, key=lambda c: vdist(c[0], c[1], plan.cx, plan.cy))
    part, todo = {start}, [start]
    while todo:
        x, y = todo.pop()
        for dx, dy in DIRS4:
            n = (x + dx, y + dy)
            if n in keep and n not in part:
                part.add(n)
                todo.append(n)
    return part


def ring_of(mask):
    """The cells of a region that touch the outside: a wall two columns or one row thick."""
    return {(x, y) for x, y in mask
            if any((x + dx, y + dy) not in mask for dx in (-2, -1, 0, 1, 2) for dy in (-1, 0, 1))}


def set_inside(plan, mask):
    """Mark the cells of `mask` as inside the walls."""
    for x, y in mask:
        plan.inside[y][x] = True


# --- walls, towers, gates ---
def build_walls(plan, mask, kind, corners=(), spacing=7.0, towers=True):
    """kind: WALL or PALISADE. Towers at the corners, then every `spacing`."""
    ring = ring_of(mask)
    for x, y in ring:
        plan.cell[y][x] = kind
    if not towers:
        return ring
    placed = []
    order = [min(ring, key=lambda c: (c[0] - px) ** 2 / 4 + (c[1] - py) ** 2) for px, py in corners]
    order += sorted(ring, key=lambda c: math.atan2(c[1] - plan.cy, (c[0] - plan.cx) / ASPECT))
    for x, y in order:
        if all(vdist(x, y, tx, ty) >= (spacing if (x, y) not in order[:len(corners)] else 2.5) for tx, ty in placed):
            if stamp_tower(plan, x, y, mask):
                placed.append((x, y))
    return ring


def stamp_tower(plan, x, y, mask, half=(2, 1)):
    """A tower: a block five columns by three rows on the wall, sticking out."""
    hx, hy = half
    cells = [(x + dx, y + dy) for dx in range(-hx, hx + 1) for dy in range(-hy, hy + 1)]
    if any(plan.ok(cx, cy) and plan.cell[cy][cx] == GATE for cx, cy in cells):
        return False
    for cx, cy in cells:
        if not plan.ok(cx, cy):
            continue
        c = plan.cell[cy][cx]
        if c in (WALL, PALISADE) or ((cx, cy) not in mask and c is None and not plan.is_water(cx, cy)):
            plan.cell[cy][cx] = TOWER
    return True


def gate_angles(plan, mask, n, rng, prefer=None):
    """n directions for the gates, spread out, toward land (or, for one of
    them, toward the water: a harbour or a bridge)."""
    if n <= 0:
        return []
    scores = []
    for k in range(48):
        a = 2 * math.pi * k / 48
        t, land = 0.0, True
        while True:
            x, y = ray(plan.cx, plan.cy, a, t)
            if (int(x), int(y)) not in mask:
                break
            t += 0.25
        for extra in (1.5, 3.0, 5.0):
            x, y = ray(plan.cx, plan.cy, a, t + extra)
            if not plan.ok(int(x), int(y)) or plan.is_water(int(x), int(y)):
                land = False
        scores.append((a, land))
    lands = [a for a, ok in scores if ok] or [a for a, _ in scores]
    start = prefer if prefer is not None else rng.choice(lands)
    spread = 2 * math.pi / n
    if plan.approach is not None and prefer is None:    # perched: one or two gates, both facing the way up
        n = min(n, 2)
        start, spread = plan.approach - (n - 1) * 0.45, 0.9
    chosen = []
    for i in range(n):
        want = start + spread * i + rng.uniform(-0.25, 0.25)
        best = min(lands, key=lambda a: min(abs(a - want) % (2 * math.pi), (want - a) % (2 * math.pi))
                   + (5 if any(abs(math.remainder(a - c, 2 * math.pi)) < 0.6 for c in chosen) else 0))
        chosen.append(best)
    return chosen


def carve_gate(plan, mask, angle, flank=True):
    """Open a gate through the wall along `angle` from the centre."""
    t = 0.0
    inner = outer = None
    cells = []
    # walk out from the centre along the angle: the wall cells crossed are the gate, the last cell before them is
    # inside, the first after them outside
    while t < plan.R * 3:
        x, y = ray(plan.cx, plan.cy, angle, t)
        ix, iy = int(x), int(y)
        if not plan.ok(ix, iy):
            break
        c = plan.cell[iy][ix]
        if c in FORT or (ix, iy) in mask and c in (WALL, TOWER, PALISADE):
            cells.append((ix, iy))
        elif cells and (ix, iy) not in mask:
            outer = (ix, iy)
            break
        elif not cells:
            inner = (ix, iy)
        t += 0.2
    if not cells or outer is None:
        return None
    # a gate in a wall running across is two letters wide, since letters are narrow
    vertical = abs(math.sin(angle)) > 0.6
    gate_cells = set()
    for x, y in cells:
        gate_cells.add((x, y))
        if vertical:
            gate_cells.add((x + 1, y))
    for x, y in gate_cells:
        if plan.ok(x, y) and plan.cell[y][x] in FORT:
            plan.cell[y][x] = GATE
    # a tower on each side of the gate, on the wall a few letters away
    if flank:
        tx, ty = -math.sin(angle), math.cos(angle)
        mx = sum(c[0] for c in cells) / len(cells)
        my = sum(c[1] for c in cells) / len(cells)
        for s in (-1, 1):
            px, py = mx + s * tx * 3.0 * ASPECT, my + s * ty * 3.0
            ring = [(x, y) for x in range(int(px) - 3, int(px) + 4) for y in range(int(py) - 2, int(py) + 3)
                    if plan.ok(x, y) and plan.cell[y][x] in (WALL, PALISADE, TOWER)]
            if ring:
                x, y = min(ring, key=lambda c: (c[0] - px) ** 2 / 4 + (c[1] - py) ** 2)
                stamp_tower(plan, x, y, mask)
    gate = {"angle": angle, "cells": sorted(gate_cells), "inner": inner, "outer": outer}
    plan.gates.append(gate)
    return gate


def moat_around(plan, mask, kind, width=1.4):
    """A ditch (dry) or a moat (water) around the walls."""
    fort = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.cell[y][x] in FORT]
    dist = distance_field(plan, fort, passable=lambda x, y: (x, y) not in mask, limit=width + 1.2)
    for y in range(plan.H):
        for x in range(plan.W):
            d = dist[y][x]
            if 0.9 < d <= 0.9 + width and plan.cell[y][x] is None and (x, y) not in mask:
                if not plan.is_water(x, y):
                    plan.cell[y][x] = kind


# --- streets ---
def street_cost(plan, organic, region=None):
    """The cost function for laying streets: cheap along existing streets, impossible across walls, buildings and
    water, noisy when `organic` (crooked medieval streets)."""
    noise = plan.n2

    def cost(x, y):
        """The cost of stepping on x, y, or None if a street cannot go there."""
        c = plan.cell[y][x]
        if region is not None and not region(x, y):
            return None
        if not plan.inside[y][x] or c in FORT or c == BLDG or plan.is_water(x, y):
            return None
        base = 0.55 if c in (STREET, SQUARE) else 1.0
        return base * (1 + (2.2 * noise[y][x] if organic else 0))
    return cost


def make_square(plan, rng, hw, hh, kind=SQUARE, irregular=True):
    """The main square at the centre: a rectangle of half-sizes hw, hh, with a bitten corner and a pushed side when
    `irregular`."""
    cx, cy = int(plan.cx), int(plan.cy)
    cells = set()
    for y in range(cy - hh, cy + hh + 1):
        for x in range(cx - hw, cx + hw + 1):
            cells.add((x, y))
    if irregular:
        for _ in range(2):                          # bite a corner off, push a side out
            corner = (rng.choice((cx - hw, cx + hw - 3)), rng.choice((cy - hh, cy + hh)))
            for dx in range(4):
                cells.discard((corner[0] + dx, corner[1]))
        side = rng.choice((-1, 1))
        for y in range(cy - hh + 1, cy + hh):
            for dx in range(1, 4):
                cells.add((cx + side * (hw + dx), y))
    for x, y in cells:
        if plan.ok(x, y) and plan.inside[y][x] and plan.cell[y][x] is None and not plan.is_water(x, y):
            plan.cell[y][x] = kind
    plan.square = {(x, y) for x, y in cells if plan.ok(x, y) and plan.cell[y][x] == kind}
    return plan.square


def main_streets(plan, rng, organic=True, straight=False):
    """From every gate to the square."""
    goal = plan.square
    for gate in plan.gates:
        if gate["inner"] is None:
            continue
        if straight:
            path = straight_path(plan, gate["inner"], (int(plan.cx), int(plan.cy)))
        else:
            path = route(plan, gate["inner"], lambda x, y: (x, y) in goal, street_cost(plan, organic),
                         target=(plan.cx, plan.cy))
        if path:
            carve(plan, path, STREET, over=(None, STREET), mark=plan.main)
        for x, y in gate["cells"]:
            plan.main.add((x, y))


def straight_path(plan, a, b):
    """Two straight legs, across then down (a planned town)."""
    (x0, y0), (x1, y1) = a, b
    path = []
    step = 1 if x1 >= x0 else -1
    for x in range(x0, x1 + step, step):
        path.append((x, y0))
    step = 1 if y1 >= y0 else -1
    for y in range(y0 + step, y1 + step, step):
        path.append((x1, y))
    return [(x, y) for x, y in path if plan.ok(x, y) and plan.inside[y][x]]


def line_cells(plan, angle, t0, t1):
    """The cells along a ray from the centre at `angle`, from distance t0 to t1."""
    out = []
    t = t0
    while t <= t1:
        x, y = ray(plan.cx, plan.cy, angle, t)
        c = (int(x), int(y))
        if not out or out[-1] != c:
            out.append(c)
        t += 0.2
    return out


def radial_streets(plan, angles):
    """Straight streets from the centre outwards at the given angles (Renaissance ideal cities)."""
    for a in angles:
        cells = []
        for x, y in line_cells(plan, a, 0, plan.R * 2):
            if not plan.ok(x, y) or plan.cell[y][x] in FORT or not plan.inside[y][x]:
                break
            cells.append((x, y))
        carve(plan, cells, STREET, over=(None, STREET), mark=plan.main)


def ring_street(plan, mask, inner=1.2):
    """The street that runs along the inside of the walls."""
    fort = [(x, y) for x, y in mask if plan.cell[y][x] in FORT]
    dist = distance_field(plan, fort, passable=lambda x, y: (x, y) in mask, limit=inner + 1)
    for x, y in mask:
        if plan.cell[y][x] is None and dist[y][x] <= inner + 0.2:
            plan.cell[y][x] = STREET


def inner_ring(plan, pts, scale):
    """A ring street on a smaller copy of the walls: the line of the old walls."""
    small = [(plan.cx + (x - plan.cx) * scale, plan.cy + (y - plan.cy) * scale) for x, y in pts]
    mask = polygon_mask(plan, small)
    for x, y in ring_of(mask):
        if plan.ok(x, y) and plan.inside[y][x] and plan.cell[y][x] is None and (x - 1, y) in mask | ring_of(mask):
            if all(plan.cell[y][x + dx] is None or plan.cell[y][x + dx] in (STREET, SQUARE)
                   for dx in (0,) if plan.ok(x + dx, y)):
                plan.cell[y][x] = STREET


def grid_streets(plan, rng, gx, gy):
    """A grid of streets every gx columns and gy rows inside the walls (planned new towns)."""
    cx, cy = int(plan.cx), int(plan.cy)
    for y in range(plan.H):
        if (y - cy) % gy == 0:
            for x in range(plan.W):
                if plan.inside[y][x] and plan.cell[y][x] is None:
                    plan.cell[y][x] = STREET
    for x in range(plan.W):
        if (x - cx) % gx == 0:
            for y in range(plan.H):
                for xx in (x, x + 1):
                    if plan.ok(xx, y) and plan.inside[y][xx] and plan.cell[y][xx] is None:
                        plan.cell[y][xx] = STREET


def lanes(plan, rng, maxd, tries=60):
    """Alleys: while some spot is too far from any street, cut a lane through it."""
    def region(x, y):
        """Free cells inside the walls, where a lane may run."""
        return plan.inside[y][x] and plan.cell[y][x] is None and not plan.is_water(x, y)
    # each round: find the free spot farthest from any street
    for _ in range(tries):
        src = [(x, y) for y in range(plan.H) for x in range(plan.W)
               if plan.inside[y][x] and plan.cell[y][x] in (STREET, SQUARE)]
        dist = distance_field(plan, src, passable=region)
        far, dmax = None, maxd
        for y in range(plan.H):
            for x in range(plan.W):
                if region(x, y) and dist[y][x] < INF and dist[y][x] > dmax:
                    far, dmax = (x, y), dist[y][x]
        if far is None:
            break
        # walk downhill on the distance field from that spot to the nearest street
        path, (x, y) = [far], far
        while dist[y][x] > 0:
            nxt = min(((x + dx, y + dy) for dx, dy in DIRS4 if plan.ok(x + dx, y + dy)),
                      key=lambda c: dist[c[1]][c[0]])
            if dist[nxt[1]][nxt[0]] >= dist[y][x]:
                break
            x, y = nxt
            path.append((x, y))
        # then wander on from the spot the other way, turning now and then, until another street: a lane through,
        # not a dead end (dropped if it runs into anything else)
        first = (path[1][0] - far[0], path[1][1] - far[1]) if len(path) > 1 else rng.choice(DIRS4)
        back, (x, y) = [], far
        d = (-first[0], -first[1])
        for _ in range(80):
            if rng.random() < 0.15:
                d = rng.choice([(d[1], d[0]), (-d[1], -d[0]), d])
            x, y = x + d[0], y + d[1]
            if not plan.ok(x, y):
                back = []
                break
            if plan.cell[y][x] in (STREET, SQUARE):
                break
            if not region(x, y):
                back = []
                break
            back.append((x, y))
        carve(plan, path + back, STREET, wide=False)


# --- buildings ---
def rect_ok(plan, x0, y0, w, h, region, gap=(1, 1)):
    """Whether a w x h building fits at x0, y0: on the map, on free cells of `region`, and `gap` cells away from
    other buildings."""
    if x0 < 1 or y0 < 1 or x0 + w > plan.W - 1 or y0 + h > plan.H - 1:
        return False
    for y in range(y0, y0 + h):
        for x in range(x0, x0 + w):
            if not region(x, y):
                return False
    gx, gy = gap
    for y in range(max(0, y0 - gy), min(plan.H, y0 + h + gy)):
        for x in range(max(0, x0 - gx), min(plan.W, x0 + w + gx)):
            if plan.bmap[y][x] >= 0:
                return False
    return True


def add_building(plan, kind, x0, y0, w, h, door, stone, outside=False):
    """Put a building on the plan: listed, and its cells marked in bmap and cell."""
    b = Building(kind, x0, y0, w, h, door, stone, outside)
    k = len(plan.buildings)
    plan.buildings.append(b)
    for x, y in b.cells():
        plan.bmap[y][x] = k
        plan.cell[y][x] = BLDG
    return b


def rect_on_front(x, y, dx, dy, w, h, rng):
    """A w x h building whose side touches the street at (x, y): the door."""
    if dy == -1:
        return x - rng.randint(1, w - 2), y
    if dy == 1:
        return x - rng.randint(1, w - 2), y - h + 1
    if dx == -1:
        return x, y - rng.randint(1, max(1, h - 2))
    return x - w + 1, y - rng.randint(1, max(1, h - 2))


def fronts(plan, region, open_kinds):
    """Cells of `region` next to an open cell (street, square...), with the direction of the opening: where a door
    can go."""
    out = []
    for y in range(1, plan.H - 1):
        for x in range(1, plan.W - 1):
            if region(x, y):
                for dx, dy in DIRS4:
                    if plan.cell[y + dy][x + dx] in open_kinds:
                        out.append((x, y, dx, dy))
    return out


def wall_backs(plan, region):
    """Free cells along the inside of a wall: buildings lean on it."""
    out = []
    for y in range(1, plan.H - 1):
        for x in range(1, plan.W - 1):
            if region(x, y):
                for dx, dy in DIRS4:
                    if plan.cell[y + dy][x + dx] in FORT:
                        out.append((x, y, dx, dy))
    return out


def opposite_door(x0, y0, w, h, dx, dy):
    """The door on the side away from the wall."""
    if dy == -1:
        return x0 + w // 2, y0 + h - 1
    if dy == 1:
        return x0 + w // 2, y0
    if dx == -1:
        return x0 + w - 1, y0 + h // 2
    return x0, y0 + h // 2


def is_stone(kind, era):
    """Whether a building of this kind is of stone in this era (some are always, some only after the Early Middle
    Ages)."""
    s = kind.get("stone", "late")
    return s == "always" or (s == "late" and era != "early")


class Fields:
    """The distance fields buildings are placed by."""

    def __init__(self, plan):
        """Distance fields of a plan, computed when first asked for."""
        self.plan = plan
        self.cache = {}

    def get(self, name):
        """The distance of every cell from the gates, walls, water or main streets (by `name`), computed once and
        kept."""
        if name in self.cache:
            return self.cache[name]
        plan = self.plan
        if name == "gate":
            src = [g["inner"] for g in plan.gates if g["inner"]] or [(int(plan.cx), int(plan.cy))]
        elif name == "fort":
            src = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.cell[y][x] in FORT]
        elif name == "water":
            src = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.is_water(x, y)]
        elif name == "main":
            src = list(plan.main) or [(int(plan.cx), int(plan.cy))]
        elif name == "square":
            src = list(getattr(plan, "square", ())) or [(int(plan.cx), int(plan.cy))]
        else:
            src = [(int(plan.cx), int(plan.cy))]
        field = distance_field(plan, src) if src else [[INF] * plan.W for _ in range(plan.H)]
        self.cache[name] = field
        return field


SUMMIT_KINDS = ("rocca", "lords_hall", "palace", "palazzo", "cathedral", "basilica", "church", "keep")


def place_one(plan, rng, kind, era, fields, region, mode, place, outside=False, gap=(1, 1), size=None,
              keep_clear=None):
    """Find the best spot for one building; None if there is no room."""
    w0, w1 = kind["w"]
    h0, h1 = kind["h"]
    # try two random sizes, then the smallest
    sizes = [size] if size else []
    sizes += [(rng.randint(w0, w1), rng.randint(h0, h1)) for _ in range(2)] + [(w0, h0)]
    stone = is_stone(kind, era)
    # anchors: the cells a building may lean on (the back of the walls, or street fronts); none when it may go
    # anywhere
    if mode == "wall":
        anchors = wall_backs(plan, region)
    elif mode == "free":
        anchors = []
    else:
        anchors = fronts(plan, region, OPEN)
    rng.shuffle(anchors)
    anchors = anchors[:700]
    centre = fields.get("centre")
    free_cells = None
    for w, h in sizes:
        best, best_score = None, -INF
        candidates = []
        if mode == "free":
            if free_cells is None:
                free_cells = [(x, y) for y in range(1, plan.H - 1) for x in range(1, plan.W - 1) if region(x, y)]
            for x0, y0 in rng.sample(free_cells, min(600, len(free_cells))):
                candidates.append((x0, y0, None, None))
        else:
            for x, y, dx, dy in anchors:
                x0, y0 = rect_on_front(x, y, dx, dy, w, h, rng)
                door = opposite_door(x0, y0, w, h, dx, dy) if mode == "wall" else (x, y)
                candidates.append((x0, y0, door, (x + dx, y + dy)))
        # score every spot that fits: a little chance, plus how close it is to where this kind belongs
        for x0, y0, door, street in candidates:
            if not rect_ok(plan, x0, y0, w, h, region, gap):
                continue
            if keep_clear and any((x, y) in keep_clear for y in range(y0 - 1, y0 + h + 1)
                                  for x in range(x0 - 1, x0 + w + 1)):
                continue
            mx, my = int(x0 + w / 2), int(y0 + h / 2)
            score = rng.random() * 2
            if plan.height and (kind.get("keep") or kind["id"] in SUMMIT_KINDS):
                score += plan.height[my][mx] * 40       # perched: up at the top
            if place == "square":
                score += 12 if street and plan.cell[street[1]][street[0]] == SQUARE else 0
                score -= fields.get("square")[my][mx] * 0.6
            elif place == "main":
                score += 6 if street and street in plan.main else 0
                score -= centre[my][mx] * 0.15
            elif place == "gate":
                score -= fields.get("gate")[my][mx] * 0.8
            elif place == "wall":
                score -= fields.get("fort")[my][mx] * 1.2
            elif place in ("river", "shore"):
                score -= fields.get("water")[my][mx] * 1.5
            elif place == "outside":
                score -= abs(centre[my][mx] - plan.R * 1.45) * 0.5
            elif place in ("keep", "centre"):
                score -= centre[my][mx] * 1.0
                if place == "keep":
                    score += fields.get("gate")[my][mx] * 0.5
            if score > best_score:
                best, best_score = (x0, y0, door), score
        # build on the best spot; a free-standing one must be reachable by an alley
        if best:
            x0, y0, door = best
            if door is None:
                door = nearest_door(plan, x0, y0, w, h)
            b = add_building(plan, kind, x0, y0, w, h, door, stone, outside)
            if mode == "free" and not connect(plan, b, region):
                unplace(plan, b)
                continue
            return b
    if mode == "front":
        # no street front left: a free spot, and an alley from its door to the nearest street
        return place_one(plan, rng, kind, era, fields, region, "free", place, outside, gap, size, keep_clear)
    return None


def door_out(b):
    """The cell just outside the door."""
    x, y = b.door
    if y == b.y0:
        return x, y - 1
    if y == b.y0 + b.h - 1:
        return x, y + 1
    if x == b.x0:
        return x - 1, y
    return x + 1, y


def connect(plan, b, region):
    """An alley (or a track, outside the walls) from the door to the nearest street or road."""
    start = door_out(b)
    if not plan.ok(*start):
        return False
    if plan.cell[start[1]][start[0]] in OPEN:
        return True
    if not region(*start):
        # try the other sides
        for door in ((b.x0 + b.w // 2, b.y0), (b.x0 + b.w // 2, b.y0 + b.h - 1),
                     (b.x0, b.y0 + b.h // 2), (b.x0 + b.w - 1, b.y0 + b.h // 2)):
            b.door = door
            start = door_out(b)
            if plan.ok(*start) and (plan.cell[start[1]][start[0]] in OPEN or region(*start)):
                break
        else:
            return False
        if plan.cell[start[1]][start[0]] in OPEN:
            return True
    kind = ROAD if b.outside else STREET

    def cost(x, y):
        """The cost of a cell for a connecting lane: free on open cells, else only in `region`."""
        if plan.cell[y][x] in OPEN:
            return 1.0
        return 1.0 if region(x, y) else None
    path = route(plan, start, lambda x, y: plan.cell[y][x] in OPEN, cost)
    if not path or len(path) > plan.R * 4:
        return False
    carve(plan, [start] + path[:-1], kind, wide=False)
    return True


def nearest_door(plan, x0, y0, w, h):
    """A door on the side facing the centre."""
    mx, my = x0 + w / 2, y0 + h / 2
    dx, dy = (plan.cx - mx) / ASPECT, plan.cy - my
    if abs(dx) > abs(dy):
        return (x0 + w - 1, y0 + h // 2) if dx > 0 else (x0, y0 + h // 2)
    return (x0 + w // 2, y0 + h - 1) if dy > 0 else (x0 + w // 2, y0)


def region_in(plan):
    """Free land cells inside the walls."""
    return lambda x, y: plan.inside[y][x] and plan.cell[y][x] is None and not plan.is_water(x, y)


def region_out(plan, near=None):
    """Free land cells outside the walls (grass, trees, hills), within `near` of the centre if given."""
    def region(x, y):
        """Whether x, y is free open land outside the walls (and near enough)."""
        if plan.inside[y][x] or plan.cell[y][x] is not None or plan.ground[y][x] not in ("grass", "tree", "shroom", "hill"):
            return False
        return near is None or vdist(x, y, plan.cx, plan.cy) <= near
    return region


def fill_houses(plan, rng, kind, era, region, sizes, gap, limit=None, opens=OPEN, outside=False):
    """Houses along the streets: narrow fronts, deep plots, as far as there's room."""
    added = []
    for _ in range(3):
        anchors = fronts(plan, region, opens)
        rng.shuffle(anchors)
        for x, y, dx, dy in anchors:
            if limit is not None and len(added) >= limit:
                return added
            if not region(x, y):
                continue
            (w0, w1), (h0, h1) = sizes
            for w, h in ((rng.randint(w0, w1), rng.randint(h0, h1)), (w0, h0)):
                x0, y0 = rect_on_front(x, y, dx, dy, w, h, rng)
                if rect_ok(plan, x0, y0, w, h, region, gap):
                    added.append(add_building(plan, kind, x0, y0, w, h, (x, y), is_stone(kind, era), outside))
                    break
    return added


def infill(plan, rng, p, kind, misses=10):
    """The blocks left empty: more houses, each with an alley to the street."""
    fieldset = Fields(plan)
    region = region_in(plan)
    fails = 0
    while fails < misses:
        b = place_one(plan, rng, kind, p["era"], fieldset, region, "free", "any", gap=(1, 1))
        if b is None:
            fails += 3
        else:
            fails = 0 if rng.random() < 0.9 else fails + 1
        fails += 0


def cemetery(plan, rng, church):
    """A graveyard beside the church."""
    sides = []
    for _ in range(40):
        w, h = rng.randint(6, 10), rng.randint(2, 3)
        side = rng.choice("NSEW")
        if side == "N":
            x0, y0 = church.x0 + rng.randint(0, max(0, church.w - w)), church.y0 - h - 1
        elif side == "S":
            x0, y0 = church.x0 + rng.randint(0, max(0, church.w - w)), church.y0 + church.h + 1
        elif side == "W":
            x0, y0 = church.x0 - w - 2, church.y0 + rng.randint(0, max(0, church.h - h))
        else:
            x0, y0 = church.x0 + church.w + 2, church.y0 + rng.randint(0, max(0, church.h - h))
        cells = [(x, y) for y in range(y0, y0 + h) for x in range(x0, x0 + w)]
        if all(plan.ok(x, y) and plan.cell[y][x] is None and not plan.is_water(x, y)
               and plan.inside[y][x] == plan.inside[church.y0][church.x0] for x, y in cells):
            sides.append(cells)
            break
    for cells in sides:
        for x, y in cells:
            plan.cell[y][x] = GRAVE
        return True
    return False


# --- the countryside ---
FIELD_WEIGHTS = {  # plough, sown, pasture, orchard, fallow
    "plains": (4, 4, 2, 1, 1), "river": (4, 3, 3, 1, 1), "coast": (2, 3, 3, 2, 1), "lake": (3, 3, 3, 1, 1),
    "hills": (2, 2, 2, 4, 1), "mountains": (1, 1, 5, 1, 2), "forest": (2, 2, 3, 1, 2), "swamp": (1, 1, 5, 0, 3),
    "fungus": (1, 1, 3, 0, 3)}
FIELD_KINDS = ("plough", "sown", "pasture", "orchard", "fallow")


def fields(plan, rng, terrain, reach):
    """Strips and patches of fields around the settlement, each with its crop."""
    far = reach * rng.uniform(2.0, 2.6)
    seeds = []
    for _ in range(int(far * far * 0.35) + 10):
        a, r = rng.uniform(0, 2 * math.pi), rng.uniform(reach * 0.6, far)
        x, y = ray(plan.cx, plan.cy, a, r)
        seeds.append((x, y, rng.choices(FIELD_KINDS, weights=FIELD_WEIGHTS[terrain])[0]))
    for y in range(plan.H):
        for x in range(plan.W):
            if plan.ground[y][x] != "grass" or plan.inside[y][x] or plan.cell[y][x] is not None:
                continue
            d = vdist(x, y, plan.cx, plan.cy)
            if d > far * (0.75 + 0.4 * plan.n1[y][x]):
                continue
            kind = min(seeds, key=lambda s: (s[0] - x) ** 2 / 4 + (s[1] - y) ** 2)[2]
            plan.ground[y][x] = "field:" + kind


HAIRPIN_WIDTH = (3.5, 5.0)  # mountain roads: how far each hairpin leg swings to the side (visual units)
HAIRPIN_DROP = (2.5, 3.5)   # ... and how far down it goes
CLIFF_BAND = 3.2           # mountains: how far below the settlement the cliffs go (visual units)
CLIFF_OPEN = 1.05          # ... except within this angle of the way up (radians)
STAIR_GRADE = 0.9         # a street steeper than this (in plan.grade) is a flight of steps


def hairpins(plan, start, angle, rng, cost):
    """A perched settlement's road: from `start` down the mountain along `angle` to the edge of the map, in hairpin
    bends (legs that cross the slope, left and right, as they go down); each leg the cheapest way between its
    bends. Returns the cells, or None."""
    ux, uy = math.cos(angle), math.sin(angle)
    vx, vy = -uy, ux
    width, drop = rng.uniform(*HAIRPIN_WIDTH), rng.uniform(*HAIRPIN_DROP)
    side = rng.choice((-1, 1))
    bends, k = [], 1
    while True:
        x = start[0] + (ux * k * drop + vx * width * side) * ASPECT
        y = start[1] + uy * k * drop + vy * width * side
        if not plan.ok(int(x), int(y)):
            break
        bends.append((int(x), int(y)))
        side, k = -side, k + 1
    path, at = [start], start
    for bend in bends:
        leg = route(plan, at, lambda x, y, b=bend: (x, y) == b, cost, target=bend)
        if leg:
            path += leg[1:]
            at = bend
    t = 0
    while plan.ok(*map(int, ray(at[0], at[1], angle, t))):
        t += 0.5
    ex, ey = ray(at[0], at[1], angle, t - 0.5)
    end = (max(0, min(plan.W - 1, int(ex))), max(0, min(plan.H - 1, int(ey))))
    leg = route(plan, at, lambda x, y: (x in (0, plan.W - 1) or y in (0, plan.H - 1)) and vdist(x, y, *end) < 8,
                cost, target=end)
    return path + leg[1:] if leg else (path if len(path) > 1 else None)


def roads_out(plan, rng):
    """From every gate (or across a village) to the edge of the map."""
    def cost(x, y):
        """The cost of a cell for a country road: cheap on roads, dear on hills, forest and water, impossible across
        walls and buildings."""
        if plan.inside[y][x]:
            return None
        c = plan.cell[y][x]
        if c in FORT or c == BLDG:
            return None
        if c in (ROAD, BRIDGE):
            return 0.5
        g = plan.ground[y][x]
        base = {"grass": 1.0, "tree": 2.5, "shroom": 2.5, "hill": 1.7, "mount": 5.0, "reed": 2.0, "water": 7.0}.get(g, 1.0)
        if c in (DITCH, MOAT):
            base = 2.0
        return base * (1 + plan.n2[y][x])
    # from each gate, a road to the map's edge in the gate's direction, the cheapest way round woods and hills
    # (in the mountains, down hairpin bends); bridges over water and ditches
    for gate in plan.gates:
        if gate["outer"] is None:
            continue
        a = gate["angle"]
        t = 0
        while True:
            x, y = ray(plan.cx, plan.cy, a, t)
            if not plan.ok(int(x), int(y)):
                break
            t += 0.5
        tx, ty = ray(plan.cx, plan.cy, a, t - 0.5)
        target = (max(0, min(plan.W - 1, int(tx))), max(0, min(plan.H - 1, int(ty))))

        def goal(x, y, target=target):
            edge = x in (0, plan.W - 1) or y in (0, plan.H - 1)
            return edge and vdist(x, y, *target) < 8

        if plan.height:
            path = hairpins(plan, gate["outer"], a, rng, cost)
        else:
            path = route(plan, gate["outer"], goal, cost, target=target)
        if path:
            carve(plan, path, ROAD, over=(None, DITCH, MOAT, ROAD))
            for x, y in path:
                if plan.cell[y][x] in (DITCH, MOAT) or plan.is_water(x, y):
                    plan.cell[y][x] = BRIDGE


def village_roads(plan, rng, n):
    """Roads that cross the village: in from one edge, through the green, out of another."""
    def cost(x, y):
        """The cost of a cell for an unwalled village's roads: like the country roads, but streets and squares are
        cheap too."""
        c = plan.cell[y][x]
        if c == BLDG:
            return None
        if c in (ROAD, STREET, SQUARE, BRIDGE):
            return 0.5
        g = plan.ground[y][x]
        base = {"grass": 1.0, "tree": 2.5, "shroom": 2.5, "hill": 1.7, "mount": 5.0, "reed": 2.0, "water": 7.0}.get(g, 1.0)
        return base * (1 + plan.n2[y][x])
    angles = gate_angles(plan, plan.mask, n, rng)
    for a in angles:
        t = 0
        while plan.ok(*map(int, ray(plan.cx, plan.cy, a, t))):
            t += 0.5
        x, y = ray(plan.cx, plan.cy, a, t - 0.5)
        start = (max(0, min(plan.W - 1, int(x))), max(0, min(plan.H - 1, int(y))))
        path = route(plan, start, lambda x, y: (x, y) in plan.square, cost, target=(plan.cx, plan.cy))
        if path and plan.height:
            # perched: the road climbs in hairpin bends up to where it enters the village
            entry = next((k for k, (x, y) in enumerate(path) if plan.inside[y][x]), None)
            if entry:
                down = hairpins(plan, path[entry], a, rng, cost)
                if down:
                    path = down[::-1] + path[entry + 1:]
                    start = path[0]
        if path:
            for x, y in path:
                kind = STREET if plan.inside[y][x] else ROAD
                if plan.is_water(x, y):
                    kind = BRIDGE
                if plan.cell[y][x] is None:
                    plan.cell[y][x] = kind
                    if kind == STREET:
                        plan.main.add((x, y))
            plan.gates.append({"angle": a, "cells": [], "inner": None, "outer": start, "road_only": True})


def pier(plan, rng):
    """A pier from the shore into the water, near the town."""
    water = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.is_water(x, y)]
    if not water or plan.water_side is None:
        return False
    sx, sy = plan.water_side
    best = None
    for x, y in water:
        for dx, dy in DIRS4:
            nx, ny = x + dx, y + dy
            if plan.ok(nx, ny) and not plan.is_water(nx, ny) and plan.cell[ny][nx] in (ROAD, STREET, None, BRIDGE):
                d = vdist(x, y, plan.cx, plan.cy)
                if best is None or d < best[0]:
                    best = (d, x, y)
    if not best:
        return False
    _, x, y = best
    length = rng.randint(5, 8)
    for k in range(length):
        px, py = x + sx * k * (2 if sx else 1), y + sy * k
        for ex in ((0, 1) if not sx else (0,)):
            cx, cy = px + ex, py
            if plan.ok(cx, cy) and plan.is_water(cx, cy):
                plan.cell[cy][cx] = PIER
            if sx and plan.ok(cx + sx, cy) and plan.is_water(cx + sx, cy):
                plan.cell[cy][cx + sx] = PIER
    plan.harbour = True
    return True


# --- what goes into a settlement ---
def building_list(p, rng):
    """Which buildings, and how many: by their support value (one business for
    every so many people, Medieval Demographics Made Easy) or a fixed count."""
    kind, era, terrain = p["type"], p["era"], p["terrain"]
    t = type_span(p)
    out, wanted = [], {}
    # every kind of building this type, era and terrain allow
    for spec in BUILDINGS:
        if spec.get("filler") or not allowed_in(spec["types"], kind):
            continue
        if spec.get("eras") and era not in spec["eras"]:
            continue
        if spec.get("terrains") and terrain not in spec["terrains"] or terrain in spec.get("deny", ()):
            continue
        count = spec.get("count", {})
        fixed = count.get(kind, count.get(building_type(kind)))
        # a fixed count (one cathedral...), more of them in bigger places
        if fixed is not None:
            lo, hi = span(fixed)
            n = max(lo, min(hi, lo + round((hi - lo) * t + rng.uniform(-0.45, 0.45))))
            real = n
        # or one every `sv` people, give or take, with a minimum and a cap
        elif "sv" in spec:
            sv = spec["sv"] * (1 + (roll("4d4", rng) - 6) / 10)
            expected = p["pop"] / sv
            real = int(expected) + (1 if rng.random() < expected - int(expected) else 0)
            mins = spec.get("min", {})
            real = max(real, mins.get(kind, mins.get(building_type(kind), 0)))
            caps = spec.get("cap", {})
            cap = caps.get(kind, caps.get(building_type(kind), 0))
            n = min(real, cap)
        else:
            continue
        if n > 0:
            out += [spec] * n
            wanted[spec["id"]] = (n, real)
    # a place of rest always has somewhere to sleep or drink
    if p["purpose"] == "rest" and not any(s.get("rest") in ("lodging", "tavern") for s in out):
        spec = BUILDING["inn" if kind not in ("village", "fortress") else "tavern"]
        out.append(spec)
        wanted[spec["id"]] = (1, 1)
    # the most important first: they get the best spots
    out.sort(key=lambda s: -s.get("priority", 0))
    return out, wanted


def where_to(spec, plan, ward):
    """(region kind, mode, place) for a building."""
    place = spec.get("place", "any")
    if place in ("river", "shore") and not plan.water:
        place = "wall" if spec["id"] in ("tannery", "dyers") else "outside" if spec["id"] == "mill" else "main"
    if ward:
        if place in ("main", "square", "gate") and spec["id"] in ("inn", "tavern"):
            place = "outside"
        elif place in ("square", "main", "river", "shore", "any"):
            place = "wall"
    if place == "outside":
        return "out", "front", place
    if place in ("river", "shore"):
        return "both", "front", place
    if place in ("keep", "centre", "motte"):
        return "in", "free", place
    if ward and place == "wall":
        return "in", "wall", place
    return "in", "front", place


def place_list(plan, rng, p, specs, ward=False, keep_clear=None, gap=(1, 1)):
    """Place the buildings of `specs` one by one where each belongs (inside, outside, by a gate, on the square...);
    returns those placed and a count of those that found no room."""
    fieldset = Fields(plan)
    placed, missing = [], Counter()
    for spec in specs:
        region_kind, mode, place = where_to(spec, plan, ward)
        if place == "motte":
            continue
        # outside the walls (mills, farms...)
        if region_kind == "out":
            region = region_out(plan, near=plan.R * 2.2)
            b = place_one(plan, rng, spec, p["era"], fieldset, region, mode, place, outside=True, gap=(2, 1))
        # inside if there is room near the water, else outside, else anywhere on a main street
        elif region_kind == "both":
            b = place_one(plan, rng, spec, p["era"], fieldset, region_in(plan), mode, place, gap=gap,
                          keep_clear=keep_clear)
            if b is None or fieldset.get("water")[int(b.y0)][int(b.x0)] > plan.R * 0.6:
                if b is not None:
                    unplace(plan, b)
                b = place_one(plan, rng, spec, p["era"], fieldset, region_out(plan, near=plan.R * 2.4), mode,
                              place, outside=True, gap=(2, 1))
                if b is None:
                    b = place_one(plan, rng, spec, p["era"], fieldset, region_in(plan), "front", "main", gap=gap,
                                  keep_clear=keep_clear)
        else:
            b = place_one(plan, rng, spec, p["era"], fieldset, region_in(plan), mode, place, gap=gap,
                          keep_clear=keep_clear)
            # against the walls if possible, else anywhere free
            if b is None and mode == "wall":
                b = place_one(plan, rng, spec, p["era"], fieldset, region_in(plan), "free", "any", gap=gap,
                              keep_clear=keep_clear)
        if b is None:
            missing[spec["id"]] += 1
            continue
        placed.append(b)
        if spec.get("cemetery"):
            cemetery(plan, rng, b)
    return placed, missing


def unplace(plan, b):
    """Take a building off the plan and renumber the others in bmap."""
    for x, y in b.cells():
        plan.bmap[y][x] = -1
        plan.cell[y][x] = None
    plan.buildings.remove(b)
    for k, other in enumerate(plan.buildings):
        for x, y in other.cells():
            plan.bmap[y][x] = k


# --- the layouts ---
def layout_for(p, rng):
    """How this settlement is built: shape, walls, streets."""
    kind, era = p["type"], p["era"]
    t = type_span(p)
    # the defaults: an unwalled, organic blob; each type and era changes them
    lay = {"walls": None, "towers": False, "shape": "blob", "streets": "organic", "gates": 0, "ring": False,
           "inner_ring": False, "moat": None, "reach": 1.0, "square": (6, 2), "lanes": 5.0, "wobble": 0.14}
    wet = p["terrain"] in ("river", "lake", "coast", "swamp")
    # villages: no walls (a palisade sometimes in the Early Middle Ages), roads instead of streets
    if kind == "village":
        lay.update(streets="village", square=(5, 2), lanes=None, wobble=0.22, gates=2 + (t > 0.5) + (rng.random() < 0.3))
        if era == "early" and rng.random() < 0.4:
            lay.update(walls=PALISADE, moat="dry")
    # towns: walls more often than not; planned new towns on a grid, or along one street
    elif kind == "town":
        walled = rng.random() < {"early": 0.75, "late": 0.7, "renaissance": 0.6}[era] or p["purpose"] == "adventure"
        lay.update(gates=2 + (t > 0.4) + (t > 0.8), square=(7, 2), lanes=5.0)
        if era == "early":
            lay.update(walls=PALISADE if walled else None, moat="dry" if walled else None)
        else:
            lay.update(walls=WALL if walled else None, towers=walled, moat=("water" if wet else "dry") if walled else None)
            if rng.random() < 0.45:
                lay.update(streets="grid", shape="rect" if rng.random() < 0.6 else "blob", lanes=None)
            elif rng.random() < 0.5:
                lay.update(streets="linear")
        lay["ring"] = walled and era != "early" and rng.random() < 0.5
    # cities: Roman grid in the Early Middle Ages, organic in the Late, bastioned and radial or gridded in the
    # Renaissance
    elif kind in ("city", "bigcity"):
        big = kind == "bigcity"
        lay.update(walls=WALL, towers=True, gates=(4 + round(t * 2)) if big else (3 + (t > 0.5)),
                   square=(10, 3) if big else (8, 3), lanes=4.6 if big else 4.8,
                   moat="water" if wet or rng.random() < 0.4 else "dry")
        if era == "early":
            lay.update(shape="roman", streets="roman", ring=False)
        elif era == "late":
            lay.update(shape="blob", streets="organic", ring=rng.random() < 0.6, inner_ring=rng.random() < 0.55)
        else:
            lay.update(shape="bastioned", towers=False, reach=1.32, ring=True,
                       streets="radial" if rng.random() < 0.55 else "grid", lanes=None if rng.random() < 0.5 else 5.2)
    # castles: motte and bailey, then stone castles, then the Renaissance rocca
    elif kind == "castle":
        lay.update(gates=1, moat="water" if wet or rng.random() < 0.35 else "dry")
        if era == "early":
            lay.update(shape="motte", walls=PALISADE, reach=1.35, moat="water" if wet else "dry")
        elif era == "late":
            lay.update(shape="castle", walls=WALL, towers=True, inner=t > 0.55 or rng.random() < 0.25)
        else:
            lay.update(shape="rocca", walls=WALL, towers=False, reach=1.3, moat="water" if wet or rng.random() < 0.6 else "dry")
    # fortresses: Roman castrum, stone fortress, star fort
    elif kind == "fortress":
        if era == "early":
            lay.update(shape="castrum", walls=WALL, towers=True, gates=4, moat="dry")
        elif era == "late":
            lay.update(shape="castle", walls=WALL, towers=True, gates=1 + (t > 0.6), inner=t > 0.45,
                       moat="water" if wet else "dry")
        else:
            lay.update(shape="star", walls=WALL, towers=False, gates=1 + (t > 0.5), reach=1.4,
                       moat="water" if wet else "dry")
    return lay


def settlement_scale(p, rng, R):
    """Metres in a row of letters, from the population and the density of
    Medieval Demographics Made Easy (people per hectare: 7d4, the two highest
    dropped, times 15)."""
    if p["type"] in WARD_ROW_M:
        return WARD_ROW_M[p["type"]], None, None
    d = DEMOGRAPHICS["density"]
    dice = sorted(rng.randint(1, 4) for _ in range(7))[:d["keep"]]
    density = sum(dice) * d["times"]
    if p["type"] == "village":
        density = max(10, round(density * DEMOGRAPHICS["village_density_factor"]))
    hectares = p["pop"] / density
    radius_m = math.sqrt(hectares * 10000 / math.pi)
    return radius_m / R, density, hectares


def build_plan(p, seed):
    """The whole map, from the seed."""
    rng = random.Random(f"wyrmurbigen-map-{seed}")
    kind = p["type"]
    t = type_span(p)
    lo, hi = RADIUS[kind]
    R = lo + (hi - lo) * t
    lay = layout_for(p, rng)
    if p["terrain"] == "mountains":
        lay["moat"] = None          # perched: the cliffs are the moat
    if p["terrain"] == "underground":     # below, the rock is the wall: only castles and fortresses keep theirs
        lay["moat"] = None
        if kind not in ("castle", "fortress"):
            lay.update(walls=None, towers=False)
    W = int(R * 2 * ASPECT * (1.55 + 0.35 * lay["reach"])) + 14
    H = int(R * 2 * (1.12 + 0.18 * lay["reach"])) + 8
    plan = Plan(W, H, rng)
    plan.R = R
    plan.cx = W / 2 + rng.uniform(-2, 2)
    plan.cy = H / 2 + rng.uniform(-1, 1)
    plan.row_m, plan.density, plan.hectares = settlement_scale(p, rng, R)
    plan.lay = lay
    environment(plan, p, rng, R * lay["reach"])
    if kind in ("castle", "fortress"):
        build_ward(plan, p, rng, lay)
    else:
        build_town(plan, p, rng, lay)
    if p["terrain"] == "fungus":    # among the giant mushrooms only temples, palaces and walls are of stone
        for b in plan.buildings:
            if b.kind.get("stone", "late") == "late":
                b.stone = False
    if p["terrain"] == "underground":     # below, everything is carved into the rock
        for b in plan.buildings:
            b.stone = b.carved = True
    finish(plan, p, rng)
    if p["terrain"] == "underground":
        dig_out(plan, random.Random(f"wyrmurbigen-deep-{seed}"))
    return plan


def dig_out(plan, rng):
    """Below: what was built, and a margin round it, is dug out of the rock; around it lie a few natural caverns
    (cave floor, giant fungi, moss, a black lake, a little magma), each joined to the town by a crooked tunnel;
    the rest is solid rock. plan.face: the rock cells that touch open space, drawn as rock faces."""
    W, H, cfg = plan.W, plan.H, TERRAIN["underground"]["caverns"]
    mx, my = cfg["margin"]
    dug = [[False] * W for _ in range(H)]
    for y in range(H):
        for x in range(W):
            if plan.cell[y][x] is not None or (x, y) in plan.feat:
                for dy in range(-my, my + 1):
                    for dx in range(-mx, mx + 1):
                        if plan.ok(x + dx, y + dy):
                            dug[y + dy][x + dx] = True
    cave = [[False] * W for _ in range(H)]
    caverns = []
    wanted = rng.randint(*cfg["count"])
    for _ in range(wanted * 30):
        if len(caverns) >= wanted:
            break
        r = rng.uniform(*cfg["radius"])
        cx, cy = rng.uniform(r * ASPECT + 1, W - r * ASPECT - 2), rng.uniform(r + 1, H - r - 2)
        if cx < 1 or cy < 1 or any(vdist(cx, cy, ox, oy) < r + orad + 2 for ox, oy, orad in caverns):
            continue
        cells = [(x, y) for y in range(max(0, int(cy - r - 1)), min(H, int(cy + r + 2)))
                 for x in range(max(0, int(cx - r * ASPECT - 1)), min(W, int(cx + r * ASPECT + 2)))
                 if vdist(x, y, cx, cy) < r * (0.8 + 0.4 * plan.n1[y][x])]
        if not cells or any(dug[y][x] for x, y in cells):
            continue
        caverns.append((cx, cy, r))
        for x, y in cells:
            cave[y][x] = True
        # a crooked tunnel towards the town, until it reaches what was dug
        x, y = cx, cy
        for _ in range(W + H):
            ix, iy = int(round(x)), int(round(y))
            if not plan.ok(ix, iy) or dug[iy][ix]:
                break
            for dx in (0, 1):
                if plan.ok(ix + dx, iy):
                    cave[iy][ix + dx] = True
            a = math.atan2(plan.cy - y, (plan.cx - x) / ASPECT) + rng.uniform(-0.6, 0.6)
            x, y = x + math.cos(a) * ASPECT, y + math.sin(a)
    # what is in the caverns: a black lake in one, magma in another, giant fungi and moss everywhere
    kinds = {}
    for k, (cx, cy, r) in enumerate(caverns):
        roll = rng.random()
        kinds[k] = "water" if roll < cfg["lake"] else "magma" if roll < cfg["lake"] + cfg["magma"] else None
    for y in range(H):
        for x in range(W):
            if dug[y][x]:
                if plan.cell[y][x] is None and plan.ground[y][x] in ("grass", "tree"):
                    plan.ground[y][x] = "cave"
                continue
            if not cave[y][x]:
                plan.ground[y][x] = "rock"
                continue
            t = plan.tex[y][x]
            g = "cave"
            for k, (cx, cy, r) in enumerate(caverns):
                if kinds[k] and vdist(x, y, cx, cy) < r * 0.5 * (0.8 + 0.4 * plan.n2[y][x]):
                    g = kinds[k]
            if g == "cave":
                g = "shroom" if t < cfg["fungi"] else "moss" if t < cfg["fungi"] + cfg["moss"] else "cave"
            plan.ground[y][x] = g
    plan.face = {(x, y) for y in range(H) for x in range(W) if plan.ground[y][x] == "rock" and plan.cell[y][x] is None
                 and any(plan.ok(x + dx, y + dy) and (plan.ground[y + dy][x + dx] != "rock"
                                                      or plan.cell[y + dy][x + dx] is not None)
                         for dx in (-1, 0, 1) for dy in (-1, 0, 1))}


def shape_points(plan, p, rng, lay):
    """The outline of the walls for a layout: rectangle, Roman camp, blob, polygon, star fort...; returns the points
    and the corners where towers or bastions go."""
    R = plan.R
    shape = lay["shape"]
    corners = []
    if shape == "rect":
        hx, hy = R * rng.uniform(0.95, 1.15), R * rng.uniform(0.7, 0.85)
        pts = rect_shape(plan.cx, plan.cy, hx, hy)
        corners = pts
    elif shape == "roman":
        hx, hy = R * rng.uniform(0.95, 1.1), R * rng.uniform(0.75, 0.9)
        pts = rect_shape(plan.cx, plan.cy, hx, hy)
        # the medieval town spilled out of the Roman square on one side
        side = rng.choice((0, 1, 2, 3))
        a, b = pts[side], pts[(side + 1) % 4]
        mid = ((a[0] + b[0]) / 2, (a[1] + b[1]) / 2)
        out = ((mid[0] - plan.cx) * 0.35, (mid[1] - plan.cy) * 0.35)
        bulge = (mid[0] + out[0], mid[1] + out[1])
        pts = pts[:side + 1] + [bulge] + pts[side + 1:]
        corners = pts
    elif shape == "bastioned":
        n = 6 + round(type_span(p) * 2) + (2 if p["type"] == "bigcity" else 0)
        pts, corners = bastioned_shape(plan.cx, plan.cy, R * 1.02, n, rng)
    else:
        stretch = 1.0
        if p["terrain"] == "mountains":
            stretch = rng.uniform(1.4, 1.8)
        elif p["terrain"] == "hills":
            stretch = rng.uniform(1.0, 1.3)
        pts = blob_shape(plan.cx, plan.cy, R, rng, wobble=lay["wobble"], stretch=stretch,
                         angle=rng.uniform(0, math.pi))
        pts = clip_to_land(plan, pts)
    return pts, corners


def build_town(plan, p, rng, lay):
    """Villages, towns and cities."""
    # the outline, and the cells inside it
    pts, corners = shape_points(plan, p, rng, lay)
    mask = clean_mask(plan, polygon_mask(plan, pts))
    plan.mask, plan.shape_pts = mask, pts
    set_inside(plan, mask)
    plan.wall_kind = {WALL: "stone", PALISADE: "palisade"}.get(lay["walls"])
    if lay["walls"]:
        # walls with towers, gates through them, a moat or ditch around
        plan.walled = True
        build_walls(plan, mask, lay["walls"], corners=corners if lay["towers"] else (),
                    spacing=7.5 if p["type"] != "town" else 9.0, towers=lay["towers"])
        prefer = None
        for a in gate_angles(plan, mask, lay["gates"], rng, prefer):
            carve_gate(plan, mask, a, flank=lay["towers"])
        if lay["moat"]:
            moat_around(plan, mask, MOAT if lay["moat"] == "water" else DITCH,
                        width=2.2 if lay["shape"] == "bastioned" else 1.3)
            plan.moat = lay["moat"]
    # the main square, then the streets of the layout
    hw, hh = lay["square"]
    make_square(plan, rng, hw + rng.randint(-1, 2), hh + rng.randint(0, 1), irregular=lay["streets"] != "grid")
    streets = lay["streets"]
    if lay["walls"]:
        if streets == "grid":
            grid_streets(plan, rng, rng.randint(14, 18), rng.randint(6, 7))
            main_streets(plan, rng, organic=False, straight=True)
        elif streets == "roman":
            grid_streets(plan, rng, rng.randint(16, 20), rng.randint(6, 8))
            main_streets(plan, rng, organic=True)
        elif streets == "radial":
            radial_streets(plan, [g["angle"] for g in plan.gates] +
                           [math.atan2(c[1] - plan.cy, (c[0] - plan.cx) / ASPECT) for c in corners])
            inner_ring(plan, pts, 0.55)
        else:
            main_streets(plan, rng, organic=True)
        if lay["inner_ring"]:
            inner_ring(plan, pts, 0.6)
        if lay["ring"]:
            ring_street(plan, mask)
        roads_out(plan, rng)
    else:
        # a village: roads meeting at the green
        village_roads(plan, rng, max(2, lay["gates"]))
    plan.layout = streets
    if p["terrain"] in ("coast", "lake"):
        pier(plan, rng)
    # the important buildings first, on the square and the main streets; then
    # the alleys run around them and the houses fill what is left
    specs, plan.wanted = building_list(p, rng)
    plan.missing = Counter()
    village = p["type"] == "village"
    gap = (2, 1) if village else (1, 1)
    placed, missing = place_list(plan, rng, p, specs, gap=gap)
    plan.missing.update(missing)
    if lay["walls"] and lay["lanes"]:
        lanes(plan, rng, lay["lanes"])
    elif not lay["walls"] and lay["lanes"] and not village:
        lanes(plan, rng, lay["lanes"] + 1)
    elif village:
        lanes(plan, rng, 7.5, tries=6)
    # houses fill the blocks left, and a few spill outside the walls
    house = BUILDING["house"]
    if village:
        fill_houses(plan, rng, house, p["era"], region_in(plan), ((5, 7), (3, 3)), (3, 1))
        outside = region_out(plan, near=plan.R * 2.0)
        fill_houses(plan, rng, house, p["era"], outside, ((5, 7), (3, 3)), (4, 2), limit=rng.randint(2, 5),
                    opens={ROAD}, outside=True)
    else:
        big = p["type"] in ("city", "bigcity")
        fill_houses(plan, rng, house, p["era"], region_in(plan), ((5, 8), (3, 4)) if big else ((5, 7), (3, 4)), (1, 1))
        infill(plan, rng, p, house)
        if p["era"] != "early" and plan.walled:
            outside = region_out(plan, near=plan.R * 1.6)
            fill_houses(plan, rng, house, p["era"], outside, ((5, 7), (3, 3)), (2, 1),
                        limit=rng.randint(3, 6 if big else 4), opens={ROAD}, outside=True)


def build_ward(plan, p, rng, lay):
    """Castles and fortresses: walls around a courtyard, buildings leaning on them."""
    R = plan.R
    shape = lay["shape"]
    corners = []
    keep_clear = set()
    plan.wall_kind = "palisade" if lay["walls"] == PALISADE else "stone"
    plan.walled = True
    # a motte and bailey is built apart; for the others, the outline of the walls by kind of ward
    if shape == "motte":
        build_motte(plan, p, rng, lay)
        return
    if shape == "castrum":
        hx, hy = R * rng.uniform(1.05, 1.2), R * rng.uniform(0.75, 0.85)
        pts = rect_shape(plan.cx, plan.cy, hx, hy)
        corners = pts
    elif shape == "rocca":
        pts, corners = bastioned_shape(plan.cx, plan.cy, R * 0.95, 4, rng, rotate=math.pi / 4)
    elif shape == "star":
        n = 4 + round(type_span(p) * 2)
        pts, corners = bastioned_shape(plan.cx, plan.cy, R, n, rng)
    else:
        n = rng.randint(5, 7)
        pts = polygon_shape(plan.cx, plan.cy, R, n, rng, jitter=0.18)
        pts = clip_to_land(plan, pts)
        corners = pts
    # walls, gates and moat
    mask = clean_mask(plan, polygon_mask(plan, pts))
    plan.mask, plan.shape_pts = mask, pts
    set_inside(plan, mask)
    build_walls(plan, mask, WALL, corners=corners if lay["towers"] else (), spacing=6.5, towers=lay["towers"])
    if shape == "castrum":
        angles = [0, math.pi / 2, math.pi, 3 * math.pi / 2]
    elif shape in ("star", "rocca"):
        mids = [math.atan2(((a[1] + b[1]) / 2 - plan.cy), ((a[0] + b[0]) / 2 - plan.cx) / ASPECT)
                for a, b in zip(corners, corners[1:] + corners[:1])]
        angles = rng.sample(mids, min(lay["gates"] or 1, len(mids)))
    else:
        angles = gate_angles(plan, mask, lay["gates"] or 1, rng)
    if plan.approach is not None and shape in ("castrum", "star", "rocca"):
        # perched: only the gates on the way up (one or two), none over the cliffs
        off = lambda a: abs(math.remainder(a - plan.approach, 2 * math.pi))
        angles = sorted(angles, key=off)
        angles = angles[:min(2, max(1, sum(1 for a in angles if off(a) < 1.2)))]
    for a in angles:
        carve_gate(plan, mask, a, flank=lay["towers"])
    if lay["moat"]:
        moat_around(plan, mask, MOAT if lay["moat"] == "water" else DITCH, width=2.4 if shape in ("star", "rocca") else 1.4)
        plan.moat = lay["moat"]
    specs, plan.wanted = building_list(p, rng)
    plan.missing = Counter()
    inner_mask = None
    # a walled inner ward on the far side from the gate, with towers and a gate of its own
    if lay.get("inner"):
        gate = plan.gates[0]["angle"] if plan.gates else 0
        ix, iy = ray(plan.cx, plan.cy, gate + math.pi, R * 0.32)
        small = [(ix + (x - plan.cx) * 0.42, iy + (y - plan.cy) * 0.42) for x, y in pts]
        inner_mask = {c for c in polygon_mask(plan, small) if c in mask and plan.cell[c[1]][c[0]] is None}
        ring = ring_of(inner_mask)
        for x, y in ring:
            plan.cell[y][x] = WALL
        for c in (small if len(small) <= 8 else small[::2]):
            near = min(ring, key=lambda r: (r[0] - c[0]) ** 2 / 4 + (r[1] - c[1]) ** 2)
            stamp_tower(plan, near[0], near[1], inner_mask, half=(1, 1))
        # the inner gate faces the outer one
        old_c = (plan.cx, plan.cy)
        plan.cx, plan.cy = ix, iy
        g = carve_gate(plan, inner_mask, gate, flank=False)
        plan.cx, plan.cy = old_c
        if g:
            g["inner_ward"] = True
        plan.inner_mask = inner_mask
    if shape == "castrum":
        hw, hh = 3, 1
        make_square(plan, rng, hw, hh, kind=SQUARE, irregular=False)
        for g in plan.gates:
            radial_streets(plan, [g["angle"]])
        ring_street(plan, mask)
        plan.layout = "castrum"
    elif shape == "star":
        make_square(plan, rng, int(R * 0.32 * ASPECT), int(R * 0.22), kind=SQUARE, irregular=False)
        for g in plan.gates:
            radial_streets(plan, [g["angle"]])
        plan.layout = "star"
    else:
        plan.square = set()
        for g in plan.gates:
            if g.get("inner_ward"):
                continue
            radial_streets(plan, [g["angle"]])
        plan.layout = shape
    for y in range(plan.H):
        for x in range(plan.W):
            if plan.cell[y][x] == STREET:
                keep_clear.add((x, y))
    # the keep first, in the inner ward or at the heart of the castle; then the rest
    keeps = [s for s in specs if s.get("keep")]
    others = [s for s in specs if not s.get("keep")]
    fieldset = Fields(plan)
    for spec in keeps:
        region = (lambda x, y: (x, y) in inner_mask and plan.cell[y][x] is None) if inner_mask else region_in(plan)
        if shape in ("castrum", "star"):
            b = place_one(plan, rng, spec, p["era"], fieldset, region, "front", "square", gap=(1, 1))
        else:
            b = place_one(plan, rng, spec, p["era"], fieldset, region, "free", "keep", gap=(2, 1),
                          keep_clear=keep_clear)
        if b is None:
            plan.missing[spec["id"]] += 1
    if shape == "castrum":
        grid_streets(plan, rng, rng.randint(12, 14), 5)
    placed, missing = place_list(plan, rng, p, others, ward=True, keep_clear=None)
    plan.missing.update(missing)
    if shape in ("castrum", "star"):
        fill = [BUILDING["barracks"]] * rng.randint(1, 3)
        more, _ = place_list(plan, rng, p, fill, ward=False)
    house = BUILDING["house"]
    outside = region_out(plan, near=plan.R * 2.0)
    fill_houses(plan, rng, house, p["era"], outside, ((5, 7), (3, 3)), (3, 1), limit=rng.randint(1, 4) + round(type_span(p) * 4),
                opens={ROAD}, outside=True)


def build_motte(plan, p, rng, lay):
    """Early castle: a palisaded bailey and a mound with a timber tower."""
    R = plan.R
    # the bailey a little off the centre, the mound beside it
    a = rng.uniform(0, 2 * math.pi)
    bx, by = ray(plan.cx, plan.cy, a + math.pi, R * 0.25)
    pts = blob_shape(bx, by, R * 0.85, rng, wobble=0.08)
    pts = clip_to_land(plan, pts)
    mask = clean_mask(plan, polygon_mask(plan, pts))
    rm = R * 0.42
    mx, my = ray(bx, by, a, R * 0.85 + rm * 0.9)
    mound = {(x, y) for y in range(plan.H) for x in range(plan.W) if vdist(x, y, mx, my) <= rm
             and not plan.is_water(x, y)}
    top = {(x, y) for x, y in mound if vdist(x, y, mx, my) <= rm - 1.6}
    mask -= mound
    plan.mask, plan.shape_pts = mask, pts
    set_inside(plan, mask)
    set_inside(plan, top)
    for x, y in mound - top:
        plan.cell[y][x] = MOUND
    # palisades round the bailey and round the top of the mound
    build_walls(plan, mask, PALISADE, towers=False)
    for x, y in ring_of(top):
        plan.cell[y][x] = PALISADE
    gate_dirs = gate_angles(plan, mask, 1, rng, prefer=a + math.pi)
    plan.cx, plan.cy = bx, by
    for g in gate_dirs:
        carve_gate(plan, mask, g, flank=False)
    plan.cx, plan.cy = (bx + mx) / 2, (by + my) / 2
    ditch = MOAT if lay["moat"] == "water" else DITCH
    moat_around(plan, mask | mound, ditch, width=1.3)
    plan.moat = lay["moat"]
    # the flying bridge from the bailey up to the top of the mound
    for x, y in line_cells_between((bx, by), (mx, my)):
        if plan.ok(x, y) and plan.cell[y][x] in (MOUND, DITCH, MOAT, PALISADE) and (x, y) not in top:
            plan.cell[y][x] = BRIDGE
        if (x, y) in top and plan.cell[y][x] == PALISADE:
            plan.cell[y][x] = GATE
    plan.cx, plan.cy = bx, by
    # the timber tower on top of the mound, the rest in the bailey
    specs, plan.wanted = building_list(p, rng)
    plan.missing = Counter()
    tower = [s for s in specs if s.get("keep")]
    rest = [s for s in specs if not s.get("keep")]
    on_top = lambda x, y: (x, y) in top and plan.cell[y][x] is None
    for spec in tower:
        done = False
        for w, h in ((spec["w"][0], spec["h"][0]), (5, 3)):
            spots = sorted(((int(mx - w / 2) + dx, int(my - h / 2) + dy) for dx in range(-3, 4) for dy in range(-2, 3)),
                           key=lambda c: abs(c[0] + w / 2 - mx) / ASPECT + abs(c[1] + h / 2 - my))
            for x0, y0 in spots:
                if rect_ok(plan, x0, y0, w, h, on_top, (0, 0)):
                    add_building(plan, spec, x0, y0, w, h, nearest_door(plan, x0, y0, w, h), False)
                    done = True
                    break
            if done:
                break
        if not done:
            plan.missing[spec["id"]] += 1
    for x, y in top:
        if plan.cell[y][x] is None:
            plan.cell[y][x] = YARD          # the top of the mound is for the tower only
    plan.square = set()
    for g in plan.gates:
        radial_streets(plan, [g["angle"]])
    placed, missing = place_list(plan, rng, p, rest, ward=True)
    plan.missing.update(missing)
    plan.layout = "motte"
    plan.motte = (mx, my, rm)
    outside = region_out(plan, near=plan.R * 2.0)
    fill_houses(plan, rng, BUILDING["house"], p["era"], outside, ((5, 7), (3, 3)), (3, 1), limit=rng.randint(1, 4),
                opens={ROAD}, outside=True)


def line_cells_between(a, b):
    """The cells on the straight line from a to b."""
    (x0, y0), (x1, y1) = a, b
    n = int(max(abs(x1 - x0), abs(y1 - y0) * 2)) + 1
    out = []
    for k in range(n + 1):
        c = (int(x0 + (x1 - x0) * k / n), int(y0 + (y1 - y0) * k / n))
        if not out or out[-1] != c:
            out.append(c)
    return out


def cliffs(plan):
    """Below a perched settlement the ground drops in cliffs, all round but on the way up."""
    edge = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.inside[y][x]]
    dist = distance_field(plan, edge, limit=CLIFF_BAND + 1)
    for y in range(plan.H):
        for x in range(plan.W):
            if plan.inside[y][x] or plan.cell[y][x] is not None or plan.is_water(x, y):
                continue
            if 0.9 < dist[y][x] <= CLIFF_BAND + (plan.n2[y][x] - 0.5) * 1.5:
                angle = math.atan2(y - plan.cy, (x - plan.cx) / ASPECT)
                if abs(math.remainder(angle - plan.approach, 2 * math.pi)) > CLIFF_OPEN:
                    plan.ground[y][x] = "cliff"


def stairs(plan):
    """The street cells of a perched settlement too steep for a cart: flights of steps."""
    out = set()
    for y in range(plan.H):
        for x in range(plan.W):
            if plan.cell[y][x] != STREET or (x, y) in plan.main:      # main streets stay ramps for carts
                continue
            for dx, dy in DIRS4:
                nx, ny = x + dx, y + dy
                if plan.ok(nx, ny) and plan.cell[ny][nx] == STREET:
                    step = 1 / ASPECT if dx else 1.0
                    if abs(plan.height[ny][nx] - plan.height[y][x]) / step / plan.grade > STAIR_GRADE:
                        out.add((x, y))
                        break
    return out


def finish(plan, p, rng):
    """Fields, gardens, wells, the cemetery crosses, quarters, numbers, secrets."""
    ward = p["type"] in ("castle", "fortress")
    tree = "shroom" if p["terrain"] in ("fungus", "underground") else "tree"     # there, a giant mushroom
    # fields around every settlement (castles: roads out first); a perched settlement first gets its cliffs and
    # its stairs
    if not ward or True:
        if ward:
            roads_out(plan, rng)
        if plan.height:
            cliffs(plan)
            plan.stairs = stairs(plan)
        if p["terrain"] != "underground":          # below, the caverns feed the town (dig_out)
            fields(plan, rng, p["terrain"], plan.R * plan.lay["reach"])
    # what is left inside the walls: courtyards and kitchen gardens
    for y in range(plan.H):
        for x in range(plan.W):
            if plan.inside[y][x] and plan.cell[y][x] is None:
                plan.cell[y][x] = YARD if ward else GARDEN
    # wells, fountain, market stalls, trees on the green
    sq = sorted(getattr(plan, "square", ()))
    if sq:
        free = [c for c in sq if all(plan.cell[c[1] + dy][c[0] + dx] in OPEN
                                      for dx in (-1, 0, 1) for dy in (-1, 0, 1) if plan.ok(c[0] + dx, c[1] + dy))]
        rng.shuffle(free)
        centre = min(sq, key=lambda c: vdist(c[0], c[1], plan.cx, plan.cy))
        if p["type"] in ("city", "bigcity") and p["era"] != "early":
            plan.feat[centre] = "fountain"
        else:
            plan.feat[centre] = "well"
        if p["type"] in ("town", "city", "bigcity"):
            for c in free[:rng.randint(3, 7)]:
                if c not in plan.feat and all(vdist(c[0], c[1], o[0], o[1]) > 1.5 for o in plan.feat):
                    plan.feat[c] = "stall"
        elif p["type"] == "village":
            for c in free[:rng.randint(1, 3)]:
                if c not in plan.feat:
                    plan.feat[c] = tree
    if ward:
        # a castle's well: in the middle of an open stretch of the courtyard
        yard = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.cell[y][x] == YARD and
                all(plan.ok(x + dx, y + dy) and plan.cell[y + dy][x + dx] in (YARD, STREET, SQUARE)
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
        if yard:
            plan.feat[rng.choice(yard)] = "well"
    else:
        # a town's wells: along the side streets, one every 25 buildings or so
        streets = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.cell[y][x] == STREET
                   and (x, y) not in plan.main]
        rng.shuffle(streets)
        for c in streets[:max(1, len(plan.buildings) // 25)]:
            plan.feat[c] = "well"
    for y in range(plan.H):
        for x in range(plan.W):
            # a few trees in the gardens
            if plan.cell[y][x] == GARDEN and plan.tex[y][x] < 0.05:
                plan.feat[(x, y)] = tree
    # then quarters and building numbers, and the secret ways
    quarters_and_numbers(plan, p)
    secrets(plan, p, rng)


def quarters_and_numbers(plan, p):
    """Walled towns: one quarter between every two gates, named after them;
    buildings are numbered quarter by quarter, top to bottom, left to right,
    and those outside the walls come last."""
    gates = [g for g in plan.gates if not g.get("inner_ward") and not g.get("road_only")]
    angles = sorted(g["angle"] % (2 * math.pi) for g in gates)
    use = p["type"] in ("town", "city", "bigcity") and len(angles) >= 2
    plan.quarters = len(angles) if use else 1
    for b in plan.buildings:
        if b.outside:
            b.quarter = plan.quarters
            continue
        if not use:
            b.quarter = 0
            continue
        x, y = b.centre()
        a = math.atan2(y - plan.cy, (x - plan.cx) / ASPECT) % (2 * math.pi)
        k = 0
        for i, g in enumerate(angles):
            if a >= g:
                k = i
        if a < angles[0]:
            k = len(angles) - 1
        b.quarter = k
    order = sorted(plan.buildings, key=lambda b: (b.quarter, int(b.centre()[1] // 4), b.centre()[0]))
    for n, b in enumerate(order, 1):
        b.number = n
        b.uid = n
    plan.buildings.sort(key=lambda b: b.number)
    plan.bmap = [[-1] * plan.W for _ in range(plan.H)]
    for k, b in enumerate(plan.buildings):
        for x, y in b.cells():
            plan.bmap[y][x] = k
    plan.quarter_angles = angles if use else []


def secrets(plan, p, rng):
    """A postern hidden in the walls, and a secret tunnel from the keep (or a
    palace, the thieves' den, a church) out past the walls."""
    if not plan.walled:
        return
    # posterns: wall cells with land on both sides, as far from the gates as possible (two in a city)
    fort = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.cell[y][x] in (WALL, PALISADE)
            and (x, y) in getattr(plan, "mask", ())]
    gates = [c for g in plan.gates for c in g["cells"]]
    good = []
    for x, y in fort:
        outside = [(x + dx, y + dy) for dx, dy in DIRS4 if plan.ok(x + dx, y + dy)
                   and not plan.inside[y + dy][x + dx] and plan.cell[y + dy][x + dx] not in FORT]
        inside = [(x + dx, y + dy) for dx, dy in DIRS4 if plan.ok(x + dx, y + dy)
                  and plan.inside[y + dy][x + dx] and plan.cell[y + dy][x + dx] not in FORT]
        if outside and inside and all(not plan.is_water(*c) for c in outside):
            d = min((vdist(x, y, gx, gy) for gx, gy in gates), default=99)
            good.append((d, x, y))
    good.sort(reverse=True)
    for d, x, y in good[:1 + (p["type"] in ("city", "bigcity"))]:
        plan.secret.add((x, y))
    # the tunnel
    starts = [b for b in plan.buildings if b.kind.get("keep") or b.id in ("thieves", "rocca")]
    starts = starts or [b for b in plan.buildings if b.id in ("church", "palazzo", "lords_hall", "manor")]
    if not starts or rng.random() < 0.3:
        return
    # from the building, straight out past the walls, under everything but the walls and other buildings, and a few
    # letters on beyond them
    b = rng.choice(starts)
    bx, by = b.centre()
    angle = math.atan2(by - plan.cy, (bx - plan.cx) / ASPECT) if (bx, by) != (plan.cx, plan.cy) else rng.uniform(0, 6)
    angle += rng.uniform(-0.4, 0.4)
    t, path = 0.0, []
    crossed = False
    while t < plan.R * 3:
        x, y = int(bx + math.cos(angle) * t * ASPECT), int(by + math.sin(angle) * t)
        if not plan.ok(x, y) or plan.is_water(x, y):
            break
        if plan.cell[y][x] in FORT:
            crossed = True
        elif crossed and not plan.inside[y][x]:
            path.append((x, y))
            if len([c for c in path if not plan.inside[c[1]][c[0]]]) > 6:
                break
        if plan.cell[y][x] not in FORT and plan.bmap[y][x] < 0:
            path.append((x, y))
        t += 0.4
    if crossed and path:
        plan.tunnel = {c for c in path if plan.cell[c[1]][c[0]] not in FORT and plan.bmap[c[1]][c[0]] < 0}
        plan.tunnel_from = b
        plan.tunnel_end = path[-1]



# --- the people ---
ALIGNMENTS = (("Legale", "Lawful"), ("Neutrale", "Neutral"), ("Caotico", "Chaotic"))
ARMOUR = {"fighter": [(5, 14), (4, 15), (3, 16), (2, 17)], "cleric": [(5, 14), (4, 15), (3, 16)],
          "thief": [(7, 12), (6, 13)], "mu": [(9, 10)], "dwarf": [(4, 15), (3, 16)], "elf": [(5, 14), (4, 15)],
          "halfling": [(6, 13), (5, 14)]}
HIT_DIE = {"fighter": 8, "cleric": 6, "mu": 4, "thief": 4, "dwarf": 8, "elf": 6, "halfling": 6}
# spell slots by level (1st, 2nd, 3rd level spells), B/X style
SLOTS = {"cleric": {1: [], 2: [1], 3: [2], 4: [2, 1], 5: [2, 2], 6: [2, 2, 1], 7: [3, 2, 2], 8: [3, 3, 2]},
         "mu": {1: [1], 2: [2], 3: [2, 1], 4: [2, 2], 5: [2, 2, 1], 6: [2, 2, 2], 7: [3, 2, 2], 8: [3, 3, 2]}}


def gendered(entry, gender):
    """(it, en) from a data entry that may have feminine forms (it_f, en_f)."""
    if isinstance(entry, tuple):
        return entry
    it = entry.get("it_f", entry["it"]) if gender == "f" else entry["it"]
    en = entry.get("en_f", entry["en"]) if gender == "f" else entry["en"]
    return it, en


def thac0(cls, lv):
    """THAC0 of a class at a level, by the Old-School Essentials tables."""
    if cls in ("fighter", "dwarf", "halfling", "elf"):
        return 19 if lv <= 3 else 17 if lv <= 6 else 14 if lv <= 9 else 12
    if cls in ("cleric", "thief"):
        return 19 if lv <= 4 else 17 if lv <= 8 else 14
    return 19 if lv <= 5 else 17


def stat_line(rng, cls, lv, align):
    """An OSR stat line, (it, en)."""
    al = ALIGNMENTS[align]
    if cls == "normal" or not lv:
        hp = rng.randint(1, 4)
        ml = rng.choice((6, 6, 7, 8))
        return (f"Umano normale · CA 9 [10] · DV ½ ({hp} PF) · Mor {ml} · AL {al[0]}",
                f"Normal human · AC 9 [10] · HD ½ ({hp}hp) · ML {ml} · AL {al[1]}")
    hp = sum(rng.randint(1, HIT_DIE[cls]) for _ in range(lv))
    ac = rng.choice(ARMOUR[cls])
    t = thac0(cls, lv)
    ml = rng.randint(7, 10)
    name = TABLES["classes"][cls]
    it = f"{name[0]} {lv} · CA {ac[0]} [{ac[1]}] · PF {hp} · THAC0 {t} [+{19 - t}] · Mor {ml} · AL {al[0]}"
    en = f"{name[1]} {lv} · AC {ac[0]} [{ac[1]}] · {hp}hp · THAC0 {t} [+{19 - t}] · ML {ml} · AL {al[1]}"
    slots = SLOTS.get(cls, {}).get(min(lv, 8), [])
    if slots:
        chosen = []
        for level, n in enumerate(slots):
            pool = TABLES["spells"][cls][min(level, len(TABLES["spells"][cls]) - 1)]
            chosen += rng.sample(pool, min(n, len(pool)))
        it += " · Incantesimi: " + ", ".join(s[0] for s in chosen)
        en += " · Spells: " + ", ".join(s[1] for s in chosen)
    return it, en


def make_npc(rng, used, role, gender=None, cls="normal", lv=None, align=None):
    """A person: name, role, class and level, alignment, trait, want, secret and OSR stats."""
    gender = gender or rng.choice("mf")
    if align is None:
        align = rng.choices((0, 1, 2), weights=(4, 4, 2))[0]
    if cls != "normal" and lv is None:
        lv = 1
    name = person_name(rng, gender, used)
    p = getattr(used, "p", None)
    if p and "number" in p:
        # a town, a family or a god of their own; drawn apart, so the rest of the settlement stays as it was
        r = random.Random(f"wyrmurbigen-npcfill-{p['number']}-{used.count}")
        values = dict(place=town_name(r, p), family=(family_name(r, p),) * 2, god=god_name(r, p))
    else:
        values = dict(place="?", family="?", god="?")
    return {"name": name, "first": name[0].split(" ")[0], "gender": gender, "role": role, "cls": cls, "lv": lv,
            "trait": fmt(gendered(rng.choice(TABLES["traits"]), gender), **values),
            "want": fmt(gendered(rng.choice(TABLES["wants"]), gender), **values),
            "secret": fmt(gendered(rng.choice(TABLES["secrets"]), gender), **values),
            "stats": stat_line(rng, cls, lv, align)}


def npc_line(npc, full=True):
    """A person on one line: name and role; with `full`, also stats, trait, want and secret."""
    head = f"{pick(npc['name'])}, {pick(npc['role'])}"
    if not full:
        return head
    return tr("npc_line", h=head, s=pick(npc["stats"]), t=pick(npc["trait"]), w=pick(npc["want"]),
              x=pick(npc["secret"]))


def keeper_npc(rng, used, kind):
    """The person who runs a building of `kind` (innkeeper, priest...), if it has one."""
    k = kind.get("keeper")
    if not k:
        return None
    gender = "m" if not k.get("f") else rng.choice("mf")
    role = k["f"] if gender == "f" and k.get("f") else k["m"]
    cls = k.get("cls", "normal")
    lv = rng.randint(*k["lv"]) if k.get("lv") else None
    return make_npc(rng, used, role, gender, cls, lv)


# --- the settlement ---
class Settlement:
    """Everything about a settlement but its map: names, history, people, economy, threat... Attributes are added as
    they are made."""
    pass


def fill_title(rng, kind, npc, s):
    """A building's name from its kind's templates: signs, gods, families, guilds, the owner."""
    title = rng.choice(kind.get("title") or [kind["name"]])
    values = {"sign": rng.choice(TABLES["signs"]), "god": god_name(rng, s.p),
              "family": (family_name(rng, s.p),) * 2,
              "guild": rng.choice(TABLES["guilds"]),
              "owner": (npc["first"], npc["first"]) if npc else (place_name(rng, None, s.p.get("names"), s.p.get("tone")),) * 2}
    return fmt(title, **values)


def plural_trades(trades):
    """A list of trades as one (it, en) phrase: smiths, tanners and weavers."""
    return join_pairs([t for t in trades])


def join_pairs(pairs):
    """A list of (it, en) pairs joined with commas and a final "e" / "and"."""
    out = []
    for lang, word in enumerate((" e ", " and ")):
        words = [p[lang] for p in pairs]
        out.append(words[0] if len(words) == 1 else ", ".join(words[:-1]) + word + words[-1])
    return tuple(out)


GROWN = 0.75                # in a mushroom forest, the share of non-stone buildings grown in a giant mushroom
GROWN_TOLD = 0.3            # ... and of the grown houses whose key tells how (every notable building does)


FOLK_TOLD = 2               # below, how many notable buildings tell each of the folk's lines, at most


def dig_in(s, seed):
    """Below: the folk (s.folk), how their notable buildings look (b.grown_text, as for the mushroom houses) and,
    for the fungus folk, houses grown in giant mushrooms; from a generator of its own."""
    s.folk = FOLK[s.p["folk"]]
    r = random.Random(f"wyrmurbigen-folk-{seed}")
    for b in s.plan.buildings:
        if s.folk.get("grown") and not b.kind.get("stone") == "always":
            b.grown = True
    notable = [b for b in s.plan.buildings if not b.kind.get("filler")]
    lines = list(s.folk["lines"]) * FOLK_TOLD
    r.shuffle(lines)
    for b, line in zip(r.sample(notable, min(len(notable), len(lines))), lines):
        b.grown_text = line


def grow_in_mushrooms(s, seed):
    """In a giant mushroom forest most of what is not stone is grown inside a mushroom (b.grown), and the key says
    how for the notable buildings and a few houses (b.grown_text); from a generator of its own."""
    r = random.Random(f"wyrmurbigen-grown-{seed}")
    lines = TERRAIN["fungus"]["grown"]
    for b in s.plan.buildings:
        if b.kind.get("grown"):         # a grown tower: a mushroom through and through, its own text says how
            b.grown = True
        elif not b.stone and r.random() < GROWN:
            b.grown = True
            if not b.kind.get("filler") or r.random() < GROWN_TOLD:
                b.grown_text = r.choice(lines)


def make_settlement(p, plan, seed):
    """Everything but the map: names, history, government, people in every
    building, demographics, economy; monsters and treasure come later."""
    rng = random.Random(f"wyrmurbigen-people-{seed}")
    s = Settlement()
    s.p, s.plan, s.seed = p, plan, seed
    used_names, used_places = NameBook(p), set()
    # the name, sometimes with an epithet of its land (on the Hill, by the Sea...), and the title
    s.name = place_name(rng, used_places, p.get("names"), p.get("tone"))
    if rng.random() < 0.35 and not re.search(r"[ -]", s.name):
        ep = rng.choice(TERRAIN[p["terrain"]]["epithet"])
        s.name_pair = (f"{s.name} {ep[0]}", f"{s.name} {ep[1]}")
    else:
        s.name_pair = (s.name, s.name)
    s.title = fmt(TYPE[p["type"]]["title"][p["era"]], n=s.name_pair)
    kind = p["type"]
    # the trades that make sense here
    trades = [t for t in TABLES["trades"] if allowed_in(t["where"], kind)
              and (not t.get("terrains") or p["terrain"] in t["terrains"])] or TABLES["trades"]
    # gates and quarters
    gates = [g for g in plan.gates if not g.get("inner_ward") and not g.get("road_only")]
    letters = "ABCDEFGHJKLMNP"
    # every gate a letter and a name: towards the sea or the lake, a bridge, or a god or another town
    for k, g in enumerate(gates):
        g["letter"] = letters[k % len(letters)]
        toward_water = False
        if g.get("outer"):
            ox, oy = g["outer"]
            for t in (2, 4, 6):
                x, y = ray(plan.cx, plan.cy, g["angle"], vdist(ox, oy, plan.cx, plan.cy) + t)
                if plan.ok(int(x), int(y)) and plan.is_water(int(x), int(y)):
                    toward_water = True
        if toward_water and p["terrain"] in ("coast", "lake"):
            g["name"] = ("Porta a Mare", "Sea Gate") if p["terrain"] == "coast" else ("Porta del Lago", "Lake Gate")
        elif toward_water:
            g["name"] = ("Porta del Ponte", "Bridge Gate")
        else:
            g["name"] = fmt(rng.choice(TABLES["gates"]), god=god_name(rng, p),
                            place=(town_name(rng, p),) * 2)
        g["dir"] = compass(g["angle"])
    s.gates = gates
    # the quarters are named after their gates
    s.quarter_names = []
    angles = plan.quarter_angles
    if angles:
        ordered = sorted(gates, key=lambda g: g["angle"] % (2 * math.pi))
        for k in range(len(angles)):
            g = ordered[k]
            q = rng.choice([q for q in TABLES["quarters"] if "{trade}" not in q[0]])
            s.quarter_names.append(fmt(q, gate=g["name"], god=god_name(rng, p),
                                       trade=(rng.choice(trades)["m"][0] + "i", rng.choice(trades)["m"][1] + "s")))
    s.quarter_names = [fix_trade_quarter(q) for q in s.quarter_names]
    # people in the buildings
    s.npcs = []
    residential = [b for b in plan.buildings if b.kind.get("filler")]
    notable = [b for b in plan.buildings if not b.kind.get("filler")]
    # the notable buildings: their keeper, name, household and description
    for b in notable:
        b.npc = keeper_npc(rng, used_names, b.kind)
        b.title = fill_title(rng, b.kind, b.npc, s)
        b.people = max(0, roll(b.kind.get("household", "1d4"), rng))
        b.text = rng.choice(b.kind["text"]) if b.kind.get("text") else None
        if b.npc:
            s.npcs.append(b.npc)
    # the houses share the rest of the population by size; each has a head of household with a trade
    taken = sum(b.people for b in notable)
    left = max(len(residential), p["pop"] - taken) if kind not in ("castle", "fortress") else max(0, p["pop"] - taken)
    area = sum(b.w * b.h for b in residential) or 1
    ppd = DEMOGRAPHICS["people_per_dwelling"].get(kind, 4)
    for b in residential:
        b.people = max(1, round(left * b.w * b.h / area))
        trade = rng.choice(trades)
        gender = rng.choice("mf")
        b.npc = make_npc(rng, used_names, trade[gender] if trade.get(gender) else trade["m"], gender,
                         "normal" if rng.random() < 0.9 else rng.choice(("fighter", "thief", "cleric")),
                         rng.randint(1, 2))
        s.npcs.append(b.npc)
        b.text = None
        dwellings = max(1, round(b.people / ppd))
        b.dwellings = dwellings
        # a house's name by how many live there: a farm or house, a house and shop, row houses, a block
        if kind == "village" or b.outside and kind in ("castle", "fortress"):
            b.title = (f"Corte di {b.npc['first']}", f"{b.npc['first']}'s Farmyard") if b.people > 6 else \
                (f"Casa di {b.npc['first']}", f"{b.npc['first']}'s House")
        elif b.people <= 9:
            b.title = (f"Casa e bottega di {b.npc['first']}", f"{b.npc['first']}'s House and Shop")
        elif b.people <= 40:
            b.title = ("Case a schiera", "Row houses")
        else:
            b.title = ("Isolato", "Block")
        extra = rng.sample(trades, min(2, len(trades)))
        b.trades = [trade["m"]] + [t["m"] for t in extra]
    if p["terrain"] == "fungus":
        grow_in_mushrooms(s, seed)
    if p["terrain"] == "underground":
        dig_in(s, seed)
    # government
    rulers = TABLES["rulers"][kind if kind in TABLES["rulers"] else building_type(kind)][p["era"]]
    title = rng.choice(rulers)
    cls = "cleric" if "sacerdote" in title[0] else "fighter"
    lv_range = {"village": (1, 3), "town": (2, 4), "city": (4, 6), "bigcity": (5, 8), "castle": (3, 7),
                "fortress": (4, 8)}[kind]
    s.ruler = make_npc(rng, used_names, title, None, cls, rng.randint(*lv_range), align=rng.choice((0, 0, 1, 2)))
    if p["terrain"] == "underground":     # below, the folk's own ruler
        s.ruler["role"] = s.folk["ruler"][s.ruler["gender"]]
    seat = [b for b in notable if b.kind.get("keep")] or \
           [b for b in notable if b.id in ("town_hall", "lords_hall", "manor", "rocca", "palazzo", "command")]
    s.ruler_seat = seat[0] if seat else None
    s.factions, s.notables, s.strata = [], [], []       # made by plan_intrigue
    # history
    founder = rng.choice([(f"{pick(person_name(rng, 'm', used_names))}",) * 2,
                          fmt(("la famiglia {f}", "the {f} family"), f=(family_name(rng, p),) * 2)])
    founded = TABLES["history"]["founded_ward" if kind in ("castle", "fortress") else "founded"][p["era"]]
    s.history = [fmt(rng.choice(founded), n=s.name_pair, founder=founder, god=god_name(rng, p))]
    s.present = fmt(rng.choice(TABLES["history"]["present_rest"]), n=s.name_pair)
    # the numbers: demography and economy
    s.demography = demography(p, plan, rng)
    s.economy = economy(p, rng, used_names)
    # rumours, events, hooks: drawn now, filled in when monsters are known
    s.rng_lore = random.Random(f"wyrmurbigen-lore-{seed}")
    s.used_names = used_names
    return s


def fix_trade_quarter(q):
    """"Rione dei tessitorei" -> plural by hand for the common endings."""
    it, en = q
    it = re.sub(r"ore?i\b", "ori", it)
    it = re.sub(r"aioi\b", "ai", it)
    it = re.sub(r"oi\b", "i", it)
    it = re.sub(r"ai\b", "ai", it)
    en = re.sub(r"ss\b", "s", en)
    return it, en


def compass(angle):
    """The compass direction of an angle (0 = east, clockwise on the map), as an (it, en) pair."""
    names = (("est", "east"), ("sud-est", "south-east"), ("sud", "south"), ("sud-ovest", "south-west"),
             ("ovest", "west"), ("nord-ovest", "north-west"), ("nord", "north"), ("nord-est", "north-east"))
    return names[round((angle % (2 * math.pi)) / (math.pi / 4)) % 8]


def demography(p, plan, rng):
    """Medieval Demographics Made Easy, by S. John Ross: support values, clergy,
    nobles, guards, livestock."""
    kind, pop = p["type"], p["pop"]
    r = DEMOGRAPHICS["ratios"]
    d = {"pop": pop, "density": plan.density, "hectares": plan.hectares,
         "dwellings": round(pop / DEMOGRAPHICS["people_per_dwelling"].get(kind, 4))}
    if kind in ("castle", "fortress"):
        share = 0.45 if kind == "castle" else 0.75
        d["garrison"] = max(4, round(pop * share))
        d["servants"] = pop - d["garrison"]
        d["horses"] = max(2, round(d["garrison"] * (0.4 if kind == "castle" else 0.2)))
        d["livestock"] = round(pop * r["livestock"])
        return d
    clergy = pop / r["clergy"]
    d.update(nobles=pop / r["noble"], lawyers=pop / r["lawyer"], clergy=clergy,
             priests=clergy / rng.randint(*r["priest_per_clergy"]), worship=pop / r["worship"],
             guards=pop / r["guard"] * (0.5 if rng.random() < 0.3 else 1.0), livestock=pop * r["livestock"])
    d["slack"] = d["guards"] < pop / r["guard"] * 0.9
    shops = []
    for b in DEMOGRAPHICS["businesses"]:
        sv = b["sv"] * (1 + (roll("4d4", rng) - 6) / 10)       # local support values
        shops.append((b["name"], pop / sv))
    d["shops"] = shops
    return d


def region_of(p):
    """The economic region around the settlement, by terrain; the Early Middle Ages are one step emptier,
    Renaissance cities one step richer."""
    order = [r["id"] for r in ECONOMY["regions"]]
    k = order.index(ECONOMY["terrain_region"][p["terrain"]])
    if p["era"] == "early":
        k = min(len(order) - 1, k + 1)          # fewer towns before the Crusades
    elif p["era"] == "renaissance" and p["type"] in ("city", "bigcity"):
        k = max(0, k - 1)
    return ECONOMY["regions"][k]


def economy(p, rng, used):
    """Skerples, OSR: Land and Investments (Coins and Scrolls): the country
    around, the lord's revenue, properties for sale."""
    region = region_of(p)
    e = {"region": region}
    revenue = region["revenue"]
    add = ECONOMY["settlement_revenue"].get(p["type"], 0)
    if p["type"] == "bigcity":
        add = round(add * p["pop"] / 10000)
    revenue += add
    e["revenue"] = revenue
    e["rural"] = region["per_hex"]
    e["villages"] = region["villages"]
    offers = [o for o in ECONOMY["properties"] if allowed_in(o["where"], p["type"])
              and (not o.get("terrains") or p["terrain"] in o["terrains"])]
    rng.shuffle(offers)
    e["offers"] = []
    for o in offers[:rng.randint(2, 4)]:
        seller = make_npc(rng, used, ("venditore", "seller"))
        people = roll(o["people"], rng) if o.get("people") else 0
        e["offers"].append({"offer": o, "seller": seller, "people": people})
    return e


def troubled(s):
    """Plague, war, famine halve every revenue; truly chaotic times divide it by ten."""
    sit = getattr(s, "situation", None)
    if not sit:
        return 1
    if sit["id"] in ECONOMY["troubled"]["tenth"]:
        return 10
    if sit["id"] in ECONOMY["troubled"]["half"]:
        return 2
    return 1


# --- place of adventure: the threat, monsters, treasure ---
def plan_threat(s):
    """The danger of a place of adventure: the situation (cult, brigands, plague...), its lair, its leader and the
    text that tells it."""
    p, plan = s.p, s.plan
    rng = random.Random(f"wyrmurbigen-threat-{s.seed}")
    # in ruins: only the threats of a ruin; inhabited: the others; older seeds: any
    state = p.get("state")
    pool = [x for x in SITUATIONS if x.get("min_danger", 1) <= p["danger"]
            and (not x.get("terrains") or p["terrain"] in x["terrains"])
            and (state is None or (x["life"] == "ruin") == (state == "ruin"))]
    sit = rng.choice(pool)
    s.situation = sit
    lairs = [b for b in plan.buildings if b.kind.get("dungeon") in sit["lairs"] and not b.outside]
    lairs.sort(key=lambda b: (-b.kind.get("priority", 0), b.number))
    s.lair = (lairs[:3] and rng.choice(lairs[:3])) or rng.choice(plan.buildings)
    villain = make_npc(rng, s.used_names, ("capo", "leader"), None,
                       rng.choice(("fighter", "thief")) if sit["id"] not in ("tyrant", "cult") else
                       ("mu" if sit["id"] == "tyrant" else "cleric"), max(1, p["danger"] * 2 - 1), align=2)
    s.villain = villain
    fam2 = family_name(rng, s.p)
    values = dict(n=s.name_pair, person=villain["name"], family=(family_name(rng, s.p),) * 2,
                  family2=(fam2,) * 2, lair=(f"n. {s.lair.number} ({s.lair.title[0]})", f"no. {s.lair.number} ({s.lair.title[1]})"))
    s.dwellers = fmt(sit["dwellers"], **values)
    s.boss = None
    if sit.get("boss"):         # who rules a ruin is a monster: a made-up name and a sketch, the stats of the table
        roots = TABLES["god_roots"]
        name = join_roots(rng.choice(roots["start"]), rng.choice(roots["m_end"] + roots["f_end"])).capitalize()
        s.boss = fmt(sit["boss"], name=name, lair=values["lair"])
    s.threat = fmt(sit["text"], **values)
    s.clock = sit["clock"]
    life = sit["life"]
    plan.ruin = life == "ruin"
    # abandoned and ruined buildings
    s.abandoned = set()
    if life == "ruin":
        for b in plan.buildings:
            b.ruined = rng.random() < 0.75
            s.abandoned.add(b.uid)
        ruin_layers(s, rng, values)
    elif life == "half":
        for b in plan.buildings:
            if rng.random() < 0.35 and b is not s.lair:
                s.abandoned.add(b.uid)
                b.ruined = rng.random() < 0.5


def ruin_layers(s, rng, values):
    """The layered history of a ruin: its founding, its height, its fall (the threat's own or a common one) and one
    or two later stories, each of which left a trace in a building. Sets s.layers, [(label, text)], and s.traces,
    {building uid: text}."""
    h, p = TABLES["ruin_history"], s.p
    pop = (f"{p['pop']:,}".replace(",", "."), f"{p['pop']:,}")
    values = dict(values, god=god_name(rng, p), pop=pop)
    labels = h["labels"]
    falls = s.situation.get("fall") if s.situation.get("fall") and rng.random() < 0.7 else h["fall"]
    years = rng.choice((30, 50, 70, 100, 150, 200, 300))
    s.layers = [(labels["founded"], s.history[0]),
                (labels["height"], fmt(rng.choice(h["height"]), **values)),
                (fmt(labels["fall"], y=str(years)), fmt(rng.choice(falls), **values))]
    s.traces = {}
    spots = [b for b in s.plan.buildings if b is not s.lair]
    rng.shuffle(spots)
    for later in rng.sample(h["after"], rng.randint(1, 2)):
        values["person"] = person_name(rng, rng.choice("mf"), s.used_names)
        s.layers.append((labels["after"], fmt(later["text"], **values)))
        if spots:
            s.traces[spots.pop().uid] = fmt(later["trace"], **values)
    s.ruin_cast = values


def fits_monster(m, where):
    """Whether a monster can live in a place of this kind (its "where" list, * for anywhere)."""
    w = m.get("where", ["*"])
    return "*" in w or where in w


def monster_label(m):
    """A monster's name, number appearing and danger, for the key."""
    name = capitalized(pick(m["name"]))
    n = f" ({m['number']})" if m.get("number") else ""
    return f"{name}{n} · {tr('danger_tag', d=m.get('danger', 2), hd=DANGER_HD.get(m.get('danger', 2), '?'))}"


def plan_monsters(s):
    """WyrmDelve's monsters, moved to a settlement: a d6 table of wandering
    monsters (the threat's own people, then monsters that fit the buildings
    here, as dangerous as the place), monsters in some buildings, a clue in an
    empty building near each of them."""
    rng = random.Random(f"wyrmurbigen-monsters-{s.seed}")
    p, plan, sit = s.p, s.plan, s.situation
    danger = p["danger"]
    here = {b.kind.get("dungeon", "city") for b in plan.buildings}
    # five monsters that could live in these buildings: as dangerous as the place first, then one step off, then any
    # that fit, then any at all
    fits = [k for k, m in enumerate(MONSTERS) if any(fits_monster(m, w) for w in here)]
    chosen = []
    for pool in ([k for k in fits if MONSTERS[k].get("danger", 2) == danger],
                 [k for k in fits if abs(MONSTERS[k].get("danger", 2) - danger) == 1], fits, range(len(MONSTERS))):
        group = [k for k in pool if k not in chosen]
        rng.shuffle(group)
        chosen += group[:5 - len(chosen)]
        if len(chosen) >= 5:
            break
    dwellers = capitalized(pick(s.dwellers))
    # how many buildings are taken: more in a half-empty place, most in a ruin
    share = {"inhabited": 0.12, "half": 0.22, "ruin": 0.35}[sit["life"]]
    bs = [b for b in plan.buildings]
    busy = max(2, min(len(bs) // 2, round(len(bs) * share)))
    occupants, contents = {}, {}
    # the threat's people in the lair and in a few other buildings of their kind
    homes = [(s.lair, "dwellers", None)]
    others = [b for b in bs if b is not s.lair and b.kind.get("dungeon") in sit["lairs"]]
    rng.shuffle(others)
    for b in others[:max(0, busy // 3 - 1)]:
        homes.append((b, "dwellers", None))
    free = [b for b in bs if b not in [h[0] for h in homes]]
    rng.shuffle(free)
    free.sort(key=lambda b: (b.uid not in s.abandoned, not b.kind.get("filler")))
    # the monsters in the free buildings that suit them, abandoned ones first
    for k in chosen:
        if len(homes) >= busy:
            break
        m = MONSTERS[k]
        spot = next((b for b in free if fits_monster(m, b.kind.get("dungeon", "city"))), None) or (free[0] if free else None)
        if spot is None:
            break
        free.remove(spot)
        homes.append((spot, "monster", k))
        if sit["life"] != "ruin":
            s.abandoned.add(spot.uid)
    for b, what, k in homes:
        if what == "dwellers":
            occupants[b.uid] = ("dwellers", None)
            contents.setdefault(b.uid, []).append(tr("room_lair", m=f"{dwellers} ({'3d6' if b is s.lair else '2d6'})"))
        else:
            occupants[b.uid] = ("monster", k)
            contents.setdefault(b.uid, []).append(tr("room_monsters", m=monster_label(MONSTERS[k])))
    # a clue to each of them in the nearest empty building
    kind_of = {b.uid: (sit["kind"] if what == "dwellers" else MONSTERS[k].get("kind")) for b, what, k in homes}
    for b, what, k in homes:
        kind = kind_of[b.uid]
        if kind == "dwellers" or kind not in CLUES:
            kind = "dwellers" if "dwellers" in CLUES else None
        if not kind:
            continue
        empty = [o for o in bs if o.uid not in occupants and o.uid not in contents]
        if not empty:
            break
        bx, by = b.centre()
        spot = min(empty, key=lambda o: (o.uid not in s.abandoned, vdist(*o.centre(), bx, by)))
        contents[spot.uid] = [tr("room_clue", c=pick(rng.choice(CLUES[kind])), r=b.number)]
    # the wandering monsters table: the threat's people, then the five monsters
    rows = [(dwellers, tr("wander_dwellers"))]
    rows += [(monster_label(MONSTERS[k]), pick(MONSTERS[k]["text"])) for k in chosen]
    s.wander = rows
    s.occupants = occupants
    s.contents = contents
    s.monster_names = [capitalized(pick(MONSTERS[k]["name"])) for k in chosen]


def in_range(value, rng_span):
    """Whether a die roll falls in a (low, high) range of a table."""
    return rng_span is not None and rng_span[0] <= value <= rng_span[1]


def magic_item(kind, expert, rng):
    """One magic item (it, en), as in WyrmDelve (Old-School Essentials tables)."""
    if kind in TREASURE["magic"]:
        table = kind
    else:
        allowed = {"weapon_armour": ("armour", "sword", "weapon"),
                   "not_weapon": ("armour", "misc", "potion", "ring", "rod", "scroll")}.get(kind)
        while True:
            d = rng.randint(1, 100)
            table = next(t["kind"] for t in TREASURE["magic_types"] if in_range(d, t["x" if expert else "b"]))
            if allowed is None or table in allowed:
                break
    items = TREASURE["magic"][table]
    basic = [i for i in items["items"] if i.get("b")]
    if expert or not basic:
        d = rng.randint(1, 100)
        name = next(i["name"] for i in items["items"] if in_range(d, i["x"]))
    else:
        d = rng.randint(1, items["basic_die"])
        name = next((i["name"] for i in basic if in_range(d, i["b"])), basic[0]["name"])
    if table == "armour" and TREASURE.get("armour_kinds"):
        d = rng.randint(1, 8)
        it, en = next(a["name"] for a in TREASURE["armour_kinds"] if in_range(d, a["roll"]))
        name = (name[0].replace("rmatura", "rmatura " + it, 1),
                re.sub("(?i)armour", lambda m: (en.capitalize() if m.group()[0] == "A" else en) + " armour", name[1], 1))
    return name


def roll_hoard(items, expert, rng):
    """Roll a hoard from a treasure type's lines: coins, gems, jewellery and magic items (`expert`: the Expert
    tables)."""
    hoard = {"coins": {}, "gems": [], "jewellery": [], "magic": []}
    for line in items:
        if rng.randint(1, 100) > line["chance"]:
            continue
        what = line["what"]
        if what in TREASURE["coin_value"]:
            hoard["coins"][what] = hoard["coins"].get(what, 0) + roll(line["dice"], rng) * line.get("times", 1)
        elif what == "gems":
            for _ in range(roll(line["dice"], rng) * line.get("times", 1)):
                d = rng.randint(1, 20)
                hoard["gems"].append(next(g["value"] for g in TREASURE["gems"] if in_range(d, g["roll"])))
        elif what == "jewellery":
            for _ in range(roll(line["dice"], rng) * line.get("times", 1)):
                hoard["jewellery"].append(roll(TREASURE["jewellery"]["dice"], rng) * TREASURE["jewellery"]["times"])
        elif what == "magic":
            for part in line["items"]:
                count = roll(part["dice"], rng) if part.get("dice") else part.get("count", 1)
                hoard["magic"] += [magic_item(part["kind"], expert, rng) for _ in range(count)]
    return hoard


def hoard_value(hoard):
    """The value of a hoard in gold pieces (magic items not counted)."""
    coins = sum(n * TREASURE["coin_value"][c] for c, n in hoard["coins"].items())
    return round(coins + sum(hoard["gems"]) + sum(hoard["jewellery"]))


def priced(values):
    """Values as a priced list: 2×50 gp, 100 gp."""
    gp = pick(TREASURE["coins"]["gp"])
    counts = Counter(values)
    return ", ".join((f"{counts[v]}×" if counts[v] > 1 else "") + f"{number(v)} {gp}" for v in sorted(counts))


def hoard_text(hoard):
    """A hoard in words: coins, gems and jewellery with their values, magic items."""
    parts = [f"{number(hoard['coins'][c])} {pick(TREASURE['coins'][c])}" for c in TREASURE["coin_value"]
             if hoard["coins"].get(c)]
    for what in ("gems", "jewellery"):
        values = hoard[what]
        if values:
            name = tr(f"treasure_{what}_one" if len(values) == 1 else f"treasure_{what}", n=len(values))
            parts.append(f"{name} ({priced(values)})")
    parts += [pick(m) for m in hoard["magic"]]
    return ", ".join(parts)


# Treasure, kept within the means of a place of adventure: the Old-School
# Essentials lair hoards (types A-O) are for a whole lair at full strength, so
# only the threat has one, in its lair, scaled (down, or up for a poor type in
# a dangerous place) to be worth about LAIR_GOLD on average for its danger and
# the size of the place; any other monster, and now and then an empty building, has the
# unguarded treasure of a dungeon level as dangerous as the place. About
# 750-2,000 gp in all at danger 1, 3,000-7,500 at 2, 10,000-20,000 at 3,
# 25,000-50,000 at 4 (cities nearer the top, villages nearer the bottom).
LAIR_GOLD = {1: 1200, 2: 3500, 3: 10000, 4: 22000}
LAIR_SIZE = {"village": 0.9, "town": 1, "castle": 1, "fortress": 1, "city": 1.15, "bigcity": 1.15}
LAIR_ROLLS = (6, 10)        # the threat's hoard: at least 6 rolls of its type, at most 10
LOOSE_BUILDINGS = 8         # empty buildings that may hide something, at most


def scaled(hoard, share, rng):
    """A hoard made richer or poorer by `share`: the coins multiplied, each gem and jewel there int(share) times
    and once more with the chance of what is left; each magic item kept with the chance `share` (never more than
    one of each)."""
    out = {"coins": {c: round(n * share) for c, n in hoard["coins"].items() if round(n * share)}}
    for what in ("gems", "jewellery"):
        out[what] = [x for x in hoard[what] for _ in range(int(share) + (rng.random() < share % 1))]
    out["magic"] = [x for x in hoard["magic"] if rng.random() < share]
    return out


def plan_treasure(s):
    """The threat's hoard in its lair (its treasure type, worth about LAIR_GOLD); in a building with
    monsters, treasure 3 times in 6, and in up to LOOSE_BUILDINGS empty ones 1 in 6: the unguarded treasure of a
    dungeon level as dangerous as the place. Lived-in houses keep their owners' savings."""
    rng = random.Random(f"wyrmurbigen-treasure-{s.seed}")
    danger = s.p["danger"]
    level = DANGER_LEVEL[danger]
    expert = level >= 4
    loose = next(t["items"] for t in TREASURE["unguarded"] if in_range(level, t["levels"]))
    found = {}

    def keep(b, hoard, where):
        """Note a hoard in a building, if there is anything in it."""
        text = hoard_text(hoard)
        if text:
            found[b.uid] = {"text": text, "value": hoard_value(hoard), "magic": len(hoard["magic"]),
                            "where": pick(where)}

    # the threat's own hoard, always there
    letter = s.situation.get("treasure") or TREASURE.get("dwellers_type", "")
    table = TREASURE["types"].get(letter or "-")
    if table:
        # several rolls of its type put together and scaled to LAIR_GOLD: the same worth on average, fewer
        # empty or enormous hoards
        share = LAIR_GOLD[danger] * LAIR_SIZE.get(s.p["type"], 1) / (table.get("average") or 1)
        rolls = min(LAIR_ROLLS[1], max(LAIR_ROLLS[0], math.ceil(share)))
        hoard = {"coins": {}, "gems": [], "jewellery": [], "magic": []}
        for _ in range(rolls):
            part = roll_hoard(table["items"], expert, rng)
            for c, n in part["coins"].items():
                hoard["coins"][c] = hoard["coins"].get(c, 0) + n
            for what in ("gems", "jewellery", "magic"):
                hoard[what] += part[what]
        magic = hoard["magic"]          # magic items: as many as in one hoard of the type, not one per roll
        hoard = scaled(hoard, share / rolls, rng)
        hoard["magic"] = [x for x in magic if rng.random() < min(1.0, share) / rolls]
        keep(s.lair, hoard, rng.choice(TREASURE["hiding"]["lair"]))
    # the other monsters, and a few of the empty buildings
    empty = [b for b in s.plan.buildings if b.uid in s.abandoned and b.uid not in s.occupants]
    looked = {b.uid for b in rng.sample(empty, min(LOOSE_BUILDINGS, len(empty)))}
    for b in s.plan.buildings:
        if b is s.lair or (b.uid not in s.occupants and b.uid not in looked):
            continue
        content = "monster" if b.uid in s.occupants else "empty"
        if rng.randint(1, 6) <= TREASURE["room_chance"][content]:
            keep(b, roll_hoard(loose, expert, rng), rng.choice(TREASURE["hiding"]["lair" if content == "monster"
                                                                                  else "loose"]))
    s.treasure = found


def treasure_line(t):
    """A treasure as a line of the key: what, where it is hidden, its value."""
    value = tr("treasure_value", v=number(t["value"])) if t["value"] else ""
    return tr("room_treasure", v=value, x=t["text"], w=t["where"])


# --- who matters: layered history, factions, main NPCs ---
# Every settlement has a layered history (strata): its founding and a few
# events, each with its age and the legacy it left (a grudge, a debt, a claim,
# a lost relic, a secret...). Factions and main NPCs are built on those
# legacies, from the tables of data/intrigue.json: what each faction wants and
# why, where each main NPC comes from, how they rose, what they want and hide,
# and whom they are tied to. A ruin's strata are its layers.
STRATA = {"village": 2, "town": 3, "city": 4, "bigcity": 4, "castle": 3, "fortress": 3}
FACTIONS = {"village": 2, "town": 3, "city": 4, "bigcity": 5, "castle": 2, "fortress": 2, "ruin": 3}
NOTABLES = {"village": 4, "town": 5, "city": 6, "bigcity": 7, "castle": 4, "fortress": 4, "ruin": 4}
FOUNDING_LEGACIES = ("claim", "wealth", "vow", "curse")


def gfill(entry, gender="m", **values):
    """(it, en) of a data entry with optional feminine forms, filled in."""
    return fmt(gendered(entry, gender), **values)


def relic(rng):
    """(it, en): a made-up relic, "the black crown of the founder"."""
    thing, quality = rng.choice(TABLES["relic_things"]), rng.choice(TABLES["relic_qualities"])
    return f"{thing['it']} {quality[thing['g']]}", f"{thing['en'].replace('the ', 'the ' + quality['en'] + ' ', 1)}"


def emblem(rng):
    """(it, en) of a faction's emblem: "del Corvo Bianco", "of the White Raven"; and the colour."""
    noun, colour = rng.choice(TABLES["emblem_nouns"]), rng.choice(TABLES["emblem_colours"])
    art = noun["art"] + ("" if noun["art"].endswith("'") else " ")
    return (f"{art}{noun['it']} {colour[noun['g']]}", f"of the {colour['en']} {noun['en']}"), colour


def cast(rng, s):
    """The fillers of a stratum: two families, a figure of the past, a god, a town, a relic."""
    p = s.p
    family = family2 = family_name(rng, p)
    for _ in range(10):
        if family2 != family:
            break
        family2 = family_name(rng, p)
    return {"n": s.name_pair, "family": (family,) * 2, "family2": (family2,) * 2,
            "person": person_name(rng, rng.choice("mf"), s.used_names), "god": god_name(rng, p),
            "place": (town_name(rng, p),) * 2, "relic": relic(rng), "dungeon": s.dungeon_name}


def stratum(label, text, short, legacy, values, when=None, mark=None):
    """One layer of the past: its label (an age), text, what to call it, the legacy it left, its fillers and the
    name it may leave on a building ("della Cometa")."""
    when = when or label
    values = dict(values, short=short, when=(when[0].lower(), when[1].lower()))
    return {"label": label, "text": text, "short": short, "legacy": legacy, "values": values, "mark": mark}


def plan_strata(s, rng):
    """s.strata: the founding and a few events, oldest first (inhabited places); a ruin's layers otherwise."""
    p, kind = s.p, s.p["type"]
    data = TABLES
    if hasattr(s, "layers"):
        shorts = data["ruin_layers"]
        names = ("height", "fall") + ("after",) * (len(s.layers) - 3)
        out = [stratum(s.layers[0][0], s.layers[0][1], fmt(("la fondazione di {n}", "the founding of {n}"), n=s.name_pair),
                       rng.choice(FOUNDING_LEGACIES), cast(rng, s), when=("secoli fa", "centuries ago"),
                       mark=rng.choice(data["founding_marks"]))]
        for (label, text), name in zip(s.layers[1:], names):
            short = {"height": ("i giorni dello splendore", "the days of glory"), "fall": ("la caduta", "the fall"),
                     "after": ("il saccheggio", "the sack")}[name]
            when = {"height": ("un tempo", "once"), "after": ("dopo la caduta", "after the fall")}.get(name)
            if name == "fall":      # "Caduta, 50 anni fa": the age after the comma
                when = tuple(part.split(", ", 1)[-1] for part in label)
            values = dict(cast(rng, s), **{k: v for k, v in s.ruin_cast.items() if k in ("family", "family2", "god")})
            mark = rng.choice(data["height_marks"]) if name == "height" else None
            out.append(stratum(label, text, short, rng.choice(shorts[name]), values, when=when, mark=mark))
        return out
    founding = stratum(("Fondazione", "Founding"), s.history[0], fmt(("la fondazione di {n}", "the founding of {n}"),
                                                                     n=s.name_pair),
                       rng.choice(FOUNDING_LEGACIES), cast(rng, s), when=("secoli fa", "centuries ago"),
                       mark=rng.choice(data["founding_marks"]))
    pool = [e for e in data["strata_events"] if allowed_in(e["where"], kind)
            and (not e.get("terrains") or p["terrain"] in e["terrains"])]
    events = rng.sample(pool, min(STRATA[kind], len(pool)))
    ages = sorted(rng.sample(range(len(data["ages"])), len(events)))
    out = [founding]
    for e, age in zip(events, ages):
        values = cast(rng, s)
        when = data["ages"][age]
        text = fmt(e["text"], **values)
        out.append(stratum((capitalized(when[0]), capitalized(when[1])), text, fmt(e["short"], **values),
                           rng.choice(e["legacies"]), values, when=when, mark=e["mark"]))
    return out


def ref(npc, home):
    """(it, en): a person and where they live: "Ruggilio Picoli (n. 12)"."""
    if home is None:
        return npc["name"]
    return tuple(f"{npc['name'][k]} ({tr_pair('ref_no')[k]} {home.number})" for k in (0, 1))


def building_ref(b):
    """(it, en): "n. 12 (Torre dei Picoli)"."""
    return tuple(f"{tr_pair('ref_no')[k]} {b.number} ({b.title[k]})" for k in (0, 1))


def plan_factions(s, rng):
    """s.factions: a few factions of the kinds this place can have, each rooted in a stratum of its past, with a
    goal, a way of working, a strength, a base, a leader, a rival and perhaps an ally."""
    p, plan = s.p, s.plan
    ruin = hasattr(s, "layers")
    kind = "ruin" if ruin else p["type"]
    kinds = [k for k in TABLES["faction_kinds"] if ("ruin" in k["where"]) == ruin and (ruin or allowed_in(k["where"], kind))
             and (not k.get("terrains") or p["terrain"] in k["terrains"])]
    rng.shuffle(kinds)
    taken, factions, goals = set(), [], set()
    gates = [g for g in getattr(s, "gates", []) if g.get("name")]
    for k in kinds[:FACTIONS[kind]]:
        roots = [st for st in s.strata if st["legacy"] in k["legacies"]] or s.strata
        st = rng.choice(roots)
        legacy = st["legacy"] if st["legacy"] in k["legacies"] else rng.choice(k["legacies"])
        mark, colour = emblem(rng)
        values = dict(st["values"], emblem=mark, guild=rng.choice(TABLES["guilds"]),
                      colour_m=(colour["m"], colour["en"]), colour_f=(colour["f"], colour["en"]), colour=colour["en"])
        name = gfill(rng.choice(k["names"]), **values)
        # the base: a building of the kind's, else none (around a ruin: a camp in a ruined building)
        if ruin:        # a building no monster holds, if there is one
            homes = [b for b in plan.buildings if b is not getattr(s, "lair", None) and b.uid not in taken]
            homes = [b for b in homes if b.uid not in getattr(s, "occupants", {})] or homes
        else:
            homes = [b for b in plan.buildings if b.id in k["hq"] and b.uid not in taken and b is not getattr(s, "lair", None)]
        hq = rng.choice(homes) if homes else None
        if hq is not None:
            taken.add(hq.uid)
        if hq is not None and getattr(hq, "npc", None) and not ruin:
            leader = hq.npc
        else:
            leader = make_npc(rng, s.used_names, None, None, rng.choice(("normal", "fighter", "thief", "cleric")),
                              rng.randint(1, 4))
            leader["role"] = gfill(k["leader"], leader["gender"], **values)
        where = "ruin" if ruin else "living"
        assets = [a for a in TABLES["faction_assets"] if (gates or "{gate}" not in gendered(a, "m")[0])
                  and where in (a.get("where", (where,)) if isinstance(a, dict) else (where,))]
        values["gate"] = rng.choice(gates)["name"] if gates else ("", "")
        goal = rng.choice([x for x in TABLES["legacies"][legacy]["goal"] if id(x) not in goals]
                          or TABLES["legacies"][legacy]["goal"])
        goals.add(id(goal))
        factions.append({"name": name, "kind": k, "stratum": st, "legacy": legacy,
                         "about": gfill(k["about"], **values), "power": rng.choice(TABLES["faction_powers"]),
                         "goal": gfill(goal, **values),
                         "method": gfill(rng.choice(k["methods"]), **values), "asset": gfill(rng.choice(assets), **values),
                         "hq": hq, "leader": leader, "camp": ruin})
    # rivals all round, and here and there an alliance
    for a, b in zip(factions, factions[1:] + factions[:1]):
        if a is not b:
            a["rival"] = (b, fmt(rng.choice(TABLES["faction_rivalry"]), **a["stratum"]["values"]))
    for f in factions:
        others = [o for o in factions if o is not f and o is not (f.get("rival") or (None,))[0]]
        if others and rng.random() < 0.45:
            f["ally"] = (rng.choice(others), fmt(rng.choice(TABLES["faction_alliance"]), **f["stratum"]["values"]))
    return factions


def plan_notables(s, rng):
    """s.notables: the main NPCs (the ruler, the threat's leader, the factions' leaders, a few keepers; around a
    ruin, the factions' leaders and a survivor), each with a story rooted in the strata, a motive with its why, a
    secret, a tie to another of them and a job for the characters."""
    p, plan = s.p, s.plan
    ruin = hasattr(s, "layers")
    kind = "ruin" if ruin else p["type"]
    chosen, seen = [], set()

    def add(npc, home, faction=None):
        """One main NPC, once."""
        if npc is not None and id(npc) not in seen:
            seen.add(id(npc))
            chosen.append({"npc": npc, "home": home, "faction": faction})
    if not ruin:
        add(s.ruler, s.ruler_seat)
    if getattr(s, "villain", None) and not getattr(s, "boss", None):
        add(s.villain, getattr(s, "lair", None))
    for f in s.factions:
        add(f["leader"], f["hq"], f)
    if ruin:
        survivor = make_npc(rng, s.used_names, None, None, "normal", None)
        survivor["role"] = gendered({"it": "sopravvissuto", "it_f": "sopravvissuta", "en": "survivor"}, survivor["gender"])
        add(survivor, None)
    else:
        keepers = [b for b in plan.buildings if getattr(b, "npc", None) and not b.kind.get("filler")]
        rng.shuffle(keepers)
        keepers.sort(key=lambda b: -b.kind.get("priority", 0))
        for b in keepers:
            if len(chosen) >= NOTABLES[kind]:
                break
            add(b.npc, b)
    legacies = TABLES["legacies"]
    taken = set()

    def fresh(pool):
        """An entry of `pool` not given to another notable yet (if there is one)."""
        left = [e for e in pool if id(e) not in taken] or pool
        e = rng.choice(left)
        taken.add(id(e))
        return e
    for nb in chosen:
        npc, g = nb["npc"], nb["npc"]["gender"]
        st = nb["faction"]["stratum"] if nb["faction"] else rng.choice(s.strata)
        legacy = nb["faction"]["legacy"] if nb["faction"] else st["legacy"]
        kin = rng.choice(TABLES["kin"])
        values = dict(st["values"], kin=kin, Kin=(capitalized(kin[0]), capitalized(kin[1])),
                      When=(capitalized(st["values"]["when"][0]), capitalized(st["values"]["when"][1])),
                      trade=rng.choice(TABLES["trades_pl"]))
        nb["values"] = values
        nb["story"] = [gfill(fresh(TABLES["origins"]), g, **values),
                       gfill(fresh(legacies[legacy]["past"]), g, **values),
                       gfill(fresh(TABLES["rises"]), g, **values)]
        npc["want"] = gfill(fresh(legacies[legacy]["want"]), g, **values)
        other = rng.choice(list(legacies)) if rng.random() < 0.4 else legacy
        npc["secret"] = gfill(fresh(legacies[other]["secret"]), g, **values)
        nb["stratum"] = st
    # ties: each of them with another, and the job they offer
    for nb in chosen:
        others = [o for o in chosen if o is not nb]
        if not others:
            nb["bonds"], nb["hook"] = [], None
            continue
        nb["bonds"] = []
        for o in rng.sample(others, min(len(others), 1 if rng.random() < 0.6 else 2)):
            bond = rng.choice(TABLES["bonds"])
            reason = fmt(rng.choice(TABLES["bond_reasons"]), **nb["values"])
            nb["bonds"].append(gfill(rng.choice(bond["text"]), nb["npc"]["gender"], other=ref(o["npc"], o["home"]),
                                     reason=reason, **{k: v for k, v in nb["values"].items() if k != "other"}))
        target = rng.choice(others)
        nb["hook"] = gfill(fresh(TABLES["npc_hooks"]), nb["npc"]["gender"], other=ref(target["npc"], target["home"]),
                           **nb["values"])
    return chosen


RENAMED = 0.2               # the share of family and owner buildings named after the past or the place instead
RENAMED_MAX = 6


def title_base(kind):
    """(it, en): what a building of `kind` is called without its family or owner ("Palazzo", "Palace"), or None."""
    for t in kind.get("title") or []:
        if "{family}" in t[0] or "{owner}" in t[0]:
            it = re.sub(r"\s*\b(?:dei|degli|di|del|della)?\s*\{(?:family|owner)\}", "", t[0]).strip()
            en = re.sub(r"\{(?:family|owner)\}(?:'s)?\s*", "", t[1]).strip()
            if it and en and "{" not in it + en:
                return it, en
    return None


def rename_buildings(s, rng):
    """In addition to the names from families and owners: a few buildings named after a layer of the past
    ("Villa della Cometa", "Isolato della Peste") or a trait of the place ("Palazzo del Guado"), with the reason
    kept for the key (b.named)."""
    p, ruin = s.p, hasattr(s, "layers")
    traits = [t for t in TABLES["place_traits"] if not t.get("terrains") or p["terrain"] in t["terrains"]]
    local, common = [t for t in traits if t.get("terrains")], [t for t in traits if not t.get("terrains")]
    chosen = rng.sample(local, min(1, len(local))) + rng.sample(common, min(1, len(common)))
    marks = [("stratum", st, st["mark"]) for st in s.strata if st.get("mark")]
    marks += [("trait", t, (t["it"], t["en"])) for t in chosen]
    bases = {b.uid: title_base(b.kind) for b in s.plan.buildings if not b.kind.get("filler")}
    candidates = [b for b in s.plan.buildings if bases.get(b.uid) and b is not getattr(s, "lair", None)]
    if not ruin:            # row houses and blocks too: "Isolato della Peste"
        candidates += [b for b in s.plan.buildings if b.kind.get("filler") and b is not getattr(s, "lair", None) and pick(b.title) in
                       ("Case a schiera", "Row houses", "Isolato", "Block")]
    if not marks or not candidates:
        return
    n = min(RENAMED_MAX, max(1, round(len(candidates) * RENAMED)), len(candidates))
    rng.shuffle(marks)
    for k, b in enumerate(rng.sample(candidates, n)):
        what, source, mark = marks[k % len(marks)]
        base = bases.get(b.uid) or b.title
        b.title = (f"{base[0]} {mark[0]}", f"{base[1]} {mark[1]}")
        if what == "stratum":
            b.named = tr_pair("named_after"), {"x": source["short"], "w": source["values"]["when"]}
        else:
            b.named = tr_pair("named_trait"), {"x": fmt(gendered(source["why"], "m"), place=(town_name(rng, p),) * 2)}


def plan_past(s):
    """The layered history (a ruin's comes with its threat) and the dungeon nearby, and the buildings named after
    them; from a generator of their own, so the rest of a seed's settlement does not change."""
    rng = random.Random(f"wyrmurbigen-past-{s.seed}")
    s.dungeon_name = fmt(rng.choice(TABLES["dungeons"]),
                         x=(place_name(rng, None, s.p.get("names"), s.p.get("tone")),) * 2)
    s.strata = plan_strata(s, rng)
    rename_buildings(s, rng)


def plan_intrigue(s):
    """The factions and the main NPCs, rooted in the layered history (plan_past), from a generator of their own
    (the rest of a seed's settlement does not change with them)."""
    rng = random.Random(f"wyrmurbigen-intrigue-{s.seed}")
    s.factions = plan_factions(s, rng)
    s.notables = plan_notables(s, rng)


def rumour_values(s, rng):
    """The fillers a rumour may use, all from this settlement: its people, main NPCs, factions, families, gods,
    towns, past, buildings and threat."""
    npcs = [b for b in s.plan.buildings if getattr(b, "npc", None)]
    st = rng.choice(s.strata)
    family = family2 = family_name(rng, s.p)
    for _ in range(10):
        if family2 != family:
            break
        family2 = family_name(rng, s.p)
    place = place2 = town_name(rng, s.p)
    for _ in range(10):
        if place2 != place:
            break
        place2 = town_name(rng, s.p)
    values = {"family": (family,) * 2, "family2": (family2,) * 2,
              "god": god_name(rng, s.p), "place": (place,) * 2, "place2": (place2,) * 2, "dungeon": s.dungeon_name,
              "Dungeon": (capitalized(s.dungeon_name[0]), capitalized(s.dungeon_name[1])), "n": s.name_pair,
              "short": st["short"], "when": st["values"]["when"], "relic": st["values"]["relic"]}
    if npcs and not hasattr(s, "layers"):
        b = rng.choice(npcs)
        values["npc"] = ref(b.npc, b)
    if s.plan.buildings:
        values["bref"] = building_ref(rng.choice(s.plan.buildings))
        b = rng.choice(s.plan.buildings)
        values["bthe"] = (f"il {tr_pair('ref_no')[0]} {b.number} ({b.title[0]})",
                          f"no. {b.number} ({b.title[1]})")
    if s.notables:
        nb = rng.choice(s.notables)
        values["notable"] = ref(nb["npc"], nb["home"])
    if s.factions:
        f = rng.sample(s.factions, min(2, len(s.factions)))
        values["faction"] = f[0]["name"]
        if len(f) > 1:
            values["faction2"] = f[1]["name"]
    if getattr(s, "situation", None):
        values["dwellers"] = s.dwellers
        if s.dwellers[0].split(" ")[0] in ("i", "gli", "le"):
            values["dwellers_pl"] = s.dwellers
        values["lair"] = building_ref(s.lair)
        names = getattr(s, "monster_names", None)
        if names:
            values["monster"] = (rng.choice(names),) * 2
    return values


RUMOURS = 10                # the rumours table: a d10
THREAT_RUMOURS = 3          # ... of which about the threat, in a place of adventure
KIT_SHARE = 0.6             # how often a rumour comes from a kit rather than the list of contents
TERRAIN_SHARE = 0.3         # ... and how often from the contents of the place's own terrain, if it has some


def expand_kit(kit):
    """Every rumour a kit makes: its text with each slot filled by each of its pieces, in every combination; a
    rumour fits where all its pieces fit."""
    out = [{"it": kit["text"][0], "en": kit["text"][1], "where": {"living", "ruin"}}]
    for slot, pieces in kit["parts"].items():
        grown = []
        for c in out:
            for piece in pieces:
                pair = piece if isinstance(piece, tuple) else (piece["it"], piece["en"])
                where = set(piece["where"]) if isinstance(piece, dict) and "where" in piece else {"living", "ruin"}
                grown.append({"it": c["it"].replace("{" + slot + "}", pair[0]),
                              "en": c["en"].replace("{" + slot + "}", pair[1]), "where": c["where"] & where})
        out = grown
    return [c for c in out if c["where"]]


RUMOUR_KITS = [expand_kit(k) for k in TABLES["rumor_kits"]]


def plan_rumours(s, rng):
    """s.rumours: RUMOURS rumours, each told by someone in some way, true, false or partly true (with what is wrong
    for the referee); a few about the threat in a place of adventure."""
    where = "ruin" if hasattr(s, "layers") else "living"
    threat_keys = ("dwellers", "dwellers_pl", "lair", "monster")
    contents = [c for c in TABLES["rumor_contents"] if where in c["where"]
                and (not c.get("terrains") or s.p["terrain"] in c["terrains"])]
    kits = [[c for c in kit if where in c["where"]] for kit in RUMOUR_KITS]
    out, used = [], set()
    wanted_threat = THREAT_RUMOURS if getattr(s, "situation", None) else 0
    tries = 0
    while len(out) < RUMOURS and tries < 400:
        tries += 1
        values = rumour_values(s, rng)
        about_threat = len(out) < wanted_threat
        # from the list, or from a kit (one kit as likely as another, whatever its size)
        own = [c for c in contents if c.get("terrains")]
        roll = rng.random()
        table = own if own and roll < TERRAIN_SHARE else rng.choice([k for k in kits if k]) if roll < KIT_SHARE \
            else contents
        pool = [c for c in table if (any("{" + k + "}" in c["it"] for k in threat_keys) == about_threat)
                and all(key in values for key in re.findall(r"\{(\w+)\}", c["it"]))]
        if not pool:
            continue
        c = rng.choice(pool)
        if c["it"] in used:
            continue
        used.add(c["it"])
        source = rng.choice(TABLES["rumor_sources"])
        verbs = [v for v in TABLES["rumor_verbs"] if "in piazza" not in gendered(v, "m")[0] or "in piazza" not in source["it"]]
        verb = gendered(rng.choice(verbs), source["g"])      # not "in the square" twice
        text = fmt((f"{source['it']} {verb[0]} {c['it']}.", f"{source['en']} {verb[1]} {c['en']}."), **values)
        truth = rng.choices(("true", "false", "partial"), weights=(5, 3, 2))[0]
        twist = fmt(rng.choice(TABLES["rumor_twists"]), **values) if truth == "partial" else None
        out.append((text, truth, twist))
    rng.shuffle(out)
    return out


# --- rumours, events, hooks, retainers ---
def plan_lore(s):
    """Rumours, events, adventure hooks and retainers for hire, filled in with the settlement's own people,
    buildings, families and dungeon."""
    rng = s.rng_lore
    npcs = [b for b in s.plan.buildings if getattr(b, "npc", None)]
    dungeon_name = s.dungeon_name

    def fill(entry):
        """Fill a text template with a random person, building, place, family, god, dungeon..."""
        b = rng.choice(npcs) if npcs else None
        other = rng.choice(s.plan.buildings) if s.plan.buildings else None
        values = {"npc": (f"{b.npc['name'][0]} ({tr_pair('ref_no')[0]} {b.number})",
                          f"{b.npc['name'][1]} ({tr_pair('ref_no')[1]} {b.number})") if b else ("qualcuno", "someone"),
                  "building": (f"{other.title[0]} ({tr_pair('ref_no')[0]} {other.number})",
                               f"{other.title[1]} ({tr_pair('ref_no')[1]} {other.number})") if other else ("", ""),
                  "dungeon": dungeon_name, "Dungeon": (capitalized(dungeon_name[0]), capitalized(dungeon_name[1])),
                  "place": (town_name(rng, s.p),) * 2, "family": (family_name(rng, s.p),) * 2,
                  "god": god_name(rng, s.p), "n": s.name_pair,
                  "person": person_name(rng, rng.choice("mf"), s.used_names)}
        if getattr(s, "situation", None):
            values["dwellers"] = s.dwellers
            values["Dwellers"] = (capitalized(s.dwellers[0]), capitalized(s.dwellers[1]))
            values["lair"] = (f"{tr_pair('ref_no')[0]} {s.lair.number}", f"{tr_pair('ref_no')[1]} {s.lair.number}")
            values["monster"] = (getattr(s, "monster_names", ["?"]) or ["?"])[0], \
                (getattr(s, "monster_names", ["?"]) or ["?"])[0]
        if isinstance(entry, tuple):
            return pick(fmt(entry, **values)), True
        return pick(fmt((entry["it"], entry["en"]), **values)), entry.get("true", True)

    # the rumours table, from the rumour generator
    ruin = hasattr(s, "layers")
    s.rumours = plan_rumours(s, rng)
    # six events and four adventure hooks
    s.events = [fill(e)[0] for e in rng.sample(TABLES["ruin_events" if ruin else "events"], 6)]
    s.hooks = [fill(h)[0] for h in rng.sample(TABLES["ruin_hooks" if ruin else "hooks"], 4)]
    # retainers and mercenaries for hire
    rows = []
    for r in rng.sample(TABLES["retainers"], rng.randint(3, 6)):
        n = roll("1d4", rng) + (2 if s.p["type"] in ("city", "bigcity", "fortress") else 0)
        rows.append((r["name"], n, r["wage"], r["stats"]))
    s.mercenaries = rows
    hirelings = []
    for _ in range(rng.randint(1, 3)):
        cls = rng.choice(("fighter", "fighter", "cleric", "thief", "mu", "dwarf", "elf", "halfling"))
        npc = make_npc(rng, s.used_names, TABLES["classes"][cls], None, cls, rng.randint(1, 2))
        hirelings.append(npc)
    s.hirelings = hirelings


def tr_pair(key):
    """The (it, en) pair of a text key, for texts that need both languages."""
    return TEXTS[key]



# --- fonts and glyphs ---
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def font_file(name):
    """The path of a font in the fonts folder."""
    return os.path.join(FONT_DIR, name)


def open_font(spec, size):
    """A font at a size, from a path or a (path, index) pair (.ttc collections)."""
    path, index = spec if isinstance(spec, tuple) else (spec, 0)
    return ImageFont.truetype(path, size, index=index)


def find_font(chosen=None):
    """Returns (regular, bold or None)."""
    candidates = []
    if chosen:
        candidates.append((chosen, None))
    candidates.append((font_file("DejaVuSansMono.ttf"), font_file("DejaVuSansMono-Bold.ttf")))
    candidates += MONO_FONTS
    for regular, bold in candidates:
        try:
            open_font(regular, 20)
        except OSError:
            continue
        try:
            if bold is None:
                raise OSError
            open_font(bold, 20)
        except OSError:
            bold = None
        return regular, bold
    sys.exit(tr("err_no_font"))


def font_name(spec):
    """The file name of a font spec, for messages."""
    return os.path.basename(spec[0] if isinstance(spec, tuple) else spec)


def font_metrics(spec):
    """A font's letter width and line height, as fractions of its size."""
    f = open_font(spec, 200)
    ascent, descent = f.getmetrics()
    return f.getlength("M") / 200, (ascent + descent) / 200


def font_has_glyph(font, ch):
    """Whether the font really draws `ch` (not the empty box of a missing glyph)."""
    def fingerprint(c):
        """The pixels of a character drawn alone."""
        img = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(img).text((10, 10), c, font=font, fill=255)
        return img.tobytes()
    missing = fingerprint("\U0010FFFD")
    return fingerprint(ch) != missing and any(fingerprint(ch))


class Glyphs:
    """G("≈", "~") -> "≈", or "~" with --ascii-only or if the font lacks ≈."""

    def __init__(self, font, ascii_only):
        """Symbol chooser for a font; `ascii_only` forces the keyboard symbols."""
        self.ascii_only = ascii_only
        self.missing = set()
        self._cache = {}
        self.font = font

    def __call__(self, fancy, plain):
        """The fancy symbol, or the plain one if keyboard characters only are wanted or the font lacks a glyph
        (remembered in `missing` for a warning)."""
        if self.ascii_only:
            return plain
        if fancy not in self._cache:
            self._cache[fancy] = all(c.isascii() or font_has_glyph(self.font, c) for c in fancy)
            if not self._cache[fancy]:
                self.missing.add(fancy)
        return fancy if self._cache[fancy] else plain


class Canvas:
    """Grid of characters, each with a style (n normal, b bold, i white on
    black), a tag (what it is: its colour on a colour map) and a fill (the
    colour of the ground under it, ditto)."""

    def __init__(self, width, height):
        """An empty canvas of width x height letters."""
        self.width, self.height = width, height
        self.chars = [[" "] * width for _ in range(height)]
        self.styles = [["n"] * width for _ in range(height)]
        self.tags = [[None] * width for _ in range(height)]
        self.fills = [[None] * width for _ in range(height)]

    def put(self, x, y, ch, style="n", tag=None):
        """Set one letter with its style and colour tag (ignored off the canvas)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.chars[y][x], self.styles[y][x], self.tags[y][x] = ch, style, tag

    def fill(self, x, y, key):
        """Set the background fill of one cell (colour maps)."""
        if 0 <= x < self.width and 0 <= y < self.height:
            self.fills[y][x] = key

    def write(self, x, y, text, style="n", tag=None, fill=None):
        """Write a text from x, y rightwards, all in one style, tag and fill."""
        for i, c in enumerate(text):
            self.put(x + i, y, c, style, tag)
            if fill:
                self.fill(x + i, y, fill)

    def paste(self, other, ox, oy):
        """Copy another canvas onto this one at ox, oy; its blank cells leave this one's untouched."""
        for y in range(other.height):
            for x in range(other.width):
                if other.fills[y][x]:
                    self.fill(ox + x, oy + y, other.fills[y][x])
                if other.chars[y][x] != " " or other.styles[y][x] != "n":
                    self.put(ox + x, oy + y, other.chars[y][x], other.styles[y][x], other.tags[y][x])

    def lines(self):
        """The canvas as text lines, trailing blanks removed."""
        return ["".join(row).rstrip() for row in self.chars]


# (fancy, keyboard) for every symbol of the map; the keyboard ones are WyrmHex's
SYMBOLS = {
    "wall": ("▓", "#"), "tower": ("█", "@"), "gate": ("+", "+"), "palisade": ("▒", "%"),
    "ditch": ("░", ":"), "water": ("≈", "~"), "bridge": ("=", "="), "street": (".", "."), "road": ("·", "."),
    "garden": ("τ", "v"), "grave": ("Ω", "i"), "mound": ("∩", "n"), "rubble": ("∴", "*"),
    "secret": ("$", "$"), "tunnel": ("░", ":"), "brambles": ("ψ", "&"), "cliff": ("Λ", "/"), "stairs": ("≣", ">"),
    "well": ("○", "o"), "fountain": ("Θ", "O"), "stall": ("π", "h"), "tree": ("♣", "T"),
    "forest1": ("♣", "T"), "forest2": ("♠", "Y"), "hill": ("∩", "n"), "mount": ("▲", "^"),
    "shroom": ("⊤", "f"), "spores": ("°", "o"),       # giant mushrooms (wide caps on tall stems) and spores, as in WyrmHex
    "reed1": ("⌠", ","), "reed2": ('"', ";"),
    "plough": ("≡", "_"), "sown": ("τ", "v"), "pasture": ('"', '"'), "orchard": ("♣", "T"),
}
# buildings: with keyboard letters only, NetHack style (stone = and H, timber - and |), so they never
# look like the town walls (#) and towers (@)
DOUBLE = {"h": ("═", "="), "v": ("║", "H"), "tl": ("╔", "="), "tr": ("╗", "="), "bl": ("╚", "="), "br": ("╝", "=")}
SINGLE = {"h": ("─", "-"), "v": ("│", "|"), "tl": ("┌", "-"), "tr": ("┐", "-"), "bl": ("└", "-"), "br": ("┘", "-")}


GROUND_TAGS = {"water": "water", "tree": "forest", "shroom": "shroom", "hill": "hill", "mount": "mount", "reed": "reed",
               "cliff": "mount", "rock": "rock", "magma": "magma", "moss": "moss"}


def ground_tag(g):
    """The colour tag of a ground: forest, hill... or the field's kind."""
    return g[6:] if g.startswith("field:") else GROUND_TAGS.get(g)


def ground_char(plan, x, y, G):
    """The letter of the bare ground at x, y: water, trees, hills, mountains, reeds or fields, spaced out by the
    texture so the map breathes."""
    g = plan.ground[y][x]
    t = plan.tex[y][x]
    if g == "water":
        return G(*SYMBOLS["water"])
    if g == "tree":
        return G(*SYMBOLS["forest1" if t < 0.45 else "forest2"]) if t < 0.75 else " "
    if g == "shroom":
        return G(*SYMBOLS["shroom" if t < 0.5 else "spores"]) if t < 0.7 else " "
    if g == "rock":         # solid rock is left blank; its face, where it meets open space, as in WyrmDelve's caves
        return "#" if (x, y) in getattr(plan, "face", ()) else " "
    if g == "magma":
        return G(*SYMBOLS["water"])
    if g == "moss":
        return '"' if t < 0.2 else " "
    if g == "hill":
        return G(*SYMBOLS["hill"])
    if g == "mount":
        return G(*SYMBOLS["mount"])
    if g == "cliff":
        return G(*SYMBOLS["cliff"])
    if g == "reed":
        return G(*SYMBOLS["reed1" if t < 0.2 else "reed2"])
    if g.startswith("field:"):
        kind = g[6:]
        if kind == "orchard":
            return G(*SYMBOLS["orchard"]) if x % 4 == 0 and y % 2 == 0 else " "
        if kind == "plough":
            return G(*SYMBOLS["plough"]) if t < 0.5 else " "
        if kind == "sown":
            return G(*SYMBOLS["sown"]) if t < 0.35 else " "
        if kind == "pasture":
            return G(*SYMBOLS["pasture"]) if t < 0.22 else " "
    return " "


RUIN_BREACH, RUIN_BRAMBLES = 0.15, 0.6      # ruins: walls below this texture fall, streets above it grow wild


def map_canvas(plan, referee, G, labels=True, secrets=None):
    """The map as letters. referee: building numbers and (unless `secrets` is
    False) the secret posterns and tunnel."""
    secrets = referee if secrets is None else secrets
    ruin = getattr(plan, "ruin", False)
    W, H = plan.W, plan.H
    c = Canvas(W, H)
    # every cell: its background fill (colour maps), then its symbol: a feature, the bare ground, or what is built
    # there
    for y in range(H):
        for x in range(W):
            cell = plan.cell[y][x]
            if cell in (STREET, SQUARE, YARD):
                c.fill(x, y, "bg:street")
            elif cell == MOAT or (cell is None and plan.ground[y][x] == "water"):
                c.fill(x, y, "bg:water")
            elif cell is None and plan.ground[y][x] == "rock":
                c.fill(x, y, "bg:rock")
            if (x, y) in plan.feat and cell not in (BLDG,) + tuple(FORT):
                feat = plan.feat[(x, y)]
                c.put(x, y, G(*SYMBOLS[feat]), "b" if feat in ("well", "fountain") else "n", feat)
                continue
            if cell is None:
                c.put(x, y, ground_char(plan, x, y, G), "n", ground_tag(plan.ground[y][x]))
            elif ruin and cell in (WALL, TOWER, PALISADE) and plan.tex[y][x] < RUIN_BREACH:
                c.put(x, y, G(*SYMBOLS["rubble"]), "n", "rubble")         # a breach in the walls of a ruin
            elif cell in (WALL, TOWER, PALISADE, DITCH, BRIDGE, MOUND):
                c.put(x, y, G(*SYMBOLS[cell]), "b" if cell == BRIDGE else "n", cell)
            elif cell == MOAT:
                c.put(x, y, G(*SYMBOLS["water"]), "n", "water")
            elif cell == GATE:
                c.put(x, y, "+", "b", "gate")
            elif cell == PIER:
                c.put(x, y, "=", "b", "bridge")
            elif cell in (STREET, SQUARE, YARD):
                bramble = ruin and plan.tex[y][x] > RUIN_BRAMBLES
                if bramble:
                    c.put(x, y, G(*SYMBOLS["brambles"]), "n", "garden")
                elif (x, y) in plan.stairs and (x + y) % 2 == 0:
                    c.put(x, y, G(*SYMBOLS["stairs"]), "n", "street")      # a flight of steps, with landings
                else:
                    c.put(x, y, ".", "n", "street")
            elif cell == ROAD:
                c.put(x, y, G(*SYMBOLS["road"]), "n", "road")
            elif cell == GARDEN:
                c.put(x, y, G(*SYMBOLS["garden"]) if plan.tex[y][x] < 0.16 else " ", "n", "garden")
            elif cell == GRAVE:
                c.put(x, y, G(*SYMBOLS["grave"]) if x % 2 == 0 else " ", "n", "grave")
    # the buildings on top, then the secret ways
    for b in plan.buildings:
        draw_building(c, b, G, referee and labels)
    if secrets:
        for x, y in plan.tunnel:
            if plan.bmap[y][x] < 0 and plan.cell[y][x] not in FORT:
                c.put(x, y, G(*SYMBOLS["tunnel"]), "n", "secret")
        for x, y in plan.secret:
            c.put(x, y, "$", "b", "secret")
    # gate letters on the road just outside, as WyrmDelve's [A] entrances
    for g in plan.gates:
        if g.get("letter") and g.get("outer"):
            x, y = g["outer"]
            dx, dy = round(math.cos(g["angle"]) * 2), round(math.sin(g["angle"]))
            x, y = x + dx, y + dy
            c.write(x - 1, y, f"[{g['letter']}]", "i", "entrance")
    return c


def draw_building(c, b, G, numbered):
    """Draw a building: its outline (double lines for stone, single for timber), rubble if ruined, its door and,
    when `numbered`, its number in the middle."""
    t = DOUBLE if b.stone else SINGLE
    tag = "stone" if b.stone else "wood"
    x0, y0, x1, y1 = b.x0, b.y0, b.x0 + b.w - 1, b.y0 + b.h - 1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
            # which part of the outline this cell is: a corner, a side, or inside
            edge = None
            if (x, y) == (x0, y0):
                edge = "tl"
            elif (x, y) == (x1, y0):
                edge = "tr"
            elif (x, y) == (x0, y1):
                edge = "bl"
            elif (x, y) == (x1, y1):
                edge = "br"
            elif y in (y0, y1):
                edge = "h"
            elif x in (x0, x1):
                edge = "v"
            if not b.ruined:
                c.fill(x, y, "bg:" + tag)
            if edge is None:
                ch = " "
                if b.ruined and ((x * 7 + y * 13) % 5 == 0):
                    ch = G(*SYMBOLS["rubble"])
                c.put(x, y, ch, "n", "rubble")
            elif b.ruined and ((x * 11 + y * 5) % 4 == 0):
                c.put(x, y, G(*SYMBOLS["rubble"]), "n", "rubble")
            else:
                c.put(x, y, G(*t[edge]), "n", tag)
    if b.door and not b.ruined:
        c.put(b.door[0], b.door[1], "+", "n", "door")
    if numbered:
        label = str(b.number)
        lx = x0 + (b.w - len(label)) // 2
        ly = y0 + b.h // 2
        c.write(lx, ly, label, "b", "number")


# --- legend and page ---
def scale_bar(plan, units):
    """A scale bar of a round length, in letters across."""
    col_m = plan.row_m / ASPECT
    if units == "imperial":
        per_col, unit, options = col_m * 3.28084, "ft", (10, 20, 25, 50, 100, 200, 250, 500, 1000, 2000)
    else:
        per_col, unit, options = col_m, "m", (5, 10, 20, 25, 50, 100, 200, 250, 500, 1000)
    best = min(options, key=lambda v: abs(v / per_col - 14))
    n = max(3, round(best / per_col))
    row = plan.row_m * (3.28084 if units == "imperial" else 1)
    return n, best, unit, row


def legend_entries(plan, p, referee, G, units, secrets=None):
    """The legend: a sample and a name for every symbol actually on the map, then the scale bar. Entries are lists
    of (text, style[, tag, fill]); `secrets` adds the referee's ones."""
    secrets = referee if secrets is None else secrets
    # what is on the map: only those symbols get an entry
    used = set()
    for y in range(plan.H):
        for x in range(plan.W):
            used.add(plan.cell[y][x])
            used.add(plan.ground[y][x])
    # buildings, walls and gates, water, streets and roads, features, fields and land, secrets, scale: in this order
    out = []
    if any(b.stone for b in plan.buildings):
        stone = "lg_carved" if p.get("terrain") == "underground" else "lg_stone"
        out.append([(G("╔═╗", "=H="), "n", "stone", "bg:stone"), (" " + tr(stone), "n")])
    if any(not b.stone for b in plan.buildings):
        wood = "lg_grown" if p.get("terrain") == "fungus" else "lg_wood"
        out.append([(G("┌─┐", "-|-"), "n", "wood", "bg:wood"), (" " + tr(wood), "n")])
    out.append([("+", "n", "door"), (" " + tr("lg_door"), "n")])
    if referee:
        out.append([("12", "b", "number"), (" " + tr("lg_number"), "n")])
    if any(b.ruined for b in plan.buildings) or getattr(plan, "ruin", False):
        out.append([(G(*SYMBOLS["rubble"]), "n", "rubble"), (" " + tr("lg_ruin"), "n")])
    for key, label in ((WALL, "lg_wall"), (TOWER, "lg_tower"), (PALISADE, "lg_palisade")):
        if key in used:
            out.append([(G(*SYMBOLS[key]), "n", key), (" " + tr(label), "n")])
    if GATE in used:
        out.append([("+", "b", "gate"), (" " + tr("lg_gate"), "n")])
    if any(g.get("letter") for g in plan.gates):
        out.append([("[A]", "i", "entrance"), (" " + tr("lg_gate_tag"), "n")])
    if DITCH in used:
        out.append([(G(*SYMBOLS["ditch"]), "n", "ditch"), (" " + tr("lg_ditch"), "n")])
    if MOAT in used or "water" in used:
        out.append([(G(*SYMBOLS["water"]), "n", "water", "bg:water"), (" " + tr("lg_water"), "n")])
    if BRIDGE in used or PIER in used:
        out.append([("=", "b", "bridge"), (" " + tr("lg_bridge"), "n")])
    if MOUND in used:
        out.append([(G(*SYMBOLS["mound"]), "n", "mound"), (" " + tr("lg_mound"), "n")])
    out.append([(".", "n", "street", "bg:street"), (" " + tr("lg_street"), "n")])
    if plan.stairs:
        out.append([(G(*SYMBOLS["stairs"]), "n", "street", "bg:street"), (" " + tr("lg_stairs"), "n")])
    if getattr(plan, "ruin", False):
        out.append([(G(*SYMBOLS["brambles"]), "n", "garden"), (" " + tr("lg_brambles"), "n")])
    if ROAD in used:
        out.append([(G(*SYMBOLS["road"]), "n", "road"), (" " + tr("lg_road"), "n")])
    if GARDEN in used:
        out.append([(G(*SYMBOLS["garden"]), "n", "garden"), (" " + tr("lg_garden"), "n")])
    if GRAVE in used:
        out.append([(G(*SYMBOLS["grave"]), "n", "grave"), (" " + tr("lg_grave"), "n")])
    feats = set(plan.feat.values())
    for key in ("well", "fountain", "stall"):
        if key in feats:
            out.append([(G(*SYMBOLS[key]), "b" if key != "stall" else "n", key), (" " + tr("lg_" + key), "n")])
    fields_used = {g[6:] for g in used if isinstance(g, str) and g.startswith("field:")}
    for key in ("plough", "sown", "pasture", "orchard"):
        if key in fields_used:
            out.append([(G(*SYMBOLS[key]), "n", key), (" " + tr("lg_" + key), "n")])
    if "rock" in used:
        out.append([("#", "n", "rock"), (" " + tr("lg_rock"), "n")])
    if "magma" in used:
        out.append([(G(*SYMBOLS["water"]), "n", "magma"), (" " + tr("lg_magma"), "n")])
    if "moss" in used:
        out.append([('"', "n", "moss"), (" " + tr("lg_moss"), "n")])
    if "shroom" in used or "shroom" in feats:
        out.append([(G(SYMBOLS["shroom"][0] + SYMBOLS["spores"][0], SYMBOLS["shroom"][1] + SYMBOLS["spores"][1]), "n",
                     "shroom"), (" " + tr("lg_shroom"), "n")])
    for key, sym, label in (("tree", "forest1", "lg_forest"), ("hill", "hill", "lg_hill"), ("mount", "mount", "lg_mount"),
                            ("cliff", "cliff", "lg_cliff"), ("reed", "reed1", "lg_reed")):
        if key in used:
            out.append([(G(*SYMBOLS[sym]), "n", ground_tag(key)), (" " + tr(label), "n")])
    if secrets and plan.secret:
        out.append([("$", "b", "secret"), (" " + tr("lg_secret"), "n")])
    if secrets and plan.tunnel:
        out.append([(G(*SYMBOLS["tunnel"]), "n", "secret"), (" " + tr("lg_tunnel"), "n")])
    n, length, unit, row = scale_bar(plan, units)
    bar_text = G("├" + "─" * (n - 2) + "┤", "|" + "-" * (n - 2) + "|")
    out.append([(tr("lg_scale"), "b"), (" " + bar_text + f" {number(length)} {unit}", "n"),
                (tr("lg_row", r=f"{row:.1f}".replace(".", "," if LANG == "it" else "."), u=unit), "n")])
    return out


def building_index(s):
    """(number, name) of every building, as everybody sees it."""
    return [(b.number, pick(b.title)) for b in sorted(s.plan.buildings, key=lambda b: b.number)]


def building_secrets(s):
    """What only the referee knows of the buildings: the thieves' hideout, the
    threat's lair, where the secret tunnel starts."""
    out = []
    for b in sorted(s.plan.buildings, key=lambda b: b.number):
        notes = []
        if b.kind.get("secret"):
            notes.append(pick(b.kind["secret"]))
        if b is getattr(s, "lair", None):
            notes.append(tr("ix_lair", d=pick(s.dwellers)))
        if b is s.plan.tunnel_from and s.plan.tunnel:
            notes.append(tr("ix_tunnel"))
        if notes:
            out.append(f"{b.number} {', '.join(notes)}")
    return out


def pack_legend(entries, width):
    """Lay legend entries out in lines no wider than `width`, four spaces apart."""
    lines, line, used = [], [], 0
    for entry in entries:
        w = sum(len(item[0]) for item in entry)
        extra = w + (4 if line else 0)
        if line and used + extra > width:
            lines.append(line)
            line, used = [], 0
            extra = w
        line.append(entry)
        used += extra
    if line:
        lines.append(line)
    return lines


def legend_width(line):
    """The width of a legend line, spaces included."""
    return sum(len(item[0]) for entry in line for item in entry) + 4 * (len(line) - 1)


INDEX_GAP = 3           # letters between two columns of the building index
INDEX_MAX = 40          # longest entry of the building index


class Layout:
    """Title, subtitle, the map, the legend and the building index (number -
    place, in columns): the page in letters."""

    def __init__(self, panel, legend, title, subtitle, index=(), secrets=(), side=False, motto=None):
        """Work out the page in letters: how wide and tall, where the map goes, the legend lines and the building
        index in columns (beside the map when `side`)."""
        self.panel = panel
        self.index, self.index_rows, self.side = list(index), [], side and bool(index)
        if self.index:
            self.index_digits = len(str(max(n for n, _ in self.index)))
            self.index_width = min(INDEX_MAX, max(self.index_digits + 1 + len(t) for _, t in self.index))
        block = 0
        if self.side:               # columns as tall as the map, beside it
            nrows = max(1, panel.height - 2)
            self.index_cols = -(-len(self.index) // nrows)
            nrows = -(-len(self.index) // self.index_cols)
            self.index_rows = [self.index[r::nrows] for r in range(nrows)]
            block = 2 * INDEX_GAP + self.index_cols * (self.index_width + INDEX_GAP) - INDEX_GAP
        inner = max(panel.width + block, len(title) + 4, len(subtitle) + 4, 60)
        if self.index and not self.side:    # columns as wide as the page, under the legend
            ncols = max(1, (inner + INDEX_GAP) // (self.index_width + INDEX_GAP))
            nrows = -(-len(self.index) // ncols)
            self.index_cols = -(-len(self.index) // nrows)
            self.index_rows = [self.index[r::nrows] for r in range(nrows)]
        self.legend = pack_legend(legend, inner)
        # the referee's secrets, one line or more under the legend
        notes = [[(tr("ix_secrets"), "b", "secret")]] + [[(t, "n")] for t in secrets] if secrets else []
        self.secrets = pack_legend(notes, inner)
        self.title, self.subtitle, self.motto = title, subtitle, motto
        self.cols = inner + 4
        self.top = (4 if title else 3) + (1 if motto else 0)
        self.panel_x = (self.cols - panel.width - block) // 2
        self.rows = (self.top + 1 + max(panel.height, len(self.index_rows) + 2 if self.side else 0) + 1
                     + len(self.legend) + 1 + (2 + len(self.index_rows) + 1 if self.index_rows and not self.side else 0)
                     + len(self.secrets) + (1 if self.secrets else 0))


def compose_page(layout):
    """The page as one canvas: title, motto, subtitle, map, legend, building index and secrets."""
    page = Canvas(layout.cols, layout.rows)
    t, s = layout.title, layout.subtitle
    # title, motto (the Pisa easter egg) and subtitle, centred
    if t:
        page.write((layout.cols - len(t)) // 2, 1, t, "b")
    if layout.motto:
        page.write((layout.cols - len(layout.motto)) // 2, layout.top - 3, layout.motto)
    page.write((layout.cols - len(s)) // 2, layout.top - 2, s)
    # the map, then the legend under it
    page.paste(layout.panel, layout.panel_x, layout.top)
    y = layout.top + max(layout.panel.height, len(layout.index_rows) + 2 if layout.side else 0) + 1
    for line in layout.legend:
        x = (layout.cols - legend_width(line)) // 2
        for n, entry in enumerate(line):
            if n:
                x += 4
            for text, style, *colour in entry:
                page.write(x, y, text, style, *colour)
                x += len(text)
        y += 1
    # the building index: beside the map at its top, or under the legend; names too long are cut with a full stop
    if layout.index_rows:
        width, digits = layout.index_width, layout.index_digits
        block = layout.index_cols * (width + INDEX_GAP) - INDEX_GAP
        if layout.side:
            x0, y0 = layout.panel_x + layout.panel.width + 2 * INDEX_GAP, layout.top
        else:
            x0, y0 = (layout.cols - block) // 2, y + 1
        head = tr("lg_buildings")
        page.write(x0 + (block - len(head)) // 2 if not layout.side else x0, y0, head, "b")
        for r, row in enumerate(layout.index_rows):
            for k, (n, title) in enumerate(row):
                x = x0 + k * (width + INDEX_GAP)
                room = width - digits - 1
                text = title if len(title) <= room else title[:room - 1].rstrip() + "."
                page.write(x, y0 + 2 + r, f"{n:>{digits}}", "b", "number")
                page.write(x + digits + 1, y0 + 2 + r, text)
        if not layout.side:
            y = y0 + 2 + len(layout.index_rows) + 1
    # the referee's secrets last
    for line in layout.secrets:
        x = (layout.cols - legend_width(line)) // 2
        for n, entry in enumerate(line):
            if n:
                x += 4
            for text, style, *colour in entry:
                page.write(x, y, text, style, *colour)
                x += len(text)
        y += 1
    return page


# --- paper ---
def paper_pixels(paper, orientation):
    """The size in pixels of a paper in an orientation, at DPI."""
    w_mm, h_mm = PAPERS[paper]
    if orientation == "landscape":
        w_mm, h_mm = h_mm, w_mm
    return round(mm(w_mm)), round(mm(h_mm))


VALID_SIZES = {paper_pixels(p, o) for p in PAPERS for o in ("portrait", "landscape")}


def fit(layout, paper, aspect):
    """Best orientation for the layout on a paper: (char_mm, fill, orientation)."""
    short, long_ = PAPERS[paper]
    max_char = MAX_CHAR_MM * short / PAPERS["A4"][0]
    best = None
    for name, (w_mm, h_mm) in (("portrait", (short, long_)), ("landscape", (long_, short))):
        page_w, page_h = w_mm - 2 * MARGIN_MM, h_mm - 2 * MARGIN_MM
        char_mm = min(page_w / layout.cols, page_h / (layout.rows * aspect), max_char)
        filled = (layout.cols * char_mm) * (layout.rows * char_mm * aspect) / (page_w * page_h)
        option = (char_mm, filled, name)
        if best is None or char_mm > best[0] * 1.08 or (char_mm >= best[0] * 0.92 and filled > best[1]):
            best = option
    return best


def best_fit(layouts, paper, aspect):
    """The layout that gives the biggest letters on a paper (the first one if
    they tie): (char_mm, fill, orientation, layout)."""
    return max((fit(layout, paper, aspect) + (layout,) for layout in layouts), key=lambda option: option[0])


def suggest_paper(layouts, aspect):
    """The smallest paper on which the map is readable (else the largest), and the best fit on every paper."""
    options = {paper: best_fit(layouts, paper, aspect) for paper in PAPERS}
    readable = [p for p in PAPERS if options[p][0] >= GOOD_CHAR_MM]
    return (readable[0] if readable else list(PAPERS)[-1]), options


def verdict(char_mm):
    """Readable, small or too small, for a letter size in mm."""
    return tr("v_too_small") if char_mm < SMALL_CHAR_MM else tr("v_small") if char_mm < GOOD_CHAR_MM else tr("v_good")


def ask_paper(layouts, aspect, wanted, ask_user, log):
    """The paper, the letter size, the orientation and the layout: of the
    `layouts` (the building index under or beside the map), on every paper
    the one with the biggest letters."""
    suggested, options = suggest_paper(layouts, aspect)
    panel = layouts[0].panel
    log.info(tr("info_paper_intro", nc=panel.width, nr=panel.height))
    for paper, (char_mm, _, orientation, _) in options.items():
        note = tr("suggested") if paper == suggested else ""
        log.info(tr("info_paper_option", paper=paper, o=tr("orientation_" + orientation), mm=char_mm,
                    v=verdict(char_mm), note=note))
    default = wanted or suggested
    if ask_user and menus_on():
        papers = list(options)
        labels = [f"{paper}  {tr('orientation_' + options[paper][2]):<11} {tr('menu_letters', mm=options[paper][0])}  "
                  f"{verdict(options[paper][0])}" + (tr("suggested") if paper == suggested else "") for paper in papers]
        default = papers[menu(tr("paper_q"), labels, papers.index(default))]
    elif ask_user:
        print()
        print(tr("paper_choice"))
        while True:
            answer = input(tr("q_paper", default=default)).strip().upper()
            if not answer:
                break
            if answer in PAPERS:
                default = answer
                break
            print(tr("paper_retry"))
    char_mm, _, orientation, layout = options[default]
    return default, char_mm, orientation, layout


# --- rendering and saving ---
def pixel_layout(layout, paper, orientation, char_mm, fonts, dpi=DPI):
    """Fonts and pixel geometry for drawing a layout on a paper: font size, letter size, sheet size and the offset
    that centres the page."""
    font_spec, bold_spec, advance_em, _ = fonts
    w_mm, h_mm = PAPERS[paper]
    if orientation == "landscape":
        w_mm, h_mm = h_mm, w_mm
    width, height = round(w_mm / 25.4 * dpi), round(h_mm / 25.4 * dpi)
    margin = MARGIN_MM / 25.4 * dpi
    area_w, area_h = width - 2 * margin, height - 2 * margin
    size = max(6, int(char_mm / 25.4 * dpi / advance_em))
    while True:
        regular = open_font(font_spec, size)
        char_w = regular.getlength("M")
        ascent, descent = regular.getmetrics()
        char_h = ascent + descent
        if (layout.cols * char_w <= area_w and layout.rows * char_h <= area_h) or size <= 6:
            break
        size -= 1
    bold = open_font(bold_spec, size) if bold_spec else None
    ox, oy = (width - layout.cols * char_w) / 2, (height - layout.rows * char_h) / 2
    return regular, bold, char_w, char_h, size, width, height, ox, oy


def render(canvas, regular, bold, char_w, char_h, size, width, height, ox, oy, progress=None, palette=MONO):
    """Rasterise. With MONO in grayscale, 0 = ink, 255 = paper (colorize gives
    the one-colour schemes); with a colour palette in RGB, every symbol in the
    colour of its tag, on the fill of its cell."""
    img = Image.new(palette["mode"], (width, height), palette["paper"])
    d = ImageDraw.Draw(img)
    ink_colour, paper = palette["ink"], palette["paper"]

    def ink(tag):
        """The colour of a tag in this palette, or the ink."""
        return palette.get(tag, ink_colour)
    if len(palette) > 3:            # the fills first, so no symbol is covered
        for y in range(canvas.height):
            for x in range(canvas.width):
                key = canvas.fills[y][x]
                if key in palette:
                    px, py = ox + x * char_w, oy + y * char_h
                    d.rectangle([px, py, px + char_w + 0.5, py + char_h + 0.5], fill=palette[key])
    # bold: the bold font where it has the glyph, else the regular one twice, shifted by `thicken` pixels
    thicken = max(1, size // 22)
    real_bold = bold is not None
    probe = bold.font_variant(size=40) if real_bold else None
    bold_can_draw = {}

    def draw_bold(px, py, ch, fill):
        """Draw a bold letter: with the bold font if it has the glyph, else the regular font twice, a little apart."""
        if real_bold:
            if ch not in bold_can_draw:
                bold_can_draw[ch] = ch.isascii() or font_has_glyph(probe, ch)
            if bold_can_draw[ch]:
                d.text((px, py), ch, font=bold, fill=fill, anchor="la")
                return
        d.text((px, py), ch, font=regular, fill=fill, anchor="la")
        d.text((px + thicken, py), ch, font=regular, fill=fill, anchor="la")

    for y in range(canvas.height):
        py = oy + y * char_h
        for x in range(canvas.width):
            ch, style, tag = canvas.chars[y][x], canvas.styles[y][x], canvas.tags[y][x]
            # every letter in its tag's colour: inverse ones (i) on a block of ink, bold ones (b) thickened
            if ch == " " and style != "i":
                continue
            px = ox + x * char_w
            if style == "i":
                d.rectangle([px, py, px + char_w + 0.5, py + char_h + 0.5], fill=ink(tag))
                if ch not in "[] ":
                    d.text((px, py), ch, font=bold or regular, fill=paper, anchor="la")
            elif style == "b":
                draw_bold(px, py, ch, ink(tag))
            else:
                d.text((px, py), ch, font=regular, fill=ink(tag), anchor="la")
        if progress:
            progress((y + 1) / canvas.height)
    return img


def colorize(img, scheme):
    """Give a grayscale map the colours of a one-colour scheme (2 and 3) through a palette; scheme 1 and the full-
    colour maps stay as they are."""
    if scheme == 1 or scheme in PALETTES:
        return img
    ink, paper = COLOR_SCHEMES[scheme]
    palette = []
    for v in range(256):
        t = v / 255
        palette += [round(ink[k] * (1 - t) + paper[k] * t) for k in range(3)]
    img.putpalette(palette)
    return img


def check_size(img, path):
    """Make sure a sheet is exactly A4, A3, A2 or A1 at 600 dpi."""
    if img.size not in VALID_SIZES:
        raise ValueError(tr("err_size", path=path, size=img.size))


def save_png(img, path, settings=None):
    """Save a sheet as PNG at 600 dpi, with the settings in a text chunk."""
    check_size(img, path)
    info = PngInfo()
    if settings:
        info.add_itxt(SETTINGS_KEY, json.dumps(settings, ensure_ascii=False))
    img.save(path, dpi=(DPI, DPI), pnginfo=info)


def pdf_text(text):
    """A text as a PDF hex string in UTF-16, for the document's information."""
    return "<" + ("﻿" + text).encode("utf-16-be").hex().upper() + ">"


class PdfFile:
    """A minimal PDF, one 600 dpi picture per page, Flate-compressed so it stays
    lossless (as in WyrmDelve)."""

    def __init__(self, path, settings=None):
        """Start writing a PDF file at `path`."""
        self.path, self.settings = path, settings
        self.f = open(path, "wb")
        self.f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        self.offsets = {}
        self.next_id = 3
        self.pages = []

    def new_id(self):
        """The number of a new PDF object."""
        self.next_id += 1
        return self.next_id - 1

    def begin(self, oid):
        """Start a PDF object, noting where it begins for the cross-reference table."""
        self.offsets[oid] = self.f.tell()
        self.f.write(f"{oid} 0 obj\n".encode())

    def obj(self, oid, body):
        """Write a whole PDF object."""
        self.begin(oid)
        self.f.write(body.encode("latin-1") + b"\nendobj\n")

    def add_page(self, img):
        """Add a sheet as a page: the picture, compressed in strips to spare memory, at its real size in points."""
        check_size(img, self.path)
        w, h = img.size
        if img.mode == "P":
            palette = bytes(img.getpalette()[:768]).ljust(768, b"\0")
            space = f"[/Indexed /DeviceRGB 255 <{palette.hex().upper()}>]"
        elif img.mode == "RGB":
            space = "/DeviceRGB"
        else:
            img = img.convert("L")
            space = "/DeviceGray"
        image_id, length_id = self.new_id(), self.new_id()
        self.begin(image_id)
        self.f.write((f"<< /Type /XObject /Subtype /Image /Width {w} /Height {h} /ColorSpace {space} "
                      f"/BitsPerComponent 8 /Filter /FlateDecode /Length {length_id} 0 R >>\nstream\n").encode())
        start, packer = self.f.tell(), zlib.compressobj(6)
        for y in range(0, h, 256):
            self.f.write(packer.compress(img.crop((0, y, w, min(h, y + 256))).tobytes()))
        self.f.write(packer.flush())
        length = self.f.tell() - start
        self.f.write(b"\nendstream\nendobj\n")
        self.obj(length_id, str(length))
        pw, ph = w / DPI * 72, h / DPI * 72
        draw = f"q {pw:.3f} 0 0 {ph:.3f} 0 0 cm /Im0 Do Q"
        content_id, page_id = self.new_id(), self.new_id()
        self.obj(content_id, f"<< /Length {len(draw)} >>\nstream\n{draw}\nendstream")
        self.obj(page_id, f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 {pw:.3f} {ph:.3f}] "
                          f"/Resources << /XObject << /Im0 {image_id} 0 R >> >> /Contents {content_id} 0 R >>")
        self.pages.append(page_id)

    def close(self):
        """Finish the PDF: page tree, catalogue, information, cross-reference table and trailer."""
        kids = " ".join(f"{p} 0 R" for p in self.pages)
        self.obj(2, f"<< /Type /Pages /Kids [{kids}] /Count {len(self.pages)} >>")
        self.obj(1, "<< /Type /Catalog /Pages 2 0 R >>")
        info_id = self.new_id()
        info = f"/Creator {pdf_text(PROGRAM + ' v' + VERSION)}"
        if self.settings:
            info += f" /Subject {pdf_text(json.dumps(self.settings, ensure_ascii=False))}"
        self.obj(info_id, f"<< {info} >>")
        xref = self.f.tell()
        self.f.write(f"xref\n0 {self.next_id}\n0000000000 65535 f \n".encode())
        for oid in range(1, self.next_id):
            self.f.write(f"{self.offsets[oid]:010d} 00000 n \n".encode())
        self.f.write(f"trailer\n<< /Size {self.next_id} /Root 1 0 R /Info {info_id} 0 R >>\n"
                     f"startxref\n{xref}\n%%EOF\n".encode())
        self.f.close()


def draw_sheet(canvas, pixels, scheme):
    """Draw a page canvas on a sheet in a colour scheme, with a live progress bar."""
    live = LiveBar()
    drawing = tr("pb_drawing")
    img = render(canvas, *pixels, progress=lambda done: live.update(0.85 * done, drawing),
                 palette=PALETTES.get(scheme, MONO))
    live.update(0.85, tr("pb_saving"))
    return colorize(img, scheme), live


def plain_text(text):
    """Only characters every monospaced font has at the same width."""
    return "".join(c if c.isascii() or c in "·" or ("À" <= c <= "ɏ") else "?" for c in text)


def write_text(path, canvas):
    """Save a page canvas as a .txt map, keyboard characters only."""
    with open(path, "w", encoding="utf-8") as f:
        f.write(plain_text("\n".join(canvas.lines())) + "\n")



# --- the key ---
def kind_label(b):
    """What a building is and what it is made of: inn, stone."""
    name = pick(b.kind["name"])
    material = (tr("grown") if getattr(b, "grown", None) else tr("carved") if getattr(b, "carved", None) else
                tr("stone") if b.stone else tr("wood"))
    return f"{name}, {material}"


def building_lines(s, b, people_on, monsters_on, treasure_on):
    """The lines of the key under a building: description, people, services, monsters, clues and treasure (as
    asked)."""
    lines = []
    ruin = hasattr(s, "layers")         # nobody lives in a ruin: what is left, and the traces of the past
    if ruin:
        if b.text:
            lines.append(capitalized(pick(b.text)) + ".")
        if b.kind.get("secret"):
            lines.append(tr("secret_use", x=pick(b.kind["secret"])))
        if b.uid in s.traces:
            lines.append(tr("trace", t=pick(s.traces[b.uid])))
    elif b.kind.get("filler") and getattr(b, "dwellings", 1) > 1 and b.people > 9:
        trades = pick(join_pairs(b.trades[:3]))
        lines.append(tr("block_line", p=number(b.people), d=b.dwellings, t=trades))
        if people_on and b.npc:
            lines.append(tr("block_head") + npc_line(b.npc, full=True))
    else:
        if b.text:
            lines.append(capitalized(pick(b.text)) + ".")
        if b.kind.get("secret"):
            lines.append(tr("secret_use", x=pick(b.kind["secret"])))
        if people_on and b.npc:
            household = tr("household", n=b.people) if b.people > 1 else ""
            lines.append(npc_line(b.npc, full=True) + household)
        elif b.npc:
            lines.append(npc_line(b.npc, full=False))
    if getattr(b, "grown_text", None) and not ruin:     # a house grown in a giant mushroom
        lines.append(capitalized(pick(b.grown_text)) + ".")
    if getattr(b, "named", None):     # a name from the past or from the place
        text, values = b.named
        lines.append(pick(fmt(text, **values)))
    if s.ruler_seat is b and not ruin:
        lines.append(tr("seat_of", r=pick(s.ruler["role"])))
    if b.kind.get("services") and s.p["purpose"] == "rest":
        lines.append(tr("services") + "; ".join(pick(x) for x in b.kind["services"]) + ".")
    if s.plan.tunnel_from is b:
        lines.append(tr("tunnel_here"))
    if s.p["purpose"] == "adventure":
        if b.uid in s.abandoned and b.uid not in s.occupants:
            lines.append(tr("ruined") if b.ruined else tr("abandoned"))
        if monsters_on:
            lines += s.contents.get(b.uid, [])
        if treasure_on and b.uid in getattr(s, "treasure", {}):
            lines.append(treasure_line(s.treasure[b.uid]))
    return lines


def adventure_words(p, s=None):
    """The purpose in words: a place of rest, or of adventure with its danger and state (in ruins, inhabited and
    threatened); with the settlement `s`, the state of its threat (older seeds have none of their own)."""
    if p["purpose"] == "rest":
        return tr("purpose_rest")
    state = p.get("state")
    if s is not None and getattr(s, "situation", None):
        state = "ruin" if s.situation["life"] == "ruin" else "threat"
    return tr("purpose_adventure", d=p["danger"]) + (", " + tr("state_" + state) if state else "")


def key_blocks(s, title, units, content):
    """The whole key as a list of blocks (title, meta, h, p, item, table, quarter, building...), which write_key and
    write_pdf both turn into text."""
    story_on, people_on, monsters_on, treasure_on, intrigue_on = content
    p, plan = s.p, s.plan
    # title, then the meta lines: seed, type, era, terrain, purpose, population, names and scale
    blocks = [("title", title)]
    ruin = hasattr(s, "layers")
    purpose = adventure_words(p, s)
    blocks += [("meta", f"{tr('key_seed')}: {s.seed}"),
               ("meta", f"{capitalized(type_name(p['type']))} · {capitalized(pick(ERA[p['era']]['name']))} · "
                        f"{capitalized(pick(TERRAIN[p['terrain']]['name']))}"),
               ("meta", f"{purpose} · {tr('key_pop_ruin' if ruin else 'key_pop', n=number(p['pop']))}")]
    if getattr(s, "folk", None):
        blocks.append(("meta", tr("key_folk", f=pick(s.folk["about"]))))
    if p.get("names"):
        blocks.append(("meta", tr("key_names", s=pick(NAME_STYLE[p["names"]]["name"]),
                                  t=pick(NAME_TONE[p["tone"]]["name"]))))
        if (p.get("people") or "places") != "places":
            blocks.append(("meta", tr("key_people", w=people_words(p))))
    n, length, unit, row = scale_bar(plan, units)
    blocks.append(("meta", tr("key_scale", r=f"{row:.1f}".replace(".", "," if LANG == "it" else "."), u=unit)))
    if story_on and ruin:           # a ruin's history in layers, from its founding to the stories after its fall
        blocks.append(("h", tr("h_history")))
        blocks += [("item", f"{pick(label)}. {capitalized(pick(text))}") for label, text in s.layers]
        blocks.append(("p", tr("gods_ruin", g=pick(gods_text(p)))))
    elif story_on:
        # history in layers, from the founding (and the present day, in a place of rest)
        blocks.append(("h", tr("h_history")))
        blocks += [("item", f"{pick(st['label'])}. {capitalized(pick(st['text']))}") for st in s.strata]
        if p["purpose"] == "rest":
            blocks.append(("p", pick(s.present)))
        blocks.append(("p", tr("gods", g=pick(gods_text(p)))))
    # an adventure: the threat, its villain, its clock and the wandering monsters
    if p["purpose"] == "adventure":
        sit = s.situation
        blocks += [("h", tr("h_threat", t=pick(sit["name"]))), ("p", pick(s.threat))]
        if s.boss:
            blocks.append(("p", tr("threat_boss", b=pick(s.boss))))
        else:
            blocks.append(("p", tr("threat_villain", v=npc_line(s.villain, full=True))))
        blocks.append(("table", tr("clock_title"), [(k + 1, capitalized(pick(c)) + ".") for k, c in enumerate(s.clock)]))
        if monsters_on:
            blocks.append(("table", tr("key_wander"), [(k + 1, f"{name}: {text}.") for k, (name, text) in enumerate(s.wander)]))
    # government, factions, demography and economy: none left in a ruin
    if not ruin:
        blocks.append(("h", tr("h_government")))
        seat = f" ({tr('lives_in', n=s.ruler_seat.number)})" if s.ruler_seat else ""
        blocks.append(("p", capitalized(npc_line(s.ruler, full=people_on)) + seat))
        if story_on and not intrigue_on:     # with the intrigue, the factions have a section of their own
            for f in s.factions:
                rival = tr("faction_rival", r=pick(f["rival"][0]["name"])) if f.get("rival") else ""
                blocks.append(("item", tr("faction", n=capitalized(pick(f["name"])), g=pick(f["goal"]),
                                          l=npc_line(f["leader"], full=False)) + rival))
        blocks += demography_blocks(s)
        if story_on:
            blocks += economy_blocks(s)
    if intrigue_on:
        blocks += intrigue_blocks(s)
    if p["purpose"] == "rest":
        # a place of rest: services, mercenaries, hirelings and hooks
        blocks.append(("h", tr("h_services")))
        for b in plan.buildings:
            if b.kind.get("services") or b.kind.get("rest"):
                blocks.append(("item", f"{b.number}  {pick(b.title)}: " + "; ".join(pick(x) for x in b.kind.get("services", []))))
        blocks.append(("table", tr("mercenaries"), [("·", tr("merc_row", n=n_, name=pick(name), w=wage, s=pick(st)))
                                                   for name, n_, wage, st in s.mercenaries]))
        if people_on:
            blocks.append(("table", tr("hirelings"), [("·", npc_line(h, full=True) + tr("hireling_pay"))
                                                     for h in s.hirelings]))
        if story_on:
            blocks.append(("table", tr("hooks"), [(k + 1, h) for k, h in enumerate(s.hooks)]))
    if story_on:
        # rumours and events
        blocks.append(("h", tr("h_lore")))
        blocks.append(("table", tr("rumours"), [(k + 1, f"{capitalized(pick(text))} "
                                                        f"[{tr('partial', x=pick(twist)) if twist else tr(truth)}]")
                                                for k, (text, truth, twist) in enumerate(s.rumours)]))
        blocks.append(("table", tr("events_ruin" if ruin else "events"), [(k + 1, e) for k, e in enumerate(s.events)]))
        if ruin:
            blocks.append(("table", tr("hooks_ruin"), [(k + 1, h) for k, h in enumerate(s.hooks)]))
    # the walls, then every building, under the name of its quarter
    blocks += walls_blocks(s)
    blocks.append(("h", tr("h_buildings")))
    current = None
    for b in plan.buildings:
        q = b.quarter
        if q != current:
            current = q
            if b.outside:
                blocks.append(("quarter", tr("outside_walls") if plan.walled else tr("outskirts")))
            elif s.quarter_names and q < len(s.quarter_names):
                blocks.append(("quarter", capitalized(pick(s.quarter_names[q]))))
        blocks.append(("building", str(b.number), f"{pick(b.title)} ({kind_label(b)})",
                       building_lines(s, b, people_on, monsters_on, treasure_on)))
    return blocks


def intrigue_blocks(s):
    """The key's main NPCs (story, motive, secret, ties, a job for the characters) and factions (who they are,
    what they want and why, how, where, who leads them, against and with whom)."""
    ruin = hasattr(s, "layers")
    out = [("h", tr("h_notables_ruin" if ruin else "h_notables"))]
    for nb in s.notables:
        npc = nb["npc"]
        lines = [f"{pick(npc['stats'])}. {capitalized(pick(npc['trait']))}.",
                 tr("nb_story", x=" ".join(sentence(pick(x)) for x in nb["story"])),
                 tr("nb_want", x=pick(npc["want"])), tr("nb_secret", x=pick(npc["secret"]))]
        if nb["faction"]:
            lines.append(tr("nb_leads", f=pick(nb["faction"]["name"])))
        if nb["bonds"]:
            lines.append(tr("nb_bonds", x="; ".join(pick(x) for x in nb["bonds"])))
        if nb["hook"]:
            lines.append(tr("nb_hook", x=pick(nb["hook"])))
        label = str(nb["home"].number) if nb["home"] is not None else "·"
        out.append(("building", label, f"{pick(npc['name'])}, {pick(npc['role'])}", lines))
    if not s.factions:
        return out
    out.append(("h", tr("h_factions_ruin" if ruin else "h_factions")))
    for f in s.factions:
        st, leader = f["stratum"], f["leader"]
        home = next((nb["home"] for nb in s.notables if nb["npc"] is leader), None)
        lines = [tr("fa_about", x=pick(f["about"]), p=pick(f["power"])), tr("fa_goal", x=pick(f["goal"])),
                 pick(fmt(tr_pair("fa_root"), s=st["short"], w=st["values"]["when"])),
                 tr("fa_how", x=pick(f["method"]), y=pick(f["asset"]))]
        if f["hq"] is not None:
            lines.append(tr("fa_camp" if f["camp"] else "fa_hq", x=pick(building_ref(f["hq"]))))
        lines.append(tr("fa_leader", x=f"{pick(ref(leader, home))}, {pick(leader['role'])}"))
        if f.get("rival"):
            lines.append(tr("fa_rival", x=pick(f["rival"][0]["name"]), r=pick(f["rival"][1])))
        if f.get("ally"):
            lines.append(tr("fa_ally", x=pick(f["ally"][0]["name"]), r=pick(f["ally"][1])))
        out.append(("building", "·", capitalized(pick(f["name"])), lines))
    return out


def demography_blocks(s):
    """The key's demography: people, density, dwellings, trades, clergy, guards..."""
    d, p = s.demography, s.p
    out = [("h", tr("h_demography"))]
    if p["type"] in ("castle", "fortress"):
        out.append(("p", tr("demo_ward", g=number(d["garrison"]), s=number(d["servants"]), h=number(d["horses"]),
                            l=number(d["livestock"]))))
        return out
    out.append(("p", tr("demo_main", p=number(p["pop"]), a=f"{d['hectares']:.1f}".replace(".", "," if LANG == "it" else "."),
                        d=number(d["density"]), w=number(d["dwellings"]), b=len(s.plan.buildings))))
    out.append(("p", tr("demo_people", n=number(round(d["nobles"])), l=number(round(d["lawyers"])),
                        c=number(round(d["clergy"])), pr=number(max(1, round(d["priests"]))),
                        w=number(max(1, round(d["worship"]))), g=number(max(1, round(d["guards"]))),
                        slack=tr("slack") if d["slack"] else "", li=number(round(d["livestock"])))))
    sure = [(pick(name), n) for name, n in d["shops"] if n >= 1]
    maybe = [(pick(name), n) for name, n in d["shops"] if 0.1 <= n < 1]
    if sure:
        out.append(("p", tr("demo_shops") + ", ".join(f"{name} {int(n)}" for name, n in sure) + "."))
    if maybe:
        out.append(("p", tr("demo_maybe") + ", ".join(f"{name} ({round(n * 100)}%)" for name, n in maybe) + "."))
    placed = sum(1 for b in s.plan.buildings if not b.kind.get("filler"))
    out.append(("note", tr("demo_note", n=placed)))
    return out


def economy_blocks(s):
    """The key's economy: the country around, its revenue, and properties for sale."""
    e = s.economy
    out = [("h", tr("h_economy"))]
    div = troubled(s)
    rev = e["revenue"] / div
    out.append(("p", tr("eco_region", r=pick(e["region"]["name"]), n=number(e["rural"]), v=e["villages"])))
    out.append(("p", tr("eco_revenue", m=number(round(rev)), y=number(round(rev * 12)),
                        t=tr("eco_troubled", d=div) if div > 1 else "")))
    rows = []
    for o in e["offers"]:
        off = o["offer"]
        cost = tr("eco_cost", c=number(off["cost"])) if off["cost"] else ""
        extra = f" {pick(off['extra'])}." if off.get("extra") else ""
        people = f" {tr('eco_people', n=o['people'], w=pick(off['people_what']))}" if o["people"] and off.get("people_what") else ""
        rows.append(("·", f"{capitalized(pick(off['name']))}{cost}: {pick(off['income'])}.{extra}{people} "
                          f"{tr('eco_seller', s=npc_line(o['seller'], full=False).split(',')[0])}"))
    out.append(("table", tr("eco_offers"), rows))
    out.append(("note", tr("eco_rules", c=round(ECONOMY["tax_cheat"] * 100))))
    return out


def walls_blocks(s):
    """The key's walls and gates: the kind of walls, every gate and the secret ways."""
    plan = s.plan
    out = [("h", tr("h_walls"))]
    if plan.walled:
        out.append(("p", tr("walls_" + (plan.wall_kind or "stone")) + (tr("moat_" + plan.moat) if plan.moat else "")))
    else:
        out.append(("p", tr("walls_none")))
    if plan.height:
        out.append(("p", tr("perched", d=pick(compass(plan.approach)))))
    for g in s.gates:
        out.append(("item", f"[{g['letter']}] {pick(g['name'])} ({pick(g['dir'])})"))
    if plan.secret:
        out.append(("item", tr("postern", n=len(plan.secret))))
    if plan.tunnel and plan.tunnel_from:
        out.append(("item", tr("tunnel", n=plan.tunnel_from.number, t=pick(plan.tunnel_from.title))))
    if plan.harbour:
        out.append(("item", tr("harbour")))
    return out


def wrap(text, width, indent=""):
    """Break a text into lines no wider than `width`, each starting with `indent`."""
    words, lines, line = text.split(), [], indent
    for w in words:
        if len(line) + len(w) + 1 > width and line.strip():
            lines.append(line.rstrip())
            line = indent
        line += w + " "
    if line.strip():
        lines.append(line.rstrip())
    return lines


def write_key(blocks, path):
    """Save the key blocks as plain text, 100 letters wide."""
    width = 100
    lines = []
    for block in blocks:
        kind = block[0]
        if kind == "title":
            lines.append(f"{PROGRAM} v{VERSION}" + (f" — {block[1]}" if block[1] else ""))
        elif kind == "meta":
            lines.append(block[1])
        elif kind == "h":
            lines += ["", block[1].upper()]
        elif kind == "quarter":
            lines += ["", "  " + block[1].upper()]
        elif kind in ("p", "note"):
            lines += wrap(block[1], width, "  ")
        elif kind == "item":
            rows = wrap(block[1], width - 4, "    ")
            lines += ["  · " + rows[0].strip()] + rows[1:]
        elif kind == "table":
            lines.append("  " + block[1])
            for n, text in block[2]:
                rows = wrap(f"{text}", width - 8, "        ")
                lines += [f"    {str(n) + '.' if n != '·' else '·':<3} " + rows[0].strip()] + rows[1:]
        elif kind == "building":
            _, label, head, extra = block
            lines += wrap(f"{label:>4}  {head}", width, "      ")
            for line in extra:
                lines += wrap(line, width, "        ")
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


# --- the PDF file ---
PDF_FONTS = ("Sebaldus-Gotisch.ttf", "CrimsonText-Regular.ttf", "CrimsonText-Italic.ttf", "CrimsonText-Bold.ttf",
              "CrimsonText-BoldItalic.ttf", "DejaVuSans.ttf")


def pdf_problem():
    """Why the PDF file cannot be made (missing fonts, missing or old fpdf2), or None."""
    missing = [name for name in PDF_FONTS if not os.path.isfile(font_file(name))]
    if missing:
        return tr("err_pdf_fonts", f=", ".join(missing), d=short_path(FONT_DIR))
    try:
        import fpdf
    except ImportError:
        return tr("err_no_fpdf")
    version = getattr(fpdf, "__version__", None) or getattr(fpdf, "FPDF_VERSION", "")
    try:
        numbers = tuple(int(x) for x in version.split(".")[:3])
    except ValueError:
        numbers = (0,)
    if numbers < (2, 7, 6) or not hasattr(fpdf.FPDF, "set_fallback_fonts"):
        return tr("err_old_fpdf", v=version or "?")
    return None


def write_pdf(blocks, path, settings, maps=()):
    """The key as an A4 PDF file, like WyrmDelve's: Sebaldus-Gotisch headings,
    Crimson Text body. `maps`: (title, PIL image, paper, orientation) pages
    to put at the front (the single-PDF option)."""
    from fpdf import FPDF

    class Page(FPDF):
        """fpdf2's page with WyrmUrbiGen's footer."""
        def footer(self):
            """The footer: program, version and page number (not on the map pages)."""
            if getattr(self, "no_footer", False):
                return
            self.set_y(-14)
            self.set_font("crimson", "I", 9)
            self.set_text_color(90)
            self.cell(0, 6, f"{PROGRAM} v{VERSION} · {self.page_no()}", align="C")
            self.set_text_color(0)

    pdf = Page(format="A4", unit="mm")
    pdf.set_margins(22, 20, 22)
    pdf.set_auto_page_break(True, 20)
    # the fonts; DejaVu fills in the glyphs the other two lack
    pdf.add_font("gothic", "", font_file("Sebaldus-Gotisch.ttf"))
    for style, name in (("", "Regular"), ("I", "Italic"), ("B", "Bold"), ("BI", "BoldItalic")):
        pdf.add_font("crimson", style, font_file(f"CrimsonText-{name}.ttf"))
    pdf.add_font("dejavu", "", font_file("DejaVuSans.ttf"))
    pdf.set_fallback_fonts(["dejavu"], exact_match=False)
    pdf.set_creator(f"{PROGRAM} v{VERSION}")
    pdf.set_subject(json.dumps(settings, ensure_ascii=False))
    # the map pages first, each on its own paper and with no footer; then the key on A4
    for _, img, paper, orientation in maps:
        w_mm, h_mm = PAPERS[paper]
        if orientation == "landscape":
            w_mm, h_mm = h_mm, w_mm
        pdf.no_footer = True
        pdf.add_page(format=(w_mm, h_mm) if orientation == "portrait" else (h_mm, w_mm),
                     orientation="P" if orientation == "portrait" else "L")
        pdf.image(img, x=0, y=0, w=w_mm, h=h_mm)
    pdf.no_footer = False
    pdf.add_page(format="A4", orientation="P")
    width = pdf.w - pdf.l_margin - pdf.r_margin

    def rule():
        """A short centred line under the title block."""
        y = pdf.get_y() + 1
        pdf.set_draw_color(120)
        pdf.line(pdf.l_margin + width * 0.3, y, pdf.l_margin + width * 0.7, y)
        pdf.set_draw_color(0)
        pdf.ln(4)

    # every block in its own font and size; a short rule before the first heading
    first_h = True
    for block in blocks:
        kind = block[0]
        if kind == "title":
            pdf.set_title(block[1] or PROGRAM)
            pdf.set_font("gothic", "", 30)
            pdf.multi_cell(0, 13, block[1] or PROGRAM, align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif kind == "motto":
            pdf.set_font("crimson", "I", 15)
            pdf.multi_cell(0, 7, block[1], align="C", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif kind == "meta":
            pdf.set_font("crimson", "I", 11)
            pdf.multi_cell(0, 5.5, block[1], align="C", new_x="LMARGIN", new_y="NEXT")
        elif kind == "h":
            if first_h:
                pdf.ln(2)
                rule()
                first_h = False
            pdf.ln(3)
            pdf.set_font("gothic", "", 19)
            pdf.multi_cell(0, 9, block[1], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif kind == "quarter":
            pdf.ln(3)
            pdf.set_font("gothic", "", 15)
            pdf.multi_cell(0, 8, block[1], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif kind == "p":
            pdf.set_font("crimson", "", 12)
            pdf.multi_cell(0, 6, block[1], align="J", new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1.5)
        elif kind == "note":
            pdf.set_font("crimson", "I", 10.5)
            pdf.multi_cell(0, 5, block[1], new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1)
        elif kind == "item":
            pdf.set_font("crimson", "", 11.5)
            pdf.set_x(pdf.l_margin + 3)
            pdf.multi_cell(width - 3, 5.8, "· " + block[1], new_x="LMARGIN", new_y="NEXT")
        elif kind == "table":
            pdf.ln(1)
            pdf.set_font("crimson", "BI", 11.5)
            pdf.multi_cell(0, 6, block[1], new_x="LMARGIN", new_y="NEXT")
            pdf.set_font("crimson", "", 10.5)
            for n, text in block[2]:
                pdf.set_x(pdf.l_margin + 4)
                mark = f"**{n}.**" if n != "·" else "**·**"
                pdf.multi_cell(width - 4, 5.2, f"{mark} {md_escape(text)}", markdown=True, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(2)
        elif kind == "building":
            _, label, head, extra = block
            pdf.set_font("crimson", "", 11.5)
            pdf.multi_cell(0, 5.8, f"**{label}**  {md_escape(head)}", markdown=True, new_x="LMARGIN", new_y="NEXT")
            for line in extra:
                pdf.set_x(pdf.l_margin + 8)
                pdf.set_font("crimson", "", 10.5)
                pdf.multi_cell(width - 8, 5.2, line, new_x="LMARGIN", new_y="NEXT")
            pdf.ln(1.2)
    pdf.output(path)


def md_escape(text):
    """fpdf2's markdown reads ** and __ as bold and italics: keep them literal."""
    return text.replace("**", "* *").replace("__", "_ _")


# --- files and folders ---
OUTPUT_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), "settlements_generated")


def short_path(path):
    """A path relative to the current folder when it is inside it, for shorter messages."""
    try:
        rel = os.path.relpath(path)
    except ValueError:
        return path
    return rel if not rel.startswith("..") else path


# --- welcome screen and questions ---
TITLE_ART = r"""
__        __                     _   _      _     _  ____
\ \      / /   _ _ __ _ __ ___  | | | |_ __| |__ (_)/ ___| ___ _ __
 \ \ /\ / / | | | '__| '_ ` _ \ | | | | '__| '_ \| | |  _ / _ \ '_ \
  \ V  V /| |_| | |  | | | | | || |_| | |  | |_) | | |_| |  __/ | | |
   \_/\_/  \__, |_|  |_| |_| |_| \___/|_|  |_.__/|_|\____|\___|_| |_|
           |___/
"""

# a castle on its rock
CASTLE = r'''
                  ^
                 / \
            ^   _|.|_   ^
          _|I|  |I .|  |.|_
          \II||~~| |~~||  /
           ~\~|~~~~~~~|~/~
             \|II I ..|/
        /\    |II.    |    /\
       /  \  _|III .  |_  /  \
       |-~| /(|I.I I  |)\ |~-|
     _/(I | +-----------+ |. )\_
     \~-----/____-~-____\-----~/
      |I.III|  /(===)\  |  .. |
      /~~~-----_________---~~~\
     `##########!\-#####%!!!!!| |\
    _/###########!!\~~-_##%!!!\_/|
    \##############!!!!!/~~-_%!!!!\
     ~)#################!!!!!/~~--\_
  __ /#####################%%!!!!/ /
  \,~\-_____##############%%%!!!!\/
  /!!!!\ \ \~-_###########%%%!!!!\
 /#####!!!!!!!\~-_#######%%%!!!!!!\_
/#############!!!\#########%%%!!!!!!\
'''


def terminal_width():
    """The width of the terminal in letters, or None if there is none."""
    try:
        return os.get_terminal_size(sys.stdout.fileno()).columns
    except (OSError, ValueError):
        return None


def menus_on():
    """Menus need asciimatics and a real terminal: otherwise numbered questions."""
    return Screen is not None and sys.stdin.isatty() and sys.stdout.isatty()


# One screen for the whole interactive run, as in WyrmHex's editor: the
# first menu opens it and it stays open from question to question, and
# while the settlement is made, so the terminal never goes back to the
# console in between. The answers and the log are kept and printed to the
# console when it closes, at the end (or on Ctrl+C or an error).
SCREEN = {"open": None, "echo": [], "live": None}


def screen_on():
    """The questions' screen, opened if it isn't yet."""
    if SCREEN["open"] is None:
        SCREEN["open"] = Screen.open()
    return SCREEN["open"]


def screen_off():
    """Back to the console: close the questions' screen and print what was answered there."""
    if SCREEN["open"] is not None:
        SCREEN["open"].close()
        SCREEN["open"] = None
    for line in SCREEN["echo"]:
        print(line)
    SCREEN["echo"].clear()


def say(line):
    """A console line; kept for later while the questions' screen is open."""
    if SCREEN["open"] is not None:
        SCREEN["echo"].append(line)
    else:
        print(line)


def console(line):
    """A line of the run's log: printed, or kept and shown on the questions' screen while it's open."""
    say(line)
    if SCREEN["open"] is not None:
        draw_console()


def console_lines():
    """The console lines kept while the questions' screen is open, one per row, and the live bar."""
    lines = [row for line in SCREEN["echo"] for row in line.split("\n")]
    return lines + ([SCREEN["live"]] if SCREEN["live"] else [])


def draw_console():
    """The run's log on the questions' screen: its last lines, as the console would show them."""
    screen = SCREEN["open"]
    screen.clear_buffer(Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
    screen.print_at(f" {PROGRAM} v{VERSION} ", 2, 1, Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_YELLOW)
    room = max(1, screen.height - 4)
    for row, line in enumerate(console_lines()[-room:]):
        screen.print_at(line[:screen.width - 1], 0, 3 + row)
    screen.refresh()


def on_screen(run):
    """run(screen) on the questions' screen; a resized terminal opens it again and draws it all anew."""
    while True:
        try:
            return run(screen_on())
        except ResizeScreenError:
            SCREEN["open"].close()
            SCREEN["open"] = None


def read_value(answer, default, kind=int, lowest=None, highest=None):
    """A typed answer as (value, None), or (None, what's wrong with it). Empty = default."""
    answer = answer.strip()
    if not answer:
        return default, None
    try:
        value = kind(answer.replace(".", "").replace(",", "") if kind is int else answer)
    except ValueError:
        return None, tr("invalid_value")
    if (lowest is not None and value < lowest) or (highest is not None and value > highest):
        return None, tr("value_range", lo=lowest, hi=highest)
    return value, None


def ask(question, default, kind=int, lowest=None, highest=None):
    """Keep asking until the answer is valid. Enter = default. With menus, typed in a field on their screen."""
    if menus_on():
        return type_in(question, str(default), lambda text: read_value(text, default, kind, lowest, highest))
    while True:
        value, wrong = read_value(input(f"  {question} [{default}]: "), default, kind, lowest, highest)
        if wrong:
            print(wrong)
            continue
        return value


def type_in(question, text="", check=None, limit=60):
    """WyrmHex's text box, on the questions' screen: a line typed in a field, Enter confirms. `check` turns the text
    into the answer as (answer, None), or says what's wrong as (None, message), shown under the field."""
    question = question.strip().rstrip(":").strip()
    check = check or (lambda t: (t.strip(), None))
    state = {"text": text, "wrong": ""}

    def draw(screen):
        """Draw the field's screen: title, question, the field with its cursor, what's wrong, keys."""
        screen.clear_buffer(Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        screen.print_at(f" {PROGRAM} v{VERSION} ", 2, 1, Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_YELLOW)
        x, y, room = 2, 3, max(20, screen.width - 4)
        for line in textwrap.wrap(question, room):
            screen.print_at(line, x, y, Screen.COLOUR_YELLOW, Screen.A_BOLD)
            y += 1
        y += 1
        width = max(4, min(limit, screen.width - 2 * x - 4))
        shown = state["text"][-(width - 1):]
        screen.print_at(" " * (width + 2), x, y, Screen.COLOUR_BLACK, Screen.A_NORMAL, Screen.COLOUR_WHITE)
        screen.print_at(shown + "_", x + 1, y, Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_WHITE)
        y += 2
        for line in textwrap.wrap(state["wrong"].strip(), room):
            screen.print_at(line, x, y, Screen.COLOUR_RED, Screen.A_BOLD)
            y += 1
        keys = tr("type_keys")
        footer = [keys] if x + len(keys) < screen.width else keys.split("   ·   ")
        for row, line in enumerate(footer):
            screen.print_at(line[:screen.width - x - 1], x, screen.height - 1 - len(footer) + row, Screen.COLOUR_WHITE)
        screen.refresh()

    def run(screen):
        """The field's loop: letters are typed, Backspace deletes, Esc clears, Enter confirms."""
        while True:
            draw(screen)
            screen.wait_for_input(0.5)
            event = screen.get_event()
            if screen.has_resized():
                raise ResizeScreenError("resized")
            if not isinstance(event, KeyboardEvent):
                continue
            code = event.key_code
            if code in (10, 13):
                answer, state["wrong"] = check(state["text"])
                if not state["wrong"]:
                    return answer
            elif code in (Screen.KEY_BACK, Screen.KEY_DELETE, 8, 127):
                state["text"], state["wrong"] = state["text"][:-1], ""
            elif code == Screen.KEY_ESCAPE:
                state["text"], state["wrong"] = "", ""
            elif code == 3:                    # Ctrl+C, when the terminal hands it over as a key
                raise KeyboardInterrupt
            elif 32 <= code < 0x110000 and chr(code).isprintable() and len(state["text"]) < limit:
                state["text"], state["wrong"] = state["text"] + chr(code), ""

    answer = on_screen(run)
    say(f"  {question}: {state['text'].strip() or answer}")
    return answer


def menu(question, options, default=0, hints=None, ticks=None, header=None, keys=None, help_key="content_help",
         tail=False):
    """WyrmDelve's menu: arrows (or the mouse) move, Enter chooses, a number
    jumps to its option; with `ticks`, Space ticks several; `header`: lines
    above the question (its last ones if `tail`, when they don't all fit).
    Without a terminal or asciimatics: the numbered question of old."""
    question = question.strip()
    hints = hints or [""] * len(options)
    # no full-screen menu: the options numbered, the answer typed (several numbers separated by commas when ticking)
    if not menus_on():
        print("\n  " + question)
        for k, (text, hint) in enumerate(zip(options, hints), 1):
            print(f"    {k} = {text}" + (f": {hint}" if hint else ""))
        if ticks is None:
            return ask(tr("choice"), default + 1, int, 1, len(options)) - 1
        print(tr(help_key))
        while True:
            answer = input(f"  {tr('choice')} [{','.join(str(k + 1) for k, on in enumerate(ticks) if on) or '0'}]: ").strip()
            if not answer:
                return tuple(ticks)
            try:
                numbers_ = [int(w) for w in answer.replace(" ", ",").split(",") if w]
            except ValueError:
                print(tr("invalid_value"))
                continue
            if all(0 <= k <= len(options) for k in numbers_):
                return tuple(k + 1 in numbers_ for k in range(len(options)))
            print(tr("invalid_value"))

    # the full-screen menu: `at` is the highlighted option, `rows` maps screen rows to options (for the mouse)
    state = {"at": default, "ticks": list(ticks) if ticks is not None else None, "rows": {}}
    keys = keys or tr("menu_keys_multi" if ticks is not None else "menu_keys")

    def draw(screen):
        """Draw the menu screen: header or title, question, options with ticks and hints, keys."""
        screen.clear_buffer(Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        lines = header or []
        x = 2
        if not lines:
            screen.print_at(f" {PROGRAM} v{VERSION} ", 2, 1, Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_YELLOW)
            y = 3
        else:
            keep = max(0, min(len(lines), screen.height - len(options) - 7))
            for row, line in enumerate(lines[len(lines) - keep:] if tail else lines[:keep]):
                screen.print_at(line[:screen.width], 0, row)
            y = keep + 1
        screen.print_at(question, x, y, Screen.COLOUR_YELLOW, Screen.A_BOLD)
        y += 2
        room = max(3, screen.height - y - 5)
        first = min(max(0, state["at"] - room + 1), max(0, len(options) - room))
        state["rows"] = {}
        for k in range(first, min(len(options), first + room)):
            box = ("[x] " if state["ticks"][k] else "[ ] ") if ticks is not None else ""
            text = f" {k + 1:>2}  {box}{options[k]} "
            if k == state["at"]:
                screen.print_at("> " + text, x, y, Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_CYAN)
            else:
                screen.print_at("  " + text, x, y, Screen.COLOUR_WHITE)
            state["rows"][y] = k
            y += 1
        hint = hints[state["at"]]
        if hint:
            screen.print_at(hint[:screen.width - x - 4], x + 4, y + 1, Screen.COLOUR_CYAN)
        footer = [keys] if x + len(keys) < screen.width else keys.split("   ·   ")
        for row, line in enumerate(footer):
            screen.print_at(line[:screen.width - x - 1], x, screen.height - 1 - len(footer) + row, Screen.COLOUR_WHITE)
        screen.refresh()

    def run(screen):
        """The menu's loop: arrows and mouse move, Space ticks, Enter confirms."""
        while True:
            draw(screen)
            screen.wait_for_input(0.5)
            event = screen.get_event()
            if screen.has_resized():
                raise ResizeScreenError("resized")
            if isinstance(event, MouseEvent) and event.buttons and event.y in state["rows"]:
                k = state["rows"][event.y]
                if ticks is not None:
                    state["at"] = k
                    state["ticks"][k] = not state["ticks"][k]
                    continue
                return k
            if not isinstance(event, KeyboardEvent):
                continue
            code = event.key_code
            if code in (Screen.KEY_UP, ord("k")):
                state["at"] = (state["at"] - 1) % len(options)
            elif code in (Screen.KEY_DOWN, ord("j"), Screen.KEY_TAB):
                state["at"] = (state["at"] + 1) % len(options)
            elif ord("1") <= code <= ord("9") and code - ord("1") < len(options):
                state["at"] = code - ord("1")
                if ticks is not None:
                    state["ticks"][state["at"]] = not state["ticks"][state["at"]]
                elif len(options) < 10:
                    return state["at"]
            elif code == ord(" ") and ticks is not None:
                state["ticks"][state["at"]] = not state["ticks"][state["at"]]
            elif code in (10, 13):
                return tuple(state["ticks"]) if ticks is not None else state["at"]
            elif code == 3:                    # Ctrl+C, when the terminal hands it over as a key
                raise KeyboardInterrupt

    answer = on_screen(run)
    # echo the answer, so it stays on screen afterwards
    chosen = options[answer] if ticks is None else (", ".join(o for o, on in zip(options, answer) if on)
                                                    or tr("menu_none"))
    say(f"  {question} {chosen}")
    return answer


def ask_language():
    """Ask the language of the run (menu or numbered question) and set LANG."""
    global LANG
    if menus_on():
        LANG = ("it", "en")[menu("Lingua / Language:", ["Italiano", "English"], keys="↑ ↓  ·  Invio / Enter")]
        return
    print("\n  Lingua / Language:")
    print("    1 = Italiano")
    print("    2 = English")
    while True:
        choice = normalize_language(input("  Scelta / Choice [1]: ") or "1")
        if choice:
            LANG = choice
            return
        print("    1 / 2")


def welcome_screen():
    """The welcome screen as lines: title art, subtitle and the castle, fitted to the terminal."""
    art = CASTLE.strip("\n").split("\n")
    title = TITLE_ART.strip("\n").split("\n")
    subtitle = f"v{VERSION}  ·  " + tr("welcome_subtitle")
    width = max(max(len(line) for line in art), max(len(line) for line in title), len(subtitle)) + 2
    columns = terminal_width()
    if columns and columns <= width:
        width = columns - 1
    tw, aw = max(len(line) for line in title), max(len(line) for line in art)
    return ["═" * width, *[(" " * max(0, (width - tw) // 2) + line)[:width] for line in title],
            "", " " * max(0, (width - len(subtitle)) // 2) + subtitle, "═" * width,
            *[(" " * max(0, (width - aw) // 2) + line)[:width] for line in art], "═" * width]


def show_welcome():
    """Show the welcome screen and ask what to do: random, choose, or rebuild from a seed."""
    screen = welcome_screen()
    say("\n" + "\n".join(line.rstrip() for line in screen) + "\n")
    modes = ("random", "params", "rebuild")
    if menus_on():
        return modes[menu(tr("welcome_q"), [tr("mode_" + m) for m in modes], header=[l.rstrip() for l in screen])]
    return modes[menu(tr("welcome_q"), [tr("mode_" + m) for m in modes])]


def ask_choice(question, items, labels, hints=None):
    """A menu with "at random" first; returns the chosen item or None."""
    k = menu(question, [tr("at_random")] + labels, 0, [""] + (hints or [""] * len(labels)))
    return None if k == 0 else items[k - 1]


def ask_params(extra=()):
    """The questions of "I'll choose": purpose, type and people, era, terrain (and below, the folk), danger, names,
    tone and people's names; every one may be left to chance (the optional terrains among them only if in
    `extra`). Returns the fixed parameters."""
    # one question per parameter; an empty answer (random) leaves it out of `fixed`
    fixed = dict.fromkeys(extra, True)
    purpose = ask_choice(tr("q_purpose"), list(PURPOSES), [tr("purpose_rest_menu"), tr("purpose_adventure_menu")],
                         [tr("purpose_rest_hint"), tr("purpose_adventure_hint")])
    if purpose:
        fixed["purpose"] = purpose
    kind = ask_choice(tr("q_type"), [t["id"] for t in TYPES], [pick(t["menu"]) for t in TYPES],
                      [pick(t["range"]) + " · " + pick(t["about"]) for t in TYPES])
    if kind:
        fixed["type"] = kind
        lo, hi = TYPE[kind]["pop"]
        # a type also asks for its population, a random one as default
        default = random_pop(kind, random.Random())
        fixed["pop"] = ask(tr("q_pop", lo=number(lo), hi=number(hi)), default, int, lo, hi)
    era = ask_choice(tr("q_era"), [e["id"] for e in ERAS], [pick(e["menu"]) for e in ERAS],
                     [pick(e["about"]) for e in ERAS])
    if era:
        fixed["era"] = era
    terrains = [t for t in TERRAINS if t["id"] in extra or not t.get("optional")]
    terrain = ask_choice(tr("q_terrain"), [t["id"] for t in terrains], [pick(t["menu"]) for t in terrains],
                         [pick(t["about"]) if t.get("about") else "" for t in terrains])
    if terrain:
        fixed["terrain"] = terrain
    if terrain == "underground":
        folk = ask_choice(tr("q_folk"), [f["id"] for f in FOLKS], [capitalized(pick(f["name"])) for f in FOLKS],
                          [pick(f["about"]) for f in FOLKS])
        if folk:
            fixed["folk"] = folk
    # names and tone show a few examples generated on the spot
    names = ask_choice(tr("q_names"), [n["id"] for n in NAME_STYLES], [capitalized(pick(n["name"])) for n in NAME_STYLES],
                       [", ".join(name_examples(n["id"], t, 1)[0] for t in ("fair", "stately", "grim")) for n in NAME_STYLES])
    if names:
        fixed["names"] = names
    tone = ask_choice(tr("q_tone"), [t["id"] for t in NAME_TONES], [capitalized(pick(t["name"])) for t in NAME_TONES],
                      [pick(t["about"]) + (" · " + ", ".join(name_examples(names, t["id"], 2)) if names else "")
                       for t in NAME_TONES])
    if tone:
        fixed["tone"] = tone
    # people's names: examples in every style, with the names and tone chosen so far
    sample = {"names": names or "italian", "tone": tone or "homely"}
    people_hints = [tr("people_places_hint") if not names else ", ".join(people_examples(dict(sample, people="places"))),
                    ", ".join(people_examples(dict(sample, people="fantasy")))]
    people_hints += [", ".join(people_examples(dict(sample, people=n["id"]))) for n in NAME_STYLES]
    people = ask_choice(tr("q_people"), list(PEOPLE_MODES) + [n["id"] for n in NAME_STYLES],
                        [tr("people_places"), tr("people_fantasy")] + [capitalized(pick(n["name"])) for n in NAME_STYLES],
                        people_hints)
    if people:
        fixed["people"] = people
    # danger only matters in a place of adventure
    if fixed.get("purpose", None) == "adventure":
        danger = ask_choice(tr("q_danger"), list(DANGERS), [tr(f"danger_{d}") for d in DANGERS])
        if danger:
            fixed["danger"] = danger
        # in ruins (the usual for a city) or still inhabited
        state = ask_choice(tr("q_state"), list(STATES), [tr("state_ruin_menu"), tr("state_threat_menu")],
                           [tr("state_ruin_hint"), tr("state_threat_hint")])
        if state:
            fixed["state"] = state
    return fixed


def ask_colors():
    """Ask the colour scheme (1 to 5)."""
    return menu(tr("colors_intro"), [tr(f"color_name_{n}") for n in range(1, 6)], 0) + 1


def ask_name():
    """Ask the name on the map: the generated one (None), one typed in, or none ("")."""
    k = menu(tr("name_intro"), [tr("name_random"), tr("name_mine"), tr("name_none")])
    if k == 0:
        return None
    if k == 2:
        return ""
    if menus_on():
        return type_in(tr("q_name"), check=lambda t: (t.strip(), None) if t.strip() else (None, tr("name_empty")))
    while True:
        name = input(tr("q_name")).strip()
        if name:
            return name
        print(tr("name_empty"))


CONTENT_KEYS = ("story", "people", "monsters", "treasure", "intrigue")
CONTENT_WORDS = {"storia": 0, "story": 0, "abitanti": 1, "people": 1, "png": 1, "npc": 1, "mostri": 2, "monsters": 2,
                 "tesori": 3, "tesoro": 3, "treasure": 3, "intrighi": 4, "intrigue": 4, "fazioni": 4, "factions": 4}


def read_content(text):
    """The --content option as five on/off flags (story, people, monsters, treasure, intrigue)."""
    words = [w for w in text.replace("+", ",").replace(" ", ",").lower().split(",") if w]
    if words in (["mappa"], ["map"], ["mappe"], ["maps"]):
        return (False,) * len(CONTENT_KEYS)
    if words in (["tutto"], ["all"]):
        return (True,) * len(CONTENT_KEYS)
    if not words or any(w not in CONTENT_WORDS for w in words):
        raise argparse.ArgumentTypeError(tr("err_content", s=text))
    return tuple(any(CONTENT_WORDS[w] == k for w in words) for k in range(len(CONTENT_KEYS)))


def ask_content(adventure):
    """Ask what goes in the key; monsters and treasure only for a place of adventure."""
    keys = [k for k in CONTENT_KEYS if adventure or k not in ("monsters", "treasure")]
    parts = [tr("content_" + k).split(": ", 1) for k in keys]
    ticks = menu(tr("content_intro"), [a.capitalize() for a, _ in parts], hints=[b for _, b in parts],
                 ticks=(True,) * len(keys))
    chosen = dict(zip(keys, ticks))
    return tuple(chosen.get(k, False) for k in CONTENT_KEYS)


def ask_units():
    """Ask metres or feet (metres by default in Italian, feet in English)."""
    default = 1 if LANG == "it" else 0
    return ("imperial", "metric")[menu(tr("units_intro"), [tr("units_imperial"), tr("units_metric")], default)]


def ask_output():
    """png, pdf (maps and PDF file apart) or single (one PDF file with everything)."""
    options = ("png", "pdf", "single")
    return options[menu(tr("output_intro"), [tr("output_" + o) for o in options], 0)]


def ask_settings():
    """The interactive run: language, welcome, then the settlement (random, chosen or rebuilt from a seed) and its
    look. Returns the parameters."""
    ask_language()
    mode = show_welcome()
    if not menus_on():
        print(tr("enter_accepts"))
    p = {"title": None, "ascii_only": False, "font": None, "paper": None, "output": OUTPUT_FOLDER, "units": None,
         "files": None}
    if mode == "rebuild" and menus_on():
        p.update(type_in(tr("ask_seed", example=example_seed()), limit=40, check=lambda t: (
            (read_seed(t), None) if read_seed(t) else (None, tr("seed_invalid", example=example_seed())))))
    elif mode == "rebuild":
        while True:
            seed = read_seed(input(tr("ask_seed", example=example_seed())))
            if seed:
                break
            print(tr("seed_invalid", example=example_seed()))
        p.update(seed)
    else:
        # the optional terrains: none ticked, places are made as always
        optional = [t["id"] for t in TERRAINS if t.get("optional")]
        ticks = menu(tr("q_optional"), [tr("opt_" + t).split(": ", 1)[0] for t in optional],
                     hints=[tr("opt_" + t).split(": ", 1)[1] for t in optional], ticks=(False,) * len(optional),
                     help_key="optional_help")
        extra = [t for t, on in zip(optional, ticks) if on]
        fixed = ask_params(extra) if mode == "params" else dict.fromkeys(extra, True)
        p.update(random_params(new_number(), fixed))
    p["colors"] = ask_colors()
    p["ascii_only"] = menu(tr("ascii_intro"), [tr("ascii_no"), tr("ascii_yes")], 0) == 1
    p["title"] = ask_name()
    p["content"] = ask_content(p["purpose"] == "adventure")
    p["units"] = ask_units()
    p["ask_paper"] = sys.stdin.isatty()
    return p


def read_choice(table, label):
    """An argparse type for an option naming an item of `table`: by id, code, name, alias, number, or the start of a
    word."""
    def parse(text):
        """The id of the item `text` names, or an argparse error."""
        t = text.strip().lower()
        for item in table:
            names = {item["id"], item["code"].lower(), *(n.lower() for n in item.get("menu", ())),
                     *(n.lower() for n in item["name"]), *(n.lower() for n in item.get("aliases", ()))}
            plain = {n.replace("à", "a") for n in names}
            if t in names or t.replace("à", "a") in plain or (len(t) >= 3 and any(
                    n.startswith(t) or (" " in n and n.split(" ")[-1].startswith(t)) or n.startswith("grande " + t)
                    for n in plain)):
                return item["id"]
        try:
            k = int(t)
            return table[k - 1]["id"]
        except (ValueError, IndexError):
            raise argparse.ArgumentTypeError(tr("err_choice", s=text, w=label))
    return parse


def settings_from_options(argv):
    """The parameters of a run from its command-line options (Italian and English names for every option); missing
    ones are chosen at random."""
    language_from_options(argv)

    def names(italian, english):
        """An option's two names, the current language's first (it shows in the help)."""
        return (f"--{italian}", f"--{english}") if LANG == "it" else (f"--{english}", f"--{italian}")
    # every option in both languages
    def read_state(text):
        """The --state option: in ruins or inhabited, in either language."""
        state = {"rovina": "ruin", "rovine": "ruin", "ruin": "ruin", "ruins": "ruin", "abitato": "threat",
                 "minacciato": "threat", "inhabited": "threat", "threatened": "threat"}.get(text.strip().lower())
        if not state:
            raise argparse.ArgumentTypeError(tr("err_choice", s=text, w="stato" if LANG == "it" else "state"))
        return state
    ap = argparse.ArgumentParser(description=tr("h_description"), epilog=tr("h_epilog"))
    ap.add_argument(*names("lingua", "language"), dest="language", default=LANG, metavar="{it,en}", help=tr("h_language"))
    ap.add_argument(*names("tipo", "type"), dest="type", type=read_choice(TYPES, "tipo"), default=None,
                    help=tr("h_type"))
    ap.add_argument(*names("popolazione", "population"), dest="pop", type=int, default=None, help=tr("h_pop"))
    ap.add_argument(*names("epoca", "era"), dest="era", type=read_choice(ERAS, "epoca"), default=None, help=tr("h_era"))
    ap.add_argument(*names("terreno", "terrain"), dest="terrain", type=read_choice(TERRAINS, "terreno"), default=None,
                    help=tr("h_terrain"))
    ap.add_argument(*names("funghi", "mushrooms"), dest="fungus", action="store_true", help=tr("h_fungus"))
    ap.add_argument(*names("sottosuolo", "underground"), dest="underground", action="store_true",
                    help=tr("h_underground"))
    ap.add_argument(*names("popolo", "folk"), dest="folk", type=read_choice(FOLKS, "popolo"), default=None,
                    help=tr("h_folk"))
    ap.add_argument(*names("scopo", "purpose"), dest="purpose", default=None, help=tr("h_purpose"))
    ap.add_argument(*names("pericolo", "danger"), dest="danger", type=int, choices=DANGERS, default=None,
                    help=tr("h_danger"))
    ap.add_argument(*names("stato", "state"), dest="state", type=read_state, default=None,
                    metavar="{rovina,abitato}" if LANG == "it" else "{ruin,inhabited}", help=tr("h_state"))
    ap.add_argument(*names("nomi", "names"), dest="names", type=read_choice(NAME_STYLES, "nomi"), default=None,
                    help=tr("h_names"))
    ap.add_argument(*names("tono", "tone"), dest="tone", type=read_choice(NAME_TONES, "tono"), default=None,
                    help=tr("h_tone"))
    language = read_choice(NAME_STYLES, "persone")

    def read_people(text):
        """The --people option: places, fantasy, or a language."""
        mode = {"luoghi": "places", "places": "places", "come-luoghi": "places", "like-places": "places",
                "fantasy": "fantasy", "fantasia": "fantasy"}.get(text.strip().lower())
        return mode or language(text)
    ap.add_argument(*names("persone", "people"), dest="people", type=read_people, default=None, help=tr("h_people"))
    ap.add_argument(*names("seme", "seed"), dest="seed", default=None, help=tr("h_seed"))
    ap.add_argument(*names("colori", "colors"), dest="colors", type=int, choices=(1, 2, 3, 4, 5), default=1, help=tr("h_colors"))
    ap.add_argument(*names("formato", "format"), dest="paper", type=str.upper, choices=list(PAPERS), default=None,
                    help=tr("h_format"))
    files = ap.add_mutually_exclusive_group()
    files.add_argument("--png", dest="files", action="store_const", const="png", default=None, help=tr("h_png"))
    files.add_argument("--pdf", dest="files", action="store_const", const="pdf", help=tr("h_pdf"))
    files.add_argument(*names("pdf-unico", "single-pdf"), dest="files", action="store_const", const="single",
                       help=tr("h_single"))
    naming = ap.add_mutually_exclusive_group()
    naming.add_argument(*names("titolo", "title"), dest="title", default=None, help=tr("h_title"))
    naming.add_argument(*names("senza-titolo", "no-title"), dest="title", action="store_const", const="",
                        help=tr("h_no_title"))
    ap.add_argument(*names("contenuto", "content"), dest="content", type=read_content, default=None,
                    metavar="{mappa,tutto,storia,abitanti,mostri,tesori,intrighi}" if LANG == "it"
                    else "{map,all,story,people,monsters,treasure,intrigue}", help=tr("h_content"))
    ap.add_argument(*names("unita", "units"), dest="units", default=None,
                    choices=("imperiale", "metrica", "imperial", "metric"), help=tr("h_units"))
    ap.add_argument(*names("solo-ascii", "ascii-only"), dest="ascii_only", action="store_true", help=tr("h_ascii"))
    ap.add_argument("--font", default=None, metavar="FILE", help=tr("h_font"))
    ap.add_argument(*names("uscita", "output"), dest="output", default=OUTPUT_FOLDER, help=tr("h_output"))
    ap.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    a = ap.parse_args(argv)
    # the look of the output, then the parameters of the settlement the user fixed
    p = {"title": a.title, "ascii_only": a.ascii_only, "font": a.font, "paper": a.paper, "output": a.output,
         "colors": a.colors, "files": a.files, "content": a.content or (True,) * len(CONTENT_KEYS),
         "units": {"imperiale": "imperial", "metrica": "metric"}.get(a.units, a.units)}
    fixed = {k: v for k, v in (("type", a.type), ("era", a.era), ("terrain", a.terrain), ("pop", a.pop),
                                ("danger", a.danger), ("state", a.state), ("names", a.names), ("tone", a.tone),
                                ("people", a.people)) if v is not None}
    if a.fungus:
        fixed["fungus"] = True
    if a.underground:
        fixed["underground"] = True
    if a.folk:                  # a folk means the underground
        fixed["folk"] = a.folk
        fixed.setdefault("terrain", "underground")
    if a.purpose:
        purpose = {"riposo": "rest", "rest": "rest", "avventura": "adventure", "adventure": "adventure"}.get(
            a.purpose.strip().lower())
        if not purpose:
            ap.error(tr("err_choice", s=a.purpose, w="scopo"))
        fixed["purpose"] = purpose
    # a danger means an adventure; a population alone picks the type that fits it
    if "danger" in fixed or "state" in fixed:
        fixed.setdefault("purpose", "adventure")
    if "pop" in fixed and "type" not in fixed:
        fixed["type"] = next((t["id"] for t in TYPES if t["id"] not in ("castle", "fortress")
                              and t["pop"][0] <= fixed["pop"] <= t["pop"][1]), "bigcity")
    # a seed gives every parameter; without one, the rest are drawn at random
    if a.seed:
        seed = read_seed(a.seed)
        if not seed:
            ap.error(tr("err_seed", s=a.seed))
        p.update(seed)
    else:
        p.update(random_params(new_number(), fixed))
    error = check_params(p)
    if error:
        ap.error(error)
    p["ask_paper"] = a.paper is None and sys.stdin.isatty()
    return p


# --- main ---
def main():
    """Run WyrmUrbiGen: interactive without options, else from the options; in interactive mode, offer to make the
    same settlement again in another look."""
    interactive = len(sys.argv) == 1
    try:
        params = ask_settings() if interactive else settings_from_options(sys.argv[1:])
        make(params, interactive)
        while interactive and ask_again():
            restyle(params)
            make(params, interactive, again=True)
    finally:
        # never leave the terminal on the questions' screen, not even on Ctrl+C or an error
        screen_off()


def ask_again():
    """At the end: the same settlement again, in other colours and styles?"""
    say("")
    log = console_lines() if SCREEN["open"] is not None else None
    try:
        return menu(tr("again_q"), [tr("again_no"), tr("again_yes")], 0, header=log, tail=True) == 1
    except EOFError:
        return False


def restyle(p):
    """The look of the next print: colours, symbols, paper and files; the seed stays."""
    p["colors"] = ask_colors()
    p["ascii_only"] = menu(tr("ascii_intro"), [tr("ascii_no"), tr("ascii_yes")], 0) == 1
    p["paper"], p["files"], p["ask_paper"] = None, None, sys.stdin.isatty()


def make(params, interactive, again=False):
    """One settlement, maps and key. again: a reprint of the same seed in another
    look; its maps and PDF file get the paper and style in their names
    (<seed>_referee_A3_c5.png), so the earlier ones stay."""
    # 1. settings: the seed, what it means, what goes in the key
    log = Log(6)
    log.step(tr("step_settings"))
    seed = make_seed(params)
    log.info(tr("info_seed", s=seed))
    p = params
    log.info(tr("info_what", t=type_name(p["type"]), n=number(p["pop"]), e=pick(ERA[p["era"]]["name"]),
                g=pick(TERRAIN[p["terrain"]]["name"])))
    log.info(adventure_words(p))
    if p.get("names"):
        log.info(tr("info_names", s=pick(NAME_STYLE[p["names"]]["name"]), t=pick(NAME_TONE[p["tone"]]["name"]),
                    m=round_millions(name_combinations(p["names"], p["tone"]))))
        m, f, c = people_counts(p)
        log.info(tr("info_people", w=people_words(p), m=number(m), f=number(f), c=number(c)))
    else:
        log.info(tr("info_names_old"))
    # a place of rest has no monsters or treasure; neither does a key without their tables
    units = p.get("units") or ("metric" if LANG == "it" else "imperial")
    content = list(p["content"])
    if p["purpose"] == "rest":
        content[2] = content[3] = False
    if content[2] and not MONSTERS:
        log.warn(tr("warn_no_monsters"))
        content[2] = False
    if content[3] and not TREASURE:
        log.warn(tr("warn_no_treasure"))
        content[3] = False
    problem = pdf_problem()
    if problem:
        log.error(problem)
    # one folder per seed
    folder = os.path.join(p["output"], seed)
    # easter egg: a settlement the user names Pisa gets a subtitle, and a
    # fonder one when the same seed was already printed as Pisa
    motto = None
    if (p["title"] or "").strip().casefold() == "pisa":
        try:
            with open(os.path.join(folder, f"{seed}_key.txt"), encoding="utf-8") as f:
                again = f.readline().strip().casefold().endswith("— pisa")
        except OSError:
            again = False
        motto = tr("bolpo_again" if again else "bolpo")
    os.makedirs(folder, exist_ok=True)
    log.info(tr("info_folder", folder=short_path(folder)))
    # the font and the shape of its letters (the map's aspect)
    font_spec, bold_spec = find_font(p["font"])
    advance_em, line_em = font_metrics(font_spec)
    aspect = line_em / advance_em

    # 2. the map
    log.step(tr("step_map"))
    plan = build_plan(p, seed)
    log.info(tr("info_map", w=plan.W, h=plan.H, b=len(plan.buildings), g=len([g for g in plan.gates if g.get("cells")])))
    if plan.missing:
        log.info(tr("info_missing", n=sum(plan.missing.values())))

    # 3. people, threat, monsters, treasure and lore
    log.step(tr("step_people"))
    s = make_settlement(p, plan, seed)
    if p["purpose"] == "adventure":
        plan_threat(s)
        if MONSTERS:
            plan_monsters(s)
        else:
            s.wander, s.occupants, s.contents = [], {}, {}
        if TREASURE:
            plan_treasure(s)
        log.info(tr("info_threat", t=pick(s.situation["name"]), n=s.lair.number))
    plan_past(s)
    plan_intrigue(s)
    plan_lore(s)
    title = pick(s.title) if p["title"] is None else p["title"]
    log.info(f"«{title}»" if LANG == "it" else f"“{title}”")

    # 4. paper and layout
    log.step(tr("step_paper"))
    G = Glyphs(open_font(font_spec, 40), p["ascii_only"])
    plain = Glyphs(None, True)
    subtitle = tr("subtitle", seed=seed, t=capitalized(type_name(p["type"])), e=pick(ERA[p["era"]]["name"]),
                  n=number(p["pop"]), b=len(plan.buildings))

    def page_layout(G, referee, title, side):
        """The referee's map has the secrets, on the map and in the building
        index; the players' map has numbers and index, but no secrets."""
        return Layout(map_canvas(plan, True, G, secrets=referee), legend_entries(plan, p, True, G, units, referee),
                      title, subtitle, building_index(s), building_secrets(s) if referee else (), side, motto)
    # the building index goes under the map or beside it, whichever prints
    # the map bigger on the paper
    paper, char_mm, orientation, ref_layout = ask_paper([page_layout(G, True, title, side) for side in (False, True)],
                                                        aspect, p["paper"], p.pop("ask_paper", False), log)
    side = ref_layout.side
    log.info(tr("info_index_side" if side else "info_index_under"))
    # PNG maps, PDF maps, or one PDF file with maps and key
    files = p["files"] or (ask_output() if interactive else "png")
    fonts = (font_spec, bold_spec, advance_em, aspect)
    pixels = pixel_layout(ref_layout, paper, orientation, char_mm, fonts)
    printed = pixels[2] / DPI * 25.4
    log.info(tr("info_sheet", paper=paper, o=tr("orientation_" + orientation), w=pixels[5], h=pixels[6], dpi=DPI,
                mm=printed))
    if printed < SMALL_CHAR_MM:
        log.warn(tr("warn_tiny"))
    settings = {"seed": seed, "colors": p["colors"], "paper": paper, "title": p["title"], "language": LANG,
                "ascii_only": p["ascii_only"], "files": files, "units": units, "version": VERSION}
    # 5. the maps: the referee's and the players', each as text and as an image
    log.step(tr("step_maps", paper=paper, dpi=DPI))
    pl_title = tr("players_title", t=title) if title else tr("players_title_plain")
    pl_layout = page_layout(G, False, pl_title, side)
    tag = f"_{paper}_c{p['colors']}" + ("_ascii" if p["ascii_only"] else "") if again else ""
    if again:
        log.info(tr("info_again", s=seed, t=tag))
    pages = [("referee", compose_page(ref_layout), pixels, compose_page(page_layout(plain, True, title, side))),
             ("players", compose_page(pl_layout), pixel_layout(pl_layout, paper, orientation, char_mm, fonts),
              compose_page(page_layout(plain, False, pl_title, side)))]
    images = []
    base = os.path.join(folder, seed)
    for name, canvas, px, text in pages:
        write_text(f"{base}_{name}.txt", text)
        img, live = draw_sheet(canvas, px, p["colors"])
        if files == "png":
            save_png(img, f"{base}_{name}{tag}.png", settings)
            live.finish()
            log.info(tr("saved", a=short_path(f"{base}_{name}{tag}.png"), b=short_path(f"{base}_{name}.txt")))
        elif files == "pdf":
            doc = PdfFile(f"{base}_{name}{tag}.pdf", settings)
            doc.add_page(img)
            doc.close()
            live.finish()
            log.info(tr("saved", a=short_path(f"{base}_{name}{tag}.pdf"), b=short_path(f"{base}_{name}.txt")))
        else:
            live.finish()
            images.append((name, img.convert("RGB") if img.mode == "P" else img, paper, orientation))
            log.info(tr("saved_txt", a=short_path(f"{base}_{name}.txt")))
        del img

    # 6. the key, as text and as a PDF file (with the maps in front, in the single-PDF option)
    log.step(tr("step_key"))
    blocks = key_blocks(s, title, units, content)
    if motto:
        blocks.insert(1, ("motto", motto))     # in the PDF file only: write_key skips it
    write_key(blocks, f"{base}_key.txt")
    log.info(tr("saved_key", a=short_path(f"{base}_key.txt")))
    if not problem:
        pdf_path = f"{base}_key{tag}.pdf"
        try:
            write_pdf(blocks, pdf_path, settings, maps=images)
            log.info(tr("saved_pdf_maps" if images else "saved_pdf", a=short_path(pdf_path)))
        except Exception as e:          # never lose the maps and the key over the PDF
            log.error(tr("err_pdf", e=f"{type(e).__name__}: {e}"))
    elif images:
        for name, img, _, _ in images:
            save_png(img, f"{base}_{name}{tag}.png", settings)
    if G.missing:
        log.warn(tr("warn_missing_glyphs", g=" ".join(sorted(G.missing))))
    log.done()


if __name__ == "__main__":
    try:
        sys.stdout.reconfigure(errors="replace")
    except AttributeError:
        pass
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print(tr("interrupted"))
        sys.exit(1)

