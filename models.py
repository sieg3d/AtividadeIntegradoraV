from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import pytz

db = SQLAlchemy()

# Defina o fuso horário correto (exemplo: América/São_Paulo)
tz = pytz.timezone('America/Sao_Paulo')

class Projeto(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    prioridade = db.Column(db.String(50), nullable=False)
    previsao_termino = db.Column(db.Date, nullable=False)
    responsavel = db.Column(db.String(100), nullable=False)
    status = db.Column(db.String(50), nullable=False)
    orcamento = db.Column(db.Float, nullable=True)
    data_criacao = db.Column(db.DateTime, default=datetime.now(tz))  # Adiciona a data de criação com o fuso horário correto

class Comentario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    projeto_id = db.Column(db.Integer, db.ForeignKey('projeto.id'), nullable=False)
    conteudo = db.Column(db.Text, nullable=False)
    data_comentario = db.Column(db.DateTime, default=datetime.now(tz))  # Ajuste de fuso horário no comentário

    # Modelos de estoque
class Item(db.Model):
    __table_args__ = {'extend_existing': True}  # Estende a tabela existente ao invés de tentar recriá-la
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    descricao = db.Column(db.Text, nullable=False)
    categoria = db.Column(db.String(50), nullable=False)
    quantidade = db.Column(db.Integer, nullable=False, default=0)
    preco = db.Column(db.Float, nullable=False)


# class MovimentacaoEstoque(db.Model):
#     __table_args__ = {'extend_existing': True}
#     id = db.Column(db.Integer, primary_key=True)
#     item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
#     tipo_movimentacao = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
#     quantidade = db.Column(db.Integer, nullable=False)
#     data_hora = db.Column(db.DateTime, default=datetime.utcnow)
#     item = db.relationship('Item', backref=db.backref('movimentacoes', lazy=True))

# class MovimentacaoEstoque(db.Model):
#     __table_args__ = {'extend_existing': True}
#     id = db.Column(db.Integer, primary_key=True)
#     item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
#     tipo_movimentacao = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
#     quantidade = db.Column(db.Integer, nullable=False)
#     data_hora = db.Column(db.DateTime, default=datetime.utcnow)
#     justificativa = db.Column(db.String(255), nullable=True)  # Novo campo para justificativa
#     item = db.relationship('Item', backref=db.backref('movimentacoes', lazy=True))

class MovimentacaoEstoque(db.Model):
    __table_args__ = {'extend_existing': True}
    id = db.Column(db.Integer, primary_key=True)
    item_id = db.Column(db.Integer, db.ForeignKey('item.id'), nullable=False)
    tipo_movimentacao = db.Column(db.String(10), nullable=False)  # 'entrada' ou 'saida'
    quantidade = db.Column(db.Integer, nullable=False)
    data_hora = db.Column(db.DateTime, default=datetime.utcnow)
    justificativa = db.Column(db.String(255), nullable=True, default='')  # Define string vazia como padrão
    saldo_atual = db.Column(db.Integer, nullable=False)  # Adiciona o campo saldo atual
    item = db.relationship('Item', backref=db.backref('movimentacoes', lazy=True))


class Morador(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    nome = db.Column(db.String(100), nullable=False)
    cpf = db.Column(db.String(14), nullable=False, unique=True)  # CPF com formato XXX.XXX.XXX-XX
    apelido = db.Column(db.String(50), nullable=True)
    endereco = db.Column(db.String(200), nullable=False)
    beneficio = db.Column(db.Boolean, default=False)  # True para 'Sim', False para 'Não'
