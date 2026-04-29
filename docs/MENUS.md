# Menu System Quick-Start Guide

The CBE Resource Hub uses a fully database-driven navigation system. You manage menus entirely from the Admin Panel — no
code changes needed.

---

## How It Works

The system has two components:

| Model        | Purpose                                            |
|--------------|----------------------------------------------------|
| **Menu**     | A named slot (e.g. `primary_header` or `footer`)   |
| **MenuItem** | A link inside a menu — can be nested for dropdowns |

The **exact name** of the `Menu` object controls which template slot it appears in.

---

## Step 1 — Create a Menu

Go to: **Admin Panel → Architecture & Curriculum → Menus → + Add New Menu**

| Slot Location      | Required Name (case-sensitive) |
|--------------------|--------------------------------|
| Header navigation  | `primary_header`               |
| Footer quick links | `footer`                       |

> You can have **any number of menus** with other names for future use.

---

## Step 2 — Add Menu Items

Go to: **Admin Panel → Menu Items → + Add New Menu Item**

| Field      | Description                                                  |
|------------|--------------------------------------------------------------|
| **Menu**   | Select the menu this item belongs to                         |
| **Title**  | Link text shown to users                                     |
| **URL**    | `/resources/`, `/pages/about/`, `https://external.com`, etc. |
| **Order**  | Display position (0 = first)                                 |
| **Parent** | (Optional) Select another item to make this a dropdown child |

---

## Dropdown Menus

To create a dropdown in the header:

1. **Add a parent item** — set URL to `#` (or leave blank), give it a title like "Quick Links"
2. **Add child items** — set **Parent** to that item, fill in real URLs

The header automatically renders parent items with a chevron dropdown button.

---

## Examples

### Header

Create a menu named `primary_header` with these items:

| Title        | URL                                   | Order | Parent       |
|--------------|---------------------------------------|-------|--------------|
| About        | /pages/about/                         | 10    | —            |
| Resources    | /resources/                           | 20    | —            |
| For Teachers | #                                     | 30    | —            |
| Lesson Plans | /resources/?resource_type=lesson_plan | 1     | For Teachers |
| Exam Papers  | /resources/?resource_type=exam        | 2     | For Teachers |

### Footer

Create a menu named `footer` with these items:

| Title          | URL                    | Order |
|----------------|------------------------|-------|
| Privacy Policy | /pages/privacy/        | 10    |
| Terms of Use   | /pages/terms/          | 20    |
| Contact Us     | /contact/              | 30    |
| Open Source    | https://github.com/... | 40    |

---

## Using Menu Items in Custom Templates

If you ever build a custom template and need to render a specific menu:

```django
{% with menu=menus.primary_header %}
{% if menu %}
  {% for item in menu.items.all %}
    {% if not item.parent %}
    <a href="{{ item.url }}">{{ item.title }}</a>
    {% endif %}
  {% endfor %}
{% endif %}
{% endwith %}
```

The `menus` context variable is injected automatically by the **global context processor** — it's available on every
page without any extra view code.
