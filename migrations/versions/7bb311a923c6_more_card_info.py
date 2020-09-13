"""more card info

Revision ID: 7bb311a923c6
Revises: a4914228aa39
Create Date: 2020-09-02 11:06:08.340827

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '7bb311a923c6'
down_revision = 'a4914228aa39'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('card', sa.Column('bucket', sa.Integer(), nullable=True))
    op.add_column('card', sa.Column('example', sa.String(length=2048), nullable=True))
    op.add_column('card', sa.Column('next_date', sa.DateTime(), nullable=True))
    op.add_column('card', sa.Column('reverse_asking', sa.Boolean(), nullable=True))
    op.add_column('card', sa.Column('source', sa.String(length=2048), nullable=True))
    op.add_column('card', sa.Column('start_date', sa.DateTime(), nullable=True))
    op.add_column('card', sa.Column('use_case', sa.String(length=2048), nullable=True))
    op.create_index(op.f('ix_card_next_date'), 'card', ['next_date'], unique=False)
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_index(op.f('ix_card_next_date'), table_name='card')
    op.drop_column('card', 'use_case')
    op.drop_column('card', 'start_date')
    op.drop_column('card', 'source')
    op.drop_column('card', 'reverse_asking')
    op.drop_column('card', 'next_date')
    op.drop_column('card', 'example')
    op.drop_column('card', 'bucket')
    # ### end Alembic commands ###