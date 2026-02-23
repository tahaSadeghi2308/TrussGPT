from flask import request , send_from_directory , jsonify , Blueprint
from app.logic.models import Node, Element
from app.logic.truss_data import materials, nodes, elements
from app.logic.truss_calculator import (
    assemble_global_stiffness,
    apply_boundary_conditions,
    solve_displacements,
    compute_forces,
    check_element_failure,
    plot_truss,
    check_boundary_conditions,
)
import io , base64 , json
import numpy as np
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

LOGIC_FOLDER = Path(__file__).parent.parent / "logic"
RESULTS_FILE = LOGIC_FOLDER / "truss_results.json"
IMAGE_FILE = LOGIC_FOLDER / "truss_deformation.png"

info_bp = Blueprint("truss_info" , __name__)

@info_bp.route("/api/truss-data", methods=["GET"])
def get_truss_data():
    """Return current truss data: nodes, elements, materials."""
    return jsonify(
        nodes=[
            {
                "node_id": n.node_id,
                "x": n.x,
                "y": n.y,
                "ux": bool(n.restraints.get("ux", False)),
                "uy": bool(n.restraints.get("uy", False)),
                "fx": float(n.loads.get("fx", 0.0)),
                "fy": float(n.loads.get("fy", 0.0)),
            }
            for n in nodes
        ],
        materials=[m.name for m in materials.values()],
        elements=[
            {
                "element_id": e.element_id,
                "node_i": e.node_i.node_id,
                "node_j": e.node_j.node_id,
                "material": e.material.name,
                "area": e.area,
            }
            for e in elements
        ],
    )


@info_bp.route("/api/nodes", methods=["POST"])
def api_add_node():
    """Add a new node with coordinates and restraints."""
    data = request.get_json(silent=True) or {}
    errors = []

    try:
        x = float(data.get("x", ""))
    except (TypeError, ValueError):
        errors.append("x must be a floating point number.")

    try:
        y = float(data.get("y", ""))
    except (TypeError, ValueError):
        errors.append("y must be a floating point number.")

    ux = bool(data.get("ux", False))
    uy = bool(data.get("uy", False))

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    for node in nodes:
        if node.x == x and node.y == y:
            return jsonify({"ok": False, "errors": ["Node already exists."]}), 400

    next_id = (max((n.node_id for n in nodes), default=0) + 1) if nodes else 1
    node = Node(node_id=next_id, x=x, y=y, restraints={"ux": ux, "uy": uy})
    nodes.append(node)

    return jsonify(
        {
            "ok": True,
            "node": {
                "node_id": node.node_id,
                "x": node.x,
                "y": node.y,
                "ux": node.restraints["ux"],
                "uy": node.restraints["uy"],
                "fx": node.loads["fx"],
                "fy": node.loads["fy"],
            },
        }
    )


@info_bp.route("/api/elements", methods=["POST"])
def api_add_element():
    data = request.get_json(silent=True) or {}
    errors = []

    try:
        node_i_id = int(data.get("node_i_id", ""))
        node_j_id = int(data.get("node_j_id", ""))
    except (TypeError, ValueError):
        return jsonify({"ok": False, "errors": ["node_i and node_j must be valid node IDs."]}), 400

    if node_i_id == node_j_id:
        errors.append("node_i and node_j must be different nodes.")

    material_name = data.get("material")
    if not material_name or material_name not in materials:
        errors.append("material must be one of the available materials.")

    node_i = next((n for n in nodes if n.node_id == node_i_id), None)
    node_j = next((n for n in nodes if n.node_id == node_j_id), None)

    if node_i is None or node_j is None:
        errors.append("Both node_i and node_j must be existing nodes.")

    try:
        area = float(data.get("area", ""))
        if area <= 0:
            errors.append("Area must be a positive number.")
    except (TypeError, ValueError):
        errors.append("Area must be a valid floating point number.")

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    element_id = (max((e.element_id for e in elements), default=0) + 1) if elements else 1
    material = materials[material_name]
    element = Element(element_id=element_id, node_i=node_i, node_j=node_j, area=area, material=material)
    elements.append(element)

    return jsonify(
        {
            "ok": True,
            "element": {
                "element_id": element.element_id,
                "node_i": element.node_i.node_id,
                "node_j": element.node_j.node_id,
                "material": element.material.name,
                "area": element.area,
            },
        }
    )


