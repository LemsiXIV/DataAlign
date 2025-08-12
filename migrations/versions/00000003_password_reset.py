"""Add password reset fields to users table

Revision ID: 00000003_password_reset
Revises: ac1eb72ff16f
Create Date: 2025-08-12 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime

# revision identifiers, used by Alembic.
revision = '00000003_password_reset'
down_revision = 'ac1eb72ff16f'
branch_labels = None
depends_on = None

def upgrade():
    """Add password reset fields to users table"""
    # Add reset_token column
    op.add_column('users', sa.Column('reset_token', sa.String(length=100), nullable=True))
    
    # Add reset_token_expires column
    op.add_column('users', sa.Column('reset_token_expires', sa.DateTime(), nullable=True))
    
    # Create unique index on reset_token
    op.create_index('ix_users_reset_token', 'users', ['reset_token'], unique=True)

def downgrade():
    """Remove password reset fields from users table"""
    # Drop the index first
    op.drop_index('ix_users_reset_token', table_name='users')
    
    # Drop the columns
    op.drop_column('users', 'reset_token_expires')
    op.drop_column('users', 'reset_token')
