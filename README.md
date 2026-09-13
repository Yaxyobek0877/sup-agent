# sup-agent

Markaziy agentga ulanadigan **qurilma agenti**. Uni makbuk, VPS yoki istalgan
serverga qo'yasiz - u markazga o'zi ulanadi va markazdan kelgan buyruqlarni
bajaradi: shell buyruq, fayl olish/berish, o'zini yangilash.

- **Faqat standart kutubxona.** Hech narsa `pip install` qilinmaydi. Python 3.8+ yetadi.
- **Port ochilmaydi.** Qurilma markazga o'zi chiqadi (long-poll), shuning uchun
  NAT yoki fayervol orqasida ham ishlaydi.
- **Sir gitga tushmaydi.** Fleet kaliti faqat `config.json` da (u `.gitignore` da).

```
   makbuk ─┐
   server ─┼──►  MARKAZ (agi.1pro.uz)  ◄── siz: agent hub run / cp / update
   vps    ─┘
```

## O'rnatish

**Bir buyruqli o'rnatish** (Linux/macOS, root systemd) — config, autostart va
majburiy tekshiruvni o'zi qiladi. Kalit o'rniga qisqa umrli **enroll (sessiya)
tokeni** ishlatiladi: node o'zini ro'yxatga olib doimiy kalitni oladi.

```bash
sudo git clone https://github.com/Yaxyobek0877/sup-agent.git /opt/sup-agent
cd /opt/sup-agent
export SUP_ENROLL='<markazda: agent hub enroll>'   # qisqa umrli token
sudo -E bash install.sh
```

`install.sh`: `setup_config.py` (token/kalit muhitdan, `chmod 600`) →
`node.py --once` (kalit yo'q bo'lsa **o'zini ro'yxatga oladi**) → tizim systemd
(`Restart=always` + boot) → o'zini-ko'tarish sinovi (**reboot emas**) →
sir-himoya tekshiruvi → hisobot. Idempotent.

Markazda token oling: **`agent hub enroll`**. Doimiy kalit kerak bo'lsa
`SUP_FLEET_KEY='<agent hub key>'` ham ishlaydi. Qo'lda/dev:
`cp config.example.json config.json && SUP_ENROLL=... python3 setup_config.py`
so'ng `python3 node.py`.

> **Qurilmani AI sozlasa (30+ server uchun)** — o'rnatishni har serverdagi
> Claude Code ga topshiring: **[docs/OPERATOR-PROMPT.md](docs/OPERATOR-PROMPT.md)**.
> Repoda `.claude/settings.json` (o'rnatish so'rovsiz, xavfli buyruq bloklangan)
> va `CLAUDE.md` (buzilmas qoidalar) borligi uchun bu **bypass rejimida ham
> xavfsiz**.

`config.json`:

| kalit | ma'nosi |
|-------|---------|
| `hub` | markaz manzili, masalan `https://agi.1pro.uz` yoki `http://192.168.1.10:8765` |
| `enroll` | sessiya tokeni (`agent hub enroll`) — `key` o'rniga; node ro'yxatdan o'tib doimiy kalitni oladi, so'ng bu maydon o'chadi |
| `key` | fleet kaliti (`agent hub key`) — `enroll` ishlatilsa avtomatik to'ladi |
| `node_id` | bo'sh qoldiring - o'zi yaratadi va yozib qo'yadi |
| `name` | qulay nom, masalan `makbuk`, `vps-1` |
| `shell` | `null` (OS standarti) yoki masalan `/bin/bash` |
| `projects` | shu qurilmadagi loyihalar `[{ "name": ..., "path": ... }]` |

## Doim ishlab turishi (autostart)

