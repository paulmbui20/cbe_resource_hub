# Homepage Architecture

This document describes the CBE Resource Hub homepage (`/`) design, sections, data flow, and extension patterns.

---

## Sections (in render order)

| #   | Section                        | Template element                     | Data source                                |
|-----|--------------------------------|--------------------------------------|--------------------------------------------|
| 1   | **Hero + live search**         | `#heroSearch` + suggestions dropdown | HTMX `GET /resources/?q=…&suggestions=1`   |
| 2   | **Resource type cards**        | `#resource-types` grid               | `context["resource_type_cards"]` (view)    |
| 3   | **Education levels**           | `#levels` pill strip                 | `context["education_levels"]`              |
| 4   | **Recent / Popular resources** | Alpine tab switcher                  | `featured_resources` / `popular_resources` |
| 5   | **Animated stats**             | `#stats-section`                     | `total_resources`, `total_downloads`, etc. |
| 6   | **Why CBE Hub**                | 6-feature grid                       | Hardcoded in template                      |
| 7   | **CTA strip**                  | Gradient banner                      | –                                          |
| 8   | **Partners**                   | Subtle footer section                | `homepage_partners` (show_as_banner=True)  |
| FAB | **Scroll-to-top**              | Fixed bottom-right button            | Vanilla JS scroll listener                 |

---

## View Context — `HomePageView`

File: `website/views.py`

| Key                   | Type       | Notes                                                     |
|-----------------------|------------|-----------------------------------------------------------|
| `featured_resources`  | QuerySet   | 8 newest free ResourceItems                               |
| `popular_resources`   | QuerySet   | 8 most-downloaded free ResourceItems                      |
| `total_resources`     | int        | All ResourceItems count                                   |
| `total_levels`        | int        | EducationLevel count                                      |
| `total_areas`         | int        | LearningArea count                                        |
| `total_downloads`     | int        | Sum of `downloads` field across all items                 |
| `education_levels`    | QuerySet   | All EducationLevels ordered by `order`, prefetch `grades` |
| `resource_type_cards` | list[dict] | `{ key, icon, label, desc, count }` per type              |
| `homepage_partners`   | QuerySet   | Partners with `show_as_banner=True`                       |

---

## Live Search (HTMX)

### How it works

1. User types in `#heroSearch`.
2. Alpine debounces 300 ms, then sets `hx-get` on `#searchSuggestions` and triggers HTMX.
3. HTMX `GET /resources/?q=<query>&suggestions=1` hits `ResourceListView`.
4. View detects `suggestions=1` and renders `resources/partials/search_suggestions.html` (partial).
5. Partial returns up to 6 items + optional "See all N results" link.
6. Pressing `Enter` or clicking "Search" navigates to full `/resources/?q=<query>`.

### Partial template

`website/templates/resources/partials/search_suggestions.html`

Context variables available inside the partial:

- `resources` — filtered QuerySet (same as normal list view)
- `search_query` — the raw `q` param value
- `page_obj` — Page object (use `page_obj.paginator.count` for total matches)

---

## Resource Type Cards

Cards are generated in `HomePageView.get_context_data` from `RESOURCE_TYPE_INFO` (defined in `resources/views.py`):

```python
RESOURCE_TYPE_INFO = {
    "lesson_plan": {"label": "Lesson Plans", "desc": "...", "icon": "📋"},
    "exam": {"label": "Exams & Tests", ...},
    # …
}
```

Each card links to `/resources/type/<key>/`, handled by `ResourceTypeDetailView`.

### Adding a new resource type

1. Add a `RESOURCE_TYPE` choice in `resources/models.ResourceItem`.
2. Add a matching entry to `RESOURCE_TYPE_INFO` in `resources/views.py`.
3. Add an `{% elif card.key == '<new_key>' %}` SVG block in `home.html` resource type card loop.
4. The new type immediately appears on the homepage and gets its own SEO landing page.

---

## Animated Stats Counter

### Pattern used

```
section#stats-section
  └── div[x-data="{ resources:0, … }" @animate-stats.window="animate()"]
        └── dd[x-text="resources.toLocaleString()"] … × 4

<script>
  // Vanilla IntersectionObserver → dispatches 'animate-stats' CustomEvent
  // when section enters viewport at 25% threshold
</script>
```

**Why not `x-intersect`?**
Alpine's `x-intersect` requires the `@alpinejs/intersect` plugin to be registered *before* `Alpine.start()`. With
`defer` scripts this ordering is fragile. The vanilla observer approach has no runtime dependencies beyond the
browser-native `IntersectionObserver` API.

---

## Partners Section

Only renders when `{% if homepage_partners %}` — i.e., there is at least one `Partner` with `show_as_banner=True`.

Partners render as grayscale logo images (if `logo.name` is set) or as text names. They link to `partner.link` (
defaulting to `#`). A "View all partners" link leads to `{% url 'partners' %}`.

> **FileField guard**: Always check `partner.logo and partner.logo.name` (not just `partner.logo`) before calling
`.url`, to avoid `ValueError` when the field record exists but has no associated file.

---

## Scroll-to-Top FAB

The `#scrollTopBtn` button is hidden by default (`opacity: 0; pointer-events: none`). A passive scroll listener shows it
after 200 px of scroll and hides it again at top. The transition is CSS `transition-all duration-300`.

No Alpine or HTMX required — pure vanilla JS in an IIFE at the bottom of `home.html`.
