#!/bin/bash
# Ortamı başlatır: imajı (gerekirse) derler, konteyneri açar, tarayıcıyı açar.
# macOS, Linux ve Windows'taki WSL (Ubuntu) terminalinde çalışır.
cd "$(dirname "$0")"
docker compose up -d --build || exit 1
echo "Masaüstü açılıyor... (ilk seferde birkaç saniye bekleyin)"
sleep 4
URL="http://localhost:6080/vnc.html?autoconnect=true&resize=scale"
if command -v open >/dev/null; then open "$URL"            # macOS
elif command -v wslview >/dev/null; then wslview "$URL"    # Windows (WSL)
elif command -v xdg-open >/dev/null; then xdg-open "$URL"  # Linux
else echo "Tarayıcıda açın: $URL"
fi
