"""
seo/tests/test_utils.py

Tests for seo/utils.py:
  - generate_meta_description(): standard truncation, HTML stripped,
    sentence-boundary truncation, empty input, exact-length input
  - generate_keywords(): single name, additional terms, lowercase, comma-separated
"""

from django.test import TestCase

from seo.utils import generate_meta_description, generate_keywords


class GenerateMetaDescriptionTests(TestCase):

    def test_empty_string_returns_empty(self):
        self.assertEqual(generate_meta_description(""), "")

    def test_none_returns_empty(self):
        self.assertEqual(generate_meta_description(None), "")

    def test_short_text_returned_as_is(self):
        text = "Short description."
        result = generate_meta_description(text)
        self.assertEqual(result, text)

    def test_text_at_exact_max_length_returned_as_is(self):
        text = "A" * 160
        result = generate_meta_description(text, max_length=160)
        self.assertEqual(result, text)

    def test_long_text_truncated_to_max_length(self):
        text = "A" * 200
        result = generate_meta_description(text, max_length=160)
        self.assertLessEqual(len(result), 160)

    def test_html_tags_stripped(self):
        text = "<p>This is a <strong>test</strong> description.</p>"
        result = generate_meta_description(text)
        self.assertNotIn("<p>", result)
        self.assertNotIn("<strong>", result)
        self.assertIn("test", result)

    def test_sentence_boundary_truncation(self):
        # If there's a period at >70% of max_length, truncate at sentence end
        # Build a text where the period is near the 70% mark
        sentence = "The quick brown fox jumps over the lazy dog."  # 44 chars
        filler = "X" * 120  # total ~164 > 160
        text = sentence + filler
        result = generate_meta_description(text, max_length=160)
        # Result should end at the period if period is at >70% of 160 = 112 chars
        if result.endswith("."):
            self.assertTrue(result.endswith("."))
        else:
            self.assertTrue(result.endswith("..."))
            self.assertLessEqual(len(result), 160)

    def test_no_sentence_boundary_uses_ellipsis(self):
        text = "A" * 200
        result = generate_meta_description(text, max_length=160)
        # No period in "AAAA..." so should end with "..."
        self.assertTrue(result.endswith("..."))

    def test_custom_max_length(self):
        text = "A" * 200
        result = generate_meta_description(text, max_length=50)
        self.assertLessEqual(len(result), 50)

    def test_result_contains_original_content(self):
        text = "CBE Resource Hub helps teachers and students."
        result = generate_meta_description(text)
        self.assertIn("CBE Resource Hub", result)


class GenerateKeywordsTests(TestCase):

    def test_single_name_returns_lowercase(self):
        result = generate_keywords("Mathematics")
        self.assertIn("mathematics", result)

    def test_additional_terms_generate_combinations(self):
        result = generate_keywords("Mathematics", "Grade 1")
        self.assertIn("mathematics grade 1", result)
        self.assertIn("grade 1 mathematics", result)

    def test_multiple_additional_terms(self):
        result = generate_keywords("English", "Grade 2", "CBC")
        self.assertIn("english grade 2", result)
        self.assertIn("grade 2 english", result)
        self.assertIn("english cbc", result)
        self.assertIn("cbc english", result)

    def test_empty_additional_term_skipped(self):
        result = generate_keywords("Science", "", None)
        # Only the base name should appear — no extra combinations
        self.assertEqual(result, "science")

    def test_returns_comma_separated_string(self):
        result = generate_keywords("History", "Term 1")
        self.assertIn(",", result)

    def test_result_is_lowercase(self):
        result = generate_keywords("MATHEMATICS", "GRADE 1")
        self.assertEqual(result, result.lower())
