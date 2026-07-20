import json
import html
from datetime import datetime

from dateutil import parser as date_parser

DATABASE = "output/database.jsonl"
OUTPUT = "output/index.html"
PER_PAGE = 10  # articles per page — change this number if you want


PAGE_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>News Summaries</title>
<style>
  :root {
    --bg: #f5f6f8;
    --card-bg: #ffffff;
    --text: #1a1a1a;
    --muted: #6b7280;
    --accent: #2563eb;
    --border: #e5e7eb;
  }
  * { box-sizing: border-box; }
  body {
    margin: 0;
    background: var(--bg);
    color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    line-height: 1.6;
  }
  header {
    background: var(--card-bg);
    border-bottom: 1px solid var(--border);
    padding: 32px 20px;
    text-align: center;
  }
  header h1 { margin: 0 0 6px; font-size: 28px; }
  header p { margin: 0; color: var(--muted); font-size: 14px; }
  main { max-width: 760px; margin: 0 auto; padding: 28px 20px 60px; }
  .card {
    background: var(--card-bg);
    border: 1px solid var(--border);
    border-radius: 12px;
    padding: 22px 24px;
    margin-bottom: 18px;
    box-shadow: 0 1px 3px rgba(0,0,0,0.04);
  }
  .card-title { margin: 0 0 8px; font-size: 19px; line-height: 1.35; }
  .card-meta { color: var(--muted); font-size: 13px; margin-bottom: 12px; }
  .card-summary { margin: 0 0 16px; }
  .card-link { color: var(--accent); text-decoration: none; font-size: 14px; font-weight: 500; }
  .card-link:hover { text-decoration: underline; }
  .pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: 16px;
    margin-top: 28px;
  }
  .pagination button {
    background: var(--accent);
    color: #fff;
    border: none;
    border-radius: 8px;
    padding: 9px 18px;
    font-size: 14px;
    font-weight: 500;
    cursor: pointer;
  }
  .pagination button:disabled {
    background: #c7cbd1;
    cursor: default;
  }
  .page-info { color: var(--muted); font-size: 14px; }
</style>
</head>
<body>
  <header>
    <h1>News Summaries</h1>
    <p>__COUNT__ articles · generated __GENERATED__</p>
  </header>
  <main>
    <div id="articles"></div>
    <div class="pagination">
      <button id="prevBtn">← Previous</button>
      <span class="page-info" id="pageInfo"></span>
      <button id="nextBtn">Next →</button>
    </div>
  </main>

  <script>
    const articles = __DATA__;
    const perPage = __PER_PAGE__;
    let currentPage = 1;
    const totalPages = Math.max(1, Math.ceil(articles.length / perPage));

    const container = document.getElementById("articles");
    const prevBtn = document.getElementById("prevBtn");
    const nextBtn = document.getElementById("nextBtn");
    const pageInfo = document.getElementById("pageInfo");

    function escapeHtml(str) {
      const div = document.createElement("div");
      div.textContent = str == null ? "" : str;
      return div.innerHTML;
    }

    function render() {
      const start = (currentPage - 1) * perPage;
      const pageItems = articles.slice(start, start + perPage);

      container.innerHTML = pageItems.map(function (a) {
        const title = escapeHtml(a.title || "Untitled");
        const summary = a.summary
          ? escapeHtml(a.summary)
          : "<em>No summary available.</em>";
        const meta = escapeHtml(a.meta || "");
        const url = escapeHtml(a.url || "#");
        return (
          '<article class="card">' +
            '<h2 class="card-title">' + title + '</h2>' +
            '<div class="card-meta">' + meta + '</div>' +
            '<p class="card-summary">' + summary + '</p>' +
            '<a class="card-link" href="' + url + '" target="_blank" rel="noopener">Read original →</a>' +
          '</article>'
        );
      }).join("");

      pageInfo.textContent = "Page " + currentPage + " of " + totalPages;
      prevBtn.disabled = currentPage === 1;
      nextBtn.disabled = currentPage === totalPages;
      window.scrollTo(0, 0);
    }

    prevBtn.addEventListener("click", function () {
      if (currentPage > 1) { currentPage--; render(); }
    });
    nextBtn.addEventListener("click", function () {
      if (currentPage < totalPages) { currentPage++; render(); }
    });

    render();
  </script>
</body>
</html>"""


def load_articles(path):
    articles = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                articles.append(json.loads(line))
    return articles


def sort_key(article):
    pub = article.get("published_at")
    if pub:
        try:
            dt = date_parser.parse(pub)
            if dt.tzinfo:
                dt = dt.replace(tzinfo=None)
            return dt
        except Exception:
            pass
    return datetime.min


def format_date(pub):
    if not pub:
        return ""
    try:
        return date_parser.parse(pub).strftime("%d %B %Y, %H:%M")
    except Exception:
        return ""


def to_view(article):
    """Trim each article down to just what the page needs."""
    source = article.get("source") or ""
    date_str = format_date(article.get("published_at"))
    meta = source + (" · " + date_str if date_str else "")
    return {
        "title": article.get("translated_title") or article.get("title") or "Untitled",
        "summary": (article.get("summary") or "").strip(),
        "meta": meta,
        "url": article.get("url") or "#",
    }


def build_website():
    articles = load_articles(DATABASE)
    articles.sort(key=sort_key, reverse=True)

    view_data = [to_view(a) for a in articles]
    data_json = json.dumps(view_data, ensure_ascii=False)
    generated = datetime.now().strftime("%d %B %Y, %H:%M")

    page = (
        PAGE_TEMPLATE
        .replace("__COUNT__", str(len(articles)))
        .replace("__GENERATED__", generated)
        .replace("__PER_PAGE__", str(PER_PAGE))
        .replace("__DATA__", data_json)
    )

    with open(OUTPUT, "w", encoding="utf-8") as f:
        f.write(page)

    print(f"Built {OUTPUT} with {len(articles)} articles ({PER_PAGE} per page).")


if __name__ == "__main__":
    build_website()