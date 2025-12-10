document.addEventListener("DOMContentLoaded", () => {
  const emailAlertsSwitch = document.getElementById("emailAlertsSwitch");
  const emailAlertsConfirmModal = document.getElementById(
    "emailAlertsConfirmModal"
  );
  const emailAlertsConfirmModalCloseBtns =
    emailAlertsConfirmModal.querySelectorAll(".modal-close-btn");

  const emailAlertsSwitchInitialState = emailAlertsSwitch.checked;

  emailAlertsConfirmModalCloseBtns.forEach((button) => {
    button.addEventListener("click", () => {
      button.blur();
      emailAlertsSwitch.checked = emailAlertsSwitchInitialState;
    });
  });
});
