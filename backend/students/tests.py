from django.test import SimpleTestCase

from .generation import SourceItem, normalise_numbered_lists, scrub_document_names, strip_leaked_tool_calls


class NumberedListRepairTests(SimpleTestCase):
    def test_repeated_model_numbering_is_repaired(self):
        self.assertEqual(
            normalise_numbered_lists("1. First\n1. Second\n1. Third"),
            "1. First\n2. Second\n3. Third",
        )


class ScrubDocumentNamesTests(SimpleTestCase):
    """Regression tests for a real production bug: scrub_document_names used to strip ANY
    source's title (including real legislation names), and produced doubled articles like
    "the the source material". Both are fixed - these tests exist so neither regresses.
    """

    def test_uploaded_document_titles_are_scrubbed(self):
        sources = [SourceItem(id="1", title="Prof Docs", kind="uploaded document")]
        text = "According to Prof Docs, the rule applies here."
        result = scrub_document_names(text, sources)
        self.assertNotIn("Prof Docs", result)

    def test_statute_and_case_names_are_never_scrubbed(self):
        # Real legal authorities must survive scrubbing even if a source with that exact
        # title exists - only kind == "uploaded document" is eligible for scrubbing.
        sources = [SourceItem(id="1", title="Official Secrets Act", kind="statute")]
        text = "This is governed by the Official Secrets Act and its provisions."
        result = scrub_document_names(text, sources)
        self.assertIn("Official Secrets Act", result)

    def test_no_doubled_article_after_scrubbing(self):
        sources = [SourceItem(id="1", title="Postal and Telecommunications Act", kind="uploaded document")]
        text = "governed by the Official Secrets Act and the Postal and Telecommunications Act."
        result = scrub_document_names(text, sources)
        self.assertNotIn("the the", result.lower())


class ToolCallLeakTests(SimpleTestCase):
    """Regression test for a real bug: a small model sometimes wrote tool-call syntax as
    visible text instead of actually invoking the tool, e.g. [cite_page(source_id="K1")].
    """

    def test_leaked_tool_call_syntax_is_stripped(self):
        text = 'The offer can be revoked before acceptance. [cite_page(source_id="K1", page="")]'
        result = strip_leaked_tool_calls(text)
        self.assertNotIn("cite_page", result)
        self.assertIn("The offer can be revoked before acceptance.", result)
