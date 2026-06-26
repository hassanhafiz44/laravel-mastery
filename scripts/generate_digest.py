#!/usr/bin/env python3
"""
Laravel Daily Digest — fetches the real Laravel 13.x documentation page for today's topic
and saves it as a clean markdown file to laravel-digest/YYYY-MM-DD.md
"""

import datetime
import os
import re
import urllib.request
import html

# Ordered exactly as Laravel recommends in their "Next Steps" + logical progression
TOPICS = [
    ("installation",            "Installation"),
    ("lifecycle",               "Request Lifecycle"),
    ("configuration",           "Configuration"),
    ("structure",               "Directory Structure"),
    ("frontend",                "Frontend"),
    ("container",               "Service Container"),
    ("facades",                 "Facades"),
    ("routing",                 "Routing"),
    ("middleware",              "Middleware"),
    ("csrf",                    "CSRF Protection"),
    ("controllers",             "Controllers"),
    ("requests",                "HTTP Requests"),
    ("responses",               "HTTP Responses"),
    ("views",                   "Views"),
    ("blade",                   "Blade Templates"),
    ("vite",                    "Asset Bundling (Vite)"),
    ("urls",                    "URL Generation"),
    ("session",                 "Session"),
    ("validation",              "Validation"),
    ("errors",                  "Error Handling"),
    ("logging",                 "Logging"),
    ("digging-deeper/artisan",  "Artisan Console"),
    ("digging-deeper/broadcasting", "Broadcasting"),
    ("cache",                   "Cache"),
    ("digging-deeper/collections", "Collections"),
    ("digging-deeper/concurrency", "Concurrency"),
    ("digging-deeper/context",  "Context"),
    ("digging-deeper/contracts", "Contracts"),
    ("digging-deeper/events",   "Events & Listeners"),
    ("digging-deeper/filesystem", "File Storage"),
    ("digging-deeper/helpers",  "Helpers"),
    ("digging-deeper/http-client", "HTTP Client"),
    ("digging-deeper/localization", "Localization"),
    ("digging-deeper/mail",     "Mail"),
    ("digging-deeper/notifications", "Notifications"),
    ("digging-deeper/packages", "Package Development"),
    ("digging-deeper/processes", "Processes"),
    ("digging-deeper/queues",   "Queues"),
    ("digging-deeper/rate-limiting", "Rate Limiting"),
    ("digging-deeper/strings",  "Strings"),
    ("digging-deeper/scheduling", "Task Scheduling"),
    ("database",                "Database: Getting Started"),
    ("queries",                 "Query Builder"),
    ("pagination",              "Pagination"),
    ("migrations",              "Migrations"),
    ("seeding",                 "Seeding"),
    ("redis",                   "Redis"),
    ("eloquent",                "Eloquent: Getting Started"),
    ("eloquent-relationships",  "Eloquent: Relationships"),
    ("eloquent-collections",    "Eloquent: Collections"),
    ("eloquent-mutators",       "Eloquent: Mutators & Casting"),
    ("eloquent-api-resources",  "Eloquent: API Resources"),
    ("eloquent-serialization",  "Eloquent: Serialization"),
    ("eloquent-factories",      "Eloquent: Factories"),
    ("authentication",          "Authentication"),
    ("authorization",           "Authorization"),
    ("verification",            "Email Verification"),
    ("encryption",              "Encryption"),
    ("hashing",                 "Hashing"),
    ("passwords",               "Password Reset"),
    ("sanctum",                 "Sanctum"),
    ("scout",                   "Scout (Full-Text Search)"),
    ("horizon",                 "Horizon (Queue Dashboard)"),
    ("telescope",               "Telescope (Debug Assistant)"),
    ("testing",                 "Testing: Getting Started"),
    ("http-tests",              "HTTP Tests"),
    ("console-tests",           "Console Tests"),
    ("dusk",                    "Browser Tests (Dusk)"),
    ("database-testing",        "Database Testing"),
    ("mocking",                 "Mocking"),
]

BASE_URL = "https://laravel.com/docs/13.x/"
START_DATE = datetime.date(2026, 6, 27)


def get_topic_for_date(date: datetime.date):
    index = (date - START_DATE).days % len(TOPICS)
    slug, name = TOPICS[index]
    return index, slug, name


def fetch_doc(slug: str) -> str:
    url = BASE_URL + slug
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return resp.read().decode("utf-8")


