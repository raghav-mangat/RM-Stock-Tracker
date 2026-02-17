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

// To ensure only a single request is made per folder by using locks
const folderLocks = new Map();

document.addEventListener("submit", async (event) => {
  const form = event.target;

  // Only intercept AJAX-enabled folder action forms
  if (!form.classList.contains("folder-action-form")) return;

  event.preventDefault();

  const folderId = form.dataset.folderId;

  // If there is an existing request for the folder, abort safely
  if (folderLocks.get(folderId)) {
    return;
  }

  // Keep track of the new request started for this folder, lock the folder
  folderLocks.set(folderId, true);

  // Get DOM references for the affected folder
  const headerContainer = document.getElementById(
    `accordion-header-${folderId}`,
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
    /* POST request                                                       */
    /* ------------------------------------------------------------------ */

    // Execute folder action (add, remove, update, etc.)
    const actionResponse = await fetch(form.action, {
      method: "POST",
      headers: { "X-Requested-With": "XMLHttpRequest" },
      body: formData,
    });

    const actionData = await actionResponse.json();

    // Stop early if server-side logic failed
    if (!actionResponse.ok && actionData.requires_refresh) {
      refreshPage(
        (message = actionData.message),
        (category = actionData.category),
      );
      return;
    }

    /* ------------------------------------------------------------------ */
    /* Fetch updated folder partial                                       */
    /* ------------------------------------------------------------------ */

    // Request refreshed HTML for the folder
    const partialResponse = await fetch(
      `/watchlist/folder/${encodeURIComponent(folderId)}/partial`,
      { headers: { "X-Requested-With": "XMLHttpRequest" } },
    );

    const partialData = await partialResponse.json();

    // Handle partial-render failure separately from POST success
    if (!partialResponse.ok && partialData.requires_refresh) {
      refreshPage(
        (message = partialData.message),
        (category = partialData.category),
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

      // Add the required event-listeners to the new HTML content
      attachAbsBtnToggleBehavior(bodyContainer, ".alert-container");
      attachAlertDeleteBtnBehavior(bodyContainer, ".alert-container");

      // Initialize the Bootstrap Popovers for the new HTML content
      initializeBSPopovers(bodyContainer);

      // Re-attach number formatting to the new HTML content
      attachNumberFormatting(bodyContainer);

      // Fade content back in
      headerContainer.classList.remove("is-fading-out");
      bodyContainer.classList.remove("is-fading-out");

      // Show feedback after UI is fully updated
      showToast(actionData.toast);
    }, FOLDER_FADE_TRANSITION_DURATION);
  } catch {
    // Catch network or unexpected runtime errors
    showToast("Unexpected error occurred", "danger");
  } finally {
    // Request for this folder was completed, free the lock for next request
    folderLocks.delete(folderId);

    // Always clean up spinner and restore interaction state
    clearTimeout(overlayTimeoutId);
    overlay.classList.add("d-none");
    bodyContainer.classList.remove("pe-none");
  }
});

/* -------------------------------------------------------------------------- */
/* Refresh Page Utility                                                       */
/* -------------------------------------------------------------------------- */

function refreshPage(message, category) {
  // Encode the message and category so it can be passed safely in a URL parameter
  const encodedMessage = encodeURIComponent(message);
  const encodedCategory = encodeURIComponent(category);

  // Redirect to the refresh watchlist route
  window.location.href = `/watchlist/refresh?message=${encodedMessage}&category=${encodedCategory}`;
}

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
function showToast(toastHTML) {
  const container = document.getElementById("toast-container-div");
  if (!container || !toastHTML) return;

  // Keep only one toast
  container.querySelectorAll(".toast").forEach((t) => t.remove());

  container.insertAdjacentHTML("beforeend", toastHTML);

  const toastEl = container.querySelector(".toast:last-child");
  const toast = new bootstrap.Toast(toastEl);
  toast.show();

  toastEl.addEventListener("hidden.bs.toast", () => toastEl.remove());
}
