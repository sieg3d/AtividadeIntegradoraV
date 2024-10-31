import unicodedata  # Importa módulo para remover acentos
import os
secret_key = os.urandom(24)
print(secret_key)
from datetime import datetime, date, timedelta

import pytz
from flask import (
    Flask, render_template, request, redirect, url_for, flash, session, jsonify
)
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate

from models import db, Item, MovimentacaoEstoque, Projeto, Comentario, Morador, Compromisso  # Importe os modelos necessários

# Configurações globais
app = Flask(__name__)
app.config['SECRET_KEY'] = secret_key

# Configurações do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projetos.db'  # Define o banco de dados SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa rastreamento de modificações (melhora a performance)

# Inicialização do banco de dados e migrações
db.init_app(app)  # Inicializa o banco de dados com o Flask app
migrate = Migrate(app, db)  # Inicializa o sistema de migração do banco de dados

# Configuração do fuso horário
tz = pytz.timezone('America/Sao_Paulo')
data_atual = datetime.now(tz).date()  # Obtém a data e hora atuais com o fuso horário definido

# Funções utilitárias
def remover_acentos(texto):
    """Remove acentos de um texto."""
    return ''.join(
        c for c in unicodedata.normalize('NFD', texto)
        if unicodedata.category(c) != 'Mn'
    )

# ---------------------------------------------------------------------
# Rotas do aplicativo
# ---------------------------------------------------------------------

# --------------------------- Rota Inicial ----------------------------

@app.route('/')
def home():
    # Contagens de status dos projetos
    total_projetos = Projeto.query.count()
    nao_iniciados = Projeto.query.filter_by(status='Não iniciado').count()
    pendentes = Projeto.query.filter_by(status='Pendente').count()
    em_andamento = Projeto.query.filter_by(status='Em andamento').count()
    concluidos = Projeto.query.filter_by(status='Concluído').count()
    cancelados = Projeto.query.filter_by(status='Cancelado').count()

    # Contagem de moradores e beneficiados
    total_moradores = Morador.query.count()
    moradores_beneficiados = Morador.query.filter_by(beneficio=True).count()

    # Compromissos de hoje e da semana
    hoje = datetime.now().date()
    semana_futura = hoje + timedelta(days=7)
    compromissos_hoje = Compromisso.query.filter(Compromisso.data == hoje).order_by(Compromisso.hora).all()
    compromissos_semana = Compromisso.query.filter(Compromisso.data > hoje, Compromisso.data <= semana_futura).order_by(Compromisso.data, Compromisso.hora).all()

    return render_template(
        'index.html',
        nao_iniciados=nao_iniciados,
        total_projetos=total_projetos,
        pendentes=pendentes,
        em_andamento=em_andamento,
        concluidos=concluidos,
        cancelados=cancelados,
        total_moradores=total_moradores,
        moradores_beneficiados=moradores_beneficiados,
        compromissos_hoje=compromissos_hoje,
        compromissos_semana=compromissos_semana
    )


# --------------------------- Estoque ---------------------------------

@app.route('/cadastrar_item', methods=['GET', 'POST'])
def cadastrar_item():
    """Rota para cadastrar um novo item no estoque."""
    if request.method == 'POST':
        nome = request.form['nome']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        quantidade = int(request.form['quantidade'])
        preco = float(request.form['preco'])

        # Verifica se a quantidade ou preço são negativos
        if quantidade < 0 or preco < 0:
            error = "Quantidade e preço não podem ser negativos!"
            return render_template(
                'cadastrar_item.html',
                error=error,
                nome=nome,
                descricao=descricao,
                categoria=categoria,
                quantidade=quantidade,
                preco=preco
            )

        # Verifica se já existe um item com o mesmo nome no banco de dados
        item_existente = Item.query.filter_by(nome=nome).first()
        if item_existente:
            # Retorna uma mensagem de erro se o item já existir
            error = "Item já cadastrado!"
            return render_template(
                'cadastrar_item.html',
                error=error,
                nome=nome,
                descricao=descricao,
                categoria=categoria,
                quantidade=quantidade,
                preco=preco
            )

        # Caso não exista, cria um novo item
        novo_item = Item(
            nome=nome,
            descricao=descricao,
            categoria=categoria,
            quantidade=quantidade,
            preco=preco
        )
        db.session.add(novo_item)
        db.session.commit()

        # Exibe uma mensagem de sucesso
        # flash("Item cadastrado com sucesso!", "success")
        flash("Item cadastrado com sucesso!", "item_sucesso")

        # Retorna para a página de cadastro com os campos limpos
        return render_template('cadastrar_item.html')

    return render_template('cadastrar_item.html')

