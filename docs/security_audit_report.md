# Security Audit Report: CBE Resource Hub

**Date:** May 9, 2026
**Scope:** URL Endpoints and Views (Public & Custom Admin)

## Executive Summary

A comprehensive security sweep of the CBE Resource Hub endpoints and view implementations was conducted. The application leverages Django's robust built-in security mechanisms (such as the ORM to prevent SQLi and `CsrfViewMiddleware` to prevent CSRF). However, some critical broken access control and privilege escalation vulnerabilities were identified within the custom admin dashboard that require immediate remediation.

---

## 1. Privilege Escalation & Broken Access Control (High Severity)

**Location:** `accounts/admin_views.py`

**Description:**
The custom admin panel utilizes the `IsAdminMixin`, which correctly restricts access to users where `is_superuser == True` OR `role == CustomUser.Role.ADMIN`. However, once an `ADMIN` role user gains access to the user management views, there is no vertical privilege separation enforcing that an `ADMIN` cannot modify a `SUPERUSER`.

**Impact:**
A user with the `ADMIN` role can inadvertently or maliciously:

1. Delete a superuser via `AdminUserDeleteView`.
2. Modify a superuser's active status, email, or role via `AdminUserUpdateView`.
3. Disable a superuser via `AdminUserBulkToggleView`.

**Applied Fix (Completed):**
Restricted `ADMIN` users from querying or modifying `SUPERUSER` accounts.

- **In `AdminUserListView`, `AdminUserUpdateView` and `AdminUserDeleteView`:** Overrode `get_queryset()` to exclude superusers unless the `request.user` is also a superuser:

  ```python
  def get_queryset(self):
      qs = super().get_queryset()
      if not self.request.user.is_superuser:
          qs = qs.exclude(is_superuser=True)
      return qs
  ```

- **In `AdminUserBulkToggleView`:** Added a validation check to block modifications and return a 403 Forbidden if any of the target `user_ids` belong to a superuser (when the requester is just an `ADMIN`).

---

## 2. Insecure Direct Object References (IDOR) Protection (Secure)

**Location:** `resources/views.py` (`ResourceUpdateView`, `ResourceDeleteView`)

**Description:**
Vendors have the ability to edit and delete resources.

**Finding: SECURE**
The implementation correctly prevents IDOR. In both `ResourceUpdateView` and `ResourceDeleteView`, the `get_queryset()` method forces a filter: `qs.filter(vendor=self.request.user)`. This ensures that a vendor cannot tamper with `id` parameters in the URL to modify or delete resources belonging to other vendors. Superusers and admins are correctly granted bypass access.

---

## 3. Cross-Site Request Forgery (CSRF) (Secure)

**Location:** Global (`cbe_res_hub/settings.py` & All Views)

**Description:**
Django's `CsrfViewMiddleware` is active globally. All state-mutating HTTP methods (`POST`, `PUT`, `DELETE`) require a valid CSRF token.

**Finding: SECURE**

- Form submissions in templates properly utilize the `{% csrf_token %}` tag.
- API-like JSON endpoints (e.g., `AdminUserBulkToggleView`) do not possess `@csrf_exempt` decorators, meaning Django inherently protects them. The frontend must correctly supply the `X-CSRFToken` header for these requests to succeed, which prevents CSRF attacks effectively.

---

## 4. SQL Injection (SQLi) (Secure)

**Location:** Global Database Queries

**Description:**
User inputs are passed into the database to perform filtering, searching, and object creation.

**Finding: SECURE**
The application strictly utilizes the Django Object-Relational Mapper (ORM). There are no instances of `.raw()`, `RawSQL`, or direct `cursor.execute()` calls using unparameterized string formatting. Search queries (e.g., `q = self.request.GET.get("q")`) are safely parameterized by the ORM via `__icontains`.

---

## 5. Cross-Site Scripting (XSS) (Low Risk)

**Location:** Public CMS and Resource Pages

**Finding: MODERATE/SECURE**
Django templates automatically HTML-escape all context variables. However, content generated from rich-text editors (like TinyMCE used for `FAQ`, `Testimonial`, or `Page` bodies) is often marked as safe (`|safe`) in templates to render HTML properly.
**Recommendation:** Ensure that all inputs originating from TinyMCE (especially if vendors/users can submit them) are sanitized in the backend using a library like `bleach` before being saved to the database.

---

---

## 6. TinyMCE Input Sanitization (Completed)

**Location:** `website/models.py`, `resources/models.py`, `cms/models.py`

**Description:**
To prevent Cross-Site Scripting (XSS) from rich-text fields (TinyMCE), a sanitization layer was implemented using `django-nh3`.

**Applied Fix:**

1. **Installed `django-nh3`**: Added to dependencies via `uv`.
2. **Global Configuration**: Defined `NH3_ALLOWED_TAGS`, `NH3_ALLOWED_ATTRIBUTES`, and `NH3_CLEAN_CONTENT_TAGS` in `cbe_res_hub/settings/base.py` to allow safe HTML while stripping dangerous tags (like `<script>`, `<iframe>`) and attributes (like `onerror`).
3. **Custom Model Field**: Created `core.fields.SafeHTMLField` which inherits from `tinymce.models.HTMLField` and `django_nh3.models.Nh3FieldMixin`. This field automatically sanitizes input during the `pre_save` signal.
4. **Model Updates**: Replaced all instances of `HTMLField` with `SafeHTMLField` in `Partner`, `ResourceItem`, and `Page` models.
5. **Database Migration**: Applied migrations to reflect the change in field classes.

**Verification:**
Confirmed via testing that:

- `<script>` and `<iframe>` tags are stripped along with their content.
- Inline event handlers like `onerror` are removed from allowed tags like `<img>`.
- Safe formatting tags like `<b>`, `<i>`, `<u>` are preserved.
