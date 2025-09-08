"""
PathResolver tests (ASDL_PATH parsing and file discovery).
Moved from import_/ to top-level elaborator tests.
"""

import pytest
import os
import tempfile
from pathlib import Path
from unittest.mock import patch

from asdl.elaborator.import_.path_resolver import PathResolver


class TestPathResolver:
    def setup_method(self):
        self.resolver = PathResolver()

    def test_asdl_path_parsing_unix(self):
        test_paths = "/pdks:/workspace/third_party:/home/user/libs"

        with patch.dict(os.environ, {'ASDL_PATH': test_paths}):
            with patch('os.name', 'posix'):
                paths = self.resolver.get_search_paths()

        expected_paths = [
            Path("/pdks"),
            Path("/workspace/third_party"),
            Path("/home/user/libs")
        ]

        asdl_path_entries = paths[:3]
        assert asdl_path_entries == expected_paths

    @patch('os.name', 'nt')
    def test_asdl_path_parsing_windows(self):
        test_paths = r"C:\pdks;D:\workspace\third_party;C:\Users\user\libs"

        with patch.dict(os.environ, {'ASDL_PATH': test_paths}):
            paths = self.resolver.get_search_paths()

        expected_paths = [
            Path(r"C:\pdks"),
            Path(r"D:\workspace\third_party"),
            Path(r"C:\Users\user\libs")
        ]

        asdl_path_entries = paths[:3]
        assert asdl_path_entries == expected_paths

    def test_search_path_env_then_default(self):
        env_path = "/env/path1:/env/path2"

        with patch.dict(os.environ, {'ASDL_PATH': env_path}):
            with patch('os.name', 'posix'):
                paths = self.resolver.get_search_paths()

        assert paths[:2] == [Path("/env/path1"), Path("/env/path2")]
        assert paths[-1] == Path(".")
        assert Path("libs") not in paths
        assert Path("third_party") not in paths

    def test_file_discovery_and_probing(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            (temp_path / "pdks" / "gf180mcu_std_tiles").mkdir(parents=True)
            (temp_path / "workspace" / "gf180mcu_std_tiles").mkdir(parents=True)

            test_file = temp_path / "workspace" / "gf180mcu_std_tiles" / "devices.asdl"
            test_file.write_text("# Test ASDL file")

            search_paths = [
                temp_path / "pdks",
                temp_path / "workspace"
            ]

            resolved_path = self.resolver.resolve_file_path(
                "gf180mcu_std_tiles/devices.asdl",
                search_paths
            )

            assert resolved_path == test_file.resolve()

    def test_file_not_found_returns_none(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            search_paths = [Path(temp_dir)]

            resolved_path = self.resolver.resolve_file_path(
                "nonexistent/file.asdl",
                search_paths
            )

            assert resolved_path is None

    def test_built_in_defaults_included(self):
        with patch.dict(os.environ, {}, clear=True):
            paths = self.resolver.get_search_paths()

        assert paths == [Path(".")]


