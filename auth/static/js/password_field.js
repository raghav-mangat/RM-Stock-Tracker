document.addEventListener("DOMContentLoaded", () => {
  const passwordField = document.getElementById("password");
  if (!passwordField) {
    return;
  }

  const reqBox = document.getElementById("password-requirements");
  if (reqBox) {
    const reqList = {
      "pw-length": (value) => value.length >= 8,
      "pw-upper": (value) => /[A-Z]/.test(value),
      "pw-lower": (value) => /[a-z]/.test(value),
      "pw-number": (value) => /[0-9]/.test(value),
      "pw-special": (value) =>
        /[!@#$%^&*()_\-+=|\\{}\[\]:;\"'<>,.?/~` ]/.test(value),
    };

    passwordField.addEventListener("input", () => {
      const value = passwordField.value;
      if (value.length > 0) {
        reqBox.classList.remove("d-none");
      } else {
        reqBox.classList.add("d-none");
      }

      for (const id in reqList) {
        const valid = reqList[id](value);
        updateRequirement(id, valid);
      }
    });

    function updateRequirement(id, condition) {
      const li = document.getElementById(id);
      const icon = li.querySelector("i");

      li.classList.toggle("text-success", condition);
      li.classList.toggle("text-danger", !condition);

      icon.classList.toggle("bi-check-circle-fill", condition);
      icon.classList.toggle("bi-x-circle-fill", !condition);
    }
  }

  // Password visibility toggle
  const toggleBtn = document.getElementById("toggle-password");
  if (toggleBtn) {
    const toggleIcon = toggleBtn.querySelector("i");
    toggleBtn.addEventListener("click", () => {
      const isHidden = passwordField.type === "password";
      passwordField.type = isHidden ? "text" : "password";
      toggleIcon.classList.toggle("bi-eye");
      toggleIcon.classList.toggle("bi-eye-slash");
      passwordField.focus();
    });
  }
});
