"""initial — full schema: all 6 tables

Revision ID: 95445ac45e04
Revises: 
Create Date: 2026-10-09 14:49:23.077760

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = '95445ac45e04'
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create all tables matching the current model definitions."""
    # ── users ────────────────────────────────────────────────
    op.create_table(
        'users',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('email', sa.String(), nullable=False),
        sa.Column('hashed_password', sa.String(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('brand_profile', sa.JSON(), nullable=True),
        sa.Column('first_name', sa.String(), nullable=True),
        sa.Column('source_asset', sa.String(), nullable=False, server_default='vbb'),
        sa.Column('marketing_consent', sa.Boolean(), nullable=False, server_default='0'),
        sa.Column('consent_timestamp', sa.DateTime(timezone=True), nullable=True),
        sa.Column('last_active_at', sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_users_id', 'users', ['id'])
    op.create_index('ix_users_email', 'users', ['email'], unique=True)

    # ── clients ──────────────────────────────────────────────
    op.create_table(
        'clients',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('brand_notes', sa.String(), nullable=True),
        sa.Column('saved_continuity', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_clients_id', 'clients', ['id'])

    # ── projects ─────────────────────────────────────────────
    op.create_table(
        'projects',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('client_id', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='draft'),
        sa.Column('brief', sa.JSON(), nullable=True),
        sa.Column('script', sa.JSON(), nullable=True),
        sa.Column('continuity', sa.JSON(), nullable=True),
        sa.Column('scenes', sa.JSON(), nullable=True),
        sa.Column('prompts', sa.JSON(), nullable=True),
        sa.Column('versions', sa.JSON(), nullable=True),
        sa.Column('source_script', sa.String(), nullable=True),
        sa.Column('adaptation_note', sa.String(), nullable=True),
        sa.Column('settings', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['client_id'], ['clients.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_projects_id', 'projects', ['id'])

    # ── render_jobs ──────────────────────────────────────────
    op.create_table(
        'render_jobs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('project_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=False),
        sa.Column('segment_index', sa.Integer(), nullable=False),
        sa.Column('tier', sa.String(), nullable=False, server_default='standard'),
        sa.Column('vertex_operation_name', sa.String(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, server_default='pending'),
        sa.Column('video_url', sa.String(), nullable=True),
        sa.Column('cost_cents_charged', sa.Integer(), nullable=True),
        sa.Column('error_message', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.ForeignKeyConstraint(['project_id'], ['projects.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_render_jobs_id', 'render_jobs', ['id'])

    # ── credit_balances ──────────────────────────────────────
    op.create_table(
        'credit_balances',
        sa.Column('id', sa.String(36), nullable=False),
        sa.Column('user_id', sa.String(36), nullable=False),
        sa.Column('balance_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('lifetime_purchased_cents', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id'),
    )

    # ── processed_stripe_sessions ────────────────────────────
    op.create_table(
        'processed_stripe_sessions',
        sa.Column('session_id', sa.String(), nullable=False),
        sa.Column('user_id', sa.String(), nullable=True),
        sa.Column('amount_cents', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.PrimaryKeyConstraint('session_id'),
    )
    op.create_index('ix_processed_stripe_sessions_session_id',
                    'processed_stripe_sessions', ['session_id'])


def downgrade() -> None:
    """Drop all tables in reverse dependency order."""
    op.drop_table('processed_stripe_sessions')
    op.drop_table('credit_balances')
    op.drop_table('render_jobs')
    op.drop_table('projects')
    op.drop_table('clients')
    op.drop_table('users')