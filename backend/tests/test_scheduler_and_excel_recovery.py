import io
import os
import openpyxl
import pytest
from app.services.excel_backup_service import excel_backup_service, TABLE_IMPORT_EXPORT_ORDER
from app.services.scheduler_service import scheduler_service
from app.models.user import User
from app.models.package import Package

def test_excel_database_export_contains_all_tables_and_summary(db_session):
    """Verifies that export_database_to_excel produces a valid .xlsx workbook
    containing the SYSTEM_SUMMARY sheet and all 26 relational table sheets.
    """
    excel_bytes, filename, meta = excel_backup_service.export_database_to_excel(
        db=db_session,
        admin_id=1,
        notes="Automated PyTest Export",
        save_copy_to_disk=False
    )

    assert excel_bytes is not None
    assert len(excel_bytes) > 1000
    assert filename.startswith("mlm_database_backup_")
    assert filename.endswith(".xlsx")
    assert meta["total_tables"] >= 20
    assert meta["total_records"] >= 1

    # Verify Excel workbook structure via openpyxl
    wb = openpyxl.load_workbook(io.BytesIO(excel_bytes), data_only=True)
    sheet_names = wb.sheetnames

    # Summary sheet check
    assert "SYSTEM_SUMMARY" in sheet_names
    summary_ws = wb["SYSTEM_SUMMARY"]
    assert "PARTNER NETWORK & REWARDS" in str(summary_ws.cell(row=1, column=1).value)

    # Core table sheets check
    for tbl in ["users", "packages", "wallets", "binary_volumes", "purchases", "commissions", "rank_configs"]:
        assert tbl in sheet_names, f"Expected sheet '{tbl}' in exported Excel workbook."

    # Validate users sheet has headers
    users_ws = wb["users"]
    headers = [cell.value for cell in users_ws[1]]
    assert "id" in headers
    assert "email" in headers
    assert "role" in headers


def test_excel_database_import_and_disaster_recovery_roundtrip(db_session):
    """Verifies full roundtrip: export current DB -> clear or update -> restore from Excel -> verify restored rows."""
    # 1. Export
    excel_bytes, _, meta_export = excel_backup_service.export_database_to_excel(
        db=db_session,
        admin_id=1,
        notes="Pre-restore test export",
        save_copy_to_disk=False
    )

    users_count_before = db_session.query(User).count()
    assert users_count_before > 0

    # 2. Import back with overwrite=True
    restore_report = excel_backup_service.import_database_from_excel(
        db=db_session,
        file_bytes=excel_bytes,
        admin_id=1,
        overwrite=True
    )

    assert restore_report["success"] is True
    assert restore_report["total_tables"] >= 20
    assert restore_report["total_inserted"] + restore_report["total_updated"] >= users_count_before

    # 3. Verify user integrity after restoration
    admin_user = db_session.query(User).filter(User.role == "ADMIN").first()
    assert admin_user is not None
    assert admin_user.is_active is True


def test_scheduler_service_status_and_job_triggers(db_session):
    """Verifies scheduler status inspection and on-demand job execution."""
    status = scheduler_service.get_status(db=db_session)
    assert "is_running" in status
    assert "jobs" in status
    assert len(status["jobs"]) >= 3

    # Check registered jobs
    job_ids = [j["job_id"] for j in status["jobs"]]
    assert "daily_reward_settlement" in job_ids
    assert "automated_backup" in job_ids
    assert "slot_settlement_maintenance" in job_ids

    # Toggle scheduler
    assert scheduler_service.toggle(False) is False
    assert scheduler_service.toggle(True) is True


@pytest.mark.asyncio
async def test_scheduler_manual_job_execution(db_session):
    """Verifies that triggering jobs on demand executes cleanly and records history."""
    # Execute automated backup job
    res = await scheduler_service.run_job_async(
        job_id="automated_backup",
        db=db_session,
        admin_id=1,
        force=True
    )
    assert res["success"] is True
    assert res["job_id"] == "automated_backup"
    assert len(scheduler_service.history) > 0


def test_admin_api_scheduler_and_excel_export_endpoints(client):
    """Tests FastAPI HTTP endpoints for scheduler and Excel disaster recovery."""
    # Obtain admin token
    login_res = client.post("/api/auth/login", json={
        "identifier": "admin@demo.com",
        "password": "Admin@123"
    })
    if login_res.status_code != 200:
        login_res = client.post("/api/auth/login", json={
            "identifier": "admin@platform.com",
            "password": "Admin@123"
        })
    admin_token = login_res.json()["data"]["token"]
    headers = {"Authorization": f"Bearer {admin_token}"}

    # 1. GET Scheduler status
    res_sched = client.get("/api/admin/system/scheduler", headers=headers)
    assert res_sched.status_code == 200
    sched_data = res_sched.json()["data"]
    assert "jobs" in sched_data
    assert len(sched_data["jobs"]) >= 3

    # 2. POST Toggle scheduler
    res_toggle = client.post("/api/admin/system/scheduler/toggle", json={"enabled": True}, headers=headers)
    assert res_toggle.status_code == 200

    # 3. GET Export Database to Excel
    res_export = client.get("/api/admin/system/database/export-excel", headers=headers)
    assert res_export.status_code == 200
    assert res_export.headers["content-type"] == "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    assert "attachment; filename=" in res_export.headers.get("content-disposition", "")
    assert len(res_export.content) > 1000

    # 4. POST Import Database from Excel
    excel_file = io.BytesIO(res_export.content)
    files = {"file": ("test_backup.xlsx", excel_file, "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")}
    res_import = client.post("/api/admin/system/database/import-excel?overwrite=true", files=files, headers=headers)
    assert res_import.status_code == 200
    import_data = res_import.json()
    assert import_data["success"] is True
    assert import_data["data"]["total_tables"] >= 20

    # 5. GET Backups list
    res_backups = client.get("/api/admin/system/database/backups", headers=headers)
    assert res_backups.status_code == 200
    assert "backups" in res_backups.json()["data"]
