# Official Sources

Codex must re-open current primary sources before implementing platform-sensitive code.

## OpenAI Codex

- Harness engineering and repository knowledge:
  https://openai.com/index/harness-engineering/
- Plugins in Codex:
  https://help.openai.com/en/articles/20001256/

Use concise `AGENTS.md` files as navigation and durable constraints. Keep detailed
specifications in versioned docs. Plugins may contain skills and apps, but app-backed
actions retain their own permissions.

## LiteRT-LM

- Repository:
  https://github.com/google-ai-edge/LiteRT-LM
- Kotlin getting started:
  https://github.com/google-ai-edge/LiteRT-LM/blob/main/docs/api/kotlin/getting_started.md
- Google Maven artifact:
  `com.google.ai.edge.litertlm:litertlm-android`

Resolve `latest.release` only to discover the current version, then pin the concrete
version. Verify the actual Kotlin signatures. The engine must be initialized off the UI
thread and explicitly closed. `.litertlm` is the expected model format.

## Android

- Foreground-service types:
  https://developer.android.com/develop/background-work/services/fgs/service-types
- Foreground-service declaration:
  https://developer.android.com/develop/background-work/services/fgs/declare
- Background-start restrictions:
  https://developer.android.com/develop/background-work/services/fgs/restrictions-bg-start
- Storage Access Framework:
  https://developer.android.com/training/data-storage/shared/documents-files
- Android Keystore:
  https://developer.android.com/privacy-and-security/keystore
- Network Security Configuration:
  https://developer.android.com/privacy-and-security/security-config

Start the broker from visible user interaction. Use a valid declared foreground-service
type and permission set. Bind the server itself to loopback; network-security XML does not
replace socket-level binding.

## GitHub Actions

- Secure use:
  https://docs.github.com/en/actions/reference/security/secure-use
- `GITHUB_TOKEN`:
  https://docs.github.com/en/actions/concepts/security/github_token
- Dependency review:
  https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/manage-your-dependency-security/configure-dependency-review-action

Use least permissions and pin third-party actions to full commit SHAs.
