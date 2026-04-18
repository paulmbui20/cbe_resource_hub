"""
website/views.py

Public-facing homepage and contact page views.
"""
from __future__ import annotations

from typing import Any

from django.contrib import messages
from django.db.models import Sum
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from notifications.notifier import notify_contact_form
from resources.models import EducationLevel, LearningArea, ResourceItem
from website.forms import ContactForm, EmailSubscriptionForm
from website.models import Partner, ContactMessage


class HomePageView(TemplateView):
    template_name = "website/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)

        # Latest 8 free resources for hero cards
        ctx["featured_resources"] = (
            ResourceItem.objects.select_related(
                "grade", "grade__level", "learning_area"
            )
            .filter(is_free=True)[:8]
        )

        # Top 8 popular resources by downloads
        ctx["popular_resources"] = (
            ResourceItem.objects.select_related(
                "grade", "grade__level", "learning_area"
            )
            .filter(is_free=True)
            .order_by("-downloads")[:8]
        )

        # Stats strip
        ctx["total_resources"] = ResourceItem.objects.count()
        ctx["total_levels"] = EducationLevel.objects.count()
        ctx["total_areas"] = LearningArea.objects.count()
        ctx["total_downloads"] = ResourceItem.objects.aggregate(d=Sum("downloads"))["d"] or 0
        ctx["education_levels"] = (
            EducationLevel.objects.prefetch_related("grades").order_by("order")
        )

        # Resource type cards with icon, label, desc, count
        resource_type_cards = []
        from resources.views import RESOURCE_TYPE_INFO
        for key, info in RESOURCE_TYPE_INFO.items():
            count = ResourceItem.objects.filter(resource_type=key, is_free=True).count()
            resource_type_cards.append({
                "key": key,
                "icon": info["icon"],
                "label": info["label"],
                "desc": info["desc"],
                "count": count,
            })
        ctx["resource_type_cards"] = resource_type_cards

        # Partners for homepage section (show_as_banner=True ones)
        ctx["homepage_partners"] = Partner.objects.filter(show_as_banner=True).order_by("name")

        return ctx


class ContactView(FormView):
    template_name = "website/contact.html"
    form_class = ContactForm

    def get_success_url(self):
        return reverse("contact")

    def form_valid(self, form):
        data = form.cleaned_data

        # Persist to database so admins can read it in the management panel
        msg = ContactMessage.objects.create(
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            subject=data["subject"],
            message=data["message"],
        )

        # Trigger robust async notification
        notify_contact_form(msg)

        messages.success(
            self.request,
            "Your message has been sent successfully. We will get back to you shortly.",
        )
        return super().form_valid(form)

    def form_invalid(self, form):
        messages.error(self.request, "Please fix the errors below and try again.")
        return super().form_invalid(form)

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["default_topics"] = [
            "Resource upload & sharing guidelines",
            "Becoming a verified content creator",
            "Curriculum alignment questions",
            "Reporting inappropriate content",
            "Technical issues or bugs",
            "Partnership & collaboration",
        ]
        return ctx


def email_subscription(request):
    template_partial = "partials/htmx_notification.html"
    original_form_partial_template = "partials/email_subscription_form.html"
    form = EmailSubscriptionForm(request.POST)
    if request.POST:
        if form.is_valid():
            try:
                form.save()
                context = {
                    "success": True,
                    "message": "Email has been sent successfully!",
                }
                return render(request, template_partial, context=context)

            except Exception as e:
                context = {
                    "success": False,
                    "message": f"Error! {str(e)}",
                }
                return render(request, original_form_partial_template, context=context)

        else:
            context = {}
            # Handle form validation errors
            for field, errors in form.errors.items():
                for error in errors:
                    context = {
                        "success": False,
                        "message": f"Error on form! : {field.replace('_', ' ').title()}: {error}",
                        "form": form,
                    }

            return render(request, original_form_partial_template, context=context)
    else:
        context = {
            "success": False,
            "message": "Http method not supported.",
        }

        return render(request, original_form_partial_template, context=context)


class PartnerListView(TemplateView):
    """Public page listing all partners."""
    template_name = "website/partners.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["partners"] = Partner.objects.all().order_by("name")
        return ctx
