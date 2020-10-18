"""initial

Revision ID: 73db263fe702
Revises: 
Create Date: 2020-09-13 21:44:19.860490

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '73db263fe702'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('username', sa.String(length=64), nullable=True),
    sa.Column('email', sa.String(length=120), nullable=True),
    sa.Column('password_hash', sa.String(length=128), nullable=True),
    sa.Column('last_seen', sa.DateTime(), nullable=True),
    sa.Column('token', sa.String(length=32), nullable=True),
    sa.Column('token_expiration', sa.DateTime(), nullable=True),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_user'))
    )
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_user_email'), ['email'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_token'), ['token'], unique=True)
        batch_op.create_index(batch_op.f('ix_user_username'), ['username'], unique=True)

    op.create_table('deck',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=256), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_deck_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_deck'))
    )
    with op.batch_alter_table('deck', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_deck_timestamp'), ['timestamp'], unique=False)

    op.create_table('notification',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('timestamp', sa.Float(), nullable=True),
    sa.Column('payload_json', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_notification_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_notification'))
    )
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_notification_name'), ['name'], unique=False)
        batch_op.create_index(batch_op.f('ix_notification_timestamp'), ['timestamp'], unique=False)

    op.create_table('task',
    sa.Column('id', sa.String(length=36), nullable=False),
    sa.Column('name', sa.String(length=128), nullable=True),
    sa.Column('description', sa.String(length=128), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('complete', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_task_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_task'))
    )
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_task_name'), ['name'], unique=False)

    op.create_table('card',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('front', sa.String(length=500), nullable=True),
    sa.Column('back', sa.String(length=1000), nullable=True),
    sa.Column('timestamp', sa.DateTime(), nullable=True),
    sa.Column('user_id', sa.Integer(), nullable=True),
    sa.Column('deck_id', sa.Integer(), nullable=True),
    sa.Column('start_date', sa.DateTime(), nullable=True),
    sa.Column('next_date', sa.DateTime(), nullable=True),
    sa.Column('bucket', sa.Integer(), nullable=True),
    sa.Column('reverse_asking', sa.Boolean(), nullable=True),
    sa.ForeignKeyConstraint(['deck_id'], ['deck.id'], name=op.f('fk_card_deck_id_deck')),
    sa.ForeignKeyConstraint(['user_id'], ['user.id'], name=op.f('fk_card_user_id_user')),
    sa.PrimaryKeyConstraint('id', name=op.f('pk_card'))
    )
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.create_index(batch_op.f('ix_card_next_date'), ['next_date'], unique=False)
        batch_op.create_index(batch_op.f('ix_card_timestamp'), ['timestamp'], unique=False)

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('card', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_card_timestamp'))
        batch_op.drop_index(batch_op.f('ix_card_next_date'))

    op.drop_table('card')
    with op.batch_alter_table('task', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_task_name'))

    op.drop_table('task')
    with op.batch_alter_table('notification', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_notification_timestamp'))
        batch_op.drop_index(batch_op.f('ix_notification_name'))

    op.drop_table('notification')
    with op.batch_alter_table('deck', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_deck_timestamp'))

    op.drop_table('deck')
    with op.batch_alter_table('user', schema=None) as batch_op:
        batch_op.drop_index(batch_op.f('ix_user_username'))
        batch_op.drop_index(batch_op.f('ix_user_token'))
        batch_op.drop_index(batch_op.f('ix_user_email'))

    op.drop_table('user')
    # ### end Alembic commands ###
