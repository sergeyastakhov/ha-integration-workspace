# HomeAssistantDev

Рабочее пространство для разработки интеграций устройств для Home Assistant.
Правила проекта — в [AGENTS.md](<AGENTS.md>), они обязательны для людей и агентов.

## Что здесь есть

| Каталог | Назначение |
|---|---|
| `AGENTS.md` | Правила: процесс, требования Home Assistant, тестирование, публикация, путь в Core |
| `openspec/` | Корень **сквозных** требований: `specs/conventions/` — правила, общие для всех интеграций и библиотек |
| `integrations/<domain>/openspec/` | Корень требований **конкретной интеграции** |
| `libraries/<name>/openspec/` | Корень требований **конкретной библиотеки** |
| `references/` | Исходные материалы по устройствам: документация производителя и извлечённые факты |
| `integrations/` | Код интеграций (custom-компоненты) |
| `libraries/` | Библиотеки протоколов, публикуемые на PyPI |
| `.agents/skills/` | Рабочие процессы OpenSpec для агентов |
| `.scratch/` | Временные файлы разработки, в репозиторий не попадает |

### Три уровня спецификаций

Требования разделены по зоне ответственности, и это же разделение переживёт вынос кода в
отдельные репозитории:

| Уровень | Что там лежит | Пример |
|---|---|---|
| Сквозной (`openspec/specs/conventions/`) | Правила, действующие на любую интеграцию: транспорт Modbus, доступность сущностей, идентичность, диагностика, локализация, упаковка | `conventions/modbus-transport` |
| Интеграция (`integrations/mtdx62/openspec/`) | Мастер настройки, сущности, поведение при недоступности, диагностика этой интеграции | `mtdx62-presence` |
| Библиотека (`libraries/mtdx62/openspec/`) | Контракт пакета: карта регистров, разбор значений, семантика ошибок | `mtdx62-registers` |

Правило, действующее на несколько интеграций, живёт только в сквозном уровне; интеграции на него
ссылаются, а не копируют. Разбор протокола — только в библиотеке; интеграция работает с её
типизированными значениями.

На время разработки интеграции и библиотеки лежат в этом репозитории рядом со спецификациями.
Перед публикацией в Marketplace каждая интеграция выносится в отдельный репозиторий GitHub —
это требование Marketplace («один репозиторий — одна интеграция»); `openspec/` уезжает вместе
с кодом.

## Порядок работы

1. Изменение начинается с предложения в OpenSpec **в корне того уровня, который меняется**:
   `openspec new change <имя>`, затем `proposal.md`, `specs/`, `design.md`, `tasks.md`.
2. Предложение проверяется: `openspec validate <имя> --strict`.
3. Предложение согласуется человеком. Без согласования код не пишется.
4. Реализация идёт по `tasks.md`, тесты — в тех же группах, что и код.
5. После проверки изменение архивируется: `openspec archive <имя>`.

Правка на границе уровней (меняется контракт библиотеки и поведение интеграции) — это два
изменения: сначала в корне библиотеки, потом в корне интеграции со ссылкой на первое.

```powershell
openspec list                       # в корне рабочего пространства — сквозные изменения
cd integrations\mtdx62              # здесь — изменения интеграции
openspec status --change add-mtdx62-presence-sensor
openspec validate add-mtdx62-presence-sensor --strict
cd ..\..\libraries\mtdx62           # здесь — изменения библиотеки
openspec validate add-mtdx62-device-library --strict
```

## Устройства

| Устройство | Протокол | Каталог фактов |
|---|---|---|
| MTD062-MB, MTD262-MB — радарные датчики присутствия | Modbus RTU / TCP | [references/mtdx62/DEVICE-FACTS.md](<references/mtdx62/DEVICE-FACTS.md>) |

## Текущее состояние

Готовы спецификации, реализация не начата:

- [Библиотека `mtdx62`](<libraries/mtdx62/openspec/changes/add-mtdx62-device-library/proposal.md>) —
  карта регистров и разбор значений на `modbus-connection`.
- [Интеграция `mtdx62`](<integrations/mtdx62/openspec/changes/add-mtdx62-presence-sensor/proposal.md>) —
  мастер настройки, сущности присутствия и окружения, диагностика.

Сквозные правила: [транспорт Modbus](<openspec/specs/conventions/modbus-transport/spec.md>),
[доступность](<openspec/specs/conventions/entity-availability/spec.md>),
[идентичность](<openspec/specs/conventions/entity-identity/spec.md>),
[диагностика](<openspec/specs/conventions/diagnostics/spec.md>),
[локализация](<openspec/specs/conventions/localization/spec.md>),
[упаковка](<openspec/specs/conventions/marketplace-packaging/spec.md>).
