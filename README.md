# TestCase Skill

一个面向测试设计场景的 Cursor Skill / Python 工具集，用于把接口文档或需求文档快速转换成结构化测试用例。

它当前的定位不是“自动替代测试工程师”，而是帮助你更快地产出第一版测试资产，包括：

- API 测试用例初稿
- 功能测试用例初稿
- 可评审、可执行、可二次加工的结构化输出
- 文档已知断言与待确认断言的明确区分

## 项目定位

这个项目最适合承担下面这个角色：

> 测试设计初稿生成工具，而不是测试结论生成工具。

也就是说，它的价值在于：

- 缩短从文档到用例的第一步时间
- 让测试工程师更快进入评审和细化阶段
- 减少手工整理基础测试资产的重复工作
- 降低“文档不完整却输出伪精确断言”的风险

## 核心能力

- 支持 API 文档和需求文档两类输入
- 自动判断当前输入更适合生成 API 用例还是功能用例
- 支持 `Markdown`、`Excel`、`JSON`、`pytest`、`Postman`、`JMeter` 等多种输出格式
- 为接口用例补充 `断言来源` 与 `是否为假设` 字段
- 在文档缺失错误响应、权限响应、性能阈值等信息时，不伪造断言，直接标记为 `待确认`

## 当前支持范围

### 输入格式

#### API 文档

| 类型 | 扩展名 | 说明 |
| ---- | ---- | ---- |
| Postman Collection | `.json` | 解析 Postman 导出的接口集合 |
| OpenAPI / Swagger | `.json` `.yaml` `.yml` | 解析 OpenAPI 2.x / 3.x 文档 |
| HAR | `.har` | 解析抓包记录中的 HTTP 请求 |
| Markdown API 文档 | `.md` | 适合章节式或表格式接口说明 |
| JSON Schema / 类 OpenAPI JSON | `.json` | 适合包含 `paths` 的接口定义 |

#### 需求文档

| 类型 | 扩展名 | 说明 |
| ---- | ---- | ---- |
| Markdown | `.md` | 推荐，结构更稳定 |
| Text | `.txt` | 适合简单需求或较短的功能描述 |

### 输出格式

| 输出格式 | 适用场景 | 说明 |
| ---- | ---- | ---- |
| `markdown` | 用例评审、归档 | 默认输出格式 |
| `excel` | 手工测试执行 | 适合测试同学直接维护 |
| `json` | 二次处理、平台接入 | 原始结构化结果 |
| `pytest` | API 自动化初稿 | 仅适用于 API 测试用例 |
| `postman` | Postman 导入执行 | 仅适用于 API 测试用例 |
| `jmeter` | 性能测试计划初稿 | 仅适用于 API 测试用例 |
| `all` | 一次导出多个格式 | 功能用例会自动跳过 API 专属格式 |

## 项目结构

```text
.
├── README.md
└── skills/
    └── testcase-generator/
        ├── SKILL.md
        ├── references/
        │   └── testcase_examples.md
        └── scripts/
            ├── main.py
            ├── testcase_generator.py
            ├── parsers/
            ├── generators/
            ├── formatters/
            └── utils/
```

关键文件说明：

- `skills/testcase-generator/SKILL.md`：给 Cursor / Agent 使用的执行规程
- `skills/testcase-generator/references/testcase_examples.md`：测试用例字段和样例参考
- `skills/testcase-generator/scripts/main.py`：当前推荐的统一入口
- `skills/testcase-generator/scripts/testcase_generator.py`：兼容旧版入口

## 安装与依赖

### 1. 克隆仓库

```bash
git clone https://github.com/XIAOQING-Edison/TestCase-Skill.git
cd TestCase-Skill
```

### 2. 安装推荐依赖

```bash
pip install pyyaml openpyxl
```

依赖说明：

- `pyyaml`：用于解析 `.yaml` / `.yml` 的 OpenAPI / Swagger 文档
- `openpyxl`：用于导出 Excel