@app.route('/entrada', methods=['GET', 'POST']) 
def entrada_item():
    """Rota para registrar a entrada de itens."""
    if request.method == 'POST':
        item_id = request.form['item_id']
        quantidade_entrada = int(request.form['quantidade'])

        # Valida a quantidade de entrada
        if quantidade_entrada < 1:
            return jsonify({'success': False, 'error': 'A quantidade deve ser maior ou igual a 1.'})

        # Atualiza a quantidade do item no estoque
        item = Item.query.get(item_id)
        item.quantidade += quantidade_entrada
        db.session.commit()

        # Captura a data e hora atuais com o fuso horário correto
        data_hora_atual = datetime.now(tz)

        # Registra a movimentação de entrada
        movimentacao = MovimentacaoEstoque(
            item_id=item_id,
            tipo_movimentacao='entrada',
            quantidade=quantidade_entrada,
            saldo_atual=item.quantidade,
            data_hora=data_hora_atual
        )
        db.session.add(movimentacao)
        db.session.commit()

        # Retorna a resposta de sucesso como JSON
        return jsonify({'success': True, 'item': item.nome, 'quantidade': quantidade_entrada})

    # Se for GET, exibe o formulário normalmente
    itens = Item.query.all()
    entradas = session.get('entradas', [])
    # Remove as entradas da sessão após exibi-las
    session.pop('entradas', None)

    return render_template('entrada_item.html', itens=itens, entradas=entradas)

@app.route('/saida', methods=['GET', 'POST'])
def saida_item():
    """Rota para registrar a saída de itens."""
    if request.method == 'POST':
        item_id = request.form['item_id']
        quantidade_saida = int(request.form['quantidade'])
        justificativa = request.form['justificativa']

        # Verifica se a quantidade de saída é um número positivo
        if quantidade_saida <= 0:
            return jsonify({'success': False, 'error': 'A quantidade de saída deve ser maior que zero.'})

        # Atualiza a quantidade do item no estoque
        item = Item.query.get(item_id)
        if item.quantidade >= quantidade_saida:
            item.quantidade -= quantidade_saida
            db.session.commit()

            # Captura a data e hora atuais com o fuso horário correto
            data_hora_atual = datetime.now(tz)

            # Registra a movimentação de saída
            movimentacao = MovimentacaoEstoque(
                item_id=item_id,
                tipo_movimentacao='saida',
                quantidade=quantidade_saida,
                saldo_atual=item.quantidade,
                justificativa=justificativa,
                data_hora=data_hora_atual
            )
            db.session.add(movimentacao)
            db.session.commit()

            # Retorna a resposta de sucesso como JSON
            return jsonify({
                'success': True,
                'item': item.nome,
                'quantidade': quantidade_saida,
                'justificativa': justificativa
            })
        else:
            return jsonify({'success': False, 'error': 'Quantidade insuficiente em estoque.'})

    # Para requisições GET, exibe o formulário normalmente
    itens = Item.query.all()
    return render_template('saida_item.html', itens=itens)

@app.route('/estoque')
def estoque_atual():
    """Rota para exibir o estoque atual."""
    busca = request.args.get('busca', '')  # Termo de busca, se houver
    categoria = request.args.get('categoria', '')  # Categoria selecionada, se houver

    # Busca inicial de todos os itens
    itens = Item.query.all()

    # Aplicar filtro de busca por nome, insensível a acentos
    if busca:
        busca_sem_acentos = remover_acentos(busca).lower()
        itens = [
            item for item in itens
            if busca_sem_acentos in remover_acentos(item.nome).lower()
        ]

    # Aplicar filtro por categoria, se uma categoria foi selecionada
    if categoria and categoria != 'todas':
        itens = [item for item in itens if item.categoria == categoria]

    # Obter todas as categorias únicas para o filtro de categoria no frontend
    categorias = list(set([item.categoria for item in Item.query.all()]))

    return render_template('estoque_atual.html', itens=itens, categorias=categorias)

