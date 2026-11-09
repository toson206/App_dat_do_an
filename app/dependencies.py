from typing import Optional
from fastapi import Header, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import User

def get_current_user_id(
    x_user_id: Optional[int] = Header(None, alias="X-User-Id", description="ID của nhân viên thực hiện thao tác"),
    db: DBSession = Depends(get_db)
) -> int:
    """
    Xác định danh tính người dùng qua Header 'X-User-Id'.
    Nếu client không truyền Header, hệ thống tự động fallback về User đầu tiên trong DB
    (tiện lợi cho việc test nhanh trên Swagger UI / môi trường phát triển).
    """
    if x_user_id is not None:
        user = db.query(User).filter(User.id == x_user_id).first()
        if not user:
            raise HTTPException(status_code=401, detail=f"Không tìm thấy nhân viên với ID {x_user_id}!")
        return user.id

    # Fallback cho môi trường dev / swagger test
    first_user = db.query(User).order_by(User.id.asc()).first()
    return first_user.id if first_user else 1
