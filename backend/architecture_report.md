# ShopEarn Platform — Architecture Report

## 1. System Overview
ShopEarn is a highly scalable **multi-level marketing (MLM) business platform** that bridges three core user roles:
- **Admin (Role 1):** Platform owner overseeing operations, approving sales, collecting commission, and managing MLM payouts.
- **Shopper/Seller (Role 2):** Retail shop owners who register, generate bills for customers, and pay a predefined commission percentage to the platform.
- **Customer (Role 3):** End consumers who purchase from shops, earn MLM-based cashback, and participate in the C2C marketplace.

## 2. Tech Stack
- **Database:** **Neon (Serverless PostgreSQL)** - Provides a resilient, auto-scaling, permanent database solution replacing ephemeral free-tier databases.
- **Backend Framework:** **Django 4.x + Django REST Framework (DRF)**
- **Frontend (Web):** **React 18 + Vite + TailwindCSS v4 + Zustand + React Query**
- **Frontend (Mobile):** **React Native (Expo)**
- **Message Broker / Queue:** **Redis** (Render Free Tier - 25MB RAM, `allkeys-lru` eviction policy)
- **Background Task Processing:** **Celery**
- **Cloud Storage:** **AWS S3** (For product images and media uploads)
- **Payment Gateway:** **Razorpay** (Live Mode integration)
- **Hosting & Infrastructure:** 
  - Backend API + Celery Worker + Redis: **Render.com**
  - Frontend Web: **Vercel / Netlify**

## 3. Infrastructure & Deployment Architecture
The production infrastructure is deployed with a decoupled, asynchronous architecture to ensure high availability and responsiveness under load:

*   **Render Web Service (`myapp-api`):** Runs Gunicorn (`--workers 1 --threads 4`). Handles incoming REST API requests from the React and React Native frontends.
*   **Render Redis (`myapp-redis`):** Acts purely as a fast, in-memory message broker (Post Office) for Celery. It does not store persistent database records or cache full HTML pages to preserve its 25MB memory limit.
*   **Render Background Worker (`celery-worker`):** Runs the Celery daemon (`--concurrency=1`). Listens to Redis and sequentially processes heavy computational tasks (like the MLM math pipeline) to prevent the Web Service from freezing during traffic spikes.
*   **Neon Database:** The single source of truth. Both the Render Web Service and the Celery Worker connect to this external PostgreSQL instance.

## 4. Core Business Workflows
### The Sale & Commission Pipeline
1. **Bill Creation:** A Shopper submits a bill (`DailySale`) for a Customer. The status defaults to Pending (`rep_status='N'`).
2. **Approval (Security Locked):** The Admin reviews the physical/online commission payment and clicks "Approve" via the Admin Dashboard. (Shoppers are strictly forbidden from approving sales).
3. **Asynchronous Offloading:** Upon approval, the Django API instantly updates the sale to Approved (`rep_status='V'`), creates a `CommissionPayment` record, and fires a `process_sale_commission_task.delay()` to Redis. The API returns a `200 OK` in milliseconds.
4. **Background MLM Execution:** The Celery Worker picks up the task from Redis, calculates the complex cascading MLM payouts (C1, C2, C3, and Plans 1-10), and commits the financial updates to the Neon Database.

### The C2C Marketplace
- Customers can buy and sell products directly to each other (`C2CListing`).
- Purchases trigger a similar `process_marketplace_order_task.delay()` which routes the marketplace commission through the same asynchronous MLM pipeline.

## 5. Security & Stability Highlights
- **Strict Role-Based Access Control (RBAC):** Crucial endpoints like `/api/v1/billing/sales/<id>/approve/` are hard-locked to Admin (`role == 1`).
- **Resilient Queuing:** Celery tasks are configured with `acks_late=True` and exponential backoff. If the worker crashes mid-calculation, the task remains in Redis and retries safely, ensuring zero lost commissions.
- **Database Integrity:** Transactions are wrapped in `transaction.atomic()` with `select_for_update()` row-level locking to prevent race conditions during concurrent financial payouts.
- **Null Safety:** `CommissionPayment` gracefully falls back to `"cash"` if `payment_method` is omitted, satisfying strict PostgreSQL `NOT NULL` constraints.
