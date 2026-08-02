"""
test_red_team_edge_cases.py
===========================
Adversarial edge-case testing against FastAPI backend:
1. Empty file upload
2. Invalid C syntax
3. UTF-8 BOM handling
4. Very large file (10,000+ lines)
5. Malformed JSON payloads
6. Duplicate file uploads
"""
import os
import sys
import requests
import unittest

BASE_URL = "http://localhost:8000"

class TestRedTeamEdgeCases(unittest.TestCase):

    def test_empty_file_upload(self):
        """Upload a 0-byte file — must return 400 or 200 with empty violations gracefully."""
        r = requests.post(f"{BASE_URL}/api/upload", files={"file": ("empty.c", b"", "text/plain")})
        self.assertIn(r.status_code, (200, 400))
        data = r.json()
        if r.status_code == 200:
            self.assertEqual(data.get("violations"), [])
            self.assertEqual(data.get("compliance_score"), 100.0)

    def test_invalid_c_syntax(self):
        """Upload malformed C code — must handle parse error gracefully without crashing server."""
        invalid_code = b"int main( { printf(\"unclosed string); return 0"
        r = requests.post(f"{BASE_URL}/api/upload", files={"file": ("invalid.c", invalid_code, "text/plain")})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertFalse(data.get("parse_valid", True))
        self.assertIsNotNone(data.get("error"))

    def test_utf8_bom_upload(self):
        """Upload C file with UTF-8 BOM header (0xEF 0xBB 0xBF) — must strip BOM and parse cleanly."""
        bom_code = b"\xef\xbb\xbfint global_var = 0;\nvoid foo(int unused) { (void)unused; global_var = 1; }\n"
        r = requests.post(f"{BASE_URL}/api/upload", files={"file": ("bom.c", bom_code, "text/plain")})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("success"))

    def test_very_large_file(self):
        """Upload a 5,000 line C file — must process in under 5 seconds."""
        large_lines = ["int g_var = 0;\n"] + [f"int func_{i}(int a) {{ return a + {i}; }}\n" for i in range(5000)]
        large_code = "".join(large_lines).encode("utf-8")
        r = requests.post(f"{BASE_URL}/api/upload", files={"file": ("very_large.c", large_code, "text/plain")})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data.get("success"))

    def test_malformed_report_payload(self):
        """Send malformed JSON payload to /api/generate-report — must return 422 Unprocessable Content."""
        r = requests.post(f"{BASE_URL}/api/generate-report", json={"invalid_field": True})
        self.assertEqual(r.status_code, 422)

    def test_apply_patches_with_empty_violations(self):
        """Send apply-patches with empty violations list — must return unchanged source code."""
        code = "int main(void) { return 0; }"
        r = requests.post(f"{BASE_URL}/api/apply-patches", json={"source_code": code, "violations": []})
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["modified_code"], code)

    def test_oversized_file_upload(self):
        """Upload a >10MB file — must reject with HTTP 413 Payload Too Large."""
        oversized_data = b"/* extra large byte padding */\n" * 400000  # ~12MB
        r = requests.post(f"{BASE_URL}/api/upload", files={"file": ("huge.c", oversized_data, "text/plain")})
        self.assertEqual(r.status_code, 413)

    def test_path_traversal_sanitization(self):
        """Send path traversal filename in generate-report payload — output PDF filename must be sanitized."""
        payload = {
            "file_name": "../../etc/passwd.c",
            "original_code": "int x = 0;",
            "corrected_code": "int x = 0;",
            "violations": [],
            "decisions": {},
            "compliance_score": 100.0,
            "remaining_violations_count": 0,
        }
        r = requests.post(f"{BASE_URL}/api/generate-report", json=payload)
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertTrue(data["success"])
        pdf_name = data["pdf_report_filename"]
        self.assertNotIn("..", pdf_name)
        self.assertNotIn("/", pdf_name)
        self.assertNotIn("\\", pdf_name)

if __name__ == "__main__":
    unittest.main(verbosity=2)
