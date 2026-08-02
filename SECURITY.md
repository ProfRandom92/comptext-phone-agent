# Security Policy

## Supported version

Security fixes are currently prepared for the latest `0.6.x` release candidate. Older development snapshots may not receive backports.

## Reporting a vulnerability

Please do **not** disclose suspected vulnerabilities in a public issue, discussion, pull request or commit message.

Use GitHub's private vulnerability reporting feature for this repository when it is enabled. If that option is not visible, contact the repository owner privately through an already established trusted channel and provide only the minimum information required to reproduce the issue.

Include:

- affected commit or version;
- affected component and platform;
- reproducible steps using sanitized paths and data;
- expected and observed behavior;
- likely impact;
- any safe proof of concept;
- suggested mitigation, when available.

Never include real API keys, access tokens, `rclone.conf`, personal file listings, raw audit databases, private Android paths or other secrets.

## Security expectations

The project treats the following as security boundaries:

- read-only analysis by default;
- typed and hash-bound mutation plans;
- expiring, single-use approval tokens;
- protected-path and symlink-escape checks;
- redaction of credentials and sensitive values;
- loopback-only Android broker communication;
- no arbitrary model-generated shell execution;
- data-preserving uninstall by default.

A report that shows a bypass of any of these boundaries should be treated as potentially security-sensitive.

## Disclosure process

The maintainer will acknowledge a valid report, investigate it, coordinate a fix and publish an advisory or release note when appropriate. Public disclosure should wait until a fix or mitigation is available.