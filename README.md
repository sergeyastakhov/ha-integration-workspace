# HomeAssistantDev

Рабочая область для разработки интеграций устройств для
[Home Assistant](https://www.home-assistant.io/) и библиотек протоколов к ним.

Здесь живут **правила и сквозные требования**, по которым делается любая интеграция. Код самих
интеграций и библиотек разрабатывается в этой же папке, но публикуется в отдельных репозиториях —
по одному на компонент, как требует Marketplace.

- Правила проекта: [`AGENTS.md`](AGENTS.md) — обязательны для людей и агентов.
- Сквозные требования: [`openspec/specs/conventions/`](openspec/specs/conventions/) — 12
  возможностей, от владения соединением до порядка выпуска.

## Из чего состоит работа

| Часть | Где | Репозиторий |
|---|---|---|
| Правила и общие требования | `AGENTS.md`, `openspec/specs/conventions/` | этот |
| Инструменты разработки | `tools/` | этот |
| Интеграция `mtdx62` | `integrations/mtdx62/` | [`ha-mtdx62`](https://github.com/sergeyastakhov/ha-mtdx62) |
| Библиотека MTDx62 | `libraries/mtdx62-modbus-library/` | [`mtdx62-modbus-library`](https://github.com/sergeyastakhov/mtdx62-modbus-library) |

Папки `integrations/` и `libraries/` в этот репозиторий не входят: они перечислены в `.gitignore`,
а их содержимое живёт в собственных репозиториях. Скрипт
[`tools/publish.py`](tools/publish.py) переносит папку рабочей области в её репозиторий.

## Как начать новую интеграцию

1. Прочитайте [`AGENTS.md`](AGENTS.md) — процесс, технические правила, путь к Core.
2. Проверьте, что домен свободен: его нет в `homeassistant/components/` Core и в каталоге
   Marketplace. Одна интеграция обслуживает несколько моделей одного производителя или протокола;
   новая интеграция нужна при другом протоколе или другой экосистеме.
3. Проверьте, какие сквозные требования уже покрывают ваш случай — особенно
   [`modbus-setup`](openspec/specs/conventions/modbus-setup/spec.md) и
   [`modbus-transport`](openspec/specs/conventions/modbus-transport/spec.md). Не переписывайте их
   у себя: в спецификации интеграции остаётся только специфика устройства.
4. Если правило нужно новое и оно пригодится другим интеграциям, поднимите его в
   `openspec/specs/conventions/` отдельным изменением. Частную формулировку из `AGENTS.md` при
   этом удалите.
5. Создайте `integrations/<domain>/` со своим корнем `openspec/`: три обязательные темы —
   подключение, сущности, диагностика. Затем протокол в отдельную библиотеку
   `libraries/<name>-library/`, а в интеграции останется связка с Home Assistant.
6. Перед выпуском пройдите проверку на живом Home Assistant по
   [`live-verification`](openspec/specs/conventions/live-verification/spec.md) и запишите результат
   в `docs/live-check.md` интеграции.

## Как доработать существующую

Папка компонента уже лежит в рабочей области, поэтому работа идёт как обычно: изменение в его
корне OpenSpec, код, тесты, `quality_scale.yaml`. Публикация — из `tools/`:

```bash
python tools/publish.py list
python tools/publish.py ha-mtdx62 --message "Explain a port held by a YAML setup"
```

Релиз (тег, заметки, PyPI) выполняют workflow в репозитории компонента.

## Требования и изменения

Три корня OpenSpec, три уровня требований:

- `openspec/` — сквозные требования, общие для всех интеграций и библиотек;
- `integrations/<domain>/openspec/` — требования конкретной интеграции;
- `libraries/<name>/openspec/` — контракт конкретной библиотеки.

Команды выполняются в каталоге нужного корня: CLI берёт ближайший `openspec/`.

```bash
openspec list --specs
openspec validate --specs
openspec new change "add-something"
openspec validate "add-something" --strict
openspec archive "add-something" --yes
```

Правило, найденное на одном устройстве, живёт сначала в корне интеграции, а когда становится ясно,
что оно общее, — поднимается в `openspec/specs/conventions/` и из локальных правил удаляется.
Именно так появились `modbus-setup`, `config-flow-errors` и `live-verification`.

## Лицензия

MIT, см. [`LICENSE`](LICENSE). Код интеграций и библиотек лицензируется в их репозиториях.
