# 测试用例生成器 (TestCase Generator)

## 一、简介

这是一个 Claude Code Skill（技能），可以根据你的需求文档或接口文档，自动生成功能测试用例和接口测试用例。

**一句话功能**：上传 API 文档 → 自动生成 30+ 测试用例 → 导出为 pytest/Postman/JMeter 等格式

---

## 二、安装方法

### 2.1 克隆或下载 Skill

```bash
# 1. 进入 Claude Skills 目录
cd ~/.claude/skills

# 2. 克隆本仓库（或手动复制文件夹）
git clone https://github.com/your-username/testcase-generator.git

# 或者手动复制：将整个 testcase-generator 文件夹复制到 ~/.claude/skills/ 下
```

### 2.2 安装依赖（可选）

```bash
cd ~/.claude/skills/testcase-generator/scripts

# 安装 Python 依赖
pip install openpyxl pyyaml

# 可选依赖
pip install requests jinja2
```

### 2.3 验证安装

```bash
cd ~/.claude/skills/testcase-generator/scripts
python main.py --help

# 应该看到帮助信息
```

---

## 三、支持的输入格式

### 3.1 接口文档

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| **Postman Collection** | `.json` | Postman 导出的接口集合 |
| **OpenAPI / Swagger** | `.json`, `.yaml`, `.yml` | 标准 OpenAPI 2.0/3.0 规范 |
| **HAR 格式** | `.har` | 浏览器抓包导出的 HTTP 归档 |
| **Markdown API 文档** | `.md` | Markdown 格式的 API 文档 |
| **JSON Schema** | `.json` | JSON Schema 格式定义 |

### 3.2 需求文档

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| **Markdown** | `.md` | 功能需求描述文档 |
| **Text** | `.txt` | 简单的文本需求 |

### 3.3 需求文档推荐结构

为了更稳定地生成功能测试用例，建议需求文档按“功能点 + 字段说明”的方式组织，例如：

```markdown
# 用户中心需求

## 用户登录
- 用户名：必填，string，长度 6-20
- 密码：必填，string，长度 8-20
- 验证码：选填，string

## 用户注册
| 字段名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| 用户名 | string | 是 | 6-20 位字母数字 |
| 邮箱 | string | 是 | 用于接收验证邮件 |
| 邀请码 | string | 否 | 渠道推广使用 |
```

> 说明：当输入为需求文档时，工具会自动识别功能点并生成功能测试用例；输出格式推荐使用 `markdown`、`excel` 或 `json`。

---

## 四、使用方法

### 4.1 准备你的文档

将你的接口文档或需求文档放到任意目录，例如：

```
/Users/yourname/projects/myapi/
├── openapi.yaml          # Swagger/OpenAPI 文档
├── postman.json          # Postman 集合
└── requirements.md       # 需求文档
```

### 4.2 在 Claude Code 中调用

在 Claude Code 对话框中，直接输入：

```
使用 testcase-generator skill，根据我的 openapi.yaml 生成测试用例，模块名称叫 UserAPI，base URL 是 https://api.example.com
```

### 4.3 Claude Code 会自动执行

```bash
# Claude Code 内部执行类似这样的命令：
cd ~/.claude/skills/testcase-generator/scripts
python main.py \
    -i /path/to/your/openapi.yaml \
    -o markdown \
    -m UserAPI \
    -b https://api.example.com \
    -v
```

### 4.4 获取生成的测试用例

Claude Code 会输出：
- 测试用例统计（总数、优先级分布、测试类型）
- 生成的文件列表
- 部分用例预览
- 断言来源与是否为假设标记（用于区分文档明确项和待确认项）

---

## 五、命令行用法（进阶）

如果你想直接使用命令行：

### 5.1 基本命令

```bash
cd ~/.claude/skills/testcase-generator/scripts

# 语法
python main.py -i <输入文件> -o <输出格式> -m <模块名> -b <base_url>
```

### 5.2 参数说明

