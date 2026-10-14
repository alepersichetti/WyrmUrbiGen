#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WyrmUrbiGen v1.0.0 - random villages, boroughs, walled cities, castles and
fortresses for OSR games, all in ASCII.

Sibling of WyrmHex (hexcrawl maps) and WyrmDelve (dungeons). It draws the plan
of a settlement with letters and symbols, like an old roguelike, numbers every
building, and writes a key (a TXT file and a PDF file, like WyrmDelve's) with the
history, the government and factions, the inhabitants of every building with
OSR stats, rumours and events, and:

  * a place of rest for adventurers: inns, healers, smiths, horses, retainers
    and mercenaries for hire, prices in gold pieces;
  * a place of adventure: a threat (brigands, a cult, plague, a curse, orcs, a
    beast, ruins, a necromancer, something from the water, a dragon, a mine, a
    feud), wandering monsters, monsters and clues in the buildings and treasure,
    using WyrmDelve's bestiary and its Old-School Essentials treasure tables.

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
suggested. Three colour schemes. --ascii-only uses keyboard characters only,
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

The seed (e.g. C2-B-R-A2-DE4-K7Q2MB = type+size, era, terrain,
purpose+danger, names+tone, code) holds the whole settlement: the same seed
always gives the same one. Seeds without names+tone, made by older versions,
still work and keep their medieval Italian names.

Usage. Every option has an Italian and an English name, use whichever:
  python wyrmurbigen.py                              interactive
  python wyrmurbigen.py --tipo citta --epoca basso   / --type city --era late
  python wyrmurbigen.py --terreno costa              / --terrain coast
  python wyrmurbigen.py --scopo avventura --pericolo 3   / --purpose adventure --danger 3
  python wyrmurbigen.py --dimensione 3               / --size 3
  python wyrmurbigen.py --nomi tedesco --tono cupo    / --names german --tone grim
  python wyrmurbigen.py --seme C2-B-R-A2-DE4-K7Q2MB  / --seed C2-B-R-A2-DE4-K7Q2MB
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


# --- settings ---

VERSION = "1.0.0"
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
    "q_danger": ("Quanto è pericoloso?", "How dangerous is it?"),
    "danger_1": ("1 · per personaggi di livello 1-2", "1 · for characters of level 1-2"),
    "danger_2": ("2 · per personaggi di livello 3-4", "2 · for characters of level 3-4"),
    "danger_3": ("3 · per personaggi di livello 5-7", "3 · for characters of level 5-7"),
    "danger_4": ("4 · per personaggi di livello 8 e oltre", "4 · for characters of level 8 and up"),
    "colors_intro": ("Combinazione di colori della mappa:", "Map colour scheme:"),
    "color_name_1": ("nero su bianco (per stampare)", "black on white (for printing)"),
    "color_name_2": ("bianco su celeste", "white on light blue"),
    "color_name_3": ("bianco su nero (per lo schermo)", "white on black (for screens)"),
    "ascii_intro": ("Simboli della mappa:", "Map symbols:"),
    "ascii_no": ("simboli come ▓ █ ≈ ♣ ╔═╗ (consigliato)", "symbols such as ▓ █ ≈ ♣ ╔═╗ (suggested)"),
    "ascii_yes": ("solo i caratteri base della tastiera, come WyrmHex (# @ ~ T)", "keyboard characters only, like WyrmHex (# @ ~ T)"),
    "name_intro": ("Nome sulla mappa:", "Name on the map:"),
    "name_random": ("quello dell'insediamento, generato a caso", "the settlement's own, made at random"),
    "name_mine": ("lo scrivo io", "I'll type it"),
    "name_none": ("nessun nome", "no name"),
    "q_name": ("  Nome della mappa: ", "  Map name: "),
    "name_empty": ("    Scrivi un nome.", "    Type a name."),
    "content_intro": ("Cosa vuoi nella chiave e nel PDF?", "What do you want in the key and the PDF?"),
    "content_story": ("storia: storia, fazioni, economia, voci ed eventi", "story: history, factions, economy, rumours and events"),
    "content_people": ("abitanti: un PNG per ogni edificio, con statistiche OSR", "people: an NPC for every building, with OSR stats"),
    "content_monsters": ("mostri: mostri erranti, mostri e indizi negli edifici", "monsters: wandering monsters, monsters and clues in the buildings"),
    "content_treasure": ("tesori: monete, gemme, gioielli e oggetti magici", "treasure: coins, gems, jewellery and magic items"),
    "content_help": ("    Scrivi i numeri che vuoi, separati da virgole (es. 1,2); 0 = solo l'elenco degli edifici.",
                     "    Type the numbers you want, separated by commas (e.g. 1,2); 0 = only the list of buildings."),
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
    "lg_hill": ("colline", "hills"),
    "lg_mount": ("montagne", "mountains"),
    "lg_reed": ("canneto", "reeds"),
    "lg_secret": ("postierla segreta (solo arbitro)", "secret postern (referee only)"),
    "lg_tunnel": ("galleria segreta (solo arbitro)", "secret tunnel (referee only)"),
    "lg_scale": ("Scala:", "Scale:"),
    "lg_row": (" (una riga = {r} {u})", " (one row = {r} {u})"),
    # key
    "key_seed": ("Seme", "Seed"),
    "key_pop": ("{n} abitanti", "{n} inhabitants"),
    "key_names": ("Nomi: {s}, tono {t}", "Names: {s}, {t} tone"),
    "key_scale": ("Scala: una riga di caratteri = {r} {u}, una colonna = metà", "Scale: one row of letters = {r} {u}, one column = half"),
    "purpose_rest": ("Luogo di riposo per gli avventurieri", "Place of rest for adventurers"),
    "purpose_adventure": ("Luogo d'avventura, pericolo {d}", "Place of adventure, danger {d}"),
    "h_history": ("Storia", "History"),
    "h_threat": ("La minaccia: {t}", "The threat: {t}"),
    "threat_villain": ("Chi c'è dietro: {v}", "Who is behind it: {v}"),
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
    "demo_note": ("Numeri da Medieval Demographics Made Easy di S. John Ross: le botteghe sono tutte in città, sulla mappa "
                  "ci sono le {n} più importanti.",
                  "Numbers from S. John Ross's Medieval Demographics Made Easy: every shop is in town, the map shows the "
                  "{n} most important ones."),
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
    "eco_rules": ("Regole di Coins and Scrolls (OSR: Land and Investments): la terra di rado si vende, più spesso si "
                  "eredita, si dona o si conquista. In tempi di peste, guerra o carestia ogni rendita si dimezza; in tempi "
                  "di vero caos si divide per 10. Chi imbroglia sulle tasse tiene un altro {c}% della rendita, finché un "
                  "signore attento non controlla i conti.",
                  "Rules from Coins and Scrolls (OSR: Land and Investments): land is rarely sold, it is more often "
                  "inherited, given or seized. In times of plague, war or famine every income is halved; in truly "
                  "chaotic times it is divided by 10. Whoever cheats on taxes keeps another {c}% of the income, until a "
                  "careful lord audits the books."),
    "h_services": ("Servizi per gli avventurieri", "Services for adventurers"),
    "mercenaries": ("Mercenari e seguaci (paga al mese)", "Mercenaries and followers (monthly wage)"),
    "merc_row": ("{n} {name}, {w} mo al mese ({s})", "{n} {name}, {w} gp a month ({s})"),
    "hirelings": ("Avventurieri da assoldare", "Adventurers for hire"),
    "hireling_pay": (" Chiede 25 mo al mese e mezza parte del bottino.", " Asks 25 gp a month and half a share of the loot."),
    "hooks": ("Lavori e agganci (d4)", "Jobs and hooks (d4)"),
    "rumours": ("Voci (d8; V vera, F falsa: solo per l'arbitro)", "Rumours (d8; T true, F false: referee only)"),
    "true": ("V", "T"),
    "false": ("F", "F"),
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
    "h_sources": ("Fonti", "Sources"),
    "sources": ("Mostri, indizi e tesori vengono da WyrmDelve (tesori: Old-School Essentials SRD, Open Game License 1.0a). "
                "Popolazione, densità e mestieri: S. John Ross, Medieval Demographics Made Easy. Contado, rendite e proprietà: "
                "Skerples, OSR: Land and Investments (Coins and Scrolls). Di queste fonti sono usati solo i numeri.",
                "Monsters, clues and treasure come from WyrmDelve (treasure: Old-School Essentials SRD, Open Game License 1.0a). "
                "Population, density and trades: S. John Ross, Medieval Demographics Made Easy. Country, revenue and property: "
                "Skerples, OSR: Land and Investments (Coins and Scrolls). Only the numbers of these sources are used."),
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
    "h_terrain": ("pianura, collina, montagna, foresta, palude, costa, fiume, lago (o 1-8)",
                  "plains, hills, mountains, forest, swamp, coast, river, lake (or 1-8)"),
    "h_purpose": ("riposo o avventura", "rest or adventure"),
    "h_danger": ("pericolo del luogo d'avventura, da 1 a 4", "danger of the place of adventure, 1 to 4"),
    "h_names": ("lingua dei nomi dei luoghi: italiano, antico (Old English), rinascimentale, gaelico, tolkien, "
                "persiano, bizantino, tedesco, francese, danese, russo, misto (o 1-12)",
                "language of the place names: italian, old english, renaissance, gaelic, tolkien, persian, byzantine, "
                "german, french, danish, russian, mixed (or 1-12)"),
    "h_tone": ("tono dei nomi: luminoso, rustico, solenne, cupo, arcano (o 1-5)",
               "tone of the names: fair, homely, stately, grim, eerie (or 1-5)"),
    "h_seed": ("seme completo (es. C9500-B-R-A2-DE4-K7Q2MB) per rifare un insediamento",
               "full seed (e.g. C9500-B-R-A2-DE4-K7Q2MB) to rebuild a settlement"),
    "h_colors": ("1 nero su bianco (default), 2 bianco su celeste, 3 bianco su nero", "1 black on white (default), 2 white on light blue, 3 white on black"),
    "h_format": ("formato di stampa; senza, viene suggerito e chiesto", "print format; without it, it is suggested and asked"),
    "h_png": ("mappe in PNG e chiave in un file PDF a parte (di base)", "PNG maps and the key in a separate PDF file (the default)"),
    "h_pdf": ("mappe in PDF e chiave in un file PDF a parte", "PDF maps and the key in a separate PDF file"),
    "h_single": ("un unico file PDF con le mappe e la chiave", "one single PDF file with the maps and the key"),
    "h_title": ("titolo della mappa (default: il nome dell'insediamento)", "map title (default: the settlement's name)"),
    "h_no_title": ("mappa senza nome", "map without a name"),
    "h_content": ("cosa mettere nella chiave: storia, abitanti, mostri, tesori, anche insieme separati da virgole; "
                  "mappa = solo l'elenco degli edifici; tutto = tutto (di base)",
                  "what to put in the key: story, people, monsters, treasure, also together separated by commas; "
                  "map = only the list of buildings; all = everything (the default)"),
    "h_units": ("unità: imperiale o metrica (di base metrica in italiano, imperiale in inglese)",
                "units: imperial or metric (by default imperial in English, metric in Italian)"),
    "h_ascii": ("solo caratteri base della tastiera, come WyrmHex", "only basic keyboard characters, like WyrmHex"),
    "h_font": ("file .ttf monospazio da usare", "monospaced .ttf font file to use"),
    "h_output": ("cartella in cui salvare (default: settlements_generated accanto allo script)",
                 "folder to save into (default: settlements_generated next to the script)"),
}



