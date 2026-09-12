# sup-agent — shu qurilmadagi AI uchun qoidalar

Bu faylni **shu kompyuterda ishlayotgan sun'iy intellekt** (Claude Code yoki
shunga o'xshash) o'qiydi. U bu yerda **avtomatik** yuklanadi — shuning uchun
buyruqlar ruxsatsiz (bypass) bajarilsa ham, quyidagi qoidalar kontekstda
turadi va **buzilmasligi shart**.

Vazifang: bu qurilmani markaziy agentga (`https://agi.1pro.uz`) doimiy ulash —
qadamma-qadam **[docs/O'RNATISH.md](docs/O'RNATISH.md)** bo'yicha. Undan
chetga chiqma.

---

## 🚫 QIZIL CHIZIQLAR — hech qachon buzilmaydi (bypass rejimida ham)

1. **Sir (`config.json`) himoya qilinadi.** Unda fleet kaliti va imzo kaliti
   (`sign_key`) bor. Uni:
   - hech qachon **chatga, jurnalga, commit xabariga, skrinshotga chiqarma**;
   - o'rnatgach **`chmod 600 config.json`** qil (faqat ega o'qiy oladi);
   - **hech qachon `git add` / `git commit` / `git push` qilma** — u
     `.gitignore` da, `git add -f` bilan ham majburlama.
   - kalitni tashqi manzilga (URL, query, webhook) yuborma.

2. **Faqat sup-agent o'rnatishga tegishli ishni qil.** Bu mashinada boshqa
   jonli xizmatlar bo'lishi mumkin (bazalar, veb-serverlar, tunnellar). Ularni
   **to'xtatma, o'chirma, qayta sozlama**.

3. **REBOOT / SHUTDOWN QILMA.** Ishlab turgan serverni qayta yuklash undagi
   hamma xizmatni uzadi. Autostart isboti reboot EMAS — jarayonni majburan
   o'ldirib, o'zi ko'tarilishini ko'rsatish (O'RNATISH.md §6.3). To'liq reboot
   sinovi kerak bo'lsa — faqat **ega ruxsati va belgilangan vaqtida**.

4. **Xavfsizlik sozlamalariga tegma.** Firewall (`ufw`, `iptables`, `nft`),
   SELinux/AppArmor, SSH konfiguratsiyasi, foydalanuvchi/parol, sertifikatlar —
   **o'zgartirma**. Kerak bo'lsa STOP qil va egadan so'ra.

5. **Halokatli buyruqlar yo'q.** Tizim yo'llarida `rm -rf` (`/`, `/etc`,
   `/var`, `/usr`, uy papkasi), `mkfs`, `dd`, disk formatlash — **ishlatma**.
   Internetdan skriptni to'g'ridan-to'g'ri shellga quyma
   (`curl … | sh`, `wget … | bash`).

6. **`sudo` faqat zarur qadamda** (paket o'rnatish, systemd unit yozish,
   `daemon-reload`, `enable`). Undan tashqarida ildiz huquqidan foydalanma.

7. **`hub` manzili faqat `https://`.** Node.py ning imzo (HMAC) va takrorga
   qarshi mantig'ini, `_canon`/`_verify` ni **zaiflashtirma yoki chetlab
   o'tma** — u markaz bilan aynan mos bo'lishi shart.

---

## ✋ STOP qil va egadan so'ra

Quyidagilarda ishni to'xtat, qilma, sabab bilan egaga yoz:

- Kalit (`key`) yo'q yoki noto'g'ri; markazga ulanib bo'lmayapti (401/403).
- Biror qadam boshqa xizmatga tegishni yoki xavfsizlik sozlamasini
  o'zgartirishni talab qilsa.
- Runbookda yo'q, kutilmagan buyruq bajarish kerak bo'lib qolsa.
- Majburiy tekshiruv (§6) o'tmasa va sababi noaniq bo'lsa.

Kutilmagan holatni "ehtimol ishlaydi" deb o'tkazib yuborma.

---

## ✅ Ish tugadi deb hisoblash sharti

**[docs/O'RNATISH.md](docs/O'RNATISH.md) §6 (MAJBURIY TEKSHIRUV)** to'liq
o'tmaguncha ish tugamagan:

1. `node.py` ishlayapti va markazga ulangan.
2. Autostart o'rnatilgan **va yoqilgan** (`is-enabled` = enabled).
3. O'zini-ko'tarish sinovi o'tgan (jarayonni o'ldirdim → qayta ko'tarildi).
4. Repo git kloni (update ishlashi uchun).
5. Egaga hisobot qatori (§7) qaytarildi.

Har tekshiruv buyrug'ini **haqiqatan ishga tushir** va chiqishini ko'r.
Tekshirilmagan autostart — tugallanmagan ish.

---

## Avtomatik (bypass) rejimi haqida

Bu ishni ega **ruxsat so'ramaydigan rejimda** ishga tushirishi mumkin. Buni
xavfsiz qiladigan ikki qatlam bor:

- **`.claude/settings.json`** — o'rnatish buyruqlari oldindan ruxsat etilgan
  (so'rovsiz o'tadi), yuqoridagi halokatli buyruqlar esa **`deny` bilan qattiq
  bloklangan**.
- **Shu CLAUDE.md** — semantik qoidalar (sirni oshkor qilmaslik, boshqa
  xizmatga tegmaslik) har doim kontekstda.

Shuning uchun tez ishla, lekin qizil chiziqlarni hech qachon kesib o'tma.
Batafsil: [docs/OPERATOR-PROMPT.md](docs/OPERATOR-PROMPT.md).
