# Progetto_EIA

## Progetto per l'esame di Elementi di Intelligenza Artificiale

Per questo progetto la scelta è stata di implementare il gioco del Nim

### Descrizione
Il Nim è un gioco combinatorio a due giocatori, a somma zero, a informazione perfetta e deterministico: due giocatori si alternano rimuovendo oggetti da pile, e vince chi prende l'ultimo oggetto. Nonostante le regole elementari, il Nim ammette una soluzione matematica esatta (teorema di Sprague-Grundy) che lo rende un banco di prova ideale per confrontare strategie analitiche e strategie di ricerca generica.

Questo progetto implementa tre agenti con approcci radicalmente diversi e ne misura le prestazioni tramite tornei automatici su diverse configurazioni di pile.

### Struttura del progetto
```text
.
├── Codice/
│   ├── nim.py            # Rappresentazione dello stato di gioco (NimState)
│   ├── agents.py         # Implementazione dei tre agenti
│   ├── experiments.py    # Motore dei tornei e raccolta statistiche
│   ├── main.py           # Entry point: partita interattiva, esperimenti, analisi nim-sum
│   └── .gitignore
├── Documentazione/
│   └── Tesina Progetto Elementi di Intelligenza Artificiale - Vernieri Leonardo.pdf   # Relazione completa del progetto
└── README.md
```
### Requisiti
- Python $\geq$ 3.10
- Nessuna dipendenza esterna (solo libreria standard)

### Installazione
```bash
git clone https://github.com/LeonardoVernieri/Progetto_EIA.git
```

### Utilizzo
```bash
cd Progetto_EIA.git
```
```bash
cd Codice
```
```bash
python main.py
```
