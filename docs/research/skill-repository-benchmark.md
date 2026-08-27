# Agent Skill 仓库形态基准调查

- 调查对象：[`haoranyu/clean-closed-issue-worktrees`](https://github.com/haoranyu/clean-closed-issue-worktrees)
- 基准提交：[`903b1d7cf2578f61a7ffb0e798b2e7f0d9550985`](https://github.com/haoranyu/clean-closed-issue-worktrees/tree/903b1d7cf2578f61a7ffb0e798b2e7f0d9550985)
- 调查日期：2026-08-27
- 来源范围：仅使用 Agent Skills 官方规范、官方产品文档、官方 GitHub 仓库及其源码/API；未使用博客聚合、社区教程或搜索摘要作为结论依据。

## 结论先行

仓库名称不需要改。`clean-closed-issue-worktrees` 是清晰的 kebab-case 名称，长度 28，符合 Agent Skills 对 `name` 的全部限制；仓库名与 skill 名一致也很适合单 skill 独立仓库。

当前内容组织在开放规范层面是合格的，而且安全协议、确定性脚本、隔离测试和三平台 CI 比大多数示例 skill 更工程化。真正偏离当前分发主流的不是 skill 内容，而是“安装单元边界”：[`SKILL.md`](https://github.com/haoranyu/clean-closed-issue-worktrees/blob/903b1d7cf2578f61a7ffb0e798b2e7f0d9550985/SKILL.md) 直接位于 Git 仓库根目录。

Agent Skills 规范允许“一个目录就是一个 skill”，所以将整个 clone 目录当作 skill 目录时，这种布局合法；官方 `skills-ref` 对当前绝对路径的验证也通过。但 GitHub CLI 2.98.0 的远端发现不会识别仓库根 `SKILL.md`，`gh skill preview` 当前返回 `no skills found`，`gh skill publish --dry-run` 也把目录识别为 `.` 并报 `name ... does not match directory name "."`。这会阻止目前最通用的 GitHub 原生 preview/install/update/publish 流程。

因此最值得学习并优先实施的是：保留单仓库、单 skill 的产品定位，不改名；把可安装 payload 下沉到 `skills/clean-closed-issue-worktrees/`，让仓库根只承载 README、测试、CI、研究文档和发布治理。

推荐目标结构：

```text
clean-closed-issue-worktrees/
├── README.md
├── LICENSE
├── docs/
├── tests/
├── .github/
│   ├── dependabot.yml
│   └── workflows/
│       └── test.yml
└── skills/
    └── clean-closed-issue-worktrees/
        ├── SKILL.md
        ├── LICENSE.txt
        ├── agents/
        │   └── openai.yaml
        ├── scripts/
        │   └── worktree_cleanup.py
        └── references/
            ├── evidence-schema.md
            ├── harness-detection.md
            └── provider-access.md
```

这个结构同时满足四种分发需求：

1. 通用 Agent Skills 客户端读取标准 skill 目录；
2. GitHub CLI 自动发现、预览、安装、更新和发布；
3. OpenAI 后续可以在仓库根增加一个很薄的 `.codex-plugin/plugin.json`，直接指向已有 `skills/`；
4. Anthropic 后续若需要 Claude plugin marketplace，也可以引用同一个 skill 目录，不复制内容。

## 调查基准

### 1. Agent Skills 开放规范

[Agent Skills specification](https://agentskills.io/specification) 规定：

- skill 是一个至少包含 `SKILL.md` 的目录；
- `scripts/`、`references/`、`assets/` 是推荐但可选的约定目录；允许其他文件；
- `name` 必须为 1–64 个小写字母、数字或连字符，不能首尾为连字符、不能有连续连字符，并且必须与父目录名一致；
- `description` 必须说明 skill 做什么以及何时使用；
- `license`、`compatibility`、`metadata`、`allowed-tools` 都是可选字段；
- 推荐 `SKILL.md` 少于 500 行，并使用相对路径、按需加载 reference；
- 官方参考验证器为 `skills-ref validate <skill-directory>`。

规范没有规定 GitHub 仓库必须叫什么，也没有要求必须使用 monorepo。换言之，“单 skill 独立仓库”和“多 skill catalog”都是发布策略，不是格式合规问题。

官方规范仓库的具体实现见 [`agentskills/agentskills`](https://github.com/agentskills/agentskills)，验证器源码和测试位于 [`skills-ref/`](https://github.com/agentskills/agentskills/tree/main/skills-ref)。

### 2. Anthropic 官方 skills 仓库

[`anthropics/skills`](https://github.com/anthropics/skills) 是多 skill monorepo：每个可安装单元位于 `skills/<name>/`，例如 [`skills/skill-creator/SKILL.md`](https://github.com/anthropics/skills/blob/main/skills/skill-creator/SKILL.md)。仓库根的 [`README.md`](https://github.com/anthropics/skills/blob/main/README.md) 明确说明每个 skill 是 self-contained folder，并把 `skills/`、`spec/`、`template/` 分开。

值得借鉴的点：

- 仓库级 README 与 skill payload 分离；
- 每个 skill 独立自洽，按需附带 scripts/references/assets；
- 使用 [`template/SKILL.md`](https://github.com/anthropics/skills/blob/main/template/SKILL.md) 提供最小模板；
- [`.claude-plugin/marketplace.json`](https://github.com/anthropics/skills/blob/main/.claude-plugin/marketplace.json) 只负责把若干 `./skills/<name>` 组合成 Claude 插件集合，不改变底层 skill 格式；
- 个别 skill 将许可证放在自己的目录，例如 [`skills/pdf/LICENSE.txt`](https://github.com/anthropics/skills/blob/main/skills/pdf/LICENSE.txt)，避免安装单个 skill 后丢失许可信息。

不应机械照搬的点：Anthropic 仓库是官方示例 catalog，所以需要多个 skill 集合、marketplace 和复杂许可说明；单 skill 独立仓库不需要为了“看起来主流”而扩成 catalog。

### 3. OpenAI 官方方向

OpenAI 现行 [Build skills](https://learn.chatgpt.com/docs/build-skills) 文档认可标准 skill 结构：`SKILL.md` 加可选的 `scripts/`、`references/`、`assets/`，并支持可选的 `agents/openai.yaml`。当前仓库的 [`agents/openai.yaml`](https://github.com/haoranyu/clean-closed-issue-worktrees/blob/903b1d7cf2578f61a7ffb0e798b2e7f0d9550985/agents/openai.yaml) 正是这一层 OpenAI 专用 UI 元数据，位置和用途合理。

同一份文档也明确区分“本地 authoring”和“可安装分发”：纯 skill 目录适合本地/仓库级使用；希望让更多人安装、组合多个 skill 或携带 connector 时，OpenAI 当前优先推荐 plugin。旧的 [`openai/skills`](https://github.com/openai/skills) catalog 已在 [`README.md`](https://github.com/openai/skills/blob/main/README.md) 标记 deprecated，当前示例转到 [`openai/plugins`](https://github.com/openai/plugins)。

OpenAI 的 [plugin packaging](https://developers.openai.com/plugins/build/plugins) 使用：

```text
my-plugin/
├── .codex-plugin/plugin.json
└── skills/
    └── my-skill/
        └── SKILL.md
```

这进一步说明把标准 payload 放到 `skills/<name>/` 是有复用价值的。但 `.codex-plugin/plugin.json` 是 Codex/ChatGPT 的分发包装，不是 Agent Skills 标准的一部分。对本项目而言，标准 skill + `gh skill` 应当先成为主分发面；Codex plugin wrapper 可以后加，不应取代跨 harness 核心。

### 4. GitHub Copilot 与 GitHub CLI

GitHub 的 [Adding agent skills for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills) 同样要求每个 skill 有独立目录，目录名使用 lowercase kebab-case，`name` 通常与目录名一致。GitHub 还明确警告：不应轻易在 `allowed-tools` 中预批准 shell/bash，因为这会移除执行前确认。当前 skill 没有预批准 shell，对高风险清理能力是正确选择。

GitHub 官方社区集合 [`github/awesome-copilot`](https://github.com/github/awesome-copilot) 是另一个多 skill monorepo，skill 位于 [`skills/<name>/SKILL.md`](https://github.com/github/awesome-copilot/tree/main/skills)。其 [`CONTRIBUTING.md`](https://github.com/github/awesome-copilot/blob/main/CONTRIBUTING.md) 要求 skill 名匹配目录名并运行 skill validation；[skill-check workflow](https://github.com/github/awesome-copilot/blob/main/.github/workflows/skill-check.yml) 会找出变更的 skill 目录并逐个 lint。

更关键的是 GitHub CLI 现已把 skills 变成 GitHub 原生发布对象：

- [`gh skill install`](https://cli.github.com/manual/gh_skill_install) 支持 GitHub Copilot、Claude Code、Codex、Cursor、Gemini CLI 等大量 harness，支持 project/user scope；
- 未指定版本时，安装顺序为“最新 GitHub Release tag → 默认分支 HEAD”；
- 可使用 `skill@v1.2.0` 或 `--pin` 固定 tag/SHA；
- [`gh skill publish`](https://cli.github.com/manual/gh_skill_publish) 会验证命名和 frontmatter、建议 SemVer tag、创建 GitHub Release，并可添加 `agent-skills` topic；
- 自动发现布局包括 `skills/*/SKILL.md`、`skills/{scope}/*/SKILL.md`、`*/SKILL.md` 和 `plugins/{scope}/skills/*/SKILL.md`。

GitHub CLI v2.98.0 的官方发现源码 [`internal/skills/discovery/discovery.go`](https://github.com/cli/cli/blob/v2.98.0/internal/skills/discovery/discovery.go) 将 `skills/<name>` 视为标准 convention，而把仓库根下一级的 `<name>/SKILL.md` 标记为 `[root]` convention；对应“single-skill repo”的官方测试见 [`discovery_test.go`](https://github.com/cli/cli/blob/v2.98.0/internal/skills/discovery/discovery_test.go#L88-L92)。直接位于仓库根的 `SKILL.md` 不属于远端发现路径。

## 当前仓库逐项评估

| 维度 | 当前状态 | 与主流/规范的差异 | 判断 |
|---|---|---|---|
| 仓库名 | `clean-closed-issue-worktrees` | 无；仓库名与 skill 名一致 | 保留 |
| `name` | 28 字符、全小写 kebab-case | 符合 1–64 字符限制 | 合规 |
| `description` | 265 字符，覆盖能力与触发场景 | 符合开放规范 1024 字符上限；超过 Anthropic Web 自定义 skill 文档的 200 字符产品限制 | 建议为最大兼容性压到 200 字符内 |
| Skill payload | 仓库根 `SKILL.md`、`scripts/`、`references/` | 开放规范合法；GitHub CLI 远端发现/发布不兼容 | 优先重排 |
| Progressive disclosure | `SKILL.md` 98 行，细节拆入 3 个 reference | 明显低于 500 行建议，引用层级浅 | 很好 |
| 确定性脚本 | Python 标准库 + Git，provider/harness 留在 agent 层 | 符合“脚本用于确定性/重复性工作”的官方建议 | 很好 |
| `agents/openai.yaml` | 有 display name、short description、default prompt | 符合 OpenAI 可选元数据格式 | 保留并随 skill 移动 |
| License | 仓库根 MIT `LICENSE`；frontmatter 无 `license` | GitHub 识别仓库许可证，但单 skill 安装不会带走根 LICENSE；`gh skill publish` 发出缺失 warning | 增加 `license: MIT` 与 payload 内 `LICENSE.txt` |
| README | 有定位、安全模型、手动安装、命令、测试 | 内容质量好；安装方式未覆盖当前最通用的 `gh skill` preview/install/pin/update | 扩充安装与发布章节 |
| 单元测试 | 305 行隔离测试，覆盖确定性脚本 | 规范不强制；对高风险脚本是明显优势 | 保留 |
| CI | Ubuntu/macOS/Windows，Python 3.9，compile + unittest | 跨平台优于多数示例；缺 spec/publish validation；Actions 使用可移动 tag | 加固 |
| 版本发布 | 没有 tags 或 GitHub Releases | catalog 常跟随 main，但独立发布物无法 pin、update 或审计版本 | 建立 SemVer Release |
| GitHub topics | 有 `agent-skill` 等 6 个 topic | `gh skill publish` 使用的是 `agent-skills`（复数） | 补充复数 topic |
| 专有包装 | 无 Codex/Claude plugin manifest | 不影响标准 skill；只影响相应插件市场安装体验 | 后续可选 |

### 描述长度的跨产品差异

开放规范允许 `description` 最长 1024 字符；当前 265 字符完全合规。Anthropic 当前 [How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) 对 Claude Web 上传的产品说明则写 200 字符上限；OpenAI [Build skills](https://learn.chatgpt.com/docs/build-skills) 还提醒宿主可能在 skill 很多时截短 description，应该前置关键触发词。

这是产品兼容性问题，不是规范错误。为了“同一份 skill 尽可能跨 harness”，建议压缩到 200 字符内，例如：

```yaml
description: Safely audit and remove Git worktrees linked to closed GitHub or GitLab issues. Use when scanning worktrees, verifying issue/PR/MR state, estimating space savings, or cleaning completed work.
```

该版本为 191 个 ASCII 字符，保留了主要触发词和安全定位。

## 实测证据

以下检查于 2026-08-27 对提交 `903b1d7` 执行，未修改远端仓库。

### 开放规范验证

使用 [`agentskills/agentskills` 的 `skills-ref`](https://github.com/agentskills/agentskills/tree/main/skills-ref)，并传入当前仓库的绝对路径：

```text
Valid skill: /Users/haoranyu/Develop/OpenSource/skills/clean-closed-issue-worktrees
```

这证明当前根目录布局作为“本地 skill 目录”符合开放规范。

### GitHub CLI 远端发现

使用 GitHub CLI 2.98.0：

```text
$ gh skill preview haoranyu/clean-closed-issue-worktrees clean-closed-issue-worktrees
no skills found in haoranyu/clean-closed-issue-worktrees
```

### GitHub CLI 发布预检

```text
$ gh skill publish --dry-run
error   clean-closed-issue-worktrees   name "clean-closed-issue-worktrees" does not match directory name "."
warning clean-closed-issue-worktrees   recommended field missing: license
warning                               no active tag protection rulesets found
validation failed with 1 error(s)
```

因此，“规范验证通过”与“GitHub 发布失败”可以同时成立：两者使用的 skill 根目录边界不同。把 payload 移到 `skills/clean-closed-issue-worktrees/` 可以消除这项差异。

## 分发布形态看待“主流”

### 单 skill 独立仓库

适合本项目。仓库有单一产品身份、独立 issues/releases/CI；仓库名等于 skill 名是优点。推荐用仓库根承载面向人类和维护者的内容，把安装单元放在 `skills/<name>/`。

若只考虑 Agent Skills 格式，`<repo>/<skill-name>/SKILL.md` 也能被 GitHub CLI 识别；但官方 CLI 将其标为 `[root]` convention，而 `skills/<name>/` 是所有官方 catalog 共同使用的标准路径，也能直接接入 OpenAI plugin manifest。因此本项目更推荐 `skills/<name>/`。

### 多 skill monorepo/catalog

Anthropic、OpenAI、GitHub 官方仓库都属于这一类。典型布局是：

```text
repo/
├── README.md
├── CONTRIBUTING.md
├── shared tooling and CI
└── skills/
    ├── skill-a/
    │   └── SKILL.md
    └── skill-b/
        └── SKILL.md
```

其优势是共享维护规范、验证器、网站和 marketplace；代价是所有 skill 共享仓库版本和治理。当前项目只有一个高度聚焦能力，没有理由仅为了模仿官方 catalog 就并入个人总仓库或改名为 `skills`。

## 具体建议与优先级

### P0：解决安装/发布兼容性

1. 将 `SKILL.md`、`agents/`、`scripts/`、`references/` 移到 `skills/clean-closed-issue-worktrees/`。
2. 调整测试中的脚本路径，以及 SKILL/README 内的相对命令示例。
3. 在 skill frontmatter 加：

   ```yaml
   license: MIT
   ```

   开放规范允许用 `compatibility` 声明 Git、Python、网络/provider 要求；但当前 Codex 内置快速校验器仍拒绝该字段。为了最大化跨 harness 兼容性，实际实现将这些要求保留在 SKILL 正文与 README，而不写入 frontmatter。不要添加 `allowed-tools: shell`，以保留宿主的执行确认。
4. 在 payload 内增加 `LICENSE.txt`；仓库根 `LICENSE` 继续保留。
5. 使用 GitHub CLI 2.90.0+ 运行：

   ```bash
   gh skill publish --dry-run
   gh skill preview haoranyu/clean-closed-issue-worktrees clean-closed-issue-worktrees
   ```

   GitHub 文档说明 `gh skill` 仍处于 public preview，因此 CI 和 README 应标注最低版本并保留手动复制 fallback。

### P1：建立可固定版本的发布流程

1. 当前项目刚发布且尚无 tag，建议首个版本用 `v0.1.0`；等真实用户验证跨仓库/跨 harness 流程后再发布 `v1.0.0`。
2. 通过：

   ```bash
   gh skill publish --tag v0.1.0
   ```

   创建 GitHub Release。该命令会执行 skill validation，并可添加 `agent-skills` topic。
3. 在 README 增加：

   ```bash
   gh skill preview haoranyu/clean-closed-issue-worktrees clean-closed-issue-worktrees

   gh skill install haoranyu/clean-closed-issue-worktrees \
     clean-closed-issue-worktrees@v0.1.0 \
     --agent codex --scope user

   gh skill install haoranyu/clean-closed-issue-worktrees \
     clean-closed-issue-worktrees@v0.1.0 \
     --agent claude-code --scope user
   ```

4. 为 `v*` 建 tag ruleset，至少阻止 tag 删除和强制更新；条件允许时启用 GitHub immutable releases。GitHub 的 [rulesets 文档](https://docs.github.com/en/repositories/configuring-branches-and-merges-in-your-repository/managing-rulesets/about-rulesets) 与 [immutable releases 文档](https://docs.github.com/en/enterprise-cloud%40latest/code-security/concepts/supply-chain-security/immutable-releases) 解释了这两层保护。
5. 不建议把版本同时写进 `SKILL.md metadata.version`；Release tag 应是单一版本真相。只有新增 Codex plugin wrapper 时，才同步维护 plugin manifest 必需的 `version`。

### P1：补齐 skill 级 CI，而不是替换已有测试

现有 [test workflow](https://github.com/haoranyu/clean-closed-issue-worktrees/blob/903b1d7cf2578f61a7ffb0e798b2e7f0d9550985/.github/workflows/test.yml) 和 [隔离测试](https://github.com/haoranyu/clean-closed-issue-worktrees/blob/903b1d7cf2578f61a7ffb0e798b2e7f0d9550985/tests/test_worktree_cleanup.py) 应保留。增加：

1. `skills-ref validate "$GITHUB_WORKSPACE/skills/clean-closed-issue-worktrees"`；官方 [`skills-ref/pyproject.toml`](https://github.com/agentskills/agentskills/blob/main/skills-ref/pyproject.toml) 当前要求 Python 3.11+，应放在独立 validator job，不要因此提高本地清理脚本的 Python 3.9 运行要求。
2. `gh skill publish --dry-run`，覆盖 GitHub 发现、frontmatter 和发布设置预检。
3. 一个安装烟雾测试：从本地仓库用 `gh skill install --from-local` 安装到临时目录，核对 `SKILL.md`、script、references、license 和 OpenAI metadata 都进入安装包。
4. 为 Python 3.9 保留三平台最低版本测试，并在 Ubuntu 增加一个当前 Python 版本，降低未来解释器兼容风险。
5. 将 `actions/checkout@v7`、`actions/setup-python@v7` 改为 full-length commit SHA，并在同一行保留版本注释；GitHub 的 [Secure use reference](https://docs.github.com/en/actions/reference/security/secure-use) 说明完整 SHA 是 Action 唯一不可变引用。GitHub 自己的 [awesome-copilot skill check](https://github.com/github/awesome-copilot/blob/main/.github/workflows/skill-check.yml) 也采用完整 SHA。
6. 增加只更新 `github-actions` 的 Dependabot 配置。官方步骤见 [Keeping your actions up to date with Dependabot](https://docs.github.com/en/code-security/how-tos/secure-your-supply-chain/secure-your-dependencies/auto-update-actions)。

### P1：改进 README 的安装和信任路径

当前 [`README.md`](https://github.com/haoranyu/clean-closed-issue-worktrees/blob/903b1d7cf2578f61a7ffb0e798b2e7f0d9550985/README.md) 的安全说明、两阶段流程和默认保留分支都应保留。建议安装章节按以下顺序重写：

1. `gh skill preview`：先审查文件树和 SKILL 内容；GitHub 官方明确建议安装第三方 skill 前 preview。
2. `gh skill install ...@TAG --agent ... --scope user`：作为跨 harness 首选。
3. 手动下载并复制 `skills/clean-closed-issue-worktrees/`：作为 `gh skill` preview 期间或 GitLab 托管 mirror 的 fallback。
4. Claude Web/Cowork：可在 Release 附加专用 ZIP，ZIP 内根目录必须是名为 `clean-closed-issue-worktrees` 的 skill folder。Anthropic 的 [custom skill packaging 文档](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills) 要求 ZIP 包含正确命名的 skill 根目录；GitHub 自动生成的整个仓库 source ZIP 不能直接替代这个专用包。
5. 增加支持矩阵，区分“已在 CI 验证的 OS/Python”“通过 `gh skill` 可安装的 harness”“provider 访问路径需要用户环境提供”。
6. 增加一个精简的扫描报告示例，展示 Recommended / Needs review / Keep、预计空间和确认边界。规范建议 body 包含输入/输出示例和常见边界，这也能让用户在安装前理解 skill 不会直接删除。

### P2：增加行为层 eval

当前测试验证脚本安全性，但没有验证 skill 的触发边界和 agent 是否坚持“两阶段确认”。OpenAI [Build skills best practices](https://learn.chatgpt.com/docs/build-skills) 建议用 prompts 测试 description 是否正确触发。

可以新增一个不依赖在线模型的 `evals/trigger-cases.json`，记录 should-trigger / should-not-trigger prompts；再维护一组人工或可选模型 eval，至少覆盖：

- “帮我扫一下已经关闭 issue 的 worktree”应触发；
- 普通 `git branch` 整理、不涉及 worktree/closed issue 时不应误触发；
- 初次说“clean”仍只做 read-only scan；
- 用户未确认精确路径时不得执行；
- issue reopened、dirty state、active harness、孤立提交、未知 ignored 文件均 fail closed；
- 用户语言为中文、英文或其他明确语言时，报告和确认问题跟随用户语言。

### P2：可选 plugin 包装

- 若希望进入 ChatGPT/Codex Plugins Directory，再增加 `.codex-plugin/plugin.json`，让 `skills` 指向 `./skills/`，按照 OpenAI [Package your plugin](https://developers.openai.com/plugins/build/plugins) 提供版本、作者、仓库、MIT、关键词和 install-surface copy。
- 若希望通过 Claude Code marketplace 分发，再增加 `.claude-plugin/marketplace.json`。Anthropic 官方示例可参考 [`anthropics/skills/.claude-plugin/marketplace.json`](https://github.com/anthropics/skills/blob/main/.claude-plugin/marketplace.json)。
- 两者都只是附加渠道；不要复制 skill payload，不要让 provider/harness 特定包装污染核心安全协议。

## 不建议做的改动

- 不改仓库名，也不把它改成泛化的 `worktree-cleanup`；当前名称准确表达“只处理 closed issue 映射”的重要安全边界。
- 不为了模仿官方 catalog 把个人所有 skills 迁入一个 monorepo。独立 issues、releases 和 CI 对高风险工具更有审计价值。
- 不把 OpenAI/Claude plugin manifest 当作开放标准的一部分。
- 不在 `allowed-tools` 里预批准 shell/bash，也不通过 manifest 绕过用户确认。
- 不把根 README、测试、CI 全部塞进安装包；安装单元应只包含运行 skill 必需的 instruction、script、references、metadata 和 license。
- 不仅追踪 `main` 而不给版本。对会删除 worktree 的能力，用户应能 preview 并 pin 到已审计的 Release。

## 建议的迁移验收标准

完成仓库重排后，应同时满足：

1. `skills-ref validate <absolute-skill-path>` 成功；
2. `gh skill publish --dry-run` 无 error；
3. `gh skill preview haoranyu/clean-closed-issue-worktrees clean-closed-issue-worktrees` 能展示正确文件树；
4. 本地 `gh skill install --from-local` 仅安装 skill payload，不包含仓库测试/CI/docs；
5. Python 单元测试在 Ubuntu、macOS、Windows 全部通过；
6. 安装后的相对 script/reference 链接全部存在；
7. `license: MIT` 和 `LICENSE.txt` 随 skill 安装，Git/Python/provider 要求在正文中可见；
8. README 的 Codex、Claude Code 安装命令均指定可固定的 tag；
9. 首个 GitHub Release 可被 `gh skill install ...@v0.1.0` 解析；
10. 对扫描、确认、备份分支、移除 worktree、保留/安全删除分支的既有安全行为没有回归。

## 来源索引

### 开放规范

- [Agent Skills specification](https://agentskills.io/specification)
- [Agent Skills official repository](https://github.com/agentskills/agentskills)
- [skills-ref validator](https://github.com/agentskills/agentskills/tree/main/skills-ref)

### Anthropic

- [anthropics/skills](https://github.com/anthropics/skills)
- [Anthropic skills README](https://github.com/anthropics/skills/blob/main/README.md)
- [Anthropic skill template](https://github.com/anthropics/skills/blob/main/template/SKILL.md)
- [Anthropic Claude plugin marketplace](https://github.com/anthropics/skills/blob/main/.claude-plugin/marketplace.json)
- [How to create custom skills](https://support.claude.com/en/articles/12512198-how-to-create-custom-skills)

### OpenAI

- [Build skills](https://learn.chatgpt.com/docs/build-skills)
- [Package your plugin](https://developers.openai.com/plugins/build/plugins)
- [openai/plugins](https://github.com/openai/plugins)
- [Deprecated openai/skills catalog](https://github.com/openai/skills/blob/main/README.md)

### GitHub

- [Adding agent skills for GitHub Copilot](https://docs.github.com/en/copilot/how-tos/copilot-on-github/customize-copilot/customize-cloud-agent/add-skills)
- [GitHub CLI: gh skill install](https://cli.github.com/manual/gh_skill_install)
- [GitHub CLI: gh skill publish](https://cli.github.com/manual/gh_skill_publish)
- [GitHub CLI v2.98.0 discovery implementation](https://github.com/cli/cli/blob/v2.98.0/internal/skills/discovery/discovery.go)
- [github/awesome-copilot skills](https://github.com/github/awesome-copilot/tree/main/skills)
- [github/awesome-copilot skill CI](https://github.com/github/awesome-copilot/blob/main/.github/workflows/skill-check.yml)
- [Secure use reference for GitHub Actions](https://docs.github.com/en/actions/reference/security/secure-use)
