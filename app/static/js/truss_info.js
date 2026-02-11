(function () {
    const API_BASE = "";

    const state = {
        nodes: [],
        elements: [],
        materials: [],
    };

    function $(selector) {
        return document.querySelector(selector);
    }

    function setStatus(el, type, message) {
        if (!el) return;
        el.classList.remove("success", "error", "visible");
        if (!message) return;
        el.classList.add(type, "visible");
        const label = type === "success" ? "Success" : "Error";
        el.innerHTML = "<span class=\"label\">" + label + ":</span>" + message;
    }

    function updateSummary() {
        const metricNodes = $("#metric-nodes");
        const metricElements = $("#metric-elements");
        const metricMaterials = $("#metric-materials");
        if (metricNodes) metricNodes.textContent = state.nodes.length.toString();
        if (metricElements) metricElements.textContent = state.elements.length.toString();
        if (metricMaterials) metricMaterials.textContent = state.materials.length.toString();
    }

    function appendLog(message) {
        const log = $("#summary-log");
        if (!log) return;
        const li = document.createElement("li");
        const timestamp = new Date().toLocaleTimeString();
        li.textContent = "[" + timestamp + "] " + message;
        log.insertBefore(li, log.firstChild);
        const items = log.querySelectorAll("li");
        const maxItems = 16;
        if (items.length > maxItems) {
            for (let i = maxItems; i < items.length; i++) {
                items[i].remove();
            }
        }
    }

    function populateSelect(select, options, placeholder) {
        if (!select) return;
        select.innerHTML = "";
        if (placeholder) {
            const ph = document.createElement("option");
            ph.disabled = true;
            ph.selected = true;
            ph.value = "";
            ph.textContent = placeholder;
            select.appendChild(ph);
        }
        for (const opt of options) {
            const o = document.createElement("option");
            o.value = opt.value;
            o.textContent = opt.label;
            select.appendChild(o);
        }
    }

    async function loadTrussData() {
        try {
            const res = await fetch(API_BASE + "/api/truss-data");
            if (!res.ok) throw new Error("Failed to load truss data");
            const data = await res.json();
            state.nodes = data.nodes || [];
            state.elements = data.elements || [];
            state.materials = data.materials || [];

            updateSummary();

            const nodeOptions = state.nodes.map(n => ({
                value: String(n.node_id),
                label: "Node " + n.node_id + " (" + n.x + ", " + n.y + ")",
            }));

            populateSelect($("#element-node-i"), nodeOptions, nodeOptions.length ? "Select node i" : "No nodes yet");
            populateSelect($("#element-node-j"), nodeOptions, nodeOptions.length ? "Select node j" : "No nodes yet");
            populateSelect($("#load-node"), nodeOptions, nodeOptions.length ? "Select node" : "No nodes yet");

            const materialOptions = state.materials.map(name => ({
                value: name,
                label: name,
            }));
            populateSelect($("#element-material"), materialOptions, materialOptions.length ? "Select material" : "No materials");
        } catch (err) {
            console.error(err);
            appendLog("Could not load current truss data.");
        }
    }

    function setupTabs() {
        const tabs = document.querySelectorAll("#mode-tabs button");
        const panels = document.querySelectorAll(".panel[data-panel]");
        tabs.forEach(btn => {
            btn.addEventListener("click", () => {
                const mode = btn.getAttribute("data-mode");
                tabs.forEach(b => b.classList.toggle("active", b === btn));
                panels.forEach(p => {
                    p.style.display = p.getAttribute("data-panel") === mode ? "" : "none";
                });
            });
        });
    }

    function setupForms() {
        const formAddNode = $("#form-add-node");
        const formAddElement = $("#form-add-element");
        const formAddLoad = $("#form-add-load");

        const statusAddNode = $("#status-add-node");
        const statusAddElement = $("#status-add-element");
        const statusAddLoad = $("#status-add-load");

        if (formAddNode) {
            formAddNode.addEventListener("submit", async (event) => {
                event.preventDefault();
                setStatus(statusAddNode, "success", "");
                setStatus(statusAddNode, "error", "");
                const formData = new FormData(formAddNode);
                const payload = {
                    x: formData.get("x"),
                    y: formData.get("y"),
                    ux: formData.get("ux") !== null,
                    uy: formData.get("uy") !== null,
                };
                try {
                    const res = await fetch(API_BASE + "/api/nodes", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    const data = await res.json();
                    if (!res.ok || !data.ok) {
                        const errors = (data && data.errors) ? data.errors.join(" ") : "Could not add node.";
                        setStatus(statusAddNode, "error", errors);
                        appendLog("Failed to add node.");
                        return;
                    }
                    state.nodes.push(data.node);
                    updateSummary();
                    await loadTrussData();
                    formAddNode.reset();
                    setStatus(statusAddNode, "success", "Node " + data.node.node_id + " added.");
                    appendLog("Added node " + data.node.node_id + " at (" + data.node.x + ", " + data.node.y + ").");
                } catch (err) {
                    console.error(err);
                    setStatus(statusAddNode, "error", "Unexpected error while adding node.");
                    appendLog("Unexpected error while adding node.");
                }
            });
        }

        if (formAddElement) {
            formAddElement.addEventListener("submit", async (event) => {
                event.preventDefault();
                setStatus(statusAddElement, "success", "");
                setStatus(statusAddElement, "error", "");
                const formData = new FormData(formAddElement);
                const payload = {
                    node_i_id: formData.get("node_i_id"),
                    node_j_id: formData.get("node_j_id"),
                    material: formData.get("material"),
                };
                if (!payload.node_i_id || !payload.node_j_id || !payload.material) {
                    setStatus(statusAddElement, "error", "Please choose both nodes and a material.");
                    return;
                }
                try {
                    const res = await fetch(API_BASE + "/api/elements", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    const data = await res.json();
                    if (!res.ok || !data.ok) {
                        const errors = (data && data.errors) ? data.errors.join(" ") : "Could not add element.";
                        setStatus(statusAddElement, "error", errors);
                        appendLog("Failed to add element.");
                        return;
                    }
                    state.elements.push(data.element);
                    updateSummary();
                    await loadTrussData();
                    formAddElement.reset();
                    setStatus(statusAddElement, "success", "Element " + data.element.element_id + " added.");
                    appendLog("Added element " + data.element.element_id + " between nodes " + data.element.node_i + " and " + data.element.node_j + ".");
                } catch (err) {
                    console.error(err);
                    setStatus(statusAddElement, "error", "Unexpected error while adding element.");
                    appendLog("Unexpected error while adding element.");
                }
            });
        }

        if (formAddLoad) {
            formAddLoad.addEventListener("submit", async (event) => {
                event.preventDefault();
                setStatus(statusAddLoad, "success", "");
                setStatus(statusAddLoad, "error", "");
                const formData = new FormData(formAddLoad);
                const payload = {
                    node_id: formData.get("node_id"),
                    fx: formData.get("fx"),
                    fy: formData.get("fy"),
                };
                if (!payload.node_id) {
                    setStatus(statusAddLoad, "error", "Please select a node for the load.");
                    return;
                }
                try {
                    const res = await fetch(API_BASE + "/api/loads", {
                        method: "POST",
                        headers: { "Content-Type": "application/json" },
                        body: JSON.stringify(payload),
                    });
                    const data = await res.json();
                    if (!res.ok || !data.ok) {
                        const errors = (data && data.errors) ? data.errors.join(" ") : "Could not add load.";
                        setStatus(statusAddLoad, "error", errors);
                        appendLog("Failed to add load.");
                        return;
                    }
                    const idx = state.nodes.findIndex(n => n.node_id === data.node.node_id);
                    if (idx >= 0) {
                        state.nodes[idx] = data.node;
                    } else {
                        state.nodes.push(data.node);
                    }
                    updateSummary();
                    await loadTrussData();
                    formAddLoad.reset();
                    setStatus(statusAddLoad, "success", "Load applied to node " + data.node.node_id + ".");
                    appendLog("Applied load to node " + data.node.node_id + " (Fx=" + data.node.fx + ", Fy=" + data.node.fy + ").");
                } catch (err) {
                    console.error(err);
                    setStatus(statusAddLoad, "error", "Unexpected error while adding load.");
                    appendLog("Unexpected error while adding load.");
                }
            });
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupTabs();
        setupForms();
        loadTrussData();
    });
})();


