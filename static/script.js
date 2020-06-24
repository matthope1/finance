
// register page

function agreeChecked() {

    alert("this function is called");
    if (document.getElementById('agree').checked)
    {
        return true;
    }
    else
    {
        alert("Please read Terms and conditions and check box");
        return false;
    }
}