"""merge migrations from binh and quy

Revision ID: dc2171dec341
Revises: 16795b2ee0df, 9c41c7015ef3
Create Date: 2021-03-21 10:51:36.398447

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = "dc2171dec341"
down_revision = ("16795b2ee0df", "9c41c7015ef3")
branch_labels = None
depends_on = None


def upgrade():
    pass


def downgrade():
    pass
