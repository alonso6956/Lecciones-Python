"""Punto de integración de pasivas por clase, sin dependencias del equipo."""

from progression import CLASES


class PasivaFactory:
    def para_clase(self, clase):
        # TODO: Construir los efectos definidos por el árbol de clase.
        return list(CLASES.get(clase, {}).get("pasivas", []))


pasiva_factory = PasivaFactory()
