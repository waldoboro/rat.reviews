"""
Rat Reviews — Local Blog Publisher
Exports to: Content/[type]/[year]/[MM]/filename.html
Copies CSS, icons, and images from the script directory into each export folder.
"""

import os
import re
import shutil
import datetime
import calendar
import markdown
import tkinter as tk
from tkinter import messagebox, scrolledtext, ttk
from pathlib import Path

SCRIPT_DIR = Path(__file__).parent.resolve()
CONTENT_DIR = SCRIPT_DIR / "Content"
ASSET_EXTENSIONS = {".css", ".ico", ".jpg", ".jpeg", ".png", ".gif", ".webp", ".svg"}

MARKDOWN_HINTS = (
    "Markdown hints:  "
    "**bold**  |  *italic*  |  # H1 / ## H2  |  "
    "[text](url)  |  ![alt](img.jpg)  |  > quote  |  "
    "- list item  |  `code`  |  +++ <br> | ~~strike~~"
)

# ── Review HTML template ────────────────── ##### ──────────────────── ##### ──────────────── ##### ───────────── ##### ────────────────

def generate_html(title, artist, album, release_year, review_type, pub_date, review_html, author):
    current_year = datetime.date.today().year
    return f"""<!DOCTYPE html>
<html>
<head>
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <link rel="shortcut icon" href="favicon.ico">
  <link rel="stylesheet" href="rat.css">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{title} — Rat Reviews</title>
  <link href='https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Blaka&family=DotGothic16&family=Abhaya+Libre&display=swap' rel='stylesheet'>
</head>
<body class="bkg" style="background-image: url(tiles.png)">

<div class="topnav">
  <a href="https://rat.reviews/Recent">Recent</a>
  <a href="https://rat.reviews/Archive">Archive</a>
  <a href="https://rat.reviews/About">About</a>
  <a href="https://rat.reviews" class="split">Home</a>
</div>

<div class="review-header-wrap">
  <div class="review-title-block">
    <h1>{title}</h1>
    <p class="sub">{artist}, <i>{album}</i> ({release_year})</p>
  </div>
</div>

<div class="WordSection1 prg" style="word-wrap:break-word;">
<br>
{review_html}

<div class="review-signature">
  <span class="sig-name">- {author}</span>
  <span class="sig-meta">{pub_date}</span>
</div>

</div>

<footer>
  <div class="footer">
    <p>&copy; Copyright {current_year}, Rat Reviews</p>
  </div>
</footer>
</body>
</html>
"""

# ── Asset copy ─────────────────────────────────────────────────────────────────

def copy_assets_to(dest_dir: Path):
    """Copy all CSS/icon/image assets from the script directory into dest_dir."""
    copied = []
    for item in SCRIPT_DIR.iterdir():
        if item.is_file() and item.suffix.lower() in ASSET_EXTENSIONS:
            target = dest_dir / item.name
            if not target.exists():
                shutil.copy2(item, target)
                copied.append(item.name)
    return copied

# ── Publish ────────────────────────────────────────────────────────────────────

