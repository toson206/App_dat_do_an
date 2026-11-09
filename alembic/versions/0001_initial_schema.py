"""0001_initial_schema

Revision ID: 0001
Revises: 
Create Date: 

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '0001'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. BẢNG USERS
    op.create_table(
        'users',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('name', sa.String(length=100), nullable=False),
        sa.Column('email', sa.String(length=255), nullable=False),
        sa.Column('password_hash', sa.String(length=255), nullable=True),
        sa.Column('department', sa.String(length=100), nullable=True),
        sa.Column('food_note', sa.Text(), nullable=True),
        sa.Column('favorite_food', sa.Text(), nullable=True),
        sa.Column('bank_name', sa.String(length=100), nullable=True),
        sa.Column('bank_account_number', sa.String(length=50), nullable=True),
        sa.Column('bank_account_name', sa.String(length=150), nullable=True),
        sa.Column('qr_image_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True)
    )
    op.create_index(op.f('ix_users_id'), 'users', ['id'], unique=False)
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)

    # 2. BẢNG RESTAURANTS
    op.create_table(
        'restaurants',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('phone', sa.String(length=20), nullable=True),
        sa.Column('address', sa.Text(), nullable=True),
        sa.Column('menu_url', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True)
    )
    op.create_index(op.f('ix_restaurants_id'), 'restaurants', ['id'], unique=False)

    # 3. BẢNG SESSIONS
    op.create_table(
        'sessions',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('share_code', sa.String(length=32), nullable=False),
        sa.Column('title', sa.String(length=200), server_default='Cơm trưa văn phòng', nullable=True),
        sa.Column('restaurant_id', sa.BigInteger(), sa.ForeignKey('restaurants.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('cloned_from_session_id', sa.BigInteger(), sa.ForeignKey('sessions.id', ondelete='SET NULL'), nullable=True),
        sa.Column('session_date', sa.Date(), server_default=sa.func.current_date(), nullable=True),
        sa.Column('deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('status', sa.String(length=30), server_default='OPEN', nullable=True),
        sa.Column('event_note', sa.Text(), nullable=True),
        sa.Column('pricing_note', sa.Text(), nullable=True),
        sa.Column('bank_name', sa.String(length=100), nullable=True),
        sa.Column('bank_account_number', sa.String(length=50), nullable=True),
        sa.Column('bank_account_name', sa.String(length=150), nullable=True),
        sa.Column('qr_image_url', sa.Text(), nullable=True),
        sa.Column('shop_message', sa.Text(), nullable=True),
        sa.Column('sent_to_shop_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True)
    )
    op.create_index(op.f('ix_sessions_id'), 'sessions', ['id'], unique=False)
    op.create_index(op.f('ix_sessions_share_code'), 'sessions', ['share_code'], unique=True)

    # 4. BẢNG MENU_ITEMS
    op.create_table(
        'menu_items',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('session_id', sa.BigInteger(), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('name', sa.String(length=150), nullable=False),
        sa.Column('image_url', sa.Text(), nullable=True),
        sa.Column('price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('display_order', sa.Integer(), server_default='0', nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True)
    )
    op.create_index(op.f('ix_menu_items_id'), 'menu_items', ['id'], unique=False)
    op.create_index(op.f('ix_menu_items_session_id'), 'menu_items', ['session_id'], unique=False)

    # 5. BẢNG ORDERS
    op.create_table(
        'orders',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('session_id', sa.BigInteger(), sa.ForeignKey('sessions.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('created_by_user_id', sa.BigInteger(), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('portion_custom_name', sa.String(length=100), nullable=True),
        sa.Column('order_note', sa.Text(), nullable=True),
        sa.Column('final_price', sa.Numeric(precision=12, scale=2), nullable=True),
        sa.Column('payment_status', sa.String(length=20), server_default='UNPAID', nullable=True),
        sa.Column('transferred_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('confirmed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=True)
    )
    op.create_index(op.f('ix_orders_id'), 'orders', ['id'], unique=False)
    op.create_index(op.f('ix_orders_session_id'), 'orders', ['session_id'], unique=False)
    op.create_index(op.f('ix_orders_user_id'), 'orders', ['user_id'], unique=False)

    # 6. BẢNG ORDER_ITEMS
    op.create_table(
        'order_items',
        sa.Column('id', sa.BigInteger(), sa.Identity(always=False), primary_key=True),
        sa.Column('order_id', sa.BigInteger(), sa.ForeignKey('orders.id', ondelete='CASCADE'), nullable=False),
        sa.Column('menu_item_id', sa.BigInteger(), sa.ForeignKey('menu_items.id', ondelete='CASCADE'), nullable=False),
        sa.Column('quantity', sa.Integer(), server_default='1', nullable=True),
        sa.Column('item_note', sa.Text(), nullable=True),
        sa.Column('price_at_order', sa.Numeric(precision=12, scale=2), nullable=True)
    )
    op.create_index(op.f('ix_order_items_id'), 'order_items', ['id'], unique=False)
    op.create_index(op.f('ix_order_items_order_id'), 'order_items', ['order_id'], unique=False)
    op.create_index(op.f('ix_order_items_menu_item_id'), 'order_items', ['menu_item_id'], unique=False)

    # 7. TRIGGER TOÀN VẸN DỮ LIỆU ORDER_ITEM - SESSION
    op.execute("""
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
    """)

    op.execute("""
    DROP TRIGGER IF EXISTS trg_check_order_item_session ON order_items;
    CREATE TRIGGER trg_check_order_item_session
    BEFORE INSERT OR UPDATE ON order_items
    FOR EACH ROW
    EXECUTE FUNCTION check_order_item_session();
    """)

    # 8. DỮ LIỆU MẪU BAN ĐẦU
    op.execute("""
    INSERT INTO users (name, email, department, favorite_food)
    SELECT 'Quản trị viên', 'admin@dxtech.asia', 'Công nghệ', 'Cơm gà xối mỡ'
    WHERE NOT EXISTS (SELECT 1 FROM users WHERE email = 'admin@dxtech.asia');
    """)


def downgrade() -> None:
    # Drop trigger và function
    op.execute("DROP TRIGGER IF EXISTS trg_check_order_item_session ON order_items;")
    op.execute("DROP FUNCTION IF EXISTS check_order_item_session();")

    # Drop tables
    op.drop_table('order_items')
    op.drop_table('orders')
    op.drop_table('menu_items')
    op.drop_table('sessions')
    op.drop_table('restaurants')
    op.drop_table('users')
