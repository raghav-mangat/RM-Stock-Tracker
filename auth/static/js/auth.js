document.addEventListener("DOMContentLoaded", () => {
  // Remove the error when the user starts typing on an input
  allInputs = document.querySelectorAll(".form-control");
  allInputs.forEach((input) => {
    input.addEventListener("input", () => {
      const inputError = document.getElementById(`error-${input.id}`);
      if (inputError) {
        inputError.remove();
      }
    });
  });

  // Add the password field functionality if the field exists
  const passwordField = document.getElementById("password");
  if (passwordField) {
    passwordFieldFunctionality(passwordField);
  }
});

function passwordFieldFunctionality(passwordField) {
  const reqBox = document.getElementById("password-requirements");
  if (!reqBox) return;

  const specialCharRegex = PASSWORD_POLICY.require_special
    ? new RegExp(PASSWORD_POLICY.special_chars_regex)
    : null;

  const reqList = {
    "pw-length": (value) =>
      value.length >= PASSWORD_POLICY.min_length &&
      value.length <= PASSWORD_POLICY.max_length,

    "pw-upper": (value) =>
      !PASSWORD_POLICY.require_upper || /[A-Z]/.test(value),

    "pw-lower": (value) =>
      !PASSWORD_POLICY.require_lower || /[a-z]/.test(value),

    "pw-number": (value) =>
      !PASSWORD_POLICY.require_number || /[0-9]/.test(value),

    "pw-special": (value) =>
      !PASSWORD_POLICY.require_special || specialCharRegex.test(value),
  };

  passwordField.addEventListener("input", () => {
    const value = passwordField.value;

    if (value.length > 0) {
      reqBox.classList.remove("d-none");
    } else {
      reqBox.classList.add("d-none");
    }

    for (const id in reqList) {
      const li = document.getElementById(id);
      if (!li) continue;

      const valid = reqList[id](value);
      updateRequirement(li, valid);
    }
  });

  function updateRequirement(li, condition) {
    const icon = li.querySelector("i");

    li.classList.toggle("text-success", condition);
    li.classList.toggle("text-danger", !condition);

    icon.classList.toggle("bi-check-circle-fill", condition);
    icon.classList.toggle("bi-x-circle-fill", !condition);
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
}