@app.route('/movimentacoes', methods=['GET'])
def movimentacoes_estoque():
    """Rota para exibir as movimentações de estoque com filtros."""
    periodo = request.args.get('periodo')  # Filtro de período
    tipo_movimentacao = request.args.get('tipo_movimentacao', 'todos')
    nome_item = request.args.get('nome_item', '').strip()

    # Query básica para obter todas as movimentações
    query = MovimentacaoEstoque.query.join(Item)

    hoje = datetime.now(tz).date()  # Data de hoje no fuso horário definido

    # Filtros baseados no período selecionado
    if periodo == 'hoje':
        query = query.filter(db.func.date(MovimentacaoEstoque.data_hora) == hoje)
    elif periodo == 'semana':
        inicio_semana = hoje - timedelta(days=hoje.weekday())
        query = query.filter(MovimentacaoEstoque.data_hora >= inicio_semana)
    elif periodo == 'mes':
        query = query.filter(
            db.extract('month', MovimentacaoEstoque.data_hora) == hoje.month,
            db.extract('year', MovimentacaoEstoque.data_hora) == hoje.year
        )
    elif periodo == 'ano':
        query = query.filter(db.extract('year', MovimentacaoEstoque.data_hora) == hoje.year)
    elif periodo == 'ultimos_30_dias':
        ultimos_30_dias = hoje - timedelta(days=30)
        query = query.filter(MovimentacaoEstoque.data_hora >= ultimos_30_dias)
    elif periodo == 'ultimos_12_meses':
        ultimos_12_meses = hoje.replace(year=hoje.year - 1)
        query = query.filter(MovimentacaoEstoque.data_hora >= ultimos_12_meses)
    elif periodo == 'personalizado':
        data_inicio = request.args.get('data_inicio')
        data_fim = request.args.get('data_fim')
        if data_inicio and data_fim:
            try:
                data_inicio_dt = datetime.strptime(data_inicio, '%Y-%m-%d')
                data_fim_dt = datetime.strptime(data_fim, '%Y-%m-%d')
                query = query.filter(
                    MovimentacaoEstoque.data_hora >= data_inicio_dt,
                    MovimentacaoEstoque.data_hora <= data_fim_dt
                )
            except ValueError:
                return "Formato de data inválido, use o formato AAAA-MM-DD.", 400

    # Filtro por tipo de movimentação
    if tipo_movimentacao in ['entrada', 'saida']:
        query = query.filter(MovimentacaoEstoque.tipo_movimentacao == tipo_movimentacao)

    # Executa a query com os filtros aplicados
    movimentacoes = query.order_by(MovimentacaoEstoque.data_hora.desc()).all()

    # Filtro adicional por nome do item
    if nome_item:
        nome_item_normalizado = remover_acentos(nome_item).lower()
        movimentacoes = [
            m for m in movimentacoes
            if remover_acentos(m.item.nome).lower().find(nome_item_normalizado) != -1
        ]

    return render_template('movimentacoes.html', movimentacoes=movimentacoes, tz=tz)

# --------------------------- Projetos ---------------------------------

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_projeto():
    """Rota para cadastrar um novo projeto."""
    if request.method == 'POST':
        nome = request.form.get('nome')
        descricao = request.form.get('descricao')
        prioridade = request.form.get('prioridade')
        previsao_termino_str = request.form.get('previsao_termino')
        responsavel = request.form.get('responsavel')
        status = request.form.get('status')
        orcamento_str = request.form.get('orcamento')

        # Converte a previsão de término para datetime.date
        if previsao_termino_str:
            previsao_termino = datetime.strptime(previsao_termino_str, '%Y-%m-%d').date()
        else:
            previsao_termino = None

        # Converte o orçamento para float
        if orcamento_str:
            try:
                orcamento = float(orcamento_str)
            except ValueError:
                error = "O orçamento deve ser um número válido."
                return render_template(
                    'cadastrar_projeto.html',
                    error=error,
                    nome=nome,
                    descricao=descricao,
                    prioridade=prioridade,
                    previsao_termino=previsao_termino_str,
                    responsavel=responsavel,
                    status=status,
                    orcamento=orcamento_str
                )
        else:
            orcamento = None

        # Verifica se o orçamento é negativo
        if orcamento is not None and orcamento < 0:
            error = "O orçamento não pode ser negativo!"
            return render_template(
                'cadastrar_projeto.html',
                error=error,
                nome=nome,
                descricao=descricao,
                prioridade=prioridade,
                previsao_termino=previsao_termino_str,
                responsavel=responsavel,
                status=status,
                orcamento=orcamento_str
            )

        # Cria um novo projeto
        novo_projeto = Projeto(
            nome=nome,
            descricao=descricao,
            prioridade=prioridade,
            previsao_termino=previsao_termino,
            responsavel=responsavel,
            status=status,
            orcamento=orcamento
        )
        db.session.add(novo_projeto)
        db.session.commit()

        flash("Projeto cadastrado com sucesso!", "success")
        return redirect(url_for('acompanhar_status'))

    return render_template('cadastrar_projeto.html')

