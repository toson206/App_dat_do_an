import secrets
from typing import List, Dict, Any, Optional
from datetime import datetime, date
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session as DBSession, joinedload
from app.database import get_db
from app.models import Session, MenuItem, Order, OrderItem, User, Restaurant
from app.schemas import (
    SessionCreate, SessionUpdate, SessionCloneRequest, BatchPricingRequest, 
    SessionResponse, SessionCandidateResponse,
    MenuItemCreate, MenuItemUpdate, MenuItemResponse
)
from app.services.message_generator import generate_shop_message, generate_internal_distribution_list
from app.dependencies import get_current_user_id

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

@router.get("/clone-candidates", response_model=List[SessionCandidateResponse], summary="Lấy danh sách các phiên mẫu để nhân bản (Clone)")
def get_clone_candidates(
    limit: int = 20,
    db: DBSession = Depends(get_db)
):
    """
    Gợi ý các phiên đặt cơm gần đây để Host bấm 'Dùng lại' / Clone:
    - Trả kèm tên quán, người tạo, số món ăn, số lượt đặt
    """
    sessions = (
        db.query(Session)
        .options(
            joinedload(Session.restaurant),
            joinedload(Session.creator),
            joinedload(Session.menu_items),
            joinedload(Session.orders)
        )
        .order_by(Session.id.desc())
        .limit(limit)
        .all()
    )

    results = []
    for s in sessions:
        results.append(SessionCandidateResponse(
            id=s.id,
            share_code=s.share_code,
            title=s.title,
            restaurant_id=s.restaurant_id,
            restaurant_name=s.restaurant.name if s.restaurant else None,
            created_by=s.created_by,
            creator_name=s.creator.name if s.creator else None,
            session_date=s.session_date,
            menu_items_count=len(s.menu_items) if s.menu_items else 0,
            total_orders_count=len(s.orders) if s.orders else 0,
            status=s.status,
            created_at=s.created_at
        ))
    return results

@router.post("/", summary="Tạo event đặt cơm mới")
def create_session(
    data: SessionCreate, 
    current_user_id: int = Depends(get_current_user_id), 
    db: DBSession = Depends(get_db)
):
    """
    Tạo event mới kèm danh sách ảnh món ăn ban đầu
    """
    # Tránh trùng lặp share_code
    share_code = generate_share_code()
    while db.query(Session).filter(Session.share_code == share_code).first():
        share_code = generate_share_code()

    # 1. Kiểm tra session gốc nếu có cloned_from_session_id
    source_session = None
    if data.cloned_from_session_id:
        source_session = db.query(Session).filter(Session.id == data.cloned_from_session_id).first()
        if not source_session:
            raise HTTPException(
                status_code=404, 
                detail=f"Không tìm thấy phiên đặt cơm gốc (ID: {data.cloned_from_session_id}) để nhân bản!"
            )

    # 2. Xác định Host và lấy thông tin ngân hàng/QR lưu sẵn nếu chưa nhập
    creator_id = data.created_by if data.created_by is not None else current_user_id
    creator = db.query(User).filter(User.id == creator_id).first()

    bank_name = (
        data.bank_name 
        or (creator.bank_name if creator and creator.bank_name else None) 
        or (source_session.bank_name if source_session else None)
    )
    bank_account_number = (
        data.bank_account_number 
        or (creator.bank_account_number if creator and creator.bank_account_number else None) 
        or (source_session.bank_account_number if source_session else None)
    )
    bank_account_name = (
        data.bank_account_name 
        or (creator.bank_account_name if creator and creator.bank_account_name else None) 
        or (source_session.bank_account_name if source_session else None)
    )
    qr_image_url = (
        data.qr_image_url 
        or (creator.qr_image_url if creator and creator.qr_image_url else None) 
        or (source_session.qr_image_url if source_session else None)
    )

    # Kế thừa restaurant_id, event_note, title từ phiên gốc nếu client chưa truyền
    restaurant_id = data.restaurant_id if data.restaurant_id is not None else (source_session.restaurant_id if source_session else None)
    event_note = data.event_note if data.event_note is not None else (source_session.event_note if source_session else None)
    title = data.title
    if (not title or title == "Cơm trưa văn phòng") and source_session and source_session.title:
        title = source_session.title

    # Lưu ngược lại vào hồ sơ Host nếu Host nhập thông tin mới
    if creator:
        if data.bank_name: creator.bank_name = data.bank_name
        if data.bank_account_number: creator.bank_account_number = data.bank_account_number
        if data.bank_account_name: creator.bank_account_name = data.bank_account_name
        if data.qr_image_url: creator.qr_image_url = data.qr_image_url

    session = Session(
        share_code=share_code,
        title=title,
        deadline=data.deadline,
        event_note=event_note,
        pricing_note=data.pricing_note,
        bank_name=bank_name,
        bank_account_number=bank_account_number,
        bank_account_name=bank_account_name,
        qr_image_url=qr_image_url,
        restaurant_id=restaurant_id,
        created_by=creator_id,
        cloned_from_session_id=source_session.id if source_session else None,
        status="OPEN"
    )
    db.add(session)
    db.flush()  # Lấy session.id

    # 3. Tạo menu_items: nếu client truyền thì dùng, nếu không truyền mà có source_session thì nhân bản menu từ source
    if data.menu_items and len(data.menu_items) > 0:
        for idx, item in enumerate(data.menu_items):
            menu_item = MenuItem(
                session_id=session.id,
                name=item.name,
                image_url=item.image_url,
                price=item.price,
                display_order=item.display_order if item.display_order is not None else idx
            )
            db.add(menu_item)
    elif source_session and source_session.menu_items:
        for idx, item in enumerate(source_session.menu_items):
            menu_item = MenuItem(
                session_id=session.id,
                name=item.name,
                image_url=item.image_url,
                price=item.price,
                display_order=item.display_order if item.display_order is not None else idx
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
            "created_by": session.created_by,
            "cloned_from_session_id": session.cloned_from_session_id,
            "cloned_from_title": session.cloned_from_title,
            "deadline": session.deadline.isoformat() if session.deadline else None,
        },
        "share_url": f"/event/{share_code}"
    }

