"""Add preferred_chapters to children table

Revision ID: 65113431137a
Revises: 0d1291b6e455
Create Date: 2025-11-02 17:18:09.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '65113431137a'
down_revision = '0d1291b6e455'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add preferred_chapters column to children table."""
    # Add preferred_chapters column with default value of 3
    op.add_column('children', sa.Column('preferred_chapters', sa.Integer(), nullable=True, default=3))
    
    # Update existing records to have the default value
    op.execute("UPDATE children SET preferred_chapters = 3 WHERE preferred_chapters IS NULL")
    
    # Make the column non-nullable after setting default values
    op.alter_column('children', 'preferred_chapters', nullable=False)
    
    # Add check constraint to ensure value is between 1 and 10
    op.create_check_constraint(
        'ck_children_preferred_chapters_range',
        'children',
        'preferred_chapters >= 1 AND preferred_chapters <= 10'
    )


def downgrade() -> None:
    """Remove preferred_chapters column from children table."""
    # Drop check constraint first
    op.drop_constraint('ck_children_preferred_chapters_range', 'children', type_='check')
    
    # Drop the column
    op.drop_column('children', 'preferred_chapters')






