"""
agents.py
---------
Implementazione dei tre agenti che giocano a Nim.

Un "agente" è qualsiasi entità in grado di scegliere una mossa
dato uno stato del gioco. Tutti e tre espongono la stessa interfaccia:
    choose_move(state: NimState) -> tuple[int, int]

Questo permette di usarli in modo intercambiabile nel motore di gioco
(pattern chiamato "polimorfismo"): run_game() non sa se sta chiamando
Random, XOR o Minimax — chiama sempre choose_move() e il comportamento
cambia in base all'agente.

Agenti implementati
-------------------
1. RandomAgent     — sceglie una mossa a caso (baseline)
2. XORAgent        — strategia ottima analitica basata sulla Nim-sum
3. MinimaxAgent    — esplora l'albero di gioco con Minimax + Alpha-Beta
"""

import random           # per scelte casuali (RandomAgent e fallback XORAgent)
import math             # per math.inf (infinito), usato nel Minimax
from nim import NimState  # importa la rappresentazione dello stato


# =============================================================================
# 1. AGENTE CASUALE
# =============================================================================

class RandomAgent:
    """
    Agente baseline: seleziona uniformemente a caso una mossa legale.

    Non ha alcuna logica di gioco. Il suo scopo è fornire un punto
    di riferimento inferiore: qualsiasi agente intelligente deve
    batterlo in modo sistematico e significativo.
    """

    def __init__(self, name: str = "Random"):
        """
        Parametri
        ---------
        name : str
            Nome dell'agente, usato nei report dei tornei.
        """
        self.name = name  # salva il nome per identificarlo nei risultati

    def choose_move(self, state: NimState) -> tuple[int, int]:
        """
        Sceglie una mossa a caso tra tutte quelle legali.

        Parametri
        ---------
        state : NimState
            Lo stato corrente del gioco.

        Ritorna
        -------
        Una mossa (indice_pila, quantità) scelta casualmente.
        """
        # Ottieni tutte le mosse legali dallo stato corrente.
        moves = state.get_legal_moves()

        # random.choice() sceglie un elemento a caso da una lista,
        # con probabilità uniforme (ogni mossa ha la stessa probabilità).
        return random.choice(moves)


# =============================================================================
# 2. AGENTE XOR (STRATEGIA OTTIMA ANALITICA)
# =============================================================================

class XORAgent:
    """
    Agente che implementa la strategia matematicamente ottima del Nim,
    basata sulla Nim-sum (XOR delle pile), derivata dal teorema di
    Sprague-Grundy (1935-1939).

    Il teorema afferma che ogni posizione del Nim è classificabile come:
    - P-position (Previous player wins): chi ha appena mosso vince.
      Equivale a nim_sum == 0. Chi deve muovere PERDERÀ con gioco ottimo.
    - N-position (Next player wins): chi deve muovere vince.
      Equivale a nim_sum != 0. Chi deve muovere VINCERÀ con gioco ottimo.

    Strategia vincente
    ------------------
    Da una N-position (nim_sum != 0), esiste sempre almeno una mossa
    che porta l'avversario in P-position (nim_sum = 0).
    Per trovarla: per ogni pila p[i], calcola p[i] XOR nim_sum.
    Se il risultato è minore di p[i], quella è la mossa vincente:
    ridurre p[i] a (p[i] XOR nim_sum) azzera la nim_sum globale.
    """

    def __init__(self, name: str = "XOR"):
        """
        Parametri
        ---------
        name : str
            Nome dell'agente per i report.
        """
        self.name = name

    def choose_move(self, state: NimState) -> tuple[int, int]:
        """
        Seleziona la mossa ottima basandosi sulla Nim-sum.

        Parametri
        ---------
        state : NimState
            Lo stato corrente del gioco.

        Ritorna
        -------
        La mossa vincente se esiste, altrimenti una mossa casuale.
        """
        # Calcola la nim_sum dello stato corrente.
        # Questo è il valore XOR di tutte le pile.
        nim_sum = state.nim_sum()

        if nim_sum == 0:
            # Siamo in P-position: qualsiasi mossa che facciamo
            # porterà la nim_sum a un valore diverso da 0,
            # lasciando l'avversario in N-position (vantaggio suo).
            # Non esiste una mossa "intelligente" → scegliamo a caso.
            return random.choice(state.get_legal_moves())

        # Siamo in N-position: cerchiamo la mossa che azzera la nim_sum.
        # Iteriamo su tutte le pile per trovare quella giusta.
        for i, pile in enumerate(state.piles):

            # Calcola il valore TARGET a cui portare la pila i.
            # Proprietà matematica: se riduciamo pile[i] a (pile[i] XOR nim_sum),
            # la nim_sum dell'intera configurazione diventa 0.
            # Dimostrazione: nim_sum_nuova = (tutti gli altri XOR) XOR target
            #   = (nim_sum XOR pile[i]) XOR (pile[i] XOR nim_sum)
            #   = 0   (perché A XOR A = 0 per ogni A)
            target = pile ^ nim_sum

            if target < pile:
                # target < pile significa che stiamo RIMUOVENDO oggetti
                # (non aggiungendo, il che sarebbe illegale).
                # La quantità da rimuovere è la differenza.
                amount = pile - target

                # Restituisce la mossa vincente: togli `amount` oggetti dalla pila i.
                return (i, amount)

        # Questo punto non dovrebbe mai essere raggiunto se nim_sum != 0,
        # perché esiste sempre almeno una mossa vincente in N-position.
        # È un fallback di sicurezza.
        return random.choice(state.get_legal_moves())


