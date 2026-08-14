class Personaje:
    SALUD_BASE = 50

    def __init__(self, nombre, arma, stats):
        self.nombre = nombre
        self.arma = arma

        self.fuerza = stats["fuerza"]
        self.destreza = stats["destreza"]
        self.constitucion = stats["Constitución"]

        self.salud_maxima = self.SALUD_BASE
        self.hp = self.salud_maxima

        self.nivel = 1
        self.oro = 0
        self.exp = 0

    def curar(self, cantidad):
        salud_anterior = self.hp
        self.hp = min(self.salud_maxima, self.hp + cantidad)
        return self.hp - salud_anterior

    def subir_nivel(self, estadistica):
        estadisticas_validas = {
            "fuerza": "fuerza",
            "destreza": "destreza",
            "constitucion": "constitucion",
        }

        if estadistica not in estadisticas_validas:
            raise ValueError("La estadística elegida no es válida")

        self.nivel += 1
        atributo = estadisticas_validas[estadistica]
        setattr(self, atributo, getattr(self, atributo) + 1)

        if estadistica == "constitucion":
            self.hp += 10
            self.salud_maxima += 10

    def ganar_exp(self, cantidad):
        self.exp += cantidad
