"""
main.py
-------
Punto d'ingresso principale del progetto Nim.

Questo file orchestra le tre modalità d'uso del software:
  1. Partita interattiva: l'utente gioca contro un agente a scelta
  2. Esperimenti automatici: tornei tra agenti con raccolta statistiche
  3. Analisi Nim-sum: spiegazione didattica della strategia ottima

La struttura a funzioni separate (play_interactive, run_experiments, ecc.)
rende il codice modulare: ogni funzione fa una sola cosa, è testabile
indipendentemente, e main() si limita a smistare.
"""

from nim import NimState
from agents import RandomAgent, XORAgent, MinimaxAgent
from experiments import (
    run_game,
    run_tournament,
    compare_agents,
    analyze_nim_sum,
    _print_tournament_result,
)


# =============================================================================
# AGENTE UMANO
# =============================================================================

class HumanAgent:
    """
    Agente che legge la mossa dall'input dell'utente tramite terminale.

    Ha la stessa interfaccia degli altri agenti (metodo choose_move):
    questo è il pattern "polimorfismo" — run_game() tratta l'umano
    esattamente come un agente algoritmico, chiamando choose_move()
    senza sapere chi c'è dall'altra parte.
    """

    def __init__(self, name: str = "Umano"):
        self.name = name  # nome mostrato nei messaggi

    def choose_move(self, state: NimState) -> tuple[int, int]:
        """
        Legge la mossa dall'utente e la valida prima di restituirla.

        Il ciclo while True continua a chiedere input finché
        l'utente non inserisce una mossa valida.
        """
        # Mostra lo stato corrente all'utente prima di chiedergli di muovere.
        print(f"\n  Stato attuale: {state}")
        print(f"  Pile: {state.piles}")

        while True:
            try:
                # int(input(...)) chiede una stringa e la converte in intero.
                # - 1 perché l'utente conta le pile da 1, Python da 0.
                pile_idx = int(input("  Scegli la pila (1, 2, ...): ")) - 1
                amount   = int(input("  Quanti oggetti rimuovere? "))

                # Costruisce la mossa come tupla.
                move = (pile_idx, amount)

                # Verifica che la mossa sia legale confrontandola
                # con la lista delle mosse ammesse dallo stato corrente.
                if move in state.get_legal_moves():
                    return move  # mossa valida: esce dal loop e la restituisce
                else:
                    print("  ⚠ Mossa non valida. Riprova.")

            except (ValueError, IndexError):
                # ValueError: l'utente ha inserito qualcosa che non è un numero
                # (es. "tre" invece di "3").
                # IndexError: l'indice di pila è fuori range.
                # In entrambi i casi, si ripete la richiesta.
                print("  ⚠ Input non valido. Inserisci numeri interi.")


# =============================================================================
# MODALITÀ 1: PARTITA INTERATTIVA
# =============================================================================

def play_interactive():
    """
    Avvia una partita interattiva tra l'utente e un agente scelto.

    Flusso:
    1. L'utente sceglie la configurazione delle pile.
    2. L'utente sceglie l'avversario (Random, XOR o Minimax).
    3. Viene mostrata l'analisi della Nim-sum della posizione iniziale.
    4. Si gioca la partita con run_game() in modalità non-verbose
       (la stampa è gestita da HumanAgent.choose_move).
    5. Viene annunciato il vincitore.
    """
    print("\n" + "="*55)
    print("  GIOCO DEL NIM — Modalità Interattiva")
    print("="*55)

    # --- Scelta della configurazione delle pile ---
    print("\n  Configurazioni predefinite:")
    print("  1. Classica:   [3, 5, 7]")
    print("  2. Facile:     [1, 2, 3]")
    print("  3. Avanzata:   [4, 5, 6, 7]")
    print("  4. Personalizzata")

    cfg_choice = input("\n  Scelta (1-4): ").strip()

    # Dizionario che mappa la scelta dell'utente alla configurazione.
    piles_map = {
        "1": [3, 5, 7],
        "2": [1, 2, 3],
        "3": [4, 5, 6, 7],
    }

    if cfg_choice in piles_map:
        # Scelta predefinita: prende la configurazione dal dizionario.
        piles = piles_map[cfg_choice]
    else:
        # Scelta personalizzata: l'utente inserisce i valori separati da spazio.
        # split() divide la stringa sugli spazi → lista di stringhe
        # map(int, ...) converte ogni stringa in intero
        # list(...) materializza il risultato in una lista
        raw = input("  Inserisci le pile separate da spazio (es: 3 5 7): ")
        piles = list(map(int, raw.split()))

    # --- Scelta dell'avversario ---
    print("\n  Scegli il tuo avversario:")
    print("  1. Random (casuale)")
    print("  2. XOR    (strategia ottima)")
    print("  3. Minimax (albero di gioco completo)")

    opp_choice = input("\n  Scelta (1-3): ").strip()

    # Dizionario che mappa la scelta all'agente corrispondente.
    # max_player_id=1 per Minimax perché l'avversario è il giocatore 1.
    opponents = {
        "1": RandomAgent(name="Random"),
        "2": XORAgent(name="XOR"),
        "3": MinimaxAgent(name="Minimax+AB", max_player_id=1),
    }

    # .get(key, default): restituisce il valore per la chiave,
    # o il default se la chiave non esiste (scelta non valida → Random).
    opponent = opponents.get(opp_choice, RandomAgent())

    human = HumanAgent()  # crea l'agente umano

    # Mostra l'analisi della posizione di partenza prima di iniziare.
    analyze_nim_sum(piles)

    print(f"\n  Inizi tu contro {opponent.name}. Buona fortuna!\n")

    # Esegue la partita. verbose=False perché HumanAgent stampa già da solo.
    result = run_game(human, opponent, piles, verbose=False)

    # Annuncia il vincitore in base all'indice restituito da run_game.
    if result["winner"] == 0:
        print("\n  🎉 Hai vinto!")
    else:
        print(f"\n  😞 Ha vinto {opponent.name}.")


# =============================================================================
# MODALITÀ 2: ESPERIMENTI AUTOMATICI
# =============================================================================

def run_experiments():
    """
    Esegue i tornei automatici tra tutti gli agenti su più configurazioni.

    Le configurazioni sono scelte per coprire casi diversi:
      [1,2,3] → nim_sum=0 (P-position): chi inizia è in svantaggio
      [3,5,7] → nim_sum=1 (N-position): chi inizia è in vantaggio
      [2,4,6] → nim_sum=0 (P-position): altra P-position con pile più grandi
      [4,5,6,7] → 4 pile: testa la scalabilità degli agenti

    I risultati permettono di confrontare:
    - Qualità della soluzione (win rate)
    - Efficienza computazionale (nodi esplorati, tempo)
    - Effetto dell'Alpha-Beta Pruning
    """
    print("\n" + "="*60)
    print("  ESPERIMENTI — Tornei tra Agenti")
    print("="*60)

    configurations = [
        [1, 2, 3],     # nim_sum = 1^2^3 = 0  → P-position
        [3, 5, 7],     # nim_sum = 3^5^7 = 1  → N-position
        [2, 4, 6],     # nim_sum = 2^4^6 = 0  → P-position
        [4, 5, 6, 7],  # nim_sum = 4^5^6^7 = 0 → P-position, 4 pile
    ]

    # compare_agents esegue tutti i tornei e restituisce i risultati.
    results = compare_agents(configurations, n_games=200)

    print("\n\n" + "="*60)
    print("  RIEPILOGO COMPLESSIVO")
    print("="*60)
    _print_summary(results)


def _print_summary(results: list[dict]):
    """
    Stampa una tabella riassuntiva aggregando i risultati su tutte le configurazioni.

    Per ogni coppia di agenti, somma le vittorie su tutte le configurazioni
    e calcola il win rate complessivo.

    Il prefisso _ indica che è una funzione di supporto interna a main.py.
    """
    # defaultdict con lambda: ogni nuova chiave ottiene {"w1":0, "w2":0, "games":0}.
    # Questo evita di inizializzare manualmente ogni coppia di agenti.
    aggregate = defaultdict(lambda: {"w1": 0, "w2": 0, "games": 0})

    for r in results:
        # La chiave è la coppia di nomi degli agenti.
        key = (r["agent1_name"], r["agent2_name"])
        aggregate[key]["w1"]    += r["wins_agent1"]  # accumula vittorie agent1
        aggregate[key]["w2"]    += r["wins_agent2"]  # accumula vittorie agent2
        aggregate[key]["games"] += r["n_games"]       # accumula partite totali

    # Stampa l'intestazione della tabella.
    # :<35 = allinea a sinistra in campo di 35 caratteri
    # :>12 = allinea a destra in campo di 12 caratteri
    print(f"\n  {'Scontro':<35} {'Vittorie A1':>12} {'Vittorie A2':>12} {'Win% A1':>9}")
    print(f"  {'─'*35} {'─'*12} {'─'*12} {'─'*9}")

    for (a1, a2), stats in aggregate.items():
        g = stats["games"]
        # :.1f = numero float con 1 decimale
        print(f"  {a1+' vs '+a2:<35} {stats['w1']:>12} {stats['w2']:>12} {stats['w1']/g*100:>8.1f}%")


# Importazione necessaria per _print_summary (usata solo qui dentro).
from collections import defaultdict


# =============================================================================
# MAIN — PUNTO D'INGRESSO
# =============================================================================

def main():
    """
    Funzione principale: mostra il menu e smista verso la modalità scelta.

    Questa funzione è volutamente minimale: non contiene logica di gioco,
    solo lettura dell'input e chiamata alla funzione appropriata.
    """
    print("\n" + "█"*55)
    print("  PROGETTO NIM — Teoria dei Giochi (IA)")
    print("  Minimax · Alpha-Beta · XOR Strategy")
    print("█"*55)

    print("\n  Modalità:")
    print("  1. Partita interattiva (Umano vs Agente)")
    print("  2. Esperimenti automatici (Tornei tra Agenti)")
    print("  3. Analisi Nim-sum di una configurazione")

    # .strip() rimuove spazi e newline accidentali dall'input.
    choice = input("\n  Scelta (1/2/3): ").strip()

    if choice == "1":
        play_interactive()
    elif choice == "2":
        run_experiments()
    elif choice == "3":
        raw = input("  Inserisci le pile (es: 3 5 7): ")
        piles = list(map(int, raw.split()))
        analyze_nim_sum(piles)
    else:
        print("  Scelta non valida. Riavvia il programma.")


# Questo blocco viene eseguito SOLO se si lancia direttamente questo file
# con "python main.py". Se main.py venisse importato da un altro modulo,
# il blocco non verrebbe eseguito (utile per i test automatici).
if __name__ == "__main__":
    main()
