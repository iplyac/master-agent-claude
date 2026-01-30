## ADDED Requirements

### Requirement: Service name for Internal DNS

Сервис SHALL деплоиться с именем `master-agent` для работы Internal Cloud Run DNS.

#### Scenario: Internal DNS resolution
- **WHEN** telegram-bot обращается к `https://master-agent.europe-west4.run.internal`
- **THEN** запрос маршрутизируется к master-agent сервису

### Requirement: Internal ingress

Сервис SHALL принимать только internal traffic (из того же VPC).

#### Scenario: Internal request accepted
- **WHEN** запрос приходит из VPC через Internal DNS
- **THEN** сервис обрабатывает запрос

#### Scenario: External request rejected
- **WHEN** запрос приходит с публичного IP
- **THEN** Cloud Run возвращает 403 Forbidden

### Requirement: Same region deployment

Сервис SHALL быть развёрнут в регионе `europe-west4` (совпадает с telegram-bot).

#### Scenario: Regional colocation
- **WHEN** оба сервиса в одном регионе
- **THEN** Internal DNS работает корректно
