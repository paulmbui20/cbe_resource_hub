from wagtail.test.utils import WagtailPageTests
from wagtail.models import Page
from website.models import BlogIndexPage, BlogPage, BlogAuthor, CustomImage
from django.core.files.uploadedfile import SimpleUploadedFile
import io
from PIL import Image

def get_test_image_file():
    f = io.BytesIO()
    Image.new('RGB', (100, 100)).save(f, 'PNG')
    f.seek(0)
    return SimpleUploadedFile('test.png', f.read(), content_type='image/png')

class BlogTests(WagtailPageTests):
    def setUp(self):
        # Get the root page
        self.root = Page.objects.get(id=1).get_first_child()
        
        # Create an image
        self.image = CustomImage.objects.create(
            title="Test Image",
            file=get_test_image_file(),
        )
        
        # Create an author
        self.author = BlogAuthor.objects.create(
            name="Test Author",
            role="Editor",
            bio="Test Bio",
            image=self.image
        )
        
        # Create blog index
        self.blog_index = BlogIndexPage(
            title="Blog",
            slug="blog",
            intro="Welcome to our blog"
        )
        self.root.add_child(instance=self.blog_index)
        self.blog_index.save_revision().publish()
        
        # Create a blog post
        self.blog_post = BlogPage(
            title="Test Post",
            slug="test-post",
            intro="Test Intro",
            body="Test Body",
            author=self.author,
            main_image=self.image,
            date="2024-05-10"
        )
        self.blog_index.add_child(instance=self.blog_post)
        self.blog_post.save_revision().publish()

    def test_blog_author_str(self):
        self.assertEqual(str(self.author), "Test Author")

    def test_blog_index_context(self):
        response = self.client.get(self.blog_index.url)
        self.assertEqual(response.status_code, 200)
        self.assertIn('blogpages', response.context)
        self.assertEqual(len(response.context['blogpages']), 1)
        self.assertEqual(response.context['blogpages'][0].id, self.blog_post.id)

    def test_blog_post_view_increment(self):
        initial_views = self.blog_post.views
        # Accessing the page should increment views
        response = self.client.get(self.blog_post.url)
        self.assertEqual(response.status_code, 200)
        
        self.blog_post.refresh_from_db()
        self.assertEqual(self.blog_post.views, initial_views + 1)

    def test_blog_post_context(self):
        response = self.client.get(self.blog_post.url)
        self.assertEqual(response.status_code, 200)
        
        # Check optimized context variables
        self.assertIn('tags', response.context)
        self.assertIn('parent', response.context)
        self.assertIn('prev_post', response.context)
        self.assertIn('next_post', response.context)
        
        self.assertEqual(response.context['parent'].id, self.blog_index.id)

    def test_blog_index_tag_filtering(self):
        # Add a tag to the post
        self.blog_post.tags.add("test-tag")
        self.blog_post.save_revision().publish()
        
        # Filter by tag
        response = self.client.get(self.blog_index.url + "?tag=test-tag")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['blogpages']), 1)
        
        # Filter by non-existent tag
        response = self.client.get(self.blog_index.url + "?tag=other-tag")
        self.assertEqual(len(response.context['blogpages']), 0)

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

    def test_toc_placeholder_logic(self):
        # With no headings, TOC section should be hidden by script logic
        # (Hard to test JS logic in Django tests, but we can check if the container exists)
        response = self.client.get(self.blog_post.url)
        self.assertContains(response, 'id="toc-sidebar-container"')
