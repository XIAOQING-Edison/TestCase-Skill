"""
API 测试用例生成器
根据 API 定义生成全面的接口测试用例
"""

import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class APITestGenerator:
    """API 测试用例生成器"""

    # HTTP 状态码分类
    STATUS_CODES = {
        'success': [200, 201, 204],
        'client_error': [400, 401, 403, 404, 405, 422],
        'server_error': [500, 502, 503, 504]
    }

    def __init__(self, base_url: str = "", module_name: str = "API"):
        self.base_url = base_url
        self.module_name = module_name
        self.testcase_id = 1
        self.testcases = []

    def generate(self, api: Dict[str, Any]) -> List[Dict]:
        """
        根据 API 定义生成测试用例

        Args:
            api: API 定义字典，包含 method, url, parameters, request_body 等

        Returns:
            测试用例列表
        """
        self.testcases = []
        api_name = api.get('name', self.module_name)
        method = api.get('method', 'GET')
        path = api.get('path', api.get('url', ''))
        full_url = api.get('url', path)
        parameters = api.get('parameters', [])
        request_body = api.get('request_body', {})
        responses = api.get('responses', {})

        # 生成正向测试用例
        self._generate_positive_tests(api_name, method, full_url, parameters, request_body, responses)

        # 生成反向测试用例
        self._generate_negative_tests(api_name, method, full_url, parameters, request_body, responses)

        # 生成安全测试用例
        self._generate_security_tests(api_name, method, full_url, request_body, responses)

        # 生成性能测试用例
        self._generate_performance_tests(api_name, method, full_url, responses)

        return self.testcases

    def _generate_positive_tests(self, api_name: str, method: str, url: str,
                                  parameters: List, request_body: Dict, responses: Dict):
        """生成正向测试用例"""
        success_expectation = self._resolve_expectation(
            responses,
            preferred_statuses=['200', '201', '202', '204'],
            fallback_note="文档未提供成功响应定义，请确认成功状态码、响应字段和业务返回值。"
        )

        # P0: 正常请求
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}正常请求成功",
            priority="P0",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=self._sample_body(request_body),
            expected_status=success_expectation['status'],
            expected=success_expectation['expected'],
            category="正向",
            assertion_source=success_expectation['source'],
            is_assumption=success_expectation['is_assumption']
        ))

        # P0: 必填参数
        required_params = [p for p in parameters if p.get('required', False)]
        if required_params:
            required_only_expectation = self._resolve_expectation(
                responses,
                preferred_statuses=['200', '201', '202', '204'],
                fallback_note="文档未说明仅传必填参数时的返回结果，请确认是否允许省略可选参数。"
            )
            params = {p.get('name', ''): self._sample_value(p) for p in required_params}
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}仅传必填参数",
                priority="P0",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps(params, ensure_ascii=False) if method in ['POST', 'PUT', 'PATCH'] else "",
                expected_status=required_only_expectation['status'],
                expected=required_only_expectation['expected'],
                category="正向",
                assertion_source=required_only_expectation['source'],
                is_assumption=required_only_expectation['is_assumption']
            ))

        # P1: 可选参数
        optional_params = [p for p in parameters if not p.get('required', False)]
        if optional_params:
            all_params_expectation = self._resolve_expectation(
                responses,
                preferred_statuses=['200', '201', '202', '204'],
                fallback_note="文档未说明传递全部参数时的返回结果，请确认响应字段是否会随可选参数变化。"
            )
            all_params = {p.get('name', ''): self._sample_value(p) for p in parameters}
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}传递全部参数",
                priority="P1",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps(all_params, ensure_ascii=False) if method in ['POST', 'PUT', 'PATCH'] else "",
                expected_status=all_params_expectation['status'],
                expected=all_params_expectation['expected'],
                category="正向",
                assertion_source=all_params_expectation['source'],
                is_assumption=all_params_expectation['is_assumption']
            ))

        # P1: 响应字段验证
        response_schema_expectation = self._resolve_schema_assertion(responses)
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}响应字段完整性",
            priority="P1",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=self._sample_body(request_body),
            expected_status=response_schema_expectation['status'],
            expected=response_schema_expectation['expected'],
            category="正向",
            remark="验证响应数据结构",
            assertion_source=response_schema_expectation['source'],
            is_assumption=response_schema_expectation['is_assumption']
        ))

    def _generate_negative_tests(self, api_name: str, method: str, url: str,
                                  parameters: List, request_body: Dict, responses: Dict):
        """生成反向测试用例"""
        validation_expectation = self._resolve_expectation(
            responses,
            preferred_statuses=['400', '422'],
            fallback_note="文档未提供参数校验失败响应定义，请确认错误状态码、错误码和提示文案。"
        )
        wrong_method_expectation = self._resolve_expectation(
            responses,
            preferred_statuses=['405'],
            fallback_note="文档未提供错误请求方法的响应定义，请确认是否返回 405 及错误文案。"
        )

        # P0: 缺少必填参数
        required_params = [p for p in parameters if p.get('required', False)]
        if required_params:
            param = required_params[0]
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}缺少必填参数【{param.get('name', '')}】",
                priority="P0",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=self._body_without_field(request_body, param.get('name', '')),
                expected_status=validation_expectation['status'],
                expected=validation_expectation['expected'],
                category="反向",
                assertion_source=validation_expectation['source'],
                is_assumption=validation_expectation['is_assumption']
            ))

        # P1: 参数类型错误
        if parameters:
            param = parameters[0]
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}参数类型错误",
                priority="P1",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps({param.get('name', ''): "string_instead_of_int"}, ensure_ascii=False),
                expected_status=validation_expectation['status'],
                expected=validation_expectation['expected'],
                category="反向",
                assertion_source=validation_expectation['source'],
                is_assumption=validation_expectation['is_assumption']
            ))

        # P1: 无效 JSON
        if method in ['POST', 'PUT', 'PATCH']:
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}无效JSON格式",
                priority="P1",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data="{invalid json: true}",
                expected_status=validation_expectation['status'],
                expected=validation_expectation['expected'],
                category="反向",
                assertion_source=validation_expectation['source'],
                is_assumption=validation_expectation['is_assumption']
            ))

        # P1: 数值越界
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}数值参数越界",
            priority="P1",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=json.dumps({"page": -1}, ensure_ascii=False),
            expected_status=validation_expectation['status'],
            expected=validation_expectation['expected'],
            category="反向",
            assertion_source=validation_expectation['source'],
            is_assumption=validation_expectation['is_assumption']
        ))

        # P2: 空值处理
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}参数值为空字符串",
            priority="P2",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=json.dumps({"name": ""}, ensure_ascii=False),
            expected_status=validation_expectation['status'],
            expected=validation_expectation['expected'],
            category="反向",
            assertion_source=validation_expectation['source'],
            is_assumption=validation_expectation['is_assumption']
        ))

        # P2: 超长字符串
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}字符串参数超长",
            priority="P2",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data=json.dumps({"name": "x" * 10000}, ensure_ascii=False),
            expected_status=validation_expectation['status'],
            expected=validation_expectation['expected'],
            category="反向",
            assertion_source=validation_expectation['source'],
            is_assumption=validation_expectation['is_assumption']
        ))

        # P1: 方法不允许
        allowed_methods = ['GET', 'POST', 'PUT', 'DELETE', 'PATCH']
        wrong_method = [m for m in allowed_methods if m != method.upper() and m in allowed_methods]
        if wrong_method:
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}不允许的请求方法",
                priority="P1",
                preconditions="无",
                url=url,
                method=wrong_method[0],
                headers={"Content-Type": "application/json"},
                params_type="json",
                data="{}",
                expected_status=wrong_method_expectation['status'],
                expected=wrong_method_expectation['expected'],
                category="反向",
                assertion_source=wrong_method_expectation['source'],
                is_assumption=wrong_method_expectation['is_assumption']
            ))

    def _generate_security_tests(self, api_name: str, method: str, url: str, request_body: Dict, responses: Dict):
        """生成安全测试用例"""
        forbidden_expectation = self._resolve_expectation(
            responses,
            preferred_statuses=['400', '403', '422'],
            fallback_note="文档未提供安全拦截场景的响应定义，请确认拦截状态码和错误文案。"
        )
        unauthorized_expectation = self._resolve_expectation(
            responses,
            preferred_statuses=['401'],
            fallback_note="文档未提供未授权访问的响应定义，请确认认证失败状态码与错误信息。"
        )
        forbidden_permission_expectation = self._resolve_expectation(
            responses,
            preferred_statuses=['403'],
            fallback_note="文档未提供权限不足的响应定义，请确认权限校验失败的状态码与错误信息。"
        )

        # P0: SQL 注入
        sql_injections = [
            ("单引号", "'"),
            ("OR 1=1", "' OR '1'='1"),
            ("UNION查询", "' UNION SELECT * FROM users--"),
        ]

        for name, value in sql_injections[:1]:
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}SQL注入攻击【{name}】",
                priority="P0",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps({"keyword": value}, ensure_ascii=False),
                expected_status=forbidden_expectation['status'],
                expected=forbidden_expectation['expected'],
                category="安全",
                assertion_source=forbidden_expectation['source'],
                is_assumption=forbidden_expectation['is_assumption']
            ))

        # P1: XSS 注入
        xss_injections = [
            ("script标签", "<script>alert('xss')</script>"),
            ("img标签", "<img src=x onerror=alert('xss')>"),
        ]

        for name, value in xss_injections[:1]:
            self.testcases.append(self._create_testcase(
                title=f"验证{api_name}XSS注入攻击【{name}】",
                priority="P1",
                preconditions="无",
                url=url,
                method=method,
                headers={"Content-Type": "application/json"},
                params_type="json",
                data=json.dumps({"content": value}, ensure_ascii=False),
                expected_status=forbidden_expectation['status'],
                expected=forbidden_expectation['expected'],
                category="安全",
                assertion_source=forbidden_expectation['source'],
                is_assumption=forbidden_expectation['is_assumption']
            ))

        # P0: 未授权访问
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}未授权访问",
            priority="P0",
            preconditions="无 Token",
            url=url,
            method=method,
            headers={},
            params_type="json",
            data="{}",
            expected_status=unauthorized_expectation['status'],
            expected=unauthorized_expectation['expected'],
            category="安全",
            assertion_source=unauthorized_expectation['source'],
            is_assumption=unauthorized_expectation['is_assumption']
        ))

        # P1: Token 过期
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}Token过期",
            priority="P1",
            preconditions="Token 已过期",
            url=url,
            method=method,
            headers={"Authorization": "Bearer expired_token"},
            params_type="json",
            data="{}",
            expected_status=unauthorized_expectation['status'],
            expected=unauthorized_expectation['expected'],
            category="安全",
            assertion_source=unauthorized_expectation['source'],
            is_assumption=unauthorized_expectation['is_assumption']
        ))

        # P1: 权限不足
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}权限不足",
            priority="P1",
            preconditions="使用普通用户 Token",
            url=url,
            method=method,
            headers={"Authorization": "Bearer normal_user_token"},
            params_type="json",
            data="{}",
            expected_status=forbidden_permission_expectation['status'],
            expected=forbidden_permission_expectation['expected'],
            category="安全",
            assertion_source=forbidden_permission_expectation['source'],
            is_assumption=forbidden_permission_expectation['is_assumption']
        ))

    def _generate_performance_tests(self, api_name: str, method: str, url: str, responses: Dict):
        """生成性能测试用例"""
        success_expectation = self._resolve_expectation(
            responses,
            preferred_statuses=['200', '201', '202', '204'],
            fallback_note="文档未提供成功响应定义，请先确认功能响应，再补充性能阈值。"
        )
        performance_expectation = self._build_assumption_expectation(
            status=success_expectation['status'],
            note="文档未提供性能 SLA，请确认响应时间、成功率和并发阈值。",
            source="性能阈值待确认"
        )

        # P1: 响应时间
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}响应时间小于1秒",
            priority="P1",
            preconditions="网络环境正常",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data="{}",
            expected_status=performance_expectation['status'],
            expected=performance_expectation['expected'],
            category="性能",
            assertion_source=f"{success_expectation['source']}；{performance_expectation['source']}",
            is_assumption="是"
        ))

        # P2: 并发请求
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}10并发请求",
            priority="P2",
            preconditions="无",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data="{}",
            expected_status=performance_expectation['status'],
            expected=performance_expectation['expected'],
            category="性能",
            remark="需要使用 JMeter 或 Locust 执行",
            assertion_source=f"{success_expectation['source']}；{performance_expectation['source']}",
            is_assumption="是"
        ))

        # P2: 负载测试
        self.testcases.append(self._create_testcase(
            title=f"验证{api_name}100并发负载",
            priority="P2",
            preconditions="服务器已准备",
            url=url,
            method=method,
            headers={"Content-Type": "application/json"},
            params_type="json",
            data="{}",
            expected_status=performance_expectation['status'],
            expected=performance_expectation['expected'],
            category="性能",
            remark="需要使用压力测试工具",
            assertion_source=f"{success_expectation['source']}；{performance_expectation['source']}",
            is_assumption="是"
        ))

    def _create_testcase(self, title: str, priority: str, preconditions: str,
                         url: str, method: str, headers: Dict, params_type: str,
                         data: str, expected_status: int, expected: str,
                         category: str = "接口", remark: str = "",
                         assertion_source: str = "未标注", is_assumption: str = "否") -> Dict:
        """创建单个测试用例"""
        tc = {
            "用例编号": f"API_{self.module_name.upper()}_{self.testcase_id:03d}",
            "用例标题": title,
            "模块/优先级": f"{self.module_name}/{priority}",
            "接口名称": self.module_name,
            "前置条件": preconditions,
            "请求URL": url,
            "请求类型": method,
            "请求头": self._format_headers(headers),
            "请求参数类型": params_type,
            "请求数据": data,
            "预期响应状态": expected_status,
            "预期响应信息": expected,
            "实际响应信息": "",
            "是否通过": "待执行",
            "测试类型": category,
            "备注": remark,
            "断言来源": assertion_source,
            "是否为假设": is_assumption
        }
        self.testcase_id += 1
        return tc

    def _format_headers(self, headers: Dict) -> str:
        """格式化请求头"""
        return '\n'.join([f"{k}: {v}" for k, v in headers.items()])

    def _sample_body(self, request_body: Dict) -> str:
        """生成示例请求体"""
        if request_body.get('type') == 'none':
            return ""
        content = request_body.get('content', {})
        if isinstance(content, dict):
            return json.dumps(content, ensure_ascii=False, indent=2)
        return content if content else "{}"

    def _sample_value(self, param: Dict) -> Any:
        """生成示例参数值"""
        param_type = param.get('type', 'string').lower()
        default = param.get('default', '')

        if default:
            return default

        if 'int' in param_type or 'number' in param_type:
            return 1
        elif 'bool' in param_type:
            return True
        elif 'array' in param_type or 'list' in param_type:
            return []
        elif 'object' in param_type:
            return {}
        else:
            return "sample_value"

    def _body_without_field(self, request_body: Dict, field_name: str) -> str:
        """生成移除指定字段的请求体"""
        content = request_body.get('content', {})
        if isinstance(content, dict) and field_name in content:
            del content[field_name]
            return json.dumps(content, ensure_ascii=False)
        return "{}"

    def _normalize_status(self, status: Any) -> Any:
        """标准化响应状态码。"""
        if isinstance(status, int):
            return status
        if isinstance(status, str) and status.isdigit():
            return int(status)
        return status

    def _documented_response(self, responses: Dict, preferred_statuses: List[str]) -> Dict[str, Any]:
        """按优先级查找文档中定义的响应。"""
        if not isinstance(responses, dict):
            return {}

        for status in preferred_statuses:
            response = responses.get(status)
            if response:
                return {'status': self._normalize_status(status), 'response': response}

        return {}

    def _serialize_response(self, response: Dict) -> str:
        """将文档中的响应定义转成可展示的断言内容。"""
        description = response.get('description', '').strip()
        schemas = response.get('schemas', [])
        if schemas:
            schema = schemas[0].get('schema', {})
            if schema:
                return json.dumps(schema, ensure_ascii=False)
        if description:
            return description
        return "接口文档已定义响应，但未提供可直接断言的响应体示例。"

    def _resolve_expectation(self, responses: Dict, preferred_statuses: List[str], fallback_note: str) -> Dict[str, Any]:
        """优先使用接口文档中的响应定义，否则显式标记为待确认。"""
        documented = self._documented_response(responses, preferred_statuses)
        if documented:
            return {
                'status': documented['status'],
                'expected': self._serialize_response(documented['response']),
                'source': f"接口文档响应定义（{documented['status']}）",
                'is_assumption': "否"
            }

        return self._build_assumption_expectation(
            status="待确认",
            note=fallback_note,
            source="待确认（文档未提供对应响应定义）"
        )

    def _resolve_schema_assertion(self, responses: Dict) -> Dict[str, Any]:
        """提取文档中的成功响应 schema，用于字段完整性验证。"""
        documented = self._documented_response(responses, ['200', '201', '202', '204'])
        if documented:
            response = documented['response']
            schemas = response.get('schemas', [])
            if schemas and schemas[0].get('schema'):
                return {
                    'status': documented['status'],
                    'expected': f"响应体应包含文档 schema 定义的字段：{json.dumps(schemas[0].get('schema', {}), ensure_ascii=False)}",
                    'source': f"接口文档 schema（{documented['status']}）",
                    'is_assumption': "否"
                }

        return self._build_assumption_expectation(
            status="待确认",
            note="文档未提供可用于字段校验的响应 schema，请补充成功响应结构。",
            source="待确认（文档未提供响应 schema）"
        )

    def _build_assumption_expectation(self, status: Any, note: str, source: str) -> Dict[str, Any]:
        """构建待确认的断言结果。"""
        return {
            'status': status,
            'expected': f"待确认：{note}",
            'source': source,
            'is_assumption': "是"
        }


# 便捷函数
def generate_api_testcases(base_url: str, module_name: str, apis: List[Dict]) -> List[Dict]:
    """生成 API 测试用例"""
    generator = APITestGenerator(base_url, module_name)
    all_cases = []
    for api in apis:
        all_cases.extend(generator.generate(api))
    return all_cases
