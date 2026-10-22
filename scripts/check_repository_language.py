"""Check publishable text and PPTX XML for unintended study translations."""
from __future__ import annotations

import json
import re
import subprocess
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
HAN = re.compile(r"[\u3400-\u9fff]")
TEXT_SUFFIXES = {".md", ".py", ".mjs", ".sh", ".json", ".csv", ".txt", ".toml", ".yml", ".yaml"}


def check():
    names = subprocess.check_output(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"], cwd=ROOT
    ).decode().split("\0")
    failures, text_count, deck_count = [], 0, 0
    for name in sorted(set(names) - {""}):
        path = ROOT / name
        if not path.is_file():
            continue
        if HAN.search(name) or "_ZH" in path.name:
            failures.append({"path": name, "reason": "translation filename"})
        if path.suffix == ".pptx":
            deck_count += 1
            with zipfile.ZipFile(path) as package:
                for part in package.namelist():
                    if part.endswith(".xml") and HAN.search(package.read(part).decode("utf-8")):
                        failures.append({"path": name, "reason": "CJK text in presentation XML", "part": part})
            continue
        if path.suffix not in TEXT_SUFFIXES and path.name not in {".gitignore", ".gitattributes"}:
            continue
        text_count += 1
        with path.open(encoding="utf-8") as source:
            for number, line in enumerate(source, 1):
                if HAN.search(line):
                    failures.append({"path": name, "reason": "CJK text", "line": number})
                    break
        # JSON writers may encode translated text using ASCII Unicode escapes.
        if path.suffix == ".json":
            value = json.loads(path.read_text())
            if HAN.search(json.dumps(value, ensure_ascii=False)):
                failures.append({"path": name, "reason": "escaped CJK text in JSON"})
    result = {"passed": not failures, "text_files_checked": text_count,
              "presentation_packages_checked": deck_count, "findings": failures,
              "scope": "Current publishable files and PPTX XML, not old Git history or image OCR."}
    print(json.dumps(result, indent=2))
    if failures:
        raise SystemExit(1)


if __name__ == "__main__":
    check()
