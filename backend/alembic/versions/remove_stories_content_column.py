"""Remove unused stories.content column

Revision ID: remove_content_column
Revises: 
Create Date: 2025-08-30 21:10:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'remove_content_column'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Drop the content column from stories table
    op.drop_column('stories', 'content')


def downgrade() -> None:
    # Add the content column back
    op.add_column('stories', sa.Column('content', sa.Text(), nullable=True))