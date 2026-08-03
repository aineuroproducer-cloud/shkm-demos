#!/usr/bin/env python3
"""
Career Intake Agent — обрабатывает папки клиентов карьерного консультанта.

Что делает:
  1. Находит папки клиентов в каталоге (по умолчанию ./demo-clients)
  2. Для каждой папки без client_profile.md — читает транскрипт, CV, анкету
  3. Анализирует через Claude API (live) ИЛИ берёт демо-результат (без ключа)
  4. Сохраняет client_profile.md и proposal_draft.md в папку клиента
  5. Печатает итоговый отчёт

Запуск:
  python agent.py                      # демо-режим (без API-ключа), все папки
  python agent.py --folder "Клиент_1_Дмитрий_Корнев"   # одна папка
  python agent.py --live               # боевой режим, нужен ANTHROPIC_API_KEY
  python agent.py --force              # перезаписать существующие профили

Учебный агент для модуля «AI-ассистенты и автоматизация» Школы карьерного менеджмента.
Собран вайбкодингом по ТЗ (см. TZ.md) — без ручного написания кода.
"""
import argparse, json, os, sys
from pathlib import Path

# --- настройки путей ---
ROOT = Path(__file__).resolve().parent
DEFAULT_CLIENTS_DIR = ROOT / "demo-clients"

INPUT_FILES = ["transcript.txt", "cv.txt", "anketa.txt"]      # что читаем у клиента


# ---------------------------------------------------------------------------
# 1. ЧТЕНИЕ ВХОДНЫХ ДАННЫХ
# ---------------------------------------------------------------------------
def read_client_inputs(folder: Path) -> dict:
    data = {"transcript": "", "cv": "", "anketa": "", "name": folder.name}
    for fname in INPUT_FILES:
        f = folder / fname
        if f.exists():
            txt = f.read_text(encoding="utf-8", errors="ignore")
            if "transcript" in fname: data["transcript"] = txt
            elif "cv" in fname:       data["cv"] = txt
            elif "anketa" in fname:   data["anketa"] = txt
    # имя клиента — из названия папки "Клиент_N_Имя_Фамилия"
    parts = folder.name.split("_")
    if len(parts) >= 4:
        data["name"] = " ".join(parts[2:])
    return data


# ---------------------------------------------------------------------------
# 2. АНАЛИЗ — LIVE (Claude API) или DEMO (готовые фикстуры)
# ---------------------------------------------------------------------------
ANALYSIS_PROMPT = """Ты — AI-ассистент карьерного консультанта.
По материалам клиента сделай два блока на русском и верни строго JSON:
{{"profile":"<markdown профиля>","proposal":"<текст письма до 200 слов>"}}

PROFILE содержит разделы: ПРОФИЛЬ КЛИЕНТА, ЗАПРОС И ЦЕЛИ, БОЛИ И ПРЕПЯТСТВИЯ,
СИЛЬНЫЕ СТОРОНЫ (hard/soft/достижения с цифрами), ПРОБЕЛЫ,
РЕКОМЕНДУЕМЫЙ ПАКЕТ (single session или пакет 3 + обоснование), СЛЕДУЮЩИЙ ШАГ.
PROPOSAL — тёплое письмо: тема, приветствие по имени, что услышал на звонке,
конкретное предложение пакета, следующий шаг, подпись.

МАТЕРИАЛЫ КЛИЕНТА:
{materials}
"""

def analyze_live(data: dict) -> dict:
    """Боевой режим: реальный вызов Claude API."""
    import anthropic  # ставится: pip install anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    materials = (
        f"ИМЯ: {data['name']}\n\nТРАНСКРИПТ:\n{data['transcript']}\n\n"
        f"CV:\n{data['cv'] or 'нет'}\n\nАНКЕТА:\n{data['anketa'] or 'нет'}"
    )
    msg = client.messages.create(
        model="claude-3-5-sonnet-20241022", max_tokens=2000,
        messages=[{"role": "user",
                   "content": ANALYSIS_PROMPT.format(materials=materials)}],
    )
    raw = msg.content[0].text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def analyze_demo(data: dict) -> dict:
    """Демо-режим: берём готовый анализ из fixtures.json (можно запускать без ключей)."""
    fixtures = json.loads((ROOT / "fixtures.json").read_text(encoding="utf-8"))
    key = None
    n = data["name"].lower()
    if "дмитрий" in n: key = "dmitry"
    elif "анна" in n:  key = "anna"
    if not key or key not in fixtures:
        raise RuntimeError(
            "Демо-режим знает только Дмитрия и Анну. "
            "Для других клиентов запусти с --live и ANTHROPIC_API_KEY.")
    return fixtures[key]


# ---------------------------------------------------------------------------
# 3. СОХРАНЕНИЕ РЕЗУЛЬТАТА
#    (в полной версии здесь были бы вызовы Google Drive / Docs / Gmail API —
#     см. TZ.md, раздел «Боевая версия с Google Workspace»)
# ---------------------------------------------------------------------------
def save_outputs(folder: Path, analysis: dict):
    (folder / "client_profile.md").write_text(analysis["profile"], encoding="utf-8")
    (folder / "proposal_draft.md").write_text(analysis["proposal"], encoding="utf-8")


# ---------------------------------------------------------------------------
# 4. ОРКЕСТРАЦИЯ
# ---------------------------------------------------------------------------
def process_folder(folder: Path, live: bool, force: bool):
    if (folder / "client_profile.md").exists() and not force:
        return ("skip", folder.name, "профиль уже есть")
    data = read_client_inputs(folder)
    if not data["transcript"]:
        return ("skip", folder.name, "нет транскрипта")
    try:
        analysis = analyze_live(data) if live else analyze_demo(data)
        save_outputs(folder, analysis)
        return ("ok", data["name"], folder.name)
    except Exception as e:
        return ("error", folder.name, str(e))


def main():
    ap = argparse.ArgumentParser(description="Career Intake Agent")
    ap.add_argument("--clients-dir", default=str(DEFAULT_CLIENTS_DIR))
    ap.add_argument("--folder", help="обработать только одну папку (имя)")
    ap.add_argument("--live", action="store_true", help="боевой режим (Claude API)")
    ap.add_argument("--force", action="store_true", help="перезаписать существующие")
    args = ap.parse_args()

    base = Path(args.clients_dir)
    if not base.exists():
        sys.exit(f"❌ Каталог клиентов не найден: {base}")

    if args.folder:
        folders = [base / args.folder]
    else:
        folders = [p for p in base.iterdir()
                   if p.is_dir() and any((p / f).exists() for f in INPUT_FILES)]

    mode = "LIVE (Claude API)" if args.live else "DEMO (без ключей)"
    print(f"\n🤖 Career Intake Agent — режим: {mode}")
    print(f"📂 Каталог клиентов: {base}\n" + "─" * 52)

    done, skipped, errors = [], [], []
    for folder in sorted(folders):
        status, a, b = process_folder(folder, args.live, args.force)
        if status == "ok":
            done.append((a, b)); print(f"✅ {a}: создан profile + proposal")
        elif status == "skip":
            skipped.append((a, b)); print(f"⏭️  {a}: {b}")
        else:
            errors.append((a, b)); print(f"❗ {a}: {b}")

    print("─" * 52)
    print(f"Готово. Обработано: {len(done)}, пропущено: {len(skipped)}, ошибок: {len(errors)}")
    if done:
        print("\nКраткое резюме:")
        for name, fld in done:
            print(f"  • {name} → профиль и черновик письма в папке «{fld}»")


if __name__ == "__main__":
    main()
