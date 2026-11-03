# Cơm Trưa - Ứng dụng đặt cơm nội bộ

Một công cụ nội bộ gọn nhẹ thay thế việc gom order cơm qua chat nhóm và ghi tay Excel.

## 1. Kiến trúc hệ thống
- **Cơ sở dữ liệu**: **PostgreSQL Local** (quản lý trực tiếp qua **pgAdmin 4** với database `App`).
- **Backend**: Python (**FastAPI + SQLAlchemy**) xử lý API gom đơn, tính tiền, thuật toán tổng hợp tin nhắn gửi quán cơm và lưu ảnh local.
- **Frontend**: React (Vite + Tailwind CSS + Lucide Icons) tối ưu giao diện Mobile-first.

## 2. Cấu trúc thư mục
```
├── backend/                  # Source code Backend FastAPI
│   ├── app/
│   │   ├── models.py         # SQLAlchemy Models (6 bảng chuẩn pgAdmin)
│   │   ├── routers/          # API Sessions, Orders, Users, Upload
│   │   ├── services/         # Thuật toán tổng hợp tin nhắn gửi quán
│   │   ├── database.py       # Kết nối PostgreSQL Local
│   │   ├── schemas.py        # Pydantic Schemas
│   │   ├── config.py         # Cấu hình môi trường
│   │   └── main.py           # Điểm khởi chạy FastAPI
│   ├── schema.sql            # File DDL tạo bảng cho PostgreSQL / pgAdmin 4
│   ├── test_generator.py     # Script test thuật toán ghép món
│   ├── requirements.txt      # Thư viện phụ thuộc
│   └── .env.example          # Mẫu cấu hình môi trường
├── PROJECT_STATUS.md         # Báo cáo tiến độ chi tiết của dự án
└── README.md
```

## 3. Hướng dẫn chạy Backend (Local)
1. Mở pgAdmin 4, đảm bảo database `App` đã sẵn sàng (đã chạy file `backend/schema.sql` nếu cần tạo mới).
2. Mở terminal tại thư mục `backend`:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
3. Cấu hình file `.env` từ `.env.example`:
   ```env
   DATABASE_URL=postgresql://postgres:mat_khau_cua_ban@localhost:5432/App
   ```
4. Khởi chạy server FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
5. Truy cập tài liệu API Swagger UI tại: `http://localhost:8000/docs`

## 4. Hướng dẫn chạy thử nghiệm trên Docker
1. Khởi động **Docker Desktop** trên máy.
2. **Cách 1 (Nhanh nhất trên Windows):** Click đúp vào file `start.bat` ở thư mục gốc để tự động bật hệ thống và mở trình duyệt.
   - Khi muốn tắt: Click đúp vào file `stop.bat`.
3. **Cách 2 (Bằng dòng lệnh):**
   ```bash
   docker-compose up --build -d
   ```
3. Truy cập các dịch vụ:
   - **FastAPI Swagger Docs**: http://localhost:8000/docs
   - **pgAdmin 4**: http://localhost:5050 (Email: `admin@admin.com`, Pass: `admin`)
4. Dừng hệ thống:
   ```bash
   docker-compose down
   ```
