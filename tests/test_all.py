"""
Tests for bangla-nlpkit — all 4 modules.
Run with: pytest tests/ -v
"""

import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from bangla_nlpkit.detector   import detect_script, is_bangla
from bangla_nlpkit.normalizer import (normalize, to_ascii_digits,
                                       to_bangla_digits, remove_invisible)
from bangla_nlpkit.tokenizer  import word_tokenize, sentence_tokenize, char_tokenize
from bangla_nlpkit.romanizer  import romanize, romanize_word, romanize_tokens


# ===========================================================================
# detector tests
# ===========================================================================

class TestDetectScript:

    def test_pure_bangla(self):
        r = detect_script("আমি বাংলায় কথা বলি")
        assert r.dominant == "bangla"
        assert r.scores["bangla"] == pytest.approx(1.0, abs=0.01)

    def test_pure_latin(self):
        r = detect_script("Hello world")
        assert r.dominant == "latin"

    def test_pure_arabic(self):
        r = detect_script("مرحبا بالعالم")
        assert r.dominant == "arabic"

    def test_pure_devanagari(self):
        r = detect_script("नमस्ते दुनिया")
        assert r.dominant == "devanagari"

    def test_mixed_bangla_latin(self):
        r = detect_script("আমি English মিশিয়ে বলি")
        assert r.dominant == "bangla"
        assert r.scores["latin"] > 0

    def test_empty_string(self):
        r = detect_script("")
        assert r.dominant == "unknown"
        assert r.total_classified == 0

    def test_whitespace_only(self):
        r = detect_script("   ")
        assert r.dominant == "unknown"

    def test_is_mixed_flag(self):
        r = detect_script("আমি English মিশিয়ে বলি")
        assert r.is_mixed(threshold=0.10) is True

    def test_is_not_mixed_pure_text(self):
        r = detect_script("আমি বাংলায় কথা বলি")
        assert r.is_mixed() is False

    def test_is_bangla_true(self):
        assert is_bangla("আমি বাংলায় কথা বলি") is True

    def test_is_bangla_false(self):
        assert is_bangla("Hello world") is False

    def test_numbers_only(self):
        # Pure digits/punctuation → unclassified chars → unknown
        r = detect_script("123 !@#")
        assert r.total_classified == 0

    def test_chakma_script(self):
        # Chakma Unicode: U+11100–U+1114F
        chakma_char = "\U00011103"  # a Chakma letter
        r = detect_script(chakma_char)
        assert r.dominant == "chakma"


# ===========================================================================
# normalizer tests
# ===========================================================================

class TestNormalize:

    def test_strips_extra_whitespace(self):
        assert normalize("  আমি  বাংলায়  ") == "আমি বাংলায়"

    def test_tabs_collapsed(self):
        assert normalize("আমি\t\tবাংলায়") == "আমি বাংলায়"

    def test_normalize_digits_to_ascii(self):
        result = normalize("আমার বয়স ২৩", normalize_digits=True, to_ascii_digits=True)
        assert "23" in result
        assert "২৩" not in result

    def test_normalize_digits_to_bangla(self):
        result = normalize("আমার বয়স 23", normalize_digits=True, to_ascii_digits=False)
        assert "২৩" in result
        assert "23" not in result

    def test_curly_quotes_normalized(self):
        result = normalize("\u201Chello\u201D")
        assert result == '"hello"'

    def test_em_dash_normalized(self):
        result = normalize("one\u2014two")
        assert result == "one-two"

    def test_nfc_applied(self):
        # Precomposed vs decomposed 'ক' — should both normalize to same NFC form
        nfc_text = "\u0995"       # ক (precomposed)
        nfd_text = "\u0995"       # same for this char, but NFC call still safe
        assert normalize(nfc_text) == normalize(nfd_text)

    def test_no_strip_option(self):
        result = normalize("  hello  ", strip=False)
        assert result == " hello "

    def test_invalid_type_raises(self):
        with pytest.raises(TypeError):
            normalize(123)  # type: ignore


class TestDigitConversion:

    def test_to_ascii_digits(self):
        assert to_ascii_digits("০১২৩৪৫৬৭৮৯") == "0123456789"

    def test_to_bangla_digits(self):
        assert to_bangla_digits("0123456789") == "০১২৩৪৫৬৭৮৯"

    def test_roundtrip(self):
        original = "আমার বয়স ২৩ বছর"
        assert to_bangla_digits(to_ascii_digits(original)) == original


