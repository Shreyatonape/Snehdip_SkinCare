"""add created_at to users

Revision ID: aa4498ce3c75
Revises: 
Create Date: 2025-12-27
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'aa4498ce3c75'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        'users',
        sa.Column(
            'created_at',
            sa.DateTime(),
            server_default=sa.func.now(),
            nullable=True
        )
    )


def downgrade():
    op.drop_column('users', 'created_at')