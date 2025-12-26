document.addEventListener("DOMContentLoaded", () => {

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

});
