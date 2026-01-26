document.addEventListener("DOMContentLoaded", () => {
  // Remove field error on input
  document.querySelectorAll(".form-control").forEach((input) => {
    input.addEventListener("input", () => {
      const error = document.getElementById(`error-${input.id}`);
      if (error) error.remove();
    });
  });

  // Initialize all password groups
  document.querySelectorAll(".password-field-group").forEach(initPasswordGroup);
});

function initPasswordGroup(group) {
  const passwordInput = group.querySelector(".password-input");
  const toggleBtn = group.querySelector(".toggle-password");
  const reqBox = group.querySelector(".password-requirements");

  if (!passwordInput || !toggleBtn) return;

  // Find confirm password next to this group
  const confirmInput = findAdjacentConfirmPassword(group);

  // Toggle visibility
  toggleBtn.addEventListener("click", () => {
    const isHidden = passwordInput.type === "password";
    const newType = isHidden ? "text" : "password";

    passwordInput.type = newType;
    if (confirmInput) confirmInput.type = newType;

    const icon = toggleBtn.querySelector("i");
    icon.classList.toggle("bi-eye", isHidden);
    icon.classList.toggle("bi-eye-slash", !isHidden);

    passwordInput.focus();
  });

  // Requirements logic
  if (!reqBox) return;

  const requirements = {
    length: (value) =>
      value.length >= PASSWORD_POLICY.min_length &&
      value.length <= PASSWORD_POLICY.max_length,

    upper: (value) => !PASSWORD_POLICY.require_upper || /[A-Z]/.test(value),

    lower: (value) => !PASSWORD_POLICY.require_lower || /[a-z]/.test(value),

    number: (value) => !PASSWORD_POLICY.require_number || /[0-9]/.test(value),

    special: (value) =>
      !PASSWORD_POLICY.require_special ||
      new RegExp(PASSWORD_POLICY.special_chars_regex).test(value),
  };

  passwordInput.addEventListener("input", () => {
    const value = passwordInput.value;
    reqBox.classList.toggle("d-none", value.length === 0);

    reqBox.querySelectorAll("[data-requirement]").forEach((li) => {
      const rule = li.dataset.requirement;
      const valid = requirements[rule]?.(value);
      updateRequirement(li, valid);
    });
  });
}

function updateRequirement(li, valid) {
  const icon = li.querySelector("i");

  li.classList.toggle("text-success", valid);
  li.classList.toggle("text-danger", !valid);

  icon.classList.toggle("bi-check-circle-fill", valid);
  icon.classList.toggle("bi-x-circle-fill", !valid);
}

// Looks for confirm password field next to this password group
function findAdjacentConfirmPassword(group) {
  let el = group.nextElementSibling;
  if (!el) return null;

  return el.querySelector("input[type='password'], input[type='text']");
}
