/* ============================
   DOM REFERENCES
============================ */
const allStocksSearchBar = document.getElementById("all-stocks-search-bar");
const watchlistSearchBar = document.getElementById("watchlist-search-bar");

const searchBar = document.getElementById("search-bar");
const suggestionsBox = document.getElementById("suggestions");

/* ============================
   STATE
============================ */
const minSuggestionLen = 1;
let activeIndex = -1;
let currentFolderId = null;

/* ============================
   DEBOUNCE CONFIG
============================ */
let debounceTimer = null;
const DEBOUNCE_DELAY = 300; // ms

/* ============================
   WATCHLIST MODAL LOGIC
============================ */
if (watchlistSearchBar) {
  const modalEl = document.getElementById("addStockModal");
  // Capture folder ID when modal is opened
  modalEl.addEventListener("show.bs.modal", function (event) {
    const button = event.relatedTarget;
    currentFolderId = button.getAttribute("data-folder-id");
    searchBar.value = "";
    resetSuggestions();
  });
  // Focus on search bar after modal is fully shown
  modalEl.addEventListener("shown.bs.modal", function () {
    searchBar.focus();
  });
}

/* ============================
   UI HELPERS
============================ */

// Clear and hide suggestions
function resetSuggestions() {
  suggestionsBox.innerHTML = "";
  suggestionsBox.classList.add("d-none");
  searchBar.setAttribute("aria-expanded", "false");
  activeIndex = -1;
}

// Highlight active suggestion
function updateActiveSuggestion(index) {
  const items = suggestionsBox.querySelectorAll(".suggestion-item");
  items.forEach((el, i) => {
    if (i === index) {
      el.classList.add("text-bg-primary");
      el.scrollIntoView({ block: "nearest", behavior: "smooth" });
    } else {
      el.classList.remove("text-bg-primary");
    }
  });
}

// Show empty-state message
function showNoResults(message) {
  suggestionsBox.innerHTML = `
    <div class="list-group-item text-muted text-center py-4">
      ${message}
    </div>
  `;
  suggestionsBox.classList.remove("d-none");
  searchBar.setAttribute("aria-expanded", "true");
}

// Header for trending stocks
function showTrendingHeader() {
  const header = document.createElement("div");
  header.className = "list-group-item fw-semibold text-muted small";
  header.innerText = "Trending Stocks";
  suggestionsBox.appendChild(header);
}

/* ============================
   FETCH + RENDER
============================ */
function fetchSuggestions(query) {
  // Guard: too short but not empty
  if (query.length < minSuggestionLen && query !== "") {
    resetSuggestions();
    return;
  }

  fetch(`/query-stocks?q=${encodeURIComponent(query)}`)
    .then((res) => res.json())
    .then((data) => {
      resetSuggestions();

      if (data.length === 0) {
        showNoResults(
          query ? "No matching stocks found" : "No trending stocks available"
        );
        return;
      }

      suggestionsBox.classList.remove("d-none");
      searchBar.setAttribute("aria-expanded", "true");

      // If query is empty, show trending stocks
      if (!query) {
        showTrendingHeader();
      }

      data.forEach((item, idx) => {
        let el;

        if (allStocksSearchBar) {
          el = document.createElement("a");
          el.href = `/stocks/${item.ticker}`;
        } else {
          el = document.createElement("button");
          el.type = "button";
          el.addEventListener("click", () => {
            document.getElementById("hidden-folder-id").value = currentFolderId;
            document.getElementById("hidden-ticker").value = item.ticker;
            addStockForm = document.getElementById("addStockForm");
            if (addStockForm) {
              // Set the data-folder-id attribute
              addStockForm.dataset.folderId = currentFolderId;
              addStockForm.requestSubmit();
            }
          });
        }

        el.innerHTML = `<strong>${item.ticker}</strong> - ${item.name}`;
        el.classList.add(
          "suggestion-item",
          "list-group-item",
          "list-group-item-action"
        );
        el.setAttribute("role", "option");

        el.addEventListener("mouseover", () => updateActiveSuggestion(idx));

        suggestionsBox.appendChild(el);
      });

      suggestionsBox.scrollTop = 0;

      activeIndex = 0;
      updateActiveSuggestion(activeIndex);
    });
}

/* ============================
   INPUT HANDLER (DEBOUNCED)
============================ */
searchBar.addEventListener("input", function () {
  const query = this.value.trim();
  suggestionsBox.scrollTop = 0;

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchSuggestions(query);
  }, DEBOUNCE_DELAY);
});

/* ============================
   FOCUS HANDLER
============================ */
searchBar.addEventListener("focus", function () {
  const query = this.value.trim();

  clearTimeout(debounceTimer);
  debounceTimer = setTimeout(() => {
    fetchSuggestions(query);
  }, DEBOUNCE_DELAY);
});

/* ============================
   KEYBOARD NAVIGATION
============================ */
searchBar.addEventListener("keydown", function (e) {
  const items = suggestionsBox.querySelectorAll(".suggestion-item");
  if (items.length === 0) return;

  if (e.key === "ArrowDown") {
    e.preventDefault();
    activeIndex = (activeIndex + 1) % items.length;
    updateActiveSuggestion(activeIndex);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    activeIndex = (activeIndex - 1 + items.length) % items.length;
    updateActiveSuggestion(activeIndex);
  } else if (e.key === "Enter") {
    if (activeIndex >= 0 && items[activeIndex]) {
      items[activeIndex].click();
    }
  }
});

/* ============================
   SCROLL BEHAVIOR
============================ */
suggestionsBox.addEventListener(
  "wheel",
  function (e) {
    const isScrollable =
      suggestionsBox.scrollHeight > suggestionsBox.clientHeight;

    if (!isScrollable) return;

    const atTop = suggestionsBox.scrollTop === 0;
    const atBottom =
      suggestionsBox.scrollTop + suggestionsBox.clientHeight >=
      suggestionsBox.scrollHeight;

    if ((e.deltaY < 0 && atTop) || (e.deltaY > 0 && atBottom)) {
      e.preventDefault();
    }
  },
  { passive: false }
);

/* ============================
   CLICK OUTSIDE TO CLOSE
============================ */
document.addEventListener("click", function (e) {
  if (!searchBar.contains(e.target) && !suggestionsBox.contains(e.target)) {
    resetSuggestions();
  }
});
