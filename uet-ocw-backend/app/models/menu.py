import enum

from app.extensions import db, BigIntegerUnsigned


class MenuLocation(enum.Enum):
    HEADER = "HEADER"
    FOOTER = "FOOTER"
    SIDEBAR = "SIDEBAR"


class MenuItem(db.Model):
    __tablename__ = "menu_items"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    parent_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "menu_items.id",
            name="fk_menu_parent",
            ondelete="CASCADE",
        ),
        nullable=True,
        index=True,
    )

    title = db.Column(
        db.String(100),
        nullable=False,
    )

    slug = db.Column(
        db.String(255),
        nullable=True,
    )

    url = db.Column(
        db.String(500),
        nullable=True,
    )

    menu_location = db.Column(
        db.Enum(
            MenuLocation,
            name="menu_location",
        ),
        default=MenuLocation.HEADER,
        server_default="HEADER",
        nullable=False,
    )

    icon = db.Column(
        db.String(100),
        nullable=True,
    )

    display_order = db.Column(
        db.Integer,
        default=0,
        server_default="0",
        nullable=False,
    )

    is_active = db.Column(
        db.Boolean,
        default=True,
        server_default="1",
        nullable=False,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
    )

    # Parent menu item
    parent = db.relationship(
        "MenuItem",
        remote_side=[id],
        back_populates="children",
    )

    # Child menu items
    children = db.relationship(
        "MenuItem",
        back_populates="parent",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="MenuItem.display_order",
    )

    def __repr__(self):
        return f"<MenuItem {self.title}>"
