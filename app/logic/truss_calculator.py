import numpy as np
import matplotlib.cm as cm
import matplotlib.colors as mcolors
import matplotlib.pyplot as plt

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

def check_boundary_conditions(nodes):
    ux_count = sum(1 for n in nodes if n.restraints.get("ux", False))
    uy_count = sum(1 for n in nodes if n.restraints.get("uy", False))
    both_count = sum(1 for n in nodes if n.restraints.get("ux", False) and n.restraints.get("uy", False))

    if ux_count == 0 and uy_count == 0:
        return False, "No boundary conditions found. You need at least one node with restraints (ux and/or uy) to prevent rigid body motion."
    
    if ux_count == 0:
        return False, "No restraints in X direction (ux). Add at least one node with ux=True to prevent horizontal translation."
    
    if uy_count == 0:
        return False, "No restraints in Y direction (uy). Add at least one node with uy=True to prevent vertical translation."
    
    total_restraints = ux_count + uy_count
    if total_restraints < 3:
        return False, f"Not enough boundary conditions ({total_restraints} found, need at least 3). " \
                     f"Add more restraints to prevent rotation. " \
                     f"Current: {ux_count} ux restraints, {uy_count} uy restraints."
    
    return True, ""


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
    try:
        det = np.linalg.det(K)
        if abs(det) < 1e-10:  # Very small determinant indicates singular matrix
            raise ValueError(
                "Stiffness matrix is singular (determinant ≈ 0). "
                "This usually means the truss structure is not properly constrained. "
                "Ensure you have at least 3 boundary conditions (restraints) to prevent rigid body motion. "
                "For a 2D truss, you typically need: "
                "- At least one node fixed in both x and y (ux=True, uy=True), OR "
                "- Multiple nodes with restraints that prevent translation and rotation."
            )
    except np.linalg.LinAlgError:
        pass
    try:
            return np.linalg.solve(K, F)
    except np.linalg.LinAlgError as e:
        try:
            solution, residuals, rank, s = np.linalg.lstsq(K, F, rcond=None)
            if rank < K.shape[0]:
                raise ValueError(
                    f"Stiffness matrix is rank-deficient (rank={rank}, expected={K.shape[0]}). "
                    "The truss structure is not properly constrained. "
                    "This typically means: "
                    "1. Not enough boundary conditions (restraints) to prevent rigid body motion, OR "
                    "2. The structure is a mechanism (unstable). "
                    "For a 2D truss, you need at least 3 independent restraints to prevent: "
                    "- Translation in X direction, "
                    "- Translation in Y direction, "
                    "- Rotation about Z axis. "
                    "Please add more restraints (supports) to your nodes."
                )
            return solution
        except Exception as inner_e:
            raise ValueError(
                f"Failed to solve truss system: {str(e)}. "
                "The structure may be unstable or improperly constrained. "
                "Check that you have sufficient boundary conditions (restraints) on your nodes."
            ) from e


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

def plot_truss(nodes, elements, displacements, forces, scale=100, filepath=None):
    import matplotlib.pyplot as plt
    
    fig, ax = plt.subplots(figsize=(10, 8))

    # Original undeformed shape
    for elem in elements:
        xi, yi = elem.node_i.x, elem.node_i.y
        xj, yj = elem.node_j.x, elem.node_j.y
        ax.plot([xi, xj], [yi, yj], "k--", linewidth=1, alpha=0.6)

    forces_vals = list(forces.values())
    abs_max = max(abs(f) for f in forces_vals) if forces_vals else 1
    norm = mcolors.TwoSlopeNorm(vmin=-abs_max, vcenter=0, vmax=abs_max)
    cmap = cm.coolwarm

    for elem in elements:
        i = (elem.node_i.node_id - 1) * 2
        j = (elem.node_j.node_id - 1) * 2

        xi = elem.node_i.x + scale * displacements[i]
        yi = elem.node_i.y + scale * displacements[i + 1]
        xj = elem.node_j.x + scale * displacements[j]
        yj = elem.node_j.y + scale * displacements[j + 1]

        force = forces[elem.element_id]
        color = cmap(norm(force))

        ax.plot([xi, xj], [yi, yj], color=color, linewidth=4)

    # Colorbar
    sm = cm.ScalarMappable(norm=norm, cmap=cmap)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax)
    cbar.set_label(
        "Axial Force (N)\n(Positive = Tension, Negative = Compression)", fontsize=12
    )
    

    ax.set_aspect("equal")
    ax.set_xlabel("X (m)")
    ax.set_ylabel("Y (m)")
    ax.set_title("Truss Deformation and Axial Force Distribution")
    ax.grid(True, alpha=0.3)
    plt.tight_layout()
    
    save_path = filepath if filepath else "truss_deformation.png"
    plt.savefig(save_path, dpi=150, bbox_inches="tight")
    plt.close()
    print(f"Plot saved as '{save_path}'")