如果你计划执行生成出来的 `pytest` 代码，还需要安装：

```bash
pip install pytest requests
```

## 使用方式

### 方式一：作为 Cursor Skill 使用

当这个项目放入 Cursor Skill 目录后，可以直接在对话中这样调用：

```text
使用 testcase-generator，根据我的 openapi.yaml 生成 API 测试用例，模块名称叫 UserAPI，输出 markdown
```

```text
使用 testcase-generator，根据 requirements.md 生成功能测试用例，模块名称叫 用户中心，输出 excel
```

```text
使用 testcase-generator，根据 postman_collection.json 生成 pytest 测试代码，base URL 是 https://api.example.com
```

### 方式二：直接命令行调用

推荐使用统一入口：

```bash
python skills/testcase-generator/scripts/main.py -i <输入文件> -o <输出格式> -m <模块名> [-b <base_url>] [-d <输出目录>] [-v]
```

参数说明：

| 参数 | 简写 | 是否必填 | 说明 |
| ---- | ---- | ---- | ---- |
| `--input` | `-i` | 是 | 输入文件路径 |
| `--output` | `-o` | 否 | 输出格式，默认 `markdown` |
| `--module` | `-m` | 否 | 模块名称，默认 `TestModule` |
| `--base-url` | `-b` | 否 | API 场景下使用的基础 URL |
| `--output-dir` | `-d` | 否 | 输出目录，默认当前目录 |
| `--verbose` | `-v` | 否 | 打印详细执行信息 |

## 常见使用示例

### 1. 从 OpenAPI 生成 Markdown 用例

```bash
python skills/testcase-generator/scripts/main.py   -i ./docs/openapi.yaml   -o markdown   -m UserAPI   -b https://api.example.com   -d ./output   -v
```

### 2. 从 Postman Collection 生成 pytest 初稿

```bash
python skills/testcase-generator/scripts/main.py   -i ./docs/postman_collection.json   -o pytest   -m PaymentAPI   -b https://api.example.com   -d ./output
```

### 3. 从需求文档生成功能测试用例

```bash
python skills/testcase-generator/scripts/main.py   -i ./docs/requirements.md   -o excel   -m 用户中心   -d ./output
```

### 4. 一次导出多个格式

```bash
python skills/testcase-generator/scripts/main.py   -i ./docs/openapi.yaml   -o all   -m AuthAPI   -b https://api.example.com   -d ./output
```

## 推荐输入文档写法

### 需求文档推荐结构

为了让功能测试用例生成更稳定，建议使用“功能点 + 字段说明”的写法。

```markdown
# 用户中心需求

## 用户登录

- 用户名：必填，string，长度 6-20
- 密码：必填，string，长度 8-20
- 验证码：选填，string

## 用户注册

| 字段名 | 类型 | 必填 | 说明 |
| ---- | ---- | ---- | ---- |
| 用户名 | string | 是 | 6-20 位字母数字 |
| 邮箱 | string | 是 | 用于接收验证邮件 |
| 邀请码 | string | 否 | 渠道推广使用 |
```

### API 文档建议

如果你希望生成的 API 用例更接近可直接评审的结果，建议接口文档尽量提供：

- 成功响应状态码
- 错误响应状态码
- 响应 description
- 响应 schema
- 鉴权方式说明
- 性能 SLA 或响应时间要求

文档越完整，输出越有参考价值。

## 输出结果说明

### API 测试用例常见字段

| 字段 | 说明 |
| ---- | ---- |
| `用例编号` | API 用例唯一标识 |
| `用例标题` | 用例名称 |
| `模块/优先级` | 模块和优先级组合值 |
| `请求URL` | 接口地址 |
| `请求类型` | HTTP 方法 |
| `请求数据` | 请求示例数据 |
| `预期响应状态` | 文档中已知状态码或 `待确认` |
| `预期响应信息` | 文档中的响应描述、schema，或待确认说明 |
| `断言来源` | 当前断言来自哪里 |
| `是否为假设` | 当前断言是否为待确认假设 |

