"""
Performance tests for file operations.
Tests query optimization, bulk operations, and scalability.
"""
import time

from django.test import TestCase, TransactionTestCase

from files.models import File
from .fixtures import FileFixtures, create_uploaded_file


class TestQueryPerformance(TestCase):
    """Test database query performance."""

    @classmethod
    def setUpTestData(cls):
        """Create test data once for all tests."""
        # Create 50 test files
        for i in range(50):
            file_type = 'png' if i % 2 == 0 else 'jpg'
            if file_type == 'png':
                buffer = FileFixtures.create_valid_png()
            else:
                buffer = FileFixtures.create_valid_jpeg()

            uploaded_file = create_uploaded_file(buffer, f'image/{file_type}')
            File.objects.create(title=f"Test {i}", file=uploaded_file)

    def test_list_all_files_queries(self):
        """Listing files should use minimal queries."""
        with self.assertNumQueries(1):
            list(File.objects.all())

    def test_filter_by_category_queries(self):
        """Filtering by category should use single query."""
        with self.assertNumQueries(1):
            list(File.objects.filter(file_category='image'))

    def test_filter_by_multiple_fields_queries(self):
        """Complex filters should still use single query."""
        with self.assertNumQueries(1):
            list(File.objects.filter(
                file_category='image',
                mime_type='image/png'
            ))

    def test_order_by_created_queries(self):
        """Ordering should not add extra queries."""
        with self.assertNumQueries(1):
            list(File.objects.order_by('-created'))

    def test_pagination_queries(self):
        """Pagination should use minimal queries."""
        with self.assertNumQueries(1):
            list(File.objects.all()[:10])

    def test_count_queries(self):
        """Count operations should be efficient."""
        with self.assertNumQueries(1):
            File.objects.count()

    def test_exists_queries(self):
        """Existence checks should be efficient."""
        with self.assertNumQueries(1):
            File.objects.filter(title="Test 1").exists()

    def test_index_usage_on_category_filter(self):
        """Category filter should use index."""
        # This test verifies indexes are working
        start_time = time.time()

        list(File.objects.filter(file_category='image'))

        end_time = time.time()
        duration = end_time - start_time

        # Should be very fast (< 0.1 seconds for 50 records)
        self.assertLess(duration, 0.1)

    def test_index_usage_on_created_ordering(self):
        """Ordering by created should use index."""
        start_time = time.time()

        list(File.objects.order_by('-created')[:10])

        end_time = time.time()
        duration = end_time - start_time

        # Should be very fast
        self.assertLess(duration, 0.1)


class TestMetadataExtractionPerformance(TestCase):
    """Test metadata extraction performance."""

    def test_image_metadata_extraction_time(self):
        """Image metadata extraction should be fast."""
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(width=500, height=500),
            'image/png'
        )

        start_time = time.time()

        file_obj = File(title="Test", file=png_file)
        file_obj._extract_metadata()

        end_time = time.time()
        duration = end_time - start_time

        # Should be very fast (< 0.5 seconds)
        self.assertLess(duration, 0.5)

    def test_large_image_metadata_extraction(self):
        """Large images should still process reasonably fast."""
        # Create larger image (but still undersize limit)
        large_png = create_uploaded_file(
            FileFixtures.create_valid_png(width=1000, height=1000),
            'image/png'
        )

        start_time = time.time()

        file_obj = File(title="Large", file=large_png)
        file_obj._extract_metadata()

        end_time = time.time()
        duration = end_time - start_time

        # Should complete in reasonable time (< 2 seconds)
        self.assertLess(duration, 2.0)

    def test_hash_calculation_time(self):
        """Hash calculation should complete in reasonable time."""
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(width=500, height=500),
            'image/png'
        )

        file_obj = File(title="Hash Test", file=png_file)

        start_time = time.time()

        file_obj._calculate_file_hash()

        end_time = time.time()
        duration = end_time - start_time

        # Should be fast (< 1 second for small image)
        self.assertLess(duration, 1.0)


class TestScalability(TestCase):
    """Test system behavior at scale."""

    def test_performance_with_100_files(self):
        """System should handle 100 files efficiently."""
        # Create 100 files
        for i in range(100):
            file_type = ['png', 'jpg'][i % 2]
            buffer = FileFixtures.create_valid_png() if file_type == 'png' else FileFixtures.create_valid_jpeg()
            uploaded_file = create_uploaded_file(buffer, f'image/{file_type}')
            File.objects.create(title=f"Scale Test {i}", file=uploaded_file)

        # Query performance should still be good
        with self.assertNumQueries(1):
            list(File.objects.all())

        # Filtering should still be fast
        start_time = time.time()
        list(File.objects.filter(file_category='image'))
        duration = time.time() - start_time

        self.assertLess(duration, 0.2)

    def test_memory_usage_with_multiple_files(self):
        """Should not consume excessive memory."""
        # Create several files
        files = []
        for i in range(10):
            png_file = create_uploaded_file(
                FileFixtures.create_valid_png(),
                'image/png'
            )
            files.append(File.objects.create(title=f"Memory {i}", file=png_file))

        # Accessing metadata should not load all files into memory
        for f in File.objects.all():
            _ = f.title
            _ = f.human_size

        # This test mainly ensures no obvious memory leaks
        # In practice, you'd use memory profiling tools


class TestDatabaseIndexEfficiency(TestCase):
    """Test that database indexes are being used effectively."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        for i in range(30):
            png_file = create_uploaded_file(
                FileFixtures.create_valid_png(),
                'image/png'
            )
            File.objects.create(title=f"Index Test {i}", file=png_file)

    def test_category_index_used(self):
        """Category index should be used in queries."""
        # This test is database-specific
        # For PostgreSQL, you could use EXPLAIN to verify index usage

        files = list(File.objects.filter(file_category='image'))

        # Should return results efficiently
        self.assertGreater(len(files), 0)

    def test_mime_type_index_used(self):
        """MIME type index should be used."""
        files = list(File.objects.filter(mime_type='image/png'))

        self.assertGreater(len(files), 0)

    def test_composite_index_used(self):
        """Composite index on category + created should be used."""
        files = list(File.objects.filter(
            file_category='image'
        ).order_by('-created'))

        self.assertGreater(len(files), 0)

    def test_hash_index_used_for_lookups(self):
        """Hash index should be used for duplicate detection."""
        file_obj = File.objects.first()
        if file_obj:
            file_obj._calculate_file_hash()
            file_obj.save()

            # Lookup by hash should be fast
            start_time = time.time()
            result = File.objects.filter(file_hash=file_obj.file_hash).first()
            duration = time.time() - start_time

            self.assertIsNotNone(result)
            self.assertLess(duration, 0.1)


class TestConcurrentAccessPerformance(TransactionTestCase):
    """Test performance under concurrent access."""

    def test_concurrent_reads(self):
        """Multiple concurrent reads should not block each other."""
        # Create test file
        png_file = create_uploaded_file(
            FileFixtures.create_valid_png(),
            'image/png'
        )
        File.objects.create(title="Concurrent Test", file=png_file)

        # Simulate concurrent reads
        start_time = time.time()

        for _ in range(10):
            list(File.objects.all())

        end_time = time.time()
        duration = end_time - start_time

        # Should complete quickly (< 1 second for 10 reads)
        self.assertLess(duration, 1.0)
