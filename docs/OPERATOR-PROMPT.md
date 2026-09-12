# Operator ko'rsatmasi — qurilmani AI bilan avtomatik ulash

Bu fayl **ega** uchun: har bir serverga sup-agent ni o'rnatishni u yerdagi AI
(Claude Code) ga topshirish, **ruxsat so'ramasdan (bypass)**, lekin xavfsizlik
buzilmasdan.

Ikki qatlam himoya ishlaydi:

- **`.claude/settings.json`** (repoda) — o'rnatish buyruqlari oldindan ruxsat
  etilgan (so'rovsiz o'tadi); reboot, firewall, `rm -rf /`, sir commit kabi
  halokatli buyruqlar `deny` bilan **qattiq bloklangan**.
- **`CLAUDE.md`** (repoda, avtomatik yuklanadi) — semantik qizil chiziqlar
  (sirni oshkor qilmaslik, boshqa xizmatga tegmaslik) har doim kontekstda.

---

## 1. Kalitni muhitga ber (chatga EMAS)

Fleet kaliti sir. Uni AI suhbatiga yozma — ishga tushiradigan shellda export
qil, skript o'zi oladi:

```bash
export SUP_FLEET_KEY='<markazda: agent hub key>'
export SUP_NODE_NAME='vps-frankfurt'      # takrorlanmas nom
```

## 2. Serverga reponi ol va AI ni ishga tushir

```bash
sudo git clone https://github.com/Yaxyobek0877/sup-agent.git /opt/sup-agent
cd /opt/sup-agent
```

Reponing ichida (`cd /opt/sup-agent`) `claude` ishga tushiriladi — u yerda
`CLAUDE.md` (qoidalar) va `.claude/settings.json` (ruxsatlar) avtomatik
qo'llanadi. Prompt qisqa bo'lishi mumkin, chunki batafsil ko'rsatma
`docs/O'RNATISH.md` da.

### Profil A — nazorat ostida avtomatik (TAVSIYA, jonli serverlar uchun)

`.claude/settings.json` o'rnatish buyruqlarini so'rovsiz o'tkazadi, xavflini
`deny` bilan bloklaydi:

```bash
claude --permission-mode acceptEdits \
  -p "docs/O'RNATISH.md ni to'liq bajar. CLAUDE.md qizil chiziqlariga amal qil. Fleet kalitini SUP_FLEET_KEY muhitidan python3 setup_config.py orqali yoz. Har tekshiruvni (§6) haqiqatan ishga tushir; oxirida §7 hisobotini qaytar."
```

Interaktiv istasang: shunchaki `claude` ni och va pastdagi **PROMPT** bloqini
joylashtir.

### Profil B — to'liq bypass (FAQAT toza/yangi, boshqa hech nima yo'q server)

Hamma narsani so'rovsiz bajaradi (`deny` ham kuchsiz) — shuning uchun faqat
yo'qotishga arzimaydigan yangi VPS da. `CLAUDE.md` baribir yuklanadi, AI o'zini
tiyadi, lekin qattiq to'siq yo'q:

```bash
claude --dangerously-skip-permissions \
  -p "docs/O'RNATISH.md ni to'liq bajar. CLAUDE.md qizil chiziqlariga amal qil. Oxirida §7 hisobotini qaytar."
```

> Jonli, muhim serverda (bazalar, tunnellar, boshqa xizmatlar bor) **Profil A
> ishlat.** Profil B ni u yerda ishlatma.

---

## 3. PROMPT (AI ga beriladigan matn)

### PROMPT

Sen shu serverdagi tizim muhandisisan. Vazifang: bu qurilmani markaziy
agentga (https://agi.1pro.uz) doimiy ulash. Qadamma-qadam `docs/O'RNATISH.md`
ni bajar va `CLAUDE.md` dagi qoidalarga qat'iy amal qil.

Buzilmas qoidalar (bypass rejimida ham):
- `config.json` sir — fleet kaliti unда. Uni chatga/jurnalga/commitga
  chiqarma; `git add` qilma; o'rnatgach `chmod 600`. Kalitni `SUP_FLEET_KEY`
  muhitidan `python3 setup_config.py` orqali yoz — qiymatini ko'rsatma.
- Faqat sup-agent o'rnatishga tegishli ishni qil. Boshqa xizmatlarni
  to'xtatma/o'chirma/qayta sozlama.
- REBOOT yoki SHUTDOWN qilma. Autostart isboti — jarayonni majburan o'ldirib,
  o'zi ko'tarilishini ko'rsatish (O'RNATISH.md §6.3), reboot emas.
- Firewall (ufw/iptables/nft), SELinux, SSH, foydalanuvchi sozlamalariga tegma.
- Tizim yo'llarida `rm -rf`, `mkfs`, `dd` ishlatma. Internet skriptini shellga
  quyma.

Ish tugadi deb hisoblama — quyidagilar tasdiqlanmaguncha (O'RNATISH.md §6):
1) node.py ishlayapti va markazga ulangan;
2) autostart o'rnatilgan va YOQILGAN (is-enabled = enabled);
3) o'zini-ko'tarish sinovi o'tgan (kill → qayta ko'tarildi);
4) repo git kloni (update uchun);
5) config.json ruxsati 600 va git da yo'q (§6.6).

Har tekshiruv buyrug'ini haqiqatan ishga tushir va chiqishini ko'r. Kutilmagan
holat, kalit yo'qligi yoki boshqa xizmatga tegish zarurati chiqsa — TO'XTA va
menga (egaga) sabab bilan yoz. Oxirida O'RNATISH.md §7 dagi hisobot qatorini
qaytar.

### PROMPT-END

---

## 4. O'rnatishdan keyin — kalitni yangilash (agar chatda ko'ringan bo'lsa)

Agar fleet kaliti biror joyda ochilgan bo'lsa (masalan xato bilan chatga
yozilgan), markazda yangisini yarat va qurilmalarga tarqat:

1. Markaz: `.fleet-key` ni o'chir va serverni qayta ishga tushir (yangi kalit).
2. Har qurilmada `SUP_FLEET_KEY` ni yangilab `python3 setup_config.py` ni
   qayta ishga tushir, so'ng `sudo systemctl restart sup-agent`.

Batafsil xavfsizlik: [../README.md](../README.md) "Xavfsizlik".
