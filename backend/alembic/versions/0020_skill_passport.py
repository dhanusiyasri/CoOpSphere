"""skills-02 competency and skill passport

Revision ID: 0020_skill_passport
Revises: 0019_digital_literacy
"""
from alembic import op
import sqlalchemy as sa
revision = "0020_skill_passport"
down_revision = "0019_digital_literacy"
branch_labels = None
depends_on = None

def upgrade():
    op.create_table("skill_catalog",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code", sa.String(50), nullable=False, unique=True),
        sa.Column("name", sa.String(160), nullable=False),
        sa.Column("category", sa.String(100), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_skill_catalog_code", "skill_catalog", ["code"])
    op.create_table("trainee_skills",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("trainee_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("skill_id", sa.Integer(), sa.ForeignKey("skill_catalog.id", ondelete="CASCADE"), nullable=False),
        sa.Column("proficiency", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("evidence_type", sa.String(50), nullable=False, server_default="TRAINER_VERIFIED"),
        sa.Column("evidence_note", sa.Text(), nullable=True),
        sa.Column("verified_by_id", sa.Integer(), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.UniqueConstraint("trainee_id", "skill_id", name="uq_trainee_skill"),
    )
    op.create_index("ix_trainee_skills_trainee_id", "trainee_skills", ["trainee_id"])
    op.create_index("ix_trainee_skills_skill_id", "trainee_skills", ["skill_id"])
    skills = [
        ("DIGITAL_RECORDS", "Digital Records", "DIGITAL", "Create, organize and maintain digital cooperative records."),
        ("MEMBER_SERVICES", "Member Services", "COOPERATIVE", "Handle member-facing cooperative service workflows."),
        ("MS_OFFICE", "Office Productivity", "DIGITAL", "Use word processing, spreadsheets and presentations effectively."),
        ("DATA_ENTRY", "Data Entry & Quality", "DIGITAL", "Enter, validate and maintain structured operational data."),
        ("COOPERATIVE_GOVERNANCE", "Cooperative Governance", "COOPERATIVE", "Understand cooperative governance and operational responsibilities."),
        ("FINANCIAL_RECORDS", "Financial Records", "COOPERATIVE", "Maintain basic cooperative financial records and reports."),
        ("COMMUNICATION", "Professional Communication", "PROFESSIONAL", "Communicate clearly with members, colleagues and employers."),
        ("CYBER_SAFETY", "Cyber Safety", "DIGITAL", "Apply safe password, privacy and secure-data practices."),
    ]
    for code,name,cat,desc in skills:
        op.execute(sa.text("INSERT INTO skill_catalog (code,name,category,description) VALUES (:code,:name,:cat,:desc) ON CONFLICT (code) DO NOTHING").bindparams(code=code, name=name, cat=cat, desc=desc))
    op.execute(sa.text("""INSERT INTO trainee_skills (trainee_id, skill_id, proficiency, evidence_type, evidence_note, verified_by_id)
        SELECT u.id, s.id, 3, 'TRAINER_VERIFIED', 'Demo competency baseline', a.id
        FROM users u CROSS JOIN skill_catalog s CROSS JOIN users a
        WHERE u.email='trainee@ncct.local' AND a.email='admin@ncct.local' AND s.code IN ('DIGITAL_RECORDS','COMMUNICATION')
        ON CONFLICT (trainee_id, skill_id) DO NOTHING"""))

def downgrade():
    op.drop_index("ix_trainee_skills_skill_id", table_name="trainee_skills")
    op.drop_index("ix_trainee_skills_trainee_id", table_name="trainee_skills")
    op.drop_table("trainee_skills")
    op.drop_index("ix_skill_catalog_code", table_name="skill_catalog")
    op.drop_table("skill_catalog")
