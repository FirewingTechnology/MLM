import os
import zipfile
import hashlib

backend_zip = 'd:/amol_personal/pr/MLM/backend/deploy/mlm-backend-elastic-beanstalk.zip'
frontend_zip = 'd:/amol_personal/pr/MLM/frontend/deploy/mystatus-frontend-prod-https.zip'

def sha256_file(path):
    h = hashlib.sha256()
    with open(path, 'rb') as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()

print("=================== BACKEND ZIP VERIFICATION ===================")
b_size = os.path.getsize(backend_zip)
b_sha = sha256_file(backend_zip)
print(f"File: {backend_zip}")
print(f"Size: {b_size:,} bytes ({round(b_size/1024, 2)} KB)")
print(f"SHA-256: {b_sha}")

with zipfile.ZipFile(backend_zip, 'r') as bz:
    names = bz.namelist()
    print(f"Total files: {len(names)}")
    root_items = sorted(list(set(n.split('/')[0] for n in names)))
    print("Root entries:", root_items)
    
    # Check exclusions
    bad_entries = [n for n in names if any(x in n for x in ['.git', '__pycache__', '.pytest_cache', 'tests/', 'data/', '.env'])]
    print("Prohibited entries found:", bad_entries)
    
    # Check key files
    key_files = [
        'Procfile', 'requirements.txt', 'alembic.ini', 'run.py',
        'app/main.py', 'app/config.py', 'app/models/rank_config.py',
        'app/models/rank_achievement.py', 'app/models/earning_cycle.py',
        'app/services/rank_service.py', 'app/services/earning_cap_service.py',
        'app/services/wallet_service.py', 'app/services/commission_service.py',
        'app/routers/rank_rewards.py', 'app/routers/earning_cap.py'
    ]
    for kf in key_files:
        print(f"  Key file [{kf}]: present = {kf in names}")
    
    # Search strings inside backend zip
    all_b_text = ''
    for n in names:
        if n.endswith('.py'):
            all_b_text += bz.read(n).decode('utf-8', errors='ignore') + '\n'
    
    print("\nBackend Content String Checks:")
    b_checks = ['partner', 'STAR', 'SUPER_STAR', 'VIP', 'RANK_REWARD', 'RETOPUP_REQUIRED', '300000', '2100', '5100', '51000', 'SCOOTER']
    for bc in b_checks:
        print(f"  \"{bc}\": present = {bc in all_b_text or bc.lower() in all_b_text.lower()}")

print("\n=================== FRONTEND ZIP VERIFICATION ===================")
f_size = os.path.getsize(frontend_zip)
f_sha = sha256_file(frontend_zip)
print(f"File: {frontend_zip}")
print(f"Size: {f_size:,} bytes ({round(f_size/1024, 2)} KB)")
print(f"SHA-256: {f_sha}")

with zipfile.ZipFile(frontend_zip, 'r') as fz:
    fnames = fz.namelist()
    print(f"Total files: {len(fnames)}")
    f_root_items = sorted(list(set(n.split('/')[0] for n in fnames)))
    print("Root entries:", f_root_items)
    
    # Check exclusions (.env.production MUST be excluded)
    bad_f_entries = [n for n in fnames if any(x in n for x in ['.git', 'node_modules', '.env.production', '.env.local', '.env.development'])]
    print("Prohibited entries found:", bad_f_entries)
    
    # Check key files
    f_key_files = [
        'Dockerfile', 'nginx.conf', 'dist/index.html',
        'dist/favicon.svg', 'dist/icons.svg', 'dist/logo.svg',
        'package.json'
    ]
    for fk in f_key_files:
        print(f"  Key file [{fk}]: present = {fk in fnames}")
    
    # Check dist assets
    dist_js = [n for n in fnames if n.startswith('dist/assets/') and n.endswith('.js')]
    print("Dist JS files:", dist_js)
    
    all_f_dist_text = ''
    for dj in dist_js:
        all_f_dist_text += fz.read(dj).decode('utf-8', errors='ignore')
    
    print("\nFrontend Dist API / Security Checks:")
    print("  Production API (https://api.mystatusads333.com):", "https://api.mystatusads333.com" in all_f_dist_text)
    print("  Invalid IP 13.207.123.229:", "13.207.123.229" in all_f_dist_text)
    print("  Invalid IP 172.31.8.152:", "172.31.8.152" in all_f_dist_text)
    print("  Invalid IP 127.0.0.1:", "127.0.0.1" in all_f_dist_text)
    print("  Hardcoded localhost API (:8000):", ":8000" in all_f_dist_text)
    
    print("\nFrontend Dist Feature String Checks:")
    f_checks = ['Franchise Partner', 'Rank & Rewards', 'STAR', 'SUPER STAR', 'VIP', 'RANK_REWARD', 'RETOPUP_REQUIRED', '300000', '3,00,000', '2,100', '5,100', '51,000', 'Scooter']
    for fc in f_checks:
        print(f"  \"{fc}\": present = {fc in all_f_dist_text}")
