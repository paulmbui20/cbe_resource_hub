from wagtail.test.utils import WagtailPageTests
from wagtail.models import Page, Site
from website.models import (
    BlogIndexPage,
    BlogPage,
    BlogAuthor,
    CustomImage,
    BlogCategory,
)
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image


def get_test_image_file():
    f = io.BytesIO()
    Image.new("RGB", (100, 100)).save(f, "PNG")
    f.seek(0)
    return SimpleUploadedFile("test.png", f.read(), content_type="image/png")


class BlogTests(WagtailPageTests):
    def setUp(self):
        # Get the Wagtail root
        wagtail_root = Page.objects.get(id=1)
        self.root = wagtail_root.get_first_child() or wagtail_root

        # Create an image
        self.image = CustomImage.objects.create(
            title="Test Image",
            file=get_test_image_file(),
        )

        # Create an author
        self.author = BlogAuthor.objects.create(
            name="Test Author", role="Editor", bio="Test Bio", image=self.image
        )

        # Create blog index
        self.blog_index = BlogIndexPage(
            title="Blog", slug="blog", intro="Welcome to our blog"
        )
        self.root.add_child(instance=self.blog_index)
        self.blog_index.save_revision().publish()

        # Point site root to our home page so URLs resolve
        Site.objects.update_or_create(
            hostname="localhost",
            port=80,
            defaults={"root_page": self.root, "is_default_site": True},
        )

        # Create a category
        self.category = BlogCategory.objects.create(name="Tech", slug="tech")

        self.blog_post = BlogPage(
            title="Test Post",
            slug="test-post",
            intro="Test Intro",
            body=[
                (
                    "paragraph",
                    "<h2>Heading 1</h2><p>Some content for reading time calculation.</p>",
                )
            ],
            author=self.author,
            main_image=self.image,
            date="2024-05-10",
        )
        self.blog_index.add_child(instance=self.blog_post)
        self.blog_post.categories.add(self.category)
        self.blog_post.save_revision().publish()

    def test_blog_author_str(self):
        self.assertEqual(str(self.author), "Test Author")

    def test_blog_index_context(self):
        response = self.client.get(self.blog_index.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("blogpages", response.context)
        self.assertEqual(len(response.context["blogpages"]), 1)
        self.assertEqual(response.context["blogpages"][0].id, self.blog_post.id)

    def test_blog_post_view_increment(self):
        initial_views = self.blog_post.views
        # Accessing the page should increment views
        response = self.client.get(self.blog_post.url)
        self.assertEqual(response.status_code, 200)

        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.views, initial_views + 1)

    def test_reading_time(self):
        # Default speed is ~200 wpm. Our body has few words.
        self.assertEqual(self.blog_post.reading_time, 1)

        # Add a lot of words
        self.blog_post.body = [("paragraph", "<p>" + "word " * 500 + "</p>")]
        self.blog_post.save()
        self.assertEqual(self.blog_post.reading_time, 3)  # 500 / 200 = 2.5 -> round 3

    def test_blog_post_context(self):
        response = self.client.get(self.blog_post.url)
        self.assertEqual(response.status_code, 200)

        # Check optimized context variables
        self.assertIn("tags", response.context)
        self.assertIn("parent", response.context)
        self.assertIn("prev_post", response.context)
        self.assertIn("next_post", response.context)

        self.assertEqual(response.context["parent"].id, self.blog_index.id)

    def test_blog_index_tag_filtering(self):
        # Add a tag to the post
        self.blog_post.tags.add("test-tag")
        self.blog_post.save_revision().publish()

        # Filter by tag using the new route
        response = self.client.get(self.blog_index.url + "tag/test-tag/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["blogpages"]), 1)
        self.assertEqual(response.context["filter_type"], "Tag")

    def test_blog_index_category_filtering(self):
        response = self.client.get(self.blog_index.url + "category/tech/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["blogpages"]), 1)
        self.assertEqual(response.context["filter_type"], "Category")
        self.assertEqual(response.context["filter_term"], "Tech")

    def test_blog_index_author_filtering(self):
        response = self.client.get(self.blog_index.url + f"author/{self.author.slug}/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context["blogpages"]), 1)
        self.assertEqual(response.context["filter_type"], "Author")
        self.assertEqual(response.context["filter_term"], self.author.name)

    def test_social_share_links_in_template(self):
        response = self.client.get(self.blog_post.url)
        # Check if social share URLs are present (Facebook, WhatsApp, Telegram)
        self.assertContains(response, "facebook.com/sharer/sharer.php")
        self.assertContains(response, "api.whatsapp.com/send")
        self.assertContains(response, "t.me/share/url")
        # Instagram "copy" button
        self.assertContains(response, "Instagram")

    def test_author_section_in_template(self):
        response = self.client.get(self.blog_post.url)
        self.assertContains(response, self.author.name)
        self.assertContains(response, self.author.role)
        self.assertContains(response, self.author.bio)
        # Check archive link
        self.assertContains(response, f"author/{self.author.slug}/")

    def test_faqs_rendering(self):
        # Add an FAQ
        from website.models import BlogPageFAQ

        BlogPageFAQ.objects.create(
            page=self.blog_post, question="How to test?", answer="<p>Like this.</p>"
        )

        response = self.client.get(self.blog_post.url)
        self.assertContains(response, "How to test?")
        self.assertContains(response, "Like this.")

    def test_toc_placeholder_logic(self):
        # With headings in body, TOC should show headings
        response = self.client.get(self.blog_post.url)
        self.assertContains(response, 'id="toc-sidebar-container"')
        # TOC is generated via JS, so we can't easily assert on the nav content here,
        # but we checked the container.


class BlogCommentTests(WagtailPageTests):
    """Tests for the HTMX-driven comment system."""

    def setUp(self):
        wagtail_root = Page.objects.get(id=1)
        self.root = wagtail_root.get_first_child() or wagtail_root

        self.image = CustomImage.objects.create(
            title="Comment Test Image",
            file=get_test_image_file(),
        )
        self.author = BlogAuthor.objects.create(
            name="Comment Author", role="Writer", bio="Bio", image=self.image
        )
        self.blog_index = BlogIndexPage(
            title="Blog", slug="blog-comments", intro="Blog"
        )
        self.root.add_child(instance=self.blog_index)
        self.blog_index.save_revision().publish()

        Site.objects.update_or_create(
            hostname="localhost",
            port=80,
            defaults={"root_page": self.root, "is_default_site": True},
        )

        self.blog_post = BlogPage(
            title="Comment Test Post",
            slug="comment-test-post",
            intro="Intro",
            body=[("paragraph", "<h2>Test</h2><p>Content.</p>")],
            author=self.author,
            main_image=self.image,
            date="2024-06-01",
        )
        self.blog_index.add_child(instance=self.blog_post)
        self.blog_post.save_revision().publish()

        self.comment_url = f"/blog/{self.blog_post.pk}/comment/"

    # ── POST valid anonymous comment ──────────────────────────────────────
    def test_anon_can_post_comment(self):
        response = self.client.post(
            self.comment_url,
            {
                "name": "Alice Anon",
                "email": "alice@example.com",
                "body": "Great article, thank you!",
                "website_url": "",  # honeypot empty
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        from website.models import BlogComment
        self.assertTrue(
            BlogComment.objects.filter(page=self.blog_post, name="Alice Anon").exists()
        )

    # ── Honeypot rejects bots ─────────────────────────────────────────────
    def test_honeypot_rejects_submission(self):
        response = self.client.post(
            self.comment_url,
            {
                "name": "Bot",
                "email": "bot@example.com",
                "body": "Buy cheap stuff at http://spam.com",
                "website_url": "http://iambot.com",  # honeypot filled!
            },
            HTTP_HX_REQUEST="true",
        )
        # Should get 422 with form errors
        self.assertEqual(response.status_code, 422)
        from website.models import BlogComment
        self.assertFalse(
            BlogComment.objects.filter(name="Bot").exists()
        )

    # ── Spam filter: too many URLs ────────────────────────────────────────
    def test_spam_link_body_rejected(self):
        spammy_body = " ".join(
            [f"Buy at http://spam{i}.com" for i in range(10)]
        )
        response = self.client.post(
            self.comment_url,
            {
                "name": "Spammer",
                "email": "",
                "body": spammy_body,
                "website_url": "",
            },
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 422)

    # ── GET is not allowed on the comment endpoint ────────────────────────
    def test_get_not_allowed(self):
        response = self.client.get(self.comment_url)
        self.assertEqual(response.status_code, 405)

    # ── Comments appear on blog detail page ──────────────────────────────
    def test_comments_shown_in_context(self):
        from website.models import BlogComment
        BlogComment.objects.create(
            page=self.blog_post,
            name="Visible User",
            body="This comment should appear.",
            is_approved=True,
        )
        BlogComment.objects.create(
            page=self.blog_post,
            name="Hidden User",
            body="This comment should NOT appear.",
            is_approved=False,
        )
        response = self.client.get(self.blog_post.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn("comments", response.context)
        approved = list(response.context["comments"])
        names = [c.name for c in approved]
        self.assertIn("Visible User", names)
        self.assertNotIn("Hidden User", names)

    # ── Auth user auto-fills identity ─────────────────────────────────────
    def test_auth_user_comment_uses_user_identity(self):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user = User.objects.create_user(
            username="testmember",
            password="securePass123!",
            first_name="Test",
            last_name="Member",
            email="member@test.com",
        )
        # Use force_login to bypass django-axes auth backend (which requires
        # a real request object and fails in tests).
        self.client.force_login(user)
        response = self.client.post(
            self.comment_url,
            {"body": "Hello from a member.", "website_url": ""},
            HTTP_HX_REQUEST="true",
        )
        self.assertEqual(response.status_code, 200)
        from website.models import BlogComment
        comment = BlogComment.objects.filter(page=self.blog_post, user=user).first()
        self.assertIsNotNone(comment)
        self.assertEqual(comment.name, "Test Member")
        self.assertEqual(comment.email, "member@test.com")
