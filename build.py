#!/usr/bin/env python3
"""Builds fellowhaven.com's static pages.

The privacy policy, terms and delete-account text are written in Markdown
in the app repo (fellowhaven-app/docs/legal) and copied into content/.
To update them:  python3 build.py [path/to/docs/legal]
"""
import html
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).parent
CONTENT = ROOT / "content"
EMAIL = "office@theospreparation.com"


def inline(text):
    text = html.escape(text, quote=False)
    text = re.sub(r"\*\*(.+?)\*\*", r"<strong>\1</strong>", text)
    links = []

    def keep(m):
        links.append(f'<a href="{m.group(2)}">{m.group(1)}</a>')
        return f"\0{len(links) - 1}\0"

    text = re.sub(r"\[([^\]]+)\]\(([^)]+)\)", keep, text)
    text = re.sub(r"https://[^\s<)]+[^\s<).,]", lambda m: f'<a href="{m.group(0)}">{m.group(0)}</a>', text)
    text = re.sub(r"(?<![\w.@/])[\w.+-]+@[\w-]+\.[\w.]+[a-z]", lambda m: f'<a href="mailto:{m.group(0)}">{m.group(0)}</a>', text)
    return re.sub(r"\0(\d+)\0", lambda m: links[int(m.group(1))], text)


def markdown(source):
    out, para, items, kind = [], [], [], None

    def flush():
        nonlocal para, items, kind
        if para:
            out.append("<p>" + "<br>\n".join(inline(l) for l in para) + "</p>")
        if items:
            out.append(f"<{kind}>" + "".join(f"<li>{inline(i)}</li>" for i in items) + f"</{kind}>")
        para, items, kind = [], [], None

    for line in source.splitlines():
        line = line.rstrip()
        if not line:
            flush()
        elif m := re.match(r"(#{1,3}) (.*)", line):
            flush()
            n = len(m.group(1))
            out.append(f"<h{n}>{inline(m.group(2))}</h{n}>")
        elif m := re.match(r"(- |\d+\. )(.*)", line):
            if para:
                flush()
            kind = "ul" if m.group(1) == "- " else "ol"
            items.append(m.group(2))
        else:
            para.append(line)
    flush()
    return "\n".join(out)


def page(title, description, body, home=False):
    bar = "" if home else (
        '<header class="bar"><a href="/"><img src="/assets/mark-white.png" alt="" width="40" height="32">'
        "FellowHaven</a></header>\n"
    )
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<meta name="description" content="{description}">
<meta name="theme-color" content="#1F3A5F">
<link rel="icon" href="/assets/favicon.png" type="image/png">
<link rel="apple-touch-icon" href="/assets/apple-touch-icon.png">
<link rel="stylesheet" href="/assets/site.css">
</head>
<body>
<a class="skip" href="#main">Skip to content</a>
{bar}{body}
<footer>
<nav aria-label="Site"><a href="/">Home</a><a href="/privacy">Privacy Policy</a><a href="/terms">Terms of Use</a><a href="/delete-account">Delete your account</a></nav>
<div>&copy; 2026 Theos Preparation LLC &middot; Cincinnati, Ohio &middot; <a href="mailto:{EMAIL}">{EMAIL}</a></div>
</footer>
</body>
</html>
"""


HOME = f"""<header class="hero">
<img src="/assets/logo-words-white.png" alt="FellowHaven" width="720" height="537">
<div class="byline"><img src="/assets/theos-logo.png" alt="Theos Preparation logo" width="132" height="132"><span>Brought to you by Theos Preparation</span></div>
<p class="tagline">Churches helping churches</p>
<h1>Welcome to FellowHaven</h1>
<p class="intro">Churches were never meant to stand alone. FellowHaven connects the churches of your city so they can share what they have and help carry what others need, whether that's chairs for an outreach, volunteers for a food drive, or a van for youth camp.</p>
</header>
<main id="main">
<h2 class="section-title">How it works</h2>
<ol class="steps">
<li><h3>Post a need</h3><p>Tell other churches what you need, like chairs, volunteers, a musician or a van, and by when.</p></li>
<li><h3>Other churches respond</h3><p>Churches nearby see your need on the Needs Board and send a short response offering to help.</p></li>
<li><h3>You connect directly</h3><p>You get each other's contact info and work out the details together, by email or phone.</p></li>
</ol>
<p class="closing">Post a need, offer a hand, and watch the churches of your city work together as one family. It's free, and it's built for churches.</p>
<section class="soon">
<h2>Coming soon to iPhone and Android</h2>
<p>Connect with local churches in your city.</p>
</section>
<p class="contact">Questions? Email us at <a href="mailto:{EMAIL}">{EMAIL}</a></p>
</main>"""

PAGES = {
    "privacy": ("Privacy Policy", "How FellowHaven handles your church's information."),
    "terms": ("Terms of Use", "The rules for using FellowHaven."),
    "delete-account": ("Delete your account", "How to delete your FellowHaven account and what it removes."),
}


def main():
    if len(sys.argv) > 1:
        for name in PAGES:
            shutil.copy(Path(sys.argv[1]) / f"{name}.md", CONTENT / f"{name}.md")
    (ROOT / "index.html").write_text(page(
        "FellowHaven · Churches helping churches",
        "FellowHaven connects the churches of your city so they can share what they have and help carry what others need.",
        HOME, home=True))
    for name, (title, description) in PAGES.items():
        body = markdown((CONTENT / f"{name}.md").read_text())
        (ROOT / f"{name}.html").write_text(page(
            f"{title} · FellowHaven", description,
            f'<main id="main" class="doc">\n{body}\n</main>'))
    (ROOT / "404.html").write_text(page(
        "Page not found · FellowHaven", "Page not found.",
        '<main id="main" class="doc"><h1>Page not found</h1><p>That page isn\'t here. <a href="/">Go to the FellowHaven home page</a>.</p></main>'))
    print("built", ", ".join(["index"] + list(PAGES) + ["404"]))


main()
