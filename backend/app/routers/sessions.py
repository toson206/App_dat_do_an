import secrets
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession, joinedload
from app.database import get_db
from app.models import Session, MenuItem, Order, OrderItem, User
from app.schemas import SessionCreate, BatchPricingRequest, SessionResponse
from app.services.message_generator import generate_shop_message, generate_internal_distribution_list

router = APIRouter(prefix="/api/sessions", tags=["Sessions (Quản lý Event)"])

def generate_share_code() -> str:
    """Sinh mã share ngẫu nhiên ngắn, dễ nhìn vd: com-a8x2b"""
    code = secrets.token_hex(3)
    return f"com-{code}"

@router.get("/today", response_model=List[SessionResponse], summary="Lấy danh sách event hôm nay")
def get_today_sessions(db: DBSession = Depends(get_db)):
    """
    Dành cho Màn 1 (Trang chủ Hôm nay): Hiển thị các event đang mở hoặc diễn ra hôm nay
    """
    sessions = db.query(Session).order_by(Session.id.desc()).limit(20).all()
    return sessions

@router.post("/", summary="Tạo event đặt cơm mới")
def create_session(data: SessionCreate, db: DBSession = Depends(get_db)):
    """
    Tạo event mới kèm danh sách ảnh món ăn ban đầu
    """
    share_code = generate_share_code()

    # 1. Tạo session
    session = Session(
        share_code=share_code,
        title=data.title,
        deadline=data.deadline,
        event_note=data.event_note,
        bank_name=data.bank_name,
        bank_account_number=data.bank_account_number,
        bank_account_name=data.bank_account_name,
        qr_image_url=data.qr_image_url,
        restaurant_id=data.restaurant_id,
        created_by=data.created_by,
        cloned_from_session_id=data.cloned_from_session_id,
        status="OPEN"
    )
    db.add(session)
    db.flush()  # Lấy session.id

    # 2. Tạo menu_items nếu có
    if data.menu_items:
        for idx, item in enumerate(data.menu_items):
            menu_item = MenuItem(
                session_id=session.id,
                name=item.name,
                image_url=item.image_url,
                price=item.price,
                display_order=item.display_order if item.display_order else idx
            )
            db.add(menu_item)

    db.commit()
    db.refresh(session)

    return {
        "message": "Tạo event thành công!",
        "session": {
            "id": session.id,
            "share_code": session.share_code,
            "title": session.title,
            "status": session.status,
            "deadline": session.deadline.isoformat() if session.deadline else None,
        },
        "share_url": f"/event/{share_code}"
    }

@router.get("/{share_code}", summary="Lấy thông tin chi tiết event theo mã chia sẻ")
def get_session_by_code(share_code: str, db: DBSession = Depends(get_db)):
    """
    Đồng nghiệp mở link event sẽ load thông tin qua API này
    """
    session = db.query(Session).filter(Session.share_code == share_code).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event đặt cơm này!")

    # Lấy danh sách món ăn
    menu_items = db.query(MenuItem).filter(MenuItem.session_id == session.id).order_by(MenuItem.display_order).all()

    # Lấy danh sách các phần cơm đã đặt
    orders = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.items).joinedload(OrderItem.menu_item)
        )
        .filter(Order.session_id == session.id)
        .order_by(Order.id.asc())
        .all()
    )

    formatted_orders = []
    for o in orders:
        items_data = []
        for it in o.items:
            items_data.append({
                "id": it.id,
                "menu_item_id": it.menu_item_id,
                "menu_item_name": it.menu_item.name if it.menu_item else "Món",
                "quantity": it.quantity,
                "item_note": it.item_note
            })

        formatted_orders.append({
            "id": o.id,
            "session_id": o.session_id,
            "user_id": o.user_id,
            "user_name": o.user.name if o.user else "Đồng nghiệp",
            "department": o.user.department if o.user else None,
            "created_by_user_id": o.created_by_user_id,
            "portion_custom_name": o.portion_custom_name,
            "order_note": o.order_note,
            "final_price": float(o.final_price) if o.final_price is not None else None,
            "payment_status": o.payment_status,
            "transferred_at": o.transferred_at,
            "confirmed_at": o.confirmed_at,
            "created_at": o.created_at,
            "items": items_data
        })

    return {
        "session": {
            "id": session.id,
            "share_code": session.share_code,
            "title": session.title,
            "restaurant_id": session.restaurant_id,
            "created_by": session.created_by,
            "session_date": str(session.session_date) if session.session_date else None,
            "deadline": session.deadline,
            "status": session.status,
            "event_note": session.event_note,
            "bank_name": session.bank_name,
            "bank_account_number": session.bank_account_number,
            "bank_account_name": session.bank_account_name,
            "qr_image_url": session.qr_image_url,
            "shop_message": session.shop_message,
            "created_at": session.created_at
        },
        "menu_items": [
            {
                "id": m.id,
                "session_id": m.session_id,
                "name": m.name,
                "image_url": m.image_url,
                "price": float(m.price) if m.price is not None else None,
                "display_order": m.display_order,
                "created_at": m.created_at
            }
            for m in menu_items
        ],
        "orders": formatted_orders
    }

