# marketplace-packaging

## Purpose

Единое правило упаковки: интеграция проекта должна устанавливаться из Marketplace и проходить его
проверки с первого релиза, без ручных исключений.

## Requirements

### Requirement: Обязательные ключи манифеста

`manifest.json` SHALL содержать `domain`, `name`, `codeowners`, `documentation`, `issue_tracker`,
`version`, `integration_type`, `iot_class` и, для настраиваемых через интерфейс интеграций,
`config_flow: true`.

Marketplace отказывается устанавливать интеграцию без `version` и `issue_tracker`, поэтому они
MUST быть заполнены с первого релиза.

#### Scenario: Установка из Marketplace

- **WHEN** пользователь устанавливает интеграцию из каталога
- **THEN** установка проходит, потому что манифест содержит версию и ссылку на трекер

### Requirement: hacs.json описывает репозиторий

В корне репозитория SHALL лежать `hacs.json` с именем и минимальной поддерживаемой версией
Home Assistant. Версия MUST повышаться, когда интеграция начинает использовать новые API.

#### Scenario: Минимальная версия Home Assistant

- **WHEN** интеграция использует API, появившийся в определённой версии Home Assistant
- **THEN** в `hacs.json` указана эта версия как минимальная, и Marketplace не предложит установку
  на более старых системах

### Requirement: Свои изображения бренда

Интеграция SHALL поставлять `brand/icon.png` и `brand/logo.png`. Брендовые изображения
Home Assistant MUST NOT использоваться: пользователь не должен принимать интеграцию за официальную.

#### Scenario: Карточка в Marketplace

- **WHEN** пользователь открывает страницу интеграции в Marketplace
- **THEN** он видит изображение проекта, а не символику Home Assistant

### Requirement: Проверки Marketplace зелёные

CI интеграции SHALL запускать hassfest и HACS action на каждый push и pull request. Красная
проверка MUST NOT игнорироваться: без неё интеграция не попадает в каталог.

#### Scenario: Пул-реквест с ошибкой в манифесте

- **WHEN** в манифест попадает неизвестный ключ или неверная категория
- **THEN** проверка hassfest или HACS action падает и правка не принимается
