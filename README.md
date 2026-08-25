# Mobile-First Virtual Binary MLM Demo Web Application

A lightweight, enterprise-grade client demonstration platform for a **Binary MLM System** built with **Python FastAPI** on the backend and **React (Vite, TypeScript, Tailwind CSS, TanStack Query)** on the frontend.

> [!IMPORTANT]
> **DEMO MODE — NO REAL MONEY**  
> All purchases, packages, Business Volume (BV), commissions, virtual wallets, and withdrawals are **100% simulated demonstration data**.

---

## 1. Technology Stack

- **Backend**: **Python FastAPI** + Uvicorn + Pydantic v2 + SQLAlchemy 2.0 (PostgreSQL / SQLite) + JWT Authentication (PyJWT + bcrypt).
- **Frontend**: **React 18** + Vite + TypeScript + Tailwind CSS + TanStack Query + React Router + Axios + Lucide icons.
- **Design**: Minimal, clean, mobile-first fintech dashboard with responsive bottom navigation (`Home`, `Network`, `Wallet`, `More`).

---

## 2. The 5 User-Facing Screens

1. **Screen 1 — Login / Register** (`/login`, `/register`)
   - 1-Click Quick Demo logins (Amol Root & System Admin).
   - Auto-detection of sponsor when registering via `/register?ref=AMOL001`.
   - Separate selection of **Sponsor** vs **Binary Placement Parent & Position** (`LEFT` | `RIGHT`).

2. **Screen 2 — Dashboard** (`/dashboard`)
   - **Virtual Wallet Card**: Live balance + total earned.
   - **Two Volume Cards**: Left BV & Right BV with carry-forward trackers.
   - **Primary Action**: Big prominent `[BUY ₹35,000 PACKAGE]` button.
   - **Your Referral Code**: 1-click copy widget.
   - **Binary Network Preview**: Visual tree sub-branch + `[View Full Network]` button.

3. **Screen 3 — Network** (`/network`)
   - Touch-friendly binary tree viewer with pan, zoom, level switcher (2, 3, 4 levels), breadcrumbs, search-to-node focus, and bottom sheet member inspection.

4. **Screen 4 — Wallet** (`/wallet`)
   - Virtual Wallet balance, all-time earnings, double-entry immutable ledger stream, and `[Request Demo Withdrawal]` modal.

5. **Screen 5 — Admin** (`/admin`)
   - Platform KPIs, virtual sales, distributors directory, withdrawal approval queue (1-click Approve/Reject in DB transaction), and 1-click **Reset Demo Environment**.

---

## 3. MLM Business Rules & Math

- **Product Package**: **Premium Business Package** (₹35,000 Total = ₹30,000 Product Value + ₹5,000 GST = **30,000 BV**).
- **Direct Referral Commission**: **10%** on BV (**₹3,000**) credited to sponsor's virtual wallet.
- **Binary Matching Commission**: **10%** on matched volume (`min(carry_left, carry_right)`).
- **Carry-Forward Retention**: Unmatched BV is preserved in the respective leg.
- **Idempotency Protection**: Unique transaction IDs prevent duplicate credits on double-clicks or browser refreshes.

---

## 4. Demo Accounts & Seed Network

| Role | Name | Email | Password | Referral Code | Placement |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **Superuser** | System Admin | `admin@demo.com` | `Admin@123` | `ADMIN001` | System |
| **Root User** | Amol Sharma | `amol@demo.com` | `Demo@123` | `AMOL001` | Root Node |
| **Distributor** | Rahul Verma | `rahul@demo.com` | `Demo@123` | `RAHUL001` | Amol **LEFT** |
| **Distributor** | Priya Patel | `priya@demo.com` | `Demo@123` | `PRIYA001` | Amol **RIGHT** |
| **Distributor** | Akash Singh | `akash@demo.com` | `Demo@123` | `AKASH001` | Rahul **LEFT** |
| **Distributor** | Neha Joshi | `neha@demo.com` | `Demo@123` | `NEHA001` | Rahul **RIGHT** |
| **Distributor** | Rohit Gupta | `rohit@demo.com` | `Demo@123` | `ROHIT001` | Priya **LEFT** |
| **Distributor** | Sneha Kulkarni | `sneha@demo.com` | `Demo@123` | `SNEHA001` | Priya **RIGHT** |

---

## 5. How to Run Locally

### 1. Start FastAPI Backend (Port 5000)
```bash
cd backend
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python run.py
```
*API is accessible at `http://127.0.0.1:5000` with interactive Swagger docs at `http://127.0.0.1:5000/docs`.*

### 2. Start React Frontend (Port 5173)
```bash
cd frontend
npm install
npm run dev
```
*Web app runs on `http://localhost:5173`.*

### 3. Run Backend Tests
```bash
$env:PYTHONPATH="backend"; backend\venv\Scripts\pytest backend/tests
```
