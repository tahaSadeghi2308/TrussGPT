from .models import Material

materials = {
    "ST-52" : Material("ST-52", 210e9, 350e6 , 550e6),
    "ST-32" : Material("ST-32", 200e9, 195e6 , 340e6),
    "Iron" : Material("Iron", 190e9, 200e6 , 325e6)
}

nodes = []

elements = []
