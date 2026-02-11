import numpy as np

class Material:
    def __init__(self, name, young_modulus, Sy, Su):
        self.name = name
        self.E = float(young_modulus)
        self.Sy = float(Sy)
        self.Su = float(Su)

class Node:
    def __init__(self, node_id, x, y, restraints=None, loads=None):
        self.node_id = int(node_id)
        self.x = float(x)
        self.y = float(y)
        self.restraints = restraints or {"ux": False, "uy": False}
        self.loads = loads or {"fx": 0.0, "fy": 0.0}

class Element:
    def __init__(self, element_id, node_i, node_j, area, material):
        self.element_id = int(element_id)
        self.node_i = node_i
        self.node_j = node_j
        self.area = float(area)
        self.material = material

    def length(self):
        dx = self.node_j.x - self.node_i.x
        dy = self.node_j.y - self.node_i.y
        return (dx*dx + dy*dy)**0.5

    def direction_cosines(self):
        L = self.length()
        if L == 0:
            raise ValueError(f"Element {self.element_id} has zero length")
        cx = (self.node_j.x - self.node_i.x) / L
        cy = (self.node_j.y - self.node_i.y) / L
        return cx, cy

    def local_stiffness(self):
        """Return the 4x4 local stiffness matrix (as a NumPy array) for a 2D truss element."""
        E = float(self.material.E)
        A = float(self.area)
        L = self.length()
        cx, cy = self.direction_cosines()

        stiffness_local = np.array([
            [ cx*cx, cx*cy, -cx*cx, -cx*cy ],
            [ cx*cy, cy*cy, -cx*cy, -cy*cy ],
            [ -cx*cx, -cx*cy, cx*cx, cx*cy ],
            [ -cx*cy, -cy*cy, cx*cy, cy*cy ]
        ], dtype=float)

        return (E * A / L) * stiffness_local