@app.route('/status', methods=['GET'])
def acompanhar_status():
    """Rota para acompanhar o status dos projetos."""
    nome_filtro = request.args.get('nome', '')
    data_filtro = request.args.get('data', '')

    # Filtros de checkbox de status
    filtro_nao_iniciado = request.args.get('Não iniciado')
    filtro_atrasado = request.args.get('atrasado')
    filtro_concluido = request.args.get('concluido')
    filtro_em_andamento = request.args.get('em_andamento')
    filtro_pendente = request.args.get('pendente')
    filtro_cancelado = request.args.get('cancelado')

    # Query básica para obter todos os projetos
    query = Projeto.query

    # Aplica o filtro por nome, se fornecido
    if nome_filtro:
        query = query.filter(Projeto.nome.ilike(f'%{nome_filtro}%'))

    # Aplica o filtro por data de previsão de término
    if data_filtro:
        query = query.filter(Projeto.previsao_termino == data_filtro)

    # Lista para armazenar condições de status
    status_filtros = []

    # Filtro para projetos atrasados
    if filtro_atrasado:
        query = query.filter(
            Projeto.previsao_termino < date.today(),
            Projeto.status != 'Concluído'
        )

    # Filtros para outros status
    if filtro_nao_iniciado:
        status_filtros.append('Não iniciado')
    if filtro_concluido:
        status_filtros.append('Concluído')
    if filtro_em_andamento:
        status_filtros.append('Em andamento')
    if filtro_pendente:
        status_filtros.append('Pendente')
    if filtro_cancelado:
        status_filtros.append('Cancelado')

    # Aplica os filtros de status, se houver
    if status_filtros:
        query = query.filter(Projeto.status.in_(status_filtros))

    # Obter os projetos filtrados
    projetos = query.all()

    # Atualiza o status para 'Atrasado' se o projeto estiver atrasado
    for projeto in projetos:
        if projeto.previsao_termino < date.today() and projeto.status != 'Concluído':
            projeto.status = 'Atrasado'

    return render_template('acompanhar_status.html', projetos=projetos)

@app.route('/editar/<int:projeto_id>', methods=['GET', 'POST'])
def editar_projeto(projeto_id):
    """Rota para editar um projeto."""
    projeto = Projeto.query.get_or_404(projeto_id)

    # Consulta os comentários relacionados ao projeto
    comentarios = Comentario.query.filter_by(projeto_id=projeto_id).all()

    if request.method == 'POST':
        comentario_conteudo = request.form['comentario']

        # Verifica se o comentário tem pelo menos 10 caracteres
        if len(comentario_conteudo) < 10:
            error = "O comentário deve ter no mínimo 10 caracteres."
            return render_template(
                'editar_projeto.html',
                projeto=projeto,
                comentarios=comentarios,
                error=error
            )

        # Atualiza os dados do projeto
        projeto.prioridade = request.form['prioridade']
        projeto.status = request.form['status']

        # Cria um novo comentário
        novo_comentario = Comentario(
            conteudo=comentario_conteudo,
            projeto_id=projeto.id
        )
        db.session.add(novo_comentario)
        db.session.commit()

        return redirect(url_for('acompanhar_status'))

    return render_template('editar_projeto.html', projeto=projeto, comentarios=comentarios)

@app.route('/comentarios/<int:projeto_id>')
def ver_comentarios(projeto_id):
    """Rota para visualizar os comentários de um projeto."""
    projeto = Projeto.query.get_or_404(projeto_id)
    comentarios = Comentario.query.filter_by(projeto_id=projeto_id).all()
    return render_template('comentarios.html', projeto=projeto, comentarios=comentarios)

# --------------------------- Cestas Básicas ----------------------------

