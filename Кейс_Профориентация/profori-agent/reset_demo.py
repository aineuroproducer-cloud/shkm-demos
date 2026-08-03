#!/usr/bin/env python3
"""Сброс демо: удаляет сгенерированные файлы, чтобы пройти путь заново."""
from pathlib import Path
ROOT = Path(__file__).resolve().parent
CLIENTS = ROOT.parent / "demo-clients"
TO_DELETE = ["анализ_и_гипотезы.md", "итоговый_отчет.md"]
removed = 0
for folder in CLIENTS.iterdir():
    if folder.is_dir():
        for fname in TO_DELETE:
            f = folder / fname
            if f.exists():
                f.unlink(); removed += 1
                print(f"🗑  удалён: {folder.name}/{fname}")
print(f"\n✅ Готово. Удалено: {removed}. Папки снова чистые — можно показывать создание с нуля.")
