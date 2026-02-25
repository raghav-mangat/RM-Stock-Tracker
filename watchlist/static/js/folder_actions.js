/**
 * folder_actions.js
 *
 * Handles all folder-level AJAX form submissions.
 * Handles all folder partial HTML AJAX loads.
 */

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

// Delay (ms) before showing spinner to avoid flicker on fast responses
const FOLDER_SPINNER_OVERLAY_DELAY = 300;

// Duration (ms) of fade-out before swapping folder HTML
const FOLDER_FADE_TRANSITION_DURATION = 150;

// Duration (ms) of staggering the requests for initial folder HTML load
const FOLDER_INITIAL_LOAD_STAGGER_MS = 75;

// To ensure only a single request is made per folder by using locks
const folderLocks = new Map();

/* -------------------------------------------------------------------------- */
/* Form Submission Handler                                                    */
/* -------------------------------------------------------------------------- */

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

  // Keep track of the request started for this folder, lock the folder
  folderLocks.set(folderId, true);

  // Get DOM references for the affected folder
  const headerContainer = document.getElementById(
    `accordion-header-${folderId}`,
  );
  const bodyContainer = document.getElementById(`accordion-body-${folderId}`);
  const overlay = document.getElementById(`folder-loading-spinner-${folderId}`);

  // Abort safely if folder DOM no longer exists
  if (!headerContainer || !bodyContainer || !overlay) {
    // Free the lock for the folder
    folderLocks.delete(folderId);
    return;
  }

  // Show spinner only if request takes longer than the delay
  const overlayTimeoutId = setTimeout(() => {
    overlay.classList.remove("d-none");
    // Prevent interaction while loading
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
    /* Fetch folder partial                                               */
    /* ------------------------------------------------------------------ */

    await loadFolderPartial(folderId, folderLocks.get(folderId), actionData);
  } catch (error) {
    // Free the lock for next request
    folderLocks.delete(folderId);
  } finally {
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

/* -------------------------------------------------------------------------- */
/* Folder Partial HTML Load Handler                                           */
/* -------------------------------------------------------------------------- */

async function loadFolderPartial(
  folderId,
  folderLock = null,
  actionData = null,
) {
  // If there is an existing request for the folder, abort safely
  if (!folderLock && folderLocks.get(folderId)) {
    return;
  }

  // Keep track of the request started for this folder, lock the folder
  folderLocks.set(folderId, true);

  // Get DOM references for the affected folder
  const headerContainer = document.getElementById(
    `accordion-header-${folderId}`,
  );
  const bodyContainer = document.getElementById(`accordion-body-${folderId}`);
  const overlay = document.getElementById(`folder-loading-spinner-${folderId}`);

  // Abort safely if folder DOM no longer exists
  if (!headerContainer || !bodyContainer || !overlay) {
    // Free the lock for the folder
    folderLocks.delete(folderId);
    return;
  }

  // Show spinner only if request takes longer than the delay
  const overlayTimeoutId = setTimeout(() => {
    overlay.classList.remove("d-none");
    // Prevent interaction while loading
    bodyContainer.classList.add("pe-none");
  }, FOLDER_SPINNER_OVERLAY_DELAY);

  try {
    // Request partial HTML for the folder
    const partialResponse = await fetch(
      `/watchlist/folder/${encodeURIComponent(folderId)}/partial`,
      {
        headers: { "X-Requested-With": "XMLHttpRequest" },
      },
    );

    const partialData = await partialResponse.json();

    // Handle partial-render failure
    if (!partialResponse.ok) {
      throw new Error("Folder partial unavailable");
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
    }, FOLDER_FADE_TRANSITION_DURATION);
  } catch (error) {
    // Show folder loading failure HTML
    folderLoadingFailure = document.getElementById(
      `folder-loading-failure-${folderId}`,
    );

    if (!folderLoadingFailure) return;

    const failureNode = folderLoadingFailure.cloneNode(true);
    failureNode.classList.remove("d-none");

    const target =
      bodyContainer.querySelector(".folder-table-container") || bodyContainer;

    target.replaceChildren(failureNode);
  } finally {
    // Request for this folder was completed, free the lock for next request
    folderLocks.delete(folderId);

    // Show feedback after UI is fully updated
    if (actionData?.toast) {
      showToast(actionData.toast);
    }

    // Always clean up spinner and restore interaction state
    clearTimeout(overlayTimeoutId);
    overlay.classList.add("d-none");
    bodyContainer.classList.remove("pe-none");
  }
}

/* -------------------------------------------------------------------------- */
/* Load all Folder HTML on initial page load                                  */
/* -------------------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", () => {
  const folders = document.querySelectorAll("[data-watchlist-folder-id]");

  folders.forEach((folderEl, index) => {
    const folderId = folderEl.dataset.watchlistFolderId;
    const folderNumItems = folderEl.dataset.watchlistFolderNumItems;

    /* ------------------------------------------------------------------ */
    /* Fetch folder partial                                               */
    /* ------------------------------------------------------------------ */

    if (folderNumItems > 0) {
      setTimeout(() => {
        loadFolderPartial(folderId);
      }, index * FOLDER_INITIAL_LOAD_STAGGER_MS);
    }
  });
});

/* -------------------------------------------------------------------------- */
/* Folder Partial HTML Retry Load Handler                                     */
/* -------------------------------------------------------------------------- */
function retryLoadFolder(folderId) {
  loadFolderPartial(folderId);
}
