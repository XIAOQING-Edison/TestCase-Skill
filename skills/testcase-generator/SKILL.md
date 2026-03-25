---
name: testcase-generator
description: 根据接口文档、需求文档、Postman Collection、HAR、OpenAPI/Swagger、Markdown 或文本生成 API 测试用例或功能测试用例。适用于用户希望生成测试用例、导出 markdown/excel/json/pytest/postman/jmeter，或将需求与接口文档转换为结构化测试资产的场景。
---

# Testcase Generator

## 何时使用这个 Skill

当用户希望完成以下工作时，使用这个 Skill：

- 根据 OpenAPI、Swagger、Postman、HAR、JSON Schema 或 Markdown API 文档生成 API 测试用例
- 根据 Markdown 或文本格式的需求文档生成功能测试用例
- 将结果导出为 `markdown`、`excel`、`json`、`pytest`、`postman` 或 `jmeter`
- 评估文档覆盖情况，并将文档转换为结构化测试用例产物

## 何时不要使用这个 Skill

在以下场景不要使用这个 Skill：

- 用户需要的是人工探索式测试思路，而不是自动生成的测试用例
- 用户当前要解决的是 Bug 排查、异常定位或根因分析
- 用户希望得到“最终可直接执行的确定性断言”，但并没有提供足够完整的接口或需求信息

## 生成前先确认的输入

在开始生成之前，先收集或确认以下信息：

1. 输入文件路径
2. 模块名称
3. 文档类型是否明确：`接口文档` 或 `需求文档`
4. 输出格式
5. 如果要生成 API 执行产物，是否提供 `Base URL`

如果是 API 测试用例，还应尽量确认：

- 鉴权方式：`Token`、`Cookie`、`API Key`、`OAuth` 或 `none`
- 文档中是否定义了错误响应
- 文档中是否定义了性能阈值或 SLA

如果是功能测试用例，还应尽量确认：

- 需要覆盖的主要功能模块
- 关键字段及其必填 / 选填属性
- 是否需要覆盖兼容性或安全性相关场景

如果关键输入缺失，先追问，不要猜测。

## 生成规则

### 1. 先判断用例类型

- 如果输入是 OpenAPI、Swagger、Postman、HAR、JSON Schema 或 Markdown 接口文档，生成 API 测试用例
- 如果输入是需求类 Markdown 或文本，生成功能测试用例
- 如果文件类型不明确，先检查内容，再决定走哪条路径

### 2. 使用项目现有流水线

优先通过项目现有脚本执行生成流程：

```bash
python scripts/main.py -i <input-file> -o <format> -m <module-name> [-b <base-url>] [-d <output-dir>] [-v]
```

优先复用项目已有的解析、生成、格式化链路，不要绕开现有管线临时拼接一套输出。

### 3. 严禁伪造断言

这是强制规则。

- 如果接口文档明确写了响应状态码、响应 schema 或响应描述，就直接使用
- 如果文档没有定义错误响应、鉴权失败响应、权限失败响应或性能 SLA，不要自己编造
- 对于文档未定义的预期，统一标记为 `待确认`
- 输出中必须保留 `断言来源` 和 `是否为假设`

示例：

- 正确：`断言来源 = 接口文档响应定义（200）`，`是否为假设 = 否`
- 正确：`断言来源 = 待确认（文档未提供对应响应定义）`，`是否为假设 = 是`
- 错误：文档没写却擅自生成 `40001`、`Token expired` 之类的精确错误码或错误信息

### 4. 严格遵守输出格式边界

- 功能测试用例优先输出为 `markdown`、`excel` 或 `json`
- API 测试用例可以输出为 `markdown`、`excel`、`json`、`pytest`、`postman` 或 `jmeter`
- 如果当前类型不支持用户要求的输出格式，要明确说明，并且只有在用户同意时才切换到最接近的可用格式

### 5. 术语保持一致

在回复和结果中尽量统一使用这些术语：

- `API 测试用例`
- `功能测试用例`
- `需求文档`
- `接口文档`
- `断言来源`
- `假设`

## 输出要求

所有生成结果都应满足以下要求：

### API 测试用例

至少包含：

- 用例编号
- 用例标题
- 优先级
- Endpoint 或 URL
- 请求方法
- 请求头
- 请求数据
- 预期状态码
- 预期响应
- 断言来源
- 是否为假设
- 测试类型

### 功能测试用例

至少包含：

- 功能编号
- 用例标题
- 功能模块
- 优先级
- 预置条件
- 测试数据
- 执行步骤
- 预期结果
- 断言来源
- 是否为假设
- 测试类型

## 完成前检查清单

在结束前，确认以下事项：

- 识别出的文档类型与输入内容相符
- 输出格式符合用户要求
- 没有把文档未定义的 API 行为当成确定断言输出
- 适用时，输出中包含 `断言来源` 与 `是否为假设`
- 已把生成的文件和摘要信息返回给用户

## 返回结果时的表达方式

向用户汇报结果时，尽量按以下顺序说明：

1. 先说明生成了什么
2. 再说明识别出的用例类型
3. 汇总用例总数、优先级分布和类型分布
4. 明确提示是否存在被标记为 `待确认` 的断言
5. 列出生成的文件路径

## 示例提示词

```text
使用 testcase-generator，根据我的 openapi.yaml 生成 API 测试用例，模块名叫 UserAPI，输出 markdown

使用 testcase-generator，根据 requirements.md 生成功能测试用例，模块名叫 用户中心，输出 excel

使用 testcase-generator，根据 postman_collection.json 生成 pytest 测试代码，base URL 是 https://api.example.com
```

## 附加资源

- 测试用例字段风格和样例可参考 [references/testcase_examples.md](references/testcase_examples.md)
