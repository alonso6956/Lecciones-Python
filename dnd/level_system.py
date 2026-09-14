import math


class SistemaNiveles:
    def __init__(self, exp_por_nivel=None, nivel_maximo=999):
        self.exp_por_nivel = exp_por_nivel
        self.nivel_maximo = nivel_maximo

    def experiencia_necesaria(self, nivel):
        if nivel < 1:
            raise ValueError("El nivel debe ser mayor o igual a 1")
        if nivel == 1:
            return 0

        total = 0
        for n in range(1, nivel):
            total += math.floor(n + 300 * (2 ** (n / 7)))
        return total // 4

    def experiencia_siguiente_nivel(self, personaje):
        if personaje.nivel >= self.nivel_maximo:
            return None
        return self.experiencia_necesaria(personaje.nivel + 1)

    def puede_subir(self, personaje):
        if personaje.nivel >= self.nivel_maximo:
            return False

        siguiente_nivel = personaje.nivel + 1
        return personaje.exp >= self.experiencia_necesaria(siguiente_nivel)
