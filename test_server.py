"""Dependency-free regression checks for the static server's path boundary.

Load the actual route function without importing optional FastAPI dependencies.
Filesystem mocks avoid creating frontend builds or temporary files.
"""

import ast
from pathlib import Path
import unittest
from unittest.mock import patch


class HTTPException(Exception):
    def __init__(self, status_code, detail):
        self.status_code = status_code
        self.detail = detail


class StaticServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server_path = Path(__file__).with_name("server.py")
        source = ast.parse(server_path.read_text(encoding="utf-8"))
        handler = next(
            node
            for node in ast.walk(source)
            if isinstance(node, ast.FunctionDef) and node.name == "serve_spa"
        )
        handler.decorator_list = []
        cls.dist = Path("/euclid/frontend/dist")
        namespace = {
            "FRONTEND_DIST": cls.dist,
            "FileResponse": lambda path: path,
            "HTTPException": HTTPException,
        }
        exec(
            compile(ast.Module(body=[handler], type_ignores=[]), str(server_path), "exec"),
            namespace,
        )
        cls.serve_spa = staticmethod(namespace["serve_spa"])

    def serve_with_files(self, route, files, symlinks=None):
        original_resolve = Path.resolve
        symlinks = symlinks or {}

        def resolve(path, *args, **kwargs):
            return symlinks.get(path, original_resolve(path, *args, **kwargs))

        with patch.object(Path, "resolve", resolve), patch.object(
            Path, "is_file", lambda path: path in files
        ):
            return self.serve_spa(route)

    def assert_not_found(self, route, files, symlinks=None):
        with self.assertRaises(HTTPException) as caught:
            self.serve_with_files(route, files, symlinks)
        self.assertEqual(caught.exception.status_code, 404)

    def test_parent_traversal_rejects_existing_file(self):
        self.assert_not_found(
            "../../content/lessons.json", {Path("/euclid/content/lessons.json")}
        )

    def test_absolute_path_rejects_existing_file(self):
        self.assert_not_found("/private/secret.txt", {Path("/private/secret.txt")})

    def test_sibling_with_same_prefix_is_outside_dist(self):
        self.assert_not_found(
            "../dist-private/secret.txt",
            {Path("/euclid/frontend/dist-private/secret.txt")},
        )

    def test_symlink_escape_is_rejected(self):
        outside = Path("/private/secret.txt")
        self.assert_not_found(
            "linked.txt", {outside}, {self.dist / "linked.txt": outside}
        )

    def test_static_file_inside_dist_is_served(self):
        asset = self.dist / "assets" / "app.js"
        self.assertEqual(self.serve_with_files("assets/app.js", {asset}), asset)

    def test_spa_route_uses_index(self):
        index = self.dist / "index.html"
        self.assertEqual(self.serve_with_files("lesson/euclid", {index}), index)

    def test_root_route_uses_index(self):
        index = self.dist / "index.html"
        self.assertEqual(self.serve_with_files("", {index}), index)

    def test_index_symlink_escape_is_rejected(self):
        outside = Path("/private/secret.txt")
        self.assert_not_found(
            "lesson/euclid", {outside}, {self.dist / "index.html": outside}
        )

    def test_missing_index_is_not_served(self):
        self.assert_not_found("lesson/euclid", set())


if __name__ == "__main__":
    unittest.main()