@router.post("/{session_id}/clone", summary="1-Click nhân bản phiên đặt cơm cũ sang phiên mới")
def clone_session(
    session_id: int,
    data: SessionCloneRequest,
    current_user_id: int = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """
    Nhân bản một event đặt cơm cũ (ví dụ cơm trưa hôm qua, quán quen):
    - Sao chép toàn bộ danh sách món ăn (menu_items)
    - Kế thừa restaurant_id, thông tin ngân hàng, qr_image_url
    - Tạo share_code mới và hạn chót mới (deadline)
    - Đặt trạng thái ban đầu là OPEN
    """
    source_session = db.query(Session).filter(Session.id == session_id).first()
    if not source_session:
        raise HTTPException(status_code=404, detail="Không tìm thấy phiên đặt cơm gốc để nhân bản!")

    share_code = generate_share_code()
    while db.query(Session).filter(Session.share_code == share_code).first():
        share_code = generate_share_code()

    # Lấy thông tin user hiện tại (Host mới)
    host = db.query(User).filter(User.id == current_user_id).first()
    bank_name = (host.bank_name if host and host.bank_name else None) or source_session.bank_name
    bank_account_number = (host.bank_account_number if host and host.bank_account_number else None) or source_session.bank_account_number
    bank_account_name = (host.bank_account_name if host and host.bank_account_name else None) or source_session.bank_account_name
    qr_image_url = (host.qr_image_url if host and host.qr_image_url else None) or source_session.qr_image_url

    new_session = Session(
        share_code=share_code,
        title=data.title or source_session.title or "Cơm trưa văn phòng",
        deadline=data.deadline,
        event_note=data.event_note or source_session.event_note,
        bank_name=bank_name,
        bank_account_number=bank_account_number,
        bank_account_name=bank_account_name,
        qr_image_url=qr_image_url,
        restaurant_id=source_session.restaurant_id,
        created_by=current_user_id,
        cloned_from_session_id=source_session.id,
        status="OPEN"
    )
    db.add(new_session)
    db.flush()

    cloned_menu_count = 0
    if data.include_menu and source_session.menu_items:
        for idx, item in enumerate(source_session.menu_items):
            menu_item = MenuItem(
                session_id=new_session.id,
                name=item.name,
                image_url=item.image_url,
                price=item.price,
                display_order=item.display_order if item.display_order is not None else idx
            )
            db.add(menu_item)
            cloned_menu_count += 1

    db.commit()
    db.refresh(new_session)

    return {
        "message": f"Nhân bản event thành công ({cloned_menu_count} món ăn)!",
        "session": {
            "id": new_session.id,
            "share_code": new_session.share_code,
            "title": new_session.title,
            "status": new_session.status,
            "created_by": new_session.created_by,
            "cloned_from_session_id": new_session.cloned_from_session_id,
            "cloned_from_title": new_session.cloned_from_title,
            "deadline": new_session.deadline.isoformat() if new_session.deadline else None,
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
                "item_note": it.item_note,
                "price_at_order": float(it.price_at_order) if it.price_at_order is not None else None
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
            "cloned_from_session_id": session.cloned_from_session_id,
            "cloned_from_title": session.cloned_from_title,
            "session_date": str(session.session_date) if session.session_date else None,
            "deadline": session.deadline,
            "status": session.status,
            "event_note": session.event_note,
            "pricing_note": session.pricing_note,
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

@router.put("/{session_id}", response_model=SessionResponse, summary="Chỉnh sửa thông tin event (Host sửa giờ chót, tiêu đề, STK)")
def update_session(
    session_id: int,
    data: SessionUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """
    Host sửa thông tin event:
    - Chỉ Host tạo event mới có quyền sửa
    - Không thể sửa khi event đã hoàn tất thanh toán (COMPLETED)
    - Hỗ trợ đổi tiêu đề, dời deadline, ghi chú, STK/QR nhận tiền, quán ăn
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")

    if session.created_by is not None and session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo event (Host) mới có quyền sửa thông tin!")

    if session.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Không thể chỉnh sửa event đã hoàn tất thanh toán!")

    if data.title is not None:
        session.title = data.title.strip()
    if data.deadline is not None:
        session.deadline = data.deadline
    if data.event_note is not None:
        session.event_note = data.event_note
    if data.pricing_note is not None:
        session.pricing_note = data.pricing_note
    if data.bank_name is not None:
        session.bank_name = data.bank_name
    if data.bank_account_number is not None:
        session.bank_account_number = data.bank_account_number
    if data.bank_account_name is not None:
        session.bank_account_name = data.bank_account_name
    if data.qr_image_url is not None:
        session.qr_image_url = data.qr_image_url
    if data.restaurant_id is not None:
        restaurant = db.query(Restaurant).filter(Restaurant.id == data.restaurant_id).first()
        if not restaurant:
            raise HTTPException(status_code=400, detail="Quán ăn không tồn tại!")
        session.restaurant_id = data.restaurant_id

    db.commit()
    db.refresh(session)
    return session

@router.delete("/{session_id}", summary="Hủy và xóa vĩnh viễn event (Host xóa event tạo nhầm)")
def delete_session(
    session_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """
    Host xóa event:
    - Chỉ Host tạo event mới có quyền xóa
    - Không thể xóa khi event đã hoàn tất (COMPLETED)
    - Xóa toàn bộ menu_items và các order liên quan tự động qua cascade
    - Gỡ liên kết cloned_from ở các phiên nhân bản con để bảo toàn tính toàn vẹn
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")

    if session.created_by is not None and session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo event (Host) mới có quyền xóa event này!")

    if session.status == "COMPLETED":
        raise HTTPException(status_code=400, detail="Không thể xóa event đã hoàn tất thanh toán!")

    # Gỡ liên kết các phiên clone từ phiên này
    db.query(Session).filter(Session.cloned_from_session_id == session_id).update({Session.cloned_from_session_id: None})

    db.delete(session)
    db.commit()
    return {"message": f"Đã xóa vĩnh viễn event '{session.title}' thành công!"}

@router.post("/{session_id}/close", summary="Đóng đặt hàng & tự động sinh tin nhắn gửi quán")
def close_session(
    session_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: DBSession = Depends(get_db)
):
    """
    Host bấm đóng đặt hàng:
    - Kiểm tra quyền: Chỉ Host (người tạo event) mới được đóng
    - Đổi status sang CLOSED
    - Tự động sinh tin nhắn gửi shop và lưu vào cột shop_message
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")

    # Chỉ Host mới có quyền đóng đặt hàng
    if session.created_by is not None and session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo event (Host) mới có quyền đóng đặt hàng!")

    if session.status != "OPEN":
        raise HTTPException(
            status_code=400, 
            detail=f"Chỉ có thể đóng khi event đang mở nhận đơn (OPEN), trạng thái hiện tại là '{session.status}'!"
        )

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
def reopen_session(
    session_id: int, 
    current_user_id: int = Depends(get_current_user_id), 
    db: DBSession = Depends(get_db)
):
    """
    Host mở lại nhận đơn trễ:
    - Chỉ Host mới được mở lại
    - Chỉ mở lại được khi event đang CLOSED (chưa báo giá/chưa thanh toán)
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")

    if session.created_by is not None and session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo event (Host) mới có quyền mở lại nhận đơn!")

    if session.status != "CLOSED":
        raise HTTPException(
            status_code=400, 
            detail="Chỉ có thể mở lại khi event đang ở trạng thái 'Đã đóng đặt hàng' (CLOSED) và chưa gửi báo giá thanh toán!"
        )

    session.status = "OPEN"
    db.commit()
    return {"message": "Đã mở lại nhận đơn!"}

@router.post("/{session_id}/pricing", summary="Host nhập giá từng phần và gửi báo giá")
def batch_update_prices(
    session_id: int, 
    payload: BatchPricingRequest, 
    current_user_id: int = Depends(get_current_user_id), 
    db: DBSession = Depends(get_db)
):
    """
    Sau khi shop báo tổng tiền, Host nhập giá từng phần:
    - Chỉ Host mới có quyền nhập giá
    - Chỉ nhập giá được sau khi đã đóng đặt hàng (CLOSED hoặc WAITING_PAYMENT)
    - Cập nhật final_price cho từng order (validate >= 0)
    - Lưu pricing_note của Host (voucher, phí ship...)
    - Chuyển session sang WAITING_PAYMENT để mọi người chuyển khoản
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")

    if session.created_by is not None and session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ người tạo event (Host) mới có quyền nhập giá và gửi báo giá!")

    if session.status not in ["CLOSED", "WAITING_PAYMENT"]:
        raise HTTPException(
            status_code=400, 
            detail="Chỉ có thể nhập giá sau khi đã đóng đặt hàng (CLOSED)!"
        )

    # Cập nhật giá từng order
    for item in payload.prices:
        if item.final_price < 0:
            raise HTTPException(status_code=400, detail="Giá tiền phần ăn không được là số âm!")
        order = db.query(Order).filter(Order.id == item.order_id, Order.session_id == session_id).first()
        if order:
            order.final_price = item.final_price

    # Lưu ghi chú tính tiền của Host
    if payload.pricing_note:
        session.pricing_note = payload.pricing_note

    # Cập nhật session sang WAITING_PAYMENT
    session.status = "WAITING_PAYMENT"
    db.commit()

    return {"message": "Đã gửi báo giá tới mọi người!", "session_status": session.status}

@router.post("/{session_id}/menu-items", response_model=MenuItemResponse, summary="Thêm món ăn mới vào event")
def add_menu_item(
    session_id: int,
    data: MenuItemCreate,
    current_user_id: int = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """
    Host bổ sung thêm món ăn mới vào menu khi event đang mở
    """
    session = db.query(Session).filter(Session.id == session_id).first()
    if not session:
        raise HTTPException(status_code=404, detail="Không tìm thấy event!")
    if session.created_by is not None and session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ Host mới có quyền thêm món vào menu!")
    if session.status != "OPEN":
        raise HTTPException(status_code=400, detail="Chỉ có thể thêm món khi event đang mở nhận đơn (OPEN)!")

    item = MenuItem(
        session_id=session_id,
        name=data.name.strip(),
        image_url=data.image_url,
        price=data.price,
        display_order=data.display_order
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item

@router.put("/menu-items/{item_id}", response_model=MenuItemResponse, summary="Sửa thông tin món ăn")
def update_menu_item(
    item_id: int,
    data: MenuItemUpdate,
    current_user_id: int = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """
    Host sửa tên, giá, ảnh hoặc thứ tự hiển thị của món ăn
    """
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy món ăn!")
    if item.session.created_by is not None and item.session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ Host mới có quyền sửa món ăn!")

    if data.name is not None:
        item.name = data.name.strip()
    if data.image_url is not None:
        item.image_url = data.image_url
    if data.price is not None:
        item.price = data.price
    if data.display_order is not None:
        item.display_order = data.display_order

    db.commit()
    db.refresh(item)
    return item

@router.delete("/menu-items/{item_id}", summary="Xóa món ăn khỏi event")
def delete_menu_item(
    item_id: int,
    current_user_id: int = Depends(get_current_user_id),
    db: DBSession = Depends(get_db)
):
    """
    Host xóa một món ăn khỏi menu (chỉ xóa được khi event còn OPEN)
    """
    item = db.query(MenuItem).filter(MenuItem.id == item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Không tìm thấy món ăn!")
    if item.session.created_by is not None and item.session.created_by != current_user_id:
        raise HTTPException(status_code=403, detail="Chỉ Host mới có quyền xóa món ăn!")
    if item.session.status != "OPEN":
        raise HTTPException(status_code=400, detail="Không thể xóa món khi event đã đóng đặt hàng!")

    db.delete(item)
    db.commit()
    return {"message": f"Đã xóa món '{item.name}' thành công!"}
