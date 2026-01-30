## 1. Изменение deploy-agent.sh

- [x] 1.1 Изменить SERVICE_NAME с `ai-agent` на `master-agent` (строка 6)
- [x] 1.2 Добавить `--ingress=internal` в команду `gcloud run deploy` (после строки 80)

## 2. Верификация

- [x] 2.1 Проверить что скрипт синтаксически корректен (`bash -n deploy-agent.sh`)
