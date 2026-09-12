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
3. **O'zini ko'tarish tekshirilgan** — jarayonni majburan o'ldirganда
   `Restart=always` uni qayta ko'taradi va yuklanishga yoqilgan (6.3). Ishlab
   turgan serverda REBOOT qilma.
4. Repo `git` kloni (markazdan `update` kelganda o'zini yangilay olishi uchun).
5. Egaga qisqa hisobot: node nomi, id si, OS, autostart turi, tekshiruv natijasi.

Tekshiruvni "ehtimol ishlaydi" deb o'tkazib yuborma. Har bir tekshiruv
buyrug'ini **haqiqatan ishga tushir** va chiqishini ko'r.

> 🚫 **Buzilmas qoidalar** ([CLAUDE.md](../CLAUDE.md) da to'liq): sirni
> (`config.json`) oshkor qilma; faqat sup-agent ishini qil, boshqa xizmatga
> tegma; **reboot/shutdown qilma**; firewall/xavfsizlik sozlamalariga tegma;
> tizim yo'llarida `rm -rf`, `mkfs`, `dd` ishlatma. Bularni **avtomatik
> (bypass) rejimida ham** buzma.

### Avtomatik (bypass) rejimi

Ega seni ruxsat so'ramaydigan rejimda ishga tushirishi mumkin. Bu holatda ham
ikki himoya ishlaydi: `.claude/settings.json` — o'rnatish buyruqlari so'rovsiz
o'tadi, halokatli buyruqlar (`deny`) **bloklangan**; va shu qoidalar. Tez
ishla, ammo yuqoridagi qizil chiziqlarni kesma. Batafsil operator ko'rsatmasi:
[OPERATOR-PROMPT.md](OPERATOR-PROMPT.md).

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

## 3. config.json ni yozish (kalit muhit orqali — sir tushmasin)

`config.json` da **fleet kaliti** bo'ladi — bu sir. Uni matn sifatida bu
yerga yozib, chatga/jurnalga/commitga tushirmaslik uchun kalitni **muhit
o'zgaruvchisidan** olamiz. Ega (seni ishga tushirgan odam) uni oldindan
export qilib qo'ygan bo'lishi kerak:

```bash
export SUP_FLEET_KEY='<markazda: agent hub key>'   # ega beradi
export SUP_NODE_NAME='vps-frankfurt'               # takrorlanmas nom
```

Keyin config ni yordamchi skript to'ldiradi (kalit qiymatini ko'rsatmaydi,
faylni `chmod 600` qiladi):

```bash
cp config.example.json config.json
python3 setup_config.py
```

Kutilgan chiqish: `config.json to'ldirildi: hub=https://agi.1pro.uz name=… (kalit yashirin, ruxsat 600)`.

- `SUP_FLEET_KEY` bo'sh bo'lsa skript to'xtaydi — egadan kalitni so'ra
  (`agent hub key`), **lekin kalit qiymatini chatga yozma**.
- `node_id` o'z-o'zidan yaratiladi (bo'sh qoldiriladi).
- **Kalitni hech qachon** `cat config.json`, `echo`, commit yoki skrinshot
  bilan oshkor qilma. `config.json` allaqachon `.gitignore` da — `git add -f`
  bilan ham majburlama.

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

### 6.3 O'zini ko'tarish sinovi (reboot SHART EMAS)

> ⚠️ **Ishlab turgan serverda reboot qilma.** Bu mashinada boshqa jonli
> xizmatlar bo'lishi mumkin - reboot ularning barchasini uzadi. Reboot
> autostartning yagona isboti EMAS. Quyidagilar rebootsiz ham "xizmat
> o'chsa o'zi ko'tariladi va yuklanishda yoqilgan" degan to'liq isbot:

```bash
# 1) yuklanishda yoqilganmi
systemctl is-enabled sup-agent            # -> enabled
# 2) unit fayl to'g'rimi
systemd-analyze verify sup-agent.service  # -> jim (xato yo'q)
# 3) jarayonni MAJBURAN o'ldir - Restart=always uni qayta ko'taradimi
sudo systemctl kill -s KILL sup-agent
sleep 8
systemctl is-active sup-agent             # -> yana active
journalctl -u sup-agent -n 5 --no-pager   # qayta ulanish izlari, xatosiz
```

To'liq reboot isboti kerak bo'lsa - uni **faqat ega belgilagan vaqtda**,
boshqa xizmatlar to'xtashiga tayyor bo'lganda, alohida qil.

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

### 6.6 Sir himoyasi (config.json git ga tushmagan, ruxsati tor)

```bash
# Linux/macOS: faqat ega o'qiy oladimi (-rw------- yoki 600)
ls -l config.json                     # -> -rw------- ... config.json
git -C . check-ignore config.json     # -> config.json (e'tiborsiz qoldirilgan)
git -C . status --porcelain config.json   # -> BO'SH (kuzatuvda emas)
```

`config.json` ruxsati 600 emas yoki git holatida ko'rinsa — darhol tuzat
(`chmod 600 config.json`), commitga qo'shma.

---

## 7. Hisobot (ishni tugatganda)

Egaga shu qatorni qaytar:

```
node: <nom> (<id>) · <OS> · autostart: <systemd|launchd|task> ·
tekshiruv: yoqilgan=ha, o'zini-ko'tardi=ha, markazda-onlayn=ha,
sir-himoya=ha (config.json 600, git da yo'q)
```

Biror band "yo'q" bo'lsa — sabab bilan yoz va tuzat. Autostart yoki reboot
sinovi tasdiqlanmagan bo'lsa, ish **tugallanmagan** hisoblanadi.
