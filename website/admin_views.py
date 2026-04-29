from django.contrib import messages
from django.db.models import Q
from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, UpdateView, CreateView, DeleteView, DetailView

from accounts.admin_views import IsAdminMixin
from accounts.models import CustomUser
from cms.models import Page
from resources.models import ResourceItem
from website.models import ContactMessage, Partner, EmailSubscriber


# ── Dashboard ────────────────────────────────────────────────────────────────
class AdminDashboardView(IsAdminMixin, TemplateView):
    template_name = "admin/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Batch user-related COUNTs into a single annotated aggregate.
        from django.db.models import Count, Q
        user_agg = CustomUser.objects.aggregate(
            total=Count("id"),
            vendors=Count("id", filter=Q(role=CustomUser.Role.VENDOR)),
        )
        context["total_users"] = user_agg["total"]
        context["total_vendors"] = user_agg["vendors"]

        # Batch resource/page/contact COUNTs into a single query each — these
        # hit different tables so they can't be collapsed further without raw SQL.
        context["total_resources"] = ResourceItem.objects.count()
        context["total_pages"] = Page.objects.count()
        context["unread_messages"] = ContactMessage.objects.filter(is_read=False).count()
        context["total_email_subscribers"] = EmailSubscriber.objects.filter(opted_out=False).count()

        # Recent items — select_related to avoid N+1 in the template
        context["recent_users"] = CustomUser.objects.order_by("-date_joined").only(
            "id", "email", "first_name", "last_name", "role", "date_joined"
        )[:5]
        context["recent_resources"] = ResourceItem.objects.order_by("-created_at")[:5]

        return context



# ── Contact Messages ─────────────────────────────────────────────────────────
class AdminContactMessageListView(IsAdminMixin, ListView):
    model = ContactMessage
    template_name = "admin/contact_message_list.html"
    context_object_name = "contact_messages"
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["unread_count"] = ContactMessage.objects.filter(is_read=False).count()
        return context


class AdminContactMessageDetailView(IsAdminMixin, DetailView):
    model = ContactMessage
    template_name = "admin/contact_message_detail.html"
    context_object_name = "msg"

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        # auto-mark as read when admin opens it
        obj = self.get_object()
        if not obj.is_read:
            obj.is_read = True
            obj.save(update_fields=["is_read"])
        return response


class AdminContactMessageDeleteView(IsAdminMixin, DeleteView):
    model = ContactMessage
    success_url = reverse_lazy("management:contact_list")

    def form_valid(self, form):
        messages.success(self.request, "Contact message deleted.")
        return super().form_valid(form)


# ── Partners ─────────────────────────────────────────────────────────────────
class AdminPartnerListView(IsAdminMixin, ListView):
    model = Partner
    template_name = "admin/partner_list.html"
    context_object_name = "partners"
    paginate_by = 30


class AdminPartnerCreateView(IsAdminMixin, CreateView):
    model = Partner
    template_name = "admin/seo_form.html"
    fields = ["name", "slug", "link", "description", "logo", "show_as_banner", "banner_cta",
              "meta_title", "meta_description", "meta_keywords", "featured_image"]
    success_url = reverse_lazy("management:partner_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New Partner"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Partners"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Partner '{form.instance.name}' added successfully.")
        return super().form_valid(form)


class AdminPartnerUpdateView(IsAdminMixin, UpdateView):
    model = Partner
    template_name = "admin/seo_form.html"
    fields = ["name", "slug", "link", "description", "logo", "show_as_banner", "banner_cta",
              "meta_title", "meta_description", "meta_keywords", "featured_image"]
    success_url = reverse_lazy("management:partner_list")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Partner: {self.object.name}"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Partners"
        return context

    def form_valid(self, form):
        messages.success(self.request, "Partner updated successfully.")
        return super().form_valid(form)


class AdminPartnerDeleteView(IsAdminMixin, DeleteView):
    model = Partner
    success_url = reverse_lazy("management:partner_list")

    def form_valid(self, form):
        messages.success(self.request, "Partner deleted.")
        return super().form_valid(form)


# Email Subscribers
class AdminEmailSubscribersListView(IsAdminMixin, ListView):
    template_name = "admin/email_subscribers_list.html"
    context_object_name = "email_subscribers"
    paginate_by = 20

    def get_queryset(self):
        qs = EmailSubscriber.objects.all()

        q = self.request.GET.get("q")
        q = str(q) if q else ""
        if q:
            qs = qs.filter(
                Q(email__icontains=q) | Q(full_name__icontains=q)
            )

        return qs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["opted_out_count"] = EmailSubscriber.objects.filter(opted_out=True).count()
        context["search_query"] = self.request.GET.get("q")

        return context


class AdminEmailSubscribersCreateView(IsAdminMixin, CreateView):
    model = EmailSubscriber
    template_name = "admin/generic_form.html"
    fields = [
        "full_name", "email", "opted_out",
    ]
    success_url = reverse_lazy("management:email_subscribers")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add an Email Subscriber"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Email Subscribers"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Email subscriber {form.instance.email} created successfully.")
        return super().form_valid(form)


class AdminEmailSubscriberEdit(IsAdminMixin, UpdateView):
    model = EmailSubscriber
    template_name = "admin/generic_form.html"
    fields = [
        "full_name", "email", "opted_out"
    ]
    success_url = reverse_lazy("management:email_subscribers")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = f"Edit Email Subscriber: {self.object.email}"
        context["cancel_url"] = self.success_url
        context["parent_title"] = "Email Subscribers"
        return context

    def form_valid(self, form):
        messages.success(self.request, f"Email subscriber {form.instance.email} updated.")
        return super().form_valid(form)


class AdminEmailSubscriberDeleteView(IsAdminMixin, DeleteView):
    model = EmailSubscriber
    success_url = reverse_lazy("management:email_subscribers")

    def form_valid(self, form):
        messages.success(self.request, "Email subscriber deleted.")
        return super().form_valid(form)
