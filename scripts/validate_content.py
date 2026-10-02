#!/usr/bin/env python3
"""静态核查教程 YAML；不会读取 kubeconfig 或连接集群。需 PyYAML。
可选 --schema PATH 使用 Kubernetes 官方 OpenAPI v2 文件检查内置资源字段。
这不是 apiserver 准入校验，不能验证插件、镜像、权限、存储及运行时行为。
"""
import argparse
import html
import json
import re
from pathlib import Path
import yaml

class UniqueLoader(yaml.SafeLoader):
    pass

def unique_mapping(loader, node, deep=False):
    result = {}
    for key_node, value_node in node.value:
        key = loader.construct_object(key_node, deep=deep)
        if key in result:
            raise yaml.constructor.ConstructorError('mapping', node.start_mark,
                                                    f'duplicate key: {key}', key_node.start_mark)
        result[key] = loader.construct_object(value_node, deep=deep)
    return result

UniqueLoader.add_constructor(yaml.resolver.BaseResolver.DEFAULT_MAPPING_TAG, unique_mapping)

def validate(value, schema, definitions, path):
    if '$ref' in schema:
        name = schema['$ref'].split('/')[-1]
        # Quantity 的 JSON 解码器也接受数字（如 GPU: 1），OpenAPI 仅标为 string。
        if name == 'io.k8s.apimachinery.pkg.api.resource.Quantity' and type(value) in (int, float):
            return []
        return validate(value, definitions[name], definitions, path)
    if value is None:
        return [f'{path}: null']
    if schema.get('x-kubernetes-int-or-string') or schema.get('format') == 'int-or-string':
        return [] if type(value) in (int, str) else [f'{path}: expected int/string']
    typ = schema.get('type')
    kinds = {'object': dict, 'array': list, 'string': str, 'integer': int, 'boolean': bool}
    if typ in kinds and type(value) is not kinds[typ]:
        return [f'{path}: expected {typ}, got {type(value).__name__}']
    errors = []
    if typ == 'object':
        for required in schema.get('required', []):
            if required not in value:
                errors.append(f'{path}.{required}: required')
        props = schema.get('properties', {})
        additional = schema.get('additionalProperties')
        for key, item in value.items():
            if key in props:
                errors.extend(validate(item, props[key], definitions, f'{path}.{key}'))
            elif isinstance(additional, dict):
                errors.extend(validate(item, additional, definitions, f'{path}.{key}'))
            elif additional is not True and not schema.get('x-kubernetes-preserve-unknown-fields'):
                errors.append(f'{path}.{key}: unknown field')
    if typ == 'array':
        for i, item in enumerate(value):
            errors.extend(validate(item, schema.get('items', {}), definitions, f'{path}[{i}]'))
    return errors

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--schema', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[1]
    definitions = json.loads(args.schema.read_text())['definitions'] if args.schema else {}
    resources = {}
    for definition in definitions.values():
        for gvk in definition.get('x-kubernetes-group-version-kind', []):
            api = (gvk['group'] + '/' if gvk['group'] else '') + gvk['version']
            resources[(api, gvk['kind'])] = definition
    source = (root / 'index.html').read_text()
    failures = []; counts = {'yaml_blocks': 0, 'documents': 0, 'builtin_checked': 0,
                            'custom_or_component_config': 0, 'objects_without_schema': 0, 'fragments': 0, 'helm_templates': 0}
    samples = []
    for m in re.finditer(r'<pre\b[^>]*>[\s\S]*?</pre>', source):
        raw = m.group()
        if not re.search(r'lang-yaml|class="lang">yaml', raw):
            continue
        cm = re.search(r'<code\b[^>]*>([\s\S]*?)</code>', raw)
        text = html.unescape(re.sub('<[^>]*>', '', cm[1]))
        label = f'index.html:{source[:m.start()].count(chr(10)) + 1}'
        counts['yaml_blocks'] += 1
        if re.search(r':\s*{{', text):
            counts['helm_templates'] += 1
            continue
        samples.append((label, text))
    for file in sorted((root / 'examples').rglob('*.yaml')):
        samples.append((str(file.relative_to(root)), file.read_text()))
    for label, text in samples:
        try:
            docs = list(yaml.load_all(text, Loader=UniqueLoader))
        except (yaml.YAMLError, TypeError) as error:
            failures.append(f'{label}: {error}')
            continue
        for i, doc in enumerate(docs, 1):
            if doc is None:
                continue
            counts['documents'] += 1
            if not isinstance(doc, dict) or not {'apiVersion', 'kind'} <= doc.keys():
                counts['fragments'] += 1
                continue
            gvk = (doc['apiVersion'], doc['kind'])
            if gvk in resources:
                counts['builtin_checked'] += 1
                failures.extend(f'{label} doc {i}: {err}' for err in
                                validate(doc, resources[gvk], definitions, doc['kind']))
            elif definitions:
                counts['custom_or_component_config'] += 1
            else:
                counts['objects_without_schema'] += 1
    print(json.dumps(counts, ensure_ascii=False))
    for error in failures:
        print(error)
    if failures:
        raise SystemExit(1)
    print('PASS: YAML 静态核查通过；运行时与准入条件需另外验证。')

if __name__ == '__main__':
    main()
