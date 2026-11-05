"""Regression tests for image lines in text submitted by a browser form."""

import ast
import re
import unittest
from pathlib import Path


RENDERING = Path(__file__).resolve().parents[1] / "netbox_documentation" / "rendering.py"


class ImageTokenTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The production renderer imports NetBox; this checks its exact pattern
        # without needing a running NetBox installation for this small test.
        tree = ast.parse(RENDERING.read_text())
        assignment = next(
            node for node in tree.body
            if isinstance(node, ast.Assign)
            and any(isinstance(target, ast.Name) and target.id == "IMAGE_LINE"
                    for target in node.targets)
        )
        cls.pattern = re.compile(ast.literal_eval(assignment.value.args[0]))

    def test_native_image_on_lf_and_crlf_lines(self):
        for newline in ("\n", "\r\n"):
            with self.subTest(newline=repr(newline)):
                text = (f"[[attachment:9]]{newline}{newline}"
                        f"[[attachment:10]]{newline}## Anleitung")
                self.assertEqual(
                    [match.group(2) for match in self.pattern.finditer(text)],
                    ["9", "10"],
                )

    def test_uploaded_image_on_crlf_line(self):
        token = "9f7ab31a-6c5b-4b86-a4f0-b2c17bb23046"
        match = self.pattern.search(f"Text\r\n\r\n[[image:{token}]]\r\n")
        self.assertIsNotNone(match)
        self.assertEqual(match.group(1), token)


if __name__ == "__main__":
    unittest.main()
