import os
import sys
import glob
import re
import zipfile
import hashlib
import subprocess
import shutil
from pathlib import Path

ROOT_DIR = Path(r"D:\amol_personal\pr\MLM")
BACKEND_DIR = ROOT_DIR / "backend"
FRONTEND_DIR = ROOT_DIR / "frontend"
BACKEND_DEPLOY_DIR = BACKEND_DIR / "deploy"
FRONTEND_DEPLOY_DIR = FRONTEND_DIR / "deploy"

BACKEND_ZIP_PATH = BACKEND_DEPLOY_DIR / "mlm-backend-elastic-beanstalk.zip"
FRONTEND_ZIP_PATH = FRONTEND_DEPLOY_DIR / "mystatus-frontend-prod-https.zip"

def sha256_file(filepath: Path) -> str:
    h = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

def build_frontend():
    print("\n=======================================================")
    print("STEP 1: BUILDING FRONTEND")
    print("=======================================================")
    res = subprocess.run(["npm", "run", "build"], cwd=str(FRONTEND_DIR), capture_output=True, text=True, shell=True)
    print(res.stdout)
    if res.returncode != 0:
        print("FRONTEND BUILD FAILED:")
        print(res.stderr)
        sys.exit(1)
    print("Frontend built successfully!")

def create_backend_zip():
    print("\n=======================================================")
    print("STEP 2: PACKAGING BACKEND ZIP")
    print("=======================================================")
    BACKEND_DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    
    if BACKEND_ZIP_PATH.exists():
        BACKEND_ZIP_PATH.unlink()

    def should_exclude(rel_path: str) -> bool:
        norm = rel_path.replace("\\", "/")
        parts = norm.split("/")
        
        ignored_names = {
            ".git", ".github", "__pycache__", ".pytest_cache", "tests", "data", "deploy",
            "venv", ".venv", "ENV", "env", "node_modules", "dist", "build", ".vscode", ".idea"
        }
        for p in parts:
            if p in ignored_names:
                return True
        
        ext_lower = Path(norm).suffix.lower()
        if ext_lower in {".pyc", ".pyo", ".pyd", ".sqlite", ".sqlite3", ".db", ".log"}:
            return True
        if norm.endswith((".sqlite3-wal", ".sqlite3-shm", ".db.bak", ".coverage")):
            return True
            
        filename = Path(norm).name
        if filename == ".env" or (filename.startswith(".env.") and filename != ".env.example"):
            return True
            
        return False

    included = []
    with zipfile.ZipFile(str(BACKEND_ZIP_PATH), "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(str(BACKEND_DIR)):
            for file in files:
                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(BACKEND_DIR))
                
                if should_exclude(rel_path):
                    continue
                
                arcname = rel_path.replace("\\", "/")
                zf.write(full_path, arcname=arcname)
                included.append(arcname)

    print(f"Backend ZIP created: {BACKEND_ZIP_PATH}")
    print(f"Total files included: {len(included)}")

    # Also copy to root deploy directory
    root_deploy_dir = ROOT_DIR / "deploy"
    root_deploy_dir.mkdir(parents=True, exist_ok=True)
    root_backend_zip = root_deploy_dir / "mlm-backend-elastic-beanstalk.zip"
    shutil.copy2(BACKEND_ZIP_PATH, root_backend_zip)
    print(f"Copied to root deploy directory: {root_backend_zip}")

