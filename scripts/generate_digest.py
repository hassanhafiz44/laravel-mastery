#!/usr/bin/env python3
"""
Laravel Daily Digest
Fetches the real Laravel 13.x doc page and extracts key points — like study notes.
"""

import datetime
import os
import re
import html
import urllib.request

TOPICS = [
    ("installation",                    "Installation"),
    ("lifecycle",                       "Request Lifecycle"),
    ("configuration",                   "Configuration"),
    ("structure",                       "Directory Structure"),
    ("frontend",                        "Frontend"),
    ("container",                       "Service Container"),
    ("facades",                         "Facades"),
    ("routing",                         "Routing"),
    ("middleware",                      "Middleware"),
    ("csrf",                            "CSRF Protection"),
    ("controllers",                     "Controllers"),
    ("requests",                        "HTTP Requests"),
    ("responses",                       "HTTP Responses"),
    ("views",                           "Views"),
    ("blade",                           "Blade Templates"),
    ("vite",                            "Asset Bundling (Vite)"),
    ("urls",                            "URL Generation"),
    ("session",                         "Session"),
    ("validation",                      "Validation"),
    ("errors",                          "Error Handling"),
    ("logging",                         "Logging"),
    ("digging-deeper/artisan",          "Artisan Console"),
    ("digging-deeper/broadcasting",     "Broadcasting"),
    ("cache",                           "Cache"),
    ("digging-deeper/collections",      "Collections"),
    ("digging-deeper/events",           "Events & Listeners"),
    ("digging-deeper/filesystem",       "File Storage"),
    ("digging-deeper/mail",             "Mail"),
    ("digging-deeper/notifications",    "Notifications"),
    ("digging-deeper/queues",           "Queues"),
    ("digging-deeper/scheduling",       "Task Scheduling"),
    ("digging-deeper/http-client",      "HTTP Client"),
    ("database",                        "Database: Getting Started"),
    ("queries",                         "Query Builder"),
    ("pagination",                      "Pagination"),
    ("migrations",                      "Migrations"),
    ("seeding",                         "Seeding"),
    ("redis",                           "Redis"),
    ("eloquent",                        "Eloquent: Getting Started"),
    ("eloquent-relationships",          "Eloquent: Relationships"),
    ("eloquent-collections",            "Eloquent: Collections"),
    ("eloquent-mutators",               "Eloquent: Mutators & Casting"),
    ("eloquent-api-resources",          "Eloquent: API Resources"),
    ("eloquent-serialization",          "Eloquent: Serialization"),
    ("eloquent-factories",              "Eloquent: Factories"),
    ("authentication",                  "Authentication"),
    ("authorization",                   "Authorization"),
    ("verification",                    "Email Verification"),
    ("encryption",                      "Encryption"),
    ("hashing",                         "Hashing"),
    ("passwords",                       "Password Reset"),
    ("sanctum",                         "Sanctum"),
    ("scout",                           "Scout (Full-Text Search)"),
    ("horizon",                         "Horizon"),
    ("telescope",                       "Telescope"),
    ("testing",                         "Testing: Getting Started"),
    ("http-tests",                      "HTTP Tests"),
    ("database-testing",                "Database Testing"),
    ("mocking",                         "Mocking"),
]

BASE_URL = "https://laravel.com/docs/13.x/"
START_DATE = datetime.date(2026, 6, 27)


def get_topic_for_date(date):
    index = (date - START_DATE).days % len(TOPICS)
    slug, name = TOPICS[index]
    return index, slug, name


def fetch_page(slug):
    url = BASE_URL + slug
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    with urllib.request.urlopen(req, timeout=20) as resp:
        return resp.read().decode("utf-8")


def html_to_text(raw):
    """Strip HTML to plain readable text."""
    raw = re.sub(r'<script[^>]*>.*?</script>', '', raw, flags=re.DOTALL)
    raw = re.sub(r'<style[^>]*>.*?</style>', '', raw, flags=re.DOTALL)
    # Strip all tags
    raw = re.sub(r'<[^>]+>', ' ', raw)
    raw = html.unescape(raw)
    raw = re.sub(r'[ \t]+', ' ', raw)
    raw = re.sub(r'\n\s*\n+', '\n\n', raw)
    return raw.strip()


