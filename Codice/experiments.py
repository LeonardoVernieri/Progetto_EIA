"""
experiments.py
--------------
Motore di torneo e raccolta dei risultati sperimentali.

Questo modulo si occupa di:
- Eseguire singole partite tra due agenti (run_game)
- Eseguire tornei statistici di N partite (run_tournament)
- Confrontare tutte le coppie di agenti su più configurazioni (compare_agents)
- Analizzare e visualizzare la Nim-sum di una configurazione (analyze_nim_sum)

La separazione tra logica di gioco (nim.py, agents.py) e logica
di misurazione (questo file) segue il principio di responsabilità
singola: ogni modulo ha un compito ben definito.
"""

import time                          # per misurare il tempo di esecuzione
from collections import defaultdict  # dizionario con valore di default automatico
from nim import NimState
from agents import RandomAgent, XORAgent, MinimaxAgent


# =============================================================================
# SINGOLA PARTITA
# =============================================================================

def run_game(
    agent1,
    agent2,
    initial_piles: list[int],
    verbose: bool = False,
) -> dict:
    """
    Esegue una singola partita tra due agenti e raccoglie le statistiche.

    agent1 gioca come giocatore 0 (primo a muovere).
    agent2 gioca come giocatore 1 (secondo a muovere).

    Parametri
    ---------
    agent1        : agente con metodo choose_move(state)
    agent2        : agente con metodo choose_move(state)
    initial_piles : configurazione iniziale delle pile, es. [3, 5, 7]
    verbose       : se True, stampa ogni stato e ogni mossa durante la partita

    Ritorna
    -------
    dict con i seguenti campi:
      winner       : int (0 o 1) — indice del giocatore vincitore
      winner_name  : str — nome dell'agente vincitore
      n_moves      : int — numero totale di mosse giocate
      duration_ms  : float — durata della partita in millisecondi
      nodes_agent1 : int — nodi esplorati da agent1 (0 se non è Minimax)
      nodes_agent2 : int — nodi esplorati da agent2 (0 se non è Minimax)
    """
    # Mette gli agenti in una lista indicizzata.
    # Così agents[state.current_player] seleziona automaticamente
    # l'agente giusto in base a chi deve muovere.
    agents = [agent1, agent2]

    # Crea lo stato iniziale: pile configurate, giocatore 0 inizia.
    state = NimState(initial_piles, current_player=0)

    # Contatore delle mosse totali della partita.
    n_moves = 0

    # Resetta i contatori di nodi per gli agenti Minimax.
    # hasattr() controlla se l'oggetto ha quell'attributo:
    # solo MinimaxAgent ha 'nodes_explored', RandomAgent e XORAgent no.
    # Questo evita un AttributeError se l'agente non è Minimax.
    for ag in agents:
        if hasattr(ag, 'nodes_explored'):
            ag.nodes_explored = 0

    # Avvia il timer PRIMA del loop di gioco.
    # perf_counter() è più preciso di time.time() per intervalli brevi.
    start = time.perf_counter()

    # Loop principale della partita: continua finché non c'è un vincitore.
    while not state.is_terminal():

        # Seleziona l'agente corretto in base a chi deve muovere.
        current_agent = agents[state.current_player]

        if verbose:
            # Stampa lo stato corrente e chi deve muovere.
            print(f"\n{state}")
            print(f"  → Turno di {current_agent.name}")

        # L'agente sceglie la sua mossa dato lo stato corrente.
        move = current_agent.choose_move(state)
        pile_idx, amount = move  # spacchetta per il messaggio verbose

        if verbose:
            print(f"  → Rimuove {amount} oggetti dalla pila {pile_idx + 1}")

        # Applica la mossa: state viene SOSTITUITO con il nuovo stato.
        # Non si modifica lo stato esistente, se ne crea uno nuovo.
        state = state.apply_move(move)
        n_moves += 1

    # Ferma il timer e converte da secondi a millisecondi (* 1000).
    duration_ms = (time.perf_counter() - start) * 1000

    # Recupera il vincitore dallo stato terminale.
    winner_id = state.get_winner()

    if verbose:
        print(f"\n{'='*50}")
        print(f"  FINE PARTITA — Vince: {agents[winner_id].name}")
        print(f"  Mosse totali: {n_moves} | Durata: {duration_ms:.2f} ms")
        print(f"{'='*50}")

    # getattr(obj, attr, default) legge l'attributo se esiste,
    # altrimenti restituisce il valore di default (0).
    # Equivalente sicuro a: ag.nodes_explored if hasattr(ag, ...) else 0
    return {
        "winner": winner_id,
        "winner_name": agents[winner_id].name,
        "n_moves": n_moves,
        "duration_ms": duration_ms,
        "nodes_agent1": getattr(agent1, 'nodes_explored', 0),
        "nodes_agent2": getattr(agent2, 'nodes_explored', 0),
    }


