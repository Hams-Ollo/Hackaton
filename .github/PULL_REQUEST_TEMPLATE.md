## 📋 Description

<!-- What does this PR do? Link to the relevant issue or ADO work item. -->

Closes #<!-- GitHub issue number -->
AB#<!-- Azure DevOps work item ID (required — links commit to ADO board) -->

## 🔍 Type of Change

- [ ] 🐛 Bug fix
- [ ] ✨ New feature / agent implementation
- [ ] 🔧 Refactor / cleanup
- [ ] 📝 Documentation / prompts
- [ ] 🏗️ Infrastructure / config
- [ ] 🧪 Tests

## ✅ Checklist

- [ ] I tagged this PR with `AB#<ID>` in the description above
- [ ] All prompts are in `prompts/` files — no inline f-string prompts in Python
- [ ] Azure OpenAI calls use `response_format` structured JSON — no free-text parsing
- [ ] No secrets or PATs hardcoded — `os.getenv()` only
- [ ] `_row_dirty=1` set on any CSV rows changed in this PR
- [ ] Read-only ADO fields are NOT patched (check `read_only_ado_columns` in `ado-config.yaml`)
- [ ] CI passes (AI PR Review action will post findings below)

## 🤖 AI Review Notes

<!-- The AI PR Review agent will automatically post a review comment on this PR. -->
<!-- You do not need to fill this section. -->
