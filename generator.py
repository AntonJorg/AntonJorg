"""Build the static site into build/.

Articles live one folder each under src/articles, holding an index.md with
required front matter (title, date, summary) plus any assets it references.
Each becomes build/articles/<slug>/index.html, and its teaser is injected into
the home page.
"""

import datetime
import html
import re
import shutil
import sys
from dataclasses import dataclass
from pathlib import Path

import markdown

SRC = Path("src")
BUILD = Path("build")
ARTICLES_SRC = SRC / "articles"
ARTICLES_OUT = BUILD / "articles"

MARKDOWN_EXTENSIONS = ["extra", "meta", "smarty", "codehilite"]

# Highlighting happens at build time, so pages need no JavaScript. Only fenced
# blocks that name their language are highlighted — guessing tends to colour
# plain-text blocks (directory trees, output dumps) as if they were code.
MARKDOWN_EXTENSION_CONFIGS = {"codehilite": {"guess_lang": False}}


def fail(message: str) -> None:
    raise SystemExit(f"error: {message}")


def replace_block(template: str, name: str, content: str) -> str:
    """Replace everything between <!-- BEGIN name --> and <!-- END name -->.

    A missing marker is a build error rather than a silent no-op: dropping one
    while editing a template would otherwise produce a page with no articles.
    """
    begin, end = f"<!-- BEGIN {name} -->", f"<!-- END {name} -->"
    pattern = re.compile(re.escape(begin) + ".*?" + re.escape(end), re.DOTALL)
    if not pattern.search(template):
        fail(f"template is missing the {begin} … {end} markers")
    return pattern.sub(lambda _: f"{begin}\n{content}\n{end}", template, count=1)


def format_date(date: datetime.date) -> str:
    # Not strftime("%-d") — that padding flag is glibc-only.
    return f"{date:%B} {date.day}, {date.year}"


@dataclass
class Article:
    slug: str
    title: str
    date: datetime.date
    summary: str
    body_html: str
    source_dir: Path


def parse_article(source_dir: Path) -> Article:
    source = source_dir / "index.md"
    md = markdown.Markdown(
        extensions=MARKDOWN_EXTENSIONS,
        extension_configs=MARKDOWN_EXTENSION_CONFIGS,
    )
    body_html = md.convert(source.read_text(encoding="utf-8"))

    # The meta extension hands back every value as a list of lines.
    meta = {key: " ".join(value).strip() for key, value in md.Meta.items()}
    for key in ("title", "date", "summary"):
        if not meta.get(key):
            fail(f"{source}: front matter is missing required key '{key}'")

    try:
        date = datetime.date.fromisoformat(meta["date"])
    except ValueError:
        fail(f"{source}: date '{meta['date']}' is not a valid ISO date (YYYY-MM-DD)")

    return Article(
        slug=source_dir.name,
        title=meta["title"],
        date=date,
        summary=meta["summary"],
        body_html=body_html,
        source_dir=source_dir,
    )


def collect_articles() -> list[Article]:
    if not ARTICLES_SRC.is_dir():
        return []

    articles = []
    for source_dir in sorted(p for p in ARTICLES_SRC.iterdir() if p.is_dir()):
        if not (source_dir / "index.md").is_file():
            print(f"warning: {source_dir} has no index.md, skipping", file=sys.stderr)
            continue
        articles.append(parse_article(source_dir))

    articles.sort(key=lambda a: (a.date, a.slug), reverse=True)
    return articles


def render_article(article: Article, template: str) -> None:
    head = (
        f"<title>{html.escape(article.title)} — Anton Jørgensen</title>\n"
        f'  <meta name="description" content="{html.escape(article.summary, quote=True)}">'
    )
    body = (
        '<article class="article-body">\n'
        "        <header>\n"
        f"          <h1>{html.escape(article.title)}</h1>\n"
        f'          <time datetime="{article.date.isoformat()}">'
        f"{format_date(article.date)}</time>\n"
        "        </header>\n"
        f"{article.body_html}\n"
        "      </article>"
    )

    page = replace_block(template, "HEAD", head)
    page = replace_block(page, "ARTICLE_BODY", body)

    out_dir = ARTICLES_OUT / article.slug
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "index.html").write_text(page, encoding="utf-8")

    # Everything else in the folder is an asset the markdown may link to
    # relatively, so it lands beside the page it belongs to.
    shutil.copytree(
        article.source_dir,
        out_dir,
        ignore=shutil.ignore_patterns("index.md"),
        dirs_exist_ok=True,
    )


def render_index(articles: list[Article], template: str) -> None:
    teasers = "\n".join(
        '      <article class="teaser">\n'
        f'        <h3><a href="articles/{article.slug}/">'
        f"{html.escape(article.title)}</a></h3>\n"
        f'        <time datetime="{article.date.isoformat()}">'
        f"{format_date(article.date)}</time>\n"
        f"        <p>{html.escape(article.summary)}</p>\n"
        "      </article>"
        for article in articles
    )
    page = replace_block(template, "ARTICLES", teasers)
    (BUILD / "index.html").write_text(page, encoding="utf-8")


def main() -> None:
    articles = collect_articles()

    shutil.rmtree(BUILD, ignore_errors=True)
    BUILD.mkdir(parents=True)
    shutil.copy(SRC / "styles.css", BUILD)
    shutil.copytree(SRC / "images", BUILD / "images")

    article_template = (SRC / "article.html").read_text(encoding="utf-8")
    for article in articles:
        render_article(article, article_template)

    render_index(articles, (SRC / "index.html").read_text(encoding="utf-8"))

    print(f"built {len(articles)} article(s) into {BUILD}/")


if __name__ == "__main__":
    main()
