## Context

Мастер агент задеплоен в Cloud Run (`europe-west4`). Текущие флаги:
- `--ingress=all` — принимает трафик из любого источника, включая публичный интернет
- `--allow-unauthenticated` — не требует аутентификации от вызывающей стороны
- `--network/--subnet/--vpc-egress=all-traffic` — уже настроен Direct VPC Egress для исходящего трафика

Таким образом, **исходящий** трафик уже идёт через VPC, но **входящий** — публично открыт. Нужно закрыть входящий трафик.

## Goals / Non-Goals

**Goals:**
- Изменить `--ingress` на `internal` — сервис принимает трафик только из VPC и Cloud Load Balancer
- Убрать `--allow-unauthenticated` — вызовы требуют IAM-аутентификации (Bearer token)
- Синхронизировать настройки в `deploy-agent.sh` и `cloudbuild.yaml`
- Задокументировать переменные `VPC_NETWORK` и `VPC_SUBNET` в `.env.example`

**Non-Goals:**
- Настройка Cloud Load Balancer или IAP (вне scope этого change)
- Изменение сетевой топологии GCP (VPC, подсети уже созданы)
- Изменение application-кода

## Decisions

### 1. `--ingress=internal` vs `--ingress=internal-and-cloud-load-balancing`

**Выбор:** `--ingress=internal`

**Почему:** Максимально ограничивает трафик — только ресурсы внутри VPC (Cloud Run сервисы, GCE, GKE) могут обращаться к сервису напрямую. Если в будущем нужен публичный доступ через Load Balancer — можно переключить на `internal-and-cloud-load-balancing` без изменения кода.

**Альтернатива:** `internal-and-cloud-load-balancing` — допускает трафик через Google Frontend (GLB), нужен когда перед Cloud Run стоит Cloud Load Balancer. Можно переключить позже при необходимости.

---

### 2. `--no-allow-unauthenticated`

**Выбор:** Убрать `--allow-unauthenticated`, использовать `--no-allow-unauthenticated`.

**Почему:** Без аутентификации любой, кто попадёт во VPC, может вызвать сервис. С аутентификацией нужен Bearer ID token — дополнительный слой защиты. Telegram бот должен использовать SA с ролью `roles/run.invoker`.

**Альтернатива:** Оставить unauthenticated и полагаться только на network ingress — менее безопасно, т.к. защита только одного уровня.

---

### 3. cloudbuild.yaml — substitution-переменные для VPC

**Выбор:** Добавить `_VPC_NETWORK` и `_VPC_SUBNET` как substitution-переменные с дефолтами `default`/`default`.

**Почему:** Позволяет переопределять сеть при запуске Cloud Build триггера без изменения yaml. Аналогично тому, как `_REGION` и `_SERVICE_NAME` уже параметризованы.

## Risks / Trade-offs

- **[BREAKING] Сервис станет недоступен из публичного интернета** → Митигация: задокументировать в tasks; Telegram бот должен ходить через VPC или Cloud Load Balancer
- **[Риск] Существующий Telegram webhook перестанет работать** → Митигация: webhook должен идти через Cloud Run сервис во VPC, или через Load Balancer — проверить перед деплоем
- **[Риск] cloudbuild.yaml — CI/CD деплой может сломать сервис если VPC переменные не заданы** → Митигация: дефолты `default`/`default` соответствуют стандартной VPC GCP

## Migration Plan

1. Убедиться что Telegram бот / webhook proxy находится в той же VPC
2. Применить изменения в deploy скриптах
3. Передеплоить сервис (`./deploy-agent.sh`)
4. Проверить доступность изнутри VPC
5. **Rollback**: вернуть `--ingress=all --allow-unauthenticated` если что-то сломалось
