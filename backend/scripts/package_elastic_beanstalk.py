"""
AWS Elastic Beanstalk Deployment Packaging Utility
==================================================
Packages the backend directory into a deployment-ready ZIP archive
with Procfile, requirements.txt, alembic.ini, alembic/, app/ at root.
Applies .ebignore rules to exclude tests, virtual environments, caches,
and local SQLite databases.
"""

import os
import sys
import zipfile
import fnmatch
from pathlib import Path

def parse_ebignore(ebignore_path: str) -> list:
    patterns = []
    if os.path.exists(ebignore_path):
        with open(ebignore_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    patterns.append(line)
    return patterns

def is_ignored(rel_path: str, patterns: list) -> bool:
    norm_path = rel_path.replace('\\', '/')
    for pat in patterns:
        pat_clean = pat.rstrip('/')
        # Check exact or directory match
        if fnmatch.fnmatch(norm_path, pat_clean) or fnmatch.fnmatch(norm_path, pat_clean + '/*') or fnmatch.fnmatch(os.path.basename(norm_path), pat_clean):
            return True
        # Check parent parts
        parts = norm_path.split('/')
        for i in range(1, len(parts) + 1):
            sub = '/'.join(parts[:i])
            if fnmatch.fnmatch(sub, pat_clean) or fnmatch.fnmatch(sub, pat_clean + '/'):
                return True
    return False

def create_eb_zip(backend_dir: str, output_zip_path: str):
    os.makedirs(os.path.dirname(os.path.abspath(output_zip_path)), exist_ok=True)
    ebignore_path = os.path.join(backend_dir, '.ebignore')
    patterns = parse_ebignore(ebignore_path)

    # Core required exclusions
    forced_exclusions = [
        'venv', '.venv', '.pytest_cache', '__pycache__', 'tests', 'data', 'deploy',
        '*.sqlite', '*.sqlite3', '*.sqlite3-wal', '*.sqlite3-shm', '*.pyc', '*.pyo',
        '.env', '.env.local', '.git', '.github', '*.log'
    ]
    patterns.extend(forced_exclusions)

    included_files = []
    excluded_files = []

    print(f"\n[PACKAGING] Building Elastic Beanstalk deployment ZIP from: {backend_dir}")
    print(f"[PACKAGING] Output ZIP path: {output_zip_path}")

    with zipfile.ZipFile(output_zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, dirs, files in os.walk(backend_dir):
            for f in files:
                full_path = os.path.join(root, f)
                rel_path = os.path.relpath(full_path, backend_dir)

                if is_ignored(rel_path, patterns):
                    excluded_files.append(rel_path)
                    continue

                zipf.write(full_path, arcname=rel_path)
                included_files.append(rel_path)

    zip_size_bytes = os.path.getsize(output_zip_path)
    zip_size_mb = round(zip_size_bytes / (1024 * 1024), 2)

    print(f"\n[SUCCESS] Deployment ZIP created successfully!")
    print(f"  * Path: {output_zip_path}")
    print(f"  * Size: {zip_size_mb} MB ({zip_size_bytes:,} bytes)")
    print(f"  * Included Files Count: {len(included_files)}")
    print(f"  * Excluded Files Count: {len(excluded_files)}")

    print("\n--- ROOT FILES IN ZIP ---")
    with zipfile.ZipFile(output_zip_path, 'r') as zipf:
        root_entries = [name for name in zipf.namelist() if '/' not in name or name.count('/') == 1 and name.endswith('/')]
        for name in sorted(root_entries)[:15]:
            print(f"  * {name}")

    return {
        "zip_path": output_zip_path,
        "size_bytes": zip_size_bytes,
        "size_mb": zip_size_mb,
        "included_files": included_files,
        "excluded_files": excluded_files
    }

if __name__ == "__main__":
    b_dir = os.path.abspath("backend")
    out_zip = os.path.abspath("deploy/mlm-backend-elastic-beanstalk.zip")
    res = create_eb_zip(b_dir, out_zip)
