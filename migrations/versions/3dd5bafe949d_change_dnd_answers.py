"""change dnd answers

Revision ID: 3dd5bafe949d
Revises: fabe9802c36a
Create Date: 2025-01-09 07:51:44.036393

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "3dd5bafe949d"
down_revision: Union[str, None] = "fabe9802c36a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "dragndrop_answers",
        "answer",
        existing_type=sa.VARCHAR(length=512),
        type_=sa.Text(),
        existing_nullable=False,
    )
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column(
        "dragndrop_answers",
        "answer",
        existing_type=sa.Text(),
        type_=sa.VARCHAR(length=512),
        existing_nullable=False,
    )
    # ### end Alembic commands ###