# =============================================================================
# 3. AGENTE MINIMAX CON ALPHA-BETA PRUNING
# =============================================================================

class MinimaxAgent:
    """
    Agente che esplora l'albero di gioco tramite l'algoritmo Minimax
    con Alpha-Beta Pruning opzionale.

    Minimax — idea di base
    ----------------------
    In un gioco a due giocatori a somma zero, un giocatore vince
    esattamente quanto l'altro perde. Possiamo assegnare un valore
    numerico a ogni stato terminale:
      +1 → ha vinto MAX (il "nostro" agente)
      -1 → ha vinto MIN (l'avversario)

    L'algoritmo risale l'albero assegnando valori agli stati intermedi:
      - Nei nodi MAX (turno del nostro agente): si sceglie il valore MASSIMO
        tra i figli (l'agente gioca la mossa migliore per sé).
      - Nei nodi MIN (turno dell'avversario): si sceglie il valore MINIMO
        tra i figli (l'avversario gioca la mossa migliore per sé).

    Alpha-Beta Pruning — ottimizzazione
    ------------------------------------
    Evita di esplorare rami che non possono influenzare la decisione finale.
    Mantiene due valori:
      alpha : il miglior valore che MAX può garantirsi finora (inizia a -∞)
      beta  : il miglior valore che MIN può garantirsi finora (inizia a +∞)

    Se in un nodo MIN il valore scende sotto alpha, MAX non sceglierà
    mai questo ramo (ha già di meglio) → si taglia (potatura alpha).
    Se in un nodo MAX il valore supera beta, MIN non sceglierà
    mai questo ramo (ha già di meglio) → si taglia (potatura beta).

    Risultato: esplora molti meno nodi mantenendo la stessa decisione ottima.
    """

    def __init__(
        self,
        name: str = "Minimax",
        max_player_id: int = 0,
        depth_limit: int | None = None,
        use_alpha_beta: bool = True,
    ):
        """
        Parametri
        ---------
        name : str
            Nome dell'agente per i report.
        max_player_id : int
            Indice del giocatore che questo agente rappresenta come MAX.
            0 = primo giocatore, 1 = secondo giocatore.
        depth_limit : int | None
            Profondità massima di esplorazione dell'albero.
            None = esplorazione completa fino agli stati terminali.
            Utile per configurazioni grandi dove l'albero è enorme.
        use_alpha_beta : bool
            Se True, applica l'Alpha-Beta Pruning (più veloce).
            Se False, esplora tutto l'albero (più lento, per confronto).
        """
        self.name = name
        self.max_player_id = max_player_id    # chi è MAX in questo agente
        self.depth_limit = depth_limit         # limite di profondità (None = illimitato)
        self.use_alpha_beta = use_alpha_beta   # abilita/disabilita la potatura

        # Contatore dei nodi esplorati: viene resettato a ogni mossa
        # e usato negli esperimenti per misurare il lavoro dell'algoritmo.
        self.nodes_explored = 0

    def choose_move(self, state: NimState) -> tuple[int, int]:
        """
        Seleziona la mossa ottima tramite Minimax.

        Questo è il metodo pubblico: itera sulle mosse del livello radice
        e chiama _minimax() su ogni stato figlio, tenendo la mossa
        che produce il valore massimo per MAX.

        Parametri
        ---------
        state : NimState
            Lo stato corrente (radice dell'albero di ricerca).

        Ritorna
        -------
        La mossa con il valore Minimax più alto per MAX.
        """
        # Resetta il contatore prima di ogni nuova decisione.
        self.nodes_explored = 0

        best_move = None           # la mossa migliore trovata finora
        best_value = -math.inf     # il suo valore (inizia al minimo possibile)

        # alpha e beta per la potatura del livello radice.
        alpha = -math.inf   # il meglio che MAX può garantirsi: parte pessimistico
        beta = math.inf     # il meglio che MIN può garantirsi: parte pessimistico

        # Esamina tutte le mosse possibili dal nodo radice.
        for move in state.get_legal_moves():

            # Genera lo stato figlio applicando la mossa.
            next_state = state.apply_move(move)

            # Chiama Minimax sul figlio. depth=1 perché siamo già un livello
            # sotto la radice. is_maximizing dipende da chi muove nel figlio:
            # se il giocatore nel figlio è MAX, allora è un nodo MAX.
            value = self._minimax(
                next_state,
                depth=1,
                alpha=alpha,
                beta=beta,
                is_maximizing=(next_state.current_player == self.max_player_id),
            )

            # Aggiorna la mossa migliore se questo figlio è migliore.
            if value > best_value:
                best_value = value
                best_move = move

            # Aggiorna alpha con il valore trovato.
            # alpha rappresenta il meglio garantito a MAX finora.
            alpha = max(alpha, best_value)

        return best_move

    def _minimax(
        self,
        state: NimState,
        depth: int,
        alpha: float,
        beta: float,
        is_maximizing: bool,
    ) -> float:
        """
        Funzione ricorsiva Minimax con Alpha-Beta Pruning.

        Esplora l'albero di gioco in profondità e risale assegnando
        valori agli stati in base al principio minimax.

        Parametri
        ---------
        state : NimState
            Lo stato corrente nell'albero di ricerca.
        depth : int
            Profondità corrente nell'albero (radice = 0).
        alpha : float
            Miglior valore garantito a MAX nel percorso corrente.
        beta : float
            Miglior valore garantito a MIN nel percorso corrente.
        is_maximizing : bool
            True = nodo MAX (turno del nostro agente).
            False = nodo MIN (turno dell'avversario).

        Ritorna
        -------
        float: valore Minimax dello stato dal punto di vista di MAX.
          +1.0 → MAX vince con gioco ottimo da questo stato
          -1.0 → MIN vince con gioco ottimo da questo stato
          ±0.1 → stima euristica (solo se depth_limit è attivo)
        """
        # Incrementa il contatore ogni volta che visitiamo un nodo.
        # Questo misura quanti stati l'algoritmo ha esaminato.
        self.nodes_explored += 1

        # -----------------------------------------------------------------
        # CASO BASE 1: stato terminale
        # Il gioco è finito → possiamo assegnare un valore certo.
        # -----------------------------------------------------------------
        if state.is_terminal():
            winner = state.get_winner()
            if winner == self.max_player_id:
                return 1.0   # MAX ha vinto → valore massimo
            else:
                return -1.0  # MIN ha vinto → valore minimo

        # -----------------------------------------------------------------
        # CASO BASE 2: limite di profondità raggiunto
        # Non esploriamo oltre → stimiamo il valore con un'euristica.
        # -----------------------------------------------------------------
        if self.depth_limit is not None and depth >= self.depth_limit:
            # Usiamo la nim_sum come euristica: nim_sum != 0 significa
            # che chi deve muovere è in vantaggio (N-position).
            nim_sum = state.nim_sum()

            # ±0.1 (invece di ±1.0) segnala che è una STIMA, non un risultato certo.
            # Questo aiuta Minimax a preferire vittorie certe a vittorie stimate.
            if state.current_player == self.max_player_id:
                # MAX deve muovere: nim_sum != 0 è vantaggio per MAX
                return 0.1 if nim_sum != 0 else -0.1
            else:
                # MIN deve muovere: nim_sum != 0 è vantaggio per MIN (svantaggio MAX)
                return -0.1 if nim_sum != 0 else 0.1

        # -----------------------------------------------------------------
        # CASO RICORSIVO — NODO MAX
        # Il giocatore MAX sceglie la mossa che MASSIMIZZA il valore.
        # -----------------------------------------------------------------
        if is_maximizing:
            value = -math.inf  # inizia al minimo: qualsiasi figlio sarà migliore

            for move in state.get_legal_moves():
                # Genera lo stato figlio.
                child = state.apply_move(move)

                # Chiamata ricorsiva sul figlio.
                # is_maximizing del figlio dipende da chi muove in quel stato.
                child_value = self._minimax(
                    child,
                    depth + 1,    # scendiamo di un livello
                    alpha,
                    beta,
                    is_maximizing=(child.current_player == self.max_player_id),
                )

                # Aggiorna il valore massimo trovato finora.
                value = max(value, child_value)

                if self.use_alpha_beta:
                    # Aggiorna alpha: MAX può garantirsi almeno `value`.
                    alpha = max(alpha, value)

                    # POTATURA BETA: se value >= beta, MIN non sceglierà
                    # mai questo nodo (ha già trovato qualcosa di meglio per sé
                    # in un ramo precedente). Inutile esplorare altri figli.
                    if beta <= alpha:
                        break  # esce dal ciclo: pota il ramo

            return value

        # -----------------------------------------------------------------
        # CASO RICORSIVO — NODO MIN
        # Il giocatore MIN sceglie la mossa che MINIMIZZA il valore.
        # Speculare al nodo MAX.
        # -----------------------------------------------------------------
        else:
            value = math.inf   # inizia al massimo: qualsiasi figlio sarà migliore

            for move in state.get_legal_moves():
                child = state.apply_move(move)

                child_value = self._minimax(
                    child,
                    depth + 1,
                    alpha,
                    beta,
                    is_maximizing=(child.current_player == self.max_player_id),
                )

                # Aggiorna il valore minimo trovato finora.
                value = min(value, child_value)

                if self.use_alpha_beta:
                    # Aggiorna beta: MIN può garantirsi al massimo `value`.
                    beta = min(beta, value)

                    # POTATURA ALPHA: se beta <= alpha, MAX non sceglierà
                    # mai questo nodo (ha già trovato qualcosa di meglio per sé).
                    if beta <= alpha:
                        break  # esce dal ciclo: pota il ramo

            return value
