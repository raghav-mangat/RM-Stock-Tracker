document.addEventListener("DOMContentLoaded", () => {
  // Setup the watchlist accordion
  watchlistAccordion = document.getElementById("watchlistAccordion");
  if (watchlistAccordion) {
    attachAbsBtnToggleBehavior(watchlistAccordion, ".alert-container");
    attachAlertDeleteBtnBehavior(watchlistAccordion, ".alert-container");
  }

  // Setup the filter folder modal
  const filterFolderModalEl = document.getElementById("filterFolderModal");
  if (!filterFolderModalEl) return;

  filterFolderModalEl.addEventListener("show.bs.modal", (event) => {
    const button = event.relatedTarget;
    if (!button) return;

    const folderId = button.getAttribute("data-folder-id");
    const attributeId = button.getAttribute("data-attribute-id");
    const label = button.getAttribute("data-attribute-label");
    const useAbs = button.getAttribute("data-use-abs");
    const minValue = button.getAttribute("data-min-value");
    const maxValue = button.getAttribute("data-max-value");

    document.getElementById("hidden-attribute-id").value = attributeId;
    document.getElementById("filter-attribute-label").textContent = label;

    document.getElementById("modal-use-abs").checked = useAbs ? true : false;

    const minInput = document.getElementById("modal-min-value");
    const maxInput = document.getElementById("modal-max-value");

    // Ensure AutoNumeric is attached
    attachNumberFormatting(filterFolderModalEl);

    const minAN = AutoNumeric.getAutoNumericElement(minInput);
    const maxAN = AutoNumeric.getAutoNumericElement(maxInput);

    // Clear previous values safely
    if (minAN) minAN.clear();
    if (maxAN) maxAN.clear();

    // Set values using AutoNumeric API
    if (minValue && minAN) minAN.set(minValue);
    if (maxValue && maxAN) maxAN.set(maxValue);

    attachAbsBtnToggleBehavior(filterFolderModalEl, ".filter-container");

    const filterForm = filterFolderModalEl.querySelector(
      'form[data-action="filter"]',
    );
    if (filterForm) {
      // Set the data-folder-id attribute
      filterForm.dataset.folderId = folderId;
    }
  });

  // Setup the delete folder confirm modal
  const deleteFolderConfirmModalEl = document.getElementById(
    "deleteFolderConfirmModal",
  );
  if (!deleteFolderConfirmModalEl) return;

  deleteFolderConfirmModalEl.addEventListener("show.bs.modal", (event) => {
    const button = event.relatedTarget;
    if (!button) return;

    const folderId = button.getAttribute("data-folder-id");
    const folderName = button.getAttribute("data-folder-name");

    deleteFolderConfirmModalEl.querySelector("#delete-folder-id").value =
      folderId;
    deleteFolderConfirmModalEl.querySelector(
      "#delete-folder-name",
    ).textContent = folderName;
  });

  // Attach number formatting to the required fields in the document
  attachNumberFormatting();
});

function attachAbsBtnToggleBehavior(content, containerRef) {
  // ABS toggle visual
  content.querySelectorAll(".use-abs-toggle").forEach((checkbox) => {
    const container = checkbox.closest(containerRef);
    if (!container) return;

    const absSymbols = container.querySelectorAll(".abs-symbol");

    function updateAbsUI() {
      absSymbols.forEach((symbol) =>
        symbol.classList.toggle("d-none", !checkbox.checked),
      );
    }

    updateAbsUI();

    if (!checkbox.dataset.absInitialized) {
      checkbox.addEventListener("change", updateAbsUI);
      checkbox.dataset.absInitialized = "true";
    }
  });
}

function attachAlertDeleteBtnBehavior(content, containerRef) {
  // Delete alert behavior
  content.querySelectorAll(".btn-delete-alert").forEach((btn) => {
    if (btn.dataset.deleteInitialized) return;
    btn.dataset.deleteInitialized = "true";

    btn.addEventListener("change", () => {
      const container = btn.closest(containerRef);
      if (!container) return;

      const heading = container.querySelector(".alert-heading");
      const body = container.querySelector(".alert-body");
      const absToggle = container.querySelector(".use-abs-toggle");

      if (!(heading && body && absToggle)) return;

      if (btn.checked) {
        heading.style.opacity = "0.4";
        body.style.opacity = "0.4";
        body
          .querySelectorAll("input, select")
          .forEach((el) => (el.disabled = true));
        absToggle.disabled = true;
      } else {
        heading.style.opacity = "1";
        body.style.opacity = "1";
        body
          .querySelectorAll("input, select")
          .forEach((el) => (el.disabled = false));
        absToggle.disabled = false;
      }
    });
  });
}

function attachNumberFormatting(root = document) {
  // Using AutoNumeric JS library to handle number formatting

  const inputs = root.querySelectorAll("input[data-number-format]");

  inputs.forEach((input) => {
    let an = AutoNumeric.getAutoNumericElement(input);

    if (!an) {
      an = new AutoNumeric(input, {
        digitGroupSeparator: ",",
        decimalCharacter: ".",
        decimalPlaces: 2,
        allowDecimalPadding: false,
        modifyValueOnWheel: false,
      });
    }

    // Handle browser autofill
    const syncFromDom = () => {
      const raw = input.value;
      if (raw !== "") {
        an.set(raw);
      }
    };

    input.addEventListener("change", syncFromDom);
    input.addEventListener("blur", syncFromDom);
  });
}
