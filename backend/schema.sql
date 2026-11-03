-- ====================================================================
-- SCHEMA DATABASE DỰ ÁN: CƠM TRƯA (POSTGRESQL / PGADMIN 4)
-- Database name: App
-- ====================================================================

-- 1. BẢNG USERS (Hồ sơ nhân viên)
CREATE TABLE IF NOT EXISTS users (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255),
    department VARCHAR(100),
    favorite_food TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 2. BẢNG RESTAURANTS (Danh bạ quán quen)
CREATE TABLE IF NOT EXISTS restaurants (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    name VARCHAR(150) NOT NULL,
    phone VARCHAR(20),
    address TEXT,
    menu_url TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 3. BẢNG SESSIONS (Sự kiện đặt cơm hàng ngày)
CREATE TABLE IF NOT EXISTS sessions (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    share_code VARCHAR(32) UNIQUE NOT NULL,
    title VARCHAR(200) DEFAULT 'Cơm trưa văn phòng',
    restaurant_id BIGINT REFERENCES restaurants(id) ON DELETE SET NULL,
    created_by BIGINT REFERENCES users(id) ON DELETE SET NULL,
    cloned_from_session_id BIGINT REFERENCES sessions(id) ON DELETE SET NULL,
    session_date DATE DEFAULT CURRENT_DATE,
    deadline TIMESTAMP WITH TIME ZONE NOT NULL,
    status VARCHAR(30) DEFAULT 'OPEN', -- OPEN, CLOSED, WAITING_PAYMENT, COMPLETED
    event_note TEXT,
    bank_name VARCHAR(100),
    bank_account_number VARCHAR(50),
    bank_account_name VARCHAR(150),
    qr_image_url TEXT,
    shop_message TEXT,
    sent_to_shop_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 4. BẢNG MENU_ITEMS (Album danh sách món ăn của event)
CREATE TABLE IF NOT EXISTS menu_items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    name VARCHAR(150) NOT NULL,
    image_url TEXT,
    price NUMERIC(12, 2),
    display_order INTEGER DEFAULT 0,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 5. BẢNG ORDERS (Mỗi dòng là 1 suất cơm)
CREATE TABLE IF NOT EXISTS orders (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    session_id BIGINT NOT NULL REFERENCES sessions(id) ON DELETE CASCADE,
    user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    created_by_user_id BIGINT REFERENCES users(id) ON DELETE SET NULL,
    portion_custom_name VARCHAR(100),
    order_note TEXT,
    final_price NUMERIC(12, 2),
    payment_status VARCHAR(20) DEFAULT 'UNPAID', -- UNPAID, TRANSFERRED, CONFIRMED
    transferred_at TIMESTAMP WITH TIME ZONE,
    confirmed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- 6. BẢNG ORDER_ITEMS (Chi tiết các món trong 1 suất cơm)
CREATE TABLE IF NOT EXISTS order_items (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    order_id BIGINT NOT NULL REFERENCES orders(id) ON DELETE CASCADE,
    menu_item_id BIGINT NOT NULL REFERENCES menu_items(id) ON DELETE CASCADE,
    quantity INTEGER DEFAULT 1,
    item_note TEXT
);

-- TRIGGER BẢO VỆ 1: Chặn chọn nhầm menu_item của session khác
CREATE OR REPLACE FUNCTION check_order_item_session()
RETURNS TRIGGER AS $$
DECLARE
    v_order_session_id BIGINT;
    v_menu_item_session_id BIGINT;
BEGIN
    SELECT session_id INTO v_order_session_id FROM orders WHERE id = NEW.order_id;
    SELECT session_id INTO v_menu_item_session_id FROM menu_items WHERE id = NEW.menu_item_id;

    IF v_order_session_id IS DISTINCT FROM v_menu_item_session_id THEN
        RAISE EXCEPTION 'Món ăn không thuộc về sự kiện đặt cơm này!';
    END IF;

    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS trg_check_order_item_session ON order_items;
CREATE TRIGGER trg_check_order_item_session
BEFORE INSERT OR UPDATE ON order_items
FOR EACH ROW
EXECUTE FUNCTION check_order_item_session();

-- TẠO DỮ LIỆU MẪU BAN ĐẦU (NẾU BẢNG USERS ĐANG TRỐNG)
INSERT INTO users (name, email, department, favorite_food)
SELECT 'Quản trị viên', 'admin@dxtech.asia', 'Công nghệ', 'Cơm gà xối mỡ'
WHERE NOT EXISTS (SELECT 1 FROM users LIMIT 1);
