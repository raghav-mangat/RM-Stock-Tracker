// Track the latest fetch request for each category
const requestTracker = {};

document.addEventListener("DOMContentLoaded", () => {
  // Fetch the data for each category when the link for that
  // category is clicked
  categoryLinks = document.querySelectorAll(".category-link");
  categoryLinks.forEach((categoryLink) => {
    categoryLink.addEventListener("click", () => {
      fetchCategoryData(categoryLink);
    });
  });
});

function fetchCategoryData(categoryLink) {
  // Get the category name from category link element's ID
  const category = categoryLink.id.split("-")[0];

  // Assign a new request ID for this category
  const reqId = (requestTracker[category] || 0) + 1;
  requestTracker[category] = reqId;

  // Check if the data for this category is already loaded
  if (categoryLink.dataset.loaded === "0") {
    // If data is not loaded fetch the required data
    fetch(`/get-top-stocks-data/${encodeURIComponent(category)}`)
      .then((response) => response.json())
      .then((data) => {
        // Ignore stale responses
        if (requestTracker[category] !== reqId) {
          return;
        }

        // Update the tables with the fetched HTML data for each stock type
        // only if this response is the most recent
        document.getElementById(`table-${category}-gainers`).innerHTML =
          data.html.gainers;
        document.getElementById(`table-${category}-losers`).innerHTML =
          data.html.losers;
        document.getElementById(`table-${category}-volume`).innerHTML =
          data.html.top_traded;

        // Mark the data as loaded
        categoryLink.dataset.loaded = "1";
      })
      .catch((err) =>
        console.error("An unexpected error occurred. Please try again later."),
      );
  }
}
