#!/usr/bin/env bash
# sup-agent supervizori — ROOT'SIZ autostart uchun (install.sh cron rejimi).
#
# cron buni @reboot va har daqiqa ishga tushiradi. flock (FD 9) tufayli
# faqat BITTA nusxa ishlaydi: qolganlari darrov chiqib ketadi. Ishlab
# turgani node.py ni doim ushlab turadi — u yiqilsa 5 soniyada qayta.
# Sudo yoki root kerak emas.
cd "$(dirname "$0")" || exit 1

exec 9>".node.lock"
flock -n 9 || exit 0            # boshqa supervizor ishlayapti — chiqamiz

while true; do
  python3 node.py >> node.log 2>&1
  sleep 5
done
