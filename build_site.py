"""Собирает site/index.html для Vercel из учебник.html (той же страницы, что и артефакт)."""
import json
import shutil
from pathlib import Path

ROOT = Path(__file__).parent
SITE = ROOT / "site"

HEAD = """<!doctype html>
<html lang="ru">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="theme-color" content="#2E8B57">
<link rel="icon" href="icon.png">
<link rel="apple-touch-icon" href="icon.png">
<link rel="manifest" href="manifest.json">
<style>
:root { color-scheme: light; padding-top: env(safe-area-inset-top, 0px); padding-bottom: env(safe-area-inset-bottom, 0px); }
body { margin: 0; font: 14px system-ui, sans-serif; }
img { max-width: 100%; }
[hidden] { display: none !important; }
</style>
"""

MANIFEST = {
    "name": "Демоэкзамен 09.02.07",
    "short_name": "Демоэкзамен",
    "start_url": "/",
    "display": "standalone",
    "background_color": "#F6F8F7",
    "theme_color": "#2E8B57",
    "icons": [{"src": "icon.png", "sizes": "512x512", "type": "image/png"}],
}

page = (ROOT / "учебник.html").read_text(encoding="utf-8")
# Всё до первого <nav> — это title/meta/style страницы, они идут в <head>
head_part, body_part = page.split('<nav class="chips"', 1)

SITE.mkdir(exist_ok=True)
(SITE / "index.html").write_text(
    HEAD + head_part + "</head>\n<body>\n<nav class=\"chips\"" + body_part + "\n</body>\n</html>\n",
    encoding="utf-8",
)
(SITE / "manifest.json").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copy(ROOT / "import" / "Icon.png", SITE / "icon.png")
print("Готово:", SITE / "index.html")
