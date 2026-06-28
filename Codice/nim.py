"""
nim.py
------
Logica del gioco del Nim e rappresentazione dello stato di gioco.

Il Nim è un gioco combinatorio a due giocatori e informazione perfetta:
- Si parte con N pile di oggetti (fiammiferi, monete, ecc.)
- A ogni turno, il giocatore attivo sceglie UNA pila e rimuove almeno 1 oggetto (fino a svuotare l'intera pila)
- Vince chi prende l'ultimo oggetto (variante "normale")
"""


class NimState:
    """
    Rappresenta uno stato del gioco del Nim.

    Uno "stato" è una fotografia completa del gioco in un dato momento:
    sapendo lo stato, si conosce tutto ciò che serve per continuare a giocare.

    Attributi
    ---------
    piles : list[int]
        Lista che rappresenta le pile. piles[i] è il numero di oggetti
        nella pila i. Es: [3, 5, 7] → tre pile con 3, 5 e 7 oggetti.
    current_player : int
        0 = giocatore 1 (chi inizia), 1 = giocatore 2 (l'avversario).
    """

    def __init__(self, piles: list[int], current_player: int = 0):
        """
        Costruttore: crea un nuovo stato del gioco.

        Parametri
        ---------
        piles : list[int]
            Configurazione iniziale delle pile.
        current_player : int
            Chi deve muovere in questo stato. Default 0 (primo giocatore).
        """
        # list(piles) crea una COPIA della lista originale.
        # Questo è importante: se usassimo direttamente piles,
        # modifiche future alla lista esterna cambierebbero anche
        # lo stato, causando bug difficili da trovare.
        self.piles = list(piles)

        # Salva quale giocatore deve muovere in questo stato.
        # 0 = giocatore MAX (chi usa Minimax), 1 = giocatore MIN (avversario).
        self.current_player = current_player

    def is_terminal(self) -> bool:
        """
        Controlla se il gioco è terminato.

        Il gioco finisce quando tutte le pile sono vuote (nessun oggetto rimasto).
        In quel momento, il giocatore che dovrebbe muovere non ha mosse disponibili,
        il che significa che l'avversario ha preso l'ultimo oggetto e ha vinto.

        Ritorna
        -------
        True se tutte le pile sono a 0, False altrimenti.
        """
        # all() restituisce True solo se OGNI elemento soddisfa la condizione.
        # "p == 0 for p in self.piles" genera True/False per ogni pila.
        # Es: [0, 0, 0] → True | [0, 2, 0] → False
        return all(p == 0 for p in self.piles)

    def get_winner(self) -> int | None:
        """
        Restituisce l'indice del giocatore vincitore.

        Logica: se lo stato è terminale, significa che il giocatore
        il cui turno sarebbe (current_player) non ha più mosse.
        Quindi è stato l'ALTRO giocatore a prendere l'ultimo oggetto → ha vinto.

        Ritorna
        -------
        int  → 0 o 1, indice del vincitore
        None → il gioco non è ancora finito
        """
        # Se non siamo in uno stato terminale, non c'è ancora un vincitore.
        if not self.is_terminal():
            return None

        # Il vincitore è il giocatore che ha appena mosso, cioè
        # l'OPPOSTO di chi dovrebbe muovere ora.
        # Trucco: 1 - 0 = 1, e 1 - 1 = 0 → inverte sempre tra 0 e 1.
        return 1 - self.current_player

    def get_legal_moves(self) -> list[tuple[int, int]]:
        """
        Genera tutte le mosse legali disponibili nello stato corrente.

        Una mossa è rappresentata come una coppia (indice_pila, quantità):
          - indice_pila : quale pila si sceglie (0-indexed)
          - quantità    : quanti oggetti si rimuovono (almeno 1, al massimo tutti)

        Esempio con piles = [2, 3]:
          Pila 0 ha 2 oggetti → mosse (0,1) e (0,2)
          Pila 1 ha 3 oggetti → mosse (1,1), (1,2), (1,3)
          Totale: [(0,1),(0,2),(1,1),(1,2),(1,3)]

        Ritorna
        -------
        Lista di tuple (indice_pila, quantità).
        """
        moves = []

        # enumerate(self.piles) restituisce coppie (indice, valore).
        # Es: piles=[3,5] → (0,3), (1,5)
        for i, pile in enumerate(self.piles):

            # range(1, pile+1) genera i valori 1, 2, ..., pile.
            # Il +1 è necessario perché range esclude l'estremo superiore.
            # Es: pile=3 → range(1,4) → 1, 2, 3
            for amount in range(1, pile + 1):
                moves.append((i, amount))  # aggiungi la mossa alla lista

        return moves

    def apply_move(self, move: tuple[int, int]) -> "NimState":
        """
        Applica una mossa e restituisce il NUOVO stato risultante.

        Importante: questo metodo NON modifica lo stato corrente (self).
        Crea e restituisce un nuovo oggetto NimState con la mossa applicata.
        Questo approccio "immutabile" è fondamentale per il Minimax:
        l'algoritmo esplora molti rami dell'albero e non deve "disfare" le mosse.

        Parametri
        ---------
        move : (indice_pila, quantità)
            La mossa da applicare.

        Ritorna
        -------
        Un nuovo NimState con la mossa applicata e il turno cambiato.
        """
        # Spacchetta la tupla nelle due variabili.
        # Equivalente a: pile_index = move[0]; amount = move[1]
        pile_index, amount = move

        # Crea una copia della lista delle pile per non modificare quella originale.
        new_piles = list(self.piles)

        # Rimuove gli oggetti dalla pila scelta.
        # Es: new_piles = [3,5,7], pile_index=1, amount=2 → new_piles = [3,3,7]
        new_piles[pile_index] -= amount

        # Crea e restituisce un nuovo stato:
        # - con le pile aggiornate
        # - con il turno passato all'altro giocatore (0→1, 1→0)
        return NimState(new_piles, 1 - self.current_player)

    def nim_sum(self) -> int:
        """
        Calcola la Nim-sum: XOR bit a bit di tutti i valori delle pile.

        Lo XOR (^) confronta i bit in posizione corrispondente:
          0 XOR 0 = 0
          0 XOR 1 = 1
          1 XOR 0 = 1
          1 XOR 1 = 0   ← diverso dall'OR: 1 XOR 1 = 0

        Esempio con [3, 5, 7]:
          3 = 011
          5 = 101
          7 = 111
          -------
          XOR= 001 = 1   → nim_sum = 1

        Proprietà fondamentale (teorema di Sprague-Grundy):
          - nim_sum == 0 → posizione PERDENTE per chi deve muovere (P-position)
          - nim_sum != 0 → posizione VINCENTE per chi deve muovere (N-position)

        Ritorna
        -------
        int: la Nim-sum della configurazione corrente.
        """
        result = 0  # 0 è l'elemento neutro dello XOR: n XOR 0 = n

        for pile in self.piles:
            # ^= è l'operatore XOR con assegnazione.
            # result = result XOR pile, accumulato per ogni pila.
            result ^= pile

        return result

    def __repr__(self) -> str:
        """
        Metodo speciale Python: definisce come l'oggetto viene stampato.
        Viene chiamato automaticamente quando si fa print(state).

        Produce una stringa visiva tipo:
          [Giocatore 1] Pila 1: ●●● (3) | Pila 2: ●●●●● (5)
        """
        # Costruisce la rappresentazione di ogni pila.
        # '●' * p ripete il carattere p volte. Es: '●' * 3 = '●●●'
        # f"Pila {i+1}" usa i+1 perché l'indice interno parte da 0
        # ma per l'utente le pile si contano da 1.
        pile_str = " | ".join(
            f"Pila {i+1}: {'●' * p} ({p})" for i, p in enumerate(self.piles)
        )

        # current_player + 1 converte da 0-indexed a 1-indexed per l'utente.
        return f"[Giocatore {self.current_player + 1}] {pile_str}"
