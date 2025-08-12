// Script to execute the Filter Dropdown

const checkboxes = document.querySelectorAll('input[name="filter"]');

document.getElementById("select-all").addEventListener("click", function (e) {
  e.preventDefault();
  checkboxes.forEach((cb) => (cb.checked = true));
});

document.getElementById("clear-all").addEventListener("click", function (e) {
  e.preventDefault();
  checkboxes.forEach((cb) => (cb.checked = false));
});

document
  .getElementById("filter-dropdown")
  .addEventListener("click", function (e) {
    e.stopPropagation();
  });
