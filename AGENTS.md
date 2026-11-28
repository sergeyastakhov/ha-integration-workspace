# AGENTS.md — правила разработки интеграций устройств для Home Assistant

Этот файл задаёт обязательные правила для людей и ИИ-агентов, которые работают в этом
рабочем пространстве. Цель — создать набор интеграций устройств для
[Home Assistant](https://www.home-assistant.io/). Они распространяются через
[Marketplace](https://www.home-assistant.io/integrations/marketplace) и с самого начала
пишутся так, чтобы их можно было перенести в
[Home Assistant Core](https://github.com/home-assistant/core), когда они достигнут нужного уровня по
[Integration Quality Scale](https://contributors.home-assistant.io/core/quality-scale/).

Первоисточники (при расхождении с этим файлом прав первоисточник, а этот файл нужно исправить):

- Документация для контрибьюторов Core: <https://contributors.home-assistant.io/core/>
- Документация для авторов Marketplace: <https://contributors.home-assistant.io/marketplace/>
- Основной репозиторий и его правила для агентов: <https://github.com/home-assistant/core> (`AGENTS.md`, `AI_POLICY.md`)
- OpenSpec: <https://github.com/Fission-AI/OpenSpec/>, <https://openspec.dev/docs>

---

## 1. Базовые принципы

1. **Сначала спецификация, потом код.** Любое изменение поведения начинается с change-предложения
   в OpenSpec (раздел 3). Код без утверждённого change не пишется. Исключения: опечатки,
   форматирование и обновление зависимостей без изменения поведения.
2. **Пишем под Core с первого дня.** Custom-интеграция строится по тем же правилам, что и
   интеграция в Core. Отличия, которых требует Marketplace, сведены в раздел 6 и держатся
   минимальными, чтобы перенос в Core был механическим.
3. **Протокол устройства — в отдельной библиотеке.** Вся работа с устройством (сеть, протокол,
   разбор данных) живёт в отдельной Python-библиотеке, опубликованной на PyPI. В интеграции
   остаётся только связка с Home Assistant. Этого требуют Core и правила Platinum
   (`async-dependency`, `inject-websession`, `dependency-transparency`).
4. **Ответственность за изменение несёт человек.** Мы соблюдаем
   [Open Home Foundation AI Policy](https://github.com/home-assistant/core/blob/dev/AI_POLICY.md):
   агент не открывает issue и PR и не публикует комментарии от имени пользователя без его проверки.
   Человек должен понимать каждое изменение и уметь его объяснить.
5. **Безопасность и приватность.** Код работает в чужих домах. Никакой телеметрии,
   никаких скрытых облачных вызовов, секреты не попадают в логи и диагностику (раздел 8).
6. **Локальное управление в приоритете.** Если устройство поддерживает локальный API
   (`local_push` / `local_polling`), выбираем его, а не облако.

---

## 2. Структура рабочего пространства

Marketplace требует, чтобы **один репозиторий содержал одну интеграцию**. Поэтому при публикации
рабочее пространство делится: общие спецификации остаются здесь, а каждая интеграция и каждая
библиотека уезжают в свой git-репозиторий.

```
HomeAssistantDev/
├── AGENTS.md                      # этот файл
├── README.md                      # что это за рабочая область и с чего начать
├── tools/                         # publish.py: папка компонента → его репозиторий
├── .github/workflows/ci.yml       # проверка сквозных требований
├── openspec/                      # корень СКВОЗНЫХ требований
│   ├── config.yaml
│   ├── specs/conventions/         # правила, общие для всех интеграций и библиотек
│   │   ├── modbus-transport/
│   │   ├── modbus-setup/
│   │   ├── config-flow-errors/
│   │   ├── live-verification/
│   │   ├── dependency-and-test-stack/
│   │   ├── entity-availability/
│   │   ├── entity-identity/
│   │   ├── diagnostics/
│   │   ├── localization/
│   │   ├── marketplace-packaging/
│   │   ├── pypi-packaging/
│   │   ├── module-naming/
│   │   └── device-documentation/
│   └── changes/                   # предложения изменений к самим сквозным правилам
├── integrations/                  # в репозиторий рабочей области не входит
│   ├── README.md                  # указатель на репозитории интеграций
│   └── <domain>/                  # репозиторий ha-<domain> → GitHub → Marketplace
│       ├── openspec/              # корень требований ЭТОЙ интеграции
│       │   ├── config.yaml
│       │   ├── specs/             # действующие требования интеграции
│       │   └── changes/           # предложения изменений интеграции
│       ├── custom_components/<domain>/
│       │   ├── __init__.py
│       │   ├── manifest.json
│       │   ├── config_flow.py
│       │   ├── const.py
│       │   ├── coordinator.py
│       │   ├── entity.py          # базовый класс сущностей
│       │   ├── diagnostics.py
│       │   ├── quality_scale.yaml
│       │   ├── icons.json
│       │   ├── services.yaml      # если есть actions
│       │   ├── strings.json       # исходник переводов (для будущего переноса в Core)
│       │   ├── translations/en.json  # обязательно для custom; плюс ru.json
│       │   ├── brand/             # icon.png, logo.png (и @2x, dark_ варианты)
│       │   └── <platform>.py      # sensor.py, switch.py, ...
│       ├── tests/                 # pytest; структура как tests/components/<domain> в Core
│       ├── docs/                  # проверка в HA, известные ограничения, скриншоты
│       ├── hacs.json
│       ├── README.md
│       ├── LICENSE
│       ├── pyproject.toml         # ruff, mypy, pytest
│       └── .github/workflows/     # hassfest, HACS action, lint, tests
└── libraries/                   # в репозиторий рабочей области не входит
    ├── README.md                  # указатель на репозитории библиотек
    └── <name>/                    # отдельный репозиторий → PyPI
        ├── openspec/              # корень требований ЭТОЙ библиотеки
        │   ├── config.yaml
        │   ├── specs/             # контракт библиотеки: регистры, разбор, ошибки
        │   └── changes/
        ├── docs/                  # описание устройства: факты, руководство, сканы
        └── src/<package>/         # код библиотеки, тесты, pyproject
```

Правила:

- **Три уровня требований, три корня OpenSpec.** `openspec/specs/conventions/` — то, что одинаково
  для всех интеграций и библиотек. `integrations/<domain>/openspec/` — требования конкретной
  интеграции. `libraries/<name>/openspec/` — контракт конкретной библиотеки. Команды OpenSpec
  выполняются в каталоге нужного корня: CLI берёт ближайший `openspec/`.
- **Имя модуля библиотеки не совпадает с доменом интеграции** (`conventions/module-naming`).
  Библиотека для интеграции `acme` называется, например, `acme-modbus-library` и импортируется
  как `acme_modbus_library`. Совпадение имён ломает импорт, когда рядом на пути лежит
  `custom_components/<domain>`, и заставляет `mypy` путать пакеты. Проверка — импорт библиотеки
  из корня репозитория интеграции в CI.
- **Что куда писать.** Правило, которое должно действовать на несколько интеграций, живёт в
  `conventions/` и никогда не копируется в интеграции. Разбор протокола, адреса регистров и
  семантика ошибок — в корне библиотеки. Поведение сущностей Home Assistant, мастер настройки,
  диагностика интеграции — в корне интеграции. Интеграция ссылается на контракт библиотеки, а не
  пересказывает его.
- **Документация устройства живёт рядом с кодом, который его обслуживает**
  (`conventions/device-documentation`). Протокол, карта регистров, руководство производителя и
  сканы — в `docs/` библиотеки; мастер настройки, сущности, порядок ручной проверки — в `docs/`
  интеграции. На верхнем уровне остаётся только то, что относится к нескольким устройствам:
  сквозные правила, выбор платформ, сравнение моделей. Документ об одном устройстве наверху —
  ошибка, даже если устройство пока одно.
- **Проверять надо каждый затронутый корень.** Изменение, которое проходит через границу уровней,
  — это два изменения: одно в корне библиотеки, другое в корне интеграции, со ссылкой на первое.
- **Код компонентов не входит в репозиторий рабочей области.** Папки `integrations/<domain>` и
  `libraries/<name>` лежат рядом со спецификациями, чтобы разрабатывать и проверять всё в одном
  месте, но в git рабочей области не попадают: Marketplace требует «один репозиторий — одна
  интеграция». Публикация — `tools/publish.py`: она переносит папку в её репозиторий обычным
  коммитом и не переписывает историю. Поэтому в репозитории рабочей области живут правила,
  сквозные требования и инструменты, а код — в репозиториях компонентов.
- `domain` — короткий, в `snake_case`, уникальный. Он **не должен совпадать** с доменом
  интеграции Core или известной custom-интеграции: каталог не принимает интеграции, которые
  заменяют встроенные. Перед выбором домена проверьте `homeassistant/components/` в Core и
  каталог Marketplace.
- Одна интеграция может обслуживать несколько моделей одного производителя или протокола.
  Новую интеграцию заводим только при другом протоколе или другой экосистеме.
- Рабочие директории (`.venv/`, `config/` тестового экземпляра HA, `__pycache__/`,
  `.pytest_cache/`, `.mypy_cache/`, `.ruff_cache/`, `htmlcov/`, `.coverage`) добавлены в
  `.gitignore` каждого репозитория.

---

## 3. Процесс на OpenSpec

### 3.1 Жизненный цикл изменения

| Шаг | Команда или skill | Результат |
|---|---|---|
| Исследование | `/openspec-explore` | Варианты и выбранный подход, без кода |
| Предложение | `/openspec-propose <change-id>` | `openspec/changes/<change-id>/` с `proposal.md`, `specs/`, `design.md`, `tasks.md` |
| Валидация | `openspec validate <change-id> --strict` | Нет ошибок |
| Согласование | человек проверяет предложение | Явное «утверждаю» в чате или PR |
| Реализация | `/openspec-apply-change` | Код, тесты, отмеченные пункты `tasks.md` |
| Проверка | `/openspec-verify-change` (расширенный профиль) | Код соответствует сценариям |
| Архивирование | `/openspec-archive-change` | Дельты влиты в `openspec/specs/`, change перенесён в `archive/` |

### 3.2 Правила для артефактов

- `change-id` пишется в kebab-case и начинается с глагола, с префиксом домена:
  `add-acme-thermostat-climate`, `fix-acme-reconnect-backoff`.
- **`proposal.md`** содержит: зачем нужно изменение, что меняется, затронутые домены и платформы,
  влияние на пользователя (breaking change?), целевой tier quality scale.
- **`specs/<capability>/spec.md`** содержит дельты `## ADDED / MODIFIED / REMOVED / RENAMED Requirements`.
  Каждое требование сформулировано с SHALL/MUST и имеет хотя бы один `#### Scenario:` в форме
  `- **WHEN** … - **THEN** …`. Сценарии описывают наблюдаемое поведение в HA: состояния
  сущностей, шаги config flow, ошибки, repair issues, а не внутреннюю реализацию.
- **`design.md`** содержит: модель данных устройства; карту «функция устройства → платформа HA →
  `device_class` / `state_class` / единицы → `EntityCategory` → enabled by default»;
  стратегию обновления (push/poll, интервал, координатор); обработку ошибок и недоступности;
  `unique_id` устройства, сущностей и config entry; поля config flow; затрагиваемые правила
  quality scale.
- **`tasks.md`** — нумерованный чек-лист. Тесты идут отдельными пунктами рядом с кодом,
  а не в конце списка.
- Сквозные требования (например, «все интеграции SHALL поддерживать diagnostics с редактированием
  секретов») живут в `openspec/specs/conventions/`. Новые интеграции ссылаются на них, а не копируют.
- Если реализация расходится со спецификацией, сначала обновляем спецификацию в том же change,
  потом код. Нельзя молча отклоняться от спецификации.

### 3.3 Обязательные спецификации для каждой новой интеграции

Минимальный набор — три темы; дробить их на несколько capability можно и полезно, дробить
мельче одной темы — нет:

1. Подключение и жизненный цикл: config flow, добавление и удаление устройств, reauth,
   reconfigure, unload, поведение при недоступности. Если устройство работает по протоколу,
   для которого есть сквозное требование (`conventions/modbus-setup`), здесь остаётся только
   специфика устройства: модель, заводские параметры обмена, что именно читать для проверки связи.
2. Сущности: перечень, значения, единицы, доступность. Обычно делится по группам сущностей
   (`<domain>-presence`, `<domain>-environment` и так далее).
3. Диагностика: состояние устройства, версии, выгрузка диагностики, repair issues.

Отдельная спецификация `<domain>-actions` добавляется, только если интеграция регистрирует
actions. Всё, что уже описано в `conventions/`, не пересказывается — вместо этого указывается,
какое сквозное требование применяется.

### 3.4 Обязательные спецификации для каждой библиотеки

1. Контракт объекта устройства: что принимает, что отдаёт, какие подсистемы есть.
2. Карта регистров или команд протокола: адреса, разрешение, единицы, допустимые значения.
3. Семантика ошибок: какие исключения и в каких случаях, что считается «нет данных».
4. Инварианты: только чтение или только запись, отсутствие зависимости от Home Assistant,
   отсутствие собственного соединения.

Библиотека не описывает сущности Home Assistant и мастер настройки — это зона интеграции.

### 3.5 Изменение на границе уровней

Правка, которая меняет и контракт библиотеки, и поведение интеграции, оформляется двумя
изменениями: сначала в корне библиотеки, затем в корне интеграции со ссылкой на первое в разделе
задач. Одно изменение, размазанное по двум корням, не пройдёт проверку: `openspec validate`
видит только свой корень.

### 3.6 Сквозные правила и что из них следует

Общее правило живёт в `openspec/specs/conventions/`. Здесь — карта: где искать ответ на вопрос,
который возникает на каждой интеграции.

| Вопрос | Где правило |
|---|---|
| Кто открывает соединение, кто его закрывает | `conventions/modbus-transport` |
| Как провести пользователя от «добавить» до работающих сущностей на Modbus | `conventions/modbus-setup` |
| Как называть порт и что делать с YAML-настройкой `modbus` | `conventions/modbus-transport` |
| Как выглядит сообщение об ошибке мастера, что делать с введённым | `conventions/config-flow-errors` |
| Какую версию зависимости требовать и на каком стеке гонять тесты | `conventions/dependency-and-test-stack` |
| Что проверять на живом Home Assistant перед выпуском | `conventions/live-verification` |
| Когда сущность `unavailable`, а когда показывает значение | `conventions/entity-availability` |
| Как устроены `unique_id` и одна запись на устройство | `conventions/entity-identity` |
| Что вырезать в диагностике | `conventions/diagnostics` |
| Где хранятся `strings.json` и переводы, как они сверяются | `conventions/localization` |
| Что обязательно для каталога Marketplace и заметок релиза | `conventions/marketplace-packaging` |
| Что должно быть верно для README библиотеки, который PyPI показывает как описание | `conventions/pypi-packaging` |
| Как назвать модуль библиотеки и репозиторий | `conventions/module-naming` |
| Где лежит документация устройства | `conventions/device-documentation` |

Появилось наблюдение, которое повторится на других интеграциях, — оно поднимается в
`conventions/` отдельным изменением, а частная формулировка из локальных правил удаляется.


---

## 4. Технические правила Home Assistant

### 4.1 Окружение и стиль

- Python — минимальная версия, которую поддерживает текущий Home Assistant (на момент написания
  3.14; сверяйтесь с `pyproject.toml` Core). Не пишем обходные пути для старых версий.
- Форматирование и линтинг: `ruff format` и `ruff check` с конфигурацией, близкой к Core;
  `pylint` с плагинами HA при подготовке к Core; `mypy --strict` (правило `strict-typing`).
- Полные аннотации типов везде, включая параметры тестов. `Any` используется только там,
  где без него нельзя обойтись.
- Комментарии объясняют «почему», а не «что». Не добавляем разделительные комментарии
  и комментарии, которые пересказывают код.
- Константы, которые используют несколько модулей, лежат в `const.py`. Константы из одного
  модуля платформы никогда не импортируются в другой.
- Логирование: `_LOGGER = logging.getLogger(__name__)`, без f-строк в вызове
  (`_LOGGER.debug("x=%s", x)`), без точки в конце сообщения, без секретов.

### 4.2 Асинхронность

- Весь код интеграции асинхронный. Блокирующий ввод-вывод в event loop запрещён.
  Если он неизбежен — `hass.async_add_executor_job`.
- HTTP-сессию берём из HA: `async_get_clientsession(hass)` и передаём в библиотеку
  (`inject-websession`).
- Не используем `time.sleep`, синхронные `requests`, `open()` в loop.
- Методы с `@callback` или префиксом `async_` не выполняют блокирующих операций.

### 4.3 Настройка и жизненный цикл

- Настройка только через UI: **config flow** (`config-flow`), без YAML. YAML допустим
  разве что для импорта, и его нужно согласовать в спецификации.
- В config flow проверяем подключение до создания записи (`test-before-configure`),
  обеспечиваем уникальность (`async_set_unique_id` + `_abort_if_unique_id_configured`,
  правило `unique-config-entry`), используем `data_description` для каждого поля.
- В `async_setup_entry` проверяем связь с устройством (`test-before-setup`) и поднимаем
  `ConfigEntryNotReady`, `ConfigEntryAuthFailed` или `ConfigEntryError` (см. «Setup failures»).
- Данные времени выполнения храним в `entry.runtime_data` с типизированным алиасом
  `type MyConfigEntry = ConfigEntry[MyData]` (`runtime-data`). `hass.data[DOMAIN]` не используем.
- `async_unload_entry` освобождает всё: слушатели, сокеты, задачи (`config-entry-unloading`).
  Для этого — `entry.async_on_unload(...)`.
- Реализуем reauth (`reauthentication-flow`) и reconfigure (`reconfiguration-flow`).
  Discovery (zeroconf / ssdp / dhcp / bluetooth / usb) добавляем, если устройство его поддерживает
  (`discovery`, `discovery-update-info`).
- Actions регистрируются в `async_setup`, а не в `async_setup_entry` (`action-setup`).
  Ошибки в них — `ServiceValidationError` для ошибок пользователя и `HomeAssistantError`
  для ошибок устройства (`action-exceptions`). Чувствительные actions регистрируются
  через `async_register_admin_service`.

### 4.4 Получение данных

- Опрос — через `DataUpdateCoordinator` в `coordinator.py`, с разумным `update_interval`
  (`appropriate-polling`). Ошибки — `UpdateFailed`, ошибки авторизации — `ConfigEntryAuthFailed`.
- Push-устройства: подписка в `async_added_to_hass`, отписка через `async_on_remove`
  (`entity-event-setup`).
- Задаём `PARALLEL_UPDATES` в каждом модуле платформы (`parallel-updates`).
- Недоступность: если устройство не отвечает, сущности становятся `unavailable`
  (`entity-unavailable`). Об этом пишется **одна** запись в лог при потере связи и одна при
  восстановлении (`log-when-unavailable`).

### 4.5 Устройства и сущности

- Каждая сущность имеет стабильный `unique_id`, не зависящий от IP и имени
  (`entity-unique-id`). Используем серийный номер или MAC.
- `_attr_has_entity_name = True` (`has-entity-name`). Имена задаются через `translation_key`
  (`entity-translations`), иконки — через `icons.json` (`icon-translations`).
- `DeviceInfo` заполняется полностью: identifiers, connections, manufacturer, model,
  model_id, sw_version, hw_version, serial_number, а при необходимости via_device (`devices`).
- Правильно указываем `device_class`, `state_class` и единицы из `homeassistant.const`
  (`entity-device-class`), `EntityCategory.DIAGNOSTIC/CONFIG` (`entity-category`).
  Редко нужные сущности выключены по умолчанию (`entity-disabled-by-default`).
- Описания сущностей задаются через `EntityDescription` (dataclass с `value_fn`),
  без копипасты классов. Общая логика — в `entity.py` (`common-modules`).
- Новые устройства добавляются без перезапуска (`dynamic-devices`). Исчезнувшие удаляются,
  или пользователь может удалить их сам через `async_remove_config_entry_device`
  (`stale-devices`).
- Атрибуты состояния не используются как свалка данных: отдельное измерение — отдельная сущность.

### 4.6 Ошибки, переводы, ремонт

- Тексты исключений, показываемые пользователю, переводятся: `translation_domain`,
  `translation_key`, `translation_placeholders` (`exception-translations`). `str(err)` не передаём
  как placeholder.
- Repair issues (`ir.async_create_issue`) — для проблем, которые пользователь может исправить
  сам (`repair-issues`).
- Блок `try` содержит как можно меньше кода. Ловим только ожидаемые исключения библиотеки.
- Диагностика: `diagnostics.py` с `async_redact_data` для токенов, паролей, MAC, координат
  и серийных номеров (`diagnostics`).

### 4.7 Modbus-устройства

Интеграция устройства **не владеет транспортом**. Транспортом владеет интеграция `modbus` ядра,
она делит одно соединение между всеми потребителями одинаковых параметров связи и сериализует
их запросы. Полные правила — `conventions/modbus-transport`.

- Своё соединение не открываем: ни сокет, ни последовательный порт. В `async_setup_entry`
  берём юнит через `async_get_unit(hass, entry, params, unit_id)`, в мастере настройки
  проверяем связь через `async_get_temporary_unit(...)` в блоке `async with`.
- Закрывать соединение не нужно и нельзя: оно живёт, пока его держит хотя бы одна запись.
  В `async_unload_entry` освобождаем только свои задачи и слушателей.
- Библиотека устройства строится на [`modbus-connection`](https://home-assistant-libs.github.io/modbus-connection/):
  юнит передаётся в библиотеку, а не создаётся в ней. Регистры описываются декларативно
  (`Component` + поля), входные регистры помечаются `register_space = "input"`. Тесты — на
  mock-бэкенде из этой же библиотеки, без железа.
- Одна запись конфигурации — одно устройство (`integration_type: device`), адрес на шине хранится
  в данных записи. Несколько устройств на одной шине — это несколько записей, соединение они
  делят автоматически.
- Обрыв связи не повод перезагружать запись: соединение восстанавливается на следующем запросе.
  Перезагрузка нужна только при смене параметров связи.
- В `manifest.json`: `dependencies: ["modbus"]`, `connectivity: ["modbus"]`, а в `loggers` —
  имя своей библиотеки, `modbus_connection` и бэкенда (`tmodbus` или `pymodbus`).
- Конфликт параметров связи (тот же датчик занят с другой скоростью обмена) поднимает
  `async_get_unit` как `HomeAssistantError`; в мастере это показывается как ошибка формы.

---

## 5. Тестирование

- Фреймворк: `pytest` + `pytest-homeassistant-custom-component` (версия соответствует
  целевой версии HA) + `syrupy` для снимков (`.ambr`).
- Обязательно:
  - 100 % покрытие `config_flow.py`, включая все ветки ошибок, abort, reauth и reconfigure
    (`config-flow-test-coverage`);
  - общее покрытие интеграции не ниже 95 % (`test-coverage`);
  - снимки состояний и регистров сущностей (`snapshot_platform`) для каждой платформы;
  - тесты setup, unload, `ConfigEntryNotReady` и перехода в `unavailable` и обратно;
  - тест diagnostics через снимок.
- Библиотека мокается на границе, в `conftest.py`. Реальное устройство и сеть в unit-тестах
  не используются. Данные ответов устройства лежат в `tests/fixtures/*.json`.
- Тесты проверяют поведение через `hass` (состояния, вызовы actions), а не приватные атрибуты.
- Тесты без условных ветвлений: используем `pytest.mark.parametrize` с `pytest.param(..., id=...)`.
  Если фикстура нужна только для эффекта — `@pytest.mark.usefixtures`.
- Каждый `#### Scenario` из спецификации OpenSpec покрыт хотя бы одним тестом.
  В docstring теста или в `tasks.md` указана ссылка на требование.
- Перед выпуском обязательна проверка на живом Home Assistant по `conventions/live-verification`:
  мастер настройки, сущности, диагностика, переконфигурация. Зелёные тесты этого не заменяют —
  тесты проверяют то, что сами и вводят.

---

## 6. Публикация через Marketplace

Marketplace встроен в HA начиная с 2026.11 и использует каталог и формат HACS.

- **`manifest.json`** (порядок ключей: `domain`, `name`, затем по алфавиту):
  `domain`, `name`, `codeowners`, `config_flow: true`, `dependencies`, `documentation`
  (ссылка на README/документацию), `integration_type` (`device`/`hub`/`service`),
  `iot_class`, `issue_tracker` (**обязательно для каталога**), `loggers`,
  `quality_scale`, `requirements` (точные версии `lib==x.y.z`, без пакетов, которые уже входят в
  зависимости HA), `version` (**обязательно**, совпадает с тегом релиза, SemVer), `categories`
  (1–3 значения из официального списка категорий интеграций), блоки discovery при необходимости.
- **`hacs.json`** в корне репозитория:
  ```json
  {
    "name": "Acme Devices",
    "homeassistant": "2026.11.0"
  }
  ```
  `homeassistant` — минимальная поддерживаемая версия HA. Её повышаем, когда используем новые API.
  `persistent_directory` — только если интеграция хранит пользовательские файлы в своей папке.
  `country` — если устройство продаётся только в отдельных странах.
- **Переводы**: Marketplace не использует `strings.json` и Lokalise. Поставляются готовые
  `translations/en.json` (полный) и `translations/ru.json`. Ради совместимости с Core
  `strings.json` хранится как источник, а `en.json` генерируется из него скриптом и
  проверяется в CI на расхождения.
- **Бренд**: `brand/icon.png` (256×256), `brand/logo.png`, при наличии варианты `@2x` и `dark_`.
  Брендовые изображения Home Assistant использовать нельзя.
- **CI** на каждый push и PR:
  - `home-assistant/actions/hassfest`;
  - `hacs/action` с `category: integration`;
  - ruff, mypy, pytest с покрытием;
  - импорт библиотеки протокола из корня репозитория — проверка `conventions/module-naming`.
  Все проверки должны быть зелёными, иначе в каталог не попасть.
- **Релизы**: GitHub Release с тегом `vX.Y.Z`, совпадающим с `manifest.json`→`version`.
  Заметки о релизе — отдельный файл на тег, только свои изменения; правила и запрет переписывать
  опубликованное — `conventions/marketplace-packaging`. Пре-релизы помечаются как pre-release.
- **README** содержит: описание, поддерживаемые устройства и прошивки, кнопку
  «Open in Marketplace», My-link `config_flow_start`, установку, параметры настройки, описание
  обновления данных, примеры автоматизаций, известные ограничения, устранение неполадок, удаление.
  Это закрывает все правила `docs-*`.
- **Совместимость**: тестируем на бете HA перед каждым релизом. Следим за уведомлениями
  об устаревании в [блоге для разработчиков](https://contributors.home-assistant.io/blog/).
  У устаревших API 12 месяцев до удаления.

---

## 7. Путь к Core и Quality Scale

- В каждой интеграции есть `quality_scale.yaml`, где каждое правило помечено как
  `done`, `todo` или `exempt` (с `comment`). В `manifest.json`→`quality_scale` указан
  достигнутый tier.
- Целевой минимум для первого релиза в Marketplace — **Bronze**. Для заявки в Core —
  **Silver**, а ориентир — **Gold**.

| Tier | Ключевые правила |
|---|---|
| Bronze | action-setup, appropriate-polling, brands, common-modules, config-flow, config-flow-test-coverage, dependency-transparency, docs-actions, docs-high-level-description, docs-installation-instructions, docs-removal-instructions, entity-event-setup, entity-unique-id, has-entity-name, runtime-data, test-before-configure, test-before-setup, unique-config-entry |
| Silver | action-exceptions, config-entry-unloading, docs-configuration-parameters, docs-installation-parameters, entity-unavailable, integration-owner, log-when-unavailable, parallel-updates, reauthentication-flow, test-coverage |
| Gold | devices, diagnostics, discovery, discovery-update-info, docs-data-update, docs-examples, docs-known-limitations, docs-supported-devices, docs-supported-functions, docs-troubleshooting, docs-use-cases, dynamic-devices, entity-category, entity-device-class, entity-disabled-by-default, entity-translations, exception-translations, icon-translations, reconfiguration-flow, repair-issues, stale-devices |
| Platinum | async-dependency, inject-websession, strict-typing |

Актуальный перечень берём на <https://contributors.home-assistant.io/core/quality-scale/rules/>.

- Каждый change в OpenSpec указывает, какие правила quality scale он закрывает. После реализации
  `quality_scale.yaml` обновляется в том же change.
- Перед заявкой в Core:
  1. Библиотека на PyPI: открытый исходный код, CI, релизы из CI, типизирована (`py.typed`).
  2. Пройден чек-лист «Does it belong in core» и «Development checklist».
  3. Первый PR в Core маленький: одна платформа, только config flow и базовые сущности.
     Остальное — последующими PR.
  4. Перенос: `brand/` уходит в репозиторий `home-assistant/brands`, переводы генерируются из
     `strings.json`, из `manifest.json` удаляются `version` и `issue_tracker`, тесты переезжают в
     `tests/components/<domain>/`, документация — в `home-assistant.io`.
  5. Соблюдаются правила PR в Core: используется шаблон PR, ничего из него не удаляется;
     уже запушенные коммиты не переписываются (amend/rebase/squash) после открытия PR.

---

## 8. Безопасность

- Учётные данные хранятся только в `entry.data`. Они не попадают в логи, исключения, атрибуты
  сущностей и диагностику.
- TLS проверяется по умолчанию. Отключать проверку можно только явной опцией пользователя,
  которую нужно обосновать в спецификации.
- Все сетевые вызовы имеют таймауты. Повторы — с backoff, без бесконечных циклов
  и «шторма» запросов к устройству.
- Входные данные actions проверяются схемой `voluptuous`. Данным от устройства не доверяем:
  разбираем их в библиотеке с валидацией.
- Зависимости закрепляются точными версиями. Их обновление — отдельный PR без других изменений.
- В интеграции нет `eval`/`exec`, загрузки кода из сети и записи вне своей папки
  (кроме `persistent_directory` и `.storage` через `Store`).

---

## 9. Правила работы ИИ-агента

1. Перед задачей прочитай этот файл, `openspec/config.yaml` и действующие спецификации
   затрагиваемого домена (`openspec/specs/`).
2. Нет утверждённого change — сначала предложи его (`/openspec-propose`) и остановись,
   дождись согласования.
3. Работай только в рамках `tasks.md` текущего change. Нашёл новую работу — допиши её в
   `tasks.md` или предложи отдельный change.
4. Перед тем как объявить задачу выполненной, запусти в репозитории интеграции:
   `ruff format --check`, `ruff check`, `mypy`, `pytest --cov`, а также hassfest и HACS action
   (локально или в CI). Приложи результаты.
5. В ответах не выдумывай API Home Assistant. Если не уверен — сверься с исходниками Core
   (`homeassistant/helpers/`, интеграции уровня Gold/Platinum как образец) и документацией.
6. Не коммить секреты, дампы реальных устройств с персональными данными и сгенерированные
   артефакты.
7. Сообщения коммитов — в повелительном наклонении на английском, со ссылкой на change-id:
   `Add climate platform (add-acme-thermostat-climate)`.
8. Код, комментарии, `strings.json` и `en.json` пишутся на английском. `ru.json`,
   спецификации и общение с пользователем — на русском, если не оговорено иное.

---

## 10. Необходимые умения (skills)

Ниже — набор умений, которые нужны для этой разработки. Каждое умение можно оформить как
отдельный agent skill (`.agents/skills/<name>/SKILL.md` или аналог для вашего инструмента)
с указанными триггерами. Пока таких файлов нет, этот раздел служит их сводным описанием.

| Skill | Когда применять | Что умеет и что проверяет |
|---|---|---|
| `openspec-workflow` | Любое новое поведение, изменение или исправление | Ведёт цикл explore → propose → validate → apply → verify → archive. Пишет требования с SHALL и сценариями WHEN/THEN, делит спецификации по capability, поддерживает `openspec/specs/conventions/` |
| `ha-device-analysis` | Старт новой интеграции или новой модели устройства | Разбирает протокол и API устройства, составляет карту «функция → платформа → device_class/state_class/единицы → категория». Выбирает `iot_class`, `integration_type` и стратегию push/poll, определяет источник `unique_id` |
| `ha-python-library` | Реализация протокола | Создаёт асинхронную типизированную библиотеку (aiohttp/asyncio, инъекция сессии, собственные исключения, `py.typed`), её тесты, CI и публикацию на PyPI через trusted publishing |
| `ha-integration-scaffold` | Создание репозитория интеграции | Структура `custom_components/<domain>/`, `manifest.json`, `hacs.json`, `pyproject.toml`, pre-commit, workflows (hassfest, HACS, lint, tests), README-шаблон, `quality_scale.yaml` |
| `ha-config-flow` | Настройка и подключение | User step, discovery (zeroconf/ssdp/dhcp/bluetooth/usb), reauth, reconfigure, options flow, subentries. Уникальность записей, `data_description`, тексты ошибок |
| `ha-coordinator-and-entities` | Получение данных и сущности | `DataUpdateCoordinator`/push, `runtime_data`, `EntityDescription`, базовый `entity.py`, `DeviceInfo`, `has_entity_name`, translation_key, `icons.json`, dynamic и stale devices, `PARALLEL_UPDATES`, unavailable |
| `ha-entity-platforms` | Выбор и реализация платформ | Знает контракты `sensor`, `binary_sensor`, `switch`, `light`, `climate`, `cover`, `number`, `select`, `button`, `event`, `update` и других. Корректно задаёт `supported_features`, единицы и режимы |
| `ha-actions-and-errors` | Сервисы и обработка ошибок | `services.yaml` и `icons.json` для actions, регистрация в `async_setup`, admin-only actions, `ServiceValidationError`/`HomeAssistantError` с переводами, исключения setup |
| `ha-diagnostics-repairs` | Поддержка пользователей | `diagnostics.py` с редактированием данных, repair issues, system health, логирование недоступности |
| `ha-i18n` | Любые тексты, видимые пользователю | `strings.json` → `translations/en.json` + `ru.json`, ключи для entity, exceptions, issues, config, options. Проверка полноты и синхронизации |
| `ha-testing` | Любые изменения кода | pytest + `pytest-homeassistant-custom-component`, фикстуры и моки библиотеки, `MockConfigEntry`, snapshot-тесты (syrupy), покрытие 100 % config flow и ≥ 95 % в целом, параметризация без ветвлений, трассировка сценариев OpenSpec |
| `ha-quality-scale-audit` | Перед релизом и перед заявкой в Core | Построчная проверка правил Bronze–Platinum, обновление `quality_scale.yaml` с обоснованием `exempt`, список недостающих работ в виде change |
| `ha-marketplace-release` | Публикация | SemVer, синхронизация `version` и тега, `hacs.json`→`homeassistant`, release notes, бренд-изображения, проверки hassfest и HACS action, заявка в каталог (`hacs/default`), My-links в README |
| `ha-core-migration` | Перенос в Core | Чек-лист «Does it belong in core», разбиение на маленькие PR, перенос `brand/` в `home-assistant/brands`, `strings.json`, удаление `version`/`issue_tracker`, документация в `home-assistant.io`, соблюдение PR-шаблона и AI Policy |
| `ha-security-review` | Ревью каждого PR | Секреты, редактирование диагностики, TLS, таймауты, валидация входных данных, блокирующие вызовы в event loop, pin зависимостей |
| `ha-compat-maintenance` | Каждый месячный релиз HA | Проверка на бете, отслеживание deprecations в блоге разработчиков, обновление минимальной версии HA и `pytest-homeassistant-custom-component` |

Порядок применения при новой интеграции:
`ha-device-analysis` → `openspec-workflow` (propose) → `ha-python-library` →
`ha-integration-scaffold` → `ha-config-flow` → `ha-coordinator-and-entities` / `ha-entity-platforms` →
`ha-actions-and-errors` → `ha-diagnostics-repairs` → `ha-i18n` → `ha-testing` →
`ha-security-review` → `ha-quality-scale-audit` → `ha-marketplace-release` →
`openspec-workflow` (archive).

---

## 11. Definition of Done для change

- [ ] Change в OpenSpec прошёл `openspec validate --strict` и утверждён человеком.
- [ ] Все пункты `tasks.md` отмечены. Каждый сценарий покрыт тестом.
- [ ] ruff, mypy (strict), pytest зелёные. Покрытие: config flow — 100 %, всё остальное — не ниже 95 %.
- [ ] hassfest и HACS action зелёные.
- [ ] `translations/en.json`, `ru.json`, `icons.json` обновлены. Нет неиспользуемых ключей.
- [ ] `quality_scale.yaml` и `manifest.json`→`quality_scale` актуальны.
- [ ] README и release notes обновлены. Breaking changes описаны отдельно.
- [ ] Проверка на живом Home Assistant пройдена по чек-листу `docs/live-check.md`, а результат
  записан отчётом в `docs/live-checks/` (`conventions/live-verification`): мастер настройки,
  сущности, диагностика, переконфигурация.
- [ ] Change заархивирован (`/openspec-archive-change`), `openspec/specs/` отражает новое поведение.
