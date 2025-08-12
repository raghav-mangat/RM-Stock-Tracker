// Footer Year
document.getElementById("currentYear").textContent = new Date().getFullYear();

// Initialize Bootstrap Popovers
const popoverTriggerList = [].slice.call(
  document.querySelectorAll('[data-bs-toggle="popover"]')
);
popoverTriggerList.forEach(
  (popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl)
);

// Page Loading Spinner Overlay
const pageSpinner = document.getElementById("page-loading-spinner");
const pageSpinnerDelay = 200; // delay before showing page loading spinner (in ms)
let pageSpinnerTimeout;

// Show page loading spinner after delay
function startSpinnerTimer() {
  pageSpinnerTimeout = setTimeout(() => {
    pageSpinner.classList.remove("d-none");
  }, pageSpinnerDelay);
}

// Stop page loading spinner
function stopSpinnerTimer() {
  clearTimeout(pageSpinnerTimeout);
  pageSpinner.classList.add("d-none");
}

// Show page loading spinner when page is loading
window.addEventListener("beforeunload", startSpinnerTimer);

// Clear page loading spinner when page is shown again
window.addEventListener("pageshow", stopSpinnerTimer);
