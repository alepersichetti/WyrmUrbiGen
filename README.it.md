# WyrmUrbiGen

<div align="center">

**Italiano** · [English](README.md)

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

<img src="img_examples/OSR%20LOGO.png" alt="Logo OSR" width="25%"><br>
Compatibile con qualunque gioco di ruolo analogico "OSR". Fratello di [WyrmHex](https://github.com/alepersichetti/WyrmHex) e [WyrmDelve](https://github.com/alepersichetti/WyrmDelve).

</div>

### WyrmUrbiGen v1.0.0

**WyrmUrbiGen** disegna a caso **villaggi, paesi, città, grandi città, castelli e fortezze** per campagne old school (OSR), fatti solo di lettere e simboli come nei roguelike NetHack, ADOM e Dwarf Fortress. Ogni edificio ha il suo **numero** sulla mappa dell'arbitro, e la **chiave** (in `.txt` e in un **file formattato PDF**) racconta tutto dell'insediamento: storia, governo e fazioni, gli abitanti di ogni edificio con le loro statistiche OSR, la demografia, l'economia del contado, le voci e gli eventi.

All'avvio il programma chiede se l'insediamento è:

- un **luogo di riposo** per gli avventurieri: locande, guaritori, fabbri, cavalli, mercenari e seguaci da assoldare, prezzi in monete d'oro, lavori e agganci;
- un **luogo d'avventura**: una minaccia (briganti, un culto, la peste, una maledizione, un assedio di orchi, una bestia notturna, rovine infestate, un signore negromante, qualcosa che sale dall'acqua, un drago, una miniera crollata, una faida), con un orologio di quello che succede se nessuno interviene, **mostri erranti, mostri e indizi negli edifici e tesori** presi dalle tabelle di WyrmDelve (bestiario e tesori di *Old-School Essentials*).

#### Tipi e popolazione

Scegli il tipo, oppure lascia che lo scelga il programma. La popolazione segue *Medieval Demographics Made Easy* di S. John Ross:

| Tipo | Abitanti |
|---|---|
| Villaggio | 20-1.000, di solito 50-300 |
| Paese (borgo) | 1.000-8.000, di solito 2.500 |
| Città | 8.000-12.000 |
| Grande città | 12.000-100.000 |
| Castello | 20-250 tra famiglia, servi e guarnigione |
| Fortezza | 80-1.000 tra guarnigione e civili |

Dopo il tipo puoi scrivere il numero esatto di abitanti (con Invio ne tieni uno casuale). Da quel numero vengono la densità (abitanti per ettaro), le abitazioni, i nobili, il clero, le guardie, il bestiame e quante botteghe di ogni mestiere ci sono (i *support value* dell'articolo: un calzolaio ogni 150 abitanti, una locanda ogni 2.000...). Le botteghe più importanti finiscono sulla mappa; tutte compaiono nella demografia. Nei luoghi grandi ogni riquadro numerato è un gruppo di case o un isolato.

#### Epoche: architettura e urbanistica

| Epoca | Come sono fatti |
|---|---|
| **Alto medioevo** | palizzate e fossati, villaggi sparsi attorno alla sala di legno del signore, castelli *motte and bailey* (terrapieno con torre di legno e recinto), *castra* romani rettangolari con cardo e decumano, città chiuse nel vecchio quadrato romano con le strade storte sopra la griglia antica |
| **Basso medioevo** | mura di pietra con torri, porte con le torri ai lati, piazze comunali con il palazzo del comune, cattedrali e battisteri, torri gentilizie, borghi franchi a griglia, conventi dei frati lungo le mura, castelli con il mastio e a volte un secondo recinto interno |
| **Rinascimento** | fortificazioni alla moderna con bastioni a punta di freccia, città ideali a raggiera o a griglia, fortezze stellate con la piazza d'armi, rocche quadrate con i bastioni agli angoli, palazzi, logge, polveriere, stamperie |

#### Terreni

Pianura, collina, montagna, foresta, palude, costa, fiume e lago. Il terreno cambia la mappa: il mare e il lago tagliano le mura e portano un molo, il fiume fa da fossato e si attraversa con un ponte, in montagna l'abitato si allunga sul crinale, la foresta lascia una radura di campi, la palude circonda un'isola asciutta. Attorno ci sono i **campi** a strisce e appezzamenti (arati, seminati, prati, frutteti), diversi per ogni terreno.

#### Economia del contado

Dalle regole di *OSR: Land and Investments* (Skerples, blog *Coins and Scrolls*): quanto è sviluppato il contado, quanti contadini e villaggi ci sono nell'esagono di 6 miglia attorno (lo stesso di WyrmHex), la rendita netta del signore (dimezzata o divisa per 10 nei tempi difficili, cioè quando c'è una minaccia), e **proprietà in vendita** con costo, rendita e affittuari: fattorie, manieri, locande, botteghe, miniere.

