#!/usr/bin/env python3
"""
Профориентация: агент обработки папок клиентов.

Что делает:
  1. Находит папки клиентов (по умолчанию ../demo-clients)
  2. Для каждой папки без "анализ_и_гипотезы.md" читает отчёт + контекст встречи
  3. Анализирует через Claude API (live) ИЛИ берёт демо-результат (без ключа)
  4. Сохраняет "анализ_и_гипотезы.md" (до сессии) и "итоговый_отчет.md" (после сессии)
  5. Печатает отчёт

Запуск:
  python agent.py                 # демо-режим (без ключей), все папки
  python agent.py --live          # боевой режим, нужен ANTHROPIC_API_KEY
  python agent.py --force         # перезаписать существующие

Учебный агент для модуля «Ассистенты и агенты» ШКМ. Собран вайбкодингом по описанию задачи.
"""
import argparse, json, os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DEFAULT_CLIENTS_DIR = ROOT.parent / "demo-clients"
REPORT_FILE = "профориентационный_отчет.txt"
CONTEXT_FILE = "контекст_встречи.txt"
OUT_ANALYSIS = "анализ_и_гипотезы.md"
OUT_REPORT = "итоговый_отчет.md"


# ---------- чтение ----------
def read_inputs(folder: Path) -> dict:
    data = {"name": folder.name, "report": "", "context": ""}
    if (folder / REPORT_FILE).exists():
        data["report"] = (folder / REPORT_FILE).read_text(encoding="utf-8", errors="ignore")
    if (folder / CONTEXT_FILE).exists():
        data["context"] = (folder / CONTEXT_FILE).read_text(encoding="utf-8", errors="ignore")
    # тип по названию/содержимому
    low = (folder.name + data["report"]).lower()
    data["kind"] = "teen" if ("подрост" in low or "класс" in low) else "adult"
    return data


# ---------- анализ ----------
ANALYSIS_PROMPT = """Ты — AI-ассистент профориентатора. По профориентационному отчёту
(методика Digital Human) и контексту встречи сделай ДВА документа на русском и верни строго JSON:
{"analysis":"<markdown: анализ и гипотезы ДО сессии>","report":"<markdown: черновик итогового отчёта ПОСЛЕ сессии>"}

analysis содержит: Краткий профиль; Сильные стороны (по компетенциям); Ценности и подходящие
сферы; Гипотезы консультанта (что проверить); Вопросы к встрече (по чек-листу); Приоритетные
направления; Рекомендации по подготовке.

report — отчёт-презентация. Для подростка: ФИО, возраст, класс, город, запрос родителей и
подростка, даты, инструменты, школьные предметы, хобби, сильные стороны, подходящие сферы,
рассматриваемые профессии, заинтересовавшие профессии, рекомендации по экзаменам (ОГЭ/ЕГЭ),
предметы для фокуса, программы ВУЗов/колледжей, общие рекомендации. Для взрослого: запрос,
точка А, сильные стороны, подходящие сферы, рекомендуемые сценарии (маршрутная карта),
общие рекомендации и шаги.

ТИП ОТЧЁТА: {kind}

ОТЧЁТ:
{report}

КОНТЕКСТ ВСТРЕЧИ:
{context}
"""

def analyze_live(data: dict) -> dict:
    import anthropic
    client = anthropic.Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    prompt = ANALYSIS_PROMPT.format(kind=data["kind"], report=data["report"],
                                    context=data["context"] or "нет")
    msg = client.messages.create(model="claude-3-5-sonnet-20241022", max_tokens=3000,
                                 messages=[{"role": "user", "content": prompt}])
    raw = msg.content[0].text.replace("```json", "").replace("```", "").strip()
    return json.loads(raw)


def analyze_demo(data: dict) -> dict:
    fixtures = json.loads((ROOT / "fixtures.json").read_text(encoding="utf-8"))
    key = data["kind"]
    if key not in fixtures:
        raise RuntimeError("Демо-режим знает только подростка и взрослого. "
                           "Для других — запусти с --live и ANTHROPIC_API_KEY.")
    return fixtures[key]


# ---------- сохранение ----------
def save_outputs(folder: Path, result: dict):
    (folder / OUT_ANALYSIS).write_text(result["analysis"], encoding="utf-8")
    (folder / OUT_REPORT).write_text(result["report"], encoding="utf-8")


# ---------- оркестрация ----------
def process_folder(folder: Path, live: bool, force: bool):
    if (folder / OUT_ANALYSIS).exists() and not force:
        return ("skip", folder.name, "анализ уже есть")
    data = read_inputs(folder)
    if not data["report"]:
        return ("skip", folder.name, "нет отчёта")
    try:
        result = analyze_live(data) if live else analyze_demo(data)
        save_outputs(folder, result)
        return ("ok", folder.name, data["kind"])
    except Exception as e:
        return ("error", folder.name, str(e))


def main():
    ap = argparse.ArgumentParser(description="Профориентация — агент обработки папок")
    ap.add_argument("--clients-dir", default=str(DEFAULT_CLIENTS_DIR))
    ap.add_argument("--folder")
    ap.add_argument("--live", action="store_true")
    ap.add_argument("--force", action="store_true")
    args = ap.parse_args()

    base = Path(args.clients_dir)
    if not base.exists():
        sys.exit(f"❌ Каталог клиентов не найден: {base}")

    folders = ([base / args.folder] if args.folder else
               [p for p in base.iterdir() if p.is_dir()])

    mode = "LIVE (Claude API)" if args.live else "DEMO (без ключей)"
    print(f"\n🧭 Профориентация — агент. Режим: {mode}")
    print(f"📂 Клиенты: {base}\n" + "─" * 52)

    done, skipped, errors = [], [], []
    for folder in sorted(folders):
        status, a, b = process_folder(folder, args.live, args.force)
        if status == "ok":
            done.append((a, b)); print(f"✅ {a}: анализ + итоговый отчёт ({b})")
        elif status == "skip":
            skipped.append((a, b)); print(f"⏭️  {a}: {b}")
        else:
            errors.append((a, b)); print(f"❗ {a}: {b}")

    print("─" * 52)
    print(f"Готово. Обработано: {len(done)}, пропущено: {len(skipped)}, ошибок: {len(errors)}")


if __name__ == "__main__":
    main()
