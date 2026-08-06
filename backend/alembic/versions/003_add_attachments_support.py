"""Add attachments table and attachments column to messages.

Revision ID: 003_add_attachments_support
Revises: 002_add_conversations
Create Date: 2026-08-06 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "003_add_attachments_support"
down_revision = "002_add_conversations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Create attachments table and add attachments column to messages."""
    # Create attachments table
    op.create_table(
        'attachments',
        sa.Column('id', sa.String(36), primary_key=True),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('filename', sa.String(255), nullable=False),
        sa.Column('mime_type', sa.String(100), nullable=False),
        sa.Column('size_bytes', sa.Integer(), nullable=False),
        sa.Column('extracted_text', sa.Text(), nullable=True),
        sa.Column('extraction_status', sa.String(20), nullable=False),
        sa.Column('extraction_error', sa.Text(), nullable=True),
        sa.Column('page_count', sa.Integer(), nullable=True),
        sa.Column('word_count', sa.Integer(), nullable=True),
        sa.Column('extraction_method', sa.String(50), nullable=True),
        sa.Column('processing_time_ms', sa.Float(), nullable=True),
        sa.Column('ocr_applied', sa.Boolean(), server_default='false'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.func.now()),
        sa.Column('expires_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
    )
    
    # Create indexes
    op.create_index('idx_attachments_user_id', 'attachments', ['user_id'])
    op.create_index('idx_attachments_status', 'attachments', ['extraction_status'])
    op.create_index('idx_attachments_expires', 'attachments', ['expires_at'])
    
    # Add attachments column to messages
    op.add_column(
        'messages',
        sa.Column('attachments', sa.JSON(), server_default='[]')
    )


def downgrade() -> None:
    """Revert attachments table and attachments column from messages."""
    # Remove column from messages
    op.drop_column('messages', 'attachments')
    
    # Drop indexes
    op.drop_index('idx_attachments_expires', table_name='attachments')
    op.drop_index('idx_attachments_status', table_name='attachments')
    op.drop_index('idx_attachments_user_id', table_name='attachments')
    
    # Drop table
    op.drop_table('attachments')
