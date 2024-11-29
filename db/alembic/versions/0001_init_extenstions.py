"""init_extenstions

Revision ID: 255011689875
Revises:
Create Date: 2023-08-24 08:00:42.817470

"""
from alembic import op

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')


def downgrade() -> None:
    op.execute('DROP EXTENSION "uuid-ossp"')
