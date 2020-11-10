"""remove start_date

Revision ID: b815dc9607a2
Revises: 5e9a7bef8549
Create Date: 2020-11-08 21:54:23.045820

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b815dc9607a2'
down_revision = '5e9a7bef8549'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('start_date')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('start_date', sa.DATETIME(), nullable=True))

    # ### end Alembic commands ###