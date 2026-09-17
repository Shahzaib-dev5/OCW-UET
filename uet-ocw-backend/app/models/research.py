import enum

from app.extensions import db, BigIntegerUnsigned


class ResearchStatus(enum.Enum):
    DRAFT = "DRAFT"
    PUBLISHED = "PUBLISHED"
    ARCHIVED = "ARCHIVED"


class ResearchPaper(db.Model):
    __tablename__ = "research_papers"

    id = db.Column(
        BigIntegerUnsigned,
        primary_key=True,
        autoincrement=True,
    )

    department_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "departments.id",
            name="fk_research_department",
            ondelete="CASCADE",
        ),
        nullable=False,
        index=True,
    )

    title = db.Column(
        db.String(500),
        nullable=False,
    )

    abstract = db.Column(
        db.Text,
        nullable=True,
    )

    # Kept because it exists in the existing database schema.
    authors = db.Column(
        db.Text,
        nullable=True,
    )

    publication_type = db.Column(
        db.String(100),
        nullable=True,
    )

    journal_name = db.Column(
        db.String(255),
        nullable=True,
    )

    conference_name = db.Column(
        db.String(255),
        nullable=True,
    )

    publication_date = db.Column(
        db.Date,
        nullable=True,
        index=True,
    )

    publication_year = db.Column(
        db.Integer,
        nullable=True,
        index=True,
    )

    doi = db.Column(
        db.String(255),
        nullable=True,
    )

    keywords = db.Column(
        db.String(1000),
        nullable=True,
    )

    paper_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    pdf_url = db.Column(
        db.String(1000),
        nullable=True,
    )

    status = db.Column(
        db.Enum(
            ResearchStatus,
            name="research_status",
        ),
        default=ResearchStatus.PUBLISHED,
        server_default="PUBLISHED",
        index=True,
    )

    display_order = db.Column(
        db.Integer,
        default=0,
        server_default="0",
    )

    created_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
    )

    updated_at = db.Column(
        db.DateTime,
        server_default=db.func.current_timestamp(),
        onupdate=db.func.current_timestamp(),
    )

    department = db.relationship(
        "Department",
        back_populates="research_papers",
    )

    author_links = db.relationship(
        "ResearchPaperAuthor",
        back_populates="research_paper",
        cascade="all, delete-orphan",
        passive_deletes=True,
        order_by="ResearchPaperAuthor.author_order",
    )

    def __repr__(self):
        return f"<ResearchPaper {self.title}>"


class ResearchPaperAuthor(db.Model):
    __tablename__ = "research_paper_authors"

    research_paper_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "research_papers.id",
            name="fk_rpa_paper",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    )

    author_id = db.Column(
        BigIntegerUnsigned,
        db.ForeignKey(
            "authors.id",
            name="fk_rpa_author",
            ondelete="CASCADE",
        ),
        primary_key=True,
        nullable=False,
    )

    author_order = db.Column(
        db.Integer,
        default=0,
        server_default="0",
    )

    research_paper = db.relationship(
        "ResearchPaper",
        back_populates="author_links",
    )

    author = db.relationship(
        "Author",
        back_populates="research_papers",
    )

    def __repr__(self):
        return (
            f"<ResearchPaperAuthor "
            f"paper={self.research_paper_id} "
            f"author={self.author_id}>"
        )
