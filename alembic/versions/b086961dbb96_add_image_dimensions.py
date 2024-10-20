"""Add image dimensions

Revision ID: b086961dbb96
Revises: 
Create Date: 2024-10-19 18:26:49.035364

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b086961dbb96'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('listings', sa.Column('image_width', sa.Integer(), nullable=True))
    op.add_column('listings', sa.Column('image_height', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('listings', 'image_height')
    op.drop_column('listings', 'image_width')
    # ### end Alembic commands ###