def create_frontend_zip():
    print("\n=======================================================")
    print("STEP 3: PACKAGING FRONTEND ZIP")
    print("=======================================================")
    FRONTEND_DEPLOY_DIR.mkdir(parents=True, exist_ok=True)
    
    if FRONTEND_ZIP_PATH.exists():
        FRONTEND_ZIP_PATH.unlink()

    def should_exclude_frontend(rel_path: str) -> bool:
        norm = rel_path.replace("\\", "/")
        parts = norm.split("/")
        
        ignored_dirs = {
            ".git", ".github", "node_modules", ".pytest_cache", "__pycache__",
            ".vscode", ".idea", "deploy"
        }
        for p in parts:
            if p in ignored_dirs:
                return True
                
        filename = Path(norm).name
        if filename in {".gitignore", ".env.production", ".env.local", ".env.development", ".env"} or (filename.startswith(".env.") and filename != ".env.example"):
            return True
            
        ext_lower = Path(norm).suffix.lower()
        if ext_lower in {".pyc", ".log", ".tmp"}:
            return True
            
        return False

    included = []
    with zipfile.ZipFile(str(FRONTEND_ZIP_PATH), "w", zipfile.ZIP_DEFLATED) as zf:
        for root, _, files in os.walk(str(FRONTEND_DIR)):
            for file in files:
                full_path = Path(root) / file
                rel_path = str(full_path.relative_to(FRONTEND_DIR))
                
                if should_exclude_frontend(rel_path):
                    continue
                
                arcname = rel_path.replace("\\", "/")
                zf.write(full_path, arcname=arcname)
                included.append(arcname)

    print(f"Frontend ZIP created: {FRONTEND_ZIP_PATH}")
    print(f"Total files included: {len(included)}")

    # Also copy to root deploy directory and root directory
    root_deploy_dir = ROOT_DIR / "deploy"
    root_deploy_dir.mkdir(parents=True, exist_ok=True)
    root_frontend_zip = root_deploy_dir / "mystatus-frontend-prod-https.zip"
    shutil.copy2(FRONTEND_ZIP_PATH, root_frontend_zip)
    root_zip = ROOT_DIR / "mystatus-frontend-prod-https.zip"
    shutil.copy2(FRONTEND_ZIP_PATH, root_zip)
    print(f"Copied to root deploy directory: {root_frontend_zip}")
    print(f"Copied to root directory: {root_zip}")

