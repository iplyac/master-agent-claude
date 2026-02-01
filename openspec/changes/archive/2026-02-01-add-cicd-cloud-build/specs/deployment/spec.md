## MODIFIED Requirements

### Requirement: Service name for Internal DNS

Сервис SHALL деплоиться с именем `master-agent`.

#### Scenario: Service naming
- **WHEN** выполняется деплой
- **THEN** сервис создается/обновляется с именем `master-agent`

### Requirement: Public ingress

Сервис SHALL принимать публичный traffic (ingress=all).

#### Scenario: Public request accepted
- **WHEN** запрос приходит с любого IP
- **THEN** сервис обрабатывает запрос

## REMOVED Requirements

### Requirement: Internal ingress

**Reason**: Cloud Run не поддерживает нативный Internal DNS (.run.internal). Переход на публичный HTTPS.

**Migration**: Telegram-bot использует публичный URL через AGENT_API_URL env var.
