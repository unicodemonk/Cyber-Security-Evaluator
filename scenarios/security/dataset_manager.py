"""
Dataset Manager for SQL Injection Detection Benchmark.

This module handles loading, managing, and sampling code datasets from JSON files.
Supports both vulnerable and secure code samples across multiple languages.
"""

import json
import random
from pathlib import Path
from typing import Any
from datetime import datetime

from .models import (
    CodeSample,
    DatasetInfo,
    DatasetMetadata,
    TestPhase
)


class DatasetManager:
    """
    Manages code sample datasets for SQL injection testing.

    Loads samples from JSON files organized by language and vulnerability status.
    Provides methods for sampling, filtering, and strategic test selection.
    """

    def __init__(self, dataset_root: str | Path):
        """
        Initialize the dataset manager.

        Args:
            dataset_root: Root directory containing dataset JSON files
        """
        self.dataset_root = Path(dataset_root)
        self.vulnerable_samples: list[CodeSample] = []
        self.secure_samples: list[CodeSample] = []
        self.dataset_info: list[DatasetInfo] = []
        self._samples_by_category: dict[str, list[CodeSample]] = {}
        self._samples_by_language: dict[str, list[CodeSample]] = {}
        self._loaded = False

    def load_datasets(self) -> DatasetMetadata:
        """
        Load all datasets from JSON files.

        Returns:
            DatasetMetadata with information about loaded datasets

        Raises:
            FileNotFoundError: If dataset directory doesn't exist
            ValueError: If JSON files are malformed
        """
        if not self.dataset_root.exists():
            raise FileNotFoundError(f"Dataset directory not found: {self.dataset_root}")

        self.vulnerable_samples.clear()
        self.secure_samples.clear()
        self.dataset_info.clear()
        self._samples_by_category.clear()
        self._samples_by_language.clear()

        # Load vulnerable code samples
        vuln_dir = self.dataset_root / "vulnerable_code"
        if vuln_dir.exists():
            self._load_from_directory(vuln_dir, is_vulnerable=True)

        # Load secure code samples
        secure_dir = self.dataset_root / "secure_code"
        if secure_dir.exists():
            self._load_from_directory(secure_dir, is_vulnerable=False)

        # Build indices
        self._build_indices()

        self._loaded = True

        return self.get_metadata()

    def _load_from_directory(self, directory: Path, is_vulnerable: bool) -> None:
        """
        Load all JSON files from a directory.

        Args:
            directory: Directory containing JSON files
            is_vulnerable: True if loading vulnerable samples, False if secure
        """
        json_files = list(directory.glob("*.json"))

        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)

                language = data.get("language", "unknown")
                samples_data = data.get("samples", [])

                loaded_samples = []
                for sample_data in samples_data:
                    # Ensure is_vulnerable is set correctly
                    sample_data["is_vulnerable"] = is_vulnerable
                    sample_data["language"] = language

                    try:
                        sample = CodeSample(**sample_data)
                        loaded_samples.append(sample)

                        if is_vulnerable:
                            self.vulnerable_samples.append(sample)
                        else:
                            self.secure_samples.append(sample)

                    except Exception as e:
                        print(f"Warning: Failed to load sample from {json_file}: {e}")
                        continue

                # Record dataset info
                categories = {}
                for sample in loaded_samples:
                    categories[sample.category] = categories.get(sample.category, 0) + 1

                info = DatasetInfo(
                    language=language,
                    vulnerability_type="sql_injection",
                    total_samples=len(loaded_samples),
                    vulnerable_count=len(loaded_samples) if is_vulnerable else 0,
                    secure_count=len(loaded_samples) if not is_vulnerable else 0,
                    categories=categories,
                    source_file=str(json_file),
                    loaded_at=datetime.now()
                )
                self.dataset_info.append(info)

            except json.JSONDecodeError as e:
                print(f"Error: Failed to parse JSON file {json_file}: {e}")
            except Exception as e:
                print(f"Error: Failed to load dataset from {json_file}: {e}")

    def _build_indices(self) -> None:
        """Build indices for fast lookups by category and language."""
        all_samples = self.vulnerable_samples + self.secure_samples

        # Index by category
        for sample in all_samples:
            if sample.category not in self._samples_by_category:
                self._samples_by_category[sample.category] = []
            self._samples_by_category[sample.category].append(sample)

        # Index by language
        for sample in all_samples:
            if sample.language not in self._samples_by_language:
                self._samples_by_language[sample.language] = []
            self._samples_by_language[sample.language].append(sample)

    def get_metadata(self) -> DatasetMetadata:
        """
        Get metadata about all loaded datasets.

        Returns:
            DatasetMetadata with comprehensive information
        """
        all_samples = self.vulnerable_samples + self.secure_samples

        return DatasetMetadata(
            total_samples=len(all_samples),
            total_vulnerable=len(self.vulnerable_samples),
            total_secure=len(self.secure_samples),
            languages=list(self._samples_by_language.keys()),
            categories=list(self._samples_by_category.keys()),
            datasets=self.dataset_info,
            loaded_at=datetime.now()
        )

    def get_samples_by_category(self, category: str) -> list[CodeSample]:
        """
        Get all samples for a specific category.

        Args:
            category: Category name (e.g., 'classic_sqli')

        Returns:
            List of code samples in that category
        """
        return self._samples_by_category.get(category, [])

    def get_samples_by_language(self, language: str) -> list[CodeSample]:
        """
        Get all samples for a specific language.

        Args:
            language: Language name (e.g., 'python')

        Returns:
            List of code samples in that language
        """
        return self._samples_by_language.get(language, [])

    def get_all_categories(self) -> list[str]:
        """Get list of all categories in the dataset."""
        return list(self._samples_by_category.keys())

    def get_all_languages(self) -> list[str]:
        """Get list of all languages in the dataset."""
        return list(self._samples_by_language.keys())

    def sample_diverse(
        self,
        n: int,
        seed: int | None = None,
        categories: list[str] | None = None,
        languages: list[str] | None = None
    ) -> list[CodeSample]:
        """
        Sample diverse test cases (exploration phase).

        Ensures balanced representation across categories and vulnerability types.

        Args:
            n: Number of samples to select
            seed: Random seed for reproducibility
            categories: Filter to specific categories (None = all)
            languages: Filter to specific languages (None = all)

        Returns:
            List of diverse code samples
        """
        if seed is not None:
            random.seed(seed)

        # Filter samples
        all_samples = self._filter_samples(categories, languages)

        if len(all_samples) <= n:
            return all_samples.copy()

        # Strategy: Sample proportionally from each category
        samples_per_category = self._distribute_samples_by_category(all_samples, n)

        selected = []
        for category, count in samples_per_category.items():
            category_samples = [s for s in all_samples if s.category == category]
            selected.extend(random.sample(category_samples, min(count, len(category_samples))))

        # If we didn't get enough, fill with random samples
        if len(selected) < n:
            remaining = [s for s in all_samples if s not in selected]
            selected.extend(random.sample(remaining, min(n - len(selected), len(remaining))))

        random.shuffle(selected)
        return selected[:n]

    def sample_focused(
        self,
        n: int,
        focus_categories: list[str],
        focus_percentage: float = 0.6,
        seed: int | None = None,
        languages: list[str] | None = None
    ) -> list[CodeSample]:
        """
        Sample with focus on specific categories (exploitation phase).

        Allocates focus_percentage of samples to focus_categories,
        remainder distributed across other categories.

        Args:
            n: Total number of samples to select
            focus_categories: Categories to focus on (weak areas)
            focus_percentage: Percentage of tests to allocate to focus categories (0.0-1.0)
            seed: Random seed for reproducibility
            languages: Filter to specific languages (None = all)

        Returns:
            List of strategically sampled code samples
        """
        if seed is not None:
            random.seed(seed)

        # Filter samples
        all_samples = self._filter_samples(None, languages)

        # Split into focus and non-focus samples
        focus_samples = [s for s in all_samples if s.category in focus_categories]
        other_samples = [s for s in all_samples if s.category not in focus_categories]

        # Calculate allocation
        focus_count = int(n * focus_percentage)
        other_count = n - focus_count

        # Sample from each group
        selected_focus = random.sample(focus_samples, min(focus_count, len(focus_samples)))
        selected_other = random.sample(other_samples, min(other_count, len(other_samples)))

        # Combine and shuffle
        selected = selected_focus + selected_other

        # If we didn't get enough, fill from remaining samples
        if len(selected) < n:
            remaining = [s for s in all_samples if s not in selected]
            selected.extend(random.sample(remaining, min(n - len(selected), len(remaining))))

        random.shuffle(selected)
        return selected[:n]

    def sample_validation(
        self,
        n: int,
        tested_ids: set[str],
        seed: int | None = None,
        categories: list[str] | None = None,
        languages: list[str] | None = None
    ) -> list[CodeSample]:
        """
        Sample for validation phase (untested samples only).

        Args:
            n: Number of samples to select
            tested_ids: IDs of samples already tested
            seed: Random seed for reproducibility
            categories: Filter to specific categories (None = all)
            languages: Filter to specific languages (None = all)

        Returns:
            List of untested code samples
        """
        if seed is not None:
            random.seed(seed)

        # Filter samples
        all_samples = self._filter_samples(categories, languages)

        # Exclude already tested samples
        untested = [s for s in all_samples if s.id not in tested_ids]

        if len(untested) <= n:
            return untested

        return random.sample(untested, n)

    def _filter_samples(
        self,
        categories: list[str] | None,
        languages: list[str] | None
    ) -> list[CodeSample]:
        """
        Filter samples by categories and languages.

        Args:
            categories: Categories to include (None = all)
            languages: Languages to include (None = all)

        Returns:
            Filtered list of samples
        """
        all_samples = self.vulnerable_samples + self.secure_samples

        if categories:
            all_samples = [s for s in all_samples if s.category in categories]

        if languages:
            all_samples = [s for s in all_samples if s.language in languages]

        return all_samples

    def _distribute_samples_by_category(
        self,
        samples: list[CodeSample],
        total: int
    ) -> dict[str, int]:
        """
        Distribute sample count proportionally across categories.

        Args:
            samples: Pool of samples
            total: Total samples to distribute

        Returns:
            Dictionary mapping category to sample count
        """
        # Count samples per category
        category_counts = {}
        for sample in samples:
            category_counts[sample.category] = category_counts.get(sample.category, 0) + 1

        # Calculate proportional allocation
        total_samples = len(samples)
        allocation = {}

        for category, count in category_counts.items():
            proportion = count / total_samples
            allocated = max(1, int(total * proportion))  # At least 1 per category
            allocation[category] = allocated

        # Adjust to match exact total
        current_total = sum(allocation.values())
        if current_total > total:
            # Remove from largest
            largest = max(allocation, key=allocation.get)
            allocation[largest] -= (current_total - total)
        elif current_total < total:
            # Add to largest
            largest = max(allocation, key=allocation.get)
            allocation[largest] += (total - current_total)

        return allocation

    def get_sample_by_id(self, sample_id: str) -> CodeSample | None:
        """
        Get a specific sample by ID.

        Args:
            sample_id: Sample identifier

        Returns:
            CodeSample if found, None otherwise
        """
        all_samples = self.vulnerable_samples + self.secure_samples
        for sample in all_samples:
            if sample.id == sample_id:
                return sample
        return None

    def is_loaded(self) -> bool:
        """Check if datasets have been loaded."""
        return self._loaded

    def get_statistics(self) -> dict[str, Any]:
        """
        Get comprehensive statistics about the datasets.

        Returns:
            Dictionary with detailed statistics
        """
        all_samples = self.vulnerable_samples + self.secure_samples

        # Category statistics
        category_stats = {}
        for category in self.get_all_categories():
            samples = self.get_samples_by_category(category)
            vuln_count = sum(1 for s in samples if s.is_vulnerable)
            category_stats[category] = {
                "total": len(samples),
                "vulnerable": vuln_count,
                "secure": len(samples) - vuln_count
            }

        # Language statistics
        language_stats = {}
        for language in self.get_all_languages():
            samples = self.get_samples_by_language(language)
            vuln_count = sum(1 for s in samples if s.is_vulnerable)
            language_stats[language] = {
                "total": len(samples),
                "vulnerable": vuln_count,
                "secure": len(samples) - vuln_count
            }

        return {
            "total_samples": len(all_samples),
            "total_vulnerable": len(self.vulnerable_samples),
            "total_secure": len(self.secure_samples),
            "vulnerability_ratio": len(self.vulnerable_samples) / len(all_samples) if all_samples else 0,
            "categories": list(self.get_all_categories()),
            "languages": list(self.get_all_languages()),
            "category_statistics": category_stats,
            "language_statistics": language_stats
        }
