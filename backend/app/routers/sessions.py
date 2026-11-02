import secrets
from typing import List, Dict, Any
from fastapi import APIRouter, HTTPException, Depends
from app.database import supabase
from app.schemas import SessionCreate, BatchPricingRequest
from app.services.message_generator import generate_shop_message, generate_internal_distribution_list

router = APIRouter(prefix="/api/sessions", tags=["Sessions (Quản lý Event)"])

def generate_share_code() -> str:
    """Sinh mã share ngẫu nhiên ngắn, dễ nhìn vd: com-a8x2b"""
    code = secrets.token_hex(3)
    return f"com-{code}"

@router.post("/", summary="Tạo event đặt cơm mới")
async def create_session(data: SessionCreate, creator_id: str = "00000000-0000-0000-0000-000000000000"):
    """
    Tạo event mới kèm danh sách ảnh món ăn ban đầu
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    share_code = generate_share_code()

    # 1. Tạo session
    session_payload = {
        "share_code": share_code,
        "title": data.title,
        "deadline": data.deadline.isoformat(),
        "event_note": data.event_note,
        "bank_name": data.bank_name,
        "bank_account_number": data.bank_account_number,
        "bank_account_name": data.bank_account_name,
        "qr_image_url": data.qr_image_url,
        "restaurant_id": data.restaurant_id,
        "cloned_from_session_id": data.cloned_from_session_id,
        "created_by": creator_id,
        "status": "OPEN"
    }

    res_session = supabase.table("sessions").insert(session_payload).execute()
    if not res_session.data:
        raise HTTPException(status_code=400, detail="Không thể tạo event!")

    new_session = res_session.data[0]
    session_id = new_session["id"]

    # 2. Tạo menu_items nếu có
    if data.menu_items:
        items_payload = []
        for idx, item in enumerate(data.menu_items):
            items_payload.append({
                "session_id": session_id,
                "name": item.name,
                "image_url": item.image_url,
                "price": item.price,
                "display_order": item.display_order if item.display_order else idx
            })
        supabase.table("menu_items").insert(items_payload).execute()

    return {
        "message": "Tạo event thành công!",
        "session": new_session,
        "share_url": f"/event/{share_code}"
    }

@router.get("/{share_code}", summary="Lấy thông tin chi tiết event theo mã chia sẻ")
async def get_session_by_code(share_code: str):
    """
    Đồng nghiệp mở link event sẽ load thông tin qua API này
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    # Lấy session
    res_session = supabase.table("sessions").select("*").eq("share_code", share_code).execute()
    if not res_session.data:
        raise HTTPException(status_code=404, detail="Không tìm thấy event đặt cơm này!")

    session_data = res_session.data[0]
    session_id = session_data["id"]

    # Lấy danh sách món ăn
    res_items = supabase.table("menu_items").select("*").eq("session_id", session_id).order("display_order").execute()

    # Lấy danh sách các phần cơm đã đặt kèm món và tên người đặt
    res_orders = supabase.table("orders").select(
        "id, user_id, portion_custom_name, order_note, final_price, payment_status, transferred_at, created_at, profiles(name, department), order_items(id, menu_item_id, quantity, item_note, menu_items(name))"
    ).eq("session_id", session_id).execute()

    return {
        "session": session_data,
        "menu_items": res_items.data,
        "orders": res_orders.data
    }

@router.post("/{session_id}/close", summary="Đóng đặt hàng & tự động sinh tin nhắn gửi quán")
async def close_session(session_id: int):
    """
    Người tạo bấm đóng đặt hàng:
    - Đổi status sang CLOSED
    - Tự động sinh tin nhắn gửi shop và lưu vào cột shop_message
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    # Lấy tất cả orders của session
    res_orders = supabase.table("orders").select(
        "id, user_id, portion_custom_name, order_note, profiles(name), order_items(quantity, item_note, menu_items(name))"
    ).eq("session_id", session_id).execute()

    # Chuẩn hóa dữ liệu để truyền vào thuật toán ghép tin nhắn
    formatted_orders = []
    for o in res_orders.data:
        user_name = o.get("profiles", {}).get("name") if o.get("profiles") else "Đồng nghiệp"
        items = []
        for oi in o.get("order_items", []):
            item_name = oi.get("menu_items", {}).get("name", "Món") if oi.get("menu_items") else "Món"
            items.append({
                "name": item_name,
                "quantity": oi.get("quantity", 1),
                "item_note": oi.get("item_note")
            })

        formatted_orders.append({
            "user_name": user_name,
            "portion_custom_name": o.get("portion_custom_name"),
            "order_note": o.get("order_note"),
            "items": items
        })

    # Sinh tin nhắn gửi shop & danh sách phát cơm nội bộ
    shop_message = generate_shop_message(formatted_orders)
    distribution_list = generate_internal_distribution_list(formatted_orders)

    # Cập nhật status và shop_message vào database
    supabase.table("sessions").update({
        "status": "CLOSED",
        "shop_message": shop_message
    }).eq("id", session_id).execute()

    return {
        "message": "Đã đóng đặt hàng thành công!",
        "shop_message": shop_message,
        "distribution_list": distribution_list
    }

@router.post("/{session_id}/reopen", summary="Mở lại nhận thêm đơn trễ")
async def reopen_session(session_id: int):
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    supabase.table("sessions").update({"status": "OPEN"}).eq("id", session_id).execute()
    return {"message": "Đã mở lại nhận đơn!"}

@router.post("/{session_id}/pricing", summary="Người tạo nhập giá từng phần và gửi báo giá")
async def batch_update_prices(session_id: int, payload: BatchPricingRequest):
    """
    Sau khi shop báo tổng tiền, người tạo nhập giá từng phần:
    - Cập nhật final_price cho từng order
    - Chuyển session sang trạng thái WAITING_PAYMENT để mọi người chuyển khoản
    """
    if not supabase:
        raise HTTPException(status_code=500, detail="Chưa kết nối Supabase!")

    # Cập nhật giá từng order
    for item in payload.prices:
        supabase.table("orders").update({
            "final_price": item.final_price
        }).eq("id", item.order_id).execute()

    # Cập nhật session sang WAITING_PAYMENT
    supabase.table("sessions").update({
        "status": "WAITING_PAYMENT"
    }).eq("id", session_id).execute()

    return {"message": "Đã gửi báo giá tới mọi người!"}
