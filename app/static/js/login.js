document.addEventListener("DOMContentLoaded", function () {
    var passwordInput = document.getElementById("password");
    var togglePassword = document.getElementById("toggle-password");
    var usernameInput = document.getElementById("username");
    var form = document.getElementById("login-form");
    var submitButton = document.getElementById("login-submit");
    
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener("click", function () {
            var type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
            passwordInput.setAttribute("type", type);
            togglePassword.textContent = type === "password" ? "Show" : "Hide";
        });
    }
    
    if (usernameInput) {
        usernameInput.focus();
    }
    
    if (form && submitButton) {
        form.addEventListener("submit", async function (event) {
            event.preventDefault();
            var username = usernameInput.value.trim();
            var password = passwordInput.value.trim();
            
            if (!username || !password) {
                alert("Please enter both username and password.");
                return;
            }
            
            submitButton.disabled = true;
            submitButton.textContent = "Signing in...";
            
            try {
                var response = await fetch("/api/login", {
                    method: "POST",
                    headers: { "Content-Type": "application/json" },
                    body: JSON.stringify({ username: username, password: password })
                });
                
                if (!response.ok && response.status === 302) {
                    alert("Server redirected. Check if /api/login endpoint is accessible.");
                    submitButton.disabled = false;
                    submitButton.textContent = "Sign in";
                    return;
                }
                
                var contentType = response.headers.get("content-type");
                if (!contentType || !contentType.includes("application/json")) {
                    var text = await response.text();
                    console.error("Non-JSON response:", text);
                    alert("Server returned invalid response. Check console for details.");
                    submitButton.disabled = false;
                    submitButton.textContent = "Sign in";
                    return;
                }
                
                var data = await response.json();
                
                if (response.ok && data.ok) {
                    localStorage.removeItem("trussgpt_chat_history_v1");
                    window.location.href = "/";
                } else {
                    var errorMsg = data.errors ? data.errors.join(" ") : "Login failed. Please try again.";
                    alert(errorMsg);
                    submitButton.disabled = false;
                    submitButton.textContent = "Sign in";
                }
            } catch (error) {
                console.error("Login error:", error);
                alert("Network error: " + error.message);
                submitButton.disabled = false;
                submitButton.textContent = "Sign in";
            }
        });
    }
});