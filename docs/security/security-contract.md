# Security Contract

Review and test:

- model-output prompt injection
- static action allowlist and strict schemas
- SSRF and external redirects
- path traversal and symlink escape
- Zip Slip
- shell/command injection
- unsafe deserialization
- SQL injection
- approval replay and mutation
- weak randomness
- token and API-key leakage
- unsafe logs and reports
- Android exported components
- PendingIntent flags
- foreground-service policy
- loopback binding
- cleartext network scope
- unsafe model import
- CI action pinning and excessive permissions
- artifact poisoning and secret leakage

No validated critical/high finding may remain. Medium findings require remediation or an
explicitly accepted, evidence-backed residual-risk entry.
