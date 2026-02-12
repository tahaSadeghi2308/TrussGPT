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

    function setupGlobalActions() {
        const btnClear = $("#btn-clear-truss");
        const btnShowVisual = $("#btn-show-visual");
        const btnGoChat = $("#btn-go-chat");
        const modal = $("#visual-modal");
        const modalClose = $("#modal-close");
        const modalStatus = $("#modal-visual-status");
        const img = $("#truss-image");

        if (btnClear) {
            btnClear.addEventListener("click", async () => {
                if (!confirm("This will delete all nodes and elements in the current truss. Continue?")) {
                    return;
                }
                try {
                    const res = await fetch(API_BASE + "/api/truss/clear", {
                        method: "POST",
                    });
                    const data = await res.json();
                    if (!res.ok || !data.ok) {
                        appendLog("Failed to clear truss data.");
                        return;
                    }
                    state.nodes = [];
                    state.elements = [];
                    updateSummary();
                    await loadTrussData();
                    appendLog("Cleared all truss data.");
                } catch (err) {
                    console.error(err);
                    appendLog("Unexpected error while clearing truss data.");
                }
            });
        }

        function openModal() {
            if (modal) {
                modal.classList.add("visible");
                modal.setAttribute("aria-hidden", "false");
            }
        }

        function closeModal() {
            if (modal) {
                modal.classList.remove("visible");
                modal.setAttribute("aria-hidden", "true");
            }
            if (modalStatus) {
                modalStatus.classList.remove("success", "error", "visible");
                modalStatus.textContent = "";
            }
        }

        if (modalClose) {
            modalClose.addEventListener("click", () => {
                closeModal();
            });
        }

        if (modal) {
            modal.addEventListener("click", (event) => {
                if (event.target === modal) {
                    closeModal();
                }
            });
        }

        if (btnShowVisual) {
            btnShowVisual.addEventListener("click", async () => {
                openModal();
                setStatus(modalStatus, "success", "Rendering truss...");
                try {
                    const res = await fetch(API_BASE + "/api/truss/plot");
                    const data = await res.json();
                    if (!res.ok || !data.ok) {
                        const errors = (data && data.errors) ? data.errors.join(" ") : "Could not render truss.";
                        setStatus(modalStatus, "error", errors);
                        appendLog("Failed to render truss.");
                        if (img) img.removeAttribute("src");
                        return;
                    }
                    if (img) {
                        img.src = "data:image/png;base64," + data.image_base64;
                    }
                    setStatus(modalStatus, "success", "Truss rendered.");
                    appendLog("Rendered truss visualization.");
                } catch (err) {
                    console.error(err);
                    setStatus(modalStatus, "error", "Unexpected error while rendering truss.");
                    appendLog("Unexpected error while rendering truss.");
                }
            });
        }

        function isTrussConnected() {
            if (!state.nodes.length || !state.elements.length) {
                return false;
            }

            const adj = new Map();
            for (const n of state.nodes) {
                adj.set(n.node_id, []);
            }

            for (const e of state.elements) {
                const i = e.node_i;
                const j = e.node_j;
                if (!adj.has(i) || !adj.has(j)) {
                    continue;
                }
                adj.get(i).push(j);
                adj.get(j).push(i);
            }

            // All nodes must be connected to at least one element
            for (const n of state.nodes) {
                const neighbors = adj.get(n.node_id) || [];
                if (!neighbors.length) {
                    return false;
                }
            }

            const visited = new Set();
            const queue = [];
            const startId = state.nodes[0].node_id;
            visited.add(startId);
            queue.push(startId);

            while (queue.length) {
                const current = queue.shift();
                const neighbors = adj.get(current) || [];
                for (const nb of neighbors) {
                    if (!visited.has(nb)) {
                        visited.add(nb);
                        queue.push(nb);
                    }
                }
            }

            return visited.size === state.nodes.length;
        }

        if (btnGoChat) {
            btnGoChat.addEventListener("click", () => {
                if (!isTrussConnected()) {
                    alert("Your truss is not valid. The graph is not fully connected or some nodes are isolated. Please correct it before going to chat.");
                    appendLog("Blocked navigation to chat because truss is not connected.");
                    return;
                }
                window.location.href = "/chat";
            });
        }
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupTabs();
        setupForms();
        setupGlobalActions();
        loadTrussData();
    });
})();


