import numpy as np

def assemble_global_stiffness(nodes, elements):
    dof = 2 * len(nodes)
    K = np.zeros((dof, dof))
    for elem in elements:
        k_local = np.array(elem.local_stiffness())
        i = (elem.node_i.node_id - 1) * 2
        j = (elem.node_j.node_id - 1) * 2
        index = [i, i+1, j, j+1]
        for a in range(4):
            for b in range(4):
                K[index[a], index[b]] += k_local[a, b]
    return K

def apply_boundary_conditions(K, F, nodes):
    for node in nodes:
        i = (node.node_id - 1) * 2
        if node.restraints.get("ux", False):
            K[i, :] = 0
            K[:, i] = 0
            K[i, i] = 1
            F[i] = 0
        if node.restraints.get("uy", False):
            K[i+1, :] = 0
            K[:, i+1] = 0
            K[i+1, i+1] = 1
            F[i+1] = 0
    return K, F

def solve_displacements(K, F):
    return np.linalg.solve(K, F)


def compute_forces(elements, displacements):
    forces = {}
    for elem in elements:
        cx, cy = elem.direction_cosines()
        i = (elem.node_i.node_id - 1) * 2
        j = (elem.node_j.node_id - 1) * 2
        u = np.array([displacements[i], displacements[i+1], displacements[j], displacements[j+1]])
        E = elem.material.E
        A = elem.area
        L = elem.length()
        strain = (1 / L) * np.array([-cx, -cy, cx, cy]).dot(u)
        forces[elem.element_id] = E * A * strain
    return forces


def check_element_failure(elements, forces):
    results = {}

    for elem in elements:
        force = forces[elem.element_id]
        stress = force / elem.area

        Sy = elem.material.Sy
        Su = elem.material.Su

        if abs(stress) >= Su:
            status = "FAILED"
        elif abs(stress) >= Sy:
            status = "YIELDED"
        else:
            status = "SAFE"

        results[elem.element_id] = {
            "force": force,
            "stress": stress,
            "status": status
        }

    return results