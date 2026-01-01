/**
 * folder_actions.js
 *
 * Handles all folder-level AJAX form submissions.
 */

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

// Delay (ms) before showing spinner to avoid flicker on fast responses
const FOLDER_SPINNER_OVERLAY_DELAY = 300;

// Duration (ms) of fade-out before swapping folder HTML
const FOLDER_FADE_TRANSITION_DURATION = 150;

// Delay (ms) before the bootstrap toasts automatically get dismissed
const TOAST_DISMISS_DELAY = 5000;

/* -------------------------------------------------------------------------- */
/* Form Submission Handler                                                    */
/* -------------------------------------------------------------------------- */

document.addEventListener("submit", async (event) => {
  const form = event.target;

  // Only intercept AJAX-enabled folder action forms
  if (!form.classList.contains("folder-action-form")) return;

  event.preventDefault();

  const folderId = form.dataset.folderId;

  // Get DOM references for the affected folder
  const headerContainer = document.getElementById(
    `accordion-header-${folderId}`
  );
  const bodyContainer = document.getElementById(`accordion-body-${folderId}`);
  const overlay = document.getElementById(`folder-loading-spinner-${folderId}`);

  // Abort safely if folder DOM no longer exists
  if (!headerContainer || !bodyContainer || !overlay) return;

  /* ---------------------------------------------------------------------- */
  /* Delayed Loading Overlay                                                */
  /* ---------------------------------------------------------------------- */

  // Show spinner only if request takes longer than the delay
  const overlayTimeoutId = setTimeout(() => {
    overlay.classList.remove("d-none");
    // prevent interaction while loading
    bodyContainer.classList.add("pe-none");
  }, FOLDER_SPINNER_OVERLAY_DELAY);

  try {
    /* ------------------------------------------------------------------ */
    /* Build FormData                                                     */
    /* ------------------------------------------------------------------ */

    // Collect form fields
    const formData = new FormData(form);

    // Include the submit button that triggered the request (AJAX-safe)
    if (event.submitter?.name) {
      formData.append(event.submitter.name, event.submitter.value);
    }

    /* ------------------------------------------------------------------ */
    /* POST request                                                       */
    /* ------------------------------------------------------------------ */

    // Execute folder action (add, remove, update, etc.)
    const actionResponse = await fetch(form.action, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      body: formData,
    });

    const actionData = await actionResponse.json();

    // Stop early if server-side validation or logic failed
    if (!actionResponse.ok) {
      showToast(
        actionData.message || "Action failed",
        actionData.category || "danger"
      );
      return;
    }

    /* ------------------------------------------------------------------ */
    /* Close interaction UI immediately                                   */
    /* ------------------------------------------------------------------ */

    // Remove modals, dropdowns, or offcanvas panels tied to this action
    closeBootstrapComponents([
      { type: "modal", selector: "#filterFolderModal" },
      { type: "modal", selector: "#addStockModal" },
      {
        type: "dropdown",
        selector: `#edit-folder-attributes-button-${folderId}`,
      },
      {
        type: "offcanvas",
        selector: `.alert-offcanvas-in-folder-${folderId}`,
        multiple: true,
      },
    ]);

    /* ------------------------------------------------------------------ */
    /* Fetch updated folder partial                                       */
    /* ------------------------------------------------------------------ */

    // Request refreshed HTML for the folder
    const partialResponse = await fetch(
      `/watchlist/folder/${encodeURIComponent(folderId)}/partial`,
      { headers: { "X-Requested-With": "XMLHttpRequest" } }
    );

    const partialData = await partialResponse.json();

    // Handle partial-render failure separately from POST success
    if (!partialResponse.ok) {
      showToast(
        partialData.message || "Failed to refresh folder",
        partialData.category || "danger"
      );
      return;
    }

    /* ------------------------------------------------------------------ */
    /* Fade + DOM swap                                                    */
    /* ------------------------------------------------------------------ */

    // Fade existing content out before swapping HTML
    headerContainer.classList.add("is-fading-out");
    bodyContainer.classList.add("is-fading-out");

    setTimeout(() => {
      // Replace folder HTML while hidden
      headerContainer.innerHTML = partialData.html.folder_header;
      bodyContainer.innerHTML = partialData.html.folder_body;

      // Fade content back in
      headerContainer.classList.remove("is-fading-out");
      bodyContainer.classList.remove("is-fading-out");

      // Show success feedback after UI is fully updated
      showToast(actionData.message, actionData.category);
    }, FOLDER_FADE_TRANSITION_DURATION);
  } catch {
    // Catch network or unexpected runtime errors
    showToast("Unexpected error occurred", "danger");
  } finally {
    // Always clean up spinner and restore interaction state
    clearTimeout(overlayTimeoutId);
    overlay.classList.add("d-none");
    bodyContainer.classList.remove("pe-none");
  }
});

/* -------------------------------------------------------------------------- */
/* Bootstrap Utilities                                                        */
/* -------------------------------------------------------------------------- */

/**
 * Closes one or more Bootstrap components safely.
 *
 * @param {Array} components
 */
function closeBootstrapComponents(components) {
  components.forEach(({ type, selector, multiple = false }) => {
    // Support single elements or collections
    const elements = multiple
      ? document.querySelectorAll(selector)
      : [document.querySelector(selector)];

    elements.forEach((el) => {
      // Skip if element doesn't exist or isn't visible
      if (!el || !el.classList.contains("show")) return;

      let instance = null;

      // Resolve the correct Bootstrap instance type
      switch (type) {
        case "modal":
          instance = bootstrap.Modal.getInstance(el);
          break;
        case "dropdown":
          instance = bootstrap.Dropdown.getInstance(el);
          break;
        case "offcanvas":
          instance = bootstrap.Offcanvas.getInstance(el);
          break;
      }

      // Hide component if instance exists
      instance?.hide();
    });
  });
}

/* -------------------------------------------------------------------------- */
/* Toast Utility                                                              */
/* -------------------------------------------------------------------------- */

function showToast(message, category = "secondary") {
  const container = document.getElementById("toast-container-div");
  if (!container) return;

  // Ensure only one toast is visible at a time
  container.querySelectorAll(".toast").forEach((toast) => toast.remove());

  const toastEl = document.createElement("div");
  toastEl.className = `toast align-items-center text-bg-${category} border-1 mb-2`;
  toastEl.setAttribute("role", "alert");
  toastEl.setAttribute("aria-live", "assertive");
  toastEl.setAttribute("aria-atomic", "true");
  toastEl.setAttribute("data-bs-delay", TOAST_DISMISS_DELAY.toString());

  toastEl.innerHTML = `
    <div class="d-flex">
      <div class="toast-body">${message}</div>
      <button type="button"
              class="btn-close btn-close-white me-2 m-auto"
              data-bs-dismiss="toast"
              aria-label="Close"></button>
    </div>
  `;

  container.appendChild(toastEl);

  const toast = new bootstrap.Toast(toastEl);
  toast.show();

  // Remove toast from DOM after it disappears
  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}
