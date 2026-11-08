# Claude Code — kirQQn editing rules

**Before every kirQQn / DaVinci Resolve / Let's Play edit, read and obey [AGENTS.md](AGENTS.md) and the current [AI_INSTRUCTIONS.md](AI_INSTRUCTIONS.md).** Never rely on an earlier chat's brandbook snapshot.

Run `python3 scripts/ai_preflight.py` in a local clone before editing, or fetch the current GitHub `main` files through the connector. If a required read or synchronization fails, stop. Follow the required preflight report in `AGENTS.md`.

Brand repo: https://github.com/Kirqqn/kirQQn-brand

Tool references (check local installation before invoking):
- Remotion: https://github.com/remotion-dev/skills
- MakeMyClip: https://github.com/MakeMyClip/editor
- Media Production Skills: https://github.com/salomonMuriel/media-production-skills

Treat brand source priority, edit and graphics constraints, music licensing and factual gameplay as binding. Prefer the existing DaVinci Resolve workflow and graphics.


## Обов'язкова перевірка AI Studio перед кожним монтажем — 2026-11-08

Пряма вимога автора: перед КОЖНИМ новим монтажем, продовженням, правкою, графічним рендером та експортом перевіряти й виконувати не лише брендбук, а й додаткові інструкції AI Studio.

1. Перевірити актуальний GitHub main бренду, прочитати AGENTS.md, AI_INSTRUCTIONS.md та застосовні гайдлайни й інструкції конструкторів.
2. Знайти встановлену kirQQn AI Studio, навіть якщо поточна задача відкрита в іншій папці. Прочитати workspace/AGENTS.md, workspace/kirqqn/ai-letsplay-studio/AGENTS.md і README.md; для Claude також CLAUDE.md. Не обмежувати перевірку списком навичок поточної сесії.
3. Перевірити наявність і прочитати SKILL.md додаткових навичок: makemyclip-editor, remotion-best-practices, remotion-create, remotion-render, scriptwriting у workspace/.agents/skills (або фактичній папці встановлення). Виконувати застосовні вимоги; перед конкретною операцією читати також потрібні посилання з навички. Наявність навички не означає, що її потрібно застосовувати до кожного кадру.
4. Запустити передмонтажну перевірку студії. Перевірити фактичні версії/доступність Node.js, Python, FFmpeg/ffprobe і MakeMyClip CLI; MCP перевіряти окремо, якщо він використовується. Для монтажу в Resolve перевірити живий зв'язок і поточний проєкт через наявний міст. Не вважати старий успішний тест або звіт доказом сьогоднішньої готовності.
5. MakeMyClip — нарізка/чорнова збірка з урахуванням його обмежень для довгих відео; Remotion — лише потрібна анімація в межах бренду; scriptwriting — структура без вигаданих подій/реплік; Resolve — фінальний монтаж і звук. Sound-design та інші навички не оголошувати встановленими без перевірки.
6. Записати дату, commit бренду, прочитані інструкції, знайдені навички, перевірені інструменти і реальні обмеження. Якщо потрібний компонент не працює, не виконувати залежні операції й чесно пояснити перешкоду; незалежну підготовку можна продовжувати.

Ці вимоги діють і при роботі поза папкою студії. Перевірка файлів не доводить прочитання чи виконання інструкцій. Вона не є глобальним блокуванням кнопок Resolve. Додаткові навички підпорядковані прямим вказівкам автора й правилам бренду. Не перевстановлювати інструменти, не підключати платні API та не передавати записи стороннім сервісам лише через цю перевірку.