# =============================================================================
# TORNEO (N PARTITE)
# =============================================================================

def run_tournament(
    agent1,
    agent2,
    initial_piles: list[int],
    n_games: int = 100,
    alternate_start: bool = True,
) -> dict:
    """
    Esegue un torneo di n_games partite tra i due agenti e aggrega le statistiche.

    Perché alternare chi inizia?
    ----------------------------
    Nel Nim, chi inizia ha un vantaggio strutturale quando la posizione
    è una N-position (nim_sum != 0): il primo giocatore può giocare
    la mossa vincente immediatamente. Se non si alternasse, i risultati
    dipenderebbero dall'ordine di gioco invece che dalla qualità dell'agente.
    Alternando, ogni agente inizia esattamente n_games/2 volte.

    Parametri
    ---------
    agent1, agent2  : agenti con metodo choose_move(state)
    initial_piles   : configurazione iniziale delle pile
    n_games         : numero totale di partite da giocare
    alternate_start : se True, il primo giocatore si alterna ogni partita

    Ritorna
    -------
    dict con statistiche aggregate del torneo.
    """
    # defaultdict(int) crea automaticamente wins[0]=0 e wins[1]=0
    # senza bisogno di inizializzarli esplicitamente.
    wins = defaultdict(int)

    # Liste per accumulare le statistiche di ogni partita.
    total_moves = []    # numero di mosse per partita
    total_times = []    # durata in ms per partita
    total_nodes1 = []   # nodi esplorati da agent1 per partita
    total_nodes2 = []   # nodi esplorati da agent2 per partita

    for i in range(n_games):

        if alternate_start and i % 2 == 1:
            # Partite con indice dispari (1, 3, 5, ...): agent2 inizia.
            # i % 2 è il resto della divisione per 2: 0 se pari, 1 se dispari.
            result = run_game(agent2, agent1, initial_piles)

            # Il risultato di run_game usa 0/1 relativi all'ordine passato
            # (agent2 era posizione 0). Dobbiamo riconvertire all'ordine
            # originale: se ha vinto il giocatore 0 in run_game (= agent2),
            # nel torneo ha vinto agent2 (indice 1). Quindi invertiamo.
            actual_winner = 1 - result["winner"]
        else:
            # Partite con indice pari (0, 2, 4, ...): agent1 inizia normalmente.
            result = run_game(agent1, agent2, initial_piles)
            actual_winner = result["winner"]  # 0 = agent1, 1 = agent2

        # Incrementa il contatore delle vittorie per il vincitore.
        wins[actual_winner] += 1

        # Accumula le statistiche della partita nelle rispettive liste.
        total_moves.append(result["n_moves"])
        total_times.append(result["duration_ms"])
        total_nodes1.append(result["nodes_agent1"])
        total_nodes2.append(result["nodes_agent2"])

    # Calcola e restituisce le statistiche aggregate.
    return {
        "agent1_name": agent1.name,
        "agent2_name": agent2.name,
        "piles": initial_piles,
        "n_games": n_games,
        "wins_agent1": wins[0],                          # vittorie totali agent1
        "wins_agent2": wins[1],                          # vittorie totali agent2
        "win_rate_agent1": wins[0] / n_games,            # percentuale vittorie agent1
        "win_rate_agent2": wins[1] / n_games,            # percentuale vittorie agent2
        "avg_moves": sum(total_moves) / n_games,         # media mosse per partita
        "avg_time_ms": sum(total_times) / n_games,       # media tempo per partita
        "avg_nodes_agent1": sum(total_nodes1) / n_games, # media nodi agent1
        "avg_nodes_agent2": sum(total_nodes2) / n_games, # media nodi agent2
    }


