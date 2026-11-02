from typing import List, Dict, Any

def format_portion_content(items: List[Dict[str, Any]], order_note: str = None) -> str:
    """
    Format nội dung các món trong 1 phần cơm theo quy tắc:
    - Số lượng 1 chỉ ghi tên (vd: trứng)
    - Số lượng >= 2 ghi kèm số (vd: 2 trứng)
    - Ghi chú món nằm trong ngoặc: trứng (ốp la)
    - Các món nối với nhau bằng ' + '
    - Ghi chú của cả phần nằm sau dấu phẩy: ', không cơm'
    """
    item_strings = []
    for item in items:
        qty = item.get("quantity", 1)
        name = item.get("name", "").strip()
        item_note = (item.get("item_note") or "").strip()

        # Format món
        if qty > 1:
            part = f"{qty} {name}"
        else:
            part = name

        # Thêm ghi chú riêng cho món nếu có
        if item_note:
            part += f" ({item_note})"

        item_strings.append(part)

    # Nối các món bằng ' + '
    dish_summary = " + ".join(item_strings)

    # Thêm ghi chú chung của cả phần nếu có
    if order_note and order_note.strip():
        dish_summary += f", {order_note.strip()}"

    return dish_summary

def generate_shop_message(orders: List[Dict[str, Any]]) -> str:
    """
    Tạo tin nhắn tổng hợp gửi shop:
    Cho em đặt 3 phần:
    1 phần trứng + thịt
    1 phần rau + giá
    1 phần 2 trứng + thịt luộc (ít mỡ), không cơm
    """
    total_portions = len(orders)
    if total_portions == 0:
        return "Chưa có phần cơm nào được đặt."

    lines = [f"Cho em đặt {total_portions} phần:"]
    for order in orders:
        portion_text = format_portion_content(order.get("items", []), order.get("order_note"))
        lines.append(f"1 phần {portion_text}")

    return "\n".join(lines)

def generate_internal_distribution_list(orders: List[Dict[str, Any]]) -> str:
    """
    Tạo danh sách có tên người để đối chiếu và phát cơm nội bộ:
    A: trứng + thịt
    B: rau + giá
    C (Đặt hộ Lan): 2 trứng + thịt luộc (ít mỡ), không cơm
    """
    lines = ["DANH SÁCH ĐỐI CHIẾU & PHÁT CƠM:"]
    for idx, order in enumerate(orders, 1):
        user_name = order.get("user_name") or "Đồng nghiệp"
        custom_name = order.get("portion_custom_name")
        label = f"{user_name} ({custom_name})" if custom_name else user_name

        portion_text = format_portion_content(order.get("items", []), order.get("order_note"))
        lines.append(f"{idx}. {label}: {portion_text}")

    return "\n".join(lines)
