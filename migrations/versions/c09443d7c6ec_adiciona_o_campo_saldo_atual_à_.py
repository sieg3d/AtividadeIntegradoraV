"""Adiciona o campo saldo_atual à MovimentacaoEstoque

Revision ID: c09443d7c6ec
Revises: 7a42e8e6f4ea
Create Date: 2024-09-18 20:45:16.069046

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'c09443d7c6ec'
down_revision = '7a42e8e6f4ea'
branch_labels = None
depends_on = None


def upgrade():
    # Comando para adicionar a coluna 'saldo_atual' com um valor padrão
    with op.batch_alter_table('movimentacao_estoque', schema=None) as batch_op:
        batch_op.add_column(sa.Column('saldo_atual', sa.Integer(), nullable=False, server_default='0'))

def downgrade():
    # Comando para remover a coluna 'saldo_atual' na reversão
    with op.batch_alter_table('movimentacao_estoque', schema=None) as batch_op:
        batch_op.drop_column('saldo_atual')

