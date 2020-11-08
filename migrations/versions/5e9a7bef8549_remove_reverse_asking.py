"""remove reverse asking

Revision ID: 5e9a7bef8549
Revises: 7c7a0fcf946f
Create Date: 2020-11-08 18:30:05.126388

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '5e9a7bef8549'
down_revision = '7c7a0fcf946f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_column('reverse_asking')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('reverse_asking', sa.BOOLEAN(), nullable=True))

    # ### end Alembic commands ###
