from flask import Flask, render_template, request, jsonify

from app.logic.models import Node, Element
from app.logic.truss_data import materials, nodes, elements

app = Flask(__name__)

@app.route('/')
def index():
    return render_template("index.html")

@app.route('/truss-info')
def truss_info():
    return render_template("truss_info.html")


@app.route("/api/truss-data", methods=["GET"])
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


@app.route("/api/nodes", methods=["POST"])
def api_add_node():
    """Add a new node with coordinates and restraints."""
    data = request.get_json(silent=True) or {}
    errors = []

    # Validate coordinates
    try:
        x = float(data.get("x", ""))
    except (TypeError, ValueError):
        errors.append("x must be a floating point number.")

    try:
        y = float(data.get("y", ""))
    except (TypeError, ValueError):
        errors.append("y must be a floating point number.")

    # Validate restraints (treat anything truthy == True)
    ux = bool(data.get("ux", False))
    uy = bool(data.get("uy", False))

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

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


@app.route("/api/elements", methods=["POST"])
def api_add_element():
    """Add a new element between two nodes with a selected material.

    Area is currently fixed to 1.0 for simplicity.
    """
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

    if errors:
        return jsonify({"ok": False, "errors": errors}), 400

    element_id = (max((e.element_id for e in elements), default=0) + 1) if elements else 1
    material = materials[material_name]
    area = 1.0
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


@app.route("/api/loads", methods=["POST"])
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

@app.route("/chat")
def chat():
    pass

if __name__== "__main__":
    app.run(debug=True)