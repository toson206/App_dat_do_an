# Cơm Trưa - Ứng dụng đặt cơm nội bộ (Backend API)

Hệ thống Backend RESTful API cho ứng dụng đặt cơm văn phòng nội bộ, thay thế hoàn toàn việc gom order qua chat nhóm và ghi tay Excel.

## 1. Kiến trúc hệ thống
- **Ngôn ngữ & Framework**: Python (**FastAPI** + **SQLAlchemy 2.0**)
- **Cơ sở dữ liệu**: **PostgreSQL 16** (mặc định database `dx_order`, quản lý qua **pgAdmin 4**).
- **Quản lý Migrations**: **Alembic** đánh version tuần tự (`0001`, `0002`...).
- **Đóng gói**: **Docker & Docker Compose** (Container prefix: `dx-order-*`).

## 2. Cấu trúc thư mục dự án
```
├── alembic/                  # Thư mục quản lý migrations
│   ├── versions/             # Các bản migration versioned (0001_initial_schema.py...)
│   └── env.py                # Cấu hình môi trường Alembic động theo .env
├── alembic.ini               # Cấu hình Alembic (template: %(rev)s_%(slug)s)
├── app/                      # Mã nguồn chính của ứng dụng
│   ├── models.py             # SQLAlchemy Models
│   ├── schemas/              # Thư mục Pydantic Schemas theo từng domain
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── session.py
│   │   ├── order.py
│   │   ├── menu_item.py
│   │   └── restaurant.py
│   ├── routers/              # API Sessions, Orders, Users, Upload
│   ├── services/             # Thuật toán tổng hợp tin nhắn gửi quán
│   ├── database.py           # Kết nối PostgreSQL
│   ├── config.py             # Cấu hình môi trường Settings (Pydantic)
│   ├── dependencies.py       # Dependency xác định danh tính (X-User-Id)
│   └── main.py               # Điểm khởi chạy FastAPI
├── Dockerfile                # Build container ứng dụng backend
├── docker-compose.yml        # Docker Compose chuẩn (Postgres, pgAdmin, Backend)
├── docker-compose.dev.yml    # Docker Compose phục vụ môi trường phát triển (Dev)
├── .dockerignore             # Bỏ qua file rác khi build Docker
├── .env                      # File cấu hình môi trường thực thi (không commit)
├── .env.example              # Mẫu cấu hình môi trường (nội dung chuẩn sẵn dùng)
├── requirements.txt          # Thư viện phụ thuộc (FastAPI, Alembic, SQLAlchemy...)
├── test_generator.py         # Script test thuật toán ghép món
├── start.bat                 # Script chạy nhanh 1-click cho Windows
├── stop.bat                  # Script dừng nhanh 1-click cho Windows
└── README.md
```

## 3. Hướng dẫn chạy Backend (Local)
1. Cài đặt dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Khởi tạo file `.env` từ file mẫu:
   ```bash
   cp .env.example .env
   ```
   *(File `.env.example` đã có sẵn đầy đủ cấu hình mặc định giống `.env`, có thể dùng ngay)*
3. Chạy migration để tự động tạo/cập nhật bảng trong PostgreSQL:
   ```bash
   alembic upgrade head
   ```
4. Khởi chạy server FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Truy cập Swagger UI tại: `http://localhost:8000/docs`

## 4. Quản lý Migrations với Alembic
- **Tạo migration mới sau khi sửa models**:
  ```bash
  alembic revision --autogenerate -m "mo_ta_thay_doi"
  ```
- **Áp dụng migration lên DB**:
  ```bash
  alembic upgrade head
  ```
- **Rollback 1 bản migration**:
  ```bash
  alembic downgrade -1
  ```

## 5. Hướng dẫn chạy trên Docker

### Cách 1: Chạy với Docker Compose mặc định
```bash
docker compose up --build -d
```

### Cách 2: Chạy với Docker Compose môi trường Dev (`docker-compose.dev.yml`)
```bash
docker compose -f docker-compose.dev.yml up --build -d
```

*(Container backend sẽ tự động chạy `alembic upgrade head` khi kết nối DB thành công)*

### Tắt các container:
- Nếu dùng file mặc định: `docker compose down`
- Nếu dùng file dev: `docker compose -f docker-compose.dev.yml down`

### Truy cập dịch vụ:
- **FastAPI Swagger Docs**: http://localhost:8000/docs
- **pgAdmin 4**: http://localhost:5050 (Email & Password trong `.env`)
