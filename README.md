# kirQQn: бренд-комплект

Тут зібрано все для оформлення контенту kirQQn, українського каналу летсплеїв: брендбук, гайдлайни, логотипи, емоції QQ, шрифти, інтро й аутро, оверлеї для DaVinci Resolve, конструктори обкладинок і гайдів, пресети рендеру.

> **AI, почни звідси:** [`AI_INSTRUCTIONS.md`](AI_INSTRUCTIONS.md) — правила та порядок джерел.
> Прямі посилання на файли: `https://raw.githubusercontent.com/Kirqqn/kirQQn-brand/main/<шлях>`

## Структура

| Папка | Що всередині |
|---|---|
| [`brandbook/`](brandbook/) | `kirQQn_brandbook.pdf`; `web/` — знімок онлайн-брендбука v1.6 з картинками й відео; `archive/` — старі версії PDF |
| [`guidelines/`](guidelines/) | Гайдлайни гайдів, епізодів і монтажу в Resolve, якість монтажу, ліцензії, походження звуку |
| [`assets/logo_emotions_avatars/`](assets/logo_emotions_avatars/) | `01_logo` — вордмарк і знак QQ (SVG/PNG); `02_qq_emotions` — 7 емоцій; `03_avatars` |
| [`assets/youtube_instagram/`](assets/youtube_instagram/) | Банер і водяний знак YouTube, приклади обкладинок; пости, сторіс і хайлайти Instagram (UA та `_en`) |
| [`assets/fonts/`](assets/fonts/) | Unbounded, JetBrains Mono, Golos Text з ліцензіями OFL |
| [`assets/intro_outro/`](assets/intro_outro/) | Інтро full 6,6 с і short 3,6 с, аутро win/lose 12 с, 1080p60 |
| [`assets/sound_source/`](assets/sound_source/) | Python-скрипти, що відтворюють звук інтро й аутро |
| [`assets/demos/`](assets/demos/) | Демо-відео епізоду та гайду |
| [`resolve_pack/`](resolve_pack/) | Прозорі оверлеї ProRes 4444 2560×1440: `qq_pop_*`, `plus_one_qq`, `skip_hud`, `glitch_stinger`, `guide_step_wipe`, handle-баги, SFX; `episode/` — картки, штампи, stinger, callout, punch, freeze |
| [`constructors/kirqqn_thumb/`](constructors/kirqqn_thumb/) | Python-конструктор обкладинок YouTube 1280×720 |
| [`constructors/kirqqn_guide/`](constructors/kirqqn_guide/) | Конструктор карток вертикальних гайдів, v1.3 |
| [`constructors/kirqqn_episode/`](constructors/kirqqn_episode/) | Конструктор графіки довгих епізодів |
| [`constructors/web/`](constructors/web/) | Знімки веб-конструкторів, відкриваються в браузері: обкладинки для всіх форматів (YouTube, вертикальні, Instagram), титри епізодів, гайди |
| [`templates/`](templates/) | Пресети рендеру Resolve (XML), шаблон Fusion для гайду 9:16 |
| [`archive/`](archive/) | Застарілий візуальний патерн Dawnwalker. Тільки історія, для нових робіт не використовувати |

## Онлайн-версії

- Брендбук: https://claude.ai/artifact/19tnt5oyNNGCSxxq2p7DDL
- Конструктор обкладинок: https://claude.ai/artifact/A7sXWUUqKfV3M4jMqJQ148
- Титри епізодів: https://claude.ai/artifact/XJRUVtEiW1AWCbMrpyTyMM
- Гайди: https://claude.ai/artifact/HfbybHdFD4qqxQZJh6vLxg

Знімки в цьому репозиторії зроблено 2026-11-04 (брендбук і конструктор обкладинок оновлено того ж дня, пізніше). Якщо онлайн-версія новіша, вона має пріоритет.

## Як користуватися конструкторами

Кожен конструктор має `GPT_INSTRUCTIONS.md` і `README.md`. Потрібні Python 3 і Pillow. Код, шрифти й assets конструкторів не змінюй: саме вони гарантують відповідність брендбуку.

## Права

Шрифти розповсюджуються за SIL Open Font License. Звук бренду синтезований програмно. Логотип, емоції QQ та айдентика належать каналу kirQQn: використовувати їх можна лише для матеріалів самого каналу.
