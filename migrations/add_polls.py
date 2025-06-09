"""Add polls and votes tables

Revision ID: add_polls
Revises: initial
Create Date: 2024-03-20
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic
revision = 'add_polls'
down_revision = 'initial'
branch_labels = None
depends_on = None

def upgrade():
    # Создаем таблицу polls
    op.create_table(
        'polls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('options', JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), onupdate=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаем таблицу votes
    op.create_table(
        'votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('poll_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('option_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.ForeignKeyConstraint(['poll_id'], ['polls.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаем индексы
    op.create_index('ix_polls_end_date', 'polls', ['end_date'])
    op.create_index('ix_votes_poll_id', 'votes', ['poll_id'])
    op.create_index('ix_votes_user_id', 'votes', ['user_id'])
    op.create_unique_constraint('uq_votes_poll_user', 'votes', ['poll_id', 'user_id'])

def downgrade():
    # Удаляем таблицы в обратном порядке
    op.drop_table('votes')
    op.drop_table('polls') 