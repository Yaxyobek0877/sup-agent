#!/usr/bin/env python3
"""config.json ni xavfsiz to'ldiradi — fleet kaliti muhit o'zgaruvchisidan.

Nega shunday: o'rnatishni AI (Claude Code) avtomatik bajarsa ham, fleet
kaliti uning suhbatiga/jurnaliga TUSHMASLIGI kerak. Shuning uchun kalit
matn sifatida yozilmaydi — ega uni muhitga export qiladi, bu skript
o'sha yerdan oladi va faylga yozadi. Skript kalit QIYMATINI hech qachon
chop etmaydi.

Ega (o'rnatishdan oldin, AI ni ishga tushiradigan shellda):
    export SUP_FLEET_KEY='<markazdan: agent hub key>'
    export SUP_NODE_NAME='vps-frankfurt'      # ixtiyoriy
    export SUP_HUB='https://agi.1pro.uz'      # ixtiyoriy (standart shu)

Keyin:
    python3 setup_config.py
"""
import json
import os
import stat
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
EXAMPLE = HERE / "config.example.json"


def main() -> None:
    key = os.environ.get("SUP_FLEET_KEY", "").strip()
    if not key:
        sys.exit(
            "SUP_FLEET_KEY topilmadi. Ega o'rnatishdan oldin export qilishi "
            "kerak:\n    export SUP_FLEET_KEY='<markazda: agent hub key>'\n"
            "Kalitni bu yerga matn sifatida yozma — muhit orqali ber.")

    # Namunadan boshlaymiz (bor bo'lsa), yo'q bo'lsa bo'sh andozadan.
    if CONFIG.exists():
        cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    elif EXAMPLE.exists():
        cfg = json.loads(EXAMPLE.read_text(encoding="utf-8"))
    else:
        cfg = {"hub": "", "key": "", "node_id": "", "name": "",
               "shell": None, "projects": []}

    cfg["key"] = key
    cfg["hub"] = os.environ.get("SUP_HUB", "").strip() or cfg.get("hub") \
        or "https://agi.1pro.uz"
    name = os.environ.get("SUP_NODE_NAME", "").strip()
    if name:
        cfg["name"] = name
    cfg.setdefault("node_id", "")          # bo'sh — node.py o'zi yaratadi
    cfg.setdefault("projects", [])

    if not cfg["hub"].startswith("https://"):
        sys.exit(f"'hub' https:// bo'lishi shart, hozir: {cfg['hub']!r}")

    CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                      encoding="utf-8")

    # Sir fayl — faqat ega o'qiy olsin (POSIX). Windows da bu satr ta'sirsiz.
    try:
        os.chmod(CONFIG, stat.S_IRUSR | stat.S_IWUSR)  # 0600
    except OSError:
        pass

    # DIQQAT: kalit qiymati chop etilmaydi.
    print(f"config.json to'ldirildi: hub={cfg['hub']} name={cfg.get('name','')} "
          f"(kalit yashirin, ruxsat 600)")


if __name__ == "__main__":
    main()
