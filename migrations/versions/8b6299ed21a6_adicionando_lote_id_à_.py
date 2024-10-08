"""Adicionando lote_id à MovimentacaoEstoque

Revision ID: 8b6299ed21a6
Revises: 743b9f6d68af
Create Date: 2024-09-20 23:12:52.274938

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '8b6299ed21a6'
down_revision = '743b9f6d68af'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('movimentacao_estoque', schema=None) as batch_op:
        batch_op.add_column(sa.Column('lote_id', sa.Integer(), nullable=True))
        # Adiciona um nome para a foreign key
        batch_op.create_foreign_key('fk_movimentacao_estoque_lote_id', 'lote', ['lote_id'], ['id'])
        batch_op.drop_column('lote')
        batch_op.drop_column('validade')

    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    with op.batch_alter_table('movimentacao_estoque', schema=None) as batch_op:
        batch_op.add_column(sa.Column('validade', sa.DATE(), nullable=True))
        batch_op.add_column(sa.Column('lote', sa.VARCHAR(length=50), nullable=True))
        # Adiciona o nome da constraint ao remover a chave estrangeira
        batch_op.drop_constraint('fk_movimentacao_estoque_lote_id', type_='foreignkey')
        batch_op.drop_column('lote_id')

    # ### end Alembic commands ###