> To'liq yo'riqnoma — **[docs/O'RNATISH.md](docs/O'RNATISH.md)**. U shu
> serverdagi AI uchun yozilgan: bosqichma-bosqich o'rnatish va **majburiy
> tekshiruv** (qayta yuklashdan keyin ham o'zi ulanishini isbotlash). Qurilmani
> AI sozlayotgan bo'lsa — o'sha faylni to'liq bajarsin va hisobot qaytarsin.

Qisqacha:

### macOS (launchd)

`~/Library/LaunchAgents/uz.1pro.supagent.plist`:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
 "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0"><dict>
  <key>Label</key><string>uz.1pro.supagent</string>
  <key>ProgramArguments</key>
  <array>
    <string>/usr/bin/python3</string>
    <string>/Users/SIZ/sup-agent/node.py</string>
  </array>
  <key>RunAtLoad</key><true/>
  <key>KeepAlive</key><true/>
</dict></plist>
```

```bash
launchctl load ~/Library/LaunchAgents/uz.1pro.supagent.plist
```

### Linux (systemd)

`/etc/systemd/system/sup-agent.service`:

```ini
[Unit]
Description=sup-agent
After=network-online.target

[Service]
ExecStart=/usr/bin/python3 /opt/sup-agent/node.py
WorkingDirectory=/opt/sup-agent
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl enable --now sup-agent
```

### Windows (Task Scheduler)

```powershell
schtasks /Create /SC ONLOGON /TN sup-agent /TR "python C:\sup-agent\node.py" /RL HIGHEST
```

## Markazdan boshqarish

Markaz kompyuterida (`agent` repo):

```bash
agent hub nodes                       # ulangan qurilmalar
agent hub run makbuk "uname -a"       # qurilmada buyruq
agent hub cp makbuk:~/x.zip vps:/srv/x.zip   # fayl o'tkazish
agent hub cp makbuk:~/x.zip tg:me      # Telegramga yuborish
agent hub update all                   # hammani GitHubdan yangilash
agent hub block makbuk                 # qurilmani vaqtincha to'xtatish
```

## Xavfsizlik

- Markaz qurilmaga **shell buyruq yuboradi va u bajariladi** - bu ataylab
  shunday (fleet boshqaruvi, Ansible kabi). Faqat fleet kalitini biladigan
  markaz buyura oladi.
- **Buyruq imzosi (HMAC):** node faqat markaz imzolagan buyruqni bajaradi.
  Imzo kaliti (`sign_key`) markaz va node da bo'ladi, vositachi Worker da
  **hech qachon** — shuning uchun sizib chiqqan fleet kaliti yoki buzilgan
  edge buyruq soxtalashtira olmaydi. Imzosiz/muddati o'tgan/takror buyruq rad
  etiladi.
- **Sir himoyasi:** `config.json` (fleet + imzo kaliti) `.gitignore` da va
  ruxsati `600` bo'lishi kerak. `python3 setup_config.py` kalitni muhitdan
  oladi — qiymati chatga/faylga matn qilib yozilmaydi.
- Kalit tarqalsa: markazda yangisini yarating (`.fleet-key` faylini o'chirib
  serverni qayta ishga tushiring) va har qurilma `config.json` ini yangilang.
- Bitta qurilmani kalitni almashtirmasdan to'xtatish: `agent hub block <nom>`.
- `hub` manzilini `https://` qiling (domen orqali) - yo'lda buyruq va fayllar
  shifrlanadi. Ochiq tarmoqda `http://` ishlatmang.
- **AI o'rnatsa:** repoda `CLAUDE.md` (buzilmas qoidalar — sirni oshkor
  qilmaslik, reboot/firewall/boshqa xizmatga tegmaslik) va `.claude/settings.json`
  (o'rnatish so'rovsiz, halokatli buyruqlar `deny`) bor. Shuning uchun avtomatik
  (bypass) o'rnatishda ham xavfsizlik qoidalari buzilmaydi.

## O'zini yangilash

`agent hub update <nom>` yuborilganda qurilma `git pull` qiladi va o'zini qayta
ishga tushiradi. Shuning uchun o'zgarishlarni shu repога push qilsangiz -
markazdan bitta buyruq bilan hamma qurilma yangilanadi.