# =============================================================================
# CONFRONTO COMPLETO TRA AGENTI
# =============================================================================

def compare_agents(configurations: list[list[int]], n_games: int = 200) -> list[dict]:
    """
    Esegue tutti i tornei tra le coppie di agenti per ogni configurazione.

    Coppie testate per ogni configurazione:
      - Minimax+AB vs XOR       (confronto tra i due agenti "intelligenti")
      - Minimax+AB vs Random    (quanto batte Minimax un agente casuale?)
      - XOR vs Random           (quanto batte XOR un agente casuale?)
      - Minimax+AB vs Minimax   (quanto aiuta l'Alpha-Beta Pruning?)

    Parametri
    ---------
    configurations : lista di configurazioni di pile da testare
    n_games        : numero di partite per ogni torneo

    Ritorna
    -------
    Lista di dizionari con i risultati di ogni torneo.
    """
    results = []  # accumula i risultati di tutti i tornei

    for piles in configurations:
        print(f"\n{'='*60}")
        print(f"  Configurazione pile: {piles}  (Nim-sum iniziale: {_nim_sum(piles)})")
        print(f"{'='*60}")

        # Calcola automaticamente il depth limit in base alla somma delle pile.
        # Pile piccole (somma <= 6): esplorazione completa, albero gestibile.
        # Pile medie (somma <= 15): depth limit 8, buon compromesso qualità/velocità.
        # Pile grandi (somma > 15): depth limit 6, necessario per tempi accettabili.
        # Senza questo limite, configurazioni come [3,5,7] (somma=15) o [4,5,6,7]
        # generano alberi con milioni di nodi e il programma si blocca.
        total = sum(piles)
        if total <= 6:
            depth = None          # esplorazione completa
            depth_label = "completo"
        elif total <= 15:
            depth = 5
            depth_label = "d=5"
        else:
            depth = 4
            depth_label = "d=4"

        # Ricrea gli agenti freschi per ogni configurazione,
        # così i contatori (nodes_explored) ripartono da zero.
        # Il nome include il depth limit per chiarezza nei risultati.
        minimax    = MinimaxAgent(name=f"Minimax+AB ({depth_label})",  max_player_id=0, use_alpha_beta=True,  depth_limit=depth)
        minimax_no = MinimaxAgent(name=f"Minimax ({depth_label})",     max_player_id=0, use_alpha_beta=False, depth_limit=depth)
        xor        = XORAgent(name="XOR")
        rnd        = RandomAgent(name="Random")

        # Lista delle coppie da sfidare.
        # Il confronto Minimax+AB vs Minimax (no AB) viene escluso
        # per configurazioni con molte pile (somma > 15): quel torneo
        # è computazionalmente molto oneroso e il risultato (sempre 50/50)
        # è già illustrato sulla configurazione [1,2,3].
        if total <= 15:
            pairs = [
                (minimax, xor),
                (minimax, rnd),
                (xor, rnd),
                (minimax, minimax_no),
            ]
        else:
            pairs = [
                (minimax, xor),
                (minimax, rnd),
                (xor, rnd),
            ]

        for a1, a2 in pairs:
            # Per gli agenti Minimax, assicura che max_player_id sia corretto:
            # il primo agente della coppia è sempre il giocatore 0 (MAX).
            if hasattr(a1, 'max_player_id'):
                a1.max_player_id = 0
            if hasattr(a2, 'max_player_id'):
                a2.max_player_id = 1

            res = run_tournament(a1, a2, piles, n_games=n_games)
            results.append(res)
            _print_tournament_result(res)

    return results


