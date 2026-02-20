document.addEventListener("DOMContentLoaded", function () {
    var passwordInput = document.getElementById("password");
    var togglePassword = document.getElementById("toggle-password");
    var emailInput = document.getElementById("email");
    if (togglePassword && passwordInput) {
        togglePassword.addEventListener("click", function () {
            var type = passwordInput.getAttribute("type") === "password" ? "text" : "password";
            passwordInput.setAttribute("type", type);
            togglePassword.textContent = type === "password" ? "Show" : "Hide";
        });
    }
    if (emailInput) {
        emailInput.focus();
    }
    var form = document.getElementById("login-form");
    var submitButton = document.getElementById("login-submit");
    if (form && submitButton) {
        form.addEventListener("submit", function (event) {
            event.preventDefault();
        });
    }
});