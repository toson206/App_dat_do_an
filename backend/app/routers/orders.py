from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import Order, OrderItem, Session
from app.schemas import OrderCreate

router = APIRouter(prefix="/api/orders", tags=["Orders (Đặt món & Thanh toán)"])

@router.post("/", summary="Đặt một phần cơm mới")
def create_order(data: OrderCreate, current_user_id: int = 1, db: DBSession = Depends(get_db)):
    """
    Đặt 1 phần cơm (hỗ trợ đặt cho mình hoặc đặt hộ):
    - Kiểm tra session có đang OPEN không
    - Tạo dòng trong bảng orders
    - Tạo các dòng chi tiết trong order_items (+1, +2 món, ghi chú riêng)
    """
    # 1. Kiểm tra session
    session = db.query(Session).filter(Session.id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event đặt cơm!")
    if session.status != "OPEN":
        raise HTTPException(status_code=400, detail="Event này đã đóng nhận đơn hoặc không còn mở!")

    # 2. Tạo đơn
    order = Order(
        session_id=data.session_id,
        user_id=data.user_id if data.user_id is not None else current_user_id,
        created_by_user_id=current_user_id,
        portion_custom_name=data.portion_custom_name,
        order_note=data.order_note,
        payment_status="UNPAID"
    )
    db.add(order)
    db.flush()  # Lấy order.id

    # 3. Tạo các món trong phần
    for item in data.items:
        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.menu_item_id,
            quantity=item.quantity,
            item_note=item.item_note
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    return {"message": "Đặt phần cơm thành công!", "order_id": order.id}

@router.delete("/{order_id}", summary="Hủy phần cơm đã đặt (chỉ khi event còn OPEN)")
def cancel_order(order_id: int, db: DBSession = Depends(get_db)):
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt này!")

    if order.session.status != "OPEN":
        raise HTTPException(status_code=400, detail="Không thể hủy đơn sau khi event đã đóng đặt hàng!")

    db.delete(order)
    db.commit()
    return {"message": "Đã hủy phần cơm thành công!"}

@router.post("/{order_id}/transfer", summary="Người đặt bấm 'Đã chuyển khoản'")
def mark_transferred(order_id: int, db: DBSession = Depends(get_db)):
    """
    Người đặt bấm 'Đã chuyển khoản'
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt này!")

    order.payment_status = "TRANSFERRED"
    order.transferred_at = datetime.now()
    db.commit()

    return {"message": "Đã đánh dấu chuyển khoản thành công!"}

@router.post("/{order_id}/confirm", summary="Người tạo event bấm xác nhận đã nhận được tiền")
def confirm_payment(order_id: int, db: DBSession = Depends(get_db)):
    """
    Người tạo event duyệt xác nhận tiền đã về tài khoản
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt này!")

    order.payment_status = "CONFIRMED"
    order.confirmed_at = datetime.now()
    db.commit()

    return {"message": "Đã xác nhận thanh toán thành công!"}
