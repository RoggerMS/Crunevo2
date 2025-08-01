"""Add forum modernization fields and tables"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.engine.reflection import Inspector

revision = "5c64e11d41b6"
down_revision = "f516460c56d7"
branch_labels = None
depends_on = None


def has_table(name: str, conn) -> bool:
    inspector = Inspector.from_engine(conn)
    return name in inspector.get_table_names()


def has_column(table_name: str, column_name: str, conn) -> bool:
    inspector = Inspector.from_engine(conn)
    columns = [col["name"] for col in inspector.get_columns(table_name)]
    return column_name in columns


def upgrade():
    conn = op.get_bind()

    # ForumQuestion extra fields
    if has_table("forum_question", conn):
        if not has_column("forum_question", "difficulty_level", conn):
            op.add_column(
                "forum_question", sa.Column("difficulty_level", sa.String(length=20))
            )
        if not has_column("forum_question", "subject_area", conn):
            op.add_column(
                "forum_question", sa.Column("subject_area", sa.String(length=100))
            )
        if not has_column("forum_question", "grade_level", conn):
            op.add_column(
                "forum_question", sa.Column("grade_level", sa.String(length=20))
            )
        if not has_column("forum_question", "bounty_points", conn):
            op.add_column(
                "forum_question",
                sa.Column("bounty_points", sa.Integer(), server_default="0"),
            )
        if not has_column("forum_question", "is_urgent", conn):
            op.add_column(
                "forum_question",
                sa.Column("is_urgent", sa.Boolean(), server_default=sa.text("false")),
            )
        if not has_column("forum_question", "is_featured", conn):
            op.add_column(
                "forum_question",
                sa.Column("is_featured", sa.Boolean(), server_default=sa.text("false")),
            )
        if not has_column("forum_question", "quality_score", conn):
            op.add_column(
                "forum_question",
                sa.Column("quality_score", sa.Float(), server_default="0"),
            )
        if not has_column("forum_question", "homework_deadline", conn):
            op.add_column(
                "forum_question", sa.Column("homework_deadline", sa.DateTime())
            )
        if not has_column("forum_question", "exam_date", conn):
            op.add_column("forum_question", sa.Column("exam_date", sa.DateTime()))
        if not has_column("forum_question", "context_type", conn):
            op.add_column(
                "forum_question",
                sa.Column(
                    "context_type", sa.String(length=50), server_default="general"
                ),
            )

    # ForumAnswer extra fields
    if has_table("forum_answer", conn):
        if not has_column("forum_answer", "explanation_quality", conn):
            op.add_column(
                "forum_answer", sa.Column("explanation_quality", sa.String(length=20))
            )
        if not has_column("forum_answer", "has_step_by_step", conn):
            op.add_column(
                "forum_answer",
                sa.Column(
                    "has_step_by_step", sa.Boolean(), server_default=sa.text("false")
                ),
            )
        if not has_column("forum_answer", "has_visual_aids", conn):
            op.add_column(
                "forum_answer",
                sa.Column(
                    "has_visual_aids", sa.Boolean(), server_default=sa.text("false")
                ),
            )
        if not has_column("forum_answer", "is_expert_verified", conn):
            op.add_column(
                "forum_answer",
                sa.Column(
                    "is_expert_verified", sa.Boolean(), server_default=sa.text("false")
                ),
            )
        if not has_column("forum_answer", "confidence_level", conn):
            op.add_column(
                "forum_answer", sa.Column("confidence_level", sa.String(length=20))
            )
        if not has_column("forum_answer", "helpful_count", conn):
            op.add_column(
                "forum_answer",
                sa.Column("helpful_count", sa.Integer(), server_default="0"),
            )
        if not has_column("forum_answer", "word_count", conn):
            op.add_column(
                "forum_answer",
                sa.Column("word_count", sa.Integer(), server_default="0"),
            )
        if not has_column("forum_answer", "estimated_reading_time", conn):
            op.add_column(
                "forum_answer",
                sa.Column("estimated_reading_time", sa.Integer(), server_default="1"),
            )
        if not has_column("forum_answer", "contains_formulas", conn):
            op.add_column(
                "forum_answer",
                sa.Column(
                    "contains_formulas", sa.Boolean(), server_default=sa.text("false")
                ),
            )
        if not has_column("forum_answer", "contains_code", conn):
            op.add_column(
                "forum_answer",
                sa.Column(
                    "contains_code", sa.Boolean(), server_default=sa.text("false")
                ),
            )

    # ForumTag table
    if not has_table("forum_tag", conn):
        op.create_table(
            "forum_tag",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=50), unique=True, nullable=False),
            sa.Column("description", sa.String(length=200)),
            sa.Column("color", sa.String(length=7), default="#667eea"),
            sa.Column("icon", sa.String(length=50), default="bi-tag"),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
            mysql_charset="utf8mb4",
        )

    # Association tables
    if not has_table("question_tags", conn):
        op.create_table(
            "question_tags",
            sa.Column(
                "question_id",
                sa.Integer(),
                sa.ForeignKey("forum_question.id"),
                primary_key=True,
            ),
            sa.Column(
                "tag_id", sa.Integer(), sa.ForeignKey("forum_tag.id"), primary_key=True
            ),
            mysql_charset="utf8mb4",
        )

    if not has_table("user_bookmarks", conn):
        op.create_table(
            "user_bookmarks",
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True
            ),
            sa.Column(
                "question_id",
                sa.Integer(),
                sa.ForeignKey("forum_question.id"),
                primary_key=True,
            ),
            mysql_charset="utf8mb4",
        )

    if not has_table("answer_votes", conn):
        op.create_table(
            "answer_votes",
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True
            ),
            sa.Column(
                "answer_id",
                sa.Integer(),
                sa.ForeignKey("forum_answer.id"),
                primary_key=True,
            ),
            sa.Column("vote_type", sa.String(length=10), nullable=False),
            mysql_charset="utf8mb4",
        )

    if not has_table("forum_report", conn):
        op.create_table(
            "forum_report",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column(
                "reporter_id", sa.Integer(), sa.ForeignKey("user.id"), nullable=False
            ),
            sa.Column(
                "reported_question_id", sa.Integer(), sa.ForeignKey("forum_question.id")
            ),
            sa.Column(
                "reported_answer_id", sa.Integer(), sa.ForeignKey("forum_answer.id")
            ),
            sa.Column("reason", sa.String(length=100), nullable=False),
            sa.Column("description", sa.Text()),
            sa.Column("status", sa.String(length=20), default="pending"),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
            mysql_charset="utf8mb4",
        )

    if not has_table("forum_badge", conn):
        op.create_table(
            "forum_badge",
            sa.Column("id", sa.Integer(), primary_key=True),
            sa.Column("name", sa.String(length=100), nullable=False),
            sa.Column("description", sa.String(length=200)),
            sa.Column("icon", sa.String(length=50), default="bi-award"),
            sa.Column("color", sa.String(length=7), default="#ffd700"),
            sa.Column("category", sa.String(length=50)),
            sa.Column("requirement_type", sa.String(length=50)),
            sa.Column("requirement_value", sa.Integer()),
            sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
            sa.Column("created_at", sa.DateTime(), default=sa.func.now()),
            mysql_charset="utf8mb4",
        )

    if not has_table("user_badges", conn):
        op.create_table(
            "user_badges",
            sa.Column(
                "user_id", sa.Integer(), sa.ForeignKey("user.id"), primary_key=True
            ),
            sa.Column(
                "badge_id",
                sa.Integer(),
                sa.ForeignKey("forum_badge.id"),
                primary_key=True,
            ),
            sa.Column("earned_at", sa.DateTime(), default=sa.func.now()),
            mysql_charset="utf8mb4",
        )


def downgrade():
    conn = op.get_bind()
    op.drop_table("user_badges", if_exists=True)
    op.drop_table("forum_badge", if_exists=True)
    op.drop_table("forum_report", if_exists=True)
    op.drop_table("answer_votes", if_exists=True)
    op.drop_table("user_bookmarks", if_exists=True)
    op.drop_table("question_tags", if_exists=True)
    op.drop_table("forum_tag", if_exists=True)
    if has_table("forum_answer", conn):
        for col in [
            "explanation_quality",
            "has_step_by_step",
            "has_visual_aids",
            "is_expert_verified",
            "confidence_level",
            "helpful_count",
            "word_count",
            "estimated_reading_time",
            "contains_formulas",
            "contains_code",
        ]:
            if has_column("forum_answer", col, conn):
                op.drop_column("forum_answer", col)
    if has_table("forum_question", conn):
        for col in [
            "difficulty_level",
            "subject_area",
            "grade_level",
            "bounty_points",
            "is_urgent",
            "is_featured",
            "quality_score",
            "homework_deadline",
            "exam_date",
            "context_type",
        ]:
            if has_column("forum_question", col, conn):
                op.drop_column("forum_question", col)
