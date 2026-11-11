import tempfile
import unittest
from pathlib import Path

from local_privacy_scanner import scan_directory
from local_privacy_scanner.cli import main


class ScanDirectoryTests(unittest.TestCase):
    def test_reports_relative_path_and_line_without_match(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "notes.txt").write_text(
                "ordinary text\nContact alice@example.test for details\n", encoding="utf-8"
            )

            findings = scan_directory(root)

        self.assertEqual(len(findings), 1)
        self.assertEqual(findings[0].path, Path("notes.txt"))
        self.assertEqual(findings[0].line, 2)
        self.assertNotIn("alice@example.test", repr(findings[0]))

    def test_skips_binary_and_oversized_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "binary.dat").write_bytes(b"x\0alice@example.test")
            (root / "large.txt").write_text("alice@example.test", encoding="utf-8")

            findings = scan_directory(root, max_bytes=8)

        self.assertEqual(findings, [])

    def test_detects_common_credential_patterns_without_storing_values(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            github_token = "ghp_" + "A" * 36
            aws_key_id = "AKIA" + "A" * 16
            credential_value = "not-a-real-secret-value"
            (root / "config.txt").write_text(
                f"github={github_token}\naws={aws_key_id}\napi_key={credential_value}\n",
                encoding="utf-8",
            )

            findings = scan_directory(root)

        self.assertEqual(
            [finding.kind for finding in findings],
            ["possible GitHub token", "possible AWS access key ID", "possible credential assignment"],
        )
        self.assertTrue(all(finding.path == Path("config.txt") for finding in findings))
        self.assertTrue(all(finding.line == index for index, finding in enumerate(findings, start=1)))
        report = repr(findings)
        self.assertNotIn(github_token, report)
        self.assertNotIn(aws_key_id, report)
        self.assertNotIn(credential_value, report)

    def test_excludes_matching_files_and_directories(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "keep.txt").write_text("person@example.test", encoding="utf-8")
            generated = root / "generated"
            generated.mkdir()
            (generated / "output.txt").write_text("hidden@example.test", encoding="utf-8")
            (root / "debug.log").write_text("also-hidden@example.test", encoding="utf-8")

            findings = scan_directory(root, exclude=("generated/**", "*.log"))

        self.assertEqual([finding.path for finding in findings], [Path("keep.txt")])

    def test_rejects_parent_traversal_exclusion(self):
        with tempfile.TemporaryDirectory() as temporary:
            with self.assertRaises(ValueError):
                scan_directory(temporary, exclude=("../outside/**",))

    def test_rejects_non_directory(self):
        with tempfile.TemporaryDirectory() as temporary:
            file_path = Path(temporary) / "file.txt"
            file_path.write_text("text", encoding="utf-8")
            with self.assertRaises(NotADirectoryError):
                scan_directory(file_path)


class CliTests(unittest.TestCase):
    def test_output_does_not_include_matched_value(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            (root / "data.txt").write_text("user: secret@example.test", encoding="utf-8")
            from contextlib import redirect_stdout
            from io import StringIO

            output = StringIO()
            with redirect_stdout(output):
                import sys

                old_argv = sys.argv
                try:
                    sys.argv = ["privacy-scan", str(root)]
                    exit_code = main()
                finally:
                    sys.argv = old_argv

        self.assertEqual(exit_code, 1)
        self.assertIn("data.txt:1: possible email address", output.getvalue())
        self.assertNotIn("secret@example.test", output.getvalue())


if __name__ == "__main__":
    unittest.main()