def publish_review():
    title       = title_entry.get().strip()
    artist      = artist_entry.get().strip()
    album       = album_entry.get().strip()
    release_year = year_entry.get().strip()
    review_type = type_entry.get().strip() or "General"
    author      = author_entry.get().strip() or "Ape"
    content     = review_text.get("1.0", tk.END).strip()

    if not title or not album:
        messagebox.showerror("Error", "Title and Album are required.")
        return

    # ── Resolve publish date ───────────────────────────────────────────────
    if override_date_var.get():
        raw = date_entry.get().strip()
        try:
            pub_date = datetime.datetime.strptime(raw, "%Y-%m-%d").date()
        except ValueError:
            messagebox.showerror("Date Error", "Date must be YYYY-MM-DD format.")
            return
    else:
        pub_date = datetime.date.today()

    year_str  = str(pub_date.year)
    month_str = f"{pub_date.month:02d}"

    # ── Build output path: Content/[type]/[year]/[MM]/ ──────────────────────
    safe_type = re.sub(r'[^\w\-]', '_', review_type)
    out_dir   = CONTENT_DIR / safe_type / year_str / month_str
    out_dir.mkdir(parents=True, exist_ok=True)

    filename  = re.sub(r'[^\w\-]', '', album.replace(" ", "")) + ".html"
    filepath  = out_dir / filename
    rel_path = str((out_dir / filename).relative_to(SCRIPT_DIR)).replace("\\", "/")

    # ── Render markdown ────────────────────────────────────────────────────
    # nl2br turns single newlines into <br> so paragraph breaks are preserved
    rendered = markdown.markdown(content, extensions=["extra", "nl2br"])
    rendered = rendered.replace("<p>", '<p class="MsoNormal">')
    # Add <br> when +++ is entered
    content = content.replace('\n+++\n', '\n<br>\n')
    rendered = markdown.markdown(content, extensions=["extra", "nl2br"])
    # Use <i>/<b> instead of semantic <em>/<strong> to match site style
    rendered = rendered.replace("<em>", "<i>").replace("</em>", "</i>")
    rendered = rendered.replace("<strong>", "<b>").replace("</strong>", "</b>")

    # ── Metadata comment block ─────────────────────────────────────────────
    metadata = f"""<!--
TITLE: {title}
ARTIST: {artist}
ALBUM: {album}
YEAR: {release_year}
TYPE: {review_type}
AUTHOR: {author}
DATE: {pub_date}
-->
"""
    full_html = metadata + generate_html(
        title, artist, album, release_year,
        review_type, str(pub_date), rendered, author
    )

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(full_html)

    # ── Copy assets ────────────────────────────────────────────────────────
    copied = copy_assets_to(out_dir)

    update_archive()
    update_recent(title, artist, album, release_year, review_type, pub_date, author, rel_path)

    asset_msg = f"\nAssets copied: {', '.join(copied)}" if copied else "\n(No new assets to copy)"
    messagebox.showinfo(
        "Published!",
        f"✓ {filename}\n→ {out_dir.relative_to(SCRIPT_DIR)}{asset_msg}"
    )

# ── Archive builder ────────────────── ##### ──────────────────── ##### ──────────────── ##### ───────────── ##### ────────────────

def update_archive():
    current_year = datetime.date.today().year
    entries = []

    for html_file in CONTENT_DIR.rglob("*.html"):
        try:
            text = html_file.read_text(encoding="utf-8")
        except Exception:
            continue

        if "<!--" not in text:
            continue

        meta_block = text.split("<!--")[1].split("-->")[0]
        meta = {}
        for line in meta_block.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()

        if "DATE" not in meta:
            continue

        try:
            date_obj = datetime.datetime.strptime(meta["DATE"], "%Y-%m-%d")
        except ValueError:
            continue

        rel_path = html_file.relative_to(SCRIPT_DIR).as_posix()
        entries.append({
            "path":   rel_path,
            "type":   meta.get("TYPE", "General"),
            "artist": meta.get("ARTIST", ""),
            "album":  meta.get("ALBUM", ""),
            "year":   meta.get("YEAR", ""),
            "date":   date_obj,
        })

    entries.sort(key=lambda x: x["date"], reverse=True)

    # Group by year → month
    grouped: dict = {}
    for e in entries:
        y = e["date"].year
        m = e["date"].month
        grouped.setdefault(y, {}).setdefault(m, []).append(e)

    archive_body = ""
    for y in sorted(grouped, reverse=True):
        archive_body += f"\n<h2>{y}</h2>\n"
        for m in sorted(grouped[y], reverse=True):
            month_name = calendar.month_name[m]
            archive_body += f'<h3 style="padding: 0 4%">{month_name}</h3>\n<ul class="a">\n'
            for e in grouped[y][m]:
                archive_body += (
                    f'<li><a class="list" href="{e["path"]}">'
                    f'[<span style="color:#02ab6d;">{e["type"]}</span>] <i>{e["album"]} - {e["artist"]}</i> ({e["year"]})'
                    f'</a></li>\n'
                )
            archive_body += "</ul>\n"

    full_archive = f"""<!DOCTYPE html>
<html>
<head>
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <link rel="shortcut icon" href="favicon.ico">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="stylesheet" href="rat.css">
  <title>Rat Reviews ⊚ Archive</title>
  <link href='https://fonts.googleapis.com/css2?family=Bebas+Neue&family=Blaka&family=DotGothic16&family=Abhaya+Libre&display=swap' rel='stylesheet'>
  <style>
    ul.a {{ list-style-type: circle; padding: 0 8%; }}
    .list {{ color: black; font-size: 1em; text-decoration: none; }}
  </style>
</head>
<body class="bkg">
<div class="topnav">
  <a class="active" href="https://rat.reviews/Recent">Reviews</a>
  <a href="https://rat.reviews/About">About</a>
  <a href="https://rat.reviews/Contact">Contact</a>
  <a href="https://rat.reviews" class="split">Home</a>
</div>
<div class="prg" style="font-size:1em; text-align:left;">
{archive_body}
</div>
<footer><div class="footer"><p>&copy; Copyright {current_year}, Rat Reviews</p></div></footer>
</body>
</html>
"""

    archive_path = SCRIPT_DIR / "Archive.html"
    with open(archive_path, "w", encoding="utf-8") as f:
        f.write(full_archive)

