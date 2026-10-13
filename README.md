# WyrmUrbiGen

<div align="center">

[Italiano](README.it.md) · **English**

</div>

<table align="center"><tr><td><pre>
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
</pre></td></tr></table>

<div align="center">

<img src="img_examples/OSR%20LOGO.png" alt="OSR logo" width="25%"><br>
Works with any "OSR" tabletop roleplaying game. Sibling of [WyrmHex](https://github.com/alepersichetti/WyrmHex) and [WyrmDelve](https://github.com/alepersichetti/WyrmDelve).

</div>

### WyrmUrbiGen v1.0.0

**WyrmUrbiGen** draws random **villages, towns, cities, big cities, castles and fortresses** for old school (OSR) campaigns, made only of letters and symbols like the roguelikes NetHack, ADOM and Dwarf Fortress. Every building has its **number** on the game master's map, and the **key** (as `.txt` and as a **PDF book** like WyrmDelve's) tells everything about the settlement: history, government and factions, the people of every building with their OSR stats, demographics, the economy of the country around, rumours and events.

At start the program asks whether the settlement is:

- a **place of rest** for adventurers: inns, healers, smiths, horses, mercenaries and followers for hire, prices in gold pieces, jobs and hooks;
- a **place of adventure**: a threat (brigands, a cult, plague, a curse, an orc siege, a night beast, haunted ruins, a necromancer lord, something rising from the water, a dragon, a collapsed mine, a feud), a clock of what happens if nobody steps in, **wandering monsters, monsters and clues in the buildings, and treasure** from WyrmDelve's tables (its bestiary and the *Old-School Essentials* treasure).

#### Types and population

Population follows S. John Ross's *Medieval Demographics Made Easy*:

| Type | People |
|---|---|
| Village | 20-1,000, usually 50-300 |
| Town (borough) | 1,000-8,000, usually 2,500 |
| City | 8,000-12,000 |
| Big city | 12,000-100,000 |
| Castle | 20-250 household, servants and garrison |
| Fortress | 80-1,000 garrison and civilians |

You can type the exact number of people. From it come the density per hectare, the dwellings, nobles, clergy, guards, livestock, and how many shops of every trade there are (the article's support values). The most important ones go on the map; all of them are in the demographics. In big places every numbered box is a group of houses or a block.

#### Eras: architecture and town planning

- **Early Middle Ages**: palisades and ditches, scattered villages around the lord's timber hall, motte-and-bailey castles, rectangular Roman castra with cardo and decumanus, towns inside the old Roman square with crooked streets over the ancient grid.
- **Late Middle Ages**: stone walls with towers, gates flanked by towers, communal squares with the town hall, cathedrals and baptisteries, tower houses, planned new towns on a grid, friaries along the walls, castles with a keep and sometimes an inner ward.
- **Renaissance**: bastioned "Italian trace" walls, radial or grid ideal cities, star forts with a parade ground, square citadels with corner bastions, palaces, loggias, powder magazines, printing shops.

#### Terrain

Plains, hills, mountains, forest, swamp, coast, river and lake: the sea and the lake cut the walls and bring a pier, the river becomes a moat crossed by a bridge, a mountain town stretches along the ridge, a forest leaves a clearing of fields, a swamp surrounds a dry island. Fields lie around in strips and patches.

#### Economy

From Skerples's *OSR: Land and Investments* (*Coins and Scrolls*): how developed the country is, how many peasants and villages live in the surrounding 6-mile hex (WyrmHex's default), the lord's net revenue (halved or divided by 10 in troubled times), and **property for sale** with cost, income and tenants.

## Installing

