#!/usr/bin/env python3
"""
测试用例生成器主程序
统一入口，支持多种文档格式和输出格式
"""

import argparse
import json
import sys
import os
from pathlib import Path
from typing import Dict, List, Any

# 添加当前目录到路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from parsers import PostmanParser, SwaggerParser, JsonSchemaParser, MarkdownParser, HarParser
from generators import FunctionalTestGenerator, APITestGenerator
from formatters import MarkdownFormatter, ExcelFormatter, PytestFormatter, PostmanFormatter, JMeterFormatter
from utils import validate_testcase, parse_priority


class TestCaseGenerator:
    """测试用例生成器主类"""

    API_ONLY_OUTPUT_FORMATS = {'pytest', 'postman', 'jmeter'}

    SUPPORTED_INPUT_FORMATS = {
        'postman': ['.json'],
        'swagger': ['.json', '.yaml', '.yml'],
        'openapi': ['.json', '.yaml', '.yml'],
        'markdown': ['.md', '.txt'],
        'json': ['.json'],
        'har': ['.har'],
        'json_schema': ['.json']
    }

    SUPPORTED_OUTPUT_FORMATS = {
        'markdown': 'md',
        'excel': 'xlsx',
        'pytest': 'py',
        'postman': 'json',
        'jmeter': 'jmx',
        'json': 'json'
    }

    def __init__(self):
        self.testcases = []

    def detect_format(self, filepath: str) -> str:
        """检测文件格式"""
        ext = Path(filepath).suffix.lower()

        if ext in ['.json']:
            # 尝试读取并检测类型
            with open(filepath, 'r', encoding='utf-8') as f:
                content = json.load(f)

            if 'info' in content and 'item' in content:
                return 'postman'
            if 'openapi' in content or 'swagger' in content:
                return 'openapi'
            if 'paths' in content:
                return 'json'
            if 'log' in content and 'entries' in content:
                return 'har'

        if ext in ['.yaml', '.yml']:
            return 'openapi'

        if ext in ['.md', '.txt']:
            return 'markdown'

        return 'unknown'

    def parse_document(self, filepath: str) -> List[Dict]:
        """解析文档"""
        format_type = self.detect_format(filepath)

        parsers = {
            'postman': PostmanParser,
            'openapi': SwaggerParser,
            'swagger': SwaggerParser,
            'json': JsonSchemaParser,
            'json_schema': JsonSchemaParser,
            'markdown': MarkdownParser,
            'har': HarParser
        }

        parser_class = parsers.get(format_type)
        if not parser_class:
            raise ValueError(f"不支持的文件格式: {format_type}")

        parser = parser_class(filepath)
        return parser.parse()

    def _is_api_document(self, items: List[Dict]) -> bool:
        """根据解析结果判断当前文档类型。"""
        if not items:
            return True

        sample = items[0]
        return any(key in sample for key in ['method', 'url', 'path', 'request_body', 'responses'])

    def generate_testcases(self, items: List[Dict], module_name: str, base_url: str = "") -> List[Dict]:
        """生成测试用例"""
        all_cases = []

        if self._is_api_document(items):
            generator = APITestGenerator(base_url, module_name)
            for api in items:
                cases = generator.generate(api)
                all_cases.extend(cases)
        else:
            generator = FunctionalTestGenerator(module_name)
            for feature in items:
                cases = generator.generate(feature)
                all_cases.extend(cases)

        return all_cases

    def format_output(self, testcases: List[Dict], module_name: str, base_url: str,
                      output_format: str, output_dir: str = ".") -> List[str]:
        """
        格式化并输出测试用例

        Args:
            testcases: 测试用例列表
            module_name: 模块名称
            base_url: 基础 URL
            output_format: 输出格式
            output_dir: 输出目录

        Returns:
            生成的文件列表
        """
        output_files = []
        timestamp = __import__('datetime').datetime.now().strftime("%Y%m%d_%H%M%S")
        os.makedirs(output_dir, exist_ok=True)

        # 过滤有效用例
        valid_cases = []
        for tc in testcases:
            is_valid, _ = validate_testcase(tc)
            if is_valid:
                valid_cases.append(tc)

        if output_format == 'all':
            formats = list(self.SUPPORTED_OUTPUT_FORMATS.keys())
        else:
            formats = [output_format]

        has_api_cases = any(tc.get('用例编号', '').startswith('API_') for tc in valid_cases)
        if not has_api_cases:
            if output_format == 'all':
                formats = [fmt for fmt in formats if fmt not in self.API_ONLY_OUTPUT_FORMATS]

            unsupported_formats = [fmt for fmt in formats if fmt in self.API_ONLY_OUTPUT_FORMATS]
            if unsupported_formats:
                raise ValueError(
                    f"功能测试用例暂不支持以下输出格式: {', '.join(unsupported_formats)}；"
                    "请使用 markdown、excel 或 json。"
                )

        for fmt in formats:
            ext = self.SUPPORTED_OUTPUT_FORMATS[fmt]
            filename = f"{output_dir}/{module_name}_testcases_{fmt}_{timestamp}.{ext}"

            if fmt == 'markdown':
                content = MarkdownFormatter(module_name, base_url).format(valid_cases)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(content)
                output_files.append(filename)

            elif fmt == 'excel':
                filepath = ExcelFormatter(module_name).format(valid_cases, filename)
                output_files.append(filepath)

            elif fmt == 'pytest':
                code = PytestFormatter(module_name, base_url).format(valid_cases)
                with open(filename.replace('.json', '.py'), 'w', encoding='utf-8') as f:
                    f.write(code)
                output_files.append(filename.replace('.json', '.py'))

            elif fmt == 'postman':
                collection = PostmanFormatter(module_name, base_url).format(valid_cases)
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(collection, f, ensure_ascii=False, indent=2)
                output_files.append(filename)

            elif fmt == 'jmeter':
                xml = JMeterFormatter(module_name, base_url).format(valid_cases)
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(xml)
                output_files.append(filename)

            elif fmt == 'json':
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(valid_cases, f, ensure_ascii=False, indent=2)
                output_files.append(filename)

        return output_files

    def print_summary(self, testcases: List[Dict]):
        """打印用例统计"""
        print("\n" + "="*60)
        print("测试用例生成完成!")
        print("="*60)

        # 统计
        api_count = len([tc for tc in testcases if tc.get('用例编号', '').startswith('API_')])
        func_count = len([tc for tc in testcases if tc.get('功能ID', '').startswith('FUNC_')])

        # 优先级统计
        priority_stats = {}
        for tc in testcases:
            priority = tc.get('模块/优先级', tc.get('优先级', '未知'))
            priority_stats[priority] = priority_stats.get(priority, 0) + 1

        print(f"\n用例总数: {len(testcases)}")
        print(f"  - 接口测试用例: {api_count}")
        print(f"  - 功能测试用例: {func_count}")

        print("\n优先级分布:")
        for priority, count in sorted(priority_stats.items()):
            print(f"  - {priority}: {count}个")

        # 类型统计
        type_stats = {}
        for tc in testcases:
            tc_type = tc.get('测试类型', '未知')
            type_stats[tc_type] = type_stats.get(tc_type, 0) + 1

        print("\n测试类型分布:")
        for tc_type, count in type_stats.items():
            print(f"  - {tc_type}: {count}个")


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="测试用例生成器 - 支持多种文档格式和输出格式",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从 Postman 集合生成测试用例
  python main.py -i api.json -o markdown -m UserAPI

  # 生成多种格式
  python main.py -i swagger.yaml -o all -m AuthAPI -b https://api.example.com

  # 生成 pytest 代码
  python main.py -i postman.json -o pytest -m PaymentAPI --base-url https://api.example.com
        """
    )

    parser.add_argument('-i', '--input', required=True, help='输入文件路径')
    parser.add_argument('-o', '--output', default='markdown', choices=['markdown', 'excel', 'pytest', 'postman', 'jmeter', 'json', 'all'],
                        help='输出格式 (默认: markdown)')
    parser.add_argument('-m', '--module', default='TestModule', help='模块名称')
    parser.add_argument('-b', '--base-url', default='', help='基础 URL')
    parser.add_argument('-d', '--output-dir', default='.', help='输出目录')
    parser.add_argument('-v', '--verbose', action='store_true', help='详细输出')

    args = parser.parse_args()

    generator = TestCaseGenerator()

    try:
        # 解析文档
        if args.verbose:
            print(f"解析文件: {args.input}")
        parsed_items = generator.parse_document(args.input)
        is_api_document = generator._is_api_document(parsed_items)

        if args.verbose:
            item_label = "接口" if is_api_document else "功能点"
            print(f"解析到 {len(parsed_items)} 个{item_label}")

        # 生成测试用例
        testcases = generator.generate_testcases(parsed_items, args.module, args.base_url)

        if args.verbose:
            print(f"生成 {len(testcases)} 个测试用例")

        # 输出
        files = generator.format_output(testcases, args.module, args.base_url, args.output, args.output_dir)

        if args.verbose:
            for f in files:
                print(f"生成文件: {f}")

        # 打印统计
        generator.print_summary(testcases)

        print(f"\n输出文件: {', '.join(files)}")

    except Exception as e:
        print(f"错误: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