#### ── Recent Builder ────────────────── ##### ──────────────────── ##### ──────────────── ##### ───────────── ##### ────────────────

MAX_RECENT = 13  # how many entries to keep before dropping the oldest

def update_recent(title, artist, album, release_year, review_type, pub_date, author, rel_path):
    recent_path = SCRIPT_DIR / "Recent.html"
    current_year = datetime.date.today().year

    # ── Read all entries from metadata comments in Content/ ───────────────
    entries = []
    for html_file in CONTENT_DIR.rglob("*.html"):
        try:
            text = html_file.read_text(encoding="utf-8")
        except Exception:
            continue
        if "<!--" not in text:
            continue
        meta_block = text.split("<!--")[1].split("-->")[0]
        meta = {}
        for line in meta_block.strip().splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        if "DATE" not in meta or "ALBUM" not in meta:
            continue
        try:
            date_obj = datetime.datetime.strptime(meta["DATE"], "%Y-%m-%d").date()
        except ValueError:
            continue
        file_rel = str(html_file.relative_to(SCRIPT_DIR)).replace("\\", "/")
        entries.append({
            "href":       f"/{file_rel}",
            "type":       meta.get("TYPE", "General"),
            "date":       date_obj,
            "date_str":   f"{date_obj.day}.{date_obj.month}.{date_obj.year}",
            "author":     meta.get("AUTHOR", ""),
            "bold":       f"{meta.get('ALBUM','')} - {meta.get('ARTIST','')} ({meta.get('YEAR','')})",
            "link_title": meta.get("TITLE", ""),
        })

    # ── Sort newest first, keep only MAX_RECENT ───────────────────────────
    entries.sort(key=lambda x: x["date"], reverse=True)
    entries = entries[:MAX_RECENT]

    # ── Render entry blocks ────────────────────────────────────────────────
    def render_entry(e):
        return (
            f'  <a class="link" href="{e["href"]}">\n'
            f'    <i style="font-size: 0.7em;">{e["type"]} | {e["date_str"]} | {e["author"]}<br>\n'
            f'    <b>{e["bold"]}</b></i> <br>\n'
            f'    {e["link_title"]}</a>\n'
        )

    entries_html = "\n".join(render_entry(e) for e in entries)

    full_html = f"""<!DOCTYPE html>
<html>
<head>
  <link rel="icon" type="image/x-icon" href="favicon.ico">
  <link rel="shortcut icon" href="favicon.ico">
  <link rel="stylesheet" href="rat.css">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Rat Reviews</title>
  <link href='https://fonts.googleapis.com/css?family=Blaka|DotGothic16|Abhaya+Libre' rel='stylesheet'>
</head>
<body class="bkg">

<div class="topnav">
  <a href="https://rat.reviews/Archive">Archive</a>
  <a href="https://rat.reviews/About">About</a>
  <a href="https://rat.reviews/Contact">Contact</a>
  <a href="https://rat.reviews" class="split">Home</a>
</div>

<p class="prg">

{entries_html}
</p>

</body>
<footer><div class="footer">
  <p>&copy; Copyright {current_year}, Rat Reviews</p>
</div></footer>
</html>
"""
    with open(recent_path, "w", encoding="utf-8") as f:
        f.write(full_html)

