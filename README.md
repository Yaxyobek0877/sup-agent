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
   server ─┼──►  MARKAZ (agent.1pro.uz)  ◄── siz: agent hub run / cp / update
   vps    ─┘
```

## O'rnatish

```bash
git clone https://github.com/Yaxyobek0877/sup-agent.git
cd sup-agent
cp config.example.json config.json
# config.json ni tahrirlang: markaz manzili va fleet kaliti
python3 node.py
```

Fleet kalitini markazda oling:

```bash
agent hub key
```

`config.json`:

| kalit | ma'nosi |
|-------|---------|
| `hub` | markaz manzili, masalan `https://agent.1pro.uz` yoki `http://192.168.1.10:8765` |
| `key` | fleet kaliti (markazdan) |
| `node_id` | bo'sh qoldiring - o'zi yaratadi va yozib qo'yadi |
| `name` | qulay nom, masalan `makbuk`, `vps-1` |
| `shell` | `null` (OS standarti) yoki masalan `/bin/bash` |
| `projects` | shu qurilmadagi loyihalar `[{ "name": ..., "path": ... }]` |

## Doim ishlab turishi

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
- Kalit tarqalsa: markazda yangisini yarating (`.fleet-key` faylini o'chirib
  serverni qayta ishga tushiring) va har qurilma `config.json` ini yangilang.
- Bitta qurilmani kalitni almashtirmasdan to'xtatish: `agent hub block <nom>`.
- `hub` manzilini `https://` qiling (domen orqali) - yo'lda buyruq va fayllar
  shifrlanadi. Ochiq tarmoqda `http://` ishlatmang.

## O'zini yangilash

`agent hub update <nom>` yuborilganda qurilma `git pull` qiladi va o'zini qayta
ishga tushiradi. Shuning uchun o'zgarishlarni shu repога push qilsangiz -
markazdan bitta buyruq bilan hamma qurilma yangilanadi.
