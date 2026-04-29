"""
website/views.py

Public-facing homepage and contact page views.
"""

from django.contrib import messages
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import FormView, TemplateView

from notifications.notifier import notify_contact_form
from resources.cache import (
    get_education_levels,
    get_learning_areas,
    get_home_stats,
)
from resources.models import ResourceItem
from website.forms import ContactForm, EmailSubscriptionForm
from website.models import Partner, ContactMessage


class HomePageView(TemplateView):
    template_name = "website/home.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # ── Resource lists ────────────────────────────────────────────────
        # Both QSs go through ResourceItemManager which already applies
        # select_related("grade", "grade__level", "vendor", "learning_area", …)
        # so no N+1 hits when templates access .grade.name / .learning_area.name.
        context["featured_resources"] = (
            ResourceItem.objects.filter(is_free=True)[:8]
        )
        context["popular_resources"] = (
            ResourceItem.objects.filter(is_free=True)
            .order_by("-downloads")[:8]
        )

        # ── Stats strip (2 DB queries total, or 0 when cached) ────────────
        # get_home_stats() returns total_resources, total_downloads,
        # and resource_type_counts in a single aggregate + one GROUP BY query,
        # then caches the result under "website:home_stats".
        stats = get_home_stats()
        context["total_resources"] = stats["total_resources"]
        context["total_downloads"] = stats["total_downloads"]

        # ── Sidebar / nav data (all served from Redis after first request) ─
        # Assign to a local so we don't call get_education_levels() twice.
        education_levels = get_education_levels()
        context["education_levels"] = education_levels
        context["total_levels"] = len(education_levels)
        context["total_areas"] = len(get_learning_areas())

        # ── Resource type cards (counts come from the cached stats block) ──
        from resources.views import RESOURCE_TYPE_INFO
        type_counts = stats["resource_type_counts"]
        context["resource_type_cards"] = [
            {
                "key": key,
                "icon": info["icon"],
                "label": info["label"],
                "desc": info["desc"],
                "count": type_counts.get(key, 0),
            }
            for key, info in RESOURCE_TYPE_INFO.items()
        ]

        return context



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
        context = super().get_context_data(**kwargs)
        context["default_topics"] = [
            "Resource upload & sharing guidelines",
            "Becoming a verified content creator",
            "Curriculum alignment questions",
            "Reporting inappropriate content",
            "Technical issues or bugs",
            "Partnership & collaboration",
        ]
        return context


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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["partners"] = Partner.objects.all().order_by("name")
        return context