def extract_content(html_src: str, page_title: str) -> str:
    """
    Pull the main doc content out of the Laravel HTML page.
    Laravel renders docs server-side so the content is in <div id="main-content"> or similar.
    We strip HTML tags and clean up the text into readable markdown.
    """
    # Try to grab the main content block
    # Laravel wraps doc content in <div class="...prose..."> or <section>
    # We'll extract everything between the first <h1> and the "On this page" nav

    # Remove script and style blocks
    html_src = re.sub(r'<script[^>]*>.*?</script>', '', html_src, flags=re.DOTALL)
    html_src = re.sub(r'<style[^>]*>.*?</style>', '', html_src, flags=re.DOTALL)

    # Find content between first h1 and "On this page" section
    match = re.search(r'(<h1.*?)(### On this page|on this page)', html_src, re.DOTALL | re.IGNORECASE)
    if match:
        html_src = match.group(1)
    else:
        # fallback: take everything after <main or first h1
        h1_match = re.search(r'<h1', html_src)
        if h1_match:
            html_src = html_src[h1_match.start():]

    # Convert headings
    html_src = re.sub(r'<h1[^>]*>(.*?)</h1>', r'# \1', html_src, flags=re.DOTALL)
    html_src = re.sub(r'<h2[^>]*>(.*?)</h2>', r'\n## \1', html_src, flags=re.DOTALL)
    html_src = re.sub(r'<h3[^>]*>(.*?)</h3>', r'\n### \1', html_src, flags=re.DOTALL)
    html_src = re.sub(r'<h4[^>]*>(.*?)</h4>', r'\n#### \1', html_src, flags=re.DOTALL)

    # Convert code blocks
    html_src = re.sub(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', lambda m: '\n```\n' + html.unescape(m.group(1)).strip() + '\n```\n', html_src, flags=re.DOTALL)

    # Convert inline code
    html_src = re.sub(r'<code[^>]*>(.*?)</code>', lambda m: '`' + html.unescape(m.group(1)) + '`', html_src, flags=re.DOTALL)

    # Convert links — keep text only for readability, drop href clutter
    html_src = re.sub(r'<a[^>]*href="([^"]*)"[^>]*>(.*?)</a>', r'\2', html_src, flags=re.DOTALL)

    # Convert bold/strong
    html_src = re.sub(r'<(strong|b)[^>]*>(.*?)</(strong|b)>', r'**\2**', html_src, flags=re.DOTALL)

    # Convert em/italic
    html_src = re.sub(r'<(em|i)[^>]*>(.*?)</(em|i)>', r'*\2*', html_src, flags=re.DOTALL)

    # Convert list items
    html_src = re.sub(r'<li[^>]*>(.*?)</li>', r'- \1', html_src, flags=re.DOTALL)
    html_src = re.sub(r'<[ou]l[^>]*>', '', html_src)
    html_src = re.sub(r'</[ou]l>', '', html_src)

    # Convert paragraphs
    html_src = re.sub(r'<p[^>]*>(.*?)</p>', r'\n\1\n', html_src, flags=re.DOTALL)

    # Convert blockquotes / notes
    html_src = re.sub(r'<blockquote[^>]*>(.*?)</blockquote>', lambda m: '\n> ' + m.group(1).strip().replace('\n', '\n> ') + '\n', html_src, flags=re.DOTALL)

    # Strip all remaining HTML tags
    html_src = re.sub(r'<[^>]+>', '', html_src)

    # Decode HTML entities
    html_src = html.unescape(html_src)

    # Clean up excessive whitespace
    html_src = re.sub(r'\n{4,}', '\n\n\n', html_src)
    html_src = re.sub(r'[ \t]+\n', '\n', html_src)
    html_src = html_src.strip()

    return html_src


def build_digest(date: datetime.date, index: int, slug: str, name: str, content: str) -> str:
    total = len(TOPICS)
    day_num = (date - START_DATE).days + 1
    next_index = (index + 1) % total
    next_slug, next_name = TOPICS[next_index]
    next_url = BASE_URL + next_slug

    header = f"""# Laravel 13.x — {name}
> **Day {day_num} | Topic {index + 1}/{total}**
> Source: {BASE_URL}{slug}
> Date: {date.strftime('%B %d, %Y')}
> Next: [{next_name}]({next_url})

---

"""
    return header + content


if __name__ == "__main__":
    today = datetime.date.today()
    index, slug, name = get_topic_for_date(today)

    print(f"Fetching: {BASE_URL}{slug}  ({name})")
    raw_html = fetch_doc(slug)
    content = extract_content(raw_html, name)
    digest = build_digest(today, index, slug, name, content)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "laravel-digest")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{today.isoformat()}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"Written: {output_path}")
    print(f"Size: {len(content)} chars")