@app.route('/cestas')
def cestas():
    """Página inicial mostrando quantas cestas podem ser geradas com base nos itens em estoque."""
    # Obtém os itens do banco de dados
    arroz = Item.query.filter_by(nome='Arroz Branco - 1 Kg').first()
    feijao = Item.query.filter_by(nome='Feijão - 1 Kg').first()
    acucar = Item.query.filter_by(nome='Açucar - 1 Kg').first()
    macarrao = Item.query.filter_by(nome='Macarrão espaguete - 500 g').first()
    sal = Item.query.filter_by(nome='Sal - 1 Kg').first()
    oleo = Item.query.filter_by(nome='Óleo de soja - 900 ml').first()
    molho = Item.query.filter_by(nome='Molho de Tomate - 340 g').first()
    farinha = Item.query.filter_by(nome='Farinha de trigo - 1 Kg').first()
    sardinha = Item.query.filter_by(nome='Sardinha em lata').first()
    fuba = Item.query.filter_by(nome='Fubá - 1 Kg').first()
    cafe = Item.query.filter_by(nome='Pó de café - 500g').first()

    # Calcula o número máximo de cestas com base nos itens em estoque
    if all([
        arroz, feijao, acucar, macarrao, sal, oleo, molho,
        farinha, sardinha, fuba, cafe
    ]):
        max_cestas = min(
            arroz.quantidade, feijao.quantidade, acucar.quantidade,
            macarrao.quantidade, sal.quantidade, oleo.quantidade,
            molho.quantidade, farinha.quantidade, sardinha.quantidade,
            fuba.quantidade, cafe.quantidade
        )
    else:
        max_cestas = 0

    return render_template('cestas.html', max_cestas=max_cestas)

@app.route('/gerar_cestas', methods=['POST'])
def gerar_cestas():
    """Rota para gerar cestas básicas."""
    qtd_cestas = int(request.form['quantidade'])

    # Verifica se a quantidade de cestas é maior que zero
    if qtd_cestas <= 0:
        flash("A quantidade de cestas deve ser maior que zero.", 'danger')
        return redirect(url_for('cestas'))

    # Obtém os itens do banco de dados
    arroz = Item.query.filter_by(nome='Arroz Branco - 1 Kg').first()
    feijao = Item.query.filter_by(nome='Feijão - 1 Kg').first()
    acucar = Item.query.filter_by(nome='Açucar - 1 Kg').first()
    macarrao = Item.query.filter_by(nome='Macarrão espaguete - 500 g').first()
    sal = Item.query.filter_by(nome='Sal - 1 Kg').first()
    oleo = Item.query.filter_by(nome='Óleo de soja - 900 ml').first()
    molho = Item.query.filter_by(nome='Molho de Tomate - 340 g').first()
    farinha = Item.query.filter_by(nome='Farinha de trigo - 1 Kg').first()
    sardinha = Item.query.filter_by(nome='Sardinha em lata').first()
    fuba = Item.query.filter_by(nome='Fubá - 1 Kg').first()
    cafe = Item.query.filter_by(nome='Pó de café - 500g').first()

    itens_faltantes = []

    # Verifica se há quantidade suficiente de cada item para gerar as cestas
    for item, nome in [
        (arroz, 'Arroz'), (feijao, 'Feijão'), (acucar, 'Açúcar'),
        (macarrao, 'Macarrão'), (sal, 'Sal'), (oleo, 'Óleo de soja'),
        (molho, 'Molho de Tomate'), (farinha, 'Farinha'),
        (sardinha, 'Sardinha'), (fuba, 'Fubá'), (cafe, 'Café')
    ]:
        if item is None or item.quantidade < qtd_cestas:
            quantidade_faltante = 0 if item is None else qtd_cestas - item.quantidade
            itens_faltantes.append(f'{nome} (faltam {quantidade_faltante} unidades)')

    # Se algum item estiver faltando, exibe uma mensagem de erro
    if itens_faltantes:
        itens_formatados = [f"• {item}" for item in itens_faltantes]
        flash(
            "Os seguintes itens estão faltando ou não possuem quantidade suficiente:<br>"
            f"{'<br>'.join(itens_formatados)}", 'danger'
        )
        return redirect(url_for('cestas'))

    # Captura a data e hora atuais com o fuso horário correto
    data_hora_atual = datetime.now(tz)

    # Atualiza o estoque e registra a movimentação de saída
    itens = [
        (arroz, 'Arroz Branco - 1 Kg'),
        (feijao, 'Feijão - 1 Kg'),
        (acucar, 'Açucar - 1 Kg'),
        (macarrao, 'Macarrão espaguete - 500 g'),
        (sal, 'Sal - 1 Kg'),
        (oleo, 'Óleo de soja - 900 ml'),
        (molho, 'Molho de Tomate - 340 g'),
        (farinha, 'Farinha de trigo - 1 Kg'),
        (sardinha, 'Sardinha em lata'),
        (fuba, 'Fubá - 1 Kg'),
        (cafe, 'Pó de café - 500g')
    ]

    for item, nome in itens:
        item.quantidade -= qtd_cestas
        movimentacao = MovimentacaoEstoque(
            item_id=item.id,
            tipo_movimentacao='saida',
            quantidade=qtd_cestas,
            saldo_atual=item.quantidade,
            justificativa='Geração de cestas básicas',
            data_hora=data_hora_atual
        )
        db.session.add(movimentacao)

    db.session.commit()

    flash(f'{qtd_cestas} cesta(s) básica(s) gerada(s) com sucesso!', 'success')
    return redirect(url_for('cestas'))

