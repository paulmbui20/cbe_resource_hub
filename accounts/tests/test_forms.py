from accounts.forms import ProfileForm
from accounts.tests.base import AccountsBaseTestcase


class ProfileFormTestCase(AccountsBaseTestcase):

    def get_sample_valid_form_data(self):
        return {
            "first_name": "John",
            "last_name": "Doe",
            "phone_number": "+254712345678",
            "disable_email_notification": True,
        }

    def test_form_valid(self):
        form_data = self.get_sample_valid_form_data()
        form = ProfileForm(form_data)

        self.assertTrue(form.is_valid())
        self.assertTrue(form.errors.as_text() == '')

    def test_form_with_invalid_phone_number(self):
        form_data = self.get_sample_valid_form_data()
        form_data["phone_number"] = "+25471234567"

        form = ProfileForm(form_data)

        self.assertFalse(form.is_valid())
        self.assertFalse(form.errors.as_text() == '')
        self.assertIn("phone_number", form.errors)

    def test_form_work_without_optional_first_name(self):
        form_data = self.get_sample_valid_form_data()
        del form_data["first_name"]
        form = ProfileForm(form_data)

        self.assertTrue(form.is_valid())
        self.assertTrue(form.errors.as_text() == '')

    def test_form_work_with_optional_last_name(self):
        form_data = self.get_sample_valid_form_data()
        del form_data["last_name"]
        form = ProfileForm(form_data)

        self.assertTrue(form.is_valid() or form.errors.as_text() == '')

    def test_form_work_with_optional_disable_email_notification(self):
        form_data = self.get_sample_valid_form_data()
        del form_data["disable_email_notification"]
        form = ProfileForm(form_data)

        self.assertTrue(form.is_valid())
        self.assertTrue(form.errors.as_text() == '')

    def test_form_save(self):
        form_data = self.get_sample_valid_form_data()
        form = ProfileForm(form_data, instance=self.user)

        if form.is_valid():
            form.save()

            self.assertEqual(self.user.first_name, "John")
            self.assertEqual(self.user.last_name, "Doe")
            self.assertEqual(self.user.phone_number, "+254712345678")
            self.assertEqual(self.user.disable_email_notification, True)
            self.assertEqual(self.user.email,
                             "testuser1@example.com"
                             )  # this check is not on the form as a form field or a submitted form data \
            # its only meant to confirm we are working on the correct user
