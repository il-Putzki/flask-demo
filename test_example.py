from app import RegisterForm


def test_reg_form_val():
    reg_form = RegisterForm(username="test_user", password="test_password", confirm="test_password")
    print("Form validation with confirm is equal to password FAILED")
    assert reg_form.validate() is True


def test_reg_form_not_val():
    reg_form = RegisterForm(username="test_user", password="test_password", confirm="test_password1")
    print("Form validation with confirm is not equal to password FAILED")
    assert reg_form.validate() is False
