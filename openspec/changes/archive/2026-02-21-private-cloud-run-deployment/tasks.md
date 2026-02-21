## 1. deploy-agent.sh

- [x] 1.1 Изменить `--ingress=all` → `--ingress=internal` в команде `gcloud run deploy`
- [x] 1.2 Убрать `--allow-unauthenticated`, добавить `--no-allow-unauthenticated` в команде `gcloud run deploy`

## 2. cloudbuild.yaml

- [x] 2.1 Добавить флаг `--ingress` со значением `internal` в gcloud run deploy step
- [x] 2.2 Убрать `--allow-unauthenticated` из gcloud run deploy step
- [x] 2.3 Добавить `--network`, `--subnet`, `--vpc-egress=all-traffic` в gcloud run deploy step, используя substitution-переменные `${_VPC_NETWORK}` и `${_VPC_SUBNET}`
- [x] 2.4 Добавить substitution-переменные `_VPC_NETWORK: 'default'` и `_VPC_SUBNET: 'default'` в секцию `substitutions`

## 3. .env.example

- [x] 3.1 Добавить `VPC_NETWORK` и `VPC_SUBNET` в `.env.example` с комментарием о назначении