### 功能测试用例常见字段

| 字段 | 说明 |
| ---- | ---- |
| `功能ID` | 功能用例唯一标识 |
| `用例标题` | 用例名称 |
| `功能模块` | 当前功能点名称 |
| `测试数据` | 样例测试数据 |
| `执行步骤` | 操作步骤 |
| `预期结果` | 预期行为 |
| `断言来源` | 当前默认标记为需求文档推导 |
| `是否为假设` | 当前默认标记为 `是` |

## 关于“断言来源”和“是否为假设”

这是当前项目最重要的一项约束。

目标是避免生成这种问题：

- 看起来很专业
- 但接口文档里其实没有写
- 最后误导测试工程师直接拿去执行

所以当前策略是：

- 文档里明确写了响应状态码、响应 description、响应 schema：直接使用
- 文档里没写错误码、错误消息、权限失败响应、性能阈值：不伪造，直接标记 `待确认`

示例：

| 场景 | 输出结果 |
| ---- | ---- |
| 文档定义了 `200` 和响应 schema | `断言来源 = 接口文档 schema（200）`，`是否为假设 = 否` |
| 文档没有定义 `400` / `401` / `403` | `断言来源 = 待确认（文档未提供对应响应定义）`，`是否为假设 = 是` |
| 文档没有性能 SLA | 保留成功状态码，但性能阈值标记为待确认 |

## 当前生成策略

### API 用例

当前会覆盖以下维度：

- 正向测试
- 反向测试
- 安全测试
- 性能测试

### 功能用例

当前会覆盖以下维度：

- 正向测试
- 反向测试
- 边界值测试
- 安全测试
- 兼容性测试

说明：

- 这是“测试设计初稿覆盖”，不是最终上线测试集
- 生成后仍建议测试工程师结合业务规则、账号体系、权限模型、环境约束进行二次筛选

## 当前限制与边界

为了避免误解，建议在使用前先了解这些边界：

1. 功能测试用例目前更适合结构化需求文档，不适合极度口语化或非常松散的描述。
2. `pytest`、`postman`、`jmeter` 只适用于 API 场景。
3. 生成的 `pytest` / `Postman` 更适合作为自动化初稿，不代表可以零修改直接上线执行。
4. 如果文档缺少错误响应定义，系统会明确标记 `待确认`，而不是替你猜测。
5. 性能测试用例目前更偏“计划模板”，不是压测平台本身。

## 适用场景

这个项目尤其适合以下情况：

- 需要快速从接口文档生成第一版测试用例
- 需求刚评审完，需要尽快拉出功能测试清单
- 希望减少手工整理基础测试资产的时间
- 希望把“文档已定义”和“人工待确认”区分开
- 想先有结构化初稿，再交给测试工程师细化

## 不适合替代的工作

以下工作仍然建议由测试工程师主导完成：

- 最终测试范围裁剪
- 高风险链路优先级确认
- 业务规则补充
- 测试数据准备与清理策略设计
- 多角色权限矩阵设计
- 探索性测试与异常场景挖掘

## 后续扩展方向

- 增加风险分层输出，例如 `smoke / core / full`
- 增加更强的鉴权识别能力
- 增加更明确的需求字段抽取规则
- 增加更完整的错误响应和权限模型识别
- 让 `references/testcase_examples.md` 与当前字段体系完全对齐

## 反馈方式

如果你在实际使用中发现以下问题，建议记录下来，作为下一轮优化输入：

- 哪类文档最容易解析失败
- 哪类断言最容易变成 `待确认`
- 哪些输出字段对测试工程师不够实用
- 哪些测试类型生成太多或太少
- 哪些自动化初稿还不够接近真实执行

如有建议或问题，欢迎提交 Issue 或 Pull Request。

---

> 本项目聚焦于将接口文档与需求文档快速转换为结构化测试用例，适合作为测试设计初稿生成工具，建议结合实际业务规则进行二次评审与完善。
