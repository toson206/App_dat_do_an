# Cơm Trưa - Ứng dụng đặt cơm nội bộ

Một công cụ nội bộ gọn nhẹ thay thế việc gom order cơm qua chat nhóm và ghi tay Excel.

## 1. Kiến trúc hệ thống
- **Cơ sở dữ liệu**: PostgreSQL trên **Supabase Cloud** (tích hợp Supabase Auth, Row Level Security RLS, Triggers bảo vệ chống gian lận giá).
- **Backend**: Python (**FastAPI**) xử lý API gom đơn, tính tiền và thuật toán tổng hợp tin nhắn gửi quán cơm.
- **Frontend**: React (Vite + Tailwind CSS) tối ưu giao diện Mobile-first.

## 2. Cấu trúc thư mục
```
├── backend/                  # Source code Backend FastAPI
│   ├── app/
│   │   ├── routers/          # API Sessions, Orders
│   │   ├── services/         # Thuật toán tổng hợp tin nhắn gửi quán
│   │   ├── database.py       # Kết nối Supabase
│   │   ├── schemas.py        # Pydantic Schemas
│   │   └── main.py           # Điểm khởi chạy FastAPI
│   ├── test_generator.py     # Script test thuật toán ghép món
│   ├── requirements.txt      # Thư viện phụ thuộc
│   └── .env.example          # Mẫu cấu hình môi trường
└── README.md
```

## 3. Hướng dẫn chạy Backend (Local)
1. Mở terminal tại thư mục `backend`:
   ```bash
   cd backend
   pip install -r requirements.txt
   ```
2. Cấu hình file `.env` từ `.env.example`:
   ```env
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
3. Khởi chạy server FastAPI:
   ```bash
   uvicorn app.main:app --reload
   ```
4. Truy cập tài liệu API Swagger UI tại: `http://localhost:8000/docs`
