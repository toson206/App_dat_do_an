from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession
from app.database import get_db
from app.models import Order, OrderItem, Session, MenuItem
from app.schemas import OrderCreate, OrderUpdate
from app.dependencies import get_current_user_id

router = APIRouter(prefix="/api/orders", tags=["Orders (Đặt món & Thanh toán)"])

@router.post("/", summary="Đặt một phần cơm mới")
def create_order(
    data: OrderCreate, 
    current_user_id: int = Depends(get_current_user_id), 
    db: DBSession = Depends(get_db)
):
    """
    Đặt 1 phần cơm (hỗ trợ đặt cho mình hoặc đặt hộ):
    - Kiểm tra session có đang OPEN không
    - Kiểm tra danh sách món không được rỗng
    - Validate từng menu_item và snapshot giá tại thời điểm đặt (price_at_order)
    """
    # 1. Kiểm tra danh sách món không rỗng
    if not data.items or len(data.items) == 0:
        raise HTTPException(status_code=400, detail="Phần cơm phải có ít nhất 1 món ăn!")

    # 2. Kiểm tra session
    session = db.query(Session).filter(Session.id == data.session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event đặt cơm!")
    if session.status != "OPEN":
        raise HTTPException(status_code=400, detail="Event này đã đóng nhận đơn hoặc không còn mở!")

    # 3. Tạo đơn
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

    # 4. Kiểm tra từng món và snapshot giá (price_at_order)
    for item in data.items:
        menu_item = db.query(MenuItem).filter(
            MenuItem.id == item.menu_item_id, 
            MenuItem.session_id == session.id
        ).first()
        if not menu_item:
            raise HTTPException(
                status_code=400, 
                detail=f"Món ăn ID {item.menu_item_id} không tồn tại hoặc không thuộc event này!"
            )

        order_item = OrderItem(
            order_id=order.id,
            menu_item_id=item.menu_item_id,
            quantity=item.quantity,
            item_note=item.item_note,
            price_at_order=menu_item.price
        )
        db.add(order_item)

    db.commit()
    db.refresh(order)

    return {"message": "Đặt phần cơm thành công!", "order_id": order.id}

@router.put("/{order_id}", summary="Chỉnh sửa phần cơm đã đặt (đổi món, số lượng, ghi chú)")
def update_order(
    order_id: int,
    data: OrderUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """
    Sửa phần cơm đã đặt:
    - Chỉ được sửa khi event còn đang mở (OPEN)
    - Chỉ người tạo đơn, người thụ hưởng hoặc Host tạo event mới có quyền sửa
    - Hỗ trợ đổi món, số lượng món, tên phần ăn, và ghi chú ăn uống
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy phần cơm này!")

    if order.session.status != "OPEN":
        raise HTTPException(
            status_code=400, 
            detail="Không thể sửa đơn sau khi event đã đóng đặt hàng hoặc đang chờ thanh toán!"
        )

    # Kiểm tra quyền: Người tạo đơn, người thụ hưởng, hoặc Host của session
    is_owner = (order.created_by_user_id == current_user_id) or (order.user_id == current_user_id)
    is_host = (order.session.created_by == current_user_id)
    if not is_owner and not is_host:
        raise HTTPException(status_code=403, detail="Bạn không có quyền chỉnh sửa phần cơm này!")

    # Cập nhật thông tin cơ bản nếu có truyền lên
    if data.user_id is not None:
        order.user_id = data.user_id
    if data.portion_custom_name is not None:
        order.portion_custom_name = data.portion_custom_name
    if data.order_note is not None:
        order.order_note = data.order_note

    # Cập nhật lại danh sách món ăn nếu client truyền items
    if data.items is not None:
        if len(data.items) == 0:
            raise HTTPException(status_code=400, detail="Phần cơm phải có ít nhất 1 món ăn!")

        # Validate toàn bộ món ăn mới trước khi xóa món cũ
        for item in data.items:
            menu_item = db.query(MenuItem).filter(
                MenuItem.id == item.menu_item_id,
                MenuItem.session_id == order.session_id
            ).first()
            if not menu_item:
                raise HTTPException(
                    status_code=400,
                    detail=f"Món ăn ID {item.menu_item_id} không tồn tại hoặc không thuộc event này!"
                )

        # Xóa các món cũ của phần cơm này
        db.query(OrderItem).filter(OrderItem.order_id == order.id).delete()

        # Thêm các món mới vào
        for item in data.items:
            menu_item = db.query(MenuItem).filter(
                MenuItem.id == item.menu_item_id,
                MenuItem.session_id == order.session_id
            ).first()
            new_order_item = OrderItem(
                order_id=order.id,
                menu_item_id=item.menu_item_id,
                quantity=item.quantity,
                item_note=item.item_note,
                price_at_order=menu_item.price
            )
            db.add(new_order_item)

    db.commit()
    db.refresh(order)
    return {"message": "Cập nhật phần cơm thành công!", "order_id": order.id}

@router.delete("/{order_id}", summary="Hủy phần cơm đã đặt (chỉ khi event còn OPEN)")
def cancel_order(
    order_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: DBSession = Depends(get_db)
):
    """
    Hủy phần cơm:
    - Chỉ được hủy khi event còn OPEN
    - Chỉ người đặt, người đặt hộ hoặc Host tạo event mới có quyền hủy
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy phần cơm này!")

    if order.session.status != "OPEN":
        raise HTTPException(status_code=400, detail="Không thể hủy đơn sau khi event đã đóng đặt hàng!")

    # Kiểm tra quyền: Người tạo đơn, người thụ hưởng, hoặc Host của session
    is_owner = (order.created_by_user_id == current_user_id) or (order.user_id == current_user_id)
    is_host = (order.session.created_by == current_user_id)
    if not is_owner and not is_host:
        raise HTTPException(status_code=403, detail="Bạn không có quyền hủy phần cơm này!")

    db.delete(order)
    db.commit()
    return {"message": "Đã hủy phần cơm thành công!"}

@router.post("/{order_id}/transfer", summary="Người đặt bấm 'Đã chuyển khoản' (Toggle bật/tắt)")
def mark_transferred(
    order_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: DBSession = Depends(get_db)
):
    """
    Người đặt bấm 'Đã chuyển khoản':
    - Hỗ trợ bấm lại để hủy (toggle UNPAID <-> TRANSFERRED) nếu bấm nhầm
    - Không được đổi nếu Host đã xác nhận CONFIRMED
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt này!")

    is_owner = (order.created_by_user_id == current_user_id) or (order.user_id == current_user_id)
    is_host = (order.session.created_by == current_user_id)
    if not is_owner and not is_host:
        raise HTTPException(status_code=403, detail="Bạn không có quyền cập nhật thanh toán cho đơn này!")

    if order.payment_status == "CONFIRMED":
        raise HTTPException(
            status_code=400, 
            detail="Đơn đặt đã được Host xác nhận thanh toán thành công, không thể thay đổi!"
        )

    # Toggle trạng thái
    if order.payment_status == "TRANSFERRED":
        order.payment_status = "UNPAID"
        order.transferred_at = None
        db.commit()
        return {
            "message": "Đã hủy đánh dấu chuyển khoản (quay lại trạng thái Chưa chuyển)!",
            "payment_status": "UNPAID"
        }
    else:
        order.payment_status = "TRANSFERRED"
        order.transferred_at = datetime.now()
        db.commit()
        return {
            "message": "Đã đánh dấu chuyển khoản thành công!",
            "payment_status": "TRANSFERRED"
        }

@router.post("/{order_id}/confirm", summary="Host bấm xác nhận đã nhận được tiền")
def confirm_payment(
    order_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: DBSession = Depends(get_db)
):
    """
    Host duyệt xác nhận tiền đã về tài khoản:
    - Chỉ Host tạo event mới có quyền duyệt
    - Tự động chuyển session sang COMPLETED khi tất cả các phần cơm đều đã CONFIRMED
    """
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt này!")

    # Chỉ Host mới có quyền xác nhận
    if order.session.created_by is not None and order.session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo event (Host) mới có quyền xác nhận đã nhận tiền!")

    order.payment_status = "CONFIRMED"
    order.confirmed_at = datetime.now()

    # Kiểm tra xem toàn bộ các đơn trong event đã hoàn tất thanh toán chưa
    all_orders = db.query(Order).filter(Order.session_id == order.session_id).all()
    all_confirmed = len(all_orders) > 0 and all(o.payment_status == "CONFIRMED" for o in all_orders)
    
    session_completed = False
    if all_confirmed and order.session.status in ["WAITING_PAYMENT", "CLOSED"]:
        order.session.status = "COMPLETED"
        session_completed = True

    db.commit()

    return {
        "message": "Đã xác nhận thanh toán thành công!",
        "order_payment_status": "CONFIRMED",
        "session_status": order.session.status,
        "is_all_completed": session_completed
    }
