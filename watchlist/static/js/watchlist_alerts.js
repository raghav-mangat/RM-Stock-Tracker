/**
 * watchlist_alerts.js
 *
 * Handles all alert folder partial HTML AJAX loads.
 */

/* -------------------------------------------------------------------------- */
/* Constants                                                                  */
/* -------------------------------------------------------------------------- */

// Duration (ms) of fade-out before swapping folder HTML
const FOLDER_FADE_TRANSITION_DURATION = 150;

// Duration (ms) of staggering the requests for initial folder HTML load
const FOLDER_INITIAL_LOAD_STAGGER_MS = 75;

// To ensure only a single request is made per folder by using locks
const folderLocks = new Map();

// Used if the user navigates away during an AJAX request
const pageAbortController = new AbortController();

/* -------------------------------------------------------------------------- */
/* Alert Folder Partial HTML Load Handler                                     */
/* -------------------------------------------------------------------------- */

async function loadFolderPartial(folderId) {
  // If there is an existing request for the folder, abort safely
  if (folderLocks.get(folderId)) {
    return;
  }
  // Keep track of the request started for this folder, lock the folder
  folderLocks.set(folderId, true);

  // Get DOM references for the affected folder
  const bodyContainer = document.getElementById(`accordion-body-${folderId}`);

  // Abort safely if folder DOM no longer exists
  if (!bodyContainer) {
    // Free the lock for the folder
    folderLocks.delete(folderId);
    return;
  }

  try {
    // Request partial HTML for the folder
    const partialResponse = await fetch(
      `/watchlist/alert/folder/${encodeURIComponent(folderId)}/partial`,
      {
        headers: { "X-Requested-With": "XMLHttpRequest" },
        signal: pageAbortController.signal,
      },
    );

    const partialData = await partialResponse.json();

    // Handle partial-render failure
    if (!partialResponse.ok) {
      throw new Error("Alert Folder partial unavailable");
    }

    /* ------------------------------------------------------------------ */
    /* Fade + DOM swap                                                    */
    /* ------------------------------------------------------------------ */

    // Fade existing content out before swapping HTML
    bodyContainer.classList.add("is-fading-out");

    setTimeout(() => {
      // Replace folder HTML while hidden
      bodyContainer.innerHTML = partialData.html.alert_folder_body;

      // Fade content back in
      bodyContainer.classList.remove("is-fading-out");
    }, FOLDER_FADE_TRANSITION_DURATION);
  } catch (error) {
    if (error.name === "AbortError") {
      return; // User navigated away, do nothing
    }

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

    // Always restore interaction state
    bodyContainer.classList.remove("pe-none");
  }
}

/* -------------------------------------------------------------------------- */
/* Load all Alert Folder HTML on initial page load                            */
/* -------------------------------------------------------------------------- */

document.addEventListener("DOMContentLoaded", () => {
  const folders = document.querySelectorAll("[data-watchlist-folder-id]");

  folders.forEach((folderEl, index) => {
    const folderId = folderEl.dataset.watchlistFolderId;

    /* ------------------------------------------------------------------ */
    /* Fetch alert folder partial                                         */
    /* ------------------------------------------------------------------ */
    setTimeout(() => {
      loadFolderPartial(folderId);
    }, index * FOLDER_INITIAL_LOAD_STAGGER_MS);
  });
});

// Abort Controller
window.addEventListener("beforeunload", () => {
  pageAbortController.abort();
});
