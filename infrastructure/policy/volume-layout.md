Rationale: Make local volumes the system’s only communication bridge.

How:
- Document the expected volume paths so both hemispheres and n8n can be
  configured consistently.

Contracts:
- `spinalcord` volume is mounted to both Trinity and Lab at `/spinalcord`.
- Rhythms are hemisphere-local and never shipped to cloud logs.

Expected spinalcord subpaths:
- `requests/` (Lab inputs from Trinity)
- `discoveries/` (Lab outputs for Trinity)
- `results/` (Trinity outputs to Lab, if needed later)
- `errors/` (structured errors and failure notes)