@info_bp.route("/api/loads", methods=["POST"])
def api_add_load():
    """Add nodal loads fx, fy to an existing node."""
    data = request.get_json(silent=True) or {}
    errors = []

    try:
        node_id = int(data.get("node_id", ""))
    except (TypeError, ValueError):
        errors.append("node_id must be a valid integer ID.")
        node_id = None

    try:
        fx = float(data.get("fx", "0"))
    except (TypeError, ValueError):
        errors.append("fx must be a floating point number.")
        fx = None

    try:
        fy = float(data.get("fy", "0"))
    except (TypeError, ValueError):
        errors.append("fy must be a floating point number.")
        fy = None

    node = next((n for n in nodes if n.node_id == node_id), None) if node_id is not None else None
    if node is None:
        errors.append("node_id must refer to an existing node.")

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    node.loads["fx"] = float(node.loads.get("fx", 0.0)) + fx
    node.loads["fy"] = float(node.loads.get("fy", 0.0)) + fy

    return jsonify(
        {
            "ok": True,
            "node": {
                "node_id": node.node_id,
                "x": node.x,
                "y": node.y,
                "ux": node.restraints["ux"],
                "uy": node.restraints["uy"],
                "fx": node.loads["fx"],
                "fy": node.loads["fy"],
            },
        }
    )


@info_bp.route("/api/truss/clear", methods=["POST"])
def api_truss_clear():
    """Delete all nodes and elements (reset current truss)."""
    nodes.clear()
    elements.clear()
    return jsonify({"ok": True})


@info_bp.route("/api/truss/load-default", methods=["POST"])
def api_truss_load_default():
    """Load default test truss data for testing."""
    TEST_DATA_FILE = LOGIC_FOLDER / "TRUSS_INPUT.txt"
    n = []
    e = []
    with open(TEST_DATA_FILE, "r") as f:
        mode = None
        for line in f:
            line = line.strip()
            if line == "" or line.startswith("#"):
                continue

            if line.lower() == "nodes":
                mode = "nodes"
                continue
            if line.lower() == "elements":
                mode = "elements"
                continue

            if mode == "nodes":
                parts = line.split()
                nid = int(parts[0])
                x, y = float(parts[1]), float(parts[2])
                ux_restr, uy_restr = bool(int(parts[3])), bool(int(parts[4]))
                fx, fy = float(parts[5]), float(parts[6])
                restraints = {"ux": ux_restr, "uy": uy_restr}
                loads = {"fx": fx, "fy": fy}
                n.append(Node(nid, x, y, restraints, loads))

            elif mode == "elements":
                eid, ni, nj, area, mat = line.split()
                elem = Element(
                    int(eid),
                    n[int(ni) - 1],
                    n[int(nj) - 1],
                    float(area),
                    materials[mat],
                )
                e.append(elem)

    nodes.extend(n)
    elements.extend(e)

    return jsonify({
        "ok": True,
        "message": "Default test truss loaded successfully.",
        "nodes_count": len(nodes),
        "elements_count": len(elements),
    })


@info_bp.route("/api/truss/plot", methods=["GET"])
def api_truss_plot():
    """Render the current truss to a PNG image and return it as base64."""
    if not nodes and not elements:
        return jsonify({"ok": False, "errors": ["No truss data to visualize. Add nodes and elements first."]}), 400

    fig, ax = plt.subplots(figsize=(6, 4), dpi=160)

    if nodes:
        xs = [n.x for n in nodes]
        ys = [n.y for n in nodes]
        span_x = max(xs) - min(xs) if len(xs) > 1 else 1.0
        span_y = max(ys) - min(ys) if len(ys) > 1 else 1.0
        span = max(span_x, span_y, 1.0)
    else:
        xs, ys, span = [], [], 1.0

    for e in elements:
        x_vals = [e.node_i.x, e.node_j.x]
        y_vals = [e.node_i.y, e.node_j.y]
        ax.plot(x_vals, y_vals, "-o", color="#38bdf8", linewidth=2.0, markersize=5)
        mid_x = 0.5 * (e.node_i.x + e.node_j.x)
        mid_y = 0.5 * (e.node_i.y + e.node_j.y)
        ax.text(mid_x, mid_y, f"E{e.element_id}", color="#e5e7eb", fontsize=7, ha="center", va="center")

    for n in nodes:
        ax.scatter(n.x, n.y, s=35, color="#f97316", zorder=5)
        ax.text(n.x, n.y, f"N{n.node_id}", color="#e5e7eb", fontsize=7, ha="left", va="bottom")

        fx = float(n.loads.get("fx", 0.0))
        fy = float(n.loads.get("fy", 0.0))
        arrow_len = 0.08 * span
        head_w = 0.03 * span
        head_l = 0.04 * span

        if fx != 0.0:
            direction_x = 1.0 if fx > 0 else -1.0
            ax.arrow(
                n.x,
                n.y,
                direction_x * arrow_len,
                0.0,
                head_width=head_w,
                head_length=head_l,
                length_includes_head=True,
                color="#f97373",
                zorder=6,
            )
            text_x = n.x + direction_x * arrow_len * 1.3
            text_y = n.y + 0.04 * span
            ax.text(
                text_x,
                text_y,
                f"Fx={fx:.1f}",
                color="#fecaca",
                fontsize=7,
                ha="center",
                va="bottom",
            )

        if fy != 0.0:
            direction_y = 1.0 if fy > 0 else -1.0
            ax.arrow(
                n.x,
                n.y,
                0.0,
                direction_y * arrow_len,
                head_width=head_w,
                head_length=head_l,
                length_includes_head=True,
                color="#f97373",
                zorder=6,
            )
            text_x = n.x + 0.02 * span
            text_y = n.y + direction_y * arrow_len * 1.3
            ax.text(
                text_x,
                text_y,
                f"Fy={fy:.1f}",
                color="#fecaca",
                fontsize=7,
                ha="left",
                va="center",
            )

    if nodes:
        x_margin = max(1.0, 0.15 * (max(xs) - min(xs) or 1.0))
        y_margin = max(1.0, 0.15 * (max(ys) - min(ys) or 1.0))
        ax.set_xlim(min(xs) - x_margin, max(xs) + x_margin)
        ax.set_ylim(min(ys) - y_margin, max(ys) + y_margin)

    ax.set_aspect("equal", adjustable="datalim")
    ax.set_xlabel("X")
    ax.set_ylabel("Y")
    ax.set_title("Truss visualization", color="#e5e7eb", fontsize=10)
    ax.grid(True, linestyle="--", alpha=0.35)
    ax.set_facecolor("#020617")
    fig.patch.set_facecolor("#020617")

    for spine in ax.spines.values():
        spine.set_color("#4b5563")

    buf = io.BytesIO()
    fig.tight_layout()
    fig.savefig(buf, format="png", bbox_inches="tight")
    plt.close(fig)
    buf.seek(0)
    image_bytes = buf.read()
    image_b64 = base64.b64encode(image_bytes).decode("ascii")

    return jsonify({"ok": True, "image_base64": image_b64})