| 参数 | 简写 | 说明 | 示例 |
|------|------|------|------|
| `--input` | `-i` | 输入文件路径（必填） | `-i api.yaml` |
| `--output` | `-o` | 输出格式 | `-o markdown` |
| `--module` | `-m` | 模块名称 | `-m UserAPI` |
| `--base-url` | `-b` | API 基础 URL | `-b https://api.example.com` |
| `--output-dir` | `-d` | 输出目录 | `-d ./output` |
| `--verbose` | `-v` | 显示详细信息 | `-v` |

### 5.3 输出格式选项

| 格式 | 说明 | 用途 |
|------|------|------|
| `markdown` | Markdown 文档 | 用例评审、文档归档 |
| `excel` | Excel 文件 | 手动测试执行 |
| `pytest` | Python 测试代码 | 自动化测试 |
| `postman` | Postman Collection | Postman 导入 |
| `jmeter` | JMeter JMX 文件 | 性能测试 |
| `json` | JSON 原始数据 | 程序处理 |
| `all` | 所有格式 | 全面覆盖 |

### 5.4 使用示例

```bash
# 示例 1：从 Postman 集合生成 Markdown 文档
python main.py -i ~/api.postman_collection.json -o markdown -m AuthAPI

# 示例 2：从 Swagger 生成 Excel 和 pytest 代码
python main.py -i swagger.yaml -o all -m Payment -b https://api.payment.com

# 示例 3：生成 JMeter 性能测试计划
python main.py -i openapi.json -o jmeter -m LoadTest -b https://api.example.com

# 示例 4：生成所有格式到指定目录
python main.py -i api.json -o all -m User -b https://api.example.com -d ./testcases
```

---

## 六、输入文档示例

### 6.1 Postman Collection 示例

```json
{
  "info": {
    "name": "用户服务",
    "description": "用户相关接口"
  },
  "item": [
    {
      "name": "用户登录",
      "request": {
        "method": "POST",
        "url": {
          "raw": "{{baseUrl}}/api/v1/user/login",
          "host": ["{{baseUrl}}"],
          "path": ["api", "v1", "user", "login"]
        },
        "body": {
          "mode": "raw",
          "raw": "{\"username\": \"test\", \"password\": \"123456\"}"
        }
      }
    }
  ]
}
```

### 6.2 OpenAPI/Swagger 示例

```yaml
openapi: 3.0.0
info:
  title: 用户服务 API
  version: 1.0.0
servers:
  - url: https://api.example.com
paths:
  /api/v1/user/login:
    post:
      summary: 用户登录
      parameters:
        - name: username
          in: body
          required: true
          schema:
            type: string
        - name: password
          in: body
          required: true
          schema:
            type: string
      responses:
        '200':
          description: 登录成功
```

---

## 七、输出示例

### 7.1 Markdown 输出预览

```markdown
# 测试用例报告

## 基本信息

| 字段 | 值 |
|------|-----|
| 模块名称 | UserAPI |
| Base URL | https://api.example.com |
| 生成时间 | 2024-01-24 11:00:00 |
| 用例总数 | 30 |

## 接口测试用例

| 用例编号 | 用例标题 | 优先级 | 接口名称 |
|----------|----------|--------|----------|
| API_USERAPI_001 | 验证用户登录正常请求成功 | P0 | 用户登录 |
| API_USERAPI_002 | 验证用户登录缺少必填参数 | P0 | 用户登录 |
| API_USERAPI_003 | 验证用户登录SQL注入攻击 | P0 | 用户登录 |
```

### 7.3 断言可信度说明

为了避免生成“看起来正确但未被文档证明”的断言，接口测试用例会额外输出以下字段：

| 字段 | 说明 |
|------|------|
| `断言来源` | 标记断言来自接口文档、响应 schema，还是待确认项 |
| `是否为假设` | `否` 表示文档中已找到对应响应定义；`是` 表示文档未提供，需要人工确认 |

