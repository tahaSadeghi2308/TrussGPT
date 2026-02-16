(function () {
    const API_BASE = "";

    const state = {
        trussData: {
            nodes: [],
            elements: [],
            materials: [],
        },
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

    function formatTimestamp() {
        const now = new Date();
        return now.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    }

    function addMessage(content, type, showTimestamp = true) {
        const messagesContainer = $("#chat-messages");
        if (!messagesContainer) return;

        const messageDiv = document.createElement("div");
        messageDiv.className = "message " + type;

        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";

        if (typeof content === "string") {
            const p = document.createElement("p");
            p.textContent = content;
            contentDiv.appendChild(p);
        } else {
            contentDiv.appendChild(content);
        }

        messageDiv.appendChild(contentDiv);

        if (showTimestamp && type !== "system") {
            const timestamp = document.createElement("div");
            timestamp.className = "message-timestamp";
            timestamp.textContent = formatTimestamp();
            messageDiv.appendChild(timestamp);
        }

        messagesContainer.appendChild(messageDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function showTypingIndicator() {
        const messagesContainer = $("#chat-messages");
        if (!messagesContainer) return;

        const typingDiv = document.createElement("div");
        typingDiv.className = "message api";
        typingDiv.id = "typing-indicator";

        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content typing-indicator";
        contentDiv.innerHTML = "<span></span><span></span><span></span>";

        typingDiv.appendChild(contentDiv);
        messagesContainer.appendChild(typingDiv);
        messagesContainer.scrollTop = messagesContainer.scrollHeight;
    }

    function removeTypingIndicator() {
        const indicator = $("#typing-indicator");
        if (indicator) {
            indicator.remove();
        }
    }

    function updateTrussSummary() {
        const metricNodes = $("#metric-nodes");
        const metricElements = $("#metric-elements");
        const metricMaterials = $("#metric-materials");

        if (metricNodes) metricNodes.textContent = state.trussData.nodes.length.toString();
        if (metricElements) metricElements.textContent = state.trussData.elements.length.toString();
        if (metricMaterials) metricMaterials.textContent = state.trussData.materials.length.toString();
    }

    async function loadTrussData() {
        try {
            const res = await fetch(API_BASE + "/api/truss-data");
            if (!res.ok) throw new Error("Failed to load truss data");
            const data = await res.json();
            state.trussData.nodes = data.nodes || [];
            state.trussData.elements = data.elements || [];
            state.trussData.materials = data.materials || [];
            updateTrussSummary();
        } catch (err) {
            console.error("Failed to load truss data:", err);
        }
    }

    async function sendMessage(message) {
        const chatInput = $("#chat-input");
        const sendBtn = $("#send-btn");
        const statusEl = $("#chat-status");

        if (!message || !message.trim()) {
            setStatus(statusEl, "error", "Please enter a message.");
            return;
        }

        chatInput.disabled = true;
        sendBtn.disabled = true;
        setStatus(statusEl, "success", "");

        addMessage(message, "user");

        showTypingIndicator();

        try {
            const res = await fetch(API_BASE + "/api/chat/req", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message }),
            });

            removeTypingIndicator();

            const data = await res.json();

            if (!res.ok || !data.ok) {
                const errorMsg = (data && data.errors) ? data.errors.join(" ") : "Failed to get response from server.";
                addMessage("Error: " + errorMsg, "api");
                setStatus(statusEl, "error", "Could not send message.");
                return;
            }

            const responseText = data.response || "No response received.";
            addMessage(responseText, "api");
            setStatus(statusEl, "success", "");

        } catch (err) {
            console.error("Error sending message:", err);
            removeTypingIndicator();
            addMessage("Error: Could not connect to server. Please try again.", "api");
            setStatus(statusEl, "error", "Network error occurred.");
        } finally {
            chatInput.disabled = false;
            sendBtn.disabled = false;
            chatInput.focus();
        }
    }

    function setupChatForm() {
        const chatForm = $("#chat-form");
        const chatInput = $("#chat-input");

        if (!chatForm || !chatInput) return;

        chatForm.addEventListener("submit", async (event) => {
            event.preventDefault();
            const message = chatInput.value.trim();
            if (!message) return;

            chatInput.value = "";
            await sendMessage(message);
        });

        chatInput.addEventListener("keydown", (event) => {
            if (event.key === "Enter" && !event.shiftKey) {
                event.preventDefault();
                chatForm.dispatchEvent(new Event("submit"));
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupChatForm();
        loadTrussData();
        const chatInput = $("#chat-input");
        if (chatInput) {
            chatInput.focus();
        }
    });
})();

