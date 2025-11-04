"""
Tests for DatasetManager.
"""

import pytest
from pathlib import Path
import sys

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from scenarios.security.dataset_manager import DatasetManager


class TestDatasetManager:
    """Test suite for DatasetManager."""

    @pytest.fixture
    def dataset_root(self):
        """Fixture providing dataset root path."""
        return Path("datasets/sql_injection")

    @pytest.fixture
    def manager(self, dataset_root):
        """Fixture providing initialized DatasetManager."""
        mgr = DatasetManager(dataset_root)
        mgr.load_datasets()
        return mgr

    def test_load_datasets(self, dataset_root):
        """Test loading datasets from JSON files."""
        manager = DatasetManager(dataset_root)
        metadata = manager.load_datasets()

        assert metadata.total_samples > 0
        assert metadata.total_vulnerable > 0
        assert metadata.total_secure > 0
        assert len(metadata.languages) > 0
        assert len(metadata.categories) > 0

        print(f"\n✓ Loaded {metadata.total_samples} samples")
        print(f"  - Vulnerable: {metadata.total_vulnerable}")
        print(f"  - Secure: {metadata.total_secure}")
        print(f"  - Languages: {metadata.languages}")
        print(f"  - Categories: {metadata.categories}")

    def test_get_samples_by_category(self, manager):
        """Test retrieving samples by category."""
        categories = manager.get_all_categories()
        assert len(categories) > 0

        for category in categories:
            samples = manager.get_samples_by_category(category)
            assert len(samples) > 0
            assert all(s.category == category for s in samples)

        print(f"\n✓ Category filtering works for {len(categories)} categories")

    def test_get_samples_by_language(self, manager):
        """Test retrieving samples by language."""
        languages = manager.get_all_languages()
        assert len(languages) > 0

        for language in languages:
            samples = manager.get_samples_by_language(language)
            assert len(samples) > 0
            assert all(s.language == language for s in samples)

        print(f"\n✓ Language filtering works for {len(languages)} languages")

    def test_sample_diverse(self, manager):
        """Test diverse sampling."""
        n = 20
        samples = manager.sample_diverse(n=n, seed=42)

        assert len(samples) <= n
        assert len(samples) > 0

        # Check diversity
        categories = set(s.category for s in samples)
        assert len(categories) > 1  # Should have multiple categories

        print(f"\n✓ Diverse sampling: {len(samples)} samples across {len(categories)} categories")

    def test_sample_focused(self, manager):
        """Test focused sampling on weak categories."""
        weak_categories = ["classic_sqli", "blind_sqli"]
        n = 20
        focus_percentage = 0.6

        samples = manager.sample_focused(
            n=n,
            focus_categories=weak_categories,
            focus_percentage=focus_percentage,
            seed=42
        )

        assert len(samples) <= n

        # Count samples in focus categories
        focus_count = sum(1 for s in samples if s.category in weak_categories)
        focus_ratio = focus_count / len(samples)

        # Should be roughly focus_percentage (allowing some variance)
        assert focus_ratio >= focus_percentage * 0.8

        print(f"\n✓ Focused sampling: {focus_count}/{len(samples)} = {focus_ratio:.1%} in focus categories")

    def test_sample_validation(self, manager):
        """Test validation sampling (untested samples only)."""
        # First sample some tests
        initial_samples = manager.sample_diverse(n=10, seed=42)
        tested_ids = {s.id for s in initial_samples}

        # Now sample for validation
        validation_samples = manager.sample_validation(
            n=10,
            tested_ids=tested_ids,
            seed=42
        )

        # Should not overlap with tested IDs
        validation_ids = {s.id for s in validation_samples}
        assert len(validation_ids.intersection(tested_ids)) == 0

        print(f"\n✓ Validation sampling: {len(validation_samples)} untested samples")

    def test_get_statistics(self, manager):
        """Test statistics generation."""
        stats = manager.get_statistics()

        assert stats["total_samples"] > 0
        assert stats["total_vulnerable"] > 0
        assert stats["total_secure"] > 0
        assert 0 < stats["vulnerability_ratio"] < 1
        assert len(stats["categories"]) > 0
        assert len(stats["languages"]) > 0

        print(f"\n✓ Statistics:")
        print(f"  - Total samples: {stats['total_samples']}")
        print(f"  - Vulnerability ratio: {stats['vulnerability_ratio']:.2%}")
        print(f"  - Categories: {len(stats['categories'])}")
        print(f"  - Languages: {len(stats['languages'])}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
