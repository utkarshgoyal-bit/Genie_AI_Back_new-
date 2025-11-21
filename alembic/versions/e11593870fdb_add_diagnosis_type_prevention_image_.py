"""Add diagnosis_type, prevention, image_urls, images_analyzed columns

Revision ID: e11593870fdb
Revises: 
Create Date: 2025-11-21 13:49:37.951076

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'e11593870fdb'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ONLY add new columns, don't modify existing ones
    op.add_column('plant_detections', sa.Column('diagnosis_type', sa.String(), nullable=True))
    op.add_column('plant_detections', sa.Column('prevention', sa.JSON(), nullable=True))
    op.add_column('plant_detections', sa.Column('image_urls', sa.JSON(), nullable=True))
    op.add_column('plant_detections', sa.Column('images_analyzed', sa.Integer(), nullable=True))


def downgrade() -> None:
    # Remove the new columns
    op.drop_column('plant_detections', 'images_analyzed')
    op.drop_column('plant_detections', 'image_urls')
    op.drop_column('plant_detections', 'prevention')
    op.drop_column('plant_detections', 'diagnosis_type')