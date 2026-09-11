#!/usr/bin/env python3
"""sup-agent - markaziy agentga ulanadigan qurilma agenti.

Bu kompyuter (makbuk, server, ...) markazga O'ZI ulanadi: har ~25 soniyada
"menga ish bormi?" deb so'rab turadi (long-poll). Shuning uchun bu yerda
hech qanday port ochilmaydi - NAT yoki fayervol orqasida ham ishlaydi.
Markazdan kelgan buyruqni bajaradi va natijani qaytaradi.

Uchta ish qiladi:
  * shell buyruqni bajarish (markaz nima buyursa)
  * fayl olish/berish (markaz orqali boshqa qurilmaga yoki Telegramga)
  * o'zini yangilash (markaz "update" desa GitHubdan git pull qilib qayta ishga)

Faqat standart kutubxona ishlatiladi - hech narsa o'rnatish shart emas.
Python 3.8+ bo'lsa yetadi.

Ishga tushirish:
    python node.py                 # config.json shu yerda bo'lishi kerak
    python node.py --once          # bir marta so'rab, chiqib ketadi (sinov)
"""
import hmac
import http.client
import json
import os
import platform
import socket
import ssl
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from hashlib import sha256
from pathlib import Path

HERE = Path(__file__).resolve().parent
CONFIG = HERE / "config.json"
VERSION = (HERE / "VERSION").read_text().strip() if (HERE / "VERSION").exists() \
    else "1.0.0"

# Long-poll markazda 25s ushlanadi - biz undan uzunroq kutamiz
POLL_TIMEOUT = 40
BACKOFF_MAX = 30

# --- buyruq imzosi ---------------------------------------------------------
# Node faqat IMZOLANGAN buyruqni bajaradi. Imzo kaliti (HMAC) markaz va shu
# node da bo'ladi - vositachi Worker da hech qachon. Ya'ni Worker yoki sizib
# chiqqan fleet kaliti buyruq soxtalashtira olmaydi. Bu funksiyalar markazdagi
# core/signing.py bilan AYNAN bir xil bo'lishi shart (kanonik satr bir xil).
_SIGVER = "hs1"
L_INFO, L_WARN, L_ERROR = "info", "warn", "error"


def _canon(cmd_id, node_id, kind, payload, issued_at, expires_at, nonce):
    body = json.dumps(payload or {}, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False)
    return "\n".join([_SIGVER, str(cmd_id), str(node_id), str(kind), body,
                      str(issued_at), str(expires_at), str(nonce)]).encode("utf-8")


def _verify(key_hex, cmd, node_id, now):
    """(ok, sabab). Imzo, muddat tekshiriladi; takror (nonce/id) chaqiruvchida."""
    if not key_hex:
        return False, "imzo kaliti yo'q"
    try:
        exp = int(cmd.get("expires_at"))
    except (TypeError, ValueError):
        return False, "muddat yaroqsiz"
    if now > exp:
        return False, "muddat o'tgan"
    if str(cmd.get("node_id")) != str(node_id):
        return False, "boshqa qurilmaga"
    want = hmac.new(
        bytes.fromhex(key_hex),
        _canon(cmd.get("id"), node_id, cmd.get("kind"), cmd.get("payload"),
               cmd.get("issued_at"), exp, cmd.get("nonce")),
        "sha256").hexdigest()
    if not hmac.compare_digest(want, str(cmd.get("sig") or "")):
        return False, "imzo mos kelmadi"
    return True, "ok"


def load_config() -> dict:
    if not CONFIG.exists():
        sys.exit(
            f"config.json topilmadi: {CONFIG}\n"
            "Namuna: config.example.json ni nusxa oling va to'ldiring.")
    cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
    if not cfg.get("hub") or not cfg.get("key"):
        sys.exit("config.json da 'hub' (markaz manzili) va 'key' (fleet kaliti) "
                 "bo'lishi shart.")
    # node_id yo'q bo'lsa - yaratamiz va config ga yozib qo'yamiz (barqaror bo'lsin)
    if not cfg.get("node_id"):
        import secrets
        host = socket.gethostname().split(".")[0].lower()
        cfg["node_id"] = f"{host}-{secrets.token_hex(2)}"
        CONFIG.write_text(json.dumps(cfg, ensure_ascii=False, indent=2),
                          encoding="utf-8")
    return cfg


