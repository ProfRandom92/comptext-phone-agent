# CompText Phone Agent 0.6.1 Community Release Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Prepare a polished, verifiable community-facing GitHub presence and editable Figma visual kit for CompText Phone Agent 0.6.1 without publishing a release or merging into `main`.

**Architecture:** Keep all changes isolated on `docs/community-release-0.6.1`. Documentation is split by audience and responsibility: README for first-time users, dedicated community policy files, dedicated release evidence, and a standalone smoke-test procedure. Figma assets mirror the public architecture and safety model but do not claim unsupported product behavior.

**Tech Stack:** GitHub Markdown, GitHub Actions badges, GitHub issue forms, YAML, Mermaid-compatible architecture content, Figma Design, Termux, Python 3.12+, pytest.

## Global Constraints

- Target branch is `docs/community-release-0.6.1`.
- Target version is `0.6.1`.
- Do not publish a GitHub Release.
- Do not merge into `main` automatically.
- Do not change runtime product code unless a release-blocking documentation mismatch is discovered.
- Do not claim root access, Play Store availability, unrestricted Android control, telemetry, or autonomous destructive cleanup.
- Every badge and factual claim must be backed by a repository file, workflow, release, or verified constraint.
- Figma visuals use near-black/graphite backgrounds, restrained neon cyan, cool blue, muted green, and semantic amber/red only where necessary.

---

### Task 1: Repository Evidence Inventory

**Files:**
- Read: `.github/workflows/*`
- Read: `pyproject.toml`
- Read: package version files
- Read: `docs/**`
- Create: `docs/release/0.6.1-evidence.md`

**Interfaces:**
- Consumes: current `main` commit `33702f2ee4133221ffec0d3691508a983481482b` and existing workflow/package metadata.
- Produces: an evidence table referenced by README badges and release checklist.

- [ ] **Step 1: Record the target commit and workflow names**
- [ ] **Step 2: Record package, Python, Android, and Termux constraints from repository files**
- [ ] **Step 3: Record verified CI/security results and explicitly mark unavailable connector evidence**
- [ ] **Step 4: Commit**

```bash
git add docs/release/0.6.1-evidence.md
git commit -m "docs: record 0.6.1 release evidence"
```

### Task 2: Community-Facing README

**Files:**
- Modify: `README.md`
- Create: `docs/assets/README-ASSETS.md`

**Interfaces:**
- Consumes: evidence from Task 1 and exported Figma asset paths.
- Produces: stable anchor links used by community and release documents.

- [ ] **Step 1: Replace the opening with project promise, maturity label, factual badges, and navigation**
- [ ] **Step 2: Add concise capabilities, safety model, quick start, workflows, architecture, limitations, verification, roadmap, contributing, and security sections**
- [ ] **Step 3: Move historical release prose out of README and link to CHANGELOG**
- [ ] **Step 4: Verify commands match current CLI names and preserve explicit approval semantics**
- [ ] **Step 5: Commit**

```bash
git add README.md docs/assets/README-ASSETS.md
git commit -m "docs: redesign community README"
```

### Task 3: Community Policies and Templates

**Files:**
- Create: `CONTRIBUTING.md`
- Create: `SECURITY.md`
- Create: `CODE_OF_CONDUCT.md`
- Create: `.github/PULL_REQUEST_TEMPLATE.md`
- Create: `.github/ISSUE_TEMPLATE/bug_report.yml`
- Create: `.github/ISSUE_TEMPLATE/feature_request.yml`
- Create: `.github/ISSUE_TEMPLATE/config.yml`

**Interfaces:**
- Consumes: README safety terminology and repository commands.
- Produces: contributor and reporter workflows that avoid secrets and sensitive paths.

- [ ] **Step 1: Add contribution workflow with setup, tests, scope, commit, and PR evidence requirements**
- [ ] **Step 2: Add private-first vulnerability reporting guidance without inventing an unsupported contact channel**
- [ ] **Step 3: Add Contributor Covenant-based conduct policy**
- [ ] **Step 4: Add PR template and structured issue forms with secret-redaction warnings**
- [ ] **Step 5: Validate YAML structure manually and commit**

```bash
git add CONTRIBUTING.md SECURITY.md CODE_OF_CONDUCT.md .github
git commit -m "docs: add community health files"
```

### Task 4: Changelog and Release Preparation

**Files:**
- Create or modify: `CHANGELOG.md`
- Create: `docs/release/0.6.1-checklist.md`
- Create: `docs/release/0.6.1-release-notes.md`
- Create: `docs/release/0.6.1-smoke-test.md`

**Interfaces:**
- Consumes: evidence file, current feature history, installer/uninstaller behavior, and artifact naming.
- Produces: release text and verification procedure suitable for a later GitHub Draft Release.

- [ ] **Step 1: Create Keep-a-Changelog-style history for 0.6.1 and preceding public milestones**
- [ ] **Step 2: Write release notes covering value, security, installation, upgrade, limitations, and rollback**
- [ ] **Step 3: Write a checkbox release checklist with commit, CI, artifacts, SHA-256, install, uninstall, rollback, and publication gates**
- [ ] **Step 4: Write non-destructive sandbox smoke-test commands and expected outcomes**
- [ ] **Step 5: Commit**

```bash
git add CHANGELOG.md docs/release
git commit -m "docs: prepare 0.6.1 release documentation"
```

### Task 5: Figma Community Release Visual Kit

**Files:**
- Create: Figma design file `CompText Phone Agent — Community Release 0.6.1`
- Update: `docs/assets/README-ASSETS.md`

**Interfaces:**
- Consumes: README message hierarchy and architecture/safety descriptions.
- Produces: editable frames for README hero, phone/terminal mockup, architecture, safety flow, release cover, and export board.

- [ ] **Step 1: Create a new Figma Design file in the user's only available plan**
- [ ] **Step 2: Build reusable color, typography, spacing, and card primitives**
- [ ] **Step 3: Build the README hero and mobile terminal mockup**
- [ ] **Step 4: Build architecture and Analyze → Plan → Approve → Apply → Audit diagrams**
- [ ] **Step 5: Build release/social cover and export board**
- [ ] **Step 6: Check legibility at desktop and mobile widths and record the Figma URL**

### Task 6: Validation and Draft Pull Request

**Files:**
- Review: all changed files
- Create: GitHub Draft Pull Request

**Interfaces:**
- Consumes: Tasks 1–5.
- Produces: reviewable Draft PR with evidence, limitations, and explicit non-publication status.

- [ ] **Step 1: Compare branch against `main` and confirm no runtime product code changed**
- [ ] **Step 2: Verify README links, workflow badge paths, YAML syntax, and command names**
- [ ] **Step 3: Check branch commit status and record any connector limitations honestly**
- [ ] **Step 4: Open Draft PR to `main` with summary, testing evidence, and release gates**
- [ ] **Step 5: Do not merge, mark ready, or publish a release**
