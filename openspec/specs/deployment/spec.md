### Requirement: Service name

Сервис SHALL деплоиться с именем `master-agent`.

#### Scenario: Service naming
- **WHEN** выполняется деплой
- **THEN** сервис создается/обновляется с именем `master-agent`

### Requirement: Public ingress

Сервис SHALL принимать публичный traffic (ingress=all).

#### Scenario: Public request accepted
- **WHEN** запрос приходит с любого IP
- **THEN** сервис обрабатывает запрос

### Requirement: Same region deployment

Сервис SHALL быть развёрнут в регионе `europe-west4` (совпадает с telegram-bot).

#### Scenario: Regional colocation
- **WHEN** оба сервиса в одном регионе
- **THEN** минимизируется latency между сервисами
