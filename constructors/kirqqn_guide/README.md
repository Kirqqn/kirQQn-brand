# kirQQn — гайди (Python)

Той самий макет, що й у веб-конструкторі «Гайди kirQQn». Перевірено: картки збігаються з веб-конструктором майже попіксельно (середня різниця менше 2 з 255 на піксель).

## Що в папці

| Файл | Що це |
|---|---|
| `kirqqn_guide.py` | Генератор карток і перевірка за гайдлайном |
| `ГАЙДЛАЙН_ГАЙДИ.md` | Усі правила гайдів: сітка, текст, колір, частини, Resolve |
| `GPT_INSTRUCTIONS.md` | Інструкція для ChatGPT |
| `fonts/` | Unbounded Black, JetBrains Mono Medium і Bold + ліцензії OFL |
| `assets/` | Фон, знак QQ, стікери емоцій — шари бренду, не чіпати |
| `examples/` | Приклад `guide_example.json` з двома кадрами |

## На своєму комп'ютері (Windows)

1. Python 3 з python.org (галочка «Add Python to PATH»), один раз `pip install pillow`.
2. У папці `kirqqn_guide`:

```
python kirqqn_guide.py check examples\guide_example.json
python kirqqn_guide.py render examples\guide_example.json --out D:\LetsPlay\guides\coen
python kirqqn_guide.py grid D:\скріни\xante_05.png
```

`render` кладе в папку: `full/` (готові PNG), `resolve_overlay/` (PNG з прозорим вікном під відео), `preview.jpg` і `ЯК_ЗІБРАТИ.txt`.
