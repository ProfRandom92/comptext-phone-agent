# CompText Phone Agent 0.6.1 Community Release Design

## Status

Approved visual direction: dark professional mobile-terminal aesthetic, restrained neon-cyan accents, strong security framing, minimal marketing language.

Target branch: `docs/community-release-0.6.1`

Target release: `0.6.1`

The work remains reviewable and must not publish a GitHub Release or merge into `main` automatically.

## Objectives

1. Make the repository understandable within the first screen of the README.
2. Present the project as a credible local-first Android and Termux tool rather than an experimental script collection.
3. Make installation, safety boundaries, supported workflows, and project maturity explicit.
4. Provide the minimum community infrastructure expected from a public open-source repository.
5. Prepare a verifiable GitHub Draft Release for version 0.6.1 without publishing it.
6. Produce reusable visual assets in Figma for the README, release page, and social sharing.

## Audience

Primary audiences:

- Android and Termux users who need storage analysis and controlled cleanup;
- privacy-conscious users who prefer local-first tooling;
- Python and Android contributors;
- reviewers evaluating the project's security and release quality.

The README must serve new users first. Deep implementation details remain available through linked documentation.

## Repository Presentation

### README opening section

The first screen will contain:

- project name and concise one-sentence value proposition;
- Figma-produced hero asset;
- factual badges for CI, security, supported Python version, Android/Termux target, license, and latest release when applicable;
- three primary actions: install, inspect security model, view release notes;
- explicit maturity label for version 0.6.1.

No badge may claim a capability or status that is not backed by a repository file, workflow, release, or verified project constraint.

### README information architecture

1. Hero and project promise
2. Why CompText Phone Agent
3. Core capabilities
4. Safety model
5. Quick start
6. Common workflows
7. Architecture overview
8. Supported environment and Android limitations
9. Provider and local orchestrator support
10. Verification and tests
11. Project status and roadmap
12. Contributing and security reporting
13. License and acknowledgements

Historical version notes currently appended to the README will move into `CHANGELOG.md` or release documentation.

## Visual System

### Style

- Backgrounds: near-black and graphite.
- Primary accent: restrained neon cyan.
- Secondary accents: cool blue and muted green for verified/safe states.
- Warning and destructive states: amber and red only when semantically necessary.
- Typography: modern grotesk for headings and readable monospace for terminal content.
- Visual tone: technical, calm, trustworthy, mobile-first.

### Figma deliverables

A single editable Figma design file named `CompText Phone Agent — Community Release 0.6.1` will contain:

1. README hero, optimized for GitHub's content width;
2. phone and terminal product mockup;
3. architecture overview;
4. security flow: Analyze → Plan → Approve → Apply → Audit;
5. release/social cover;
6. asset export board with PNG and SVG-ready frames where supported.

The visuals must remain legible in GitHub dark and light themes. Text embedded in images will be limited to titles, short labels, and terminal examples.

## Community Files

The branch will add or revise:

- `README.md`
- `CHANGELOG.md`
- `CONTRIBUTING.md`
- `SECURITY.md`
- `CODE_OF_CONDUCT.md`
- `.github/PULL_REQUEST_TEMPLATE.md`
- `.github/ISSUE_TEMPLATE/bug_report.yml`
- `.github/ISSUE_TEMPLATE/feature_request.yml`
- `.github/ISSUE_TEMPLATE/config.yml`
- release checklist documentation under `docs/release/`

Templates must request reproducible evidence while avoiding collection of secrets, API keys, private file paths, or sensitive audit data.

## Release Preparation

The 0.6.1 preparation will verify:

- target commit identity;
- required CI and security results;
- version consistency across package metadata and documentation;
- install and uninstall paths;
- APK and package artifact names;
- SHA-256 checksums;
- release notes and upgrade guidance;
- known limitations;
- first-run smoke test instructions;
- rollback and data-preservation behavior.

The resulting GitHub Release must remain a draft. Publication requires an explicit later instruction.

## External Smoke Test

A first-time user test will cover:

1. clone or download the release package;
2. run the sandbox installer;
3. execute `doctor`;
4. run a mock scan;
5. create a report;
6. create, approve, and apply a reversible mock cleanup plan;
7. restore the mock item;
8. confirm no mutation occurs without approval;
9. verify uninstall preserves user data by default.

The test must be runnable without real phone storage, cloud credentials, or destructive actions.

## Architecture Presentation

The public architecture diagram will show bounded layers:

- CLI and Textual TUI;
- orchestration and typed planner boundary;
- policy and approval engine;
- storage analysis, duplicate detection, reporting, backup, and device adapters;
- SQLite state, audit, approvals, cache, and sessions;
- optional loopback Android LiteRT-LM broker;
- external providers as optional and explicitly isolated.

The diagram must make clear that model output cannot directly execute arbitrary shell commands.

## Error and Trust Communication

Documentation will distinguish:

- verified behavior;
- optional integrations;
- Android platform restrictions;
- experimental components;
- planned work.

Failures must be described with actionable recovery steps. Documentation must not imply root access, unrestricted Android control, guaranteed access to scoped-storage locations, or autonomous destructive cleanup.

## Validation

Before the draft PR is considered ready:

- every README link must resolve;
- badge endpoints and workflow names must be correct;
- Markdown must render cleanly on GitHub;
- documented commands must match the current CLI;
- community templates must be syntactically valid;
- Figma exports must be visually checked at desktop and mobile widths;
- the branch diff must contain no product-code changes unless needed to correct a release-blocking documentation mismatch;
- CI and security evidence must be recorded in the release checklist.

## Non-goals

This work will not:

- publish the release;
- merge the branch automatically;
- redesign the application runtime or TUI;
- add unrestricted shell execution;
- claim Play Store availability;
- introduce telemetry or remote analytics;
- expose repository secrets or private release artifacts.

## Completion Criteria

The design is complete when:

1. a polished community-facing README is present;
2. required community files are present and internally consistent;
3. Figma assets are editable and exportable;
4. the external smoke test is documented and verified where connector evidence permits;
5. a Draft PR summarizes all changes and evidence;
6. a GitHub Draft Release for 0.6.1 is fully prepared but not published.
