(function () {
  const themeSwitch = document.getElementById("themeSwitch");
  if (!themeSwitch) return;

  // Set theme and sync checkbox
  function setTheme(theme) {
    document.documentElement.setAttribute("data-bs-theme", theme);
    localStorage.setItem("theme", theme);
    themeSwitch.checked = theme === "dark";
  }

  // Initial sync (theme already set in <head>, so no flicker)
  const currentTheme = document.documentElement.getAttribute("data-bs-theme");

  setTheme(currentTheme);

  // Toggle handler
  themeSwitch.addEventListener("change", () => {
    setTheme(themeSwitch.checked ? "dark" : "light");
    window.dispatchEvent(new Event("themechange"));
  });
})();

// Function available to other JS code to get the current theme
function getCurrentTheme() {
  return document.documentElement.getAttribute("data-bs-theme") || "light";
}
