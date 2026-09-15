# Workflow: OpenAPI Contract

Use this workflow after an API surface is stable enough to publish or validate as a contract.

1. Confirm endpoint paths, methods, DTOs, validation, status codes, authentication, and error responses.
2. Generate or maintain OpenAPI from the Spring controllers using the project's chosen Springdoc setup.
3. Add descriptions and examples only where generated metadata is insufficient.
4. Exclude or protect internal Actuator and administrative endpoints.
5. Validate the generated document in tests or CI and review breaking changes before release.
6. Keep generated artifacts out of source control unless the repository intentionally publishes a versioned contract.
