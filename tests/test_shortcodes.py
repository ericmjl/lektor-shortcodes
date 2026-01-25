"""Tests for the shortcodes functionality."""

# Test the scodes module directly without importing the main package
import os
import sys
from typing import Any, Optional

import pytest

# Add the package root to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

# Import the scodes module directly
from lektor_shortcodes.scodes import Parser, RenderingError, register


def test_parser_initialization() -> None:
    """Test that parser initializes correctly."""
    parser = Parser()
    assert parser.start == "[%"
    assert parser.ends == []  # ends starts empty
    assert parser.esc_start == "\\[%"  # Check the escape start pattern


def test_register_handler() -> None:
    """Test registering a shortcode handler."""
    parser = Parser()

    def test_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        return f"<div>{content or 'no content'}</div>"

    parser.register(test_handler, "test")
    assert "test" in parser.tags
    assert parser.tags["test"]["func"] == test_handler


def test_parse_simple_shortcode() -> None:
    """Test parsing a simple shortcode."""
    parser = Parser()

    def test_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        return f"<div>Hello {kwargs.get('name', 'World')}</div>"

    parser.register(test_handler, "hello")
    result = parser.parse("[% hello name=Test %]")
    assert "Hello Test" in result


def test_parse_shortcode_with_content() -> None:
    """Test parsing a shortcode with content."""
    parser = Parser()

    def test_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        return f"<div class='{kwargs.get('class', 'default')}'>{content}</div>"

    parser.register(test_handler, "div", "enddiv")
    result = parser.parse("[% div class=highlight %]This is content[% enddiv %]")
    assert "class='highlight'" in result
    assert "This is content" in result


def test_image_shortcode() -> None:
    """Test the image shortcode with align, image, and caption parameters."""
    parser = Parser()

    def image_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        align = kwargs.get("align", "")
        image = kwargs.get("image", "")
        caption = kwargs.get("caption", "")
        link = kwargs.get("link", "")

        html = f'<div class="align{align}">'
        if link:
            html += f'<a href="{link}">'
        html += f'<img src="{image}">'
        if link:
            html += "</a>"
        if caption:
            html += f'<span class="caption">{caption}</span>'
        html += "</div>"
        return html

    parser.register(image_handler, "image")

    # Test with all parameters
    result = parser.parse(
        '[% image align=right image=test.jpg caption="A test image" link=large.jpg %]'
    )
    assert '<div class="alignright">' in result
    assert '<img src="test.jpg">' in result
    assert '<span class="caption">A test image</span>' in result
    assert '<a href="large.jpg">' in result

    # Test without caption and link
    result_simple = parser.parse("[% image align=left image=simple.jpg %]")
    assert '<div class="alignleft">' in result_simple
    assert '<img src="simple.jpg">' in result_simple
    assert "caption" not in result_simple
    assert "<a" not in result_simple


def test_global_register_decorator() -> None:
    """Test the global register decorator function."""
    from lektor_shortcodes.scodes import globalends, globaltags

    # Clear any existing global registrations
    globaltags.clear()
    globalends.clear()

    @register("testglobal")
    def simple_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        return "<p>Global shortcode</p>"

    # Verify handler was registered globally
    assert "testglobal" in globaltags
    assert globaltags["testglobal"]["func"] == simple_handler
    assert globaltags["testglobal"]["endtag"] is None

    # Test with end tag
    @register("blockglobal", "endblockglobal")
    def block_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        return f"<div>{content}</div>"

    assert "blockglobal" in globaltags
    assert globaltags["blockglobal"]["endtag"] == "endblockglobal"
    assert "endblockglobal" in globalends

    # Clean up
    globaltags.clear()
    globalends.clear()


def test_error_handling_in_shortcode() -> None:
    """Test that exceptions in shortcode handlers are properly wrapped."""
    parser = Parser()

    def failing_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        raise ValueError("Intentional test error")

    parser.register(failing_handler, "fail")

    # Should raise RenderingError wrapping the original ValueError
    with pytest.raises(RenderingError) as exc_info:
        parser.parse("[% fail %]")

    # Check that the error message mentions the shortcode tag
    assert "fail" in str(exc_info.value)
    # Check that the original exception is preserved
    assert isinstance(exc_info.value.__cause__, ValueError)


def test_shortcode_with_positional_args() -> None:
    """Test shortcodes with positional arguments (no key=value)."""
    parser = Parser()

    def args_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        # pargs should contain positional arguments
        return f"<p>Args: {' '.join(pargs)}</p>"

    parser.register(args_handler, "args")
    result = parser.parse("[% args one two three %]")
    assert "one" in result
    assert "two" in result
    assert "three" in result


def test_shortcode_with_mixed_args() -> None:
    """Test shortcodes with both positional and keyword arguments."""
    parser = Parser()

    def mixed_handler(
        context: Any, content: Optional[str], pargs: list[str], kwargs: dict[str, str]
    ) -> str:
        return f"<p>Pargs: {len(pargs)}, Kwargs: {len(kwargs)}</p>"

    parser.register(mixed_handler, "mixed")
    result = parser.parse("[% mixed pos1 pos2 key1=value1 key2=value2 %]")
    # Should have 2 positional args and 2 keyword args
    assert "Pargs: 2" in result
    assert "Kwargs: 2" in result