@info_bp.route("/api/truss/calculate", methods=["POST"])
def api_truss_calculate():
    """Calculate truss, save results, and generate plot."""
    if not nodes or not elements:
        return jsonify({"ok": False, "errors": ["No truss data to calculate. Add nodes and elements first."]}), 400

    try:
        is_valid, error_msg = check_boundary_conditions(nodes)
        if not is_valid:
            return jsonify({"ok": False, "errors": [error_msg]}), 400

        dof = 2 * len(nodes)
        F = np.zeros(dof)
        for n in nodes:
            idx = 2 * (n.node_id - 1)
            F[idx] = n.loads.get("fx", 0.0)
            F[idx + 1] = n.loads.get("fy", 0.0)

        K = assemble_global_stiffness(nodes, elements)
        K_bc, F_bc = apply_boundary_conditions(K, F, nodes)
        d = solve_displacements(K_bc, F_bc)
        forces = compute_forces(elements, d)
        results = check_element_failure(elements, forces)

        displacements_data = []
        for i in range(0, len(d), 2):
            node_id = i // 2 + 1
            displacements_data.append({
                "node_id": node_id,
                "ux": float(d[i]),
                "uy": float(d[i + 1]),
            })

        forces_data = {}
        for eid, f_val in forces.items():
            forces_data[int(eid)] = {
                "force": float(f_val),
                "status": "Tension" if f_val > 0 else "Compression"
            }

        results_data = {}
        for eid, r in results.items():
            results_data[int(eid)] = {
                "force": float(r["force"]),
                "stress": float(r["stress"]),
                "status": r["status"]
            }

        elements_data = {}
        for elem in elements:
            elements_data[int(elem.element_id)] = {
                "node_i": elem.node_i.node_id,
                "node_j": elem.node_j.node_id,
                "area": float(elem.area),
                "material": elem.material.name,
                "length": float(elem.length()),
                "young_modulus": float(elem.material.E),
            }

        truss_results = {
            "displacements": displacements_data,
            "forces": forces_data,
            "element_results": results_data,
            "elements": elements_data,
        }
        
        with open(RESULTS_FILE, "w") as f:
            json.dump(truss_results, f, indent=2)

        plot_truss(nodes, elements, d, forces, scale=100, filepath=str(IMAGE_FILE))

        return jsonify({
            "ok": True,
            "message": "Truss calculated and results saved.",
            "image_path": str(IMAGE_FILE.relative_to(Path(__file__).parent.parent)),
        })

    except Exception as e:
        return jsonify({"ok": False, "errors": [f"Calculation error: {str(e)}"]}), 500


@info_bp.route("/api/truss/results", methods=["GET"])
def api_truss_results():
    """Get saved truss calculation results."""
    if not RESULTS_FILE.exists():
        return jsonify({"ok": False, "errors": ["No calculation results found."]}), 404
    
    try:
        with open(RESULTS_FILE, "r") as f:
            results = json.load(f)
        return jsonify({"ok": True, "results": results})
    except Exception as e:
        return jsonify({"ok": False, "errors": [f"Error reading results: {str(e)}"]}), 500


@info_bp.route("/api/truss/image", methods=["GET"])
def api_truss_image():
    """Serve the saved truss deformation image."""
    if not IMAGE_FILE.exists():
        return jsonify({"ok": False, "errors": ["No truss image found."]}), 404
    
    return send_from_directory(LOGIC_FOLDER, IMAGE_FILE.name)
