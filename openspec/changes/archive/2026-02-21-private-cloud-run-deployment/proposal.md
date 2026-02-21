## Why

Мастер агент сейчас задеплоен с `--ingress=all` и `--allow-unauthenticated` — сервис доступен из публичного интернета без аутентификации. Это противоречит принципу минимальных привилегий: сервис должен принимать трафик только из VPC (от Telegram webhook proxy / Load Balancer), а не напрямую из интернета.

## What Changes

- **deploy-agent.sh**: изменить `--ingress=all` → `--ingress=internal`, убрать `--allow-unauthenticated` → добавить `--no-allow-unauthenticated`
- **cloudbuild.yaml**: добавить VPC-настройки (`--network`, `--subnet`, `--vpc-egress`), изменить `--ingress all` → `--ingress internal`, убрать `--allow-unauthenticated`, добавить substitution-переменные `_VPC_NETWORK` и `_VPC_SUBNET`
- **.env.example**: задокументировать переменные `VPC_NETWORK` и `VPC_SUBNET` (уже используются в deploy-agent.sh, но не задокументированы)

## Capabilities

### New Capabilities
- `private-deployment`: Cloud Run сервис недоступен из публичного интернета — принимает трафик только через VPC (Direct VPC Egress + internal ingress)

### Modified Capabilities
<!-- Изменения только в процедуре деплоя, не в runtime-поведении сервиса -->

## Impact

- **deploy-agent.sh**: 2 флага (`--ingress`, `--allow-unauthenticated`)
- **cloudbuild.yaml**: добавить 4 флага в gcloud deploy step, 2 substitution-переменные
- **.env.example**: документация переменных
- **Требование**: VPC и подсеть должны быть созданы в GCP проекте до деплоя; SA Cloud Run нужна роль `roles/vpcaccess.user` или прямой доступ к подсети
- **BREAKING**: после изменения сервис станет недоступен из публичного интернета — необходим Cloud Load Balancer или IAP для внешнего доступа