```
python3 -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Making a settlement

```
python wyrmurbigen.py
```

The welcome screen with the castle comes first, then the questions (menus: arrows, Enter, or the option's number; every question also has **At random**): language; random settlement, **I'll choose**, or **rebuild from a seed**; place of rest or adventure; type and number of people; era; terrain; danger 1-4; colours; symbols (WyrmDelve's, or **keyboard characters only**, like WyrmHex); name; what goes in the key (story, people, monsters, treasure); units; paper (A4-A1, the suggested one highlighted); files: **PNG maps + PDF book**, **PDF maps + PDF book**, or **one single PDF** with both maps and the book.

## The seed

`C9500-B-R-A2-K7Q2MB` = type and people (`V` village, `B` town, `C` city, `G` big city, `K` castle, `F` fortress), era (`A` early, `B` late, `R` Renaissance), terrain (`P` plains, `H` hills, `M` mountains, `F` forest, `S` swamp, `C` coast, `R` river, `L` lake), purpose (`R0` rest, `A1`-`A4` adventure and danger), code. **The same seed always gives the same settlement.**

## Files

In `settlements_generated/<seed>/`: `<seed>_gm` (numbers, secret posterns `$`, secret tunnel `░`) and `<seed>_players` (no numbers, no secrets) as PNG or PDF plus `.txt`; `<seed>_key.txt`; `<seed>_book.pdf` (with the maps inside, with the single-PDF option).

## Options

```
python wyrmurbigen.py --type city --era late --terrain river --purpose adventure --danger 2
python wyrmurbigen.py --population 30000 --era renaissance --terrain coast --single-pdf
python wyrmurbigen.py --seed C9500-B-R-A2-K7Q2MB --format A3 --ascii-only
```

Every option has an Italian and an English name; see `python wyrmurbigen.py --help` and [README.it.md](README.it.md) for the full table, the symbols and the data files.

## Gallery

Game master maps, scaled down (the originals are 600 dpi). A sample key and book (in Italian): [esempio_chiave_citta.txt](img_examples/esempio_chiave_citta.txt), [esempio_libro_citta.pdf](img_examples/esempio_libro_citta.pdf).

**City, Late Middle Ages, river (adventure)**

<a href="img_examples/thumbs/citta_basso_medioevo_fiume.png"><img src="img_examples/thumbs/citta_basso_medioevo_fiume.png" alt="City, Late Middle Ages, river (adventure)" width="100%"></a>

**Big city, Renaissance, coast**

<a href="img_examples/thumbs/grande_citta_rinascimento_costa.png"><img src="img_examples/thumbs/grande_citta_rinascimento_costa.png" alt="Big city, Renaissance, coast" width="100%"></a>

**Town, Late Middle Ages, hills**

<a href="img_examples/thumbs/paese_basso_medioevo_collina.png"><img src="img_examples/thumbs/paese_basso_medioevo_collina.png" alt="Town, Late Middle Ages, hills" width="100%"></a>

**Village, Early Middle Ages, forest**

<a href="img_examples/thumbs/villaggio_alto_medioevo_foresta.png"><img src="img_examples/thumbs/villaggio_alto_medioevo_foresta.png" alt="Village, Early Middle Ages, forest" width="100%"></a>

**Motte-and-bailey castle, swamp**

<a href="img_examples/thumbs/castello_motte_palude.png"><img src="img_examples/thumbs/castello_motte_palude.png" alt="Motte-and-bailey castle, swamp" width="100%"></a>

**Castle, Late Middle Ages, lake**

<a href="img_examples/thumbs/castello_basso_medioevo_lago.png"><img src="img_examples/thumbs/castello_basso_medioevo_lago.png" alt="Castle, Late Middle Ages, lake" width="100%"></a>

**Star fort, keyboard only**

<a href="img_examples/thumbs/fortezza_stellata_solo_ascii.png"><img src="img_examples/thumbs/fortezza_stellata_solo_ascii.png" alt="Star fort, keyboard only" width="100%"></a>

## Sources and licences

- Population, density, trades, clergy, nobles, guards, livestock: S. John Ross, *Medieval Demographics Made Easy* (Cumberland Games). Only the numbers are used.
- Country, revenue, property, troubled times: Skerples, [*OSR: Land and Investments*](https://coinsandscrolls.blogspot.com/2017/09/osr-land-and-investments.html). Only the numbers are used.
- Monsters, clues, treasure: from [WyrmDelve](https://github.com/alepersichetti/WyrmDelve); treasure tables adapted from the *Old-School Essentials System Reference Document* © 2019 Gavin Norman, Open Game Content under the [Open Game License 1.0a](LICENSE-OGL.txt).
- Castle drawing on the welcome screen: Marcin "StfoReK" Glinski (signed `fsc`), from [asciiart.eu](https://www.asciiart.eu/art/692e286c8f3199ee).
- The fonts keep their own licences (see `fonts/README.md`).

WyrmUrbiGen is free software under the [GNU General Public License v3.0](LICENSE).
