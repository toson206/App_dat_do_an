"""
Script chạy thử nghiệm thuật toán tổng hợp tin nhắn gửi quán cơm
Chạy bằng lệnh: python test_generator.py
"""
from app.services.message_generator import generate_shop_message, generate_internal_distribution_list

# Dữ liệu mô phỏng theo đúng ví dụ trong tài liệu thiết kế:
# - A đặt: trứng + thịt
# - B đặt: rau + giá
# - C đặt: 2 trứng + thịt luộc (ít mỡ), không cơm
sample_orders = [
    {
        "user_name": "Nguyễn Văn A",
        "portion_custom_name": None,
        "order_note": None,
        "items": [
            {"name": "Trứng", "quantity": 1, "item_note": None},
            {"name": "Thịt luộc", "quantity": 1, "item_note": None}
        ]
    },
    {
        "user_name": "Trần Thị B",
        "portion_custom_name": None,
        "order_note": None,
        "items": [
            {"name": "Rau", "quantity": 1, "item_note": None},
            {"name": "Giá", "quantity": 1, "item_note": None}
        ]
    },
    {
        "user_name": "Lê Văn C",
        "portion_custom_name": "Phần ăn trưa",
        "order_note": "không cơm",
        "items": [
            {"name": "Trứng", "quantity": 2, "item_note": None},
            {"name": "Thịt luộc", "quantity": 1, "item_note": "ít mỡ"}
        ]
    }
]

if __name__ == "__main__":
    print("=" * 60)
    print("1. KẾT QUẢ TIN NHẮN TỔNG HỢP GỬI QUÁN CƠM (BƯỚC 4):")
    print("=" * 60)
    shop_msg = generate_shop_message(sample_orders)
    print(shop_msg)

    print("\n" + "=" * 60)
    print("2. KẾT QUẢ DANH SÁCH ĐỐI CHIẾU & PHÁT CƠM NỘI BỘ:")
    print("=" * 60)
    dist_list = generate_internal_distribution_list(sample_orders)
    print(dist_list)
    print("=" * 60)
