# CodeQL and Dependabot Hardening Design

## Goal

Add continuous semantic security analysis for the Python and Kotlin/Android codebases and automated dependency-update discovery for all maintained package ecosystems without broadening workflow permissions or weakening existing strict dependency verification.

## CodeQL

Use GitHub CodeQL Action v4.37.3 pinned to the immutable release commit:

`e4fba868fa4b1b91e1fdab776edc8cfbe6e9fb81`

Analyze two language families:

- `python` with build mode `none`;
- `java-kotlin` with build mode `manual` because Kotlin requires a build for complete CodeQL extraction.

The Kotlin build reuses the repository's established Android toolchain and strict Gradle dependency-verification policy. After CodeQL initialization, the workflow sets up JDK 21 and Gradle, makes the wrapper executable, and runs `:app:compileDebugKotlin` under `--dependency-verification strict`.

The workflow runs on pull requests, pushes to `main`, manual dispatch, and a weekly schedule. Permissions are limited to `contents: read` and `security-events: write`; no repository-content write permission is granted.

Use `security-extended` queries to increase security coverage beyond the default suite while keeping the analysis focused on security findings.

## Dependabot

Add `.github/dependabot.yml` for the three maintained dependency ecosystems:

- `pip` at `/`;
- `gradle` at `/android-broker`;
- `github-actions` at `/`.

Run weekly updates with small open-PR limits. Dependency updates remain ordinary pull requests subject to the repository's existing Python, Android, Security, release-workflow, and CodeQL checks. Dependabot must not auto-merge.

## Safety properties

- Every GitHub Action reference remains pinned to a full 40-character SHA.
- CodeQL receives only `security-events: write`; it cannot modify source or publish releases.
- The Kotlin analyzer must not bypass Gradle dependency verification.
- Dependabot only proposes pull requests; it has no auto-merge policy.
- Existing release and runtime behavior is untouched.

## Verification

Regression tests assert the exact CodeQL pin, language/build-mode matrix, permissions, strict Kotlin build command, and all three Dependabot ecosystems. The new CodeQL workflow must execute successfully on the stacked PR before the PR is marked ready for review.
