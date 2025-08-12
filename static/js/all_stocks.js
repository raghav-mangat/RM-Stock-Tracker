document.addEventListener("DOMContentLoaded", function () {
  const searchBar = document.getElementById("search-bar");
  const suggestionsBox = document.getElementById("suggestions");
  const minSuggestionLen = 1;
  let activeIndex = -1;

  // Reset suggestions UI
  function resetSuggestions() {
    suggestionsBox.innerHTML = "";
    suggestionsBox.classList.add("d-none");
    searchBar.setAttribute("aria-expanded", "false");
    activeIndex = -1;
  }

  // Update which suggestion is highlighted
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

  // Fetch suggestions as user types
  searchBar.addEventListener("input", function () {
    const query = this.value.trim();

    suggestionsBox.scrollTop = 0; // Reset scroll position

    if (query.length < minSuggestionLen) {
      resetSuggestions();
      return;
    }

    fetch(`/query_stocks?q=${encodeURIComponent(query)}`)
      .then((response) => response.json())
      .then((data) => {
        resetSuggestions();
        if (data.length === 0) return;

        suggestionsBox.classList.remove("d-none");
        searchBar.setAttribute("aria-expanded", "true");

        // Create each suggestion as a Bootstrap list-group item
        data.forEach((item, idx) => {
          const anchor = document.createElement("a");
          anchor.href = `/stocks/${item.ticker}`;
          anchor.innerHTML = `<span><strong>${item.ticker}</strong> - ${item.name}</span>`;
          anchor.classList.add(
            "suggestion-item",
            "list-group-item",
            "list-group-item-action"
          );
          anchor.setAttribute("role", "option");
          anchor.setAttribute("tabindex", "-1");

          // Mouse Hover styling will use updateActiveSuggestion
          anchor.addEventListener("mouseover", () =>
            updateActiveSuggestion(idx)
          );

          suggestionsBox.appendChild(anchor);

          // Auto-select the first suggestion
          activeIndex = 0;
          updateActiveSuggestion(activeIndex);
        });
      });
  });

  // Handle focus event to show suggestions again
  searchBar.addEventListener("focus", function () {
    const query = this.value.trim();
    if (query.length >= minSuggestionLen) {
      // Manually trigger input event logic
      const inputEvent = new Event("input");
      this.dispatchEvent(inputEvent);
    }
  });

  // Handle up/down/enter keyboard navigation
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

  // Prevent page from scrolling when mouse is over suggestions box
  suggestionsBox.addEventListener(
    "wheel",
    function (e) {
      const isScrollable =
        suggestionsBox.scrollHeight > suggestionsBox.clientHeight;
      if (isScrollable) {
        const atTop = suggestionsBox.scrollTop === 0;
        const atBottom =
          suggestionsBox.scrollTop + suggestionsBox.clientHeight >=
          suggestionsBox.scrollHeight;

        if ((e.deltaY < 0 && atTop) || (e.deltaY > 0 && atBottom)) {
          e.preventDefault(); // Prevent scrolling the page
        }
      }
    },
    { passive: false }
  );

  // Hide suggestions when clicking outside
  document.addEventListener("click", function (e) {
    if (!searchBar.contains(e.target) && !suggestionsBox.contains(e.target)) {
      resetSuggestions();
    }
  });
});
