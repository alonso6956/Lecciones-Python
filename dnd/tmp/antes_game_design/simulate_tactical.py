"""Balance reproducible: python -B simulate_tactical.py --n 1000 --seed-base 1234."""

import argparse
import json
from collections import Counter, defaultdict
from dataclasses import replace
from pathlib import Path

from tactical_combat import CombatResolver
from tactical_diagnostics import normalizar_causa
from tactical_models import Encuentro, preparacion_adaptada, preparacion_ofensiva


def simular(encuentro, party, n=1000, seed_base=1234):
    if type(n) is not int or n < 1:
        raise ValueError("N debe ser un entero positivo.")
    victorias = rupturas = activaciones = castigos = 0
    rondas = Counter()
    resultados = Counter()
    causas = Counter()
    dano = defaultdict(float)
    supervivencia = Counter()
    for i in range(n):
        combate = CombatResolver(party, encuentro, seed_base + i)
        resumen = combate.ejecutar()
        resultado = resumen["resultado"]
        resultados[resultado] += 1
        victorias += resultado == "victoria"
        rondas[resultado] += resumen["rondas"]
        if resumen["diagnostico"]:
            causas[resumen["diagnostico"]["causa"]] += 1
        tipos = {e.tipo for e in combate.log.eventos}
        rupturas += "escudo_roto" in tipos
        activaciones += "escudo_activado" in tipos
        castigos += "castigo_escudo" in tipos
        for e in combate.log.eventos:
            if e.tipo == "dano_recibido":
                dano[normalizar_causa(e.fuente_tag)] += e.cantidad
        supervivencia.update(resumen["supervivientes"])
    derrotas = n - victorias
    return {"n": n, "seed_base": seed_base, "victorias_pct": round(100 * victorias / n, 2),
            "rondas_promedio": round(sum(rondas.values()) / n, 2),
            "rondas_por_resultado": {k: round(rondas[k] / resultados[k], 2) for k in resultados},
            "derrotas_por_causa_pct": {k: round(100 * v / derrotas, 2) for k, v in causas.items()},
            "escudo_activado_pct": round(100 * activaciones / n, 2),
            "ruptura_exitosa_pct": round(100 * rupturas / n, 2),
            "ruptura_sobre_activaciones_pct": round(100 * rupturas / activaciones, 2) if activaciones else 0,
            "castigo_escudo_pct": round(100 * castigos / n, 2),
            "dano_recibido_promedio_por_tag": {k: round(v / n, 2) for k, v in dano.items()},
            "supervivencia_por_personaje_pct": {s.personaje_id: round(100 * supervivencia[s.personaje_id] / n, 2) for s in party}}


def perfiles():
    ofensiva = preparacion_ofensiva()
    adaptada = preparacion_adaptada()
    return {"ofensiva": ofensiva, "adaptada": adaptada,
            "solo_build": [replace(s, build="adaptacion") for s in ofensiva],
            "solo_arma": [replace(s, arma=a.arma) for s, a in zip(ofensiva, adaptada)],
            "solo_ia": [replace(s, prioridad="tactica") for s in ofensiva]}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=1000)
    parser.add_argument("--seed-base", type=int, default=1234)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.n < 1:
        parser.error("--n debe ser positivo")
    report = {nombre: simular(Encuentro(), party, args.n, args.seed_base) for nombre, party in perfiles().items()}
    texto = json.dumps(report, ensure_ascii=False, indent=2)
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(texto + "\n", encoding="utf-8")
    print(texto)


if __name__ == "__main__":
    main()
