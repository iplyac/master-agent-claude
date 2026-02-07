## ADDED Requirements

### Requirement: Dynamic prompt update

Сервис SHALL поддерживать динамическое обновление системного промпта в runtime.

#### Scenario: Prompt update in memory
- **WHEN** загружен новый промпт
- **THEN** создаётся новый Agent с новым промптом
- **AND** создаётся новый Runner с новым агентом
- **AND** обновляется `app.state.runner`

#### Scenario: Mutable agent storage
- **WHEN** сервис запускается
- **THEN** agent и runner хранятся в `app.state`
- **AND** могут быть заменены при reload
