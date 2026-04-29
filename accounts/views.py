"""accounts/views.py"""

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import redirect
from django.urls import reverse_lazy
from django.views.generic import TemplateView, UpdateView, View

from .forms import ProfileForm
from .models import CustomUser


class DashboardView(LoginRequiredMixin, TemplateView):
    """Authenticated user dashboard — overview of account + recent activity."""
    template_name = "accounts/dashboard.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user

        # Resources uploaded by this user (vendor context)
        from resources.models import ResourceItem
        context["my_resources"] = (
            ResourceItem.objects.select_related("grade", "grade__level", "learning_area")
            .filter(vendor=user)
            .order_by("-created_at")[:10]
        )
        context["my_resource_count"] = ResourceItem.objects.filter(vendor=user).count()

        # Allauth email verification status
        try:
            from allauth.account.models import EmailAddress
            context["email_verified"] = EmailAddress.objects.filter(
                user=user, verified=True
            ).exists()
        except Exception:
            context["email_verified"] = False

        # User's favorites
        context["my_favorites"] = (
            user.favorites.all()[:10]
        )
        context["my_favorites_count"] = user.favorites.count()

        return context


class ProfileView(LoginRequiredMixin, UpdateView):
    """Edit own profile — name + phone number."""
    model = CustomUser
    form_class = ProfileForm
    template_name = "accounts/profile.html"
    success_url = reverse_lazy("accounts:dashboard")

    def get_object(self, queryset=None):
        return self.request.user

    def form_valid(self, form):
        messages.success(self.request, "Profile updated successfully.")
        return super().form_valid(form)


class BecomeVendorView(LoginRequiredMixin, View):
    """
    Allows a standard user to become a vendor.
    Only users with role == USER can upgrade themselves to VENDOR.
    """
    http_method_names = [
        'post',
    ]

    def post(self, request, *args, **kwargs):
        user = request.user
        if user.role == CustomUser.Role.USER:
            user.role = CustomUser.Role.VENDOR
            user.is_vendor = True
            user.save(update_fields=["role", "is_vendor"])
            messages.success(request, "You are now a Content Creator! You can start uploading resources.")
        elif user.role == CustomUser.Role.ADMIN or user.is_superuser or user.is_staff:
            messages.warning(request, "Admins inherently have creator privileges.")
        else:
            messages.info(request, "You are already a Content Creator.")

        return redirect("accounts:dashboard")
