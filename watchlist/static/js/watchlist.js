document.querySelectorAll(".btn-delete-alert").forEach((btn) => {
  btn.addEventListener("click", function () {
    btn_id_split = btn.id.split("-");
    loop_index = btn_id_split[1];
    db_id = btn_id_split[2];

    alertRow = document.getElementById(`alert-row-${loop_index}-${db_id}`);
    attribute = document.getElementById(`attribute-${loop_index}-${db_id}`);
    operator = document.getElementById(`operator-${loop_index}-${db_id}`);
    value = document.getElementById(`value-${loop_index}-${db_id}`);

    if (btn.checked) {
      alertRow.style.opacity = 0.4;
      attribute.disabled = true;
      operator.disabled = true;
      value.disabled = true;
    } else {
      alertRow.style.opacity = 1;
      attribute.disabled = false;
      operator.disabled = false;
      value.disabled = false;
    }
  });
});
