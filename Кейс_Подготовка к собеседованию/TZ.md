# ТЗ для Claude Code
## Агент: Career Consulting Intake Processor

---

## Задача одной строкой

Создать Python-агента, который принимает транскрипт звонка с клиентом (и опционально CV),
анализирует их через Claude API, создаёт структурированный Client Profile в Google Docs
и готовит черновик письма-предложения в Gmail.

---

## Что агент должен уметь делать

### Входные данные (агент принимает):
- Текстовый файл с транскриптом звонка (`transcript.txt`)
- Опционально: PDF или DOCX с CV клиента
- Имя клиента и email (из командной строки или из транскрипта)

### Шаги агента (по порядку):

**Шаг 1 — Прочитать транскрипт**
Открыть файл, прочитать содержимое.

**Шаг 2 — Если есть CV — прочитать CV**
Извлечь текст из PDF или DOCX.

**Шаг 3 — Отправить в Claude API**
Собрать промпт из транскрипта + CV (если есть).
Получить структурированный JSON с анализом клиента:
- имя, роль, уровень seniority, индустрия
- цели (краткосрочные / долгосрочные)
- боли и страхи
- сильные стороны
- рекомендуемый пакет услуг (single session / пакет 3)
- черновик предложения (2–3 предложения)

**Шаг 4 — Создать папку в Google Drive**
Папка: `Clients / [Имя клиента] - [дата]`
Подпапки: `CV`, `Sessions`, `Reports`

**Шаг 5 — Создать Google Doc "Client Profile"**
Из шаблона (ID шаблона задаётся в конфиге).
Заполнить разделы данными из анализа Claude.

**Шаг 6 — Если CV загружен — сохранить в папку CV**
Скопировать файл в подпапку `CV` клиента.

**Шаг 7 — Создать черновик письма в Gmail**
Тема: `Proposal for [Имя клиента]`
Тело: черновик предложения из анализа Claude.
Адресат: email клиента.

**Шаг 8 — Вывести итог в терминал**
```
✅ Client profile created: [ссылка на Google Doc]
✅ Draft email ready in Gmail
📁 Client folder: [ссылка на папку Drive]
```

---

## Технический стек

```
Python 3.11+
anthropic          # Claude API
google-auth        # авторизация Google
google-api-python-client  # Drive + Docs + Gmail API
python-docx        # чтение DOCX
PyMuPDF (fitz)     # чтение PDF
python-dotenv      # .env для ключей
```

---

## Файловая структура проекта

```
career-intake-agent/
├── .env                    # API ключи (не коммитить!)
├── config.py               # настройки (ID шаблона, email и т.д.)
├── agent.py                # главный файл, точка входа
├── modules/
│   ├── reader.py           # чтение транскрипта и CV
│   ├── analyzer.py         # вызов Claude API, парсинг ответа
│   ├── drive.py            # создание папок и файлов в Drive
│   ├── docs.py             # создание и заполнение Google Doc
│   └── gmail.py            # создание черновика письма
├── templates/
│   └── prompts.py          # промпты для Claude
└── requirements.txt
```

---

## .env файл (шаблон)

```
ANTHROPIC_API_KEY=sk-ant-...
GOOGLE_CREDENTIALS_PATH=credentials.json
TEMPLATE_DOC_ID=1abc...xyz          # ID шаблона Client Profile в Drive
CONSULTANT_EMAIL=consultant@gmail.com
```

---

## Промпт для Claude (из templates/prompts.py)

```python
INTAKE_ANALYSIS_PROMPT = """
You are an expert career consultant assistant.

Analyze the following intake call transcript{cv_section} and return a JSON object with this exact structure:

{{
  "client": {{
    "name": "...",
    "current_role": "...",
    "seniority": "junior|mid|senior|lead|executive",
    "industry": "...",
    "location": "..."
  }},
  "goals": {{
    "short_term": "...",
    "long_term": "..."
  }},
  "pain_points": ["...", "..."],
  "fears": ["...", "..."],
  "strengths": ["...", "..."],
  "gaps": ["...", "..."],
  "recommended_package": "single_session|package_3",
  "package_rationale": "...",
  "proposal_draft": "..."
}}

TRANSCRIPT:
{transcript}

{cv_text}

Return only valid JSON. No markdown, no explanation.
"""
```

---

## Пример запуска

```bash
# Только с транскриптом
python agent.py --transcript transcript.txt --email client@gmail.com

# С транскриптом и CV
python agent.py --transcript transcript.txt --cv cv_francesco.docx --email client@gmail.com
```

---

## Что НЕ входит в MVP (можно добавить позже)

- Интеграция с Calendly (триггер по webhook)
- Автоматическое скачивание транскрипта из Google Meet
- Cappfinity reminder
- Versioning CV
- Dashboard трекинг клиентов

---

## Чем агент на Claude Code отличается от Make.com

| | Make.com | Claude Code агент |
|---|---|---|
| Кто строит | Визуально, без кода | Python-разработчик или Claude Code |
| Гибкость | Ограничена модулями | Любая логика |
| Условия и ветвления | Базовые | Сложные (if/else, циклы, обработка ошибок) |
| Отладка | Трудно | Полный контроль |
| Стоимость | $9–16/мес за Make | Только API (несколько центов за запуск) |
| Для кого | Консультант сам | Нужен разработчик или Claude Code |

**Агент — это когда система сама принимает решения, а не просто выполняет шаги.**
В этом примере: если CV не загружен — агент пропускает шаги 2 и 6, но продолжает работу.
Если Claude вернул ошибку — агент ретраит. Make.com просто упадёт.

---

## Как использовать это ТЗ с Claude Code

Открываешь Claude Code в терминале и пишешь:

```
Реализуй агента по этому ТЗ: [вставляешь содержимое этого файла]

Начни с создания структуры проекта и модуля analyzer.py.
После каждого модуля жди подтверждения перед следующим.
```

Claude Code сам напишет код, запустит, исправит ошибки.
Весь проект — около 200–300 строк кода, 1–2 часа работы агента.
