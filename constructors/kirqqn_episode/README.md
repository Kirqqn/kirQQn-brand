# kirQQn — титри епізодів (Python)

Той самий макет, що й у веб-конструкторі «Титри kirQQn». Перевірено: PNG збігаються з веб-версією майже попіксельно (середня різниця менше 1 з 255 на піксель).

| Файл | Що це |
|---|---|
| `kirqqn_episode.py` | Генератор карток і перевірка за гайдлайном, зокрема щільності |
| `ГАЙДЛАЙН_ЕПІЗОДИ.md` | Усі правила: HUD, місця, картки, переклад, меми, ліміти, Resolve |
| `GPT_INSTRUCTIONS.md` | Інструкція для ChatGPT |
| `fonts/`, `assets/` | Шрифти й шари бренду — не чіпати |
| `examples/episode_example.txt` | Приклад сценарію титрів |

## На своєму комп'ютері (Windows)

Python 3 з python.org, один раз `pip install pillow`. У папці `kirqqn_episode`:

```
python kirqqn_episode.py check examples\episode_example.txt
python kirqqn_episode.py render examples\episode_example.txt --out D:\LetsPlay\titles\ep16
python kirqqn_episode.py render D:\LetsPlay\markers\ep16.edl --out D:\LetsPlay\titles\ep16
python kirqqn_episode.py counters --out D:\LetsPlay\titles\counters
```