---

## 1. Cosa ti serve

Metti questi file nella **stessa cartella**:

- `wyrmurbigen.py` (il programma)
- la cartella `data` (le parole e le tabelle: edifici, abitanti, insediamenti, demografia, economia; mostri, indizi e tesori vengono da WyrmDelve)
- la cartella `fonts` (i font della mappa e del libro)
- `requirements.txt`

Ti serve **Python 3.8 o più recente** (meglio l'ultima versione).

## 2. Installazione

Come per WyrmHex e WyrmDelve, una volta sola:

**Windows**
```
py -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

**macOS e Linux**
```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Le librerie sono **Pillow** (le immagini), **fpdf2** (il libro PDF) e **asciimatics** (i menu da scorrere con le frecce).

## 3. Creare un insediamento

Con l'ambiente virtuale attivo:

```
python wyrmurbigen.py
```

Compare la schermata di benvenuto con il castello, poi le domande. **Le domande a scelta sono menu**: frecce **↑ ↓**, **Invio** per confermare, oppure il numero dell'opzione. Le domande in cui scrivi hanno una risposta pronta tra parentesi quadre: Invio la accetta.

1. **Lingua**: italiano o inglese.
2. **Cosa vuoi fare?** Un insediamento casuale, **scelgo io**, oppure **rifaccio un insediamento dal suo seme**.
3. Se scegli tu, ogni domanda ha anche la risposta **A caso**:
   - **luogo di riposo o luogo d'avventura**;
   - **tipo** (villaggio, paese, città, grande città, castello, fortezza) e **numero di abitanti**;
   - **epoca** (alto medioevo, basso medioevo, Rinascimento);
   - **terreno** (pianura, collina, montagna, foresta, palude, costa, fiume, lago);
   - per un luogo d'avventura, il **pericolo** da 1 a 4 (per personaggi di livello 1-2, 3-4, 5-7, 8 e oltre).
4. **Colori**: nero su bianco (per stampare), bianco su celeste, bianco su nero.
5. **Simboli**: quelli di WyrmDelve (`▓ █ ≈ ♣ ╔═╗`) oppure **solo i caratteri della tastiera**, come in WyrmHex.
6. **Nome sulla mappa**: quello generato, uno tuo, oppure nessuno.
7. **Cosa vuoi nella chiave**: storia, abitanti e (in un luogo d'avventura) mostri e tesori; Spazio segna e toglie.
8. **Unità**: metri o piedi.
9. **Formato di stampa**: A4, A3, A2 o A1, con quello consigliato già evidenziato.
10. **Che file vuoi**: mappe in **PNG** e libro PDF separati, mappe in **PDF** e libro PDF separati, oppure **un unico PDF** con le due mappe e poi il libro.

## 4. Il seme

Ogni insediamento ha un **seme**, come `C9500-B-R-A2-K7Q2MB`: tipo e abitanti, epoca, terreno, scopo e pericolo, codice.

| Parte | Valori |
|---|---|
| Tipo | `V` villaggio, `B` paese, `C` città, `G` grande città, `K` castello, `F` fortezza, seguito dagli abitanti |
| Epoca | `A` alto medioevo, `B` basso medioevo, `R` Rinascimento |
| Terreno | `P` pianura, `H` collina, `M` montagna, `F` foresta, `S` palude, `C` costa, `R` fiume, `L` lago |
| Scopo | `R0` luogo di riposo, `A1`-`A4` luogo d'avventura con il suo pericolo |

**Lo stesso seme dà sempre lo stesso insediamento**: mappa, abitanti, mostri e tesori. Il seme è anche il nome della cartella dentro `settlements_generated`.

## 5. I file che ottieni

Tutto va in `settlements_generated/<seme>/`:

| File | Cosa contiene |
|---|---|
| `<seme>_referee.png` (o `.pdf`) | la **mappa dell'arbitro**: numeri degli edifici, postierle segrete `$`, galleria segreta `░` |
| `<seme>_players.png` (o `.pdf`) | la **mappa dei giocatori**: la stessa mappa senza numeri e senza segreti |
| `.txt` accanto a ogni mappa | la mappa come testo, solo caratteri della tastiera |
| `<seme>_key.txt` | la **chiave**: storia, minaccia, governo e fazioni, demografia, economia, servizi e mercenari, voci ed eventi, mura e porte, e ogni edificio con il suo abitante |
| `<seme>_book.pdf` | la stessa chiave come **libro A4** (titoli in Sebaldus-Gotisch, testo in Crimson Text); con l'opzione **PDF unico** contiene anche le due mappe |

### Simboli

| Simbolo | Tastiera | Significato |
|---|---|---|
| `╔═╗ ║` | `=H=` | edificio in pietra |
| `┌─┐ │` | `-|-` | edificio in legno o graticcio |
| `+` | `+` | porta (in grassetto: porta della città) |
| `12` | `12` | numero dell'edificio (solo arbitro) |
| `▓` | `#` | mura |
| `█` | `@` | torre o bastione |
| `▒` | `%` | palizzata |
| `[A]` | `[A]` | ingresso dalla strada |
| `░` | `:` | fossato asciutto (sulla mappa dell'arbitro può essere la galleria segreta) |
| `≈` | `~` | acqua: fiume, lago, mare, fossato |
| `=` | `=` | ponte o molo |
| `.` `·` | `.` | strada, piazza, cortile; strada di campagna |
| `τ` | `v` | orti; campo seminato |
| `≡` | `_` | campo arato |
| `"` | `"` | prato e pascolo |
| `♣` `♠` | `T` `Y` | bosco, frutteto |
| `∩` `▲` | `n` `^` | colline, montagne |
| `†` | `t` | cimitero |
| `○` `Θ` `π` | `o` `O` `h` | pozzo, fontana, banco del mercato |
| `∴` | `*` | macerie |
| `$` | `$` | postierla segreta (solo arbitro) |

**Scala.** In fondo alla legenda c'è una scala grafica. Le lettere sono alte il doppio di quanto sono larghe: una riga di caratteri vale il doppio di una colonna, e la chiave dice quanti metri (o piedi) vale una riga.

## 6. Per chi ha fretta: le opzioni

```
python wyrmurbigen.py --tipo citta --epoca basso --terreno fiume --scopo avventura --pericolo 2
python wyrmurbigen.py --popolazione 30000 --epoca rinascimento --terreno costa --pdf-unico
python wyrmurbigen.py --seme C9500-B-R-A2-K7Q2MB --formato A3 --solo-ascii
python wyrmurbigen.py --language en --type castle --purpose rest --png
```

| Opzione | Cosa fa |
|---|---|
| `--lingua` / `--language` | `it` o `en` |
| `--tipo` / `--type` | `villaggio`, `paese`, `citta`, `grande`, `castello`, `fortezza` (o da 1 a 6) |
| `--popolazione` / `--population` | numero di abitanti (se manca il tipo, lo sceglie dal numero) |
| `--epoca` / `--era` | `alto`, `basso`, `rinascimento` (o da 1 a 3) |
| `--terreno` / `--terrain` | `pianura`, `collina`, `montagna`, `foresta`, `palude`, `costa`, `fiume`, `lago` |
| `--scopo` / `--purpose` | `riposo` o `avventura` |
| `--pericolo` / `--danger` | da 1 a 4 (solo luogo d'avventura) |
| `--seme` / `--seed` | rifà l'insediamento di quel seme |
| `--colori` / `--colors` | 1 nero su bianco, 2 bianco su celeste, 3 bianco su nero |
| `--formato` / `--format` | `A4`, `A3`, `A2`, `A1` |
| `--png`, `--pdf`, `--pdf-unico` / `--single-pdf` | mappe PNG e libro, mappe PDF e libro, oppure un unico PDF |
| `--titolo` / `--title`, `--senza-titolo` / `--no-title` | nome sulla mappa |
| `--contenuto` / `--content` | `storia`, `abitanti`, `mostri`, `tesori` separati da virgole; `mappa`; `tutto` |
| `--unita` / `--units` | `metrica` o `imperiale` |
| `--solo-ascii` / `--ascii-only` | solo caratteri della tastiera |
| `--font` | un font monospazio a tua scelta |
| `--uscita` / `--output` | cartella in cui salvare |

Quello che non indichi è scelto a caso. `python wyrmurbigen.py --help` mostra l'elenco completo.

## 7. Cambiare le parole

Le tabelle stanno nella cartella `data`, in file JSON che puoi modificare con un qualsiasi editor (fai prima una copia):

| File | Cosa contiene |
|---|---|
| `settlements.json` | tipi di insediamento, epoche, terreni, nomi di luoghi, santi, insegne, porte, contrade, frasi della storia, minacce, voci, eventi, agganci |
| `buildings.json` | gli edifici: nome, tipi ed epoche in cui compaiono, quanti (`sv`: uno ogni tanti abitanti; oppure `count`), dimensioni, pietra o legno, dove stanno (piazza, strada maestra, porta, mura, fiume, fuori), chi ci vive, servizi e prezzi, descrizioni |
| `people.json` | nomi, famiglie, mestieri, caratteri, desideri, segreti, governanti, fazioni, classi, incantesimi, mercenari |
| `demographics.json` | i numeri di *Medieval Demographics Made Easy* |
| `economy.json` | i numeri di *OSR: Land and Investments* |
| `monsters.json`, `clues.json`, `treasure.json` | da WyrmDelve: bestiario, indizi, tesori di *Old-School Essentials* |

## Galleria

Mappe dell'arbitro ridotte (gli originali sono a 600 dpi). Un esempio di chiave e di libro: [esempio_chiave_citta.txt](img_examples/esempio_chiave_citta.txt), [esempio_libro_citta.pdf](img_examples/esempio_libro_citta.pdf).

**Città, basso medioevo, fiume (avventura)**

<a href="img_examples/thumbs/citta_basso_medioevo_fiume.png"><img src="img_examples/thumbs/citta_basso_medioevo_fiume.png" alt="Città, basso medioevo, fiume (avventura)" width="100%"></a>

**Grande città, Rinascimento, costa**

<a href="img_examples/thumbs/grande_citta_rinascimento_costa.png"><img src="img_examples/thumbs/grande_citta_rinascimento_costa.png" alt="Grande città, Rinascimento, costa" width="100%"></a>

**Paese, basso medioevo, collina**

<a href="img_examples/thumbs/paese_basso_medioevo_collina.png"><img src="img_examples/thumbs/paese_basso_medioevo_collina.png" alt="Paese, basso medioevo, collina" width="100%"></a>

**Villaggio, alto medioevo, foresta**

<a href="img_examples/thumbs/villaggio_alto_medioevo_foresta.png"><img src="img_examples/thumbs/villaggio_alto_medioevo_foresta.png" alt="Villaggio, alto medioevo, foresta" width="100%"></a>

**Castello motte and bailey, palude**

<a href="img_examples/thumbs/castello_motte_palude.png"><img src="img_examples/thumbs/castello_motte_palude.png" alt="Castello motte and bailey, palude" width="100%"></a>

**Castello, basso medioevo, lago**

<a href="img_examples/thumbs/castello_basso_medioevo_lago.png"><img src="img_examples/thumbs/castello_basso_medioevo_lago.png" alt="Castello, basso medioevo, lago" width="100%"></a>

**Fortezza stellata, solo tastiera**

<a href="img_examples/thumbs/fortezza_stellata_solo_ascii.png"><img src="img_examples/thumbs/fortezza_stellata_solo_ascii.png" alt="Fortezza stellata, solo tastiera" width="100%"></a>

## Fonti e licenze

- **Popolazione, densità, mestieri, clero, nobili, guardie, bestiame**: S. John Ross, *Medieval Demographics Made Easy* (Cumberland Games). Sono usati solo i numeri; il testo non è copiato.
- **Contado, rendite, proprietà, tempi difficili**: Skerples, [*OSR: Land and Investments*](https://coinsandscrolls.blogspot.com/2017/09/osr-land-and-investments.html) (*Coins and Scrolls*). Sono usati solo i numeri.
- **Mostri, indizi e tesori**: da [WyrmDelve](https://github.com/alepersichetti/WyrmDelve); le tabelle dei tesori sono adattate dall'*Old-School Essentials System Reference Document* © 2019 Gavin Norman, Open Game Content con [Open Game License 1.0a](LICENSE-OGL.txt).
- **Disegno del castello** nella schermata di benvenuto: Marcin "StfoReK" Glinski (firma `fsc`), da [asciiart.eu](https://www.asciiart.eu/art/692e286c8f3199ee).
- I **font** mantengono le loro licenze (vedi `fonts/README.md`).

WyrmUrbiGen è software libero con licenza [GNU General Public License v3.0](LICENSE).
