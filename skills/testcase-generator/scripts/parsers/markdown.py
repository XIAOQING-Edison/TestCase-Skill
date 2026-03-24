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
        '验收标准', '非功能需求', '业务规则', '流程说明', '术语说明'
    }

    def __init__(self, source: str):
        self.source = source
        self.raw_content = self._load_content(source)
        self.lines = self.raw_content.splitlines()

    def _load_content(self, source: str) -> str:
        """加载 Markdown 内容，支持文件路径或直接传入内容。"""
        if os.path.exists(source):
            with open(source, 'r', encoding='utf-8') as f:
                return f.read()
        return source

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
        content = self.raw_content.lower()
        # 检查常见的 API 文档标记
        api_markers = ['接口路径', '请求参数', '响应参数', '接口描述',
                       'method', 'endpoint', 'request body', 'response']
        if any(marker.lower() in content for marker in api_markers):
            return True

        for line in self.lines:
            normalized = line.lower().replace(' ', '')
            if '|' in normalized and ('method' in normalized or 'url' in normalized or 'endpoint' in normalized):
                return True

        return False

    def _parse_api_doc(self) -> List[Dict]:
        """解析 API 文档格式"""
        apis = []
        current_api = {}

        i = 0
        while i < len(self.lines):
            line = self.lines[i].strip()

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
        features = []
        current_feature = None
        current_lines: List[str] = []

        for raw_line in self.lines:
            line = raw_line.rstrip()
            heading = self._parse_heading(line.strip())

            if heading:
                if current_feature:
                    self._finalize_feature(current_feature, current_lines, features)
                    current_feature = None
                    current_lines = []

                level, title = heading
                if self._is_requirement_feature_heading(level, title):
                    current_feature = {
                        'name': self._clean_heading_title(title),
                        'description': '',
                        'fields': []
                    }
                continue

            if current_feature is not None:
                current_lines.append(line)

        if current_feature:
            self._finalize_feature(current_feature, current_lines, features)

        if features:
            return features

        # 没有明确功能标题时，退化成单功能需求
        fallback_feature = {
            'name': self._extract_title(),
            'description': self._build_description(self.lines),
            'fields': self._extract_fields(self.lines)
        }
        return [fallback_feature]

    def _parse_param_table(self, start_idx: int) -> (List[Dict], int):
        """解析参数表格"""
        params = []
        headers = []

        i = start_idx

        # 找到表头
        while i < len(self.lines):
            line = self.lines[i].strip()
            if '|' in line:
                headers = [h.strip() for h in line.split('|')]
                i += 1
                break
            i += 1

        # 解析数据行
        while i < len(self.lines):
            line = self.lines[i].strip()
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

    def _is_requirement_feature_heading(self, level: int, title: str) -> bool:
        """判断标题是否可以作为功能点。"""
        if level < 2 or level > 4:
            return False

        normalized = self._clean_heading_title(title)
        return normalized not in self.IGNORED_REQUIREMENT_HEADINGS

    def _clean_heading_title(self, title: str) -> str:
        """清洗标题中的编号前缀。"""
        title = re.sub(r'^[0-9]+[.)、]\s*', '', title)
        title = re.sub(r'^[一二三四五六七八九十]+[、.]\s*', '', title)
        title = re.sub(r'^[（(][一二三四五六七八九十0-9]+[）)]\s*', '', title)
        return title.strip()

    def _finalize_feature(self, feature: Dict[str, Any], lines: List[str], features: List[Dict[str, Any]]):
        """补全 feature 描述和字段并写入结果集。"""
        feature['description'] = self._build_description(lines)
        feature['fields'] = self._extract_fields(lines)

        if feature['name']:
            features.append(feature)

    def _build_description(self, lines: List[str]) -> str:
        """提取需求摘要描述。"""
        description_lines = []

        for line in lines:
            stripped = line.strip()
            if not stripped or stripped.startswith('|') or re.match(r'^\s*[-:|]+\s*$', stripped):
                continue
            if re.match(r'^\s*[-*+]\s+', stripped) and self._looks_like_field_definition(stripped):
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
        for line in self.lines[:10]:
            if line.startswith('# '):
                return line.replace('#', '').strip()
        return 'Unknown'


# 便捷函数
def parse_markdown(content: str) -> List[Dict]:
    """解析 Markdown API 文档"""
    return MarkdownParser(content).parse()
