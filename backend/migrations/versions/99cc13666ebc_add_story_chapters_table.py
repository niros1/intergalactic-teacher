"""add_story_chapters_table

Revision ID: 99cc13666ebc
Revises: 179400ee2fd3
Create Date: 2025-08-27 14:23:07.388334

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '99cc13666ebc'
down_revision = '179400ee2fd3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create story_chapters table
    op.create_table(
        'story_chapters',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('story_id', sa.Integer(), nullable=False),
        sa.Column('chapter_number', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('created_from_choice_id', sa.Integer(), nullable=True),
        sa.Column('created_from_branch_id', sa.Integer(), nullable=True),
        sa.Column('is_ending', sa.Boolean(), nullable=True),
        sa.Column('is_published', sa.Boolean(), nullable=True),
        sa.Column('estimated_reading_time', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['created_from_branch_id'], ['story_branches.id'], ),
        sa.ForeignKeyConstraint(['created_from_choice_id'], ['choices.id'], ),
        sa.ForeignKeyConstraint(['story_id'], ['stories.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_story_chapters_id'), 'story_chapters', ['id'], unique=False)
    op.create_index(op.f('ix_story_chapters_story_id'), 'story_chapters', ['story_id'], unique=False)


def downgrade() -> None:
    # Drop story_chapters table
    op.drop_index(op.f('ix_story_chapters_story_id'), table_name='story_chapters')
    op.drop_index(op.f('ix_story_chapters_id'), table_name='story_chapters')
    op.drop_table('story_chapters')