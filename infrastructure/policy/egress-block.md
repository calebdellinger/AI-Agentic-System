Rationale: Preserve “Sovereignty First” by preventing Lab hemisphere
internet egress.

How:
- Docker network design uses an `internal: true` network for the Lab
  container.
- The DinD sandbox runner must additionally run inner workloads with
  `--network none` (or an internal-only network) so no container inside the
  lab can reach the public internet.

Contracts:
- Treat this as an enforce-at-runtime requirement; compose-level isolation
  is necessary but not sufficient for strict compliance.

