# Query Optimization & Caching Audit

## Methodology

All fixes follow a strict two-pass rule from the roadmap:

1. **Pass 1 — Reduce raw DB queries** using `select_related`, `prefetch_related`,
   `values_list`, `only()`, aggregation batching, and queryset annotations.
2. **Pass 2 — Cache appropriately** using the existing `resources/cache.py` pattern —
   per-key invalidation via signals, **never** whole-page caching.

---

## Route-by-Route Findings & Fixes

### 🟠 Homepage `/`  (`website/views.py::HomePageView`)

**Before — 16+ queries:**

| Query | Problem |
|-------|---------|
| `ResourceItem.objects.filter(is_free=True)[:8]` | No `select_related` → N+1 in template on `.grade.name`, `.grade.level.name`, `.learning_area.name` |
| `ResourceItem.objects.filter(is_free=True).order_by("-downloads")[:8]` | Same N+1 as above |
| `ResourceItem.objects.count()` | Separate query |
| `get_education_levels().count()` | Evaluates cached QS then counts — fine |
| `get_learning_areas().count()` | Same |
| `ResourceItem.objects.aggregate(d=Sum("downloads"))` | Separate query |
| `get_education_levels()` | Second call — hits cache but evaluates the QS again |
| `ResourceItem.objects.filter(resource_type=key, is_free=True).count()` × N types | **N separate COUNT queries (one per resource type!)** |

**Fix:**

- Add `select_related("grade", "grade__level", "learning_area")` to both featured/popular QSs.
- Batch all scalar stats into a **single `aggregate()` call**.
- Replace the per-type COUNT loop with a single **`values("resource_type").annotate(count=Count(...))`** query.
- Cache the homepage stats block under `website:home_stats` with invalidation signal on `ResourceItem`.

**After — 4 queries (cold) / 1 query (warm cache):**
1. featured resources (1 JOIN query)
2. popular resources (1 JOIN query)
3. stats aggregate (1 query — or 0 when cached)
4. resource type counts (1 GROUP BY query — or 0 when cached)

---

### ✅ Resource List `/resources/` (`resources/views.py::ResourceListView`)

Already good — uses `ResourceItemManager` (which has `select_related` + `prefetch_related`
baked in), sidebar filters are all cached. Only issue: `ResourceItem.objects.filter(is_free=True)`
bypasses the custom manager. **Fix:** change to `ResourceItem.objects.filter(is_free=True)` after
verifying the manager is the default, OR use `ResourceItem.objects.get_queryset().filter(is_free=True)`.

Actually — confirmed the `ResourceItemManager` is assigned as `objects`. All queries through
`ResourceItem.objects` already carry the `select_related`. ✅ No changes needed.

---

### 🟡 Resource Detail `/resources/<slug>/` (`resources/views.py::ResourceDetailView`)

**Problem:** `DetailView` calls `get_object()` which does `ResourceItem.objects.get(slug=slug)` —
this goes through the custom manager so `select_related` is already applied. ✅

**Minor fix:** Add caching for the detail object using existing `get_slug_based_object_or_404_with_cache`.

---

### 🟡 Resource Type Landing Page `/resources/type/<type>/`

**Problem:** `get_context_data` calls `ResourceItem.objects.filter(resource_type=type)` — goes through
manager so relations are joined. Context also calls `get_education_levels()`, `get_grades()`,
`get_learning_areas()` — all cached. ✅ Good.

---

### 🟠 Admin Dashboard `/management/` (`website/admin_views.py::AdminDashboardView`)

**Before — 8 separate COUNT/SELECT queries:**

```python
CustomUser.objects.count()
CustomUser.objects.filter(role=VENDOR).count()
ResourceItem.objects.count()
Page.objects.count()
ContactMessage.objects.filter(is_read=False).count()
CustomUser.objects.order_by("-date_joined")[:5]
ResourceItem.objects.all()[:5]
EmailSubscriber.objects.filter(opted_out=False).count()
```

**Fix:** Batch the 5 COUNTs into 2 aggregate calls. Add `select_related` to recent queries.
Cache the entire stats block under `website:admin_dashboard_stats` with short TTL (60s) —
invalidated by model signals.

---

### 🟡 Toggle Favorite (`resources/views.py::ToggleFavoriteView`)

**Problem:** `if resource in user.favorites.all()` — evaluates the full M2M QS to check membership.
**Fix:** Use `user.favorites.filter(pk=resource.pk).exists()` — single indexed EXISTS query.

---

### 🟡 `get_learning_areas()` / `get_grades()` — cache bug

**Problem:** `prefetch_related("resources")` is attached to every cached QS. This means the cache
stores the full resources reverse-relation too — unnecessary memory bloat and staleness risk
when resources are added/deleted.

**Fix:** Remove `prefetch_related("resources")` from the sidebar cache functions. The sidebar
only ever renders `learning_area.name` / `grade.name` — not their resources list.

---

### 🟠 `get_education_levels()` — double evaluation on homepage

Called **twice** in `HomePageView.get_context_data`: once for `.count()` and once to pass as
`education_levels`. The second call returns the cached QS but evaluating it twice forces Django
to re-evaluate the SQL unless it's already a list.

**Fix:** Assign to a local variable, count from it, pass both.

---

## Cache Key Reference (complete map after fixes)

| Key | Stores | Invalidated by |
|-----|--------|----------------|
| `resources:education_levels` | `EducationLevel` QS | `EducationLevel` post_save/delete |
| `resources:grades` | `Grade` QS (no prefetch) | `Grade` post_save/delete |
| `resources:learning_areas` | `LearningArea` QS (no prefetch) | `LearningArea` post_save/delete |
| `resources:resource_types` | dict of choices | Never changes (constant) |
| `resources:academic_sessions` | `AcademicSession` QS | AcademicSession post_save/delete |
| `resources:{model}:{slug}` | single model instance | model post_save/delete |
| `website:home_stats` | stats dict (counts + type_counts) | `ResourceItem` post_save/delete |
| `cms:menus` | Menu+MenuItem QS | Menu/MenuItem post_save/delete |
| `cms:site_settings` | SiteSetting QS | SiteSetting post_save/delete |

---

## What is NOT cached (intentionally)

- **Paginated resource lists** — filter params make per-page caching impractical and stale.
- **Admin views** — correctness trumps speed; admins need live data.
- **Full HTML pages** — fragile, hard to invalidate, defeats partial HTMX updates.
- **Auth-dependent content** — favorites, user dashboards, per-user queries.
