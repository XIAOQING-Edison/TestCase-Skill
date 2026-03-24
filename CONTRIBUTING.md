# Contributing Guide

感谢你参与 `TestCase Skill` 的改进。

这个项目当前定位为团队内部协作项目，目标是持续提升测试用例生成质量、文档可维护性，以及对测试工程师的实际可用性。

## 协作原则

- 先保证输出可信，再追求生成数量
- 优先修复错误断言、错误解析、错误格式化问题
- 新能力如果会引入不确定性，必须明确边界和降级策略
- 不要把文档里没有定义的接口行为写成“确定断言”

## 建议的协作流程

1. 在开始开发前，先确认问题类型：
   - Bug 修复
   - 解析能力增强
   - 生成策略优化
   - 输出格式优化
   - 文档与协作规范更新
2. 使用独立分支开发，不要直接在 `main` 上修改
3. 改动完成后，至少做一轮最小验证
4. 通过 Pull Request 合并

## 分支命名建议

建议使用下面的命名方式：

- `feat/<short-description>`
- `fix/<short-description>`
- `docs/<short-description>`
- `refactor/<short-description>`

示例：

- `feat/add-risk-level-output`
- `fix/swagger-path-loading`
- `docs/update-readme`

## 提交信息建议

建议使用简洁明确的提交信息，格式不限于 Conventional Commits，但推荐如下：

- `feat: add risk-aware testcase grouping`
- `fix: avoid fabricating undocumented assertions`
- `docs: rewrite project readme`

## 提交前检查

提交前请至少确认以下内容：

- 解析器改动没有破坏已有输入格式
- 生成器改动没有把“待确认”错误写成确定断言
- 新增字段在 `markdown`、`excel`、`json` 等主要输出中有一致体现
- 相关文档已经同步更新

## 重点关注区域

### 1. 解析器

目录：`skills/testcase-generator/scripts/parsers/`

修改这里时，请重点关注：

- 是否兼容现有文档结构
- 是否会把文件路径误当内容解析
- 是否会错误识别文档类型

### 2. 生成器

目录：`skills/testcase-generator/scripts/generators/`

修改这里时，请重点关注：

- 是否引入新的伪造断言
- 是否改变已有字段结构
- 是否影响优先级、类型分类、假设标记

### 3. 输出格式化器

目录：`skills/testcase-generator/scripts/formatters/`

修改这里时，请重点关注：

- 字段是否对齐
- 输出是否可读
- 是否遗漏 `断言来源`、`是否为假设` 等关键信息

### 4. Skill 与文档

关键文件：

- `skills/testcase-generator/SKILL.md`
- `skills/testcase-generator/references/testcase_examples.md`
- `README.md`

如果你修改了规则、字段、流程，请同步更新这些文件，避免“实现和文档脱节”。

## PR 审查重点

PR 评审时建议优先看：

1. 是否提升了结果可信度
2. 是否引入了新的错误假设
3. 是否破坏了现有输入输出兼容性
4. 是否把边界写清楚了

## 不建议直接提交的改动

以下改动建议先讨论再做：

- 大幅调整输出字段结构
- 删除现有输入格式支持
- 更改断言可信度策略
- 引入新的第三方依赖
- 修改项目定位或协作方式

## 反馈建议

如果你在使用过程中发现问题，建议在提 PR 或 Issue 时尽量带上：

- 输入文档样例
- 期望输出
- 实际输出
- 影响范围
- 是否属于回归问题

这样会更容易定位问题和快速合并。
