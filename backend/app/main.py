from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import sessions, orders

app = FastAPI(
    title="Cơm Trưa - API Đặt cơm nội bộ",
    description="Hệ thống backend xử lý gom đơn cơm trưa, tổng hợp tin nhắn gửi quán và quản lý thanh toán.",
    version="1.0.0"
)

# Cấu hình CORS để Frontend React (Vite) gọi được không bị chặn
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Trong môi trường dev cho phép mọi origin
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Đăng ký các router
app.include_router(sessions.router)
app.include_router(orders.router)

@app.get("/", tags=["Hệ thống"])
async def root():
    return {
        "app": "Cơm Trưa API",
        "status": "Online",
        "docs_url": "/docs"
    }

if __name__ == "__main__":
    import uvicorn
    from app.config import settings
    uvicorn.run("app.main:app", host=settings.HOST, port=settings.PORT, reload=True)
