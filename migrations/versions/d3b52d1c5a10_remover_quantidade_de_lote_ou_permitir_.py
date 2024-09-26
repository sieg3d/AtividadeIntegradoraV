"""Remover quantidade de Lote ou permitir NULL

Revision ID: d3b52d1c5a10
Revises: 8b6299ed21a6
Create Date: 2024-09-21 01:15:35.133414

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'd3b52d1c5a10'
down_revision = '8b6299ed21a6'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('movimentacao_estoque', schema=None) as batch_op:
        batch_op.drop_column('quantidade')
        batch_op.drop_column('saldo_atual')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('movimentacao_estoque', schema=None) as batch_op:
        batch_op.add_column(sa.Column('saldo_atual', sa.INTEGER(), server_default=sa.text("'0'"), nullable=False))
        batch_op.add_column(sa.Column('quantidade', sa.INTEGER(), nullable=False))

    # ### end Alembic commands ###