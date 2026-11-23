import base64
import io
import json
import os
import unittest
from unittest.mock import patch
from zipfile import ZipFile

import app
from pypdf import PdfWriter


def encoded(data):
    return base64.b64encode(data).decode()


class DocumentTests(unittest.TestCase):
    def test_text_and_word_documents(self):
        self.assertEqual(app.extract_document("paper.txt", encoded(b"\xef\xbb\xbfHello world")), "Hello world")
        document = b'''<w:document xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main"><w:body><w:p><w:r><w:t>First</w:t></w:r></w:p><w:p><w:r><w:t>Second</w:t></w:r></w:p></w:body></w:document>'''
        data = io.BytesIO()
        with ZipFile(data, "w") as archive:
            archive.writestr("word/document.xml", document)
        self.assertEqual(app.extract_document("paper.docx", encoded(data.getvalue())), "First\nSecond")

    def test_empty_pdf_and_bad_files_are_rejected(self):
        writer = PdfWriter()
        writer.add_blank_page(width=100, height=100)
        data = io.BytesIO()
        writer.write(data)
        for name, content in [("paper.pdf", encoded(data.getvalue())), ("paper.docx", encoded(b"bad")), ("paper.txt", "!"), ("paper.rtf", encoded(b"text"))]:
            with self.subTest(name=name), self.assertRaises(ValueError):
                app.extract_document(name, content)

    def test_file_size_and_extracted_text_limits(self):
        with self.assertRaises(ValueError):
            app.extract_document("paper.txt", encoded(b"x" * (app.MAX_FILE_BYTES + 1)))
        with self.assertRaises(ValueError):
            app.extract_document("paper.txt", encoded(b"x" * (app.MAX_TEXT + 1)))


class GenerationTests(unittest.TestCase):
    def setUp(self):
        self.payload = {
            "action": "revise", "samples": ["My writing."], "profile": "Direct.",
            "assignment": "An essay", "rubric": "Use examples", "guidance": "Be concise",
            "draft": "My edited draft", "revision": "Improve the ending",
        }

    def test_revision_includes_context_and_preserves_task(self):
        messages = app.build_messages(self.payload)
        context = json.loads(messages[1]["content"])
        self.assertEqual(context["writing_samples"], ["My writing."])
        for key in ("profile", "assignment", "rubric", "guidance", "draft", "revision"):
            self.assertEqual(context[key], self.payload[key])
        self.assertIn("complete revised paper", messages[0]["content"])

    def test_analysis_and_draft_send_only_relevant_context(self):
        self.payload["action"] = "analyze"
        self.assertEqual(json.loads(app.build_messages(self.payload)[1]["content"]), {"writing_samples": ["My writing."]})
        self.payload["action"] = "draft"
        context = json.loads(app.build_messages(self.payload)[1]["content"])
        self.assertNotIn("draft", context)
        self.assertNotIn("revision", context)
        self.assertEqual(context["rubric"], "Use examples")

    def test_required_inputs_are_validated(self):
        for key in ("draft", "revision", "profile"):
            payload = {**self.payload, key: ""}
            with self.subTest(key=key), self.assertRaises(ValueError):
                app.build_messages(payload)
        for samples in ([], [" "], ["x"] * 11):
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                app.build_messages({**self.payload, "samples": samples})
        with self.assertRaises(ValueError):
            app.build_messages({**self.payload, "action": "draft", "assignment": ""})

    @patch.dict(os.environ, {"OPENAI_API_KEY": "test-key"})
    @patch("app.urlopen")
    def test_provider_request_and_truncation(self, urlopen):
        response = urlopen.return_value.__enter__.return_value
        response.read.return_value = json.dumps({"choices": [{"message": {"content": "Revised paper"}, "finish_reason": "stop"}]}).encode()
        self.assertEqual(app.generate(self.payload), "Revised paper")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.get_header("Authorization"), "Bearer " + "test-key")
        self.assertEqual(json.loads(request.data)["messages"], app.build_messages(self.payload))
        response.read.return_value = json.dumps({"choices": [{"message": {"content": "Cut off"}, "finish_reason": "length"}]}).encode()
        with self.assertRaisesRegex(ValueError, "cut off"):
            app.generate(self.payload)

    @patch.dict(os.environ, {}, clear=True)
    def test_missing_api_key(self):
        with self.assertRaisesRegex(ValueError, "OPENAI_API_KEY"):
            app.generate(self.payload)


if __name__ == "__main__":
    unittest.main()
