---
name: testcase-generator
description: Generate API test cases or functional test cases from API docs, requirement docs, Postman collections, HAR files, OpenAPI/Swagger, Markdown, or text. Use when the user asks to generate test cases, API cases, functional cases, export to markdown/excel/json/pytest/postman/jmeter, or convert requirements and interface docs into test assets.
---

# Testcase Generator

## Use This Skill When

Use this skill when the user wants to:

- Generate API test cases from OpenAPI, Swagger, Postman, HAR, JSON Schema, or Markdown API docs
- Generate functional test cases from requirement documents in Markdown or text
- Export generated cases to `markdown`, `excel`, `json`, `pytest`, `postman`, or `jmeter`
- Review document coverage and convert docs into a structured testcase deliverable

## Do Not Use This Skill When

Do not use this skill when:

- The user wants manual exploratory testing advice rather than generated cases
- The user needs a bug investigation or root-cause analysis
- The user wants a final assertion baseline without providing enough API or requirement detail

## Inputs To Collect First

Before generating anything, collect or confirm:

1. Input file path
2. Module name
3. Document type if ambiguous: `API doc` or `requirement doc`
4. Output format
5. Base URL for API cases if request execution artifacts are needed

For API test cases, also try to confirm:

- Auth mechanism: `Token`, `Cookie`, `API Key`, `OAuth`, or `none`
- Whether the doc contains error responses
- Whether performance thresholds are documented

For functional test cases, also try to confirm:

- Main feature modules to cover
- Key fields and whether they are required/optional
- Whether compatibility or security cases are in scope

If critical inputs are missing, ask first instead of guessing.

## Generation Rules

### 1. Decide The Case Type

- If the input is OpenAPI, Swagger, Postman, HAR, JSON Schema, or Markdown API documentation, generate API test cases
- If the input is requirement Markdown or text, generate functional test cases
- If the file type is ambiguous, inspect the content before choosing

### 2. Use The Existing Pipeline

Run the generator through the existing script:

```bash
python scripts/main.py -i <input-file> -o <format> -m <module-name> [-b <base-url>] [-d <output-dir>] [-v]
```

Use the built-in parsing, generation, and formatting pipeline rather than inventing an ad hoc output format.

### 3. Never Fabricate Assertions

This rule is mandatory.

- If the interface document defines a response status, response schema, or response description, use it
- If the document does not define the expected error response, auth failure response, permission failure response, or performance SLA, do not invent values
- Mark undocumented expectations as `待确认`
- Preserve `断言来源` and `是否为假设` in the output

Examples:

- Good: `断言来源 = 接口文档响应定义（200）`, `是否为假设 = 否`
- Good: `断言来源 = 待确认（文档未提供对应响应定义）`, `是否为假设 = 是`
- Bad: inventing `40001` or `Token expired` when the source document never states them

### 4. Respect Format Boundaries

- Functional test cases should prefer `markdown`, `excel`, or `json`
- API test cases may output `markdown`, `excel`, `json`, `pytest`, `postman`, or `jmeter`
- If the requested format is not supported for the detected case type, say so clearly and use the nearest valid format only if the user agrees

### 5. Keep Terminology Consistent

Use these terms consistently:

- `API test case`
- `functional test case`
- `requirement doc`
- `API doc`
- `assertion source`
- `assumption`

## Output Requirements

Every generated result should preserve these expectations:

### API Test Cases

Include at least:

- Case ID
- Title
- Priority
- Endpoint or URL
- Method
- Request headers
- Request data
- Expected status
- Expected response
- Assertion source
- Whether the assertion is an assumption
- Test type

### Functional Test Cases

Include at least:

- Case ID
- Title
- Feature module
- Priority
- Preconditions
- Test data
- Steps
- Expected result
- Assertion source
- Whether the assertion is an assumption
- Test type

## Validation Checklist

Before finishing, verify:

- The detected document type matches the input content
- The output format matches the user request
- No undocumented API behavior was presented as a confirmed assertion
- `断言来源` and `是否为假设` are present in the generated output where applicable
- The generated files and summary are returned to the user

## Response Pattern

When reporting results back to the user:

1. State what was generated
2. State the detected case type
3. Summarize totals, priorities, and case categories
4. Highlight whether some assertions are marked `待确认`
5. List generated files

## Example Prompts

```text
使用 testcase-generator，根据我的 openapi.yaml 生成 API 测试用例，模块名叫 UserAPI，输出 markdown

使用 testcase-generator，根据 requirements.md 生成功能测试用例，模块名叫 用户中心，输出 excel

使用 testcase-generator，根据 postman_collection.json 生成 pytest 测试代码，base URL 是 https://api.example.com
```

## Additional Resources

- For testcase field styles and examples, read [references/testcase_examples.md](references/testcase_examples.md)