# =============================================================================
# FUNZIONI DI SUPPORTO (PRIVATE)
# =============================================================================

def _nim_sum(piles: list[int]) -> int:
    """
    Calcola la nim_sum di una lista di pile (funzione standalone).
    Usata internamente senza dover creare un NimState.
    Il prefisso _ indica che è una funzione "privata" del modulo.
    """
    r = 0
    for p in piles:
        r ^= p  # XOR accumulato
    return r


def _print_tournament_result(res: dict):
    """
    Stampa i risultati di un torneo in formato leggibile.
    Il prefisso _ indica che è una funzione "privata" del modulo.
    """
    print(f"\n  {res['agent1_name']} vs {res['agent2_name']}  ({res['n_games']} partite)")
    print(f"  ├─ Vittorie {res['agent1_name']}: {res['wins_agent1']}  ({res['win_rate_agent1']*100:.1f}%)")
    print(f"  ├─ Vittorie {res['agent2_name']}: {res['wins_agent2']}  ({res['win_rate_agent2']*100:.1f}%)")
    print(f"  ├─ Media mosse per partita: {res['avg_moves']:.1f}")
    print(f"  ├─ Media tempo per partita: {res['avg_time_ms']:.3f} ms")
    if res['avg_nodes_agent1'] > 0:
        print(f"  └─ Media nodi esplorati ({res['agent1_name']}): {res['avg_nodes_agent1']:.0f}")
    if res['avg_nodes_agent2'] > 0:
        print(f"  └─ Media nodi esplorati ({res['agent2_name']}): {res['avg_nodes_agent2']:.0f}")


# =============================================================================
# ANALISI DIDATTICA DELLA NIM-SUM
# =============================================================================

def analyze_nim_sum(piles: list[int]):
    """
    Stampa un'analisi didattica della Nim-sum di una configurazione.

    Mostra:
    - Il valore decimale e binario di ogni pila
    - Il risultato dello XOR colonna per colonna
    - Se la posizione è vincente o perdente per chi deve muovere

    Esempio di output per [3, 5, 7]:
      Pila 1:   3  →  00000011
      Pila 2:   5  →  00000101
      Pila 3:   7  →  00000111
      ────────────────────
      Nim-sum:    1  →  00000001
      ✓  Posizione VINCENTE per chi deve muovere (N-position)

    Parametri
    ---------
    piles : list[int]
        Configurazione delle pile da analizzare.
    """
    print(f"\n{'─'*50}")
    print(f"  Analisi Nim-sum per pile = {piles}")
    print(f"{'─'*50}")

    for i, p in enumerate(piles):
        # {p:3d}  → intero in campo di 3 caratteri (allineamento colonne)
        # {p:08b} → binario con 8 cifre, zeri iniziali se necessario
        # Es: p=3 → "  3  →  00000011"
        print(f"  Pila {i+1}: {p:3d}  →  {p:08b}")

    nim_s = _nim_sum(piles)

    # Separatore visivo tra le pile e il risultato.
    print(f"  {'─'*20}")
    print(f"  Nim-sum:  {nim_s:3d}  →  {nim_s:08b}")

    # Interpreta il risultato secondo la teoria di Sprague-Grundy.
    if nim_s == 0:
        print(f"  ⚠  Posizione PERDENTE per chi deve muovere (P-position)")
    else:
        print(f"  ✓  Posizione VINCENTE per chi deve muovere (N-position)")

    print(f"{'─'*50}")
