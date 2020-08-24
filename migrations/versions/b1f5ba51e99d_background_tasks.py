"""background tasks

Revision ID: b1f5ba51e99d
Revises: 14c816eae3fa
Create Date: 2020-08-09 22:46:23.335464

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b1f5ba51e99d'
down_revision = '14c816eae3fa'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('task',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=128), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('complete', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_task_name'), ['name'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_task_name'))

    op.drop_table('task')
    # ### end Alembic commands ###