@app.route('/cestas_personalizadas')
def cestas_personalizadas():
    """Rota para cestas básicas personalizadas."""
    # Obtém todos os itens do estoque
    itens = Item.query.all()
    return render_template('cestas_personalizadas.html', itens=itens)

@app.route('/gerar_cestas_personalizadas', methods=['POST'])
def gerar_cestas_personalizadas():
    """Rota para gerar cestas básicas personalizadas."""
    qtd_cestas = int(request.form['quantidade'])
    itens_selecionados_ids = request.form.getlist('itens_selecionados')

    if qtd_cestas <= 0:
        flash("A quantidade de cestas deve ser maior que zero.", 'danger')
        return redirect(url_for('cestas_personalizadas'))

    if not itens_selecionados_ids:
        flash("Selecione pelo menos um item para incluir na cesta básica.", 'danger')
        return redirect(url_for('cestas_personalizadas'))

    # Obter os itens selecionados
    itens_selecionados = Item.query.filter(Item.id.in_(itens_selecionados_ids)).all()

    # Verificar a quantidade disponível de cada item
    itens_faltantes = []
    max_cestas_possiveis = qtd_cestas
    for item in itens_selecionados:
        if item.quantidade < qtd_cestas:
            itens_faltantes.append(f"{item.nome} (disponível: {item.quantidade})")
            if item.quantidade < max_cestas_possiveis:
                max_cestas_possiveis = item.quantidade

    if itens_faltantes:
        flash(f"Quantidade insuficiente dos seguintes itens: {', '.join(itens_faltantes)}", 'danger')
        if max_cestas_possiveis and max_cestas_possiveis > 0:
            flash(
                f"Você pode gerar até {max_cestas_possiveis} cesta(s) com os itens selecionados.",
                'info'
            )
        return redirect(url_for('cestas_personalizadas'))

    # Atualizar o estoque e registrar as movimentações
    data_hora_atual = datetime.now(tz)

    for item in itens_selecionados:
        item.quantidade -= qtd_cestas
        movimentacao = MovimentacaoEstoque(
            item_id=item.id,
            tipo_movimentacao='saida',
            quantidade=qtd_cestas,
            saldo_atual=item.quantidade,
            justificativa='Geração de cestas básicas personalizadas',
            data_hora=data_hora_atual
        )
        db.session.add(movimentacao)

    db.session.commit()

    flash(f'{qtd_cestas} cesta(s) básica(s) personalizada(s) gerada(s) com sucesso!', 'success')
    return redirect(url_for('cestas_personalizadas'))


@app.route('/cadastrar_morador', methods=['GET', 'POST'])
def cadastrar_morador():
    if request.method == 'POST':
        nome = request.form['nome']
        cpf = request.form['cpf']
        apelido = request.form.get('apelido')
        endereco = request.form['endereco']
        beneficio = request.form['beneficio'] == 'sim'

        # Função para formatar o CPF
        def formatar_cpf(cpf):
            cpf = ''.join(filter(str.isdigit, cpf))  # Remove tudo que não for número
            return f'{cpf[:3]}.{cpf[3:6]}.{cpf[6:9]}-{cpf[9:]}'

        cpf = formatar_cpf(cpf)

        # Verifica se já existe um morador com o mesmo CPF
        morador_existente = Morador.query.filter_by(cpf=cpf).first()
        if morador_existente:
            error = "CPF já cadastrado!"
            return render_template(
                'cadastrar_morador.html',
                error=error,
                nome=nome,
                cpf=cpf,
                apelido=apelido,
                endereco=endereco,
                beneficio=beneficio
            )

        # Cria um novo morador
        novo_morador = Morador(
            nome=nome,
            cpf=cpf,
            apelido=apelido,
            endereco=endereco,
            beneficio=beneficio
        )
        db.session.add(novo_morador)
        db.session.commit()

        flash("Morador cadastrado com sucesso!", "success")
        return redirect(url_for('listar_moradores'))

    return render_template('cadastrar_morador.html')



