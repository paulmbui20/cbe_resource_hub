import json
import secrets
import string

from django.contrib import messages
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, TemplateView

from accounts.models import CustomUser
from notifications.notifier import notify_generic_message


class IsAdminMixin(UserPassesTestMixin):
    def test_func(self):
        return self.request.user.is_authenticated and (
                self.request.user.is_superuser or self.request.user.role == CustomUser.Role.ADMIN)


# ── Users ────────────────────────────────────────────────────────────────────
class AdminUserListView(IsAdminMixin, ListView):
    model = CustomUser
    template_name = "admin/user_list.html"
    context_object_name = "users"
    paginate_by = 30

    def get_queryset(self):
        qs = CustomUser.objects.all().order_by("-date_joined")
        q = self.request.GET.get("q")
        if q:
            qs = qs.filter(email__icontains=q)
        return qs


class AdminUserCreateView(IsAdminMixin, CreateView):
    model = CustomUser
    template_name = "admin/generic_form.html"
    fields = ["email", "first_name", "last_name", "is_active", "role", "is_vendor"]
    success_url = reverse_lazy("management:user_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = "Create New User"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        user = form.save(commit=False)
        print(user)
        print(user.email)
        alphabet = string.ascii_letters + string.digits + "!@#$%^&*"
        raw_password = "".join(secrets.choice(alphabet) for _ in range(12))

        user.set_password(raw_password)
        user.must_change_password = True
        user.save()
        message = f"User created securely! Their generated password is: {raw_password}"
        subject = "User created!"
        context = f"Username = {user.username}, email = {user.email}, role = {user.role}, date_joined = {user.date_joined}"

        messages.success(self.request, message)

        notify_generic_message(subject, message, context)
        return super().form_valid(form)


class AdminUserUpdateView(IsAdminMixin, UpdateView):
    model = CustomUser
    template_name = "admin/generic_form.html"
    fields = ["email", "first_name", "last_name", "is_active", "role", "is_vendor"]
    success_url = reverse_lazy("management:user_list")

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["title"] = f"Edit User: {self.object.email}"
        ctx["cancel_url"] = self.success_url
        return ctx

    def form_valid(self, form):
        message = f"User {self.object.email}  updated successfully."
        subject = "User updated!"
        context = f"Username = {self.object.username}, email = {self.object.email}, role = {self.object.role}, updated at: {timezone.now()}"
        notify_generic_message(subject, message, context)
        messages.success(self.request, message)
        return super().form_valid(form)


class AdminUserDeleteView(IsAdminMixin, DeleteView):
    model = CustomUser
    success_url = reverse_lazy("management:user_list")

    def form_valid(self, form):
        message = f"User {self.object.email} deleted permanently."
        subject = "User deleted!"
        context = f"Username = {self.object.username}, email = {self.object.email}, deleted at: {timezone.now()}"
        notify_generic_message(subject, message, context)
        messages.success(self.request, message)
        return super().form_valid(form)


class AdminUserBulkToggleView(IsAdminMixin, TemplateView):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            action = data.get("action")
            user_ids = data.get("user_ids", [])

            if action not in ["enable", "disable"] or not user_ids:
                return JsonResponse({"error": "Invalid request"}, status=400)

            # Guard against disabling self
            if action == "disable" and str(request.user.id) in [str(u) for u in user_ids]:
                return JsonResponse({"error": "You cannot disable your own account."}, status=403)

            is_active_val = (action == "enable")
            updated = CustomUser.objects.filter(id__in=user_ids).update(is_active=is_active_val)
            messages.success(request, f"Successfully {action}d {updated} users.")
            return JsonResponse({"success": True})

        except Exception as e:
            return JsonResponse({"error": str(e)}, status=400)
