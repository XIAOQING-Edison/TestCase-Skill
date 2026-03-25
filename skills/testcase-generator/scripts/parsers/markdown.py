"""
Markdown 文档解析器
支持解析 API 文档和需求文档的 Markdown / Text 格式
"""

import os
import re
from typing import Dict, List, Any, Tuple


class MarkdownParser:
    """Markdown 文档解析器"""

    IGNORED_REQUIREMENT_HEADINGS = {
        '简介', '概述', '背景', '范围', '目标', '说明', '备注', '附录',
        '验收标准', '非功能需求', '业务规则', '流程说明', '术语说明',
        '文档介绍', '文档概述', '修订历史', '名词解释', '产品描述',
        '需求概述', '竞品分析', '流程图', '状态机', '产品功能清单',
        '用户角色权限', '功能概述', '功能属性', '所属板块', '功能说明', '功能交互'
    }

    REQUIREMENT_SECTION_MARKERS = [
        '功能需求描述', '产品功能清单', '页面名称', '功能说明',
        '所属板块', '用户角色权限', '涉众分析'
    ]

    def __init__(self, source: str):
        self.source = source
        self.raw_content = self._load_content(source)
        self.lines = self.raw_content.splitlines()
        self.cleaned_lines = [self._sanitize_line(line) for line in self.lines]

    def _load_content(self, source: str) -> str:
        """加载 Markdown 内容，支持文件路径或直接传入内容。"""
        if os.path.exists(source):
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
        return source

    def _sanitize_line(self, line: str) -> str:
        """移除需求文档中的图片占位、HTML 标记和无关噪音。"""
        line = re.sub(
            r'<MagicCompressibleContent[^>]*>.*?```oss-file.*?```.*?</MagicCompressibleContent>',
            '',
            line,
            flags=re.IGNORECASE
        )
        line = re.sub(r'```oss-file.*?```', '', line, flags=re.IGNORECASE)
        line = re.sub(r'<[^>]+>', '', line)
        line = line.replace('**', '')
        line = re.sub(r'\s+', ' ', line)
        return line.strip()

    def parse(self) -> List[Dict[str, Any]]:
        """解析并返回接口列表或功能列表"""
        if self.detect_doc_type() == 'api':
            return self._parse_api_doc()
        return self._parse_requirement_doc()

    def detect_doc_type(self) -> str:
        """检测当前文档更像 API 文档还是需求文档。"""
        return 'api' if self._is_api_doc_format() else 'requirement'

    def _is_api_doc_format(self) -> bool:
        """检测是否为 API 文档格式"""
        content = '\n'.join(self.cleaned_lines).lower()
        requirement_markers = [marker.lower() for marker in self.REQUIREMENT_SECTION_MARKERS]
        if any(marker in content for marker in requirement_markers):
            has_strong_api_markers = any(
                marker in content for marker in [
                    'openapi', 'swagger', '接口路径', '请求方法', '请求参数',
                    '响应参数', '返回参数', 'curl ', ' /api/', 'endpoint'
                ]
            )
            if not has_strong_api_markers:
                return False

        api_score = 0
        api_markers = [
            '接口路径', '请求方法', '请求参数', '响应参数',
            '返回参数', 'openapi', 'swagger', 'endpoint'
        ]
        for marker in api_markers:
            if marker.lower() in content:
                api_score += 1

        for line in self.cleaned_lines:
            normalized = line.lower().replace(' ', '')
            if '|' in normalized and any(key in normalized for key in ['method', 'url', 'endpoint', 'path']):
                api_score += 2
            if re.search(r'\b(get|post|put|delete|patch|options|head)\b', normalized):
                api_score += 1
            if re.search(r'(^|[^a-z])/api/|(^|[^a-z])/v[0-9]+/', normalized):
                api_score += 1

        return api_score >= 2

    def _parse_api_doc(self) -> List[Dict]:
        """解析 API 文档格式"""
        apis = []
        current_api = {}

        i = 0
        while i < len(self.cleaned_lines):
            line = self.cleaned_lines[i].strip()

            # 检测接口标题
            if line.startswith('## ') or line.startswith('### '):
                if current_api and current_api.get('method'):
                    apis.append(current_api)
                current_api = {'description': '', 'parameters': [], 'responses': []}

                # 提取接口名称
                title = line.replace('##', '').replace('###', '').strip()

                # 尝试提取方法
                method_match = re.search(r'(GET|POST|PUT|DELETE|PATCH|OPTIONS|HEAD)\s*[-–]\s*(.+)', title, re.I)
                if method_match:
                    current_api['method'] = method_match.group(1).upper()
                    current_api['name'] = method_match.group(2).strip()
                else:
                    current_api['name'] = title
                    current_api['method'] = 'GET'

            # 解析接口路径
            path_match = re.search(r'[接口路径|Endpoint|URL]*[:：]?\s*(/[^\s]*)', line, re.I)
            if path_match:
                current_api['url'] = path_match.group(1)
                current_api['path'] = path_match.group(1)

            # 解析参数表格
            if '参数名' in line or '参数' in line and '|' in line:
                param_table, i = self._parse_param_table(i)
                if param_table:
                    current_api['parameters'] = param_table

            # 解析响应表格
            if '响应' in line and '|' in line:
                response_table, i = self._parse_param_table(i)
                if response_table:
                    current_api['responses'] = response_table

            i += 1

        # 添加最后一个接口
        if current_api and current_api.get('method'):
            apis.append(current_api)

        return apis

    def _parse_requirement_doc(self) -> List[Dict[str, Any]]:
        """解析需求文档，输出功能测试生成器可消费的 feature 列表。"""
        scoped_lines = self._extract_requirement_scope()
        features = self._parse_requirement_features(scoped_lines)
        if features:
            return features

        fallback_feature = {
            'name': self._extract_title(),
            'description': self._build_description(self.cleaned_lines),
            'fields': self._extract_fields(self.cleaned_lines),
            'rules': self._extract_business_rules(self.cleaned_lines)
        }
        return [fallback_feature]

    def _extract_requirement_scope(self) -> List[str]:
        """优先截取功能需求描述章节，避免把前置说明章节误识别为功能点。"""
        start_idx = 0
        for idx, line in enumerate(self.cleaned_lines):
            if '功能需求描述' in line:
                start_idx = idx + 1
                break
        return self.cleaned_lines[start_idx:]

    def _parse_requirement_features(self, lines: List[str]) -> List[Dict[str, Any]]:
        """按功能章节解析需求文档。"""
        features = []
        current_feature = None
        current_lines: List[str] = []

        for line in lines:
            heading = self._parse_heading(line)
            if heading:
                level, title = heading
                if self._is_major_requirement_heading(level, title):
                    if current_feature:
                        self._finalize_feature(current_feature, current_lines, features)
                    current_feature = {
                        'name': self._normalize_feature_name(title),
                        'description': '',
                        'fields': [],
                        'rules': []
                    }
                    current_lines = []
                    continue

                if current_feature is not None:
                    current_lines.append(self._clean_heading_title(title))
                continue

            if current_feature is not None and line:
                current_lines.append(line)

        if current_feature:
            self._finalize_feature(current_feature, current_lines, features)

        deduped = []
        seen = set()
        for feature in features:
            name = feature.get('name', '').strip()
            if not name or name in seen:
                continue
            seen.add(name)
            deduped.append(feature)
        return deduped

    def _parse_param_table(self, start_idx: int) -> (List[Dict], int):
        """解析参数表格"""
        params = []
        headers = []

        i = start_idx

        # 找到表头
        while i < len(self.cleaned_lines):
            line = self.cleaned_lines[i].strip()
            if '|' in line:
                headers = [h.strip() for h in line.split('|')]
                i += 1
                break
            i += 1

        # 解析数据行
        while i < len(self.cleaned_lines):
            line = self.cleaned_lines[i].strip()
            if not line or '|' not in line:
                break

            cells = [c.strip() for c in line.split('|')]
            param = {}
            for idx, header in enumerate(headers):
                if idx < len(cells):
                    param[header] = cells[idx]

            if param:
                params.append(param)
            i += 1

        return params, i

    def _parse_heading(self, line: str) -> Tuple[int, str]:
        """解析 Markdown 标题。"""
        match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if not match:
            return ()
        return len(match.group(1)), match.group(2).strip()

    def _is_major_requirement_heading(self, level: int, title: str) -> bool:
        """判断是否为需求文档中的主要功能标题。"""
        if level != 2:
            return False

        normalized = self._normalize_feature_name(title)
        if normalized in self.IGNORED_REQUIREMENT_HEADINGS:
            return False

        return bool(re.match(r'^\d+\.\d+', title.strip()))

    def _is_requirement_feature_heading(self, level: int, title: str) -> bool:
        """判断标题是否可以作为功能点。"""
        if level < 2 or level > 4:
            return False

        normalized = self._clean_heading_title(title)
        return normalized not in self.IGNORED_REQUIREMENT_HEADINGS

    def _clean_heading_title(self, title: str) -> str:
        """清洗标题中的编号前缀。"""
        title = title.replace('#', ' ').strip()
        title = re.sub(r'^\d+(?:\.\d+)+\s*', '', title)
        title = re.sub(r'^[0-9]+[.)、]\s*', '', title)
        title = re.sub(r'^[一二三四五六七八九十]+[、.]\s*', '', title)
        title = re.sub(r'^[（(][一二三四五六七八九十0-9]+[）)]\s*', '', title)
        return title.strip()

    def _normalize_feature_name(self, title: str) -> str:
        """清洗功能名中的编号、星号和尾部标点。"""
        title = self._clean_heading_title(title)
        title = re.sub(r'^\d+(?:\.\d+)*\s*', '', title)
        title = title.replace('：', '').replace(':', '')
        title = re.sub(r'[、,，xX·]+$', '', title)
        return title.strip()

    def _finalize_feature(self, feature: Dict[str, Any], lines: List[str], features: List[Dict[str, Any]]):
        """补全 feature 描述和字段并写入结果集。"""
        scenario_features = self._extract_page_scenarios(feature, lines)
        if scenario_features:
            features.extend(scenario_features)
            return

        feature['description'] = self._build_description(lines)
        feature['fields'] = self._extract_fields(lines)
        feature['rules'] = self._extract_business_rules(lines)
        if feature['name']:
            features.append(feature)

    def _extract_page_scenarios(self, feature: Dict[str, Any], lines: List[str]) -> List[Dict[str, Any]]:
        """从“页面名称/说明”表格中提取业务场景。"""
        scenarios = []
        i = 0

        while i < len(lines) - 1:
            header_line = lines[i].strip()
            separator_line = lines[i + 1].strip()

            if '|' not in header_line or '|' not in separator_line:
                i += 1
                continue

            if not re.match(r'^\|?[\s:\-|\u2013]+\|?$', separator_line):
                i += 1
                continue

            headers = [cell.strip() for cell in self._split_table_row(header_line)]
            if not any('页面名称' in header for header in headers) or not any('说明' in header for header in headers):
                i += 1
                continue

            i += 2
            while i < len(lines):
                row_line = lines[i].strip()
                if '|' not in row_line:
                    break

                row = self._split_table_row(row_line)
                row_data = {headers[idx]: row[idx].strip() for idx in range(min(len(headers), len(row)))}
                page_name = self._normalize_feature_name(row_data.get('页面名称', ''))
                description = row_data.get('说明', '').strip()
                if page_name and description:
                    scenarios.append({
                        'name': f"{feature['name']} - {page_name}",
                        'description': description,
                        'fields': self._extract_fields([description]),
                        'rules': self._extract_business_rules([description])
                    })
                i += 1

        return scenarios

    def _extract_business_rules(self, lines: List[str]) -> List[Dict[str, Any]]:
        """从需求描述中拆分并结构化业务规则条目。"""
        rule_texts = []
        paragraph_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('|') or re.match(r'^\s*[-:|]+\s*$', stripped):
                continue
            if '页面名称' in stripped and '说明' in stripped:
                continue

            bullet_match = re.match(r'^\s*[-*+]\s*(.+)$', stripped)
            if bullet_match:
                rule_texts.extend(self._explode_rule_fragments(bullet_match.group(1).strip()))
                continue

            paragraph_lines.append(stripped)

        if paragraph_lines:
            combined_text = ' '.join(paragraph_lines)
            for clause in self._split_numbered_clauses(combined_text):
                rule_texts.extend(self._explode_rule_fragments(clause))

        structured_rules = []
        seen = set()
        for rule_text in rule_texts:
            normalized = re.sub(r'\s+', ' ', rule_text).strip(' -;；。.，,')
            if len(normalized) < 4 or normalized in seen:
                continue
            seen.add(normalized)
            structured_rules.append(self._classify_business_rule(normalized))

        return structured_rules

    def _split_numbered_clauses(self, text: str) -> List[str]:
        """切分“1、2、3”式需求条目，尽量避开示例数据中的编号串。"""
        marker_pattern = re.compile(r'(?:(?<=^)|(?<=[。；！？;.!?\"”]))\s*(\d+[、.])(?!\d)')
        matches = list(marker_pattern.finditer(text))
        if not matches:
            return [text.strip()]

        clauses = []
        for index, match in enumerate(matches):
            start = match.start()
            end = matches[index + 1].start() if index + 1 < len(matches) else len(text)
            clause = text[start:end].strip()
            clause = re.sub(r'^\d+[、.]\s*', '', clause)
            if clause:
                clauses.append(clause)

        return clauses

    def _explode_rule_fragments(self, text: str) -> List[str]:
        """进一步拆分复合规则，尽量将一段话拆成更原子的业务条目。"""
        starter_pattern = (
            r'(?:支持|点击|当|异常情况|最多|优化|新增|隐藏|无需|默认|列表|文件名称|文件类型|'
            r'选择|多选|翻页|移除|返回|批量|弹窗|任务|导入|下载|商品搜索|高级搜索|'
            r'陈列图状态|使用上下滚动条显示|鼠标移入)'
        )
        working_text = text.strip()
        if not working_text:
            return []

        # 将行内 bullet 和新的编号条目拆开，但避免误切示例数据中的 1、2、3。
        working_text = re.sub(rf'\s*-\s*(?={starter_pattern})', '\n', working_text)
        working_text = re.sub(rf'(?<![0-9])(?P<marker>\d+[、.])(?={starter_pattern})', '\n\\g<marker>', working_text)
        working_text = re.sub(rf'(?<=[。；;!?\"”])\s*(?={starter_pattern})', '\n', working_text)

        fragments = []
        for part in working_text.splitlines():
            cleaned = part.strip(' -;；')
            cleaned = re.sub(r'^\d+[、.]\s*', '', cleaned)
            cleaned = cleaned.strip(' -;；')
            if cleaned:
                fragments.append(cleaned)

        return fragments or [text.strip()]

    def _classify_business_rule(self, rule_text: str) -> Dict[str, Any]:
        """将自然语言规则归类为可复用的规则类型。"""
        normalized = self._normalize_rule_text(rule_text)
        categories = []

        if '搜索' in normalized:
            categories.append('search')
        if '换行' in normalized and '搜索' in normalized:
            categories.append('search_multiline')
        if '最多' in normalized and '条' in normalized:
            categories.append('limit')
        if '未找到' in normalized:
            categories.append('feedback_not_found')
        if '多选' in normalized or '复选框选中' in normalized:
            categories.append('multi_select')
        if '翻页' in normalized and any(keyword in normalized for keyword in ['不会取消', '保留', '留存']):
            categories.append('selection_persistence')
        if '下方显示' in normalized and any(keyword in normalized for keyword in ['已选择', '已选', '名称']):
            categories.append('selection_summary')
        if '高级搜索' in normalized and any(keyword in normalized for keyword in ['显示/隐藏', '默认隐藏', '默认显示']):
            categories.append('toggle')
        if (('支持按' in normalized or '支持商品' in normalized or '支持陈列图' in normalized) and
                '搜索' in normalized):
            categories.append('search_filters')
        if '移除' in normalized and any(keyword in normalized for keyword in ['重新选', '添加', '不会']):
            categories.append('remove_restore')
        if '弹窗' in normalized and any(keyword in normalized for keyword in ['显示', '展示', '编辑']):
            categories.append('dialog_display')
        if '批量填写' in normalized or '批量修改' in normalized:
            categories.append('batch_edit')
        if ('返回上一步' in normalized or '上一步' in normalized) and any(
                keyword in normalized for keyword in ['留存', '保留', '当前数据']):
            categories.append('state_retention')
        if '增量更新' in normalized and '未来版本' in normalized:
            categories.append('data_sync')
        if '导入导出管理' in normalized or '下载导入文件' in normalized:
            categories.append('audit_record')
        if '任务成功' in normalized or '提醒任务成功' in normalized:
            categories.append('feedback_success')
        if any(keyword in normalized for keyword in ['任务失败', '操作失败', '查看详情', '部分数据失败']):
            categories.append('feedback_failure')
        if any(keyword in normalized for keyword in ['请先选择', '未选择']):
            categories.append('action_precondition')
        if any(keyword in normalized for keyword in ['分页', '单页显示', '每页显示']):
            categories.append('pagination')
        if '隐藏' in normalized and '显示/隐藏' not in normalized and any(
                keyword in normalized for keyword in ['按钮', '菜单', '页面', 'icon']):
            categories.append('visibility_control')

        return {
            'text': rule_text,
            'normalized_text': normalized,
            'categories': categories,
            'negative': self._is_negative_rule(normalized, categories),
            'limit': self._extract_rule_limit(rule_text),
            'messages': self._extract_rule_messages(rule_text),
            'default_state': self._extract_rule_default_state(normalized)
        }

    def _normalize_rule_text(self, text: str) -> str:
        """归一化规则文本，便于做宽松匹配。"""
        return re.sub(r'\s+', '', text or '')

    def _is_negative_rule(self, normalized_text: str, categories: List[str]) -> bool:
        """判断规则是否表达了限制、禁止或失败语义。"""
        negative_markers = ['不支持', '无需支持', '无需要支持', '不会', '失败']
        if any(marker in normalized_text for marker in negative_markers):
            return True
        if 'visibility_control' in categories and '隐藏' in normalized_text and '显示/隐藏' not in normalized_text:
            return True
        return False

    def _extract_rule_limit(self, text: str) -> int:
        """提取规则中的数值限制。"""
        patterns = [
            r'最多支持单次(\d+)条',
            r'最多支持(\d+)条',
            r'单次(\d+)条',
            r'默认单页显示(\d+)条',
            r'每页显示(\d+)条'
        ]
        for pattern in patterns:
            match = re.search(pattern, text)
            if match:
                return int(match.group(1))
        return 0

    def _extract_rule_messages(self, text: str) -> List[str]:
        """提取规则中的显式提示文案。"""
        messages = []
        messages.extend(re.findall(r'[“"]([^”"]+)[”"]', text))

        reminder_match = re.search(r'提醒[:：]\s*([^。；]+)', text)
        if reminder_match:
            messages.append(reminder_match.group(1).strip())

        deduped = []
        seen = set()
        for message in messages:
            normalized = message.strip()
            if not normalized or normalized in seen:
                continue
            seen.add(normalized)
            deduped.append(normalized)
        return deduped

    def _extract_rule_default_state(self, normalized_text: str) -> str:
        """提取控件默认状态。"""
        if '默认隐藏' in normalized_text:
            return 'hidden'
        if '默认显示' in normalized_text:
            return 'visible'
        return ''

    def _build_description(self, lines: List[str]) -> str:
        """提取需求摘要描述。"""
        description_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('|') or re.match(r'^\s*[-:|]+\s*$', stripped):
                continue
            if re.match(r'^\s*[-*+]\s+', stripped) and self._looks_like_field_definition(stripped):
                continue
            if '页面名称' in stripped and '说明' in stripped:
                continue
            description_lines.append(stripped)
            if len(description_lines) >= 5:
                break

        return ' '.join(description_lines)

    def _extract_fields(self, lines: List[str]) -> List[Dict[str, Any]]:
        """从需求文档中提取字段定义。"""
        fields = []
        fields.extend(self._extract_fields_from_tables(lines))
        fields.extend(self._extract_fields_from_bullets(lines))

        deduped = []
        seen = set()
        for field in fields:
            name = field.get('name', '').strip()
            if not name or name in seen:
                continue
            seen.add(name)
            deduped.append(field)
        return deduped

    def _extract_fields_from_tables(self, lines: List[str]) -> List[Dict[str, Any]]:
        """从 Markdown 表格中提取字段。"""
        fields = []
        i = 0

        while i < len(lines) - 1:
            header_line = lines[i].strip()
            separator_line = lines[i + 1].strip()

            if '|' not in header_line or '|' not in separator_line:
                i += 1
                continue

            if not re.match(r'^\|?[\s:\-|\u2013]+\|?$', separator_line):
                i += 1
                continue

            headers = [cell.strip().lower() for cell in self._split_table_row(header_line)]
            if not self._looks_like_field_table(headers):
                i += 1
                continue

            i += 2
            while i < len(lines):
                row_line = lines[i].strip()
                if '|' not in row_line:
                    break

                row = self._split_table_row(row_line)
                row_data = {headers[idx]: row[idx].strip() for idx in range(min(len(headers), len(row)))}
                field = self._build_field_from_row(row_data)
                if field:
                    fields.append(field)
                i += 1

        return fields

    def _extract_fields_from_bullets(self, lines: List[str]) -> List[Dict[str, Any]]:
        """从列表项中提取字段。"""
        fields = []
        bullet_pattern = re.compile(r'^\s*(?:[-*+]|\d+[.)])\s*(.+)$')

        for line in lines:
            match = bullet_pattern.match(line.strip())
            if not match:
                continue

            content = match.group(1).strip()
            if not self._looks_like_field_definition(content):
                continue

            name, detail = self._split_field_definition(content)
            fields.append({
                'name': name,
                'required': self._parse_required_flag(detail),
                'type': self._extract_field_type(detail),
                'description': detail
            })

        return fields

    def _split_table_row(self, row: str) -> List[str]:
        """切分表格行。"""
        row = row.strip().strip('|')
        return [cell.strip() for cell in row.split('|')]

    def _looks_like_field_table(self, headers: List[str]) -> bool:
        """判断表格是否为字段定义表。"""
        header_text = ' '.join(headers)
        return any(key in header_text for key in ['字段', '参数', '必填', 'required', 'type', '说明', '描述', 'name'])

    def _build_field_from_row(self, row_data: Dict[str, str]) -> Dict[str, Any]:
        """从表格行构造字段定义。"""
        name = (
            row_data.get('字段') or row_data.get('字段名') or row_data.get('参数') or
            row_data.get('参数名') or row_data.get('名称') or row_data.get('name', '')
        ).strip()
        if not name:
            return {}

        detail = row_data.get('说明') or row_data.get('描述') or row_data.get('备注') or ''
        required_value = row_data.get('必填') or row_data.get('是否必填') or row_data.get('required', '')
        field_type = row_data.get('类型') or row_data.get('数据类型') or row_data.get('type', 'string')

        return {
            'name': name,
            'required': self._parse_required_flag(required_value),
            'type': field_type.strip() or 'string',
            'description': detail.strip()
        }

    def _looks_like_field_definition(self, content: str) -> bool:
        """判断一行文本是否像字段说明。"""
        keywords = ['必填', '选填', '可选', 'required', '字段', '参数', '类型']
        return '：' in content or ':' in content or any(keyword in content.lower() for keyword in keywords)

    def _split_field_definition(self, content: str) -> Tuple[str, str]:
        """拆分字段名和字段描述。"""
        if '：' in content:
            name, detail = content.split('：', 1)
        elif ':' in content:
            name, detail = content.split(':', 1)
        else:
            parts = content.split(' ', 1)
            name = parts[0]
            detail = parts[1] if len(parts) > 1 else ''
        return name.strip(), detail.strip()

    def _parse_required_flag(self, value: str) -> bool:
        """解析必填标记。"""
        normalized = str(value).strip().lower()
        return normalized in {'是', 'y', 'yes', 'true', 'required', '必填'}

    def _extract_field_type(self, detail: str) -> str:
        """从描述中提取字段类型。"""
        detail_lower = detail.lower()
        if 'int' in detail_lower or 'integer' in detail_lower or '数字' in detail_lower:
            return 'int'
        if 'bool' in detail_lower or '布尔' in detail_lower:
            return 'bool'
        if 'array' in detail_lower or 'list' in detail_lower or '数组' in detail_lower:
            return 'array'
        if 'object' in detail_lower or '对象' in detail_lower:
            return 'object'
        if 'float' in detail_lower or 'double' in detail_lower or '小数' in detail_lower:
            return 'float'
        return 'string'

    def get_info(self) -> Dict:
        """获取文档信息"""
        return {
            'title': self._extract_title(),
            'api_count': len(self.parse()),
            'format': self.detect_doc_type()
        }

    def _extract_title(self) -> str:
        """提取标题"""
        for line in self.cleaned_lines[:10]:
            if line.startswith('# '):
                return line.replace('#', '').strip()
        return 'Unknown'


# 便捷函数
def parse_markdown(content: str) -> List[Dict]:
    """解析 Markdown API 文档"""
    return MarkdownParser(content).parse()
