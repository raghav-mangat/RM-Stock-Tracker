// Track the latest fetch request for each category
const requestTracker = {};

document.addEventListener("DOMContentLoaded", () => {
  // Fetch the data for each category when the link for that
  // category is clicked
  const categoryLinks = document.querySelectorAll(".category-link");
  categoryLinks.forEach((categoryLink) => {
    categoryLink.addEventListener("click", () => {
      fetchCategoryData(categoryLink);
    });
  });
});

function fetchCategoryData(categoryLink) {
  // Get the category name from category link element's ID
  const category = categoryLink.id.replace("-tab", "");

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

        function removeLoadingState(region, body) {
          region.setAttribute("aria-busy", "false");
          body.classList.remove("pe-none");
          body.removeAttribute("aria-hidden");
        }

        // Update the tables with the fetched HTML data for each stock type
        // only if this response is the most recent

        const gainers_region = document.getElementById(
          `top-stocks-region-${category}-gainers`,
        );
        const gainers_body = document.getElementById(
          `table-${category}-gainers`,
        );
        if (gainers_region && gainers_body) {
          gainers_body.innerHTML = data.html.gainers;
          removeLoadingState(gainers_region, gainers_body);
        }

        const losers_region = document.getElementById(
          `top-stocks-region-${category}-losers`,
        );
        const losers_body = document.getElementById(`table-${category}-losers`);
        if (losers_region && losers_body) {
          losers_body.innerHTML = data.html.losers;
          removeLoadingState(losers_region, losers_body);
        }

        const volume_region = document.getElementById(
          `top-stocks-region-${category}-volume`,
        );
        const volume_body = document.getElementById(`table-${category}-volume`);
        if (volume_region && volume_body) {
          volume_body.innerHTML = data.html.top_traded;
          removeLoadingState(volume_region, volume_body);
        }

        // Mark the data as loaded
        categoryLink.dataset.loaded = "1";
      })
      .catch((err) =>
        console.error("An unexpected error occurred. Please try again later."),
      );
  }
}
