# sup-agent — o'rnatish, autostart va majburiy tekshiruv

> **Bu yo'riqnoma shu serverdagi AI (agent) uchun.** Ya'ni buni odam emas,
> mana shu kompyuterda ishlayotgan sun'iy intellekt bajaradi. Shuning uchun
> har qadam aniq buyruq bilan yozilgan va oxirida **majburiy tekshiruv** bor:
> autostart haqiqatan qo'yilganini isbotlamasdan ishni tugatgan deb hisoblama.

Vazifa: bu qurilmani markaziy agentga (`https://agi.1pro.uz`) doimiy ulash.
Natijada markaz bu qurilmaga buyruq bera oladi, fayl o'tkazadi va yangilaydi.

---

## 0. Sening majburiyating (AI uchun)

Ishni tugatdim deyishdan oldin **hammasi** bajarilgan bo'lishi shart:

1. `node.py` ishlab turibdi va markazga ulangan.
2. Autostart o'rnatilgan (kompyuter o'chib-yonsa o'zi ishga tushadi).
3. **Qayta yuklab (yoki servisni qayta ishga tushirib) tekshirilgan** — node
   yana o'zi ulandi.
4. Repo `git` kloni (markazdan `update` kelganda o'zini yangilay olishi uchun).
5. Egaga qisqa hisobot: node nomi, id si, OS, autostart turi, tekshiruv natijasi.

Tekshiruvni "ehtimol ishlaydi" deb o'tkazib yuborma. Har bir tekshiruv
buyrug'ini **haqiqatan ishga tushir** va chiqishini ko'r.

---

## 1. Talablar

```bash
python3 --version     # 3.8+ bo'lishi kerak
git --version         # update ishlashi uchun kerak
```

Yo'q bo'lsa avval o'rnat (Linux: `apt install -y python3 git`, macOS: `brew install git`).

## 2. Repo ni klonlash (default repo)

Autostartda yangilanish ishlashi uchun repo **git kloni** bo'lishi shart -
zip emas. Standart joylar: Linux `/opt/sup-agent`, macOS/uy `~/sup-agent`.

```bash
sudo git clone https://github.com/Yaxyobek0877/sup-agent.git /opt/sup-agent
cd /opt/sup-agent
```

## 3. config.json ni yozish

```bash
cp config.example.json config.json
```

`config.json` ni tahrirla:

```json
{
  "hub": "https://agi.1pro.uz",
  "key": "<MARKAZDAN OLINGAN FLEET KALITI>",
  "node_id": "",
  "name": "<shu qurilmaga qulay nom, masalan vps-frankfurt>",
  "projects": []
}
```

- `key` ni egadan so'ra yoki markazda `agent hub key` chiqaradi.
- `node_id` ni bo'sh qoldir — birinchi ishga tushganda o'zi yaratadi.
- `name` — takrorlanmas, aniq nom qo'y.

## 4. Birinchi ulanishni sinash

```bash
python3 node.py --once
```

Kutilgan chiqish: `[sup-agent] <nom> (<id>) -> https://agi.1pro.uz` va xatosiz
tugashi. Xato bo'lsa (`ulanmadi`, `401`, `403`) — `hub` manzili, `key` va
tarmoqni tekshir, davom etma.

---

## 5. Autostart o'rnatish (OS bo'yicha)

### Linux — systemd

`/etc/systemd/system/sup-agent.service`:

```ini
[Unit]
Description=sup-agent (markaziy agent node)
After=network-online.target
Wants=network-online.target

[Service]
Type=simple
WorkingDirectory=/opt/sup-agent
ExecStart=/usr/bin/python3 /opt/sup-agent/node.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now sup-agent
```

### macOS — launchd

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
  <key>StandardErrorPath</key><string>/tmp/supagent.err</string>
  <key>StandardOutPath</key><string>/tmp/supagent.out</string>
</dict></plist>
```

```bash
launchctl load -w ~/Library/LaunchAgents/uz.1pro.supagent.plist
```

### Windows — Task Scheduler

Ma'muriy PowerShell da (yo'lni o'zingnikiga moslashtir):

```powershell
$py = (Get-Command python).Source
schtasks /Create /TN sup-agent /SC ONLOGON /RL HIGHEST /F `
  /TR "`"$py`" C:\sup-agent\node.py"
schtasks /Run /TN sup-agent
```

Kompyuter tarmoqqa ulanmasdan yonsa ham ishlashi uchun `-Restart` mantiqi
`node.py` da bor (o'zi qayta uriladi).

---

## 6. MAJBURIY TEKSHIRUV (autostart haqiqatan ishlaydimi)

Har bir bandni **ishga tushirib** tekshir. Kutilgan natijani ko'rmasang -
autostart noto'g'ri, tuzatmaguncha ish tugamagan.

### 6.1 Servis yoqilgan (boot da ishga tushadimi)

```bash
# Linux
systemctl is-enabled sup-agent      # -> enabled
systemctl is-active sup-agent       # -> active
# macOS
launchctl list | grep supagent      # -> ro'yxatda, PID bilan
# Windows
schtasks /Query /TN sup-agent /V /FO LIST | findstr "Status Scheduled"
```

### 6.2 Jarayon ishlayapti va ulangan

```bash
# Linux/macOS
journalctl -u sup-agent -n 5 --no-pager     # Linux
tail -5 /tmp/supagent.out /tmp/supagent.err  # macOS
```
Logda `-> https://agi.1pro.uz` ko'rinishi va xato bo'lmasligi kerak.

### 6.3 QAYTA YUKLASH SINOVI (eng muhim)

Autostartning yagona haqiqiy isboti — qayta yuklashdan keyin o'zi ulanishi.

```bash
sudo reboot        # yoki servisni qayta ishga tushir: systemctl restart sup-agent
```

Qayta yonganidan ~1 daqiqa keyin 6.1 va 6.2 ni **yana** tekshir. Node yana
`active` va ulangan bo'lishi shart. Haqiqiy reboot imkoni bo'lmasa, hech
bo'lmasa servisni to'liq `stop` qilib, `start` qilib, o'zi ko'tarilishini ko'r.

### 6.4 Markaz tomonidan tasdiqlash (egada)

Ega markazda:

```bash
agent hub nodes                       # bu qurilma "onlayn" ko'rinsin
agent hub run <nom> "echo tekshiruv"  # -> tekshiruv
```

### 6.5 Yangilanish yo'li tayyor

Markazdan `update` kelganda `git pull` ishlashi uchun:

```bash
git -C /opt/sup-agent remote -v       # origin -> .../sup-agent.git
git -C /opt/sup-agent status -sb      # ## main...origin/main, toza
```

---

## 7. Hisobot (ishni tugatganda)

Egaga shu qatorni qaytar:

```
node: <nom> (<id>) · <OS> · autostart: <systemd|launchd|task> ·
tekshiruv: yoqilgan=ha, reboot-sinovi=ha, markazda-onlayn=ha
```

Biror band "yo'q" bo'lsa — sabab bilan yoz va tuzat. Autostart yoki reboot
sinovi tasdiqlanmagan bo'lsa, ish **tugallanmagan** hisoblanadi.
