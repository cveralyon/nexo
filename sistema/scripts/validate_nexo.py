"""Offline structural validation for Nexo. No external resources are accessed.

Navigation starts at README.md and START_HERE.md. Templates and test trees are
excluded. Unindexed notes and future metadata dates request human review.
Markdown headings use GitHub style slugs; explicit HTML anchors are unsupported.
"""
from __future__ import annotations

import argparse
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path
import re
import unicodedata
from urllib.parse import unquote, urlsplit
from uuid import UUID

from markdown_it import MarkdownIt
import yaml

AREAS = set('perfil salud relaciones trabajo finanzas hogar tecnologia aprendizaje ocio-y-viajes ideas-y-futuro _bandeja'.split())
TYPES = set('tema proyecto persona decision idea aprendizaje experiencia registro'.split())
STATES = set('activo borrador en-curso por-confirmar cerrado archivado sustituido'.split())
EXCLUDED = {'.git', '.venv', '__pycache__', 'node_modules'}
FUNCTIONAL_EXCLUSIONS = {'plantillas', 'templates', 'fixtures', 'tests'}
CONFLICT = re.compile(r'^(?:<{7}(?: |$)|={7}$|>{7}(?: |$)|\|{7}(?: |$))')
PARSER = MarkdownIt('commonmark').enable('table')
# Parse all destinations as data, including file URLs, without fetching them.
PARSER.validateLink = lambda destination: True


class StrictLoader(yaml.SafeLoader):
    """Safe YAML with duplicate keys and aliases rejected to avoid ambiguity."""

    def compose_node(self, parent, index):
        if self.check_event(yaml.AliasEvent):
            raise yaml.YAMLError('YAML aliases are not supported')
        return super().compose_node(parent, index)

    def construct_mapping(self, node, deep=False):
        self.flatten_mapping(node)
        result = {}
        for key_node, value_node in node.value:
            key = self.construct_object(key_node, deep=deep)
            if not isinstance(key, str) or key in result:
                raise yaml.YAMLError('Metadata keys must be unique strings')
            result[key] = self.construct_object(value_node, deep=deep)
        return result


@dataclass
class ValidationResult:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


def valid_id(value):
    if not isinstance(value, str) or not value.startswith('n-'):
        return False
    try:
        parsed = UUID(value[2:])
        return parsed.version == 4 and str(parsed) == value[2:]
    except ValueError:
        return False


def valid_date(value):
    if type(value) is date:
        return value
    if isinstance(value, str) and re.fullmatch(r'\d{4}-\d{2}-\d{2}', value):
        try:
            return date.fromisoformat(value)
        except ValueError:
            pass
    return None


def heading_ids(tokens):
    seen = set()
    for index, token in enumerate(tokens):
        if token.type != 'heading_open':
            continue
        children = tokens[index + 1].children or []
        title = ''.join(child.content for child in children if child.type in {'text', 'code_inline', 'image'})
        base = ''.join(c for c in title.lower() if c in ' _-' or unicodedata.category(c)[0] in 'LN').replace(' ', '-')
        slug, suffix = base, 0
        while slug in seen:
            suffix += 1
            slug = f'{base}-{suffix}'
        seen.add(slug)
    return seen


def validate_repository(root: Path) -> ValidationResult:
    root = root.resolve()
    result = ValidationResult()
    documents, metadata, graph, ids = {}, {}, {}, {}
    def error(path, message):
        result.errors.append(f'{path.relative_to(root)}: {message}')
    def warning(path, message):
        result.warnings.append(f'{path.relative_to(root)}: {message}')
    def excluded(path):
        parts = path.relative_to(root).parts
        return bool(EXCLUDED.intersection(parts) or (len(parts) > 1 and parts[0] == 'sistema' and parts[1] in FUNCTIONAL_EXCLUSIONS))
    for entry in ('README.md', 'START_HERE.md'):
        if not (root / entry).is_file():
            error(root / entry, 'Required entry index is missing')
    paths = sorted(p for p in root.rglob('*.md') if not excluded(p))
    for path in sorted(p for p in root.rglob('*') if p.is_file() and p.suffix in {'.py', '.yml', '.yaml', '.txt'} and not excluded(p)):
        if path.is_symlink():
            error(path, 'Symbolic links are not supported')
            continue
        try:
            content = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError):
            error(path, 'Cannot read UTF-8 utility file')
            continue
        if any(CONFLICT.match(line) for line in content.splitlines()):
            error(path, 'Unresolved conflict marker in utility file')
    for path in paths:
        if path.is_symlink():
            error(path, 'Symbolic links are not supported')
            continue
        try:
            text = path.read_text(encoding='utf-8')
        except (OSError, UnicodeError) as exc:
            error(path, f'Cannot read UTF-8 document ({exc.__class__.__name__})')
            continue
        body, data = text, None
        lines = text.splitlines()
        if lines and lines[0].strip() == '---':
            end = next((i for i in range(1, len(lines)) if lines[i].strip() == '---'), None)
            if end is None:
                error(path, 'Unclosed front matter')
                continue
            body = '\n'.join(lines[end + 1:])
            try:
                data = yaml.load('\n'.join(lines[1:end]), Loader=StrictLoader)
            except (yaml.YAMLError, RecursionError, ValueError):
                error(path, 'Invalid or unsafe YAML metadata')
            if not isinstance(data, dict):
                error(path, 'Front matter must be a mapping')
                data = {}
        elif path.relative_to(root).parts[0] in AREAS and path.name != 'README.md':
            error(path, 'Content note requires front matter')
        if data is not None:
            metadata[path] = data
            for key in ('id', 'tipo', 'estado', 'actualizado', 'resumen'):
                if key not in data:
                    error(path, f'Missing metadata {key}')
            ident = data.get('id')
            if not valid_id(ident):
                error(path, 'id must be canonical n-UUIDv4')
            elif ident in ids:
                error(path, f'Duplicate id also in {ids[ident].relative_to(root)}')
            else:
                ids[ident] = path
            for key, allowed in [('tipo', TYPES), ('estado', STATES)]:
                if not isinstance(data.get(key), str) or data[key] not in allowed:
                    error(path, f'Invalid {key}')
            if not isinstance(data.get('resumen'), str) or not data['resumen'].strip():
                error(path, 'resumen must be a nonempty string')
            if 'aliases' in data and (not isinstance(data['aliases'], list) or any(not isinstance(a, str) or not a.strip() for a in data['aliases'])):
                error(path, 'aliases must be a list of nonempty strings')
            for key in ('actualizado', 'verificado'):
                if key == 'verificado' and key not in data:
                    continue
                value = valid_date(data.get(key))
                if value is None:
                    error(path, f'{key} must be an ISO calendar date YYYY-MM-DD')
                elif value > date.today():
                    warning(path, f'{key} date is in the future and needs review')
            if 'sustituido_por' in data and not valid_id(data['sustituido_por']):
                error(path, 'sustituido_por must be an n-UUIDv4')
        tokens = PARSER.parse(body)
        documents[path] = tokens
        graph[path] = set()
        excluded_lines = set()
        for token in tokens:
            if token.type in {'fence', 'code_block'} and token.map:
                excluded_lines.update(range(*token.map))
            elif token.type == 'heading_open' and token.markup == '=' and token.map:
                # A valid Setext underline is not an unresolved merge separator.
                excluded_lines.add(token.map[1] - 1)
        for i, line in enumerate(body.splitlines()):
            if i not in excluded_lines and CONFLICT.match(line):
                error(path, 'Unresolved conflict marker')
        if len(text.split()) > 2000 or len(text.encode('utf-8')) > 30 * 1024:
            warning(path, 'Document exceeds 2000 words or 30 KiB')
    for path, tokens in documents.items():
        entries = 0
        for token in tokens:
            for child in token.children or []:
                if child.type not in {'link_open', 'image'}:
                    continue
                href = child.attrGet('href' if child.type == 'link_open' else 'src') or ''
                if re.match(r'^(?:file:|[A-Za-z]:[\\/]|~[/\\]|/)', href):
                    if not href.startswith('//'):
                        warning(path, f'Nonportable local path {href}')
                    continue
                try:
                    parsed = urlsplit(href)
                except ValueError:
                    error(path, f'Malformed link destination {href}')
                    continue
                if parsed.scheme or parsed.netloc:
                    continue
                target = (path.parent / unquote(parsed.path)).resolve() if parsed.path else path
                if not target.is_relative_to(root):
                    warning(path, f'Local path leaves repository {href}')
                    continue
                if target.is_dir():
                    target = target / 'README.md'
                if not target.exists():
                    error(path, f'Broken local link {href}')
                    continue
                if child.type == 'link_open':
                    graph[path].add(target)
                    if parsed.path:
                        entries += 1
                if parsed.fragment and target in documents and unquote(parsed.fragment) not in heading_ids(documents[target]):
                    error(path, f'Unknown heading fragment {href}')
        if path.name == 'README.md' and entries >= 40:
            warning(path, 'Index has at least 40 direct entries')
    reachable, pending = set(), [root / 'README.md', root / 'START_HERE.md']
    while pending:
        path = pending.pop()
        if path not in reachable:
            reachable.add(path)
            pending.extend(graph.get(path, set()) - reachable)
    for path in documents:
        if path in metadata or (path.relative_to(root).parts[0] in AREAS and path.name != 'README.md'):
            if path not in reachable:
                warning(path, 'Orphan content note has no route from entry indexes')
    replacements = {}
    for path, data in metadata.items():
        if 'sustituido_por' not in data or not valid_id(data['sustituido_por']):
            continue
        target = ids.get(data['sustituido_por'])
        if target is None:
            error(path, 'Replacement id does not exist')
        elif target == path:
            error(path, 'Replacement cannot reference itself')
        else:
            replacements[path] = target
    for start in replacements:
        visited, current = set(), start
        while current in replacements:
            if current in visited:
                error(start, 'Replacement cycle detected')
                break
            visited.add(current)
            current = replacements[current]
    return result


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[2])
    args = parser.parse_args()
    if not args.root.is_dir():
        parser.error('--root must be an existing directory')
    result = validate_repository(args.root)
    for message in result.warnings:
        print(f'WARNING {message}')
    for message in result.errors:
        print(f'ERROR {message}')
    print(f'{len(result.errors)} errors, {len(result.warnings)} warnings')
    return bool(result.errors)


if __name__ == '__main__':
    raise SystemExit(main())
