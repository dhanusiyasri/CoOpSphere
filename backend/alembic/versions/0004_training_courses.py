"""ERP-07 training course curriculum

Revision ID: 0004_training_courses
Revises: 0003_participant_profiles
"""
from alembic import op
import sqlalchemy as sa
revision = "0004_training_courses"
down_revision = "0003_participant_profiles"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("training_courses",
        sa.Column("id", sa.Integer(), primary_key=True), sa.Column("programme_id", sa.Integer(), nullable=False),
        sa.Column("course_code", sa.String(50), nullable=False), sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.Text()), sa.Column("category", sa.String(100), nullable=False, server_default="GENERAL"),
        sa.Column("delivery_mode", sa.String(30), nullable=False, server_default="HYBRID"), sa.Column("duration_hours", sa.Integer(), nullable=False, server_default="4"),
        sa.Column("level", sa.String(30), nullable=False, server_default="FOUNDATION"), sa.Column("status", sa.String(30), nullable=False, server_default="DRAFT"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["programme_id"],["training_programmes.id"],ondelete="CASCADE"),
        sa.UniqueConstraint("programme_id","course_code",name="uq_course_programme_code"))
    op.create_index("ix_training_courses_programme_id","training_courses",["programme_id"])
    op.create_table("training_course_modules",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("course_id",sa.Integer(),nullable=False),sa.Column("module_number",sa.Integer(),nullable=False),sa.Column("title",sa.String(200),nullable=False),sa.Column("learning_objectives",sa.Text()),sa.Column("duration_minutes",sa.Integer(),nullable=False,server_default="60"),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.ForeignKeyConstraint(["course_id"],["training_courses.id"],ondelete="CASCADE"),sa.UniqueConstraint("course_id","module_number",name="uq_course_module_number"))
    op.create_index("ix_training_course_modules_course_id","training_course_modules",["course_id"])
    op.create_table("training_course_lessons",
        sa.Column("id",sa.Integer(),primary_key=True),sa.Column("module_id",sa.Integer(),nullable=False),sa.Column("lesson_number",sa.Integer(),nullable=False),sa.Column("title",sa.String(200),nullable=False),sa.Column("content_type",sa.String(30),nullable=False,server_default="TEXT"),sa.Column("content_url",sa.String(500)),sa.Column("duration_minutes",sa.Integer(),nullable=False,server_default="15"),sa.Column("is_mandatory",sa.Boolean(),nullable=False,server_default=sa.true()),sa.Column("created_at",sa.DateTime(timezone=True),server_default=sa.func.now(),nullable=False),sa.ForeignKeyConstraint(["module_id"],["training_course_modules.id"],ondelete="CASCADE"),sa.UniqueConstraint("module_id","lesson_number",name="uq_module_lesson_number"))
    op.create_index("ix_training_course_lessons_module_id","training_course_lessons",["module_id"])

def downgrade():
    op.drop_index("ix_training_course_lessons_module_id",table_name="training_course_lessons"); op.drop_table("training_course_lessons")
    op.drop_index("ix_training_course_modules_course_id",table_name="training_course_modules"); op.drop_table("training_course_modules")
    op.drop_index("ix_training_courses_programme_id",table_name="training_courses"); op.drop_table("training_courses")
