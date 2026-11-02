from datetime import datetime
from fastapi import APIRouter, HTTPException
from app.database import supabase
from app.schemas import OrderCreate

router = APIRouter(prefix="/api/orders", tags=["Orders (Đặt món & Thanh toán)"])

@router.post("/", summary="Đặt một phần cơm mới")
async def create_order(data: OrderCreate, current_user_id: str = "00000000-0000-0000-0000-000000000000"):
    """
    Đặt 1 phần cơm (hỗ trợ đặt cho mình hoặc đặt hộ):
    - Kiểm tra session có đang OPEN không
    - Tạo dòng trong bảng orders
    - Tạo các dòng chi tiết trong order_items (+1, +2 món, ghi chú riêng)
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    # 1. Kiểm tra session
    res_session = supabase.table("sessions").select("status").eq("id", data.session_id).execute()
    if not res_session.data or res_session.data[0]["status"] != "OPEN":
        raise HTTPException(status_code=400, detail="Event này đã đóng đặt hàng hoặc không tồn tại!")

    # 2. Tạo đơn
    order_payload = {
        "session_id": data.session_id,
        "user_id": data.user_id,
        "created_by_user_id": current_user_id,
        "portion_custom_name": data.portion_custom_name,
        "order_note": data.order_note,
        "payment_status": "UNPAID"
    }

    res_order = supabase.table("orders").insert(order_payload).execute()
    if not res_order.data:
        raise HTTPException(status_code=400, detail="Lỗi khi tạo phần cơm!")

    order_id = res_order.data[0]["id"]

    # 3. Tạo các món trong phần
    items_payload = []
    for item in data.items:
        items_payload.append({
            "order_id": order_id,
            "menu_item_id": item.menu_item_id,
            "quantity": item.quantity,
            "item_note": item.item_note
        })

    if items_payload:
        supabase.table("order_items").insert(items_payload).execute()

    return {"message": "Đặt phần cơm thành công!", "order_id": order_id}

@router.delete("/{order_id}", summary="Hủy phần cơm đã đặt (chỉ khi event còn OPEN)")
async def cancel_order(order_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    # Lấy thông tin order và session
    res_order = supabase.table("orders").select("session_id, sessions(status)").eq("id", order_id).execute()
    if not res_order.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy đơn đặt này!")

    session_status = res_order.data[0].get("sessions", {}).get("status")
    if session_status != "OPEN":
        raise HTTPException(status_code=400, detail="Không thể hủy đơn sau khi event đã đóng đặt hàng!")

    supabase.table("orders").delete().eq("id", order_id).execute()
    return {"message": "Đã hủy phần cơm thành công!"}

@router.post("/{order_id}/transfer", summary="Người đặt bấm 'Đã chuyển khoản'")
async def mark_transferred(order_id: int):
    """
    Bước 12: Người đặt bấm 'Đã chuyển khoản'
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    supabase.table("orders").update({
        "payment_status": "TRANSFERRED",
        "transferred_at": datetime.now().isoformat()
    }).eq("id", order_id).execute()

    return {"message": "Đã đánh dấu chuyển khoản thành công!"}

@router.post("/{order_id}/confirm", summary="Người tạo event bấm xác nhận đã nhận được tiền")
async def confirm_payment(order_id: int):
    """
    Bước 13: Người tạo event duyệt xác nhận tiền đã về tài khoản
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    supabase.table("orders").update({
        "payment_status": "CONFIRMED",
        "confirmed_at": datetime.now().isoformat()
    }).eq("id", order_id).execute()

    return {"message": "Đã xác nhận thanh toán thành công!"}
