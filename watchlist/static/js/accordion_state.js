(function () {
  // Key used to store accordion state in sessionStorage
  const STORAGE_KEY = "rm_watchlist_open_accordions";

  // Safely retrieve stored accordion state
  function getState() {
    try {
      return JSON.parse(sessionStorage.getItem(STORAGE_KEY)) || {};
    } catch {
      // If storage is corrupted or unreadable, fall back to empty state
      return {};
    }
  }

  // Persist accordion state to sessionStorage
  function saveState(state) {
    sessionStorage.setItem(STORAGE_KEY, JSON.stringify(state));
  }

  // Determine which page we are on (watchlist vs alerts)
  function getPageKey() {
    if (window.location.pathname.includes("/watchlist/alerts")) {
      return "alerts";
    }
    return "watchlist";
  }

  // Restore previously opened accordions on page load
  function initAccordionState() {
    const pageKey = getPageKey();
    const state = getState();
    const openIds = new Set(state[pageKey] || []);

    document.querySelectorAll(".accordion-collapse").forEach((collapse) => {
      const id = collapse.id;
      if (!id) return;

      // Programmatically open accordions that were previously open
      if (openIds.has(id)) {
        const instance = bootstrap.Collapse.getOrCreateInstance(collapse, {
          toggle: false,
        });
        instance.show();
      }
    });
  }

  // Track accordion open/close events and persist state
  function trackAccordionEvents() {
    const pageKey = getPageKey();
    const state = getState();
    state[pageKey] = state[pageKey] || [];

    document.querySelectorAll(".accordion-collapse").forEach((collapse) => {
      const id = collapse.id;
      if (!id) return;

      // Store accordion ID when it is opened
      collapse.addEventListener("shown.bs.collapse", () => {
        if (!state[pageKey].includes(id)) {
          state[pageKey].push(id);
          saveState(state);
        }
      });

      // Remove accordion ID when it is closed
      collapse.addEventListener("hidden.bs.collapse", () => {
        state[pageKey] = state[pageKey].filter((x) => x !== id);
        saveState(state);
      });
    });
  }

  // Initialize accordion state handling after DOM is ready
  document.addEventListener("DOMContentLoaded", () => {
    initAccordionState();
    trackAccordionEvents();
  });
})();
