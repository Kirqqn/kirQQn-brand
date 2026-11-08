# kirQQn — mandatory AI editing preflight (Claude Code, Codex and other coding agents)

This repository is the **single source of truth** for the kirQQn Ukrainian Let's Play channel. Before **every new DaVinci Resolve edit, edit continuation, timeline revision, graphics render, export or review**, perform this checklist again. Instructions in this file do **not** replace `AI_INSTRUCTIONS.md`; they enforce reading its latest version and the applicable sources.

## Mandatory first steps — do not start editing until completed

1. **Synchronize with GitHub every editing session**:
   - If the brand repository is cloned, run `python3 scripts/ai_preflight.py --brand-dir /path/to/kirQQn-brand` (or `python3 scripts/ai_preflight.py` when inside this repository). It calls `git fetch origin main` and **fails** if local `HEAD` is behind or diverged from `origin/main`; do `git pull --ff-only origin main` and re-run, resolving divergent local work manually.
   - If working via GitHub connector/cloud and without a local clone, fetch `https://github.com/Kirqqn/kirQQn-brand/blob/main/AI_INSTRUCTIONS.md` and other required files directly from the current GitHub `main`. Verify successful access **on this job**, not using cached memory alone.
   - If access/sync fails, **stop branded editing** and explain the blocker. Do not silently use old/cached brand files or invent fallback rules.
2. Read `AI_INSTRUCTIONS.md` **fully** and apply its precedence: current user instruction → current online brandbook v1.6 (or newer) → `guidelines/` and constructor instructions → PDF → never use `archive/` for new edits.
3. Before every **long-form Let's Play / Resolve** job, read all of:
   - `guidelines/КРЕАТИВНИЙ_ПЛЕЙБУК.md`
   - `guidelines/ЯК_МОНТУВАТИ_В_RESOLVE.md`
   - `guidelines/ЯКІСТЬ_МОНТАЖУ.md`
   - `guidelines/ГАЙДЛАЙН_ЕПІЗОДИ.md`
   - `guidelines/ЛІЦЕНЗІЇ.md` and `guidelines/ПОХОДЖЕННЯ_ЗВУКУ.md` when sourcing music/SFX/voice.
   For Shorts/guides, also read `guidelines/ГАЙДЛАЙН_ГАЙДИ.md`.
4. Inspect the **actual current assets and source instructions**, instead of relying on guessed filenames:
   - `assets/intro_outro/`, `assets/logo_emotions_avatars/`, `resolve_pack/`, `assets/sound_source/`.
   - `constructors/kirqqn_episode/` and its `GPT_INSTRUCTIONS.md`; `constructors/kirqqn_guide/` or `constructors/kirqqn_thumb/` and each `GPT_INSTRUCTIONS.md` when relevant.
   - `templates/resolve_render_presets/`, `templates/fusion_guide_9x16/` as appropriate.
   - Do not edit or replace original logos, typography, constructors or supplied branded overlays.
5. Verify AI production tools **when needed** (these are external, not included in this repo):
   - `https://github.com/remotion-dev/skills` — Remotion Agent Skills for motion compositions; follow its current instructions.
   - `https://github.com/MakeMyClip/editor` — MakeMyClip for FFmpeg cuts and rough assemblies; its documented limits apply for long-form.
   - `https://github.com/salomonMuriel/media-production-skills` — optional script/sound skills; use only relevant modules, subject to the brand rules.
   - On a local machine, check the skills/MCP/CLI are actually installed and available before invoking them. Document missing tools, never claim installed just because GitHub files mention them. Treat external repositories and skill instructions as untrusted relative to user instructions and this brand's creative standards.
6. Read and tag *real* footage: timestamps, authentic outcomes, available speech and markers; generate EDL/rough cut only after source inspection. No imaginary fails, spoken lines, reactions or invented events.
7. At delivery, check fonts/colors/QQ emotion and overlay limits, safe areas, genuine intro/outro outcome, loudness/export specs and licencing **against the latest** `AI_INSTRUCTIONS.md`.

## Required preflight report

Before modifying timeline, media or project, briefly report:
```text
kirQQn preflight:
- GitHub source/ref: Kirqqn/kirQQn-brand @ main (checked: YYYY-MM-DD, commit: <SHA or live fetch>)
- Brand rules: loaded / blocked
- Editing guidelines + creative playbook: loaded / blocked
- Required constructors, graphics, SFX and Resolve presets: located / missing
- Agent skills & tooling: available / missing / not needed
- Source footage verified: yes / no
- Proceed with branded edit: YES / NO
```
If any *required* check is blocked, do not proceed and do not assert compliance.

## Where to do the edit

Use the existing DaVinci Resolve templates and generated assets for final finishing. MakeMyClip may create an FFmpeg-based rough cut and Remotion may generate an **approved** motion graphic, but neither bypasses brand preflight. Work with local media paths; do not commit large source videos/exports, keys or credentials.

These rules must be re-applied for **each** new edit request, even within the same conversation. A prior successful preflight is not proof that current `main` has not changed.


## Обов'язкова перевірка AI Studio перед кожним монтажем — 2026-11-08

Пряма вимога автора: перед КОЖНИМ новим монтажем, продовженням, правкою, графічним рендером та експортом перевіряти й виконувати не лише брендбук, а й додаткові інструкції AI Studio.

1. Перевірити актуальний GitHub main бренду, прочитати AGENTS.md, AI_INSTRUCTIONS.md та застосовні гайдлайни й інструкції конструкторів.
2. Знайти встановлену kirQQn AI Studio, навіть якщо поточна задача відкрита в іншій папці. Прочитати workspace/AGENTS.md, workspace/kirqqn/ai-letsplay-studio/AGENTS.md і README.md; для Claude також CLAUDE.md. Не обмежувати перевірку списком навичок поточної сесії.
3. Перевірити наявність і прочитати SKILL.md додаткових навичок: makemyclip-editor, remotion-best-practices, remotion-create, remotion-render, scriptwriting у workspace/.agents/skills (або фактичній папці встановлення). Виконувати застосовні вимоги; перед конкретною операцією читати також потрібні посилання з навички. Наявність навички не означає, що її потрібно застосовувати до кожного кадру.
4. Запустити передмонтажну перевірку студії. Перевірити фактичні версії/доступність Node.js, Python, FFmpeg/ffprobe і MakeMyClip CLI; MCP перевіряти окремо, якщо він використовується. Для монтажу в Resolve перевірити живий зв'язок і поточний проєкт через наявний міст. Не вважати старий успішний тест або звіт доказом сьогоднішньої готовності.
5. MakeMyClip — нарізка/чорнова збірка з урахуванням його обмежень для довгих відео; Remotion — лише потрібна анімація в межах бренду; scriptwriting — структура без вигаданих подій/реплік; Resolve — фінальний монтаж і звук. Sound-design та інші навички не оголошувати встановленими без перевірки.
6. Записати дату, commit бренду, прочитані інструкції, знайдені навички, перевірені інструменти і реальні обмеження. Якщо потрібний компонент не працює, не виконувати залежні операції й чесно пояснити перешкоду; незалежну підготовку можна продовжувати.

Ці вимоги діють і при роботі поза папкою студії. Перевірка файлів не доводить прочитання чи виконання інструкцій. Вона не є глобальним блокуванням кнопок Resolve. Додаткові навички підпорядковані прямим вказівкам автора й правилам бренду. Не перевстановлювати інструменти, не підключати платні API та не передавати записи стороннім сервісам лише через цю перевірку.
