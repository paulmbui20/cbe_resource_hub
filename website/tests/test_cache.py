from django.core.cache import cache
from website.cache import get_faqs, get_testimonials
from website.models import FAQ, Testimonial
from website.tests.base import WebsiteBaseTestCase


class CacheInvalidationTests(WebsiteBaseTestCase):
    def setUp(self):
        super().setUp()
        cache.clear()

    def tearDown(self):
        super().tearDown()
        cache.clear()

    def test_faqs_caching_and_invalidation(self):
        # Initial call should cache the active FAQs
        FAQ.objects.create(question="Q1", answer="A1", is_active=True, order=1)
        FAQ.objects.create(question="Q2", answer="A2", is_active=False, order=2)
        
        faqs = get_faqs()
        self.assertEqual(len(faqs), 1)
        self.assertEqual(faqs[0].question, "Q1")
        
        # Verify it's cached
        cached_faqs = cache.get("website:faqs")
        self.assertIsNotNone(cached_faqs)
        self.assertEqual(len(cached_faqs), 1)
        
        # Adding a new FAQ should invalidate the cache (via signal)
        new_faq = FAQ.objects.create(question="Q3", answer="A3", is_active=True, order=0)
        
        # Cache should be cleared
        self.assertIsNone(cache.get("website:faqs"))
        
        # Next call should re-cache with the new item
        updated_faqs = get_faqs()
        self.assertEqual(len(updated_faqs), 2)
        
        # Deleting should also invalidate
        new_faq.delete()
        self.assertIsNone(cache.get("website:faqs"))

    def test_testimonials_caching_and_invalidation(self):
        # Initial call should cache the active Testimonials
        Testimonial.objects.create(author_name="A1", body="B1", is_active=True, order=1)
        Testimonial.objects.create(author_name="A2", body="B2", is_active=False, order=2)
        
        testimonials = get_testimonials()
        self.assertEqual(len(testimonials), 1)
        self.assertEqual(testimonials[0].author_name, "A1")
        
        # Verify it's cached
        cached_testimonials = cache.get("website:testimonials")
        self.assertIsNotNone(cached_testimonials)
        self.assertEqual(len(cached_testimonials), 1)
        
        # Adding a new Testimonial should invalidate the cache (via signal)
        new_testimonial = Testimonial.objects.create(author_name="A3", body="B3", is_active=True, order=0)
        
        # Cache should be cleared
        self.assertIsNone(cache.get("website:testimonials"))
        
        # Next call should re-cache with the new item
        updated_testimonials = get_testimonials()
        self.assertEqual(len(updated_testimonials), 2)
        
        # Deleting should also invalidate
        new_testimonial.delete()
        self.assertIsNone(cache.get("website:testimonials"))
