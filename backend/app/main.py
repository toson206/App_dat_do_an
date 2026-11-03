import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from app.config import settings
from app.database import engine
from app.models import Base
from app.routers import sessions, orders, upload, users

# Đảm bảo bảng tồn tại (nếu chưa tạo) và thư mục uploads sẵn sàng
os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
try:
    Base.metadata.create_all(bind=engine)
except Exception as e:
    print(f"Lưu ý kết nối DB: {e}")

app = FastAPI(
    title="Cơm Trưa - API Đặt cơm nội bộ",
    description="Hệ thống backend kết nối trực tiếp PostgreSQL (quản lý qua pgAdmin 4). Xử lý gom đơn, tổng hợp tin nhắn gửi quán và quản lý thanh toán.",
    version="2.0.0"
)

# Cấu hình CORS để Frontend React (Vite) gọi được không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Phục vụ file tĩnh (ảnh món ăn, mã QR chuyển khoản lưu tại local)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Đăng ký các router
app.include_router(sessions.router)
app.include_router(orders.router)
app.include_router(users.router)
app.include_router(upload.router)

@app.get("/", tags=["Hệ thống"])
def root():
    return {
        "app": "Cơm Trưa API",
        "database": "PostgreSQL (pgAdmin 4)",
        "status": "Online",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
