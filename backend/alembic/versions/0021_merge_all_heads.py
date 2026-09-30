"""Merge the training/skills and LMS lesson-progress migration branches."""

from typing import Sequence, Union

from alembic import op

revision: str = "0021_merge_all_heads"
down_revision: Union[str, Sequence[str], None] = ("0020_skill_passport", "d47869571d78")
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
