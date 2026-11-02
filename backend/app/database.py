from supabase import create_client, Client
from app.config import settings

def get_supabase_client() -> Client:
    if not settings.SUPABASE_URL or not settings.SUPABASE_KEY:
        raise ValueError("Chưa cấu hình SUPABASE_URL hoặc SUPABASE_KEY trong file .env!")
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_KEY)

# Khởi tạo client dùng chung
try:
    supabase: Client = get_supabase_client()
except Exception as e:
    print(f"Cảnh báo Supabase: {e}")
    supabase = None
