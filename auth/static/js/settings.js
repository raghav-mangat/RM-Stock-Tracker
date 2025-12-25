document.addEventListener("DOMContentLoaded", () => {
  // ------------------------------------------------------------------
  // Settings page tab - URL hash synchronization
  // ------------------------------------------------------------------

  const tabLinks = document.querySelectorAll(
    '#settings-tab a[data-bs-toggle="list"]'
  );

  // Tracks the last valid tab hash (e.g. "profile", "account")
  let lastValidTabHash = null;

  /**
   * Returns the logical name of the currently active tab.
   */
  function getActiveTabName() {
    const activeTab = document.querySelector(
      "#settings-tab a.active[data-tab]"
    );
    return activeTab ? activeTab.getAttribute("data-tab") : null;
  }

  /**
   * Normalizes the URL to the currently active tab.
   * Updates lastValidTabHash and replaces the URL hash using history API.
   */
  function normalizeUrlToActiveTab() {
    const activeTab = getActiveTabName();

    if (activeTab) {
      lastValidTabHash = activeTab;
      history.replaceState(null, "", `#${activeTab}`);
    } else {
      history.replaceState(null, "", window.location.pathname);
    }
  }

  /**
   * Activates the correct tab based on the URL hash.
   * - Supports deep links and manual hash edits
   * - Prevents browser auto-scroll
   * - Cleans invalid or empty hashes
   */
  function activateTabFromHash() {
    const rawHash = window.location.hash.replace("#", "");

    // Empty hash (#)
    if (rawHash === "") {
      normalizeUrlToActiveTab();
      return;
    }

    // Temporarily remove hash to prevent browser anchor scrolling
    history.replaceState(null, "", window.location.pathname);

    const trigger = document.querySelector(
      `#settings-tab a[data-tab="${rawHash}"]`
    );

    if (trigger) {
      // Valid hash: activate matching tab
      new bootstrap.Tab(trigger).show();
      lastValidTabHash = rawHash;
      history.replaceState(null, "", `#${rawHash}`);
    } else {
      // Invalid hash
      normalizeUrlToActiveTab();
      return;
    }
  }

  // Apply hash-based tab selection on initial page load
  activateTabFromHash();

  // React to manual hash changes (typing, Enter, back/forward)
  window.addEventListener("hashchange", activateTabFromHash);

  /**
   * Keeps the URL hash in sync when users switch tabs.
   */
  tabLinks.forEach((link) => {
    // Handles standard Bootstrap tab switches
    link.addEventListener("shown.bs.tab", (event) => {
      const tabName = event.target.getAttribute("data-tab");

      if (tabName) {
        lastValidTabHash = tabName;
        history.replaceState(null, "", `#${tabName}`);
      }
    });
  });

  // ------------------------------------------------------------------

  // Profile settings update confirmation
  const profileSettingsConfirmModalBtn = document.getElementById(
    "profileSettingsConfirmModalBtn"
  );
  profileSettingsConfirmModalBtn.addEventListener("click", () => {
    const profileSettingsConfirmModal = document.getElementById(
      "profileSettingsConfirmModal"
    );
    const modalInstance = bootstrap.Modal.getInstance(
      profileSettingsConfirmModal
    );
    profileSettingsConfirmModal.addEventListener("hidden.bs.modal", () => {
      const profileSettingsform = document.getElementById(
        "profile-settings-form"
      );
      profileSettingsform.submit();
    });
    modalInstance.hide();
  });

  // ------------------------------------------------------------------

  // Account settings email alerts toggle
  const emailAlertsSwitch = document.getElementById("emailAlertsSwitch");
  const emailAlertsConfirmModal = document.getElementById(
    "emailAlertsConfirmModal"
  );
  const emailAlertsConfirmModalCloseBtns =
    emailAlertsConfirmModal.querySelectorAll(".modal-close-btn");

  const emailAlertsSwitchInitialState = emailAlertsSwitch.checked;

  emailAlertsConfirmModalCloseBtns.forEach((button) => {
    button.addEventListener("click", () => {
      emailAlertsSwitch.checked = emailAlertsSwitchInitialState;
    });
  });

  // ------------------------------------------------------------------
});
