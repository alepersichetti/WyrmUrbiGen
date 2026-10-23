# Changelog

All notable changes to WyrmUrbiGen. [Italiano](CHANGELOG.it.md) · **English**

The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/), and versions follow [Semantic Versioning](https://semver.org/).

## [1.0.0] - 2026-10-23

The first release.

### Settlements and maps
- Random **villages, towns, cities, big cities, castles and fortresses** for OSR games, drawn only with letters and symbols, as in NetHack, ADOM and Dwarf Fortress. Every building has a number on the map.
- **Population** from *Medieval Demographics Made Easy*: density, dwellings, nobles, clergy, guards, livestock, and how many shops of every trade there are.
- **Three eras** with their own architecture and town planning:
  - Early Middle Ages: palisades, *motte-and-bailey* castles, Roman *castra*;
  - Late Middle Ages: stone walls with towers, communal squares, tower houses, planned new towns;
  - Renaissance: bastions, ideal cities, star forts, citadels.
- **Eight terrains** that change the map: plains, hills, mountains, forest, swamp, coast, river and lake.
  - In the **mountains** the settlement is perched on a spur: cliffs all round but on the one way up, with hairpin bends and stepped lanes.
  - Every terrain has a short description in the menu.
- **Fields** all round in strips and patches (ploughed, sown, meadows, orchards), different for every terrain.
- **Giant mushroom forests**, inspired by Morrowind, on request: asked at the start (as in WyrmHex) or with `--funghi` / `--mushrooms`.
  - The map: mushrooms `⊤°` all round and among the houses.
  - Buildings: most of them are grown inside the stalks. Only there: grown towers, mushroom farms and beetle stables.
  - Their own trades, gods, history events and traits of the place.
  - Without them, seeds and places are as before.
- **Two maps** (referee's and players'), as PNG or PDF at 600 dpi plus a text version, with the list of buildings. Secret posterns, tunnels and the Secrets line are only on the referee's.
- Five **colour schemes**, as in WyrmHex: black on white, white on light blue, white on black, and colour on white or on black.
- **Keyboard-only symbols** on request.
- Paper from A4 to A1, with the readable sizes suggested.
- **Make the same settlement again** in other colours and styles: its seed stays the same.

### The key (TXT and PDF)
- An A4 PDF file with headings in Sebaldus-Gotisch and text in Crimson Text. With the single-PDF option it also holds the two maps.
- **History in layers**: the founding and two to four events, each with its age and the legacy it left (grudge, exile, claim, debt, relic, secret, vow, curse, treasure, betrayal, prophecy, fortune).
- **Government and factions**: two to five factions rooted in that history. Each has its emblem, goal and the reason for it, its means, base, leader, rivals and allies.
- **The NPCs who matter**: personal story, a motive with its why, a secret, ties to the others with building numbers, and a job for the characters.
- **Every building** with its keeper or head of household, their OSR stats, character, want and secret, services and prices.
- **Demographics** and **the economy of the country around** (from *OSR: Land and Investments*): revenue, troubled times, property for sale.
- **Rumours**: a d10 table of true, false and partly true rumours from a generator, with about 2,800 contents.
  - Flavours: the real middle ages, sword and sorcery, the weird and science fantasy.
- **Events**, **hooks**, mercenaries and followers for hire.
- **Walls, gates and secrets.**
- What goes in the key can be chosen: story, people, monsters, treasure, intrigue.

### Places of rest and places of adventure
- **A place of rest** for adventurers: inns, healers, smiths, horses, mercenaries, prices in gold pieces, jobs and hooks.
- **A place of adventure**, either inhabited and threatened or **in ruins**, at a danger from 1 to 4.
  - **Inhabited and threatened**: brigands, a cult, plague, a curse, an orc siege, a night beast, a necromancer lord, something rising from the water, a dragon, a collapsed mine, a feud.
  - **In ruins**: abandoned and full of monsters, with a layered history (founding, height, fall, sack) and traces of it in the buildings.
  - Either way: a clock of what happens if nobody steps in, plus wandering monsters, and monsters and clues in the buildings, from WyrmDelve.
- **Treasure** within the place's means: a lair hoard for the threat, and the unguarded treasure of a dungeon level as dangerous as the place.

### Names
- **Place names** in eleven languages (medieval Italian, Old English, Renaissance English, Scottish Gaelic, Tolkienian, Persian and Arabic, Byzantine Greek, German, French, Danish and Swedish, Russian and Baltic) and a mix of them all, in five tones. They are built from real roots, so the names themselves are made up.
- **People's names** by the thousand: in the language of the places, in another language, or fantasy.
- Every settlement has a dozen great families and a dozen towns nearby, which come back in buildings, factions, history and rumours.
  - Three great families in four mix the roots of the noble houses of Europe and Byzantium.
- **Made-up gods**: a pantheon of five for every settlement, some tied to its terrain.
- Some buildings are named after an event in the place's history or one of its traits, and the key says why.

### Using it
- Menus in **Italian or English**: a random settlement, *I'll choose*, or rebuilt from its **seed**.
- **Command-line options** in both languages for every choice.
- All the tables are in `data/*.json`, so the words can be changed without touching the code.
- A welcome screen with a castle on its rock.
