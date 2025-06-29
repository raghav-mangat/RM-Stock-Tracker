document.addEventListener("DOMContentLoaded", function () {
  const searchBar = document.getElementById("search-bar");
  const suggestionsBox = document.getElementById("suggestions");
  let activeIndex = -1;

  function resetSuggestions() {
    suggestionsBox.innerHTML = "";
    suggestionsBox.classList.add("d-none");
    searchBar.setAttribute("aria-expanded", "false");
    activeIndex = -1;
  }

  function updateActiveSuggestion(index) {
    const items = suggestionsBox.querySelectorAll(".suggestion-item");
    items.forEach((el, i) => {
      el.classList.toggle("active", i === index);
    });
  }

  searchBar.addEventListener("input", function () {
    const query = this.value.trim();
    if (query.length < 2) {
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

        data.forEach((item, idx) => {
          const div = document.createElement("div");
          div.textContent = `${item.ticker} — ${item.name}`;
          div.classList.add("suggestion-item", "px-3", "py-2", "border-bottom");
          div.setAttribute("role", "option");
          div.setAttribute("tabindex", "-1");
          div.addEventListener("click", () => {
            window.location.href = `/stocks/${item.ticker}`;
          });
          suggestionsBox.appendChild(div);
        });
      });
  });

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

  document.addEventListener("click", function (e) {
    if (!searchBar.contains(e.target) && !suggestionsBox.contains(e.target)) {
      resetSuggestions();
    }
  });
});
