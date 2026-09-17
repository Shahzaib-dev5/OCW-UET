from app.extensions import db, BigIntegerUnsigned

class Author(db.Model):
    __tablename__ = "authors"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    name = db.Column(
        db.String(255),
        nullable=False,
    )

    affiliation = db.Column(
        db.String(255),
        nullable=True,
    )

    email = db.Column(
        db.String(150),
        nullable=True,
    )

    profile_url = db.Column(
        db.String(500),
        nullable=True,
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
    )

    research_papers = db.relationship(
        "ResearchPaperAuthor",
        back_populates="author",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )

    def __repr__(self):
        return f"<Author {self.name}>"