def extract_sections(raw_html):
    """
    Pull h2/h3 headings + their paragraph content from the doc.
    Returns list of (heading, body_text) tuples.
    """
    # Cut off nav/footer noise — stop at "On this page"
    cut = re.search(r'on this page', raw_html, re.IGNORECASE)
    if cut:
        raw_html = raw_html[:cut.start()]

    # Find main content after first h1
    h1 = re.search(r'<h1', raw_html)
    if h1:
        raw_html = raw_html[h1.start():]

    # Split by h2/h3 headings
    parts = re.split(r'(<h[23][^>]*>.*?</h[23]>)', raw_html, flags=re.DOTALL)

    sections = []
    current_heading = None
    for part in parts:
        heading_match = re.match(r'<h[23][^>]*>(.*?)</h[23]>', part, re.DOTALL)
        if heading_match:
            current_heading = re.sub(r'<[^>]+>', '', heading_match.group(1)).strip()
            current_heading = html.unescape(current_heading)
        elif current_heading:
            text = html_to_text(part).strip()
            # Only keep sections with real content (skip tiny nav fragments)
            if len(text) > 80:
                sections.append((current_heading, text))
            current_heading = None

    return sections


def extract_code_examples(raw_html):
    """Pull the most illustrative code blocks from the page."""
    blocks = re.findall(r'<pre[^>]*><code[^>]*>(.*?)</code></pre>', raw_html, re.DOTALL)
    examples = []
    for block in blocks:
        code = html.unescape(re.sub(r'<[^>]+>', '', block)).strip()
        # Skip tiny one-liners that aren't meaningful, keep up to 5 good examples
        if len(code) > 30 and len(examples) < 5:
            # Trim very long blocks
            lines = code.splitlines()
            if len(lines) > 20:
                code = '\n'.join(lines[:20]) + '\n// ...'
            examples.append(code)
    return examples


def build_digest(date, index, slug, name, raw_html):
    total = len(TOPICS)
    day_num = (date - START_DATE).days + 1
    next_index = (index + 1) % total
    next_slug, next_name = TOPICS[next_index]

    sections = extract_sections(raw_html)
    code_examples = extract_code_examples(raw_html)

    lines = [
        f"# {name}",
        f"",
        f"**Day {day_num} | Topic {index + 1}/{total}** | [Docs]({BASE_URL}{slug}) | Next: [{next_name}]({BASE_URL}{next_slug})",
        f"",
        f"---",
        f"",
        f"## Key Points",
        f"",
    ]

    # Summarise each section into bullet points
    # We keep the heading and extract the most meaningful sentences
    for heading, body in sections:
        # Skip purely navigational headings
        if heading.lower() in ('introduction', 'next steps', 'further reading', 'see also'):
            continue

        lines.append(f"### {heading}")
        lines.append("")

        # Split body into sentences and pick the most informative ones (up to 3)
        sentences = re.split(r'(?<=[.!?])\s+', body)
        picked = []
        for s in sentences:
            s = s.strip()
            # Skip very short or nav-like sentences
            if len(s) < 40:
                continue
            if re.search(r'(click here|learn more|see the|check out|read more)', s, re.IGNORECASE):
                continue
            picked.append(s)
            if len(picked) == 3:
                break

        for s in picked:
            lines.append(f"- {s}")
        lines.append("")

    # Code examples
    if code_examples:
        lines += [
            "---",
            "",
            "## Code Examples",
            "",
        ]
        for i, code in enumerate(code_examples, 1):
            lines.append(f"```php")
            lines.append(code)
            lines.append("```")
            lines.append("")

    lines += [
        "---",
        "",
        f"*{date.strftime('%Y-%m-%d')} — Laravel 13.x study notes*",
    ]

    return '\n'.join(lines)


if __name__ == "__main__":
    today = datetime.date.today()
    index, slug, name = get_topic_for_date(today)

    print(f"Topic: {name}  ({BASE_URL}{slug})")
    raw_html = fetch_page(slug)
    digest = build_digest(today, index, slug, name, raw_html)

    output_dir = os.path.join(os.path.dirname(__file__), "..", "laravel-digest")
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, f"{today.isoformat()}.md")

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(digest)

    print(f"Written: {output_path}  ({len(digest)} chars)")