def tr(key, **values):
    text = TEXTS[key][LANGUAGES.index(LANG)]
    return text.format(**values) if values else text


def pick(pair):
    return pair[LANGUAGES.index(LANG)]


def fmt(pair, **values):
    return tuple(t.format(**{k: (v[i] if isinstance(v, tuple) else v) for k, v in values.items()})
                 for i, t in enumerate(pair))


def capitalized(text):
    return text[:1].upper() + text[1:] if text else text


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
    text = f"{n:,}"
    return text.replace(",", ".") if LANG == "it" else text


# --- console output ---
def bar(fraction, cells):
    full = round(max(0.0, min(1.0, fraction)) * cells)
    return "[" + "█" * full + "░" * (cells - full) + "]"


class LiveBar:
    """Progress bar that keeps redrawing the same line. Silent when stdout isn't a tty."""

    def __init__(self):
        self.live = sys.stdout.isatty()
        self.shown = None

    def update(self, fraction, label):
        percent = int(fraction * 100)
        if self.live and (percent, label) != self.shown:
            self.shown = (percent, label)
            print(f"\r        {bar(fraction, 30)} {percent:>3}%  {label:<14}", end="", flush=True)

    def finish(self):
        if self.live:
            print(f"\r        {bar(1, 30)} 100%  {tr('pb_done'):<14}")


class Log:

    def __init__(self, total_steps):
        self.total_steps, self.step_number, self.start_time = total_steps, 0, time.perf_counter()

    def step(self, message):
        self.step_number += 1
        progress = bar(self.step_number / self.total_steps, self.total_steps)
        print(f"\n{progress} {self.step_number:>2}/{self.total_steps}  {message}")

    def info(self, message):
        print(f"        · {message}")

    def warn(self, message):
        print(f"        ! {message}")

    def error(self, message):
        print(f"        ✗ {message}")

    def done(self):
        print("\n" + tr("done", s=time.perf_counter() - self.start_time))


# --- tables ---
# The words the settlements are made of live in the JSON files of the data
# folder, next to this file. Every text there is {"it": ..., "en": ...}; here
# it becomes (it, en).
HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
OPTIONAL_DATA = ("monsters.json", "clues.json", "treasure.json")    # from WyrmDelve: without them, no monsters or treasure
REQUIRED = ("settlement_types", "eras", "terrains", "name_styles", "name_tones", "name_forms", "saints", "signs", "gates",
            "quarters", "history",
            "situations", "rumors", "adventure_rumors", "events", "hooks", "dungeons", "buildings", "first_names",
            "families", "family_adj", "bynames", "places", "trades", "traits", "wants", "secrets", "rulers",
            "factions", "guilds", "classes", "spells", "retainers", "demographics", "economy")


def from_json(value):
    if isinstance(value, dict) and set(value) == {"it", "en"}:
        return value["it"], value["en"]
    if isinstance(value, dict):
        return {k: from_json(v) for k, v in value.items()}
    if isinstance(value, list):
        return [from_json(v) for v in value]
    return value


def read_json(path):
    name = os.path.relpath(path, HERE)
    try:
        with open(path, encoding="utf-8") as f:
            return from_json(json.load(f))
    except OSError:
        sys.exit(f"Non riesco a leggere {name} / Cannot read {name}")
    except ValueError as e:
        sys.exit(f"C'è un errore nel file {name} / There is a mistake in {name}:\n  {e}")


def load_tables(folder=DATA):
    if not os.path.isdir(folder):
        sys.exit("Manca la cartella data: mettila nella stessa cartella di wyrmurbigen.py.\n"
                 "The data folder is missing: put it in the same folder as wyrmurbigen.py.")
    tables = {}
    for name in sorted(os.listdir(folder)):
        if name.endswith(".json") and name not in OPTIONAL_DATA:
            tables.update(read_json(os.path.join(folder, name)))
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


TABLES = load_tables()
TYPES = TABLES["settlement_types"]
TYPE = {t["id"]: t for t in TYPES}
TYPE_BY_CODE = {t["code"]: t["id"] for t in TYPES}
ERAS = TABLES["eras"]
ERA = {e["id"]: e for e in ERAS}
ERA_BY_CODE = {e["code"]: e["id"] for e in ERAS}
TERRAINS = TABLES["terrains"]
TERRAIN = {t["id"]: t for t in TERRAINS}
TERRAIN_BY_CODE = {t["code"]: t["id"] for t in TERRAINS}
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
# TYPE+POPULATION-ERA-TERRAIN-PURPOSE+DANGER-NAMES+TONE-CODE, e.g.
# C9500-B-R-A2-DE4-K7Q2MB: a city of 9,500 people, Late Middle Ages, on a river,
# a place of adventure of danger 2, grim German names. CODE = 6 symbols, 30
# random bits. Older seeds have no NAMES+TONE part: their names are the
# medieval Italian ones of old, made exactly as before.
SEED_SYMBOLS = "0123456789ABCDEFGHJKMNPQRSTVWXYZ"   # no I, L, O, U: too easy to misread
CODE_LENGTH = 6
PURPOSES = ("rest", "adventure")


def new_number():
    return int.from_bytes(os.urandom(4), "big") % (len(SEED_SYMBOLS) ** CODE_LENGTH)


def to_code(n):
    out = []
    for _ in range(CODE_LENGTH):
        n, r = divmod(n, len(SEED_SYMBOLS))
        out.append(SEED_SYMBOLS[r])
    return "".join(reversed(out))


def from_code(text):
    text = text.strip().upper().replace("O", "0").replace("I", "1").replace("L", "1")
    if len(text) != CODE_LENGTH or any(c not in SEED_SYMBOLS for c in text):
        return None
    n = 0
    for c in text:
        n = n * len(SEED_SYMBOLS) + SEED_SYMBOLS.index(c)
    return n


def make_seed(p):
    purpose = "A" if p["purpose"] == "adventure" else "R"
    names = f"{NAME_STYLE[p['names']]['code']}{NAME_TONE[p['tone']]['code']}-" if p.get("names") else ""
    return (f"{TYPE[p['type']]['code']}{p['pop']}-{ERA[p['era']]['code']}-{TERRAIN[p['terrain']]['code']}-"
            f"{purpose}{p['danger']}-{names}{to_code(p['number'])}")


def read_seed(text):
    parts = (text or "").strip().upper().replace(" ", "").split("-")
    names = tone = None
    if len(parts) == 6:             # with the names part
        names, tone = NAME_STYLE_BY_CODE.get(parts[4][:-1]), NAME_TONE_BY_CODE.get(parts[4][-1:])
        if None in (names, tone):
            return None
        del parts[4]
    if len(parts) != 5 or len(parts[0]) < 2 or len(parts[3]) != 2:
        return None
    kind, era, terrain = TYPE_BY_CODE.get(parts[0][0]), ERA_BY_CODE.get(parts[1]), TERRAIN_BY_CODE.get(parts[2])
    purpose = {"A": "adventure", "R": "rest"}.get(parts[3][0])
    n = from_code(parts[4])
    if None in (kind, era, terrain, purpose, n) or not parts[0][1:].isdigit() or not parts[3][1].isdigit():
        return None
    p = {"type": kind, "pop": int(parts[0][1:]), "era": era, "terrain": terrain, "purpose": purpose,
         "danger": int(parts[3][1]), "names": names, "tone": tone, "number": n}
    return None if check_params(p) else p


def example_seed():
    return "C9500-B-R-A2-DE4-K7Q2MB"


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


def random_params(n, fixed=None):
    """Random parameters from the seed number; `fixed` ones are kept as they are."""
    fixed = dict(fixed or {})
    r = random.Random(f"wyrmurbigen-params-{n}")
    p = {"type": r.choices([t["id"] for t in TYPES], weights=[5, 4, 2, 1, 3, 2][:len(TYPES)])[0],
         "era": r.choice([e["id"] for e in ERAS]),
         "terrain": r.choice([t["id"] for t in TERRAINS]),
         "purpose": r.choice(PURPOSES)}
    p.update({k: v for k, v in fixed.items() if k in ("type", "era", "terrain", "purpose")})
    p["pop"] = fixed.get("pop") or random_pop(p["type"], r)
    if p["purpose"] == "adventure":
        p["danger"] = fixed.get("danger") or r.choices(DANGERS, weights=[4, 4, 3, 1])[0]
    else:
        p["danger"] = 0
    p["names"] = fixed.get("names") or r.choice([n["id"] for n in NAME_STYLES])
    p["tone"] = fixed.get("tone") or r.choice([t["id"] for t in NAME_TONES])
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


def styled_name(rng, names, tone):
    style = NAME_STYLE[names]
    if style.get("mix"):            # every root from a language of its own
        styles = [n for n in NAME_STYLES if not n.get("mix")]
        first, last = rng.choice(styles), rng.choice(styles)
        pick_from = {"word": first, "start": first, "middle": rng.choice(styles), "end": last, "after": last}
    else:
        pick_from = dict.fromkeys(("word", "start", "middle", "end", "after"), style)
    forms = TABLES["name_forms"]
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
        return len({w for s in styles for key in ("all", tone) for w in s["roots"].get(slot, {}).get(key, [])})
    return sum(math.prod(size(slot) for slot in form.split()) for form, _ in TABLES["name_forms"])


def round_millions(n):
    """12,345,678 -> "12 milioni" / "12 million"; from a billion up, billions."""
    key, n = ("billions", n / 1e9) if n >= 1e9 else ("millions", n / 1e6)
    return tr(key, n=number(round(n)) if n >= 10 else f"{n:.1f}".replace(".", "," if LANG == "it" else "."))


def name_examples(names, tone, count=3):
    rng = random.Random(f"wyrmurbigen-examples-{names}-{tone}")
    used = set()
    return [place_name(rng, used, names, tone) for _ in range(count)]


def person_name(rng, gender, used=None):
    """(it, en): first name and a surname, a father's name, a home town or a byname."""
    used = used if used is not None else set()
    for _ in range(50):
        first = rng.choice(TABLES["first_names"][gender])
        style = rng.random()
        if style < 0.3:
            father = rng.choice(TABLES["first_names"]["m"])
            name = (f"{first} di {father}",) * 2
        elif style < 0.6:
            name = (f"{first} {rng.choice(TABLES['families'])}",) * 2
        elif style < 0.8:
            name = (f"{first} da {rng.choice(TABLES['places'])}",) * 2
        else:
            by = rng.choice(TABLES["bynames"])
            name = (f"{first} {by[0]}", f"{first} {by[1]}")
        if name[0] not in used:
            used.add(name[0])
            return name
    return name


class Deck:
    """Draws without repeats until the deck is empty, then reshuffles."""

    def __init__(self, items, rng):
        self.items, self.rng, self.pool = list(items), rng, []

    def draw(self):
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

    def __init__(self, kind, x0, y0, w, h, door, stone, outside=False):
        self.kind, self.x0, self.y0, self.w, self.h = kind, x0, y0, w, h
        self.door, self.stone, self.outside = door, stone, outside
        self.number, self.quarter, self.ruined = 0, 0, False
        self.uid = None

    def cells(self):
        return [(x, y) for y in range(self.y0, self.y0 + self.h) for x in range(self.x0, self.x0 + self.w)]

    def centre(self):
        return self.x0 + (self.w - 1) / 2, self.y0 + (self.h - 1) / 2

    @property
    def id(self):
        return self.kind["id"]


class Plan:

    def __init__(self, W, H, rng):
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

    def ok(self, x, y):
        return 0 <= x < self.W and 0 <= y < self.H

    def is_water(self, x, y):
        return self.ground[y][x] == "water"