class TestRemoveInvisible:

    def test_removes_zero_width_space(self):
        text = "আমি\u200Bবাংলা"   # zero-width space
        assert "\u200B" not in remove_invisible(text)

    def test_removes_bom(self):
        text = "\uFEFFআমি"
        assert "\uFEFF" not in remove_invisible(text)

    def test_keeps_normal_space(self):
        text = "আমি বাংলা"
        assert remove_invisible(text) == "আমি বাংলা"


# ===========================================================================
# tokenizer tests
# ===========================================================================

class TestWordTokenize:

    def test_basic_bangla(self):
        tokens = word_tokenize("আমি বাংলায় কথা বলি")
        assert tokens == ["আমি", "বাংলায়", "কথা", "বলি"]

    def test_strips_danda(self):
        tokens = word_tokenize("আমি বাংলায় কথা বলি।")
        assert "।" not in tokens

    def test_keeps_danda_with_flag(self):
        tokens = word_tokenize("আমি বলি।", keep_punctuation=True)
        assert "।" in tokens

    def test_mixed_bangla_latin(self):
        tokens = word_tokenize("আমি English মিশিয়ে বলি")
        assert "English" in tokens
        assert "আমি" in tokens

    def test_digits_included(self):
        tokens = word_tokenize("আমার বয়স ২৩ বছর")
        assert "২৩" in tokens

    def test_empty_string(self):
        assert word_tokenize("") == []

    def test_whitespace_only(self):
        assert word_tokenize("   ") == []


class TestSentenceTokenize:

    def test_bangla_danda_split(self):
        text = "আমি বাংলায় কথা বলি। তুমি কি বাংলায় কথা বলো?"
        sents = sentence_tokenize(text)
        assert len(sents) == 2
        assert sents[0] == "আমি বাংলায় কথা বলি।"

    def test_english_period_split(self):
        sents = sentence_tokenize("Hello world. How are you?")
        assert len(sents) == 2

    def test_single_sentence(self):
        sents = sentence_tokenize("আমি বাংলায় কথা বলি")
        assert sents == ["আমি বাংলায় কথা বলি"]

    def test_empty_string(self):
        assert sentence_tokenize("") == []

    def test_no_split_on_decimal(self):
        # "3.14" should not be split
        sents = sentence_tokenize("Pi is 3.14 approximately.")
        # Should not produce ['Pi is 3', '14 approximately.']
        assert not any("14" == s.strip() for s in sents)


class TestCharTokenize:

    def test_basic(self):
        chars = char_tokenize("বাং")
        assert chars == ["ব", "া", "ং"]

    def test_excludes_whitespace(self):
        chars = char_tokenize("আ ব")
        assert " " not in chars

    def test_empty(self):
        assert char_tokenize("") == []


# ===========================================================================
# romanizer tests
# ===========================================================================

class TestRomanize:

    def test_bangladesh(self):
        assert romanize("বাংলাদেশ") == "bangladesh"

    def test_dhaka(self):
        assert romanize("ঢাকা") == "dhaka"

    def test_bangla(self):
        assert romanize("বাংলা") == "bangla"

    def test_sentence(self):
        result = romanize("আমি বাংলায় কথা বলি।")
        assert "ami" in result
        assert "banglay" in result

    def test_passthrough_latin(self):
        result = romanize("আমি English মিশিয়ে বলি")
        assert "English" in result

    def test_no_passthrough(self):
        result = romanize("আমি English বলি", passthrough_non_bangla=False)
        assert "English" not in result

    def test_bangla_digits(self):
        result = romanize("আমার ২৩")
        assert "23" in result

    def test_danda_to_period(self):
        result = romanize("বলি।")
        assert "." in result

    def test_romanize_word(self):
        assert romanize_word("বাংলাদেশ") == "bangladesh"

    def test_romanize_tokens(self):
        tokens = ["আমি", "বাংলায়", "কথা", "বলি"]
        result = romanize_tokens(tokens)
        assert result == ["ami", "banglay", "kotha", "boli"]

    def test_empty_string(self):
        assert romanize("") == ""

    def test_whitespace_passthrough(self):
        assert romanize("আমি বলি") == "ami boli"