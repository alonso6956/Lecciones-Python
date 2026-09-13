"""Demostración reproducible: python3 simulate_enemy_ai.py --cerebro comandante."""

import argparse
import json
from collections import Counter

from enemy_ai import PerfilIA
from tactical_board import Tablero
from tactical_combat import CombatResolver
from tactical_models import Encuentro, preparacion_ofensiva


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cerebro", choices=["bestia", "soldado", "comandante"], default="comandante")
    parser.add_argument("--seed", type=int, default=1234)
    args = parser.parse_args()
    party = preparacion_ofensiva()
    encuentro = Encuentro(perfil_ia=PerfilIA(args.cerebro, ("rompe_tanque", "cobarde")))
    tablero = Tablero.inicial([s.personaje_id for s in party], encuentro.id)
    combate = CombatResolver(party, encuentro, seed=args.seed, tablero=tablero.plan())
    resultado = combate.ejecutar()
    decisiones = [e for e in resultado["eventos"] if e["tipo"] == "decision_ia"]
    print(json.dumps({"cerebro": args.cerebro, "seed": args.seed,
                      "resultado": resultado["resultado"], "rondas": resultado["rondas"],
                      "motivos": dict(Counter(e["metadata"]["motivo"] for e in decisiones)),
                      "decisiones": decisiones}, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
