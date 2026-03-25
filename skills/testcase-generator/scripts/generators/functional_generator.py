"""
功能测试用例生成器
根据功能需求生成全面的功能测试用例
"""

import re
import json
from datetime import datetime
from typing import Dict, List, Any, Optional


class FunctionalTestGenerator:
    """功能测试用例生成器"""

    # 特殊字符测试数据
    SPECIAL_CHARS = [
        ("英文双引号", '"'),
        ("英文单引号", "'"),
        ("左尖括号", "<"),
        ("右尖括号", ">"),
        ("反斜杠", "\\"),
        ("正斜杠", "/"),
        ("&符号", "&"),
        ("等于号", "="),
        ("分号", ";"),
        ("换行符", "\n"),
        ("制表符", "\t"),
        ("NULL字符", "\x00"),
        ("表情符号", "🎉"),
        ("中文标点", "，。？！"),
        ("空格", " "),
        ("多个空格", "   "),
    ]

    # 边界值数据
    BOUNDARY_VALUES = {
        'int': [-2147483649, -2147483648, -1, 0, 1, 2147483647, 2147483648],
        'str': ['', 'a' * 255, 'a' * 256, 'a' * 1000, 'a' * 10000],
        'float': [-1.7976931348623157e+308, -1.0, 0, 1.0, 1.7976931348623157e+308],
    }

    def __init__(self, module_name: str = "Module"):
        self.module_name = module_name
        self.testcase_id = 1
        self.testcases = []
        self.current_feature_name = module_name
        self.generated_case_keys = set()

    def generate(self, feature: Dict[str, Any]) -> List[Dict]:
        """
        根据功能描述生成测试用例

        Args:
            feature: 功能描述字典，包含 name, description, fields 等

        Returns:
            测试用例列表
        """
        self.testcases = []
        self.generated_case_keys = set()
        feature_name = feature.get('name', self.module_name)
        self.current_feature_name = feature_name
        fields = feature.get('fields', [])
        description = feature.get('description', '')
        rules = feature.get('rules', [])

        # 生成正向测试用例
        self._generate_positive_tests(feature_name, fields)

        # 根据需求规则生成更贴近业务语义的用例
        self._generate_rule_based_tests(feature_name, description, rules)

        # 生成反向测试用例
        self._generate_negative_tests(feature_name, fields, description, rules)

        # 生成边界值测试用例
        self._generate_boundary_tests(feature_name, fields, description, rules)

        # 生成安全测试用例
        self._generate_security_tests(feature_name, description, rules)

        # 生成兼容性测试用例
        self._generate_compatibility_tests(feature_name, description)

        return self.testcases

    def _generate_positive_tests(self, feature_name: str, fields: List[Dict]):
        """生成正向测试用例"""
        # P0: 主流程测试
        self._add_testcase(
            key=f"{feature_name}:main-flow",
            title=f"验证{feature_name}主流程正常执行",
            priority="P0",
            preconditions="无",
            test_data="标准有效数据",
            steps=f"1. 进入{feature_name}页面\n2. 填写所有必填字段\n3. 提交请求\n4. 验证结果",
            expected="功能正常执行，返回成功结果",
            category="正向"
        )

        # P1: 必填字段测试
        required_fields = [f.get('name', '') for f in fields if f.get('required', False)]
        if required_fields:
            all_fields = ", ".join(required_fields)
            self._add_testcase(
                key=f"{feature_name}:required-only",
                title=f"验证{feature_name}所有必填字段",
                priority="P0",
                preconditions="无",
                test_data=f"必填字段: {all_fields}",
                steps=f"1. 进入{feature_name}页面\n2. 仅填写必填字段\n3. 提交请求\n4. 验证结果",
                expected="功能正常执行，成功保存数据",
                category="正向"
            )

        # P1: 可选字段测试
        optional_fields = [f for f in fields if not f.get('required', False)]
        if optional_fields:
            field_names = ", ".join([f.get('name', '') for f in optional_fields[:3]])
            self._add_testcase(
                key=f"{feature_name}:required-and-optional",
                title=f"验证{feature_name}必填+可选字段组合",
                priority="P1",
                preconditions="无",
                test_data=f"必填+部分可选字段: {field_names}",
                steps=f"1. 进入{feature_name}页面\n2. 填写必填和部分可选字段\n3. 提交请求\n4. 验证结果",
                expected="功能正常执行，正确保存所有数据",
                category="正向"
            )

        # P2: 全量数据测试
        if fields:
            self._add_testcase(
                key=f"{feature_name}:all-fields",
                title=f"验证{feature_name}填写全部字段",
                priority="P2",
                preconditions="无",
                test_data="所有字段填写真实有效数据",
                steps=f"1. 进入{feature_name}页面\n2. 填写所有字段\n3. 提交请求\n4. 验证结果",
                expected="功能正常执行，所有数据正确保存",
                category="正向"
            )

    def _generate_rule_based_tests(self, feature_name: str, description: str, rules: List[Dict[str, Any]]):
        """根据结构化规则生成更通用的功能用例。"""
        for rule in [self._ensure_rule_dict(item) for item in rules]:
            categories = set(rule.get('categories', []))
            rule_text = rule.get('text', '')
            messages = rule.get('messages', [])
            limit = rule.get('limit') or 0
            default_state = rule.get('default_state')
            negative = rule.get('negative', False)

            if 'search_multiline' in categories:
                title = f"验证{feature_name}商品搜索不支持换行批量搜索" if negative else f"验证{feature_name}支持换行批量搜索"
                expected = (
                    "系统不按换行拆分商品搜索条件，或给出不支持该输入方式的提示"
                    if negative else
                    "系统按换行拆分搜索条件并返回对应结果"
                )
                self._add_testcase(
                    key=f"{feature_name}:search-multiline:{'negative' if negative else 'positive'}",
                    title=title,
                    priority="P1" if negative else "P0",
                    preconditions="已进入搜索区域",
                    test_data="多条业务对象标识，使用换行分隔",
                    steps=f"1. 进入{feature_name}\n2. 在搜索区域输入多条换行分隔的数据\n3. 点击搜索",
                    expected=expected,
                    category="反向" if negative else "业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'limit' in categories and 'search' in categories and limit:
                self._add_testcase(
                    key=f"{feature_name}:search-limit:{limit}",
                    title=f"验证{feature_name}批量搜索单次最多支持{limit}条",
                    priority="P0",
                    preconditions="已进入批量搜索区域",
                    test_data=f"恰好{limit}条合法搜索值",
                    steps=f"1. 进入{feature_name}\n2. 输入{limit}条搜索值\n3. 执行批量搜索",
                    expected=f"系统成功受理{limit}条搜索数据并返回查询结果",
                    category="边界值",
                    remark=f"规则来源: {rule_text}"
                )
                self._add_testcase(
                    key=f"{feature_name}:search-limit-over:{limit}",
                    title=f"验证{feature_name}批量搜索超过{limit}条时的限制提示",
                    priority="P1",
                    preconditions="已进入批量搜索区域",
                    test_data=f"{limit + 1}条合法搜索值",
                    steps=f"1. 进入{feature_name}\n2. 输入{limit + 1}条搜索值\n3. 执行批量搜索",
                    expected=f"系统拦截超限数据，并提示单次最多支持{limit}条",
                    category="反向",
                    remark=f"规则来源: {rule_text}"
                )

            if 'feedback_not_found' in categories:
                expected = "系统提示未找到"
                if messages:
                    expected = f"系统提示{messages[0]}"
                self._add_testcase(
                    key=f"{feature_name}:search-not-found",
                    title=f"验证{feature_name}搜索不存在数据时的提示文案",
                    priority="P0",
                    preconditions="搜索功能可用",
                    test_data="包含至少1条不存在的数据",
                    steps=f"1. 进入{feature_name}\n2. 输入不存在的数据并执行搜索\n3. 观察提示信息",
                    expected=expected,
                    category="反向",
                    remark=f"规则来源: {rule_text}"
                )

            if 'multi_select' in categories:
                self._add_testcase(
                    key=f"{feature_name}:multi-select",
                    title=f"验证{feature_name}支持多选操作",
                    priority="P0",
                    preconditions="列表存在多条可选数据",
                    test_data="至少2条业务数据",
                    steps=f"1. 进入{feature_name}\n2. 勾选多条数据\n3. 观察选择结果",
                    expected="系统允许一次选中多条数据并保留选择状态",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'selection_persistence' in categories:
                self._add_testcase(
                    key=f"{feature_name}:selection-persistence",
                    title=f"验证{feature_name}翻页后已选数据仍然保留",
                    priority="P0",
                    preconditions="列表支持分页且存在多页数据",
                    test_data="第1页和第2页各选中部分数据",
                    steps=f"1. 在{feature_name}中第1页勾选数据\n2. 切换到其他页继续勾选\n3. 再返回原页查看选中状态",
                    expected="翻页不会取消已选择的数据，已选内容持续可见",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'selection_summary' in categories:
                self._add_testcase(
                    key=f"{feature_name}:selection-summary",
                    title=f"验证{feature_name}已选内容在汇总区域展示",
                    priority="P1",
                    preconditions="已选择至少1条数据",
                    test_data="已勾选的业务数据",
                    steps=f"1. 进入{feature_name}\n2. 选择一条或多条数据\n3. 查看页面中的已选汇总区域",
                    expected="汇总区域准确展示已选择数据的名称或标识",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'toggle' in categories:
                default_text = "默认隐藏" if default_state == 'hidden' else "默认显示" if default_state == 'visible' else "符合需求定义"
                self._add_testcase(
                    key=f"{feature_name}:toggle:{default_state or 'unknown'}",
                    title=f"验证{feature_name}筛选区默认状态与展开收起",
                    priority="P1",
                    preconditions="筛选入口可见",
                    test_data="无",
                    steps=f"1. 进入{feature_name}\n2. 观察筛选区域默认状态\n3. 点击图标切换展开或收起",
                    expected=f"筛选区域初始状态{default_text}，点击后可正确显示或隐藏相关条件",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'search_filters' in categories:
                self._add_testcase(
                    key=f"{feature_name}:search-filters",
                    title=f"验证{feature_name}支持多维度筛选搜索",
                    priority="P1",
                    preconditions="搜索和筛选区域可见",
                    test_data="文档声明的不同搜索条件组合",
                    steps=f"1. 进入{feature_name}\n2. 分别使用不同筛选条件执行搜索\n3. 观察结果列表",
                    expected="系统支持需求文档中声明的搜索维度，且返回结果与筛选条件一致",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'remove_restore' in categories:
                self._add_testcase(
                    key=f"{feature_name}:remove-restore",
                    title=f"验证{feature_name}移除后可重新添加并影响执行结果",
                    priority="P0",
                    preconditions="已选中待操作数据",
                    test_data="1条待移除数据",
                    steps=f"1. 在{feature_name}中选中数据\n2. 将其中1条从已选区域移除\n3. 确认其不参与本次操作\n4. 再重新添加该数据",
                    expected="被移除数据不会参与当前操作；重新添加后可再次参与执行",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'dialog_display' in categories:
                self._add_testcase(
                    key=f"{feature_name}:dialog-display",
                    title=f"验证{feature_name}弹窗展示关键业务信息",
                    priority="P0",
                    preconditions="已选择待处理数据",
                    test_data="至少1条业务数据",
                    steps=f"1. 进入{feature_name}\n2. 选择数据后触发对应操作\n3. 查看弹窗中的展示内容",
                    expected="弹窗准确展示需求文档约定的关键业务信息，并支持继续操作",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'batch_edit' in categories:
                self._add_testcase(
                    key=f"{feature_name}:batch-edit",
                    title=f"验证{feature_name}支持批量填写或批量修改",
                    priority="P1",
                    preconditions="批量编辑入口可见",
                    test_data="统一的批量编辑值",
                    steps=f"1. 进入{feature_name}\n2. 点击批量编辑入口\n3. 输入统一值并确认",
                    expected="系统将批量填写的值应用到目标数据，并在界面中正确回显",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'state_retention' in categories:
                self._add_testcase(
                    key=f"{feature_name}:state-retention",
                    title=f"验证{feature_name}返回上一步后已填数据仍然保留",
                    priority="P0",
                    preconditions="已完成上一步数据填写",
                    test_data="已编辑的流程数据",
                    steps=f"1. 在{feature_name}流程中进入下一步\n2. 点击返回上一步\n3. 检查上一步页面中的已填写数据",
                    expected="返回后系统保留当前已填信息，无需重新录入",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'data_sync' in categories:
                self._add_testcase(
                    key=f"{feature_name}:data-sync",
                    title=f"验证{feature_name}执行后增量同步关联数据",
                    priority="P0",
                    preconditions="存在当前版本及目标版本关联数据",
                    test_data="按需求示例准备当前与未来版本数据",
                    steps=f"1. 在{feature_name}中执行目标操作\n2. 检查当前数据变化\n3. 检查关联版本或目标数据",
                    expected="系统按需求描述进行增量同步更新，不会出现全量覆盖或漏同步",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'audit_record' in categories:
                self._add_testcase(
                    key=f"{feature_name}:audit-record",
                    title=f"验证{feature_name}任务记录写入管理台",
                    priority="P1",
                    preconditions="已触发相关业务任务",
                    test_data="1次成功任务或失败任务",
                    steps=f"1. 在{feature_name}中执行任务\n2. 进入任务管理或导入导出管理页面\n3. 查看任务记录和文件信息",
                    expected="系统生成对应任务记录，文件名称、文件类型及下载信息符合需求定义",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'feedback_success' in categories:
                success_message = messages[0] if messages else "任务成功"
                self._add_testcase(
                    key=f"{feature_name}:feedback-success",
                    title=f"验证{feature_name}操作成功时的页面反馈",
                    priority="P1",
                    preconditions="任务可成功执行",
                    test_data="合法业务数据",
                    steps=f"1. 在{feature_name}中发起任务\n2. 等待任务成功完成\n3. 观察页面提示",
                    expected=f"任务成功后页面直接反馈成功结果，如 {success_message}",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

            if 'feedback_failure' in categories:
                failure_message = messages[0] if messages else "操作失败，请前往详情页查看"
                self._add_testcase(
                    key=f"{feature_name}:feedback-failure",
                    title=f"验证{feature_name}操作失败时的页面反馈与引导",
                    priority="P1",
                    preconditions="构造可触发失败的业务数据",
                    test_data="部分异常或非法数据",
                    steps=f"1. 在{feature_name}中发起任务\n2. 等待任务失败或部分失败\n3. 观察页面提示并检查详情入口",
                    expected=f"页面给出失败提示并引导用户查看详情，如 {failure_message}",
                    category="反向",
                    remark=f"规则来源: {rule_text}"
                )

            if 'action_precondition' in categories:
                warning_message = messages[0] if messages else "请先完成前置操作"
                self._add_testcase(
                    key=f"{feature_name}:action-precondition",
                    title=f"验证{feature_name}缺少前置条件时的拦截提示",
                    priority="P0",
                    preconditions="未满足规则要求的前置条件",
                    test_data="无",
                    steps=f"1. 进入{feature_name}\n2. 不满足前置条件直接执行操作\n3. 观察提示信息",
                    expected=f"系统拦截当前操作，并提示 {warning_message}",
                    category="反向",
                    remark=f"规则来源: {rule_text}"
                )

            if 'pagination' in categories and limit:
                self._add_testcase(
                    key=f"{feature_name}:pagination:{limit}",
                    title=f"验证{feature_name}分页默认每页显示{limit}条",
                    priority="P1",
                    preconditions=f"列表数据量大于{limit}条",
                    test_data=f"至少{limit + 1}条列表数据",
                    steps=f"1. 进入{feature_name}\n2. 观察列表默认分页数量\n3. 切换页码检查分页效果",
                    expected=f"列表默认单页展示{limit}条数据，翻页逻辑正常",
                    category="边界值",
                    remark=f"规则来源: {rule_text}"
                )

            if 'visibility_control' in categories:
                self._add_testcase(
                    key=f"{feature_name}:visibility-control",
                    title=f"验证{feature_name}按需求隐藏指定入口或控件",
                    priority="P1",
                    preconditions="用户已进入对应模块",
                    test_data="无",
                    steps=f"1. 进入{feature_name}相关页面\n2. 检查需求中要求隐藏的按钮、菜单或页面入口",
                    expected="被要求隐藏的功能入口对当前用户不可见且不可触达",
                    category="业务规则",
                    remark=f"规则来源: {rule_text}"
                )

    def _generate_negative_tests(self, feature_name: str, fields: List[Dict], description: str, rules: List[Dict[str, Any]]):
        """生成反向测试用例"""
        # P0: 缺少必填字段
        if fields:
            required_fields = [f for f in fields if f.get('required', False)]
            for field in required_fields[:2]:  # 限制数量
                self._add_testcase(
                    key=f"{feature_name}:missing-required:{field.get('name', '')}",
                    title=f"验证{feature_name}缺少必填字段【{field.get('name', '')}】",
                    priority="P0",
                    preconditions="无",
                    test_data=f"缺少字段: {field.get('name', '')}",
                    steps=f"1. 进入{feature_name}页面\n2. 不填写【{field.get('name', '')}】\n3. 提交请求",
                    expected=f"系统提示【{field.get('name', '该字段')}】不能为空",
                    category="反向"
                )

        # P1: 空值测试
        if fields:
            self._add_testcase(
                key=f"{feature_name}:all-empty",
                title=f"验证{feature_name}所有字段为空",
                priority="P1",
                preconditions="无",
                test_data="所有字段留空",
                steps=f"1. 进入{feature_name}页面\n2. 所有字段留空\n3. 提交请求",
                expected="系统提示必填字段不能为空",
                category="反向"
            )

        content = self._normalize_text(description + ' ' + self._join_rule_texts(rules))
        if any(keyword in content for keyword in ['输入', '填写', '搜索']):
            self._add_testcase(
                key=f"{feature_name}:input-too-long",
                title=f"验证{feature_name}输入超长字符时的处理",
                priority="P2",
                preconditions="对应输入框可编辑",
                test_data="超过长度限制的超长文本",
                steps=f"1. 进入{feature_name}\n2. 在可输入区域填写超长内容\n3. 提交或执行查询",
                expected="系统对超长内容进行拦截、截断或错误提示，且不会导致页面异常",
                category="反向"
            )

        # P2: 重复提交
        if any(keyword in content for keyword in ['提交', '确认', '执行']):
            self._add_testcase(
                key=f"{feature_name}:duplicate-submit",
                title=f"验证{feature_name}重复提交",
                priority="P2",
                preconditions="首次提交成功",
                test_data="与首次相同的数据",
                steps=f"1. 完成{feature_name}并提交\n2. 立即再次提交相同数据",
                expected="系统正确处理重复提交（成功、拦截或提示已存在），不会产生脏数据",
                category="反向"
            )

    def _generate_boundary_tests(self, feature_name: str, fields: List[Dict], description: str, rules: List[Dict[str, Any]]):
        """生成边界值测试用例"""
        # P1: 数值边界
        numeric_fields = [field for field in fields if field.get('type') in {'int', 'float'}]
        if numeric_fields:
            self._add_testcase(
                key=f"{feature_name}:numeric-lower-bound",
                title=f"验证{feature_name}数值下边界",
                priority="P1",
                preconditions="无",
                test_data="数值字段使用最小允许值",
                steps=f"1. 进入{feature_name}页面\n2. 填写最小数值\n3. 提交请求",
                expected="功能正常执行，数据正确保存",
                category="边界值"
            )

            self._add_testcase(
                key=f"{feature_name}:numeric-upper-bound",
                title=f"验证{feature_name}数值上边界",
                priority="P1",
                preconditions="无",
                test_data="数值字段使用最大允许值",
                steps=f"1. 进入{feature_name}页面\n2. 填写最大数值\n3. 提交请求",
                expected="功能正常执行，数据正确保存",
                category="边界值"
            )

        # P2: 字符串长度边界
        if fields:
            self._add_testcase(
                key=f"{feature_name}:string-length-boundary",
                title=f"验证{feature_name}字符串长度边界",
                priority="P2",
                preconditions="无",
                test_data="字符串字段使用边界长度（255字符）",
                steps=f"1. 进入{feature_name}页面\n2. 输入255字符\n3. 提交请求",
                expected="功能正常执行，数据正确保存",
                category="边界值"
            )

    def _generate_security_tests(self, feature_name: str, description: str, rules: List[Dict[str, Any]]):
        """生成安全测试用例"""
        content = self._normalize_text(description + ' ' + self._join_rule_texts(rules))
        if not any(keyword in content for keyword in ['输入', '搜索', '填写', '批量']):
            return

        # P0: SQL 注入
        sql_injection_tests = [
            ("单引号", "'"),
            ("OR 1=1", "' OR '1'='1"),
            ("UNION查询", "' UNION SELECT * FROM users--"),
            ("注释符", "admin'--"),
            ("DROP语句", "'; DROP TABLE users--"),
        ]

        for name, value in sql_injection_tests[:1]:
            self._add_testcase(
                key=f"{feature_name}:sql-injection:{name}",
                title=f"验证{feature_name}SQL注入攻击【{name}】",
                priority="P0",
                preconditions="无",
                test_data=f"输入SQL注入内容: {value[:30]}...",
                steps=f"1. 进入{feature_name}页面\n2. 输入SQL注入字符串\n3. 提交请求",
                expected="系统正确转义或拒绝，数据不被执行",
                category="安全",
                remark="安全测试用例"
            )

        # P1: XSS 攻击
        xss_tests = [
            ("script标签", "<script>alert('xss')</script>"),
            ("img标签", "<img src=x onerror=alert('xss')>"),
            ("svg标签", "<svg onload=alert('xss')>"),
            ("JavaScript协议", "javascript:alert('xss')"),
        ]

        for name, value in xss_tests[:1]:
            self._add_testcase(
                key=f"{feature_name}:xss:{name}",
                title=f"验证{feature_name}XSS攻击【{name}】",
                priority="P1",
                preconditions="无",
                test_data=f"输入XSS内容: {value[:30]}...",
                steps=f"1. 进入{feature_name}页面\n2. 输入XSS字符串\n3. 提交请求",
                expected="系统正确转义，脚本不被执行",
                category="安全",
                remark="安全测试用例"
            )

    def _generate_compatibility_tests(self, feature_name: str, description: str):
        """生成兼容性测试用例"""
        if not any(keyword in description for keyword in ['页面', '列表', '弹窗', '搜索', '按钮']):
            return

        # 浏览器兼容
        browsers = [
            ("Chrome", "Chrome 最新版本"),
            ("Edge", "Edge 最新版本"),
        ]

        for browser, desc in browsers:
            self._add_testcase(
                key=f"{feature_name}:browser:{browser}",
                title=f"验证{feature_name}在{browser}浏览器",
                priority="P1",
                preconditions=f"安装{browser}浏览器",
                test_data="标准有效数据",
                steps=f"1. 打开{browser}浏览器\n2. 进入{feature_name}\n3. 执行标准操作",
                expected=f"{desc}下功能正常",
                category="兼容性",
                remark=f"浏览器兼容性测试 - {browser}"
            )

        # 移动端兼容
        self._add_testcase(
            key=f"{feature_name}:mobile:android-chrome",
            title=f"验证{feature_name}在Android Chrome端",
            priority="P1",
            preconditions="使用 Android 手机 Chrome",
            test_data="标准有效数据",
            steps=f"1. 打开Android Chrome\n2. 进入{feature_name}\n3. 执行标准操作",
            expected="Android 手机 Chrome 下功能正常",
            category="兼容性",
            remark="移动端兼容性测试 - Android Chrome"
        )

    def _ensure_rule_dict(self, rule: Any) -> Dict[str, Any]:
        """兼容字符串规则和结构化规则。"""
        if isinstance(rule, dict):
            return rule
        normalized = self._normalize_text(str(rule))
        return {
            'text': str(rule),
            'normalized_text': normalized,
            'categories': [],
            'negative': False,
            'limit': 0,
            'messages': [],
            'default_state': ''
        }

    def _join_rule_texts(self, rules: List[Any]) -> str:
        """拼接规则原文，便于做兜底关键词判断。"""
        texts = []
        for rule in rules:
            rule_data = self._ensure_rule_dict(rule)
            texts.append(rule_data.get('text', ''))
        return ' '.join(texts)

    def _normalize_text(self, text: str) -> str:
        """归一化文本，便于关键词匹配。"""
        return re.sub(r'\s+', '', text or '')

    def _add_testcase(self, key: str, title: str, priority: str, preconditions: str,
                      test_data: str, steps: str, expected: str,
                      category: str = "功能", remark: str = ""):
        """按业务 key 去重后添加测试用例。"""
        if key in self.generated_case_keys:
            return
        self.generated_case_keys.add(key)
        self.testcases.append(self._create_testcase(
            title=title,
            priority=priority,
            preconditions=preconditions,
            test_data=test_data,
            steps=steps,
            expected=expected,
            category=category,
            remark=remark
        ))

    def _create_testcase(self, title: str, priority: str, preconditions: str,
                         test_data: str, steps: str, expected: str,
                         category: str = "功能", remark: str = "") -> Dict:
        """创建单个测试用例"""
        tc = {
            "功能ID": f"FUNC_{self.module_name.upper()}_{self.testcase_id:03d}",
            "用例标题": title,
            "功能模块": self.current_feature_name,
            "优先级": priority,
            "预置条件": preconditions,
            "测试数据": test_data,
            "执行步骤": steps,
            "预期结果": expected,
            "测试结果": "待执行",
            "测试版本号": "v1.0.0",
            "测试人员": "",
            "备注": remark,
            "测试类型": category,
            "断言来源": "需求文档推导",
            "是否为假设": "是"
        }
        self.testcase_id += 1
        return tc


# 便捷函数
def generate_functional_testcases(module_name: str, features: List[Dict]) -> List[Dict]:
    """生成功能测试用例"""
    generator = FunctionalTestGenerator(module_name)
    all_cases = []
    for feature in features:
        all_cases.extend(generator.generate(feature))
    return all_cases
