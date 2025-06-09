"""Initial migration

Revision ID: initial
Revises: 
Create Date: 2024-03-20

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'initial'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Создаем таблицу пользователей
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('telegram_id', sa.Integer(), nullable=False),
        sa.Column('is_admin', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('telegram_id')
    )

    # Создаем таблицу мероприятий
    op.create_table(
        'events',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('date', sa.DateTime(), nullable=False),
        sa.Column('location', sa.String()),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('created_by', sa.Integer(), sa.ForeignKey('users.id')),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаем таблицу опросов
    op.create_table(
        'polls',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('description', sa.String()),
        sa.Column('end_date', sa.DateTime(), nullable=False),
        sa.Column('options', sa.JSON, nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаем таблицу голосов
    op.create_table(
        'votes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('poll_id', sa.Integer(), sa.ForeignKey('polls.id', ondelete='CASCADE'), nullable=False),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('option_index', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Создаем индексы
    op.create_index('ix_polls_end_date', 'polls', ['end_date'])
    op.create_index('ix_votes_poll_id', 'votes', ['poll_id'])
    op.create_index('ix_votes_user_id', 'votes', ['user_id'])
    op.create_unique_constraint('uq_votes_poll_user', 'votes', ['poll_id', 'user_id'])

def downgrade() -> None:
    # Удаляем таблицы в обратном порядке
    op.drop_table('votes')
    op.drop_table('polls')
    op.drop_table('events')
    op.drop_table('users') 