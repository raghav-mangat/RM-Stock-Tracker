// Initialize the Bootstrap Popovers for the entire document
document.addEventListener("DOMContentLoaded", () => {
  initializeBSPopovers(document);
});

// To auto-show and auto-remove all toasts
document.addEventListener("DOMContentLoaded", () => {
  const toastElList = [].slice.call(document.querySelectorAll(".toast"));
  toastElList.map((toastEl) => new bootstrap.Toast(toastEl).show());
  toastElList.map((toastEl) =>
    toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove()),
  );
});

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

function initializeBSPopovers(content) {
  // Initialize Bootstrap Popovers
  const popoverTriggerList = [].slice.call(
    content.querySelectorAll('[data-bs-toggle="popover"]'),
  );
  popoverTriggerList.forEach(
    (popoverTriggerEl) => new bootstrap.Popover(popoverTriggerEl),
  );
}

// Clear the session storage on logout
document.addEventListener("DOMContentLoaded", () => {
  const logoutLink = document.getElementById("logout-link");

  if (!logoutLink) return;

  logoutLink.addEventListener("click", () => {
    // Clear only auth-scoped UI state

    sessionStorage.removeItem("rm_watchlist_open_accordions");

    // If we later add more auth-scoped keys, clear them here too
  });
});
