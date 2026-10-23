# Registro delle modifiche

Le modifiche di WyrmUrbiGen che contano. **Italiano** · [English](CHANGELOG.md)

Il formato segue [Keep a Changelog](https://keepachangelog.com/it-IT/1.1.0/), e le versioni seguono il [Versionamento Semantico](https://semver.org/lang/it/).

## [1.0.0] - 2026-10-23

La prima versione.

### Insediamenti e mappe
- **Villaggi, paesi, città, grandi città, castelli e fortezze** a caso per giochi OSR, disegnati solo con lettere e simboli, come in NetHack, ADOM e Dwarf Fortress. Ogni edificio ha il suo numero sulla mappa.
- **Popolazione** da *Medieval Demographics Made Easy*: densità, abitazioni, nobili, clero, guardie, bestiame, e quante botteghe ci sono di ogni mestiere.
- **Tre epoche**, ognuna con la sua architettura e urbanistica:
  - alto medioevo: palizzate, castelli *motte-and-bailey*, *castra* romani;
  - basso medioevo: mura di pietra con torri, piazze comunali, case-torri, borghi nuovi;
  - Rinascimento: bastioni, città ideali, fortezze a stella, cittadelle.
- **Otto terreni** che cambiano la mappa: pianura, collina, montagna, foresta, palude, costa, fiume e lago.
  - In **montagna** l'insediamento è arroccato su uno sperone: dirupi tutt'intorno tranne dalla parte dell'unica salita, con tornanti e vie a gradinate.
  - Ogni terreno ha una breve descrizione nel menu.
- **Campi** tutto intorno a strisce e appezzamenti (arati, seminati, prati, frutteti), diversi per ogni terreno.
- **Foreste di funghi giganti**, ispirate a Morrowind, su richiesta: si chiedono all'avvio (come in WyrmHex) oppure con `--funghi` / `--mushrooms`.
  - La mappa: funghi `⊤°` tutto intorno e tra le case.
  - Gli edifici: per lo più cresciuti dentro i gambi. Solo lì: torri cresciute, colture di funghi e stalle dei coleotteri.
  - Mestieri, dei, eventi della storia e peculiarità del luogo tutti loro.
  - Senza, semi e luoghi restano quelli di prima.
- **Due mappe** (dell'arbitro e dei giocatori), in PNG o PDF a 600 dpi più una versione di testo, con l'elenco degli edifici. Postierle segrete, gallerie e la riga dei Segreti stanno solo in quella dell'arbitro.
- Cinque **schemi di colore**, come in WyrmHex: nero su bianco, bianco su celeste, bianco su nero, e a colori su bianco o su nero.
- **Solo i caratteri della tastiera**, se li chiedi.
- Formati dall'A4 all'A1, con quelli leggibili suggeriti.
- **Rifare lo stesso insediamento** con altri colori e stili: il seme resta lo stesso.

### La chiave (TXT e PDF)
- Un file PDF in A4 con i titoli in Sebaldus-Gotisch e il testo in Crimson Text. Con l'opzione PDF unico contiene anche le due mappe.
- **Storia a strati**: la fondazione e da due a quattro eventi, ognuno con la sua epoca e l'eredità che ha lasciato (rancore, esilio, pretesa, debito, reliquia, segreto, voto, maledizione, tesoro, tradimento, profezia, fortuna).
- **Governo e fazioni**: da due a cinque fazioni con le radici in quella storia. Ognuna ha il suo stemma, lo scopo e il perché, i mezzi, la sede, chi la guida, rivali e alleati.
- **I PNG che contano**: storia personale, una motivazione col suo perché, un segreto, i legami con gli altri (con il numero dell'edificio) e un lavoro per i personaggi.
- **Ogni edificio** con chi lo gestisce o il capofamiglia: statistiche OSR, carattere, desiderio e segreto, servizi e prezzi.
- **Demografia** ed **economia del contado** (da *OSR: Land and Investments*): rendite, tempi difficili, proprietà in vendita.
- **Voci**: una tabella da d10 di voci vere, false e vere solo in parte, fatta da un generatore con circa 2.800 contenuti.
  - Toni: medioevo vero, sword & sorcery, weird e science fantasy.
- **Eventi**, **agganci**, mercenari e seguaci da assoldare.
- **Mura, porte e segreti.**
- Si sceglie cosa mettere nella chiave: storia, abitanti, mostri, tesori, intrighi.

### Luoghi di riposo e luoghi d'avventura
- **Un luogo di riposo** per gli avventurieri: locande, guaritori, fabbri, cavalli, mercenari, prezzi in monete d'oro, lavori e agganci.
- **Un luogo d'avventura**, abitato e minacciato oppure **in rovina**, con pericolo da 1 a 4.
  - **Abitato e minacciato**: briganti, un culto, la peste, una maledizione, un assedio di orchi, una bestia notturna, un signore negromante, qualcosa che sale dall'acqua, un drago, una miniera crollata, una faida.
  - **In rovina**: abbandonato e pieno di mostri, con una storia a strati (fondazione, splendore, caduta, saccheggio) e le sue tracce negli edifici.
  - In tutti e due i casi: un orologio di quello che succede se nessuno interviene, poi mostri erranti, e mostri e indizi negli edifici, da WyrmDelve.
- **Tesori** alla portata del luogo: un tesoro di tana per la minaccia, e il tesoro incustodito di un livello di dungeon pericoloso quanto il luogo.

### Nomi
- **Nomi dei luoghi** in undici lingue (italiano medievale, inglese antico, inglese rinascimentale, gaelico scozzese, tolkieniano, persiano e arabeggiante, greco bizantino, tedesco, francese, danese e svedese, russo e baltico) e una mescolanza di tutte, in cinque toni. Sono costruiti da radici vere, quindi i nomi sono inventati.
- **Nomi delle persone** a migliaia: nella lingua dei luoghi, in un'altra lingua oppure fantasy.
- Ogni insediamento ha una dozzina di grandi famiglie e una dozzina di città vicine, che tornano negli edifici, nelle fazioni, nella storia e nelle voci.
  - Tre grandi famiglie su quattro mescolano le radici delle casate nobili d'Europa e di Bisanzio.
- **Dei inventati**: un pantheon di cinque per ogni insediamento, alcuni legati al suo terreno.
- Alcuni edifici prendono il nome da un evento della storia del luogo o da una sua peculiarità, e la chiave dice perché.

### Come si usa
- Menu in **italiano o inglese**: un insediamento casuale, *scelgo io*, oppure rifatto dal suo **seme**.
- **Opzioni da riga di comando** in tutte e due le lingue per ogni scelta.
- Tutte le tabelle stanno in `data/*.json`, quindi le parole si cambiano senza toccare il codice.
- Una schermata di benvenuto con un castello sulla roccia.