@router.post("/{session_id}/close", summary="Đóng đặt hàng & tự động sinh tin nhắn gửi quán")
def close_session(session_id: int, db: DBSession = Depends(get_db)):
    """
    Người tạo bấm đóng đặt hàng:
    - Đổi status sang CLOSED
    - Tự động sinh tin nhắn gửi shop và lưu vào cột shop_message
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")

    orders = (
        db.query(Order)
        .options(
            joinedload(Order.user),
            joinedload(Order.items).joinedload(OrderItem.menu_item)
        )
        .filter(Order.session_id == session_id)
        .all()
    )

    # Chuẩn hóa dữ liệu để truyền vào thuật toán ghép tin nhắn
    formatted_orders = []
    for o in orders:
        user_name = o.user.name if o.user else "Đồng nghiệp"
        items = []
        for oi in o.items:
            item_name = oi.menu_item.name if oi.menu_item else "Món"
            items.append({
                "name": item_name,
                "quantity": oi.quantity,
                "item_note": oi.item_note
            })

        formatted_orders.append({
            "user_name": user_name,
            "portion_custom_name": o.portion_custom_name,
            "order_note": o.order_note,
            "items": items
        })

    # Sinh tin nhắn gửi shop & danh sách phát cơm nội bộ
    shop_message = generate_shop_message(formatted_orders)
    distribution_list = generate_internal_distribution_list(formatted_orders)

    # Cập nhật status và shop_message vào database
    session.status = "CLOSED"
    session.shop_message = shop_message
    db.commit()

    return {
        "message": "Đã đóng đặt hàng thành công!",
        "shop_message": shop_message,
        "distribution_list": distribution_list
    }

@router.post("/{session_id}/reopen", summary="Mở lại nhận thêm đơn trễ")
def reopen_session(session_id: int, db: DBSession = Depends(get_db)):
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")

    session.status = "OPEN"
    db.commit()
    return {"message": "Đã mở lại nhận đơn!"}

@router.post("/{session_id}/pricing", summary="Người tạo nhập giá từng phần và gửi báo giá")
def batch_update_prices(session_id: int, payload: BatchPricingRequest, db: DBSession = Depends(get_db)):
    """
    Sau khi shop báo tổng tiền, người tạo nhập giá từng phần:
    - Cập nhật final_price cho từng order
    - Chuyển session sang trạng thái WAITING_PAYMENT để mọi người chuyển khoản
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")

    # Cập nhật giá từng order
    for item in payload.prices:
        order = db.query(Order).filter(Order.id == item.order_id, Order.session_id == session_id).first()
        if order:
            order.final_price = item.final_price

    # Cập nhật session sang WAITING_PAYMENT
    session.status = "WAITING_PAYMENT"
    db.commit()

    return {"message": "Đã gửi báo giá tới mọi người!"}
