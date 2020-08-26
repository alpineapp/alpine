"""deck

Revision ID: adef7acc1cb4
Revises: e536e278330f
Create Date: 2020-08-25 00:45:32.148007

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'adef7acc1cb4'
down_revision = 'e536e278330f'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.add_column(sa.Column('deck_id', sa.Integer(), nullable=True))
        batch_op.create_foreign_key(batch_op.f('fk_card_deck_id_deck'), 'deck', ['deck_id'], ['id'])

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_constraint(batch_op.f('fk_card_deck_id_deck'), type_='foreignkey')
        batch_op.drop_column('deck_id')

    # ### end Alembic commands ###
