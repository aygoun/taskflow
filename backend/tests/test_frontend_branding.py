"""Branding tests for the frontend markup and Google color theme.

These tests read the static frontend files directly (no DB fixtures needed)
and assert that index.html carries the multicolor TaskFlow logo markup and
favicon, and that styles.css implements the Google color theme.
"""

import re
from html.parser import HTMLParser
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIR = REPO_ROOT / "frontend"
INDEX_HTML = FRONTEND_DIR / "index.html"
STYLES_CSS = FRONTEND_DIR / "styles.css"

GOOGLE_HEXES = ["#4285F4", "#EA4335", "#FBBC05", "#34A853"]
LOGO_CLASSES = {"g-blue", "g-red", "g-yellow", "g-green"}


class _HeadParser(HTMLParser):
    """Collect favicon link hrefs from <head> and spans inside the h1 logo."""

    def __init__(self):
        super().__init__()
        self.in_head = False
        self.in_h1 = False
        self.h1_spans = []  # list of (text, set_of_classes)
        self._current_span = None
        self.favicon_hrefs = []

    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "head":
            self.in_head = True
        elif tag == "h1" and "logo" in attrs.get("class", "").split():
            self.in_h1 = True
        elif tag == "link" and self.in_head and attrs.get("rel") == "icon":
            self.favicon_hrefs.append(attrs.get("href", ""))
        elif tag == "span" and self.in_h1:
            self._current_span = {"text": "", "classes": set(attrs.get("class", "").split())}

    def handle_endtag(self, tag):
        if tag == "head":
            self.in_head = False
        elif tag == "h1" and self.in_h1:
            self.in_h1 = False
        elif tag == "span" and self.in_h1 and self._current_span is not None:
            self.h1_spans.append((self._current_span["text"], self._current_span["classes"]))
            self._current_span = None

    def handle_data(self, data):
        if self.in_h1 and self._current_span is not None:
            self._current_span["text"] += data


@pytest.fixture(scope="module")
def index_html():
    return INDEX_HTML.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def styles_css():
    return STYLES_CSS.read_text(encoding="utf-8")


@pytest.fixture(scope="module")
def head_parser(index_html):
    parser = _HeadParser()
    parser.feed(index_html)
    return parser


class TestLogoMarkup:
    def test_logo_has_eight_letter_spans_spelling_taskflow(self, head_parser):
        texts = [text for text, _ in head_parser.h1_spans]
        assert len(head_parser.h1_spans) == 8
        assert "".join(texts) == "TaskFlow"

    def test_logo_span_classes_come_from_google_palette(self, head_parser):
        for _, classes in head_parser.h1_spans:
            branding = classes - {"g"}  # "g" is the shared base class on every span
            assert branding, "every logo span must carry a Google color class"
            assert branding <= LOGO_CLASSES

    def test_all_four_google_classes_used_in_logo(self, head_parser):
        used = set().union(*(classes - {"g"} for _, classes in head_parser.h1_spans))
        assert used == LOGO_CLASSES


class TestFavicon:
    def test_svg_data_uri_favicon_present(self, head_parser):
        assert any("data:image/svg+xml" in href for href in head_parser.favicon_hrefs)


class TestGoogleColorTheme:
    @pytest.mark.parametrize("hex_color", GOOGLE_HEXES)
    def test_styles_contains_google_hex(self, styles_css, hex_color):
        assert hex_color.lower() in styles_css.lower()

    def test_rainbow_bar_rule_defined(self, styles_css):
        assert re.search(r"\.rainbow-bar\b", styles_css)

    def test_logo_span_rules_defined(self, styles_css):
        assert re.search(r"\.logo\s+span", styles_css)
        for cls in LOGO_CLASSES:
            assert re.search(rf"\.{cls}\b", styles_css)