# ── GUI ────────────────────────────────────────────────────────────────────────

BG       = "#1a1a1a"
BG2      = "#2a2a2a"
FG       = "#f5f0e8"
ACCENT   = "#FFE500"
BORDER   = "#444444"
FONT     = ("Courier New", 10)
FONT_LG  = ("Courier New", 11, "bold")

root = tk.Tk()
root.title("Rat Reviews — Publisher")
root.configure(bg=BG)
root.resizable(True, True)
root.minsize(700, 700)

# ── helper to make a labeled row ──────────────────────────────────────────────
def labeled_entry(parent, label_text, width=52):
    row = tk.Frame(parent, bg=BG)
    row.pack(fill="x", padx=20, pady=(8, 0))
    tk.Label(row, text=label_text, bg=BG, fg=ACCENT, font=FONT_LG, anchor="w").pack(fill="x")
    e = tk.Entry(row, width=width, bg=BG2, fg=FG, insertbackground=FG,
                 font=FONT, relief="flat", highlightthickness=1,
                 highlightbackground=BORDER, highlightcolor=ACCENT)
    e.pack(fill="x", ipady=4)
    return e

# ── Title block ────────────────────────────────────────────────────────────────
header = tk.Frame(root, bg=ACCENT, pady=10)
header.pack(fill="x")
tk.Label(header, text="RAT REVIEWS  //  PUBLISHER",
         bg=ACCENT, fg=BG, font=("Courier New", 13, "bold")).pack()

# ── Collapsible metadata section ──────────────────────────────────────────────
meta_visible = tk.BooleanVar(value=True)
meta_frame = tk.Frame(root, bg=BG)

def toggle_meta():
    if meta_visible.get():
        meta_frame.pack_forget()
        meta_toggle_btn.config(text="▶  REVIEW DETAILS")
        meta_visible.set(False)
    else:
        # Re-pack BEFORE the hints/text area
        meta_frame.pack(fill="x", after=meta_toggle_btn)
        meta_toggle_btn.config(text="▼  REVIEW DETAILS")
        meta_visible.set(True)

meta_toggle_btn = tk.Button(
    root, text="▼  REVIEW DETAILS",
    command=toggle_meta,
    bg=BG2, fg=ACCENT,
    font=FONT_LG, relief="flat",
    cursor="hand2", anchor="w",
    padx=20, pady=6,
    activebackground=BORDER, activeforeground=ACCENT
)
meta_toggle_btn.pack(fill="x", padx=20, pady=(10, 0))
meta_frame.pack(fill="x")

# ── Fields ─────────────────────────────────────────────────────────────────────
title_entry  = labeled_entry(meta_frame, "Review Title")
artist_entry = labeled_entry(meta_frame, "Artist")
album_entry  = labeled_entry(meta_frame, "Album")
year_entry   = labeled_entry(meta_frame, "Release Year", width=12)
type_entry   = labeled_entry(meta_frame, "Review Type  (e.g. Albums, Tracks, Essays — sets export folder)", width=30)
author_entry = labeled_entry(meta_frame, "Author  (signature shown on page)", width=30)

# ── Date override ──────────────────────────────────────────────────────────────
date_frame = tk.Frame(meta_frame, bg=BG)
date_frame.pack(fill="x", padx=20, pady=(10, 0))

override_date_var = tk.BooleanVar(value=False)

def toggle_date_entry():
    if override_date_var.get():
        date_entry.configure(state="normal", highlightbackground=ACCENT)
        date_entry.delete(0, tk.END)
        date_entry.insert(0, datetime.date.today().isoformat())
    else:
        date_entry.configure(state="disabled", highlightbackground=BORDER)

chk = tk.Checkbutton(
    date_frame, text="Override publish date",
    variable=override_date_var, command=toggle_date_entry,
    bg=BG, fg=FG, selectcolor=BG2, activebackground=BG,
    activeforeground=ACCENT, font=FONT_LG
)
chk.pack(side="left")

date_entry = tk.Entry(
    date_frame, width=14, bg=BG2, fg=FG,
    insertbackground=FG, font=FONT, relief="flat",
    highlightthickness=1, highlightbackground=BORDER,
    highlightcolor=ACCENT, state="disabled"
)
date_entry.pack(side="left", padx=(10, 0), ipady=4)
tk.Label(date_frame, text="YYYY-MM-DD", bg=BG, fg="#777777", font=("Courier New", 9)).pack(side="left", padx=6)

# ── Markdown hints ─────────────────────────────────────────────────────────────
hints_frame = tk.Frame(root, bg="#222222", pady=6, padx=12)
hints_frame.pack(fill="x", padx=20, pady=(12, 0))
tk.Label(hints_frame, text="📝 " + MARKDOWN_HINTS,
         bg="#222222", fg="#aaaaaa", font=("Courier New", 8),
         wraplength=640, justify="left", anchor="w").pack(fill="x")

# ── Review text area ───────────────────────────────────────────────────────────
text_frame = tk.Frame(root, bg=BG)
text_frame.pack(fill="both", expand=True, padx=20, pady=(6, 0))
tk.Label(text_frame, text="Review Body (Markdown)", bg=BG, fg=ACCENT, font=FONT_LG, anchor="w").pack(fill="x")
review_text = scrolledtext.ScrolledText(
    text_frame, width=80, height=18,
    bg=BG2, fg=FG, insertbackground=FG,
    font=("Courier New", 10), relief="flat",
    highlightthickness=1, highlightbackground=BORDER,
    highlightcolor=ACCENT, wrap="word"
)
review_text.pack(fill="both", expand=True)

# ── Publish button ─────────────────────────────────────────────────────────────
btn_frame = tk.Frame(root, bg=BG)
btn_frame.pack(fill="x", padx=20, pady=14)

publish_btn = tk.Button(
    btn_frame, text="▶  PUBLISH",
    command=publish_review,
    bg=ACCENT, fg=BG,
    font=("Courier New", 12, "bold"),
    relief="flat", cursor="hand2",
    padx=24, pady=8,
    activebackground="#ccb800", activeforeground=BG
)
publish_btn.pack(side="right")

tk.Label(btn_frame,
         text=f"Exports to: Content/[type]/[year]/[MM]/album.html\nAssets copied from: {SCRIPT_DIR.name}/",
         bg=BG, fg="#666666", font=("Courier New", 8), justify="left").pack(side="left")

def clear_fields():
    title_entry.delete(0, tk.END)
    artist_entry.delete(0, tk.END)
    album_entry.delete(0, tk.END)
    year_entry.delete(0, tk.END)
    type_entry.delete(0, tk.END)
    author_entry.delete(0, tk.END)
    review_text.delete("1.0", tk.END)
    override_date_var.set(False)
    toggle_date_entry()

clear_btn = tk.Button(
    btn_frame, text="✕  CLEAR",
    command=clear_fields,
    bg=BG2, fg=FG,
    font=("Courier New", 12, "bold"),
    relief="flat", cursor="hand2",
    padx=24, pady=8,
    activebackground=BORDER, activeforeground=FG
)
clear_btn.pack(side="right", padx=(0, 10))

root.mainloop()
