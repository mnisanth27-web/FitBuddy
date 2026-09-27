from bleach import clean
from markdown import markdown
from markupsafe import Markup

_ALLOWED_TAGS = {
    "a", "blockquote", "br", "code", "del", "em", "h1", "h2", "h3", "h4", "h5", "h6",
    "hr", "i", "li", "ol", "p", "pre", "strong", "table", "tbody", "td", "th", "thead", "tr", "ul",
}
_ALLOWED_ATTRIBUTES = {"a": ["href", "title"], "td": ["align"], "th": ["align"]}

def render_markdown(value: str | None) -> Markup:
    """Render generated Markdown while stripping unsafe HTML and attributes."""
    source = value or ""
    rendered = markdown(source, extensions=["tables", "fenced_code", "sane_lists"])
    safe_html = clean(
        rendered,
        tags=_ALLOWED_TAGS,
        attributes=_ALLOWED_ATTRIBUTES,
        protocols=["http", "https", "mailto"],
        strip=True,
        strip_comments=True,
    )
    return Markup(safe_html)
