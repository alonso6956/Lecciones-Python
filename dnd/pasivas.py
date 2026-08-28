"""Modelos de las pasivas otorgadas por el arma equipada."""

from dataclasses import dataclass, field


@dataclass(frozen=True)
class Pasiva:
    id: str
    nombre: str
    descripcion: str
    tipo_arma: str
    efecto: str
    tier: int
    valor: float
    parametros: dict = field(default_factory=dict)

    @property
    def probabilidad(self):
        if self.efecto in {"critico", "ignorar_defensa"}:
            return self.valor
        return 0.0

    @property
    def dano_sangrado(self):
        if self.efecto == "doble_ataque_sangrado":
            return int(self.valor)
        return 0

    @property
    def numero_ataques(self):
        return int(self.parametros.get("numero_ataques", 1))

    @property
    def duracion_turnos(self):
        return int(self.parametros.get("duracion_turnos", 0))

    def calcular_critico(self, dano_bruto):
        """Aplica el multiplicador crítico antes de las capas defensivas."""
        if self.efecto != "critico":
            return dano_bruto
        multiplicador = float(self.parametros.get("multiplicador", 1.5))
        return dano_bruto * multiplicador

    def ignora_defensa(self, tirada):
        """Indica si la maza atraviesa armadura y bloqueo en este ataque."""
        return self.efecto == "ignorar_defensa" and tirada < self.probabilidad
