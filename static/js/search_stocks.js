document.addEventListener("DOMContentLoaded", function () {
  const searchBar = document.getElementById("search-bar");
  const suggestions = document.getElementById("suggestions");

  searchBar.addEventListener("input", function () {
    const query = this.value;
    if (query.length < 2) {
      suggestions.innerHTML = "";
      return;
    }

    fetch(`/query_stocks?q=${encodeURIComponent(query)}`)
      .then(response => response.json())
      .then(data => {
        suggestions.innerHTML = "";
        data.forEach(item => {
          const div = document.createElement("div");
          div.textContent = `${item.ticker} — ${item.name}`;
          div.classList.add("suggestion-item");
          div.addEventListener("click", () => {
            window.location.href = `/stock/${item.ticker}`;
          });
          suggestions.appendChild(div);
        });
      });
  });

  // Hide suggestions if click is outside both search bar and suggestions
  document.addEventListener("click", function (e) {
    if (!searchBar.contains(e.target) && !suggestions.contains(e.target)) {
      suggestions.innerHTML = "";
    }
  });
});
