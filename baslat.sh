#!/bin/bash
# Ortamı başlatır: imajı (gerekirse) derler, konteyneri açar, tarayıcıyı açar.
cd "$(dirname "$0")"
docker compose up -d --build || exit 1
echo "Masaüstü açılıyor... (ilk seferde birkaç saniye bekleyin)"
sleep 4
open "http://localhost:6080/vnc.html?autoconnect=true&resize=scale"
