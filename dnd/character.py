class Personaje:
    def __init__(self, nombre, arma, stats):
        self.nombre = nombre
        self.arma = arma

        self.fuerza = stats["fuerza"]
        self.destreza = stats["destreza"]
        self.constitucion = stats["Constitución"]

        self.salud_maxima = 50 * self.constitucion
        self.hp = self.salud_maxima

        self.nivel = 1
        self.oro = 0
        self.exp = 0