当接口文档没有给出错误码、错误消息、性能 SLA 等信息时，工具不会再直接伪造这些断言，而是输出 `待确认` 提示。

### 7.2 pytest 代码预览

```python
"""UserAPI 测试用例
自动化生成的 pytest 测试代码
"""

import pytest
import requests

BASE_URL = "https://api.example.com"

class TestValidation:
    """响应验证工具类"""
    @staticmethod
    def validate_response(response, expected_status=200):
        assert response.status_code == expected_status

class TestUserLogin:
    """用户登录测试类"""

    def test_verify_user_login_success(self, base_url, headers):
        """验证用户登录正常请求成功"""
        url = f"{base_url}/api/v1/user/login"
        response = requests.post(url, headers=headers, json={"username": "test"})

        assert response.status_code == 200
        TestValidation.validate_json(response)
```

---

## 八、测试用例类型

生成的测试用例覆盖以下维度：

| 类型 | 说明 | 优先级 |
|------|------|--------|
| **正向测试** | 正常参数请求、必填参数验证 | P0-P1 |
| **反向测试** | 缺少参数、类型错误、越界、无效 JSON | P0-P2 |
| **安全测试** | SQL 注入、XSS、未授权、Token 过期 | P0-P1 |
| **性能测试** | 响应时间、并发请求、负载测试 | P1-P2 |
| **兼容性测试** | 浏览器兼容、移动端兼容 | P1 |

---

## 九、在 Claude Code 中的使用示例

### 9.1 简单调用

```
> 使用 testcase-generator，根据我的 ~/api.yaml 生成测试用例
```

### 9.2 指定参数

```
> 使用 testcase-generator，解析 ~/Documents/postman_collection.json，
   模块名称叫 PaymentAPI，base URL 是 https://api.payment.com，
   输出为 pytest 和 postman 格式
```

### 9.3 查看帮助

```
> testcase-generator 有哪些输入格式支持？
```

---

## 十、常见问题

### Q1: 生成的用例可以直接用吗？

**答**: 生成的用例是模板，需要根据实际业务调整测试数据和预期结果。

### Q2: 支持中文吗？

**答**: 完全支持中文，包括用例标题、描述、文档内容。

### Q3: Swagger 文件有引用（$ref）能解析吗？

**答**: 支持解析 Swagger 中的 `$ref` 引用。

### Q4: 生成的 pytest 代码可以直接运行吗？

**答**: 基本框架可直接运行，但认证逻辑需要自行补充。

### Q5: 可以生成功能测试用例吗？

**答**: 可以，通过 Markdown 格式的需求文档生成功能测试用例。

---

## 十一、文件结构

```
testcase-generator/
├── SKILL.md                    # 本文档
├── references/
│   └── testcase_examples.md    # 用例模板示例
└── scripts/
    ├── main.py                 # 主入口（推荐使用）
    ├── testcase_generator.py   # 兼容旧版本
    ├── parsers/                # 文档解析器
    │   ├── __init__.py
    │   ├── postman.py
    │   ├── swagger.py
    │   ├── markdown.py
    │   ├── har.py
    │   └── json_schema.py
    ├── generators/             # 用例生成器
    │   ├── __init__.py
    │   ├── api_generator.py
    │   └── functional_generator.py
    ├── formatters/             # 输出格式化器
    │   ├── __init__.py
    │   ├── markdown.py
    │   ├── excel.py
    │   ├── pytest.py
    │   ├── postman.py
    │   └── jmeter.py
    └── utils/                  # 工具函数
        ├── __init__.py
        └── validators.py
```

---

## 十二、版本历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 2.0.0 | 2024-01 | 完整重构，支持多种文档和输出格式 |
| 1.0.0 | 2023-06 | 初始版本，仅支持 Postman 和 Excel |

---

## 十三、联系方式

如有问题或建议，请提交 Issue 或 Pull Request。

---

*Generated by TestCase Generator Skill for Claude Code*
