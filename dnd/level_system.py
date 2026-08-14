class SistemaNiveles:
    def __init__(self, exp_por_nivel=30, nivel_maximo=10):
        self.exp_por_nivel = exp_por_nivel
        self.nivel_maximo = nivel_maximo

    def experiencia_necesaria(self, nivel):
        if nivel < 1:
            raise ValueError("El nivel debe ser mayor o igual a 1")

        return (nivel - 1) * self.exp_por_nivel

    def puede_subir(self, personaje):
        if personaje.nivel >= self.nivel_maximo:
            return False

        siguiente_nivel = personaje.nivel + 1
        return personaje.exp >= self.experiencia_necesaria(siguiente_nivel)
