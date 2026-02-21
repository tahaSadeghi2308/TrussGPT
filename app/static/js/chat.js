(function () {
    const API_BASE = "";
    const STORAGE_KEY = "trussgpt_chat_history_v1";

    const state = {
        trussData: {
            nodes: [],
            elements: [],
            materials: [],
        },
        conversation: [],
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

    function renderMarkdown(mdText) {
        let processedText = renderLatex(mdText);
        const rawHtml = marked.parse(processedText);
        const cleanHtml = DOMPurify.sanitize(rawHtml);
        return cleanHtml;
    }

    function renderLatex(text) {
        if (typeof katex === 'undefined') {
            return text;
        }
        
        text = text.replace(/\$\$([\s\S]*?)\$\$/g, function(match, latex) {
            try {
                return katex.renderToString(latex.trim(), {
                    displayMode: true,
                    throwOnError: false,
                    output: 'html'
                });
            } catch (e) {
                return match;
            }
        });
        
        text = text.replace(/\$([^\$\n]+?)\$/g, function(match, latex) {
            try {
                return katex.renderToString(latex.trim(), {
                    displayMode: false,
                    throwOnError: false,
                    output: 'html'
                });
            } catch (e) {
                return match;
            }
        });
        
        text = text.replace(/\\\(([\s\S]*?)\\\)/g, function(match, latex) {
            try {
                return katex.renderToString(latex.trim(), {
                    displayMode: false,
                    throwOnError: false,
                    output: 'html'
                });
            } catch (e) {
                return match;
            }
        });
        
        text = text.replace(/\\\[([\s\S]*?)\\\]/g, function(match, latex) {
            try {
                return katex.renderToString(latex.trim(), {
                    displayMode: true,
                    throwOnError: false,
                    output: 'html'
                });
            } catch (e) {
                return match;
            }
        });
        
        return text;
    }

    function addMessage(content, type, showTimestamp = true) {
        const messagesContainer = $("#chat-messages");
        if (!messagesContainer) return;

        const messageDiv = document.createElement("div");
        messageDiv.className = "message " + type;

        const contentDiv = document.createElement("div");
        contentDiv.className = "message-content";

        if (typeof content === "string") {
            contentDiv.innerHTML = renderMarkdown(content);
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

    function saveConversation() {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(state.conversation));
        } catch (e) {}
    }

    function loadConversation() {
        try {
            const raw = localStorage.getItem(STORAGE_KEY);
            if (!raw) return;
            const parsed = JSON.parse(raw);
            if (Array.isArray(parsed)) {
                state.conversation = parsed
                    .filter(m => m && (m.role === "user" || m.role === "assistant") && typeof m.content === "string")
                    .slice(-40);
            }
        } catch (e) {
            state.conversation = [];
        }
    }

    function renderConversation() {
        const messagesContainer = $("#chat-messages");
        if (!messagesContainer) return;
        messagesContainer.innerHTML = "";

        const systemDiv = document.createElement("div");
        systemDiv.className = "message system";
        const systemContent = document.createElement("div");
        systemContent.className = "message-content";
        const p = document.createElement("p");
        p.textContent = "Welcome! Start a conversation about your truss model.";
        systemContent.appendChild(p);
        systemDiv.appendChild(systemContent);
        messagesContainer.appendChild(systemDiv);

        for (const m of state.conversation) {
            if (m.role === "user") {
                addMessage(m.content, "user");
            } else if (m.role === "assistant") {
                addMessage(m.content, "api");
            }
        }
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

        // Send prior chat history along with the current message
        const historyToSend = state.conversation.slice(-20);

        addMessage(message, "user");
        state.conversation.push({ role: "user", content: message });
        saveConversation();

        showTypingIndicator();

        try {
            const res = await fetch(API_BASE + "/api/chat/req", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ message: message, history: historyToSend }),
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
            
            // If there's an image URL, add it to the message
            if (data.image_url) {
                const messageDiv = document.createElement("div");
                messageDiv.className = "message api";
                
                const contentDiv = document.createElement("div");
                contentDiv.className = "message-content";
                
                // Use innerHTML with renderMarkdown to properly render LaTeX and markdown
                const textDiv = document.createElement("div");
                textDiv.innerHTML = renderMarkdown(responseText);
                contentDiv.appendChild(textDiv);
                
                // Add image if URL is provided
                const imgLink = document.createElement("a");
                imgLink.href = data.image_url;
                imgLink.target = "_blank";
                imgLink.textContent = "View Truss Image";
                imgLink.style.color = "var(--accent)";
                imgLink.style.textDecoration = "underline";
                imgLink.style.marginTop = "8px";
                imgLink.style.display = "inline-block";
                contentDiv.appendChild(imgLink);
                
                messageDiv.appendChild(contentDiv);
                
                const timestamp = document.createElement("div");
                timestamp.className = "message-timestamp";
                timestamp.textContent = formatTimestamp();
                messageDiv.appendChild(timestamp);
                
                const messagesContainer = $("#chat-messages");
                if (messagesContainer) {
                    messagesContainer.appendChild(messageDiv);
                    messagesContainer.scrollTop = messagesContainer.scrollHeight;
                }
            } else {
                addMessage(responseText, "api");
            }

            state.conversation.push({ role: "assistant", content: responseText });
            saveConversation();
            
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

    function setupLogout() {
        const logoutBtn = $("#logout-btn");
        if (!logoutBtn) return;

        logoutBtn.addEventListener("click", async function() {
            if (!confirm("Are you sure you want to logout? This will reset all project data.")) {
                return;
            }

            logoutBtn.disabled = true;
            logoutBtn.textContent = "Logging out...";

            try {
                const response = await fetch("/api/logout", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" }
                });

                const data = await response.json();

                if (response.ok && data.ok) {
                    localStorage.removeItem(STORAGE_KEY);
                    window.location.href = "/login";
                } else {
                    alert("Logout failed. Please try again.");
                    logoutBtn.disabled = false;
                    logoutBtn.textContent = "Logout";
                }
            } catch (error) {
                console.error("Logout error:", error);
                alert("Network error during logout. Please try again.");
                logoutBtn.disabled = false;
                logoutBtn.textContent = "Logout";
            }
        });
    }

    document.addEventListener("DOMContentLoaded", () => {
        setupChatForm();
        setupLogout();
        loadTrussData();
        loadConversation();
        renderConversation();
        const chatInput = $("#chat-input");
        if (chatInput) {
            chatInput.focus();
        }
    });
})();

