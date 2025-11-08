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
});
