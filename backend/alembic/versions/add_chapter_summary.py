"""add chapter summary field

Revision ID: add_chapter_summary
Revises: 
Create Date: 2025-11-18

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_chapter_summary'
down_revision = None  # Will be set by alembic
head = None


def upgrade():
    op.add_column('story_chapters', sa.Column('summary', sa.Text(), nullable=True))


def downgrade():
    op.drop_column('story_chapters', 'summary')
