from __future__ import annotations

import os
import re
import subprocess
import tomllib
import unicodedata
from dataclasses import dataclass
from datetime import date, datetime
from pathlib import Path, PurePosixPath

from bs4 import BeautifulSoup

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "_site"
POSTS_DIR = ROOT / "content" / "posts"
PINNED_LIMIT = 3
RECENT_LIMIT = 5


@dataclass
class SidebarPost:
    source: Path
    title: str
    day: date
    relpath: PurePosixPath
    pinned: bool
    posted_at: int


def slugify(value: str) -> str:
    value = unicodedata.normalize("NFKD", value).encode("ascii", "ignore").decode("ascii")
    value = re.sub(r"[^a-zA-Z0-9]+", "-", value.lower()).strip("-")
    return value or "texto"


def first_commit_timestamp(path: Path) -> int:
    rel = path.relative_to(ROOT).as_posix()
    result = subprocess.run(
        ["git", "log", "--follow", "--format=%ct", "--", rel],
        cwd=ROOT,
        check=True,
        capture_output=True,
        text=True,
    )
    stamps = [int(line) for line in result.stdout.splitlines() if line.strip().isdigit()]
    if stamps:
        return min(stamps)
    return 0


def parse_post(path: Path) -> SidebarPost:
    raw = path.read_text(encoding="utf-8")
    match = re.match(r"\A\+\+\+\s*\n(.*?)\n\+\+\+\s*\n?(.*)\Z", raw, flags=re.S)
    if not match:
        raise ValueError(f"{path}: cabeçalho TOML entre +++ não encontrado")
    meta = tomllib.loads(match.group(1))

    title = str(meta["title"]).strip()
    d = meta["date"]
    if isinstance(d, datetime):
        d = d.date()
    elif isinstance(d, str):
        d = date.fromisoformat(d)
    if not isinstance(d, date):
        raise ValueError(f"{path}: data inválida")

    slug = slugify(str(meta.get("slug", title)))
    relpath = PurePosixPath("archive") / f"{d.year:04d}" / f"{d.month:02d}" / f"{d.day:02d}" / f"{slug}.html"
    pinned = bool(meta.get("pinned", False))
    return SidebarPost(path, title, d, relpath, pinned, first_commit_timestamp(path))


def load_posts() -> list[SidebarPost]:
    posts = []
    for path in sorted(POSTS_DIR.glob("*.md")):
        if path.name.startswith("_") or path.name.lower() == "readme.md":
            continue
        posts.append(parse_post(path))
    return posts


def update_sidebar(posts: list[SidebarPost]) -> None:
    pinned = sorted(
        (p for p in posts if p.pinned),
        key=lambda p: (p.posted_at, p.title.casefold()),
        reverse=True,
    )
    if len(pinned) > PINNED_LIMIT:
        names = ", ".join(p.title for p in pinned)
        raise ValueError(f"Há {len(pinned)} posts com pinned=true; o limite é {PINNED_LIMIT}: {names}")

    pinned_paths = {p.relpath for p in pinned}
    recent = sorted(
        (p for p in posts if p.relpath not in pinned_paths),
        key=lambda p: (p.posted_at, p.title.casefold()),
        reverse=True,
    )[:RECENT_LIMIT]
    selected = pinned + recent

    for path in OUT.rglob("*.html"):
        soup = BeautifulSoup(path.read_text(encoding="utf-8"), "html.parser")
        box = None
        for candidate in soup.select(".rightbar .box"):
            heading = candidate.find("h2")
            if heading and heading.get_text(" ", strip=True) == "Mensagens recentes":
                box = candidate
                break
        if box is None:
            continue

        ul = box.find("ul")
        if ul is None:
            continue
        ul.clear()

        rel = os.path.relpath(OUT, path.parent).replace("\\", "/")
        prefix = "" if rel == "." else rel.rstrip("/") + "/"

        for post in selected:
            li = soup.new_tag("li")
            a = soup.new_tag("a", href=f"{prefix}{post.relpath}")
            a.string = post.title
            li.append(a)
            ul.append(li)

        path.write_text(str(soup), encoding="utf-8")

    print("Mensagens recentes atualizadas:")
    for post in pinned:
        print(f"  [fixado] {post.title}")
    for post in recent:
        print(f"  [recente] {post.title}")


def main() -> int:
    posts = load_posts()
    update_sidebar(posts)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
