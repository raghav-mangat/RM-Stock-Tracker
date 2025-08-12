// Footer Year
document.getElementById("currentYear").textContent = new Date().getFullYear();

// Initialize Bootstrap Popovers
const popoverTriggerList = [].slice.call(
  document.querySelectorAll('[data-bs-toggle="popover"]')
);
popoverTriggerList.forEach(
  (popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl)
);

// Spinner Overlay
const spinner = document.getElementById("page-loading-spinner");
const spinnerDelay = 200; // delay before showing spinner (in ms)
let spinnerTimeout;

window.addEventListener("beforeunload", () => {
  spinnerTimeout = setTimeout(
    () => spinner.classList.remove("d-none"),
    spinnerDelay
  );
});

window.addEventListener("pageshow", () => {
  clearTimeout(spinnerTimeout);
  spinner.classList.add("d-none");
});
