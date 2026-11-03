"""Собирает курс из course.html: учебник.html (артефакт Claude) и site/index.html (Vercel).

В course.html метки <!--INCLUDE:файл--> заменяются содержимым файла, поэтому код в курсе
всегда совпадает с настоящими shop_app.py, schema.sql и migrate.sql.
Метка <!--RAW:файл--> вставляет файл как есть (для SVG-схемы).
"""
import html
import json
import re
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


def include(match):
    return html.escape((ROOT / match.group(1)).read_text(encoding="utf-8").rstrip("\n"), quote=False)


def include_raw(match):
    return (ROOT / match.group(1)).read_text(encoding="utf-8")


page = (ROOT / "course.html").read_text(encoding="utf-8")
page = re.sub(r"<!--INCLUDE:(.+?)-->", include, page)
page = re.sub(r"<!--RAW:(.+?)-->", include_raw, page)
head_part, body_part = page.split("<!--BODY-->", 1)

(ROOT / "учебник.html").write_text(head_part + body_part, encoding="utf-8")

SITE.mkdir(exist_ok=True)
(SITE / "index.html").write_text(
    HEAD + head_part + "</head>\n<body>" + body_part + "\n</body>\n</html>\n",
    encoding="utf-8",
)
(SITE / "manifest.json").write_text(json.dumps(MANIFEST, ensure_ascii=False, indent=2), encoding="utf-8")
shutil.copy(ROOT / "import" / "Icon.png", SITE / "icon.png")
print("Готово:", SITE / "index.html")
