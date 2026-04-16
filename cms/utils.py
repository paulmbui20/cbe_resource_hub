def slug_to_title(slug: str) -> str:
    slug = slug
    if "-" in slug:
        slug = slug.replace("-", " ")
    if "_" in slug:
        slug = slug.replace("_", " ")
    slug = slug.title()
    return slug
