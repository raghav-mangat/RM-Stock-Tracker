document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll(".btn-delete-alert").forEach((btn) => {
    btn.addEventListener("click", function () {
      btn_id_split = btn.id.split("-");
      loop_index = btn_id_split[1];
      db_id = btn_id_split[2];

      alertRow = document.getElementById(`alert-row-${loop_index}-${db_id}`);
      attribute = document.getElementById(`attribute-${loop_index}-${db_id}`);
      useAbs = document.getElementById(`use-abs-${loop_index}-${db_id}`);
      minValue = document.getElementById(`min-value-${loop_index}-${db_id}`);
      maxValue = document.getElementById(`max-value-${loop_index}-${db_id}`);

      if (btn.checked) {
        alertRow.style.opacity = 0.4;
        attribute.disabled = true;
        useAbs.disabled = true;
        minValue.disabled = true;
        maxValue.disabled = true;
      } else {
        alertRow.style.opacity = 1;
        attribute.disabled = false;
        useAbs.disabled = false;
        minValue.disabled = false;
        maxValue.disabled = false;
      }
    });
  });

  const modalEl = document.getElementById("filterFolderModal");
  modalEl.addEventListener("show.bs.modal", (event) => {
    const button = event.relatedTarget;

    const attributeId = button.getAttribute("data-attribute-id");
    const label = button.getAttribute("data-attribute-label");
    const useAbs = button.getAttribute("data-use-abs");
    const minValue = button.getAttribute("data-min-value");
    const maxValue = button.getAttribute("data-max-value");

    document.getElementById("hidden-attribute-id").value = attributeId;
    document.getElementById("filter-attribute-label").textContent = label;

    document.getElementById("modal-use-abs").checked = useAbs ? true : false;
    document.getElementById("modal-min-value").value = minValue ?? "";
    document.getElementById("modal-max-value").value = maxValue ?? "";
  });
});