def _norm_projects(raw) -> list:
    if isinstance(raw, dict):
        return [{"name": k, "path": v} for k, v in raw.items()]
    out = []
    for p in raw or []:
        if isinstance(p, str):
            out.append({"name": Path(p).name, "path": p})
        elif isinstance(p, dict):
            out.append({"name": p.get("name") or Path(p.get("path", "")).name,
                        "path": p.get("path", "")})
    return out


class Node:
    def __init__(self, cfg: dict) -> None:
        self.cfg = cfg
        self.hub = cfg["hub"].rstrip("/")
        self.key = cfg["key"]
        self.node_id = cfg["node_id"]
        self.name = cfg.get("name") or self.node_id
        self.shell = cfg.get("shell")  # None = OS standarti
        self.projects = _norm_projects(cfg.get("projects"))
        self.sign_key = cfg.get("sign_key") or ""   # buyruq imzosi kaliti
        self.seen = set()                            # bajarilgan buyruq id lari (takrorga qarshi)
        self.logbuf = []                             # markazga yuboriladigan jurnal
        parsed = urllib.parse.urlparse(self.hub)
        self._https = parsed.scheme == "https"
        self._host = parsed.hostname
        self._port = parsed.port or (443 if self._https else 80)

    # ---- HTTP yordamchilar ----

    def _post(self, path: str, body: dict, timeout: int) -> dict:
        data = json.dumps(body).encode("utf-8")
        req = urllib.request.Request(
            f"{self.hub}{path}", data=data, method="POST",
            headers={"Content-Type": "application/json",
                     "X-Fleet-Key": self.key, "X-Node-Id": self.node_id})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))

    # ---- markaziy jurnal: node nima qilyapti / qanday xatoga uchradi ----

    def _log(self, level: str, detail: str) -> None:
        """Bir qatorni ekranga chiqaradi va markazga yuborish uchun buferga
        qo'yadi. Node noto'g'ri ishlasa ham, sabab markazda ko'rinsin."""
        line = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                "level": level, "detail": str(detail)[:1000]}
        self.logbuf.append(line)
        if len(self.logbuf) > 200:       # ulanmagan bo'lsa cheksiz o'smasin
            self.logbuf = self.logbuf[-200:]
        print(f"[sup-agent] {level}: {detail}")

    def _flush_logs(self) -> None:
        """Buferdagi jurnalni markazga yuboradi. Yuborilmasa - keyingi safar."""
        if not self.logbuf:
            return
        batch, self.logbuf = self.logbuf[:100], self.logbuf[100:]
        try:
            self._post("/api/hub/log",
                       {"node_id": self.node_id, "logs": batch}, 30)
        except (urllib.error.URLError, OSError):
            self.logbuf = batch + self.logbuf     # qaytarib qo'yamiz

    def _conn(self):
        if self._https:
            return http.client.HTTPSConnection(
                self._host, self._port, timeout=1800,
                context=ssl.create_default_context())
        return http.client.HTTPConnection(self._host, self._port, timeout=1800)

    # ---- asosiy tsikl ----

    def hello(self) -> dict:
        return {
            "node_id": self.node_id,
            "name": self.name,
            "os": platform.system(),
            "arch": platform.machine(),
            "hostname": socket.gethostname(),
            "version": VERSION,
            "projects": self.projects,
            "labels": self.cfg.get("labels") or {},
            "keyed": bool(self.sign_key),
        }

    def _provision(self, prov) -> None:
        """Markaz birinchi ulanishda imzo kalitini yuboradi - saqlab qo'yamiz."""
        if not prov:
            return
        key = prov.get("sign_key")
        if key and not self.sign_key:
            self.sign_key = key
            try:
                cfg = json.loads(CONFIG.read_text(encoding="utf-8"))
                cfg["sign_key"] = key
                CONFIG.write_text(
                    json.dumps(cfg, ensure_ascii=False, indent=2),
                    encoding="utf-8")
                print("[sup-agent] imzo kaliti o'rnatildi")
            except OSError as exc:
                print(f"[sup-agent] kalitni saqlab bo'lmadi: {exc}")

    def _authorize(self, cmd) -> tuple:
        """Buyruq imzosi va takror tekshiruvi. Faqat o'tgan buyruq bajariladi."""
        ok, why = _verify(self.sign_key, cmd, self.node_id, int(time.time()))
        if not ok:
            return False, why
        cid = cmd.get("id")
        if cid in self.seen:
            return False, "takror"
        self.seen.add(cid)
        if len(self.seen) > 5000:
            self.seen = set(sorted(self.seen)[-2000:])
        return True, "ok"

    def run_forever(self, once: bool = False) -> None:
        self._log(L_INFO, f"ishga tushdi {self.name} -> {self.hub}")
        backoff = 1
        while True:
            try:
                resp = self._post("/api/hub/poll", self.hello(), POLL_TIMEOUT)
                backoff = 1
                self._provision(resp.get("provision"))
                cmd = resp.get("command")
                if cmd:
                    self.handle(cmd)
                self._flush_logs()
                if once:
                    return
            except urllib.error.HTTPError as exc:
                if exc.code == 403:
                    print("[sup-agent] bu qurilma bloklangan. To'xtatilyapti.")
                    return
                # Markazga yetdik, lekin xato qaytdi - buni ham yozib qo'yamiz
                self._log(L_WARN, f"markaz xatosi {exc.code}")
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
            except (urllib.error.URLError, OSError, ConnectionError) as exc:
                # Ulanmadi - jurnal buferda qoladi, ulangach yuboriladi
                self._log(L_WARN, f"ulanmadi: {exc}")
                time.sleep(backoff)
                backoff = min(backoff * 2, BACKOFF_MAX)
                if once:
                    return

    # ---- buyruqlarni bajarish ----

    def handle(self, cmd: dict) -> None:
        kind = cmd.get("kind")
        cid = cmd.get("id")
        payload = cmd.get("payload") or {}
        # Imzo tekshiruvi - imzosiz/soxta buyruq BAJARILMAYDI.
        ok, why = self._authorize(cmd)
        if not ok:
            self._log(L_ERROR, f"buyruq #{cid} rad etildi: {why}")
            self._report(cid, "error", {"error": f"imzo rad etdi: {why}"}, None)
            return
        self._log(L_INFO, f"buyruq #{cid}: {kind}")
        try:
            if kind == "run":
                status, result, code = self._do_run(payload)
            elif kind == "put":
                status, result, code = self._do_put(payload)
            elif kind == "get":
                status, result, code = self._do_get(payload)
            elif kind == "update":
                self._report(cid, "done", {"note": "yangilanyapti"}, 0)
                self._log(L_INFO, "yangilanish boshlandi")
                self._flush_logs()
                self._do_update()
                return
            else:
                status, result, code = "error", {"error": f"noma'lum: {kind}"}, None
        except Exception as exc:  # noqa: BLE001 - har qanday xato natija bo'lib qaytadi
            status, result, code = "error", {"error": str(exc)}, None
        # Natija - ayniqsa xato - markaziy jurnalga tushsin
        extra = ""
        if status == "error":
            r = result or {}
            extra = ": " + str(r.get("error") or r.get("stderr")
                               or f"kod {code}")[:200]
        self._log(L_ERROR if status == "error" else L_INFO,
                  f"#{cid} {kind} -> {status}{extra}")
        self._report(cid, status, result, code)

    def _do_run(self, p: dict):
        cmd = p.get("cmd", "")
        cwd = p.get("cwd") or None
        timeout = int(p.get("timeout") or 60)
        if cwd:
            cwd = os.path.expanduser(cwd)
        run_kw = {"cwd": cwd, "capture_output": True, "text": True,
                  "timeout": timeout}
        if self.shell:
            proc = subprocess.run([self.shell, "-lc", cmd], **run_kw)
        else:
            proc = subprocess.run(cmd, shell=True, **run_kw)
        status = "done" if proc.returncode == 0 else "error"
        return status, {"stdout": proc.stdout, "stderr": proc.stderr,
                        "cwd": cwd or os.getcwd()}, proc.returncode

    def _do_put(self, p: dict):
        """Faylni markazga yuklaydi, blob_id ni qaytaradi."""
        path = os.path.expanduser(p.get("path", ""))
        if not os.path.isfile(path):
            return "error", {"error": f"fayl yo'q: {path}"}, None
        name = os.path.basename(path)
        info = self._upload(path, name)
        return "done", {"blob_id": info["blob_id"], "name": name,
                        "size": info["size"], "sha256": info["sha256"]}, 0

    def _do_get(self, p: dict):
        """Markazdagi blobni shu qurilmaga tushiradi."""
        blob_id = p.get("blob_id")
        dest = os.path.expanduser(p.get("dest_path") or p.get("name") or blob_id)
        if os.path.isdir(dest):
            dest = os.path.join(dest, p.get("name") or blob_id)
        os.makedirs(os.path.dirname(os.path.abspath(dest)), exist_ok=True)
        got = self._download(blob_id, dest)
        return "done", {"path": os.path.abspath(dest), "size": got}, 0

    # ---- fayl o'tkazish (oqim bilan, xotirani band qilmasdan) ----

    def _upload(self, path: str, name: str) -> dict:
        size = os.path.getsize(path)
        h = sha256()
        conn = self._conn()
        q = urllib.parse.urlencode({"name": name})
        conn.putrequest("POST", f"/api/hub/blob?{q}")
        conn.putheader("X-Fleet-Key", self.key)
        conn.putheader("X-Node-Id", self.node_id)
        conn.putheader("Content-Type", "application/octet-stream")
        conn.putheader("Content-Length", str(size))
        conn.endheaders()
        with open(path, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                conn.send(chunk)
                h.update(chunk)
        resp = conn.getresponse()
        body = resp.read().decode("utf-8")
        conn.close()
        if resp.status != 200:
            raise RuntimeError(f"yuklash rad etildi ({resp.status}): {body}")
        info = json.loads(body)
        if info.get("sha256") and info["sha256"] != h.hexdigest():
            raise RuntimeError("sha256 mos kelmadi - fayl buzilgan")
        return info

    def _download(self, blob_id: str, dest: str) -> int:
        req = urllib.request.Request(
            f"{self.hub}/api/hub/blob/{blob_id}",
            headers={"X-Fleet-Key": self.key, "X-Node-Id": self.node_id})
        size = 0
        with urllib.request.urlopen(req, timeout=1800) as resp, \
                open(dest, "wb") as fh:
            for chunk in iter(lambda: resp.read(1 << 20), b""):
                fh.write(chunk)
                size += len(chunk)
        return size

    # ---- natijani qaytarish ----

    def _report(self, cid, status, result, code) -> None:
        try:
            self._post("/api/hub/result", {
                "command_id": cid, "status": status,
                "result": result, "exit_code": code}, 60)
        except (urllib.error.URLError, OSError) as exc:
            print(f"[sup-agent] natijani yuborib bo'lmadi: {exc}")

    # ---- o'zini yangilash ----

    def _do_update(self) -> None:
        print("[sup-agent] git pull ...")
        try:
            out = subprocess.run(
                ["git", "-C", str(HERE), "pull", "--ff-only"],
                capture_output=True, text=True, timeout=120)
            print(out.stdout.strip() or out.stderr.strip())
        except Exception as exc:  # noqa: BLE001
            print(f"[sup-agent] yangilash xatosi: {exc}")
            return
        print("[sup-agent] qayta ishga tushirilyapti ...")
        os.execv(sys.executable,
                 [sys.executable, str(HERE / "node.py"), *sys.argv[1:]])


def main() -> None:
    once = "--once" in sys.argv
    node = Node(load_config())
    try:
        node.run_forever(once=once)
    except KeyboardInterrupt:
        print("\n[sup-agent] to'xtatildi")


if __name__ == "__main__":
    main()
