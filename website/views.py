"""
website/views.py

Public-facing homepage and contact page views.
"""
from __future__ import annotations

from typing import Any

from django.conf import settings
from django.contrib import messages
from django.core.mail import send_mail
from django.views.generic import FormView, TemplateView

from resources.models import EducationLevel, LearningArea, ResourceItem
from resources.views import RESOURCE_TYPE_INFO
from website.forms import ContactForm
from website.models import Partner


class HomePageView(TemplateView):
    template_name = "website/home.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)

        # Latest 8 free resources for hero cards
        ctx["featured_resources"] = (
            ResourceItem.objects.select_related(
                "grade", "grade__level", "learning_area"
            )
            .filter(is_free=True)
            .order_by("-created_at")[:8]
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
        from django.db.models import Sum
        ctx["total_resources"]  = ResourceItem.objects.count()
        ctx["total_levels"]     = EducationLevel.objects.count()
        ctx["total_areas"]      = LearningArea.objects.count()
        ctx["total_downloads"]  = ResourceItem.objects.aggregate(d=Sum("downloads"))["d"] or 0
        ctx["education_levels"] = (
            EducationLevel.objects.prefetch_related("grades").order_by("order")
        )

        # Resource type cards with icon, label, desc, count
        resource_type_cards = []
        for key, info in RESOURCE_TYPE_INFO.items():
            count = ResourceItem.objects.filter(resource_type=key, is_free=True).count()
            resource_type_cards.append({
                "key":   key,
                "icon":  info["icon"],
                "label": info["label"],
                "desc":  info["desc"],
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
        from django.urls import reverse
        return reverse("contact")

    def form_valid(self, form):
        data = form.cleaned_data
        support_email = getattr(settings, "DEFAULT_FROM_EMAIL")

        # Persist to database so admins can read it in the management panel
        from website.models import ContactMessage
        msg = ContactMessage.objects.create(
            name=data["name"],
            email=data.get("email"),
            phone=data.get("phone"),
            subject=data["subject"],
            message=data["message"],
        )

        # Trigger robust async notification
        from notifications.notifier import notify_contact_form
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



class PartnerListView(TemplateView):
    """Public page listing all partners."""
    template_name = "website/partners.html"

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        ctx = super().get_context_data(**kwargs)
        ctx["partners"] = Partner.objects.all().order_by("name")
        return ctx
