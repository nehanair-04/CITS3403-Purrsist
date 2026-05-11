"""merge friendship and cat image changes

Revision ID: 9a4d35b4fd9e
Revises: 78d92b936d3c, 9d88a81e77dd
Create Date: 2026-05-11 12:22:36.039866

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '9a4d35b4fd9e'
down_revision = ('78d92b936d3c', '9d88a81e77dd')
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
