"""Check the source-only export without executing historical patch scripts."""
from pathlib import Path
import ast
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[2]
ALLOWED = {'.py', '.md', '.json', '.txt'}
SPECIAL = {'LICENSE', '.gitignore', '.gitattributes'}


def validate(root):
    files = [p for p in root.rglob('*') if p.is_file() and '.git' not in p.relative_to(root).parts]
    for path in files:
        assert not path.is_symlink(), f'Symlink: {path}'
        assert path.suffix in ALLOWED or path.name in SPECIAL, f'Non-source file: {path}'
        if path.suffix == '.py':
            assert path.parent == root/'source/scripts', f'Python file outside source/scripts: {path}'
        text = path.read_text(encoding='utf-8')
        assert '\x00' not in text, f'Binary content: {path}'
        assert not re.search(r'C:[/\\]Users[/\\]', text, re.I), f'Personal path: {path}'
        assert not re.search(r'(?:gh[pousr]_|sk-proj-)[A-Za-z0-9_-]{20,}', text), f'Possible credential: {path}'
        if path.suffix == '.py':
            tree = ast.parse(text, filename=str(path))
            for node in ast.walk(tree):
                if isinstance(node, ast.Constant) and isinstance(node.value, bytes):
                    assert len(node.value) < 4096, f'Embedded binary payload: {path}'
                if isinstance(node, ast.Constant) and isinstance(node.value, str):
                    assert not re.fullmatch(r'[0-9a-fA-F]{8192,}', node.value), f'Embedded hex payload: {path}'
    manifest = json.loads((root/'docs/source-manifest.json').read_text())
    assert {p.relative_to(root).as_posix() for p in (root/'source').rglob('*.py') if p.name != 'validate_repository.py'} == {r['path'] for r in manifest}
    for row in manifest:
        path = root/row['path']
        assert hashlib.sha256(path.read_bytes()).hexdigest() == row['sha256'], f'Source hash mismatch: {path}'
    return len(files), len(manifest)


if __name__ == '__main__':
    files, scripts = validate(ROOT)
    print(f'PASS: {files} text/source files; {scripts} historical scripts parsed and hash-verified. No patch or game/media binaries in repository.')