def smoothstep(t):
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
    n1 = noise_grid(W, H, rng, max(4.0, R * 0.6))
    n2 = noise_grid(W, H, rng, 3.0)
    plan.n1, plan.n2 = n1, n2
    ground, tex = plan.ground, plan.tex
    plan.water_side = None
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
    elif terrain == "lake":
        angle = rng.uniform(0, 2 * math.pi)
        radius = R * rng.uniform(1.0, 1.5)
        lx, ly = ray(cx, cy, angle, reach + radius * 0.85)
        plan.water_side = (round(math.cos(angle)), round(math.sin(angle)))
        for y in range(H):
            for x in range(W):
                if vdist(x, y, lx, ly) < radius * (0.8 + 0.4 * n1[y][x]):
                    ground[y][x] = "water"
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
    for y in range(H):
        for x in range(W):
            if ground[y][x] == "water":
                continue
            d = vdist(x, y, cx, cy)
            a, b, t = n1[y][x], n2[y][x], tex[y][x]
            if terrain == "swamp":
                if d > reach * 1.15 and b > 0.64:
                    ground[y][x] = "water"
                elif d > reach * 1.05 and a > 0.4 and t < 0.45:
                    ground[y][x] = "reed"
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
                if d > reach * 1.35 and a > 0.56 and t < 0.6:
                    ground[y][x] = "mount"
                elif d > reach * 1.15 and a > 0.44 and t < 0.32:
                    ground[y][x] = "hill"
                elif d > reach * 1.2 and b > 0.7 and t < 0.45:
                    ground[y][x] = "tree"
            else:
                if d > reach * 1.2 and b > 0.8 and t < 0.35:
                    ground[y][x] = "tree"          # copses and hedgerows
    plan.water = any(ground[y][x] == "water" for y in range(H) for x in range(W))


# --- shapes ---
def to_letters(cx, cy, vx, vy):
    return cx + vx * ASPECT, cy + vy


def blob_shape(cx, cy, R, rng, n=24, wobble=0.12, stretch=1.0, angle=0.0):
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
    chosen = []
    for i in range(n):
        want = start + 2 * math.pi * i / n + rng.uniform(-0.25, 0.25)
        best = min(lands, key=lambda a: min(abs(a - want) % (2 * math.pi), (want - a) % (2 * math.pi))
                   + (5 if any(abs(math.remainder(a - c, 2 * math.pi)) < 0.6 for c in chosen) else 0))
        chosen.append(best)
    return chosen


def carve_gate(plan, mask, angle, flank=True):
    """Open a gate through the wall along `angle` from the centre."""
    t = 0.0
    inner = outer = None
    cells = []
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
    vertical = abs(math.sin(angle)) > 0.6
    gate_cells = set()
    for x, y in cells:
        gate_cells.add((x, y))
        if vertical:
            gate_cells.add((x + 1, y))
    for x, y in gate_cells:
        if plan.ok(x, y) and plan.cell[y][x] in FORT:
            plan.cell[y][x] = GATE
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
    noise = plan.n2

    def cost(x, y):
        c = plan.cell[y][x]
        if region is not None and not region(x, y):
            return None
        if not plan.inside[y][x] or c in FORT or c == BLDG or plan.is_water(x, y):
            return None
        base = 0.55 if c in (STREET, SQUARE) else 1.0
        return base * (1 + (2.2 * noise[y][x] if organic else 0))
    return cost


def make_square(plan, rng, hw, hh, kind=SQUARE, irregular=True):
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
        return plan.inside[y][x] and plan.cell[y][x] is None and not plan.is_water(x, y)
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
        path, (x, y) = [far], far
        while dist[y][x] > 0:
            nxt = min(((x + dx, y + dy) for dx, dy in DIRS4 if plan.ok(x + dx, y + dy)),
                      key=lambda c: dist[c[1]][c[0]])
            if dist[nxt[1]][nxt[0]] >= dist[y][x]:
                break
            x, y = nxt
            path.append((x, y))
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
    s = kind.get("stone", "late")
    return s == "always" or (s == "late" and era != "early")


class Fields:
    """The distance fields buildings are placed by."""

    def __init__(self, plan):
        self.plan = plan
        self.cache = {}

    def get(self, name):
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


def place_one(plan, rng, kind, era, fields, region, mode, place, outside=False, gap=(1, 1), size=None,
              keep_clear=None):
    """Find the best spot for one building; None if there is no room."""
    w0, w1 = kind["w"]
    h0, h1 = kind["h"]
    sizes = [size] if size else []
    sizes += [(rng.randint(w0, w1), rng.randint(h0, h1)) for _ in range(2)] + [(w0, h0)]
    stone = is_stone(kind, era)
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
        for x0, y0, door, street in candidates:
            if not rect_ok(plan, x0, y0, w, h, region, gap):
                continue
            if keep_clear and any((x, y) in keep_clear for y in range(y0 - 1, y0 + h + 1)
                                  for x in range(x0 - 1, x0 + w + 1)):
                continue
            mx, my = int(x0 + w / 2), int(y0 + h / 2)
            score = rng.random() * 2
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
    return lambda x, y: plan.inside[y][x] and plan.cell[y][x] is None and not plan.is_water(x, y)


def region_out(plan, near=None):
    def region(x, y):
        if plan.inside[y][x] or plan.cell[y][x] is not None or plan.ground[y][x] not in ("grass", "tree", "hill"):
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
    "hills": (2, 2, 2, 4, 1), "mountains": (1, 1, 5, 1, 2), "forest": (2, 2, 3, 1, 2), "swamp": (1, 1, 5, 0, 3)}
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


def roads_out(plan, rng):
    """From every gate (or across a village) to the edge of the map."""
    def cost(x, y):
        if plan.inside[y][x]:
            return None
        c = plan.cell[y][x]
        if c in FORT or c == BLDG:
            return None
        if c in (ROAD, BRIDGE):
            return 0.5
        g = plan.ground[y][x]
        base = {"grass": 1.0, "tree": 2.5, "hill": 1.7, "mount": 5.0, "reed": 2.0, "water": 7.0}.get(g, 1.0)
        if c in (DITCH, MOAT):
            base = 2.0
        return base * (1 + plan.n2[y][x])
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

        path = route(plan, gate["outer"], goal, cost, target=target)
        if path:
            carve(plan, path, ROAD, over=(None, DITCH, MOAT, ROAD))
            for x, y in path:
                if plan.cell[y][x] in (DITCH, MOAT) or plan.is_water(x, y):
                    plan.cell[y][x] = BRIDGE


def village_roads(plan, rng, n):
    """Roads that cross the village: in from one edge, through the green, out of another."""
    def cost(x, y):
        c = plan.cell[y][x]
        if c == BLDG:
            return None
        if c in (ROAD, STREET, SQUARE, BRIDGE):
            return 0.5
        g = plan.ground[y][x]
        base = {"grass": 1.0, "tree": 2.5, "hill": 1.7, "mount": 5.0, "reed": 2.0, "water": 7.0}.get(g, 1.0)
        return base * (1 + plan.n2[y][x])
    angles = gate_angles(plan, plan.mask, n, rng)
    for a in angles:
        t = 0
        while plan.ok(*map(int, ray(plan.cx, plan.cy, a, t))):
            t += 0.5
        x, y = ray(plan.cx, plan.cy, a, t - 0.5)
        start = (max(0, min(plan.W - 1, int(x))), max(0, min(plan.H - 1, int(y))))
        path = route(plan, start, lambda x, y: (x, y) in plan.square, cost, target=(plan.cx, plan.cy))
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
    for spec in BUILDINGS:
        if spec.get("filler") or not allowed_in(spec["types"], kind):
            continue
        if spec.get("eras") and era not in spec["eras"]:
            continue
        if spec.get("terrains") and terrain not in spec["terrains"]:
            continue
        count = spec.get("count", {})
        fixed = count.get(kind, count.get(building_type(kind)))
        if fixed is not None:
            lo, hi = span(fixed)
            n = max(lo, min(hi, lo + round((hi - lo) * t + rng.uniform(-0.45, 0.45))))
            real = n
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
    if p["purpose"] == "rest" and not any(s.get("rest") in ("lodging", "tavern") for s in out):
        spec = BUILDING["inn" if kind not in ("village", "fortress") else "tavern"]
        out.append(spec)
        wanted[spec["id"]] = (1, 1)
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
    fieldset = Fields(plan)
    placed, missing = [], Counter()
    for spec in specs:
        region_kind, mode, place = where_to(spec, plan, ward)
        if place == "motte":
            continue
        if region_kind == "out":
            region = region_out(plan, near=plan.R * 2.2)
            b = place_one(plan, rng, spec, p["era"], fieldset, region, mode, place, outside=True, gap=(2, 1))
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
    lay = {"walls": None, "towers": False, "shape": "blob", "streets": "organic", "gates": 0, "ring": False,
           "inner_ring": False, "moat": None, "reach": 1.0, "square": (6, 2), "lanes": 5.0, "wobble": 0.14}
    wet = p["terrain"] in ("river", "lake", "coast", "swamp")
    if kind == "village":
        lay.update(streets="village", square=(5, 2), lanes=None, wobble=0.22, gates=2 + (t > 0.5) + (rng.random() < 0.3))
        if era == "early" and rng.random() < 0.4:
            lay.update(walls=PALISADE, moat="dry")
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
    elif kind == "castle":
        lay.update(gates=1, moat="water" if wet or rng.random() < 0.35 else "dry")
        if era == "early":
            lay.update(shape="motte", walls=PALISADE, reach=1.35, moat="water" if wet else "dry")
        elif era == "late":
            lay.update(shape="castle", walls=WALL, towers=True, inner=t > 0.55 or rng.random() < 0.25)
        else:
            lay.update(shape="rocca", walls=WALL, towers=False, reach=1.3, moat="water" if wet or rng.random() < 0.6 else "dry")
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
    finish(plan, p, rng)
    return plan


def shape_points(plan, p, rng, lay):
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
    pts, corners = shape_points(plan, p, rng, lay)
    mask = clean_mask(plan, polygon_mask(plan, pts))
    plan.mask, plan.shape_pts = mask, pts
    set_inside(plan, mask)
    plan.wall_kind = {WALL: "stone", PALISADE: "palisade"}.get(lay["walls"])
    if lay["walls"]:
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
    for a in angles:
        carve_gate(plan, mask, a, flank=lay["towers"])
    if lay["moat"]:
        moat_around(plan, mask, MOAT if lay["moat"] == "water" else DITCH, width=2.4 if shape in ("star", "rocca") else 1.4)
        plan.moat = lay["moat"]
    specs, plan.wanted = building_list(p, rng)
    plan.missing = Counter()
    inner_mask = None
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
    (x0, y0), (x1, y1) = a, b
    n = int(max(abs(x1 - x0), abs(y1 - y0) * 2)) + 1
    out = []
    for k in range(n + 1):
        c = (int(x0 + (x1 - x0) * k / n), int(y0 + (y1 - y0) * k / n))
        if not out or out[-1] != c:
            out.append(c)
    return out


