#!/usr/bin/env python3
"""
Сброс демо: удаляет client_profile.md и proposal_draft.md из всех папок клиентов,
чтобы пройти путь заново с чистого листа.

Запуск:
    python reset_demo.py
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parent
CLIENTS = ROOT / "demo-clients"
TO_DELETE = ["client_profile.md", "proposal_draft.md"]

removed = 0
for folder in CLIENTS.iterdir():
    if folder.is_dir():
        for fname in TO_DELETE:
            f = folder / fname
            if f.exists():
                f.unlink(); removed += 1
                print(f"🗑  удалён: {folder.name}/{fname}")

print(f"\n✅ Готово. Удалено файлов: {removed}. Папки клиентов снова чистые.")
print("Теперь можно запускать agent.py заново и смотреть на создание профилей с нуля.")