def verify_all():
    print("\n=======================================================")
    print("STEP 4: DETAILED PROGRAMMATIC VERIFICATION")
    print("=======================================================")
    
    # 1. Frontend verification
    f_size = FRONTEND_ZIP_PATH.stat().st_size
    f_sha = sha256_file(FRONTEND_ZIP_PATH)
    
    print(f"\n[FRONTEND ZIP]")
    print(f"  Path: {FRONTEND_ZIP_PATH}")
    print(f"  Size: {f_size:,} bytes ({f_size / 1024:.2f} KB)")
    print(f"  SHA-256: {f_sha}")
    
    with zipfile.ZipFile(str(FRONTEND_ZIP_PATH), "r") as zf:
        f_namelist = zf.namelist()
        
        corrupt = zf.testzip()
        print(f"  Integrity test: {'PASSED (no corruption)' if corrupt is None else f'FAILED: {corrupt}'}")
        
        f_root_entries = sorted(list(set(n.split("/")[0] for n in f_namelist)))
        print(f"  Root entries: {f_root_entries}")
        
        env_prod_present = any(n == ".env.production" or n.endswith("/.env.production") for n in f_namelist)
        print(f"  .env.production EXCLUDED: {'PASS' if not env_prod_present else 'FAIL'}")
        
        print(f"  Dockerfile present: {'PASS' if 'Dockerfile' in f_namelist else 'FAIL'}")
        print(f"  nginx.conf present: {'PASS' if 'nginx.conf' in f_namelist else 'FAIL'}")
        print(f"  dist/index.html present: {'PASS' if 'dist/index.html' in f_namelist else 'FAIL'}")
        
        bad_f = [n for n in f_namelist if any(x in n for x in [".git", "node_modules", ".env.production", ".env.local"])]
        print(f"  Prohibited entries found: {bad_f} ({'PASS' if not bad_f else 'FAIL'})")
        
        js_files = [n for n in f_namelist if n.startswith("dist/assets/") and n.endswith(".js")]
        all_js = ""
        for js in js_files:
            all_js += zf.read(js).decode("utf-8", errors="ignore")
            
        print(f"  Dist JS files: {js_files}")
        
        has_prod_api = "https://api.mystatusads333.com/api" in all_js or "https://api.mystatusads333.com" in all_js
        print(f"  Production API (https://api.mystatusads333.com/api): {'PASS' if has_prod_api else 'FAIL'}")
        
        forbidden_apis = ["13.207.123.229", "172.31.8.152", "127.0.0.1:8000", "localhost:8000", "http://api.mystatusads333.com"]
        for fa in forbidden_apis:
            is_present = fa in all_js
            print(f"  Forbidden API target [{fa}] present: {is_present} ({'PASS' if not is_present else 'FAIL'})")
            
        print(f"  dist/payment-qr.png present: {'PASS' if 'dist/payment-qr.png' in f_namelist else 'FAIL'}")
        print(f"  public/payment-qr.png present: {'PASS' if 'public/payment-qr.png' in f_namelist else 'FAIL'}")

        features = [
            "Franchise Partner",
            "Rank & Rewards",
            "STAR",
            "SUPER STAR",
            "VIP",
            "2,100",
            "5,100",
            "51,000",
            "3,00,000",
            "RETOPUP_REQUIRED",
            "Scooter",
            "35,400",
            "10,000",
            "payment-qr.png"
        ]
        for feat in features:
            print(f"  Feature string [{feat}]: {'PASS' if feat in all_js else 'FAIL'}")

    # 2. Backend verification
    b_size = BACKEND_ZIP_PATH.stat().st_size
    b_sha = sha256_file(BACKEND_ZIP_PATH)
    
    print(f"\n[BACKEND ZIP]")
    print(f"  Path: {BACKEND_ZIP_PATH}")
    print(f"  Size: {b_size:,} bytes ({b_size / 1024:.2f} KB)")
    print(f"  SHA-256: {b_sha}")
    
    with zipfile.ZipFile(str(BACKEND_ZIP_PATH), "r") as zf:
        b_namelist = zf.namelist()
        
        corrupt = zf.testzip()
        print(f"  Integrity test: {'PASSED (no corruption)' if corrupt is None else f'FAILED: {corrupt}'}")
        
        b_root_entries = sorted(list(set(n.split("/")[0] for n in b_namelist)))
        print(f"  Root entries: {b_root_entries}")
        
        key_files = [
            "Procfile",
            "requirements.txt",
            "Dockerfile",
            "alembic.ini",
            "run.py",
            "seed.py",
            "create_backup.py",
            "app/main.py",
            "app/config.py",
            "app/database.py",
            "app/security.py",
            "app/models/rank_config.py",
            "app/models/rank_achievement.py",
            "app/models/earning_cycle.py",
            "app/models/wallet.py",
            "app/models/security_pin.py",
            "app/services/rank_service.py",
            "app/services/earning_cap_service.py",
            "app/services/wallet_service.py",
            "app/services/commission_service.py",
            "app/routers/rank_rewards.py",
            "app/routers/earning_cap.py",
            "app/routers/auth.py",
            "app/routers/dashboard.py",
            "app/routers/network.py"
        ]
        for kf in key_files:
            present = kf in b_namelist
            print(f"  Key file [{kf}]: {'PASS' if present else 'FAIL'}")
            
        dockerfile_content = zf.read("Dockerfile").decode("utf-8")
        has_expose_8000 = "EXPOSE 8000" in dockerfile_content
        has_expose_5000 = "EXPOSE 5000" in dockerfile_content
        print(f"  Dockerfile EXPOSE 8000: {'PASS' if has_expose_8000 and not has_expose_5000 else 'FAIL'}")
        
        procfile_content = zf.read("Procfile").decode("utf-8")
        print(f"  Procfile content: {procfile_content.strip()}")
        
        bad_b = [n for n in b_namelist if any(x in n for x in [".git", "__pycache__", ".pytest_cache", "tests/", "data/", ".env"])]
        print(f"  Prohibited entries found: {bad_b} ({'PASS' if not bad_b else 'FAIL'})")
        
        all_py = ""
        for n in b_namelist:
            if n.endswith(".py"):
                all_py += zf.read(n).decode("utf-8", errors="ignore") + "\n"
                
        b_features = [
            ("STAR", "STAR" in all_py),
            ("SUPER_STAR / SUPER STAR", "SUPER_STAR" in all_py or "SUPER STAR" in all_py),
            ("VIP", "VIP" in all_py),
            ("RANK_REWARD", "RANK_REWARD" in all_py),
            ("RETOPUP_REQUIRED", "RETOPUP_REQUIRED" in all_py),
            ("300000", "300000" in all_py),
            ("35400 / 35,400", "35400" in all_py),
            ("2100", "2100" in all_py),
            ("5100", "5100" in all_py),
            ("51000", "51000" in all_py),
            ("SCOOTER / EV Scooter", "SCOOTER" in all_py or "Scooter" in all_py),
            ("Partner Network / Franchise Partner", "partner" in all_py.lower())
        ]
        for label, present in b_features:
            print(f"  Backend feature [{label}]: {'PASS' if present else 'FAIL'}")

if __name__ == "__main__":
    build_frontend()
    create_backend_zip()
    create_frontend_zip()
    verify_all()
