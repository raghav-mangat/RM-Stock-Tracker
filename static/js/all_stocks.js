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
    if (query.length < minSuggestionLen) {
      resetSuggestions();
      return;
    }

    fetch(`/query_stocks?q=${encodeURIComponent(query)}`)
      .then(response => response.json())
      .then(data => {
        resetSuggestions();
        if (data.length === 0) return;

        suggestionsBox.classList.remove("d-none");
        searchBar.setAttribute("aria-expanded", "true");

        // Create each suggestion as a Bootstrap list-group item
        data.forEach((item, idx) => {
          const div = document.createElement("div");
          div.textContent = `${item.ticker} - ${item.name}`;
          div.classList.add("suggestion-item", "list-group-item", "list-group-item-action");
          div.setAttribute("role", "option");
          div.setAttribute("tabindex", "-1");

          // Mouse Hover styling will use updateActiveSuggestion
          div.addEventListener("mouseover", () => updateActiveSuggestion(idx));
          div.addEventListener("click", () => {
            window.location.href = `/stocks/${item.ticker}`;
          });

          suggestionsBox.appendChild(div);
        });
      });
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

  // Hide suggestions when clicking outside
  document.addEventListener("click", function (e) {
    if (!searchBar.contains(e.target) && !suggestionsBox.contains(e.target)) {
      resetSuggestions();
    }
  });
});
