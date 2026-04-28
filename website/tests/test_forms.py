"""
website/tests/test_forms.py

Tests for ContactForm and EmailSubscriptionForm:
  ContactForm:
    - Valid data accepted
    - Required fields enforced (name, subject, message)
    - Email and phone are optional
    - Honeypot field (website_url) blocks bots
    - Honeypot field is a HiddenInput widget
  EmailSubscriptionForm:
    - Valid data accepted
    - Email required; full_name optional
    - Duplicate email raises ValidationError
    - ModelForm saves correctly
"""

from django.test import TestCase
from website.forms import ContactForm, EmailSubscriptionForm
from website.models import EmailSubscriber
from website.tests.base import WebsiteBaseTestCase


class ContactFormTests(WebsiteBaseTestCase):

    def _valid(self, **overrides):
        data = {
            "name": "Jane Doe",
            "email": "jane@example.com",
            "subject": "Hello",
            "message": "This is a test message.",
            "website_url": "",  # honeypot — must be empty
        }
        data.update(overrides)
        return data

    # ── Validity ──────────────────────────────────────────────────────────────

    def test_valid_form_is_valid(self):
        form = ContactForm(data=self._valid())
        self.assertTrue(form.is_valid(), form.errors)

    def test_missing_name_is_invalid(self):
        form = ContactForm(data=self._valid(name=""))
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)

    def test_missing_subject_is_invalid(self):
        form = ContactForm(data=self._valid(subject=""))
        self.assertFalse(form.is_valid())
        self.assertIn("subject", form.errors)

    def test_missing_message_is_invalid(self):
        form = ContactForm(data=self._valid(message=""))
        self.assertFalse(form.is_valid())
        self.assertIn("message", form.errors)

    def test_email_optional(self):
        form = ContactForm(data=self._valid(email=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_phone_optional(self):
        form = ContactForm(data=self._valid())
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email_format(self):
        form = ContactForm(data=self._valid(email="not-an-email"))
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    # ── Honeypot ──────────────────────────────────────────────────────────────

    def test_honeypot_filled_raises_validation_error(self):
        form = ContactForm(data=self._valid(website_url="http://spam.com"))
        self.assertFalse(form.is_valid())
        self.assertIn("website_url", form.errors)

    def test_honeypot_empty_passes(self):
        form = ContactForm(data=self._valid(website_url=""))
        self.assertTrue(form.is_valid(), form.errors)

    def test_honeypot_is_hidden_input(self):
        from django import forms as dj_forms
        form = ContactForm()
        self.assertIsInstance(form.fields["website_url"].widget, dj_forms.HiddenInput)

    # ── Widget types ──────────────────────────────────────────────────────────

    def test_message_widget_is_textarea(self):
        from django import forms as dj_forms
        form = ContactForm()
        self.assertIsInstance(form.fields["message"].widget, dj_forms.Textarea)

    def test_name_max_length(self):
        form = ContactForm(data=self._valid(name="A" * 151))
        self.assertFalse(form.is_valid())
        self.assertIn("name", form.errors)


class EmailSubscriptionFormTests(TestCase):

    def test_valid_form_is_valid(self):
        form = EmailSubscriptionForm(data={"email": "new@example.com", "full_name": "New User"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_email_required(self):
        form = EmailSubscriptionForm(data={"email": "", "full_name": "No Email"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_full_name_optional(self):
        form = EmailSubscriptionForm(data={"email": "nameopt@example.com"})
        self.assertTrue(form.is_valid(), form.errors)

    def test_invalid_email_rejected(self):
        form = EmailSubscriptionForm(data={"email": "invalid-email"})
        self.assertFalse(form.is_valid())

    def test_valid_form_saves_subscriber(self):
        form = EmailSubscriptionForm(data={"email": "saved@example.com", "full_name": "Saved"})
        self.assertTrue(form.is_valid())
        sub = form.save()
        self.assertIsNotNone(sub.pk)
        self.assertEqual(sub.email, "saved@example.com")

    def test_duplicate_email_is_invalid(self):
        EmailSubscriber.objects.create(email="dup@example.com")
        form = EmailSubscriptionForm(data={"email": "dup@example.com"})
        self.assertFalse(form.is_valid())
        self.assertIn("email", form.errors)

    def test_form_has_email_and_full_name_fields(self):
        form = EmailSubscriptionForm()
        self.assertIn("email", form.fields)
        self.assertIn("full_name", form.fields)
