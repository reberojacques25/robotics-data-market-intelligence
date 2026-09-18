"""Test that no large files are tracked in the repository."""

import os
from pathlib import Path


class TestNoLargeFiles:
    """Ensure no large files are committed."""

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10 MB

    def test_no_large_files(self):
        """No tracked file should exceed 10 MB."""
        repo_root = Path(__file__).parent.parent
        large_files = []
        for root, dirs, files in os.walk(repo_root):
            # Skip .git directory
            if ".git" in root:
                continue
            # Skip data/raw and data/interim (gitignored)
            if "data/raw" in root or "data/interim" in root:
                continue
            for fname in files:
                fpath = os.path.join(root, fname)
                try:
                    size = os.path.getsize(fpath)
                    if size > self.MAX_FILE_SIZE:
                        large_files.append(f"{fpath}: {size / 1024 / 1024:.1f} MB")
                except OSError:
                    pass
        assert len(large_files) == 0, f"Large files found: {large_files}"