def finish(plan, p, rng):
    """Fields, gardens, wells, the cemetery crosses, quarters, numbers, secrets."""
    ward = p["type"] in ("castle", "fortress")
    if not ward or True:
        if ward:
            roads_out(plan, rng)
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
                    plan.feat[c] = "tree"
    if ward:
        yard = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.cell[y][x] == YARD and
                all(plan.ok(x + dx, y + dy) and plan.cell[y + dy][x + dx] in (YARD, STREET, SQUARE)
                    for dx in (-1, 0, 1) for dy in (-1, 0, 1))]
        if yard:
            plan.feat[rng.choice(yard)] = "well"
    else:
        streets = [(x, y) for y in range(plan.H) for x in range(plan.W) if plan.cell[y][x] == STREET
                   and (x, y) not in plan.main]
        rng.shuffle(streets)
        for c in streets[:max(1, len(plan.buildings) // 25)]:
            plan.feat[c] = "well"
    for y in range(plan.H):
        for x in range(plan.W):
            if plan.cell[y][x] == GARDEN and plan.tex[y][x] < 0.05:
                plan.feat[(x, y)] = "tree"
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
    gender = gender or rng.choice("mf")
    if align is None:
        align = rng.choices((0, 1, 2), weights=(4, 4, 2))[0]
    if cls != "normal" and lv is None:
        lv = 1
    name = person_name(rng, gender, used)
    return {"name": name, "first": name[0].split(" ")[0], "gender": gender, "role": role, "cls": cls, "lv": lv,
            "trait": gendered(rng.choice(TABLES["traits"]), gender),
            "want": gendered(rng.choice(TABLES["wants"]), gender),
            "secret": gendered(rng.choice(TABLES["secrets"]), gender),
            "stats": stat_line(rng, cls, lv, align)}


def npc_line(npc, full=True):
    head = f"{pick(npc['name'])}, {pick(npc['role'])}"
    if not full:
        return head
    return tr("npc_line", h=head, s=pick(npc["stats"]), t=pick(npc["trait"]), w=pick(npc["want"]),
              x=pick(npc["secret"]))


def keeper_npc(rng, used, kind):
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
    pass


def fill_title(rng, kind, npc, s):
    title = rng.choice(kind.get("title") or [kind["name"]])
    adj_it, adj_en = TABLES["family_adj"]
    k = rng.randrange(len(adj_it))
    values = {"sign": rng.choice(TABLES["signs"]), "saint": rng.choice(TABLES["saints"]),
              "family": (rng.choice(TABLES["families"]),) * 2, "family_adj": (adj_it[k], adj_en[k]),
              "guild": rng.choice(TABLES["guilds"]),
              "owner": (npc["first"], npc["first"]) if npc else (place_name(rng, None, s.p.get("names"), s.p.get("tone")),) * 2}
    return fmt(title, **values)


def plural_trades(trades):
    return join_pairs([t for t in trades])


def join_pairs(pairs):
    out = []
    for lang, word in enumerate((" e ", " and ")):
        words = [p[lang] for p in pairs]
        out.append(words[0] if len(words) == 1 else ", ".join(words[:-1]) + word + words[-1])
    return tuple(out)


def make_settlement(p, plan, seed):
    """Everything but the map: names, history, government, people in every
    building, demographics, economy; monsters and treasure come later."""
    rng = random.Random(f"wyrmurbigen-people-{seed}")
    s = Settlement()
    s.p, s.plan, s.seed = p, plan, seed
    used_names, used_places = set(), set()
    s.name = place_name(rng, used_places, p.get("names"), p.get("tone"))
    if rng.random() < 0.35 and not re.search(r"[ -]", s.name):
        ep = rng.choice(TERRAIN[p["terrain"]]["epithet"])
        s.name_pair = (f"{s.name} {ep[0]}", f"{s.name} {ep[1]}")
    else:
        s.name_pair = (s.name, s.name)
    s.title = fmt(TYPE[p["type"]]["title"][p["era"]], n=s.name_pair)
    kind = p["type"]
    trades = [t for t in TABLES["trades"] if allowed_in(t["where"], kind)
              and (not t.get("terrains") or p["terrain"] in t["terrains"])] or TABLES["trades"]
    # gates and quarters
    gates = [g for g in plan.gates if not g.get("inner_ward") and not g.get("road_only")]
    letters = "ABCDEFGHJKLMNP"
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
            g["name"] = fmt(rng.choice(TABLES["gates"]), saint=rng.choice(TABLES["saints"]),
                            place=(rng.choice(TABLES["places"]),) * 2)
        g["dir"] = compass(g["angle"])
    s.gates = gates
    s.quarter_names = []
    angles = plan.quarter_angles
    if angles:
        ordered = sorted(gates, key=lambda g: g["angle"] % (2 * math.pi))
        for k in range(len(angles)):
            g = ordered[k]
            q = rng.choice([q for q in TABLES["quarters"] if "{trade}" not in q[0]])
            s.quarter_names.append(fmt(q, gate=g["name"], saint=rng.choice(TABLES["saints"]),
                                       trade=(rng.choice(trades)["m"][0] + "i", rng.choice(trades)["m"][1] + "s")))
    s.quarter_names = [fix_trade_quarter(q) for q in s.quarter_names]
    # people in the buildings
    s.npcs = []
    residential = [b for b in plan.buildings if b.kind.get("filler")]
    notable = [b for b in plan.buildings if not b.kind.get("filler")]
    for b in notable:
        b.npc = keeper_npc(rng, used_names, b.kind)
        b.title = fill_title(rng, b.kind, b.npc, s)
        b.people = max(0, roll(b.kind.get("household", "1d4"), rng))
        b.text = rng.choice(b.kind["text"]) if b.kind.get("text") else None
        if b.npc:
            s.npcs.append(b.npc)
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
    # government
    rulers = TABLES["rulers"][kind if kind in TABLES["rulers"] else building_type(kind)][p["era"]]
    title = rng.choice(rulers)
    cls = "cleric" if "vescovo" in title[0] else "fighter"
    lv_range = {"village": (1, 3), "town": (2, 4), "city": (4, 6), "bigcity": (5, 8), "castle": (3, 7),
                "fortress": (4, 8)}[kind]
    s.ruler = make_npc(rng, used_names, title, None, cls, rng.randint(*lv_range), align=rng.choice((0, 0, 1, 2)))
    seat = [b for b in notable if b.kind.get("keep")] or \
           [b for b in notable if b.id in ("town_hall", "lords_hall", "manor", "rocca", "palazzo", "command")]
    s.ruler_seat = seat[0] if seat else None
    # factions
    pool = [f for f in TABLES["factions"] if allowed_in(f["where"], kind)]
    rng.shuffle(pool)
    s.factions = []
    for f in pool[:rng.randint(2, 3) if kind != "village" else 2]:
        name = fmt(f["name"], family=(rng.choice(TABLES["families"]),) * 2, guild=rng.choice(TABLES["guilds"]),
                   saint=rng.choice(TABLES["saints"]))
        leader = make_npc(rng, used_names, ("capo", "leader"), None,
                          rng.choice(("normal", "fighter", "thief", "cleric")), rng.randint(1, 4))
        s.factions.append({"name": name, "goal": f["goal"], "leader": leader})
    for a, b in zip(s.factions, s.factions[1:] + s.factions[:1]):
        a["rival"] = b["name"] if len(s.factions) > 1 and rng.random() < 0.6 else None
    # history
    founder = rng.choice([(f"{pick(person_name(rng, 'm', used_names))}",) * 2,
                          fmt(("la famiglia {f}", "the {f} family"), f=(rng.choice(TABLES["families"]),) * 2)])
    founded = TABLES["history"]["founded_ward" if kind in ("castle", "fortress") else "founded"][p["era"]]
    parts = [fmt(rng.choice(founded), n=s.name_pair, founder=founder,
                 saint=rng.choice(TABLES["saints"]))]
    for e in rng.sample(TABLES["history"]["events"], 2):
        parts.append(fmt(e, saint=rng.choice(TABLES["saints"]), family=(rng.choice(TABLES["families"]),) * 2))
    s.history = parts
    s.present = fmt(rng.choice(TABLES["history"]["present_rest"]), n=s.name_pair)
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
    p, plan = s.p, s.plan
    rng = random.Random(f"wyrmurbigen-threat-{s.seed}")
    pool = [x for x in SITUATIONS if x.get("min_danger", 1) <= p["danger"]
            and (not x.get("terrains") or p["terrain"] in x["terrains"])]
    sit = rng.choice(pool)
    s.situation = sit
    lairs = [b for b in plan.buildings if b.kind.get("dungeon") in sit["lairs"] and not b.outside]
    lairs.sort(key=lambda b: (-b.kind.get("priority", 0), b.number))
    s.lair = (lairs[:3] and rng.choice(lairs[:3])) or rng.choice(plan.buildings)
    villain = make_npc(rng, s.used_names, ("capo", "leader"), None,
                       rng.choice(("fighter", "thief")) if sit["id"] not in ("tyrant", "cult") else
                       ("mu" if sit["id"] == "tyrant" else "cleric"), max(1, p["danger"] * 2 - 1), align=2)
    s.villain = villain
    fam2 = rng.choice(TABLES["families"])
    values = dict(n=s.name_pair, person=villain["name"], family=(rng.choice(TABLES["families"]),) * 2,
                  family2=(fam2,) * 2, lair=(f"n. {s.lair.number} ({s.lair.title[0]})", f"no. {s.lair.number} ({s.lair.title[1]})"))
    s.dwellers = fmt(sit["dwellers"], **values)
    s.threat = fmt(sit["text"], **values)
    s.clock = sit["clock"]
    life = sit["life"]
    # abandoned and ruined buildings
    s.abandoned = set()
    if life == "ruin":
        for b in plan.buildings:
            b.ruined = rng.random() < 0.75
            s.abandoned.add(b.uid)
    elif life == "half":
        for b in plan.buildings:
            if rng.random() < 0.35 and b is not s.lair:
                s.abandoned.add(b.uid)
                b.ruined = rng.random() < 0.5


def fits_monster(m, where):
    w = m.get("where", ["*"])
    return "*" in w or where in w


def monster_label(m):
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
    share = {"inhabited": 0.12, "half": 0.22, "ruin": 0.35}[sit["life"]]
    bs = [b for b in plan.buildings]
    busy = max(2, min(len(bs) // 2, round(len(bs) * share)))
    occupants, contents = {}, {}
    homes = [(s.lair, "dwellers", None)]
    others = [b for b in bs if b is not s.lair and b.kind.get("dungeon") in sit["lairs"]]
    rng.shuffle(others)
    for b in others[:max(0, busy // 3 - 1)]:
        homes.append((b, "dwellers", None))
    free = [b for b in bs if b not in [h[0] for h in homes]]
    rng.shuffle(free)
    free.sort(key=lambda b: (b.uid not in s.abandoned, not b.kind.get("filler")))
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
    rows = [(dwellers, tr("wander_dwellers"))]
    rows += [(monster_label(MONSTERS[k]), pick(MONSTERS[k]["text"])) for k in chosen]
    s.wander = rows
    s.occupants = occupants
    s.contents = contents
    s.monster_names = [capitalized(pick(MONSTERS[k]["name"])) for k in chosen]


def in_range(value, rng_span):
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
    coins = sum(n * TREASURE["coin_value"][c] for c, n in hoard["coins"].items())
    return round(coins + sum(hoard["gems"]) + sum(hoard["jewellery"]))


def priced(values):
    gp = pick(TREASURE["coins"]["gp"])
    counts = Counter(values)
    return ", ".join((f"{counts[v]}×" if counts[v] > 1 else "") + f"{number(v)} {gp}" for v in sorted(counts))


def hoard_text(hoard):
    parts = [f"{number(hoard['coins'][c])} {pick(TREASURE['coins'][c])}" for c in TREASURE["coin_value"]
             if hoard["coins"].get(c)]
    for what in ("gems", "jewellery"):
        values = hoard[what]
        if values:
            name = tr(f"treasure_{what}_one" if len(values) == 1 else f"treasure_{what}", n=len(values))
            parts.append(f"{name} ({priced(values)})")
    parts += [pick(m) for m in hoard["magic"]]
    return ", ".join(parts)


def plan_treasure(s):
    """The Old-School Essentials stocking rules, as in WyrmDelve: a building
    with monsters has treasure 3 times in 6 (their treasure type), an
    abandoned one 1 in 6 (the unguarded treasure of a dungeon level as
    dangerous as the place); lived-in houses keep their owners' savings."""
    rng = random.Random(f"wyrmurbigen-treasure-{s.seed}")
    level = DANGER_LEVEL[s.p["danger"]]
    expert = level >= 4
    found = {}
    for b in s.plan.buildings:
        who = s.occupants.get(b.uid)
        if not who and b.uid not in s.abandoned:
            continue
        content = "monster" if who else "empty"
        chance = rng.randint(1, 6)
        where = rng.choice(TREASURE["hiding"]["lair" if who else "loose"])
        if chance > TREASURE["room_chance"][content]:
            continue
        if who:
            letter = (s.situation.get("treasure") or TREASURE.get("dwellers_type", "")) if who[0] == "dwellers" \
                else MONSTERS[who[1]].get("treasure", "")
            table = TREASURE["types"].get(letter or "-")
            if not table:
                continue
            items = table["items"]
        else:
            items = next(t["items"] for t in TREASURE["unguarded"] if in_range(level, t["levels"]))
        hoard = roll_hoard(items, expert, rng)
        text = hoard_text(hoard)
        if text:
            found[b.uid] = {"text": text, "value": hoard_value(hoard), "magic": len(hoard["magic"]),
                            "where": pick(where)}
    s.treasure = found


def treasure_line(t):
    value = tr("treasure_value", v=number(t["value"])) if t["value"] else ""
    return tr("room_treasure", v=value, x=t["text"], w=t["where"])


# --- rumours, events, hooks, retainers ---
def plan_lore(s):
    rng = s.rng_lore
    npcs = [b for b in s.plan.buildings if getattr(b, "npc", None)]
    dungeon_name = fmt(rng.choice(TABLES["dungeons"]), x=(place_name(rng, None, s.p.get("names"), s.p.get("tone")),) * 2)

    def fill(entry):
        b = rng.choice(npcs) if npcs else None
        other = rng.choice(s.plan.buildings) if s.plan.buildings else None
        values = {"npc": (f"{b.npc['name'][0]} ({tr_pair('ref_no')[0]} {b.number})",
                          f"{b.npc['name'][1]} ({tr_pair('ref_no')[1]} {b.number})") if b else ("qualcuno", "someone"),
                  "building": (f"{other.title[0]} ({tr_pair('ref_no')[0]} {other.number})",
                               f"{other.title[1]} ({tr_pair('ref_no')[1]} {other.number})") if other else ("", ""),
                  "dungeon": dungeon_name, "Dungeon": (capitalized(dungeon_name[0]), capitalized(dungeon_name[1])),
                  "place": (rng.choice(TABLES["places"]),) * 2, "family": (rng.choice(TABLES["families"]),) * 2,
                  "saint": rng.choice(TABLES["saints"]),
                  "person": person_name(rng, rng.choice("mf"), s.used_names)}
        if getattr(s, "situation", None):
            values["dwellers"] = (capitalized(s.dwellers[0]), capitalized(s.dwellers[1]))
            values["lair"] = (f"{tr_pair('ref_no')[0]} {s.lair.number}", f"{tr_pair('ref_no')[1]} {s.lair.number}")
            values["monster"] = (getattr(s, "monster_names", ["?"]) or ["?"])[0], \
                (getattr(s, "monster_names", ["?"]) or ["?"])[0]
        if isinstance(entry, tuple):
            return pick(fmt(entry, **values)), True
        return pick(fmt((entry["it"], entry["en"]), **values)), entry.get("true", True)

    general = list(TABLES["rumors"])
    rng.shuffle(general)
    rumours = []
    if getattr(s, "situation", None):
        special = list(TABLES["adventure_rumors"])
        rng.shuffle(special)
        rumours += [fill(r) for r in special[:4]]
        if hasattr(s, "monster_names"):
            pass
    rumours += [fill(r) for r in general[:8 - len(rumours)]]
    rng.shuffle(rumours)
    s.rumours = rumours
    s.events = [fill(e)[0] for e in rng.sample(TABLES["events"], 6)]
    s.hooks = [fill(h)[0] for h in rng.sample(TABLES["hooks"], 4)]
    s.dungeon_name = dungeon_name
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
    return TEXTS[key]



# --- fonts and glyphs ---
FONT_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "fonts")


def font_file(name):
    return os.path.join(FONT_DIR, name)


def open_font(spec, size):
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
    return os.path.basename(spec[0] if isinstance(spec, tuple) else spec)


def font_metrics(spec):
    f = open_font(spec, 200)
    ascent, descent = f.getmetrics()
    return f.getlength("M") / 200, (ascent + descent) / 200


def font_has_glyph(font, ch):
    def fingerprint(c):
        img = Image.new("L", (80, 80), 0)
        ImageDraw.Draw(img).text((10, 10), c, font=font, fill=255)
        return img.tobytes()
    missing = fingerprint("\U0010FFFD")
    return fingerprint(ch) != missing and any(fingerprint(ch))


class Glyphs:
    """G("≈", "~") -> "≈", or "~" with --ascii-only or if the font lacks ≈."""

    def __init__(self, font, ascii_only):
        self.ascii_only = ascii_only
        self.missing = set()
        self._cache = {}
        self.font = font

    def __call__(self, fancy, plain):
        if self.ascii_only:
            return plain
        if fancy not in self._cache:
            self._cache[fancy] = all(c.isascii() or font_has_glyph(self.font, c) for c in fancy)
            if not self._cache[fancy]:
                self.missing.add(fancy)
        return fancy if self._cache[fancy] else plain


class Canvas:
    """Grid of characters, each with a style: n normal, b bold, i white on black."""

    def __init__(self, width, height):
        self.width, self.height = width, height
        self.chars = [[" "] * width for _ in range(height)]
        self.styles = [["n"] * width for _ in range(height)]

    def put(self, x, y, ch, style="n"):
        if 0 <= x < self.width and 0 <= y < self.height:
            self.chars[y][x], self.styles[y][x] = ch, style

    def write(self, x, y, text, style="n"):
        for i, c in enumerate(text):
            self.put(x + i, y, c, style)

    def paste(self, other, ox, oy):
        for y in range(other.height):
            for x in range(other.width):
                if other.chars[y][x] != " " or other.styles[y][x] != "n":
                    self.put(ox + x, oy + y, other.chars[y][x], other.styles[y][x])

    def lines(self):
        return ["".join(row).rstrip() for row in self.chars]


# (fancy, keyboard) for every symbol of the map; the keyboard ones are WyrmHex's
SYMBOLS = {
    "wall": ("▓", "#"), "tower": ("█", "@"), "gate": ("+", "+"), "palisade": ("▒", "%"),
    "ditch": ("░", ":"), "water": ("≈", "~"), "bridge": ("=", "="), "street": (".", "."), "road": ("·", "."),
    "garden": ("τ", "v"), "grave": ("†", "t"), "mound": ("∩", "n"), "rubble": ("∴", "*"),
    "secret": ("$", "$"), "tunnel": ("░", ":"),
    "well": ("○", "o"), "fountain": ("Θ", "O"), "stall": ("π", "h"), "tree": ("♣", "T"),
    "forest1": ("♣", "T"), "forest2": ("♠", "Y"), "hill": ("∩", "n"), "mount": ("▲", "^"),
    "reed1": ("⌠", ","), "reed2": ('"', ";"),
    "plough": ("≡", "_"), "sown": ("τ", "v"), "pasture": ('"', '"'), "orchard": ("♣", "T"),
}
# buildings: with keyboard letters only, NetHack style (stone = and H, timber - and |), so they never
# look like the town walls (#) and towers (@)
DOUBLE = {"h": ("═", "="), "v": ("║", "H"), "tl": ("╔", "="), "tr": ("╗", "="), "bl": ("╚", "="), "br": ("╝", "=")}
SINGLE = {"h": ("─", "-"), "v": ("│", "|"), "tl": ("┌", "-"), "tr": ("┐", "-"), "bl": ("└", "-"), "br": ("┘", "-")}


def ground_char(plan, x, y, G):
    g = plan.ground[y][x]
    t = plan.tex[y][x]
    if g == "water":
        return G(*SYMBOLS["water"])
    if g == "tree":
        return G(*SYMBOLS["forest1" if t < 0.45 else "forest2"]) if t < 0.75 else " "
    if g == "hill":
        return G(*SYMBOLS["hill"])
    if g == "mount":
        return G(*SYMBOLS["mount"])
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


def map_canvas(plan, referee, G, labels=True, secrets=None):
    """The map as letters. referee: building numbers and (unless `secrets` is
    False) the secret posterns and tunnel."""
    secrets = referee if secrets is None else secrets
    W, H = plan.W, plan.H
    c = Canvas(W, H)
    for y in range(H):
        for x in range(W):
            cell = plan.cell[y][x]
            if (x, y) in plan.feat and cell not in (BLDG,) + tuple(FORT):
                c.put(x, y, G(*SYMBOLS[plan.feat[(x, y)]]), "b" if plan.feat[(x, y)] in ("well", "fountain") else "n")
                continue
            if cell is None:
                c.put(x, y, ground_char(plan, x, y, G))
            elif cell in (WALL, TOWER, PALISADE, DITCH, BRIDGE, MOUND):
                c.put(x, y, G(*SYMBOLS[cell]), "b" if cell == BRIDGE else "n")
            elif cell == MOAT:
                c.put(x, y, G(*SYMBOLS["water"]))
            elif cell == GATE:
                c.put(x, y, "+", "b")
            elif cell == PIER:
                c.put(x, y, "=", "b")
            elif cell in (STREET, SQUARE, YARD):
                c.put(x, y, ".")
            elif cell == ROAD:
                c.put(x, y, G(*SYMBOLS["road"]))
            elif cell == GARDEN:
                c.put(x, y, G(*SYMBOLS["garden"]) if plan.tex[y][x] < 0.16 else " ")
            elif cell == GRAVE:
                c.put(x, y, G(*SYMBOLS["grave"]) if x % 2 == 0 else " ")
    for b in plan.buildings:
        draw_building(c, b, G, referee and labels)
    if secrets:
        for x, y in plan.tunnel:
            if plan.bmap[y][x] < 0 and plan.cell[y][x] not in FORT:
                c.put(x, y, G(*SYMBOLS["tunnel"]), "n")
        for x, y in plan.secret:
            c.put(x, y, "$", "b")
    # gate letters on the road just outside, as WyrmDelve's [A] entrances
    for g in plan.gates:
        if g.get("letter") and g.get("outer"):
            x, y = g["outer"]
            dx, dy = round(math.cos(g["angle"]) * 2), round(math.sin(g["angle"]))
            x, y = x + dx, y + dy
            c.write(x - 1, y, f"[{g['letter']}]", "i")
    return c


def draw_building(c, b, G, numbered):
    t = DOUBLE if b.stone else SINGLE
    x0, y0, x1, y1 = b.x0, b.y0, b.x0 + b.w - 1, b.y0 + b.h - 1
    for y in range(y0, y1 + 1):
        for x in range(x0, x1 + 1):
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
            if edge is None:
                ch = " "
                if b.ruined and ((x * 7 + y * 13) % 5 == 0):
                    ch = G(*SYMBOLS["rubble"])
                c.put(x, y, ch)
            elif b.ruined and ((x * 11 + y * 5) % 4 == 0):
                c.put(x, y, G(*SYMBOLS["rubble"]))
            else:
                c.put(x, y, G(*t[edge]))
    if b.door and not b.ruined:
        c.put(b.door[0], b.door[1], "+")
    if numbered:
        label = str(b.number)
        lx = x0 + (b.w - len(label)) // 2
        ly = y0 + b.h // 2
        c.write(lx, ly, label, "b")


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
    secrets = referee if secrets is None else secrets
    used = set()
    for y in range(plan.H):
        for x in range(plan.W):
            used.add(plan.cell[y][x])
            used.add(plan.ground[y][x])
    out = []
    if any(b.stone for b in plan.buildings):
        out.append([(G("╔═╗", "=H="), "n"), (" " + tr("lg_stone"), "n")])
    if any(not b.stone for b in plan.buildings):
        out.append([(G("┌─┐", "-|-"), "n"), (" " + tr("lg_wood"), "n")])
    out.append([("+", "n"), (" " + tr("lg_door"), "n")])
    if referee:
        out.append([("12", "b"), (" " + tr("lg_number"), "n")])
    if any(b.ruined for b in plan.buildings):
        out.append([(G(*SYMBOLS["rubble"]), "n"), (" " + tr("lg_ruin"), "n")])
    for key, label in ((WALL, "lg_wall"), (TOWER, "lg_tower"), (PALISADE, "lg_palisade")):
        if key in used:
            out.append([(G(*SYMBOLS[key]), "n"), (" " + tr(label), "n")])
    if GATE in used:
        out.append([("+", "b"), (" " + tr("lg_gate"), "n")])
    if any(g.get("letter") for g in plan.gates):
        out.append([("[A]", "i"), (" " + tr("lg_gate_tag"), "n")])
    if DITCH in used:
        out.append([(G(*SYMBOLS["ditch"]), "n"), (" " + tr("lg_ditch"), "n")])
    if MOAT in used or "water" in used:
        out.append([(G(*SYMBOLS["water"]), "n"), (" " + tr("lg_water"), "n")])
    if BRIDGE in used or PIER in used:
        out.append([("=", "b"), (" " + tr("lg_bridge"), "n")])
    if MOUND in used:
        out.append([(G(*SYMBOLS["mound"]), "n"), (" " + tr("lg_mound"), "n")])
    out.append([(".", "n"), (" " + tr("lg_street"), "n")])
    if ROAD in used:
        out.append([(G(*SYMBOLS["road"]), "n"), (" " + tr("lg_road"), "n")])
    if GARDEN in used:
        out.append([(G(*SYMBOLS["garden"]), "n"), (" " + tr("lg_garden"), "n")])
    if GRAVE in used:
        out.append([(G(*SYMBOLS["grave"]), "n"), (" " + tr("lg_grave"), "n")])
    feats = set(plan.feat.values())
    for key in ("well", "fountain", "stall"):
        if key in feats:
            out.append([(G(*SYMBOLS[key]), "b" if key != "stall" else "n"), (" " + tr("lg_" + key), "n")])
    fields_used = {g[6:] for g in used if isinstance(g, str) and g.startswith("field:")}
    for key in ("plough", "sown", "pasture", "orchard"):
        if key in fields_used:
            out.append([(G(*SYMBOLS[key]), "n"), (" " + tr("lg_" + key), "n")])
    for key, sym, label in (("tree", "forest1", "lg_forest"), ("hill", "hill", "lg_hill"), ("mount", "mount", "lg_mount"),
                            ("reed", "reed1", "lg_reed")):
        if key in used:
            out.append([(G(*SYMBOLS[sym]), "n"), (" " + tr(label), "n")])
    if secrets and plan.secret:
        out.append([("$", "b"), (" " + tr("lg_secret"), "n")])
    if secrets and plan.tunnel:
        out.append([(G(*SYMBOLS["tunnel"]), "n"), (" " + tr("lg_tunnel"), "n")])
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
    lines, line, used = [], [], 0
    for entry in entries:
        w = sum(len(t) for t, _ in entry)
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
    return sum(len(t) for entry in line for t, _ in entry) + 4 * (len(line) - 1)


INDEX_GAP = 3           # letters between two columns of the building index
INDEX_MAX = 40          # longest entry of the building index


class Layout:
    """Title, subtitle, the map, the legend and the building index (number -
    place, in columns): the page in letters."""

    def __init__(self, panel, legend, title, subtitle, index=(), secrets=(), side=False, motto=None):
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
        notes = [[(tr("ix_secrets"), "b")]] + [[(t, "n")] for t in secrets] if secrets else []
        self.secrets = pack_legend(notes, inner)
        self.title, self.subtitle, self.motto = title, subtitle, motto
        self.cols = inner + 4
        self.top = (4 if title else 3) + (1 if motto else 0)
        self.panel_x = (self.cols - panel.width - block) // 2
        self.rows = (self.top + 1 + max(panel.height, len(self.index_rows) + 2 if self.side else 0) + 1
                     + len(self.legend) + 1 + (2 + len(self.index_rows) + 1 if self.index_rows and not self.side else 0)
                     + len(self.secrets) + (1 if self.secrets else 0))


def compose_page(layout):
    page = Canvas(layout.cols, layout.rows)
    t, s = layout.title, layout.subtitle
    if t:
        page.write((layout.cols - len(t)) // 2, 1, t, "b")
    if layout.motto:
        page.write((layout.cols - len(layout.motto)) // 2, layout.top - 3, layout.motto)
    page.write((layout.cols - len(s)) // 2, layout.top - 2, s)
    page.paste(layout.panel, layout.panel_x, layout.top)
    y = layout.top + max(layout.panel.height, len(layout.index_rows) + 2 if layout.side else 0) + 1
    for line in layout.legend:
        x = (layout.cols - legend_width(line)) // 2
        for n, entry in enumerate(line):
            if n:
                x += 4
            for text, style in entry:
                page.write(x, y, text, style)
                x += len(text)
        y += 1
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
                page.write(x, y0 + 2 + r, f"{n:>{digits}}", "b")
                page.write(x + digits + 1, y0 + 2 + r, text)
        if not layout.side:
            y = y0 + 2 + len(layout.index_rows) + 1
    for line in layout.secrets:
        x = (layout.cols - legend_width(line)) // 2
        for n, entry in enumerate(line):
            if n:
                x += 4
            for text, style in entry:
                page.write(x, y, text, style)
                x += len(text)
        y += 1
    return page


# --- paper ---
def paper_pixels(paper, orientation):
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
    options = {paper: best_fit(layouts, paper, aspect) for paper in PAPERS}
    readable = [p for p in PAPERS if options[p][0] >= GOOD_CHAR_MM]
    return (readable[0] if readable else list(PAPERS)[-1]), options


def verdict(char_mm):
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


def render(canvas, regular, bold, char_w, char_h, size, width, height, ox, oy, progress=None):
    """Rasterise in grayscale: 0 = ink, 255 = paper (colours come later)."""
    img = Image.new("L", (width, height), 255)
    d = ImageDraw.Draw(img)
    thicken = max(1, size // 22)
    real_bold = bold is not None
    probe = bold.font_variant(size=40) if real_bold else None
    bold_can_draw = {}

    def draw_bold(px, py, ch):
        if real_bold:
            if ch not in bold_can_draw:
                bold_can_draw[ch] = ch.isascii() or font_has_glyph(probe, ch)
            if bold_can_draw[ch]:
                d.text((px, py), ch, font=bold, fill=0, anchor="la")
                return
        d.text((px, py), ch, font=regular, fill=0, anchor="la")
        d.text((px + thicken, py), ch, font=regular, fill=0, anchor="la")

    for y in range(canvas.height):
        py = oy + y * char_h
        for x in range(canvas.width):
            ch, style = canvas.chars[y][x], canvas.styles[y][x]
            if ch == " " and style != "i":
                continue
            px = ox + x * char_w
            if style == "i":
                d.rectangle([px, py, px + char_w + 0.5, py + char_h + 0.5], fill=0)
                if ch not in "[] ":
                    d.text((px, py), ch, font=bold or regular, fill=255, anchor="la")
            elif style == "b":
                draw_bold(px, py, ch)
            else:
                d.text((px, py), ch, font=regular, fill=0, anchor="la")
        if progress:
            progress((y + 1) / canvas.height)
    return img


def colorize(img, scheme):
    if scheme == 1:
        return img
    ink, paper = COLOR_SCHEMES[scheme]
    palette = []
    for v in range(256):
        t = v / 255
        palette += [round(ink[k] * (1 - t) + paper[k] * t) for k in range(3)]
    img.putpalette(palette)
    return img


def check_size(img, path):
    if img.size not in VALID_SIZES:
        raise ValueError(tr("err_size", path=path, size=img.size))


def save_png(img, path, settings=None):
    check_size(img, path)
    info = PngInfo()
    if settings:
        info.add_itxt(SETTINGS_KEY, json.dumps(settings, ensure_ascii=False))
    img.save(path, dpi=(DPI, DPI), pnginfo=info)


def pdf_text(text):
    return "<" + ("﻿" + text).encode("utf-16-be").hex().upper() + ">"


class PdfFile:
    """A minimal PDF, one 600 dpi picture per page, Flate-compressed so it stays
    lossless (as in WyrmDelve)."""

    def __init__(self, path, settings=None):
        self.path, self.settings = path, settings
        self.f = open(path, "wb")
        self.f.write(b"%PDF-1.4\n%\xe2\xe3\xcf\xd3\n")
        self.offsets = {}
        self.next_id = 3
        self.pages = []

    def new_id(self):
        self.next_id += 1
        return self.next_id - 1

    def begin(self, oid):
        self.offsets[oid] = self.f.tell()
        self.f.write(f"{oid} 0 obj\n".encode())

    def obj(self, oid, body):
        self.begin(oid)
        self.f.write(body.encode("latin-1") + b"\nendobj\n")

    def add_page(self, img):
        check_size(img, self.path)
        w, h = img.size
        if img.mode == "P":
            palette = bytes(img.getpalette()[:768]).ljust(768, b"\0")
            space = f"[/Indexed /DeviceRGB 255 <{palette.hex().upper()}>]"
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
    live = LiveBar()
    drawing = tr("pb_drawing")
    img = render(canvas, *pixels, progress=lambda done: live.update(0.85 * done, drawing))
    live.update(0.85, tr("pb_saving"))
    return colorize(img, scheme), live


def plain_text(text):
    """Only characters every monospaced font has at the same width."""
    return "".join(c if c.isascii() or c in "·" or ("À" <= c <= "ɏ") else "?" for c in text)


def write_text(path, canvas):
    with open(path, "w", encoding="utf-8") as f:
        f.write(plain_text("\n".join(canvas.lines())) + "\n")



# --- the key ---
def kind_label(b):
    name = pick(b.kind["name"])
    material = tr("stone") if b.stone else tr("wood")
    return f"{name}, {material}"


def building_lines(s, b, people_on, monsters_on, treasure_on):
    lines = []
    if b.kind.get("filler") and getattr(b, "dwellings", 1) > 1 and b.people > 9:
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
    if s.ruler_seat is b:
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


def key_blocks(s, title, units, content):
    story_on, people_on, monsters_on, treasure_on = content
    p, plan = s.p, s.plan
    blocks = [("title", title)]
    purpose = tr("purpose_rest") if p["purpose"] == "rest" else tr("purpose_adventure", d=p["danger"])
    blocks += [("meta", f"{tr('key_seed')}: {s.seed}"),
               ("meta", f"{capitalized(type_name(p['type']))} · {capitalized(pick(ERA[p['era']]['name']))} · "
                        f"{capitalized(pick(TERRAIN[p['terrain']]['name']))}"),
               ("meta", f"{purpose} · {tr('key_pop', n=number(p['pop']))}")]
    if p.get("names"):
        blocks.append(("meta", tr("key_names", s=pick(NAME_STYLE[p["names"]]["name"]),
                                  t=pick(NAME_TONE[p["tone"]]["name"]))))
    n, length, unit, row = scale_bar(plan, units)
    blocks.append(("meta", tr("key_scale", r=f"{row:.1f}".replace(".", "," if LANG == "it" else "."), u=unit)))
    if story_on:
        blocks += [("h", tr("h_history"))] + [("p", " ".join(pick(x) for x in s.history))]
        if p["purpose"] == "rest":
            blocks.append(("p", pick(s.present)))
    if p["purpose"] == "adventure":
        sit = s.situation
        blocks += [("h", tr("h_threat", t=pick(sit["name"]))), ("p", pick(s.threat))]
        blocks.append(("p", tr("threat_villain", v=npc_line(s.villain, full=True))))
        blocks.append(("table", tr("clock_title"), [(k + 1, capitalized(pick(c)) + ".") for k, c in enumerate(s.clock)]))
        if monsters_on:
            blocks.append(("table", tr("key_wander"), [(k + 1, f"{name}: {text}.") for k, (name, text) in enumerate(s.wander)]))
    blocks.append(("h", tr("h_government")))
    seat = f" ({tr('lives_in', n=s.ruler_seat.number)})" if s.ruler_seat else ""
    blocks.append(("p", capitalized(npc_line(s.ruler, full=people_on)) + seat))
    if story_on:
        for f in s.factions:
            rival = tr("faction_rival", r=pick(f["rival"])) if f.get("rival") else ""
            blocks.append(("item", tr("faction", n=capitalized(pick(f["name"])), g=pick(f["goal"]),
                                      l=npc_line(f["leader"], full=False)) + rival))
    blocks += demography_blocks(s)
    if story_on:
        blocks += economy_blocks(s)
    if p["purpose"] == "rest":
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
        blocks.append(("h", tr("h_lore")))
        blocks.append(("table", tr("rumours"), [(k + 1, f"{text} [{tr('true') if ok else tr('false')}]")
                                                for k, (text, ok) in enumerate(s.rumours)]))
        blocks.append(("table", tr("events"), [(k + 1, e) for k, e in enumerate(s.events)]))
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
    blocks.append(("h", tr("h_sources")))
    blocks.append(("note", tr("sources")))
    return blocks


def demography_blocks(s):
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
    plan = s.plan
    out = [("h", tr("h_walls"))]
    if plan.walled:
        out.append(("p", tr("walls_" + (plan.wall_kind or "stone")) + (tr("moat_" + plan.moat) if plan.moat else "")))
    else:
        out.append(("p", tr("walls_none")))
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
        def footer(self):
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
    pdf.add_font("gothic", "", font_file("Sebaldus-Gotisch.ttf"))
    for style, name in (("", "Regular"), ("I", "Italic"), ("B", "Bold"), ("BI", "BoldItalic")):
        pdf.add_font("crimson", style, font_file(f"CrimsonText-{name}.ttf"))
    pdf.add_font("dejavu", "", font_file("DejaVuSans.ttf"))
    pdf.set_fallback_fonts(["dejavu"], exact_match=False)
    pdf.set_creator(f"{PROGRAM} v{VERSION}")
    pdf.set_subject(json.dumps(settings, ensure_ascii=False))
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
        y = pdf.get_y() + 1
        pdf.set_draw_color(120)
        pdf.line(pdf.l_margin + width * 0.3, y, pdf.l_margin + width * 0.7, y)
        pdf.set_draw_color(0)
        pdf.ln(4)

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

# castle by Marcin 'StfoReK' Glinski ("fsc"), from asciiart.eu: his signature stays in the corner
CASTLE = r'''
                                 ____
                              .-"    `-.      ,
                            .'          '.   /j\
                           /              \,/:/#\                /\
                          ;              ,//' '/#\              //#\
                          |             /' :   '/#\            /  /#\
                          :         ,  /' /'    '/#\__..--""""/    /#\__
                           \       /'\'-._:__    '/#\        ;      /#, """---
                            `-.   / ;#\']" ; """--./#J       ':____...!
                               `-/   /#\  J  [;[;[;Y]         |      ;
""""""---....             __.--"/    '/#\ ;   " "  |     !    |   #! |
             ""--.. _.--""     /      ,/#\'-..____.;_,   |    |   '  |
                   "-.        :_....___,/#} "####" | '_.-",   | #['  |
                      '-._      |[;[;[;[;|         |.;'  /;\  |      |
                      ,   `-.   |        :     _   .;'    /;\ |   #" |
                      !      `._:      _  ;   ##' .;'      /;\|  _,  |
                     .#\"""---..._    ';, |      .;{___     /;\  ]#' |__....--
          .--.      ;'/#\         \    ]! |       "| , """--./_J    /
         /  '%;    /  '/#\         \   !' :        |!# #! #! #|    :`.__
        i__..'%] _:_   ;##J         \      :"#...._!   '  "  "|__  |    `--.._
         | .--""" !|""""  |"""----...J     | '##"" `-._       |  """---.._
     ____: |      #|      |         #|     |          "]      ;   ___...-"T,
    /   :  :      !|      |   _______!_    |           |__..--;"""     ,;MM;
   :____| :    .-.#|      |  /\      /#\   |          /'               ''MM;
    |""": |   /   \|   .----+  ;      /#\  :___..--"";                  ,'MM;
   _Y--:  |  ;     ;.-'      ;  \______/#: /         ;                  ''MM;
  /    |  | ;_______;     ____!  |"##"""MM!         ;                    ,'MM;
 !_____|  |  |"#"#"|____.'""##"  |       :         ;                     ''MM
  | """"--!._|     |##""         !       !         :____.....-------"""""" |'
  |          :     |______                        ___!_ "#""#""#"""#"""#"""|
__|          ;     |MM"MM"""""---..._______...--""MM"MM]                   |
  "\-.      :      |#                                  :                   |
    /#'.    |      /##,                                !                   |
   .',/'\   |       #:#,                                ;       .==.       |
  /"\'#"\',.|       ##;#,                               !     ,'||||',     |
        /;/`:       ######,          ____             _ :     M||||||M     |
       ###          /;"\.__"-._   """                   |===..M!!!!!!M_____|
                           `--..`--.._____             _!_
                                          `--...____,="_.'`-.____        fsc
'''


def terminal_width():
    try:
        return os.get_terminal_size(sys.stdout.fileno()).columns
    except (OSError, ValueError):
        return None


def menus_on():
    """Menus need asciimatics and a real terminal: otherwise numbered questions."""
    return Screen is not None and sys.stdin.isatty() and sys.stdout.isatty()


def ask(question, default, kind=int, lowest=None, highest=None):
    """Keep asking until the answer is valid. Enter = default."""
    while True:
        answer = input(f"  {question} [{default}]: ").strip()
        if not answer:
            return default
        try:
            value = kind(answer.replace(".", "").replace(",", "") if kind is int else answer)
        except ValueError:
            print(tr("invalid_value"))
            continue
        if (lowest is not None and value < lowest) or (highest is not None and value > highest):
            print(tr("value_range", lo=lowest, hi=highest))
            continue
        return value


def menu(question, options, default=0, hints=None, ticks=None, header=None, keys=None):
    """WyrmDelve's menu: arrows (or the mouse) move, Enter chooses, a number
    jumps to its option; with `ticks`, Space ticks several. Without a terminal
    or asciimatics: the numbered question of old."""
    question = question.strip()
    hints = hints or [""] * len(options)
    if not menus_on():
        print("\n  " + question)
        for k, (text, hint) in enumerate(zip(options, hints), 1):
            print(f"    {k} = {text}" + (f": {hint}" if hint else ""))
        if ticks is None:
            return ask(tr("choice"), default + 1, int, 1, len(options)) - 1
        print(tr("content_help"))
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

    state = {"at": default, "ticks": list(ticks) if ticks is not None else None, "rows": {}}
    keys = keys or tr("menu_keys_multi" if ticks is not None else "menu_keys")

    def draw(screen):
        screen.clear_buffer(Screen.COLOUR_WHITE, Screen.A_NORMAL, Screen.COLOUR_BLACK)
        lines = header or []
        x = 2
        if not lines:
            screen.print_at(f" {PROGRAM} v{VERSION} ", 2, 1, Screen.COLOUR_BLACK, Screen.A_BOLD, Screen.COLOUR_YELLOW)
            y = 3
        else:
            keep = max(0, min(len(lines), screen.height - len(options) - 7))
            for row, line in enumerate(lines[:keep]):
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

    while True:
        try:
            answer = Screen.wrapper(run)
            break
        except ResizeScreenError:
            continue
    chosen = options[answer] if ticks is None else (", ".join(o for o, on in zip(options, answer) if on)
                                                    or tr("menu_none"))
    print(f"  {question} {chosen}")
    return answer


def ask_language():
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
    art = CASTLE.strip("\n").split("\n")
    title = TITLE_ART.strip("\n").split("\n")
    subtitle = f"v{VERSION}  ·  " + tr("welcome_subtitle")
    width = max(max(len(line) for line in art), max(len(line) for line in title), len(subtitle)) + 2
    columns = terminal_width()
    if columns and columns <= width:
        width = columns - 1
    tw = max(len(line) for line in title)
    return ["═" * width, *[(" " * max(0, (width - tw) // 2) + line)[:width] for line in title],
            "", " " * max(0, (width - len(subtitle)) // 2) + subtitle, "═" * width,
            *[line[:width] for line in art], "═" * width]


def show_welcome():
    screen = welcome_screen()
    print("\n" + "\n".join(line.rstrip() for line in screen) + "\n")
    modes = ("random", "params", "rebuild")
    if menus_on():
        return modes[menu(tr("welcome_q"), [tr("mode_" + m) for m in modes], header=[l.rstrip() for l in screen])]
    return modes[menu(tr("welcome_q"), [tr("mode_" + m) for m in modes])]


def ask_choice(question, items, labels, hints=None):
    """A menu with "at random" first; returns the chosen item or None."""
    k = menu(question, [tr("at_random")] + labels, 0, [""] + (hints or [""] * len(labels)))
    return None if k == 0 else items[k - 1]


def ask_params():
    fixed = {}
    purpose = ask_choice(tr("q_purpose"), list(PURPOSES), [tr("purpose_rest_menu"), tr("purpose_adventure_menu")],
                         [tr("purpose_rest_hint"), tr("purpose_adventure_hint")])
    if purpose:
        fixed["purpose"] = purpose
    kind = ask_choice(tr("q_type"), [t["id"] for t in TYPES], [pick(t["menu"]) for t in TYPES],
                      [pick(t["range"]) + " · " + pick(t["about"]) for t in TYPES])
    if kind:
        fixed["type"] = kind
        lo, hi = TYPE[kind]["pop"]
        default = random_pop(kind, random.Random())
        fixed["pop"] = ask(tr("q_pop", lo=number(lo), hi=number(hi)), default, int, lo, hi)
    era = ask_choice(tr("q_era"), [e["id"] for e in ERAS], [pick(e["menu"]) for e in ERAS],
                     [pick(e["about"]) for e in ERAS])
    if era:
        fixed["era"] = era
    terrain = ask_choice(tr("q_terrain"), [t["id"] for t in TERRAINS], [pick(t["menu"]) for t in TERRAINS])
    if terrain:
        fixed["terrain"] = terrain
    names = ask_choice(tr("q_names"), [n["id"] for n in NAME_STYLES], [capitalized(pick(n["name"])) for n in NAME_STYLES],
                       [", ".join(name_examples(n["id"], t, 1)[0] for t in ("fair", "stately", "grim")) for n in NAME_STYLES])
    if names:
        fixed["names"] = names
    tone = ask_choice(tr("q_tone"), [t["id"] for t in NAME_TONES], [capitalized(pick(t["name"])) for t in NAME_TONES],
                      [pick(t["about"]) + (" · " + ", ".join(name_examples(names, t["id"], 2)) if names else "")
                       for t in NAME_TONES])
    if tone:
        fixed["tone"] = tone
    if fixed.get("purpose", None) == "adventure":
        danger = ask_choice(tr("q_danger"), list(DANGERS), [tr(f"danger_{d}") for d in DANGERS])
        if danger:
            fixed["danger"] = danger
    return fixed


def ask_colors():
    return menu(tr("colors_intro"), [tr("color_name_1"), tr("color_name_2"), tr("color_name_3")], 0) + 1


def ask_name():
    k = menu(tr("name_intro"), [tr("name_random"), tr("name_mine"), tr("name_none")])
    if k == 0:
        return None
    if k == 2:
        return ""
    while True:
        name = input(tr("q_name")).strip()
        if name:
            return name
        print(tr("name_empty"))


CONTENT_KEYS = ("story", "people", "monsters", "treasure")
CONTENT_WORDS = {"storia": 0, "story": 0, "abitanti": 1, "people": 1, "png": 1, "npc": 1, "mostri": 2, "monsters": 2,
                 "tesori": 3, "tesoro": 3, "treasure": 3}


def read_content(text):
    words = [w for w in text.replace("+", ",").replace(" ", ",").lower().split(",") if w]
    if words in (["mappa"], ["map"], ["mappe"], ["maps"]):
        return (False,) * 4
    if words in (["tutto"], ["all"]):
        return (True,) * 4
    if not words or any(w not in CONTENT_WORDS for w in words):
        raise argparse.ArgumentTypeError(tr("err_content", s=text))
    return tuple(any(CONTENT_WORDS[w] == k for w in words) for k in range(4))


def ask_content(adventure):
    keys = CONTENT_KEYS if adventure else CONTENT_KEYS[:2]
    parts = [tr("content_" + k).split(": ", 1) for k in keys]
    ticks = menu(tr("content_intro"), [a.capitalize() for a, _ in parts], hints=[b for _, b in parts],
                 ticks=(True,) * len(keys))
    return tuple(ticks) + (False,) * (4 - len(ticks))


def ask_units():
    default = 1 if LANG == "it" else 0
    return ("imperial", "metric")[menu(tr("units_intro"), [tr("units_imperial"), tr("units_metric")], default)]


def ask_output():
    """png, pdf (maps and PDF file apart) or single (one PDF file with everything)."""
    options = ("png", "pdf", "single")
    return options[menu(tr("output_intro"), [tr("output_" + o) for o in options], 0)]


def ask_settings():
    ask_language()
    mode = show_welcome()
    print(tr("enter_accepts"))
    p = {"title": None, "ascii_only": False, "font": None, "paper": None, "output": OUTPUT_FOLDER, "units": None,
         "files": None}
    if mode == "rebuild":
        while True:
            seed = read_seed(input(tr("ask_seed", example=example_seed())))
            if seed:
                break
            print(tr("seed_invalid", example=example_seed()))
        p.update(seed)
    elif mode == "params":
        p.update(random_params(new_number(), ask_params()))
    else:
        p.update(random_params(new_number()))
    p["colors"] = ask_colors()
    p["ascii_only"] = menu(tr("ascii_intro"), [tr("ascii_no"), tr("ascii_yes")], 0) == 1
    p["title"] = ask_name()
    p["content"] = ask_content(p["purpose"] == "adventure")
    p["units"] = ask_units()
    p["ask_paper"] = sys.stdin.isatty()
    return p


def read_choice(table, label):
    def parse(text):
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
    language_from_options(argv)

    def names(italian, english):
        return (f"--{italian}", f"--{english}") if LANG == "it" else (f"--{english}", f"--{italian}")
    ap = argparse.ArgumentParser(description=tr("h_description"), epilog=tr("h_epilog"))
    ap.add_argument(*names("lingua", "language"), dest="language", default=LANG, metavar="{it,en}", help=tr("h_language"))
    ap.add_argument(*names("tipo", "type"), dest="type", type=read_choice(TYPES, "tipo"), default=None,
                    help=tr("h_type"))
    ap.add_argument(*names("popolazione", "population"), dest="pop", type=int, default=None, help=tr("h_pop"))
    ap.add_argument(*names("epoca", "era"), dest="era", type=read_choice(ERAS, "epoca"), default=None, help=tr("h_era"))
    ap.add_argument(*names("terreno", "terrain"), dest="terrain", type=read_choice(TERRAINS, "terreno"), default=None,
                    help=tr("h_terrain"))
    ap.add_argument(*names("scopo", "purpose"), dest="purpose", default=None, help=tr("h_purpose"))
    ap.add_argument(*names("pericolo", "danger"), dest="danger", type=int, choices=DANGERS, default=None,
                    help=tr("h_danger"))
    ap.add_argument(*names("nomi", "names"), dest="names", type=read_choice(NAME_STYLES, "nomi"), default=None,
                    help=tr("h_names"))
    ap.add_argument(*names("tono", "tone"), dest="tone", type=read_choice(NAME_TONES, "tono"), default=None,
                    help=tr("h_tone"))
    ap.add_argument(*names("seme", "seed"), dest="seed", default=None, help=tr("h_seed"))
    ap.add_argument(*names("colori", "colors"), dest="colors", type=int, choices=(1, 2, 3), default=1, help=tr("h_colors"))
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
                    metavar="{mappa,tutto,storia,abitanti,mostri,tesori}" if LANG == "it"
                    else "{map,all,story,people,monsters,treasure}", help=tr("h_content"))
    ap.add_argument(*names("unita", "units"), dest="units", default=None,
                    choices=("imperiale", "metrica", "imperial", "metric"), help=tr("h_units"))
    ap.add_argument(*names("solo-ascii", "ascii-only"), dest="ascii_only", action="store_true", help=tr("h_ascii"))
    ap.add_argument("--font", default=None, metavar="FILE", help=tr("h_font"))
    ap.add_argument(*names("uscita", "output"), dest="output", default=OUTPUT_FOLDER, help=tr("h_output"))
    ap.add_argument("--version", action="version", version=f"{PROGRAM} {VERSION}")
    a = ap.parse_args(argv)
    p = {"title": a.title, "ascii_only": a.ascii_only, "font": a.font, "paper": a.paper, "output": a.output,
         "colors": a.colors, "files": a.files, "content": a.content or (True,) * 4,
         "units": {"imperiale": "imperial", "metrica": "metric"}.get(a.units, a.units)}
    fixed = {k: v for k, v in (("type", a.type), ("era", a.era), ("terrain", a.terrain), ("pop", a.pop),
                                ("danger", a.danger), ("names", a.names), ("tone", a.tone)) if v is not None}
    if a.purpose:
        purpose = {"riposo": "rest", "rest": "rest", "avventura": "adventure", "adventure": "adventure"}.get(
            a.purpose.strip().lower())
        if not purpose:
            ap.error(tr("err_choice", s=a.purpose, w="scopo"))
        fixed["purpose"] = purpose
    if "danger" in fixed:
        fixed.setdefault("purpose", "adventure")
    if "pop" in fixed and "type" not in fixed:
        fixed["type"] = next((t["id"] for t in TYPES if t["id"] not in ("castle", "fortress")
                              and t["pop"][0] <= fixed["pop"] <= t["pop"][1]), "bigcity")
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
    interactive = len(sys.argv) == 1
    params = ask_settings() if interactive else settings_from_options(sys.argv[1:])
    log = Log(6)
    log.step(tr("step_settings"))
    seed = make_seed(params)
    log.info(tr("info_seed", s=seed))
    p = params
    log.info(tr("info_what", t=type_name(p["type"]), n=number(p["pop"]), e=pick(ERA[p["era"]]["name"]),
                g=pick(TERRAIN[p["terrain"]]["name"])))
    log.info(tr("purpose_rest") if p["purpose"] == "rest" else tr("purpose_adventure", d=p["danger"]))
    if p.get("names"):
        log.info(tr("info_names", s=pick(NAME_STYLE[p["names"]]["name"]), t=pick(NAME_TONE[p["tone"]]["name"]),
                    m=round_millions(name_combinations(p["names"], p["tone"]))))
    else:
        log.info(tr("info_names_old"))
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
    font_spec, bold_spec = find_font(p["font"])
    advance_em, line_em = font_metrics(font_spec)
    aspect = line_em / advance_em

    log.step(tr("step_map"))
    plan = build_plan(p, seed)
    log.info(tr("info_map", w=plan.W, h=plan.H, b=len(plan.buildings), g=len([g for g in plan.gates if g.get("cells")])))
    if plan.missing:
        log.info(tr("info_missing", n=sum(plan.missing.values())))

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
    plan_lore(s)
    title = pick(s.title) if p["title"] is None else p["title"]
    log.info(f"«{title}»" if LANG == "it" else f"“{title}”")

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
    log.step(tr("step_maps", paper=paper, dpi=DPI))
    pl_title = tr("players_title", t=title) if title else tr("players_title_plain")
    pl_layout = page_layout(G, False, pl_title, side)
    pages = [("referee", compose_page(ref_layout), pixels, compose_page(page_layout(plain, True, title, side))),
             ("players", compose_page(pl_layout), pixel_layout(pl_layout, paper, orientation, char_mm, fonts),
              compose_page(page_layout(plain, False, pl_title, side)))]
    images = []
    base = os.path.join(folder, seed)
    for name, canvas, px, text in pages:
        write_text(f"{base}_{name}.txt", text)
        img, live = draw_sheet(canvas, px, p["colors"])
        if files == "png":
            save_png(img, f"{base}_{name}.png", settings)
            live.finish()
            log.info(tr("saved", a=short_path(f"{base}_{name}.png"), b=short_path(f"{base}_{name}.txt")))
        elif files == "pdf":
            doc = PdfFile(f"{base}_{name}.pdf", settings)
            doc.add_page(img)
            doc.close()
            live.finish()
            log.info(tr("saved", a=short_path(f"{base}_{name}.pdf"), b=short_path(f"{base}_{name}.txt")))
        else:
            live.finish()
            images.append((name, img.convert("RGB") if img.mode == "P" else img, paper, orientation))
            log.info(tr("saved_txt", a=short_path(f"{base}_{name}.txt")))
        del img

    log.step(tr("step_key"))
    blocks = key_blocks(s, title, units, content)
    if motto:
        blocks.insert(1, ("motto", motto))     # in the PDF file only: write_key skips it
    write_key(blocks, f"{base}_key.txt")
    log.info(tr("saved_key", a=short_path(f"{base}_key.txt")))
    if not problem:
        pdf_path = f"{base}_key.pdf"
        try:
            write_pdf(blocks, pdf_path, settings, maps=images)
            log.info(tr("saved_pdf_maps" if images else "saved_pdf", a=short_path(pdf_path)))
        except Exception as e:          # never lose the maps and the key over the PDF
            log.error(tr("err_pdf", e=f"{type(e).__name__}: {e}"))
    elif images:
        for name, img, _, _ in images:
            save_png(img, f"{base}_{name}.png", settings)
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