@app.route('/listar_moradores', methods=['GET'])
def listar_moradores():
    beneficio_filtro = request.args.get('beneficio')
    busca = request.args.get('busca', '').strip()

    query = Morador.query

    # Aplicando o filtro de benefício
    if beneficio_filtro == 'sim':
        query = query.filter_by(beneficio=True)
    elif beneficio_filtro == 'nao':
        query = query.filter_by(beneficio=False)

    # Aplicando a busca por nome, apelido ou CPF
    if busca:
        query = query.filter(
            Morador.nome.ilike(f'%{busca}%') | 
            Morador.apelido.ilike(f'%{busca}%') |
            Morador.cpf.ilike(f'%{busca}%')
        )

    moradores = query.all()

    return render_template('listar_moradores.html', moradores=moradores)





@app.route('/editar_morador/<int:morador_id>', methods=['GET', 'POST'])
def editar_morador(morador_id):
    morador = Morador.query.get_or_404(morador_id)

    if request.method == 'POST':
        morador.nome = request.form['nome']
        morador.cpf = request.form['cpf']
        morador.apelido = request.form.get('apelido')
        morador.endereco = request.form['endereco']
        morador.beneficio = request.form['beneficio'] == 'sim'

        db.session.commit()
        flash("Morador atualizado com sucesso!", "success")
        return redirect(url_for('listar_moradores'))

    return render_template('editar_morador.html', morador=morador)


@app.route('/remover_morador/<int:morador_id>', methods=['POST'])
def remover_morador(morador_id):
    morador = Morador.query.get_or_404(morador_id)
    db.session.delete(morador)
    db.session.commit()
    flash("Morador removido com sucesso!", "success")
    return redirect(url_for('listar_moradores'))

@app.route('/agendar', methods=['GET', 'POST'])
def agendar_compromisso():
    """Rota para agendar compromissos."""
    if request.method == 'POST':
        nome_compromisso = request.form['nome_compromisso']
        data = request.form['data']
        hora = request.form['hora']
        observacoes = request.form.get('observacoes', '')  # Observações são opcionais

        # Validação da data e hora
        try:
            data_formatada = datetime.strptime(data, '%Y-%m-%d').date()
            hora_formatada = datetime.strptime(hora, '%H:%M').time()
        except ValueError:
            flash('Data ou hora inválida. Por favor, insira corretamente.', 'danger')
            return redirect(url_for('agendar_compromisso'))

        # Verifica se a data/hora está no passado
        agora = datetime.now()
        data_hora_compromisso = datetime.combine(data_formatada, hora_formatada)
        if data_hora_compromisso < agora:
            flash('Não é possível agendar um compromisso no passado.', 'danger')
            return redirect(url_for('agendar_compromisso'))

        # Criando um novo compromisso
        novo_compromisso = Compromisso(
            nome_compromisso=nome_compromisso,
            data=data_formatada,
            hora=hora_formatada,
            observacoes=observacoes
        )

        # Salvando no banco de dados
        db.session.add(novo_compromisso)
        db.session.commit()

        flash('Compromisso agendado com sucesso!', 'success')
        return redirect(url_for('agendar_compromisso'))

    return render_template('agendar_compromisso.html')

@app.route('/compromissos', methods=['GET'])
def listar_compromissos():
    """Rota para listar compromissos agendados."""
    compromissos = Compromisso.query.order_by(Compromisso.data, Compromisso.hora).all()
    return render_template('listar_compromissos.html', compromissos=compromissos)


# ---------------------------------------------------------------------
# Inicialização da aplicação
# ---------------------------------------------------------------------

if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados se elas não existirem
    app.run(debug=True)  # Inicia o servidor Flask em modo debug
