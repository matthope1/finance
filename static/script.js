
// register page



function termsChecked(termsCheckBox) {
    if (termsCheckBox.checked) {
        document.getElementById("submit-button").disabled = false;
    } else {
        document.getElementById("submit-button").disabled = true;
    }
}