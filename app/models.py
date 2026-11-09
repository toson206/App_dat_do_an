from sqlalchemy import (
    Column, BigInteger, String, Text, Numeric, Integer, 
    DateTime, Date, ForeignKey, Identity, func
)
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(BigInteger, Identity(always=False), primary_key=True, index=True)
    name = Column(String(100), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=True)
    department = Column(String(100), nullable=True)
    food_note = Column(Text, nullable=True)        # Ghi chú ăn uống: dị ứng, ăn chay...
    favorite_food = Column(Text, nullable=True)
    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    bank_account_name = Column(String(150), nullable=True)
    qr_image_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions_created = relationship("Session", back_populates="creator", foreign_keys="Session.created_by")
    orders = relationship("Order", back_populates="user", foreign_keys="Order.user_id")


class Restaurant(Base):
    __tablename__ = "restaurants"

    id = Column(BigInteger, Identity(always=False), primary_key=True, index=True)
    name = Column(String(150), nullable=False)
    phone = Column(String(20), nullable=True)
    address = Column(Text, nullable=True)
    menu_url = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    sessions = relationship("Session", back_populates="restaurant")


class Session(Base):
    __tablename__ = "sessions"

    id = Column(BigInteger, Identity(always=False), primary_key=True, index=True)
    share_code = Column(String(32), unique=True, nullable=False, index=True)
    title = Column(String(200), default="Cơm trưa văn phòng")
    restaurant_id = Column(BigInteger, ForeignKey("restaurants.id"), nullable=True)
    created_by = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    cloned_from_session_id = Column(BigInteger, ForeignKey("sessions.id"), nullable=True)
    session_date = Column(Date, server_default=func.current_date())
    deadline = Column(DateTime(timezone=True), nullable=False)
    status = Column(String(30), default="OPEN")  # OPEN, CLOSED, WAITING_PAYMENT, COMPLETED
    event_note = Column(Text, nullable=True)
    pricing_note = Column(Text, nullable=True)  # Ghi chú tính tiền của Host (voucher, phí ship...)
    bank_name = Column(String(100), nullable=True)
    bank_account_number = Column(String(50), nullable=True)
    bank_account_name = Column(String(150), nullable=True)
    qr_image_url = Column(Text, nullable=True)
    shop_message = Column(Text, nullable=True)
    sent_to_shop_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    restaurant = relationship("Restaurant", back_populates="sessions")
    creator = relationship("User", foreign_keys=[created_by], back_populates="sessions_created")
    source_session = relationship("Session", remote_side=[id], foreign_keys=[cloned_from_session_id], backref="cloned_sessions")
    menu_items = relationship("MenuItem", back_populates="session", cascade="all, delete-orphan", order_by="MenuItem.display_order")
    orders = relationship("Order", back_populates="session", cascade="all, delete-orphan")

    @property
    def cloned_from_title(self):
        return self.source_session.title if self.source_session else None


class MenuItem(Base):
    __tablename__ = "menu_items"

    id = Column(BigInteger, Identity(always=False), primary_key=True, index=True)
    session_id = Column(BigInteger, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(150), nullable=False)
    image_url = Column(Text, nullable=True)
    price = Column(Numeric(12, 2), nullable=True)
    display_order = Column(Integer, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="menu_items")
    order_items = relationship("OrderItem", back_populates="menu_item")


class Order(Base):
    __tablename__ = "orders"

    id = Column(BigInteger, Identity(always=False), primary_key=True, index=True)
    session_id = Column(BigInteger, ForeignKey("sessions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True, index=True)
    created_by_user_id = Column(BigInteger, ForeignKey("users.id"), nullable=True)
    portion_custom_name = Column(String(100), nullable=True)
    order_note = Column(Text, nullable=True)
    final_price = Column(Numeric(12, 2), nullable=True)
    payment_status = Column(String(20), default="UNPAID")  # UNPAID, TRANSFERRED, CONFIRMED
    transferred_at = Column(DateTime(timezone=True), nullable=True)
    confirmed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    session = relationship("Session", back_populates="orders")
    user = relationship("User", foreign_keys=[user_id], back_populates="orders")
    creator = relationship("User", foreign_keys=[created_by_user_id])
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = "order_items"

    id = Column(BigInteger, Identity(always=False), primary_key=True, index=True)
    order_id = Column(BigInteger, ForeignKey("orders.id", ondelete="CASCADE"), nullable=False, index=True)
    menu_item_id = Column(BigInteger, ForeignKey("menu_items.id"), nullable=False, index=True)
    quantity = Column(Integer, default=1)
    item_note = Column(Text, nullable=True)
    price_at_order = Column(Numeric(12, 2), nullable=True)  # Snapshot giá món tại thời điểm đặt

    order = relationship("Order", back_populates="items")
    menu_item = relationship("MenuItem", back_populates="order_items")
