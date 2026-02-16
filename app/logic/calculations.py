from .truss_data import nodes , elements
from .truss_calculator import *

dof = 2 * len(nodes)
F = np.zeros(dof)

for n in nodes:
    idx = 2 * (n.node_id - 1)
    F[idx] = n.loads["fx"]
    F[idx + 1] = n.loads["fy"]

K = assemble_global_stiffness(nodes, elements)
K_bc, F_bc = apply_boundary_conditions(K, F, nodes)
d = solve_displacements(K_bc, F_bc)

forces = compute_forces(elements, d)
results = check_element_failure(elements, forces)

# ================== WRITE RESULTS ==================
with open("RESULT.txt", "w") as file:

    file.write("Displacements (m):\n")
    for i in range(0, len(d), 2):
        node_id = i // 2 + 1
        file.write(
            f"Node {node_id}: ux = {d[i]:.6e}, uy = {d[i + 1]:.6e}\n"
        )

    file.write("\nElement Axial Forces (N):\n")
    for eid, f_val in forces.items():
        status = "Tension" if f_val > 0 else "Compression"
        file.write(
            f"Element {eid}: {f_val:8.2f} N ({status})\n"
        )

    file.write("\nElement Stress Check:\n")
    for eid, r in results.items():
        file.write(
            f"Element {eid}: "
            f"Force = {r['force']:.2f} N, "
            f"Stress = {r['stress']:.2e} Pa, "
            f"Status = {r['status']}\n"
        )