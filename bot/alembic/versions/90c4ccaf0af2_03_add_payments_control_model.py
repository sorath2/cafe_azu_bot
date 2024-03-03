"""03_add_payments_control_model

Revision ID: 90c4ccaf0af2
Revises: 583ac24d4d9b
Create Date: 2024-01-31 14:01:35.297406

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '90c4ccaf0af2'
down_revision: Union[str, None] = '583ac24d4d9b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('azucafe_payment',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('chat_id', sa.BigInteger(), nullable=False),
    sa.Column('order_id', sa.Integer(), nullable=False),
    sa.Column('payment_link', sa.String(), nullable=False),
    sa.Column('payment_start', sa.DateTime(), nullable=False),
    sa.Column('payment_message_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['order_id'], ['azucafe_order.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('azucafe_payment')
    # ### end Alembic commands ###
