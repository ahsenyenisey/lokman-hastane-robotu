#!/bin/bash
# Konteyneri durdurur (dosyalarınız Mac'te kalır, hiçbir şey silinmez).
cd "$(dirname "$0")"
docker compose down
