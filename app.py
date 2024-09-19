from flask import Flask, render_template, request, redirect, url_for, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from models import db, Item, MovimentacaoEstoque, Projeto, Comentario  # Importe os modelos necessários
from datetime import datetime, date, timedelta
import pytz
import unicodedata  # Importa módulo para remover acentos
from flask import jsonify  # Importa jsonify para retornar respostas em JSON

# Função para remover acentos de um texto
def remover_acentos(texto):
    return ''.join(c for c in unicodedata.normalize('NFD', texto) if unicodedata.category(c) != 'Mn')



# Definir o fuso horário correto
tz = pytz.timezone('America/Sao_Paulo')
data_atual = datetime.now(tz).date()  # Obtém a data e hora atuais com o fuso horário definido

app = Flask(__name__)

app.config['SECRET_KEY'] = 'xablau' 

# Configurações do banco de dados
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///projetos.db'  # Define o banco de dados SQLite
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False  # Desativa rastreamento de modificações (melhora a performance)

db.init_app(app)  # Inicializa o banco de dados com o Flask app
migrate = Migrate(app, db)  # Inicializa o sistema de migração do banco de dados


#-------------------------------------------------------------------------ROTAS----------------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------ESTOQUE----------------------------------------------------------------------------------------------------

# Rota para a página inicial
@app.route('/')
def home():
    return render_template('index.html')  # Renderiza o template 'index.html'

# Rota para cadastrar um novo item no estoque
@app.route('/cadastrar_item', methods=['GET', 'POST'])
def cadastrar_item():
    if request.method == 'POST':  # Se a requisição for POST, processa o formulário
        nome = request.form['nome']
        descricao = request.form['descricao']
        categoria = request.form['categoria']
        quantidade = int(request.form['quantidade'])
        preco = float(request.form['preco'])

        # Verifica se a quantidade ou preço são negativos
        if quantidade < 0 or preco < 0:
            return render_template('cadastrar_item.html', error="Quantidade e preço não podem ser negativos!", nome=nome, descricao=descricao, categoria=categoria, quantidade=quantidade, preco=preco)

        # Verifica se já existe um item com o mesmo nome no banco de dados
        item_existente = Item.query.filter_by(nome=nome).first()
        if item_existente:
            # Retorna uma mensagem de erro se o item já existir
            return render_template('cadastrar_item.html', error="Item já cadastrado!", nome=nome, descricao=descricao, categoria=categoria, quantidade=quantidade, preco=preco)

        # Caso não exista, cria um novo item
        novo_item = Item(nome=nome, descricao=descricao, categoria=categoria, quantidade=quantidade, preco=preco)
        db.session.add(novo_item)  # Adiciona o item ao banco de dados
        db.session.commit()  # Confirma a transação

        # Exibe uma mensagem de sucesso
        flash("Item cadastrado com sucesso!", "success")

        # Retorna para a página de cadastro com os campos limpos
        return render_template('cadastrar_item.html')

    return render_template('cadastrar_item.html')  # Se for GET, exibe o formulário de cadastro


# Rota para registrar a entrada de itens


from datetime import datetime
import pytz

@app.route('/entrada', methods=['GET', 'POST']) 
def entrada_item():
    if request.method == 'POST':  # Se a requisição for POST, processa a entrada de itens
        item_id = request.form['item_id']
        quantidade_entrada = int(request.form['quantidade'])

        # Valida a quantidade de entrada
        if quantidade_entrada < 1:
            return jsonify({'success': False, 'error': 'A quantidade deve ser maior ou igual a 1.'})

        # Atualiza a quantidade do item no estoque
        item = Item.query.get(item_id)
        item.quantidade += quantidade_entrada
        db.session.commit()  # Confirma a transação

        # Captura a data e hora atuais com o fuso horário correto
        tz = pytz.timezone('America/Sao_Paulo')
        data_hora_atual = datetime.now(tz)

        # Registra a movimentação de entrada com o saldo atual e a data/hora correta
        movimentacao = MovimentacaoEstoque(
            item_id=item_id,
            tipo_movimentacao='entrada',
            quantidade=quantidade_entrada,
            saldo_atual=item.quantidade,  # Armazena o saldo atualizado após a entrada
            data_hora=data_hora_atual  # Armazena a data e hora corretas
        )
        db.session.add(movimentacao)
        db.session.commit()

        # Retorna a resposta de sucesso como JSON
        return jsonify({'success': True, 'item': item.nome, 'quantidade': quantidade_entrada})

    # Se for GET, exibe o formulário normalmente
    itens = Item.query.all()  # Obtém todos os itens do banco de dados
    entradas = session.get('entradas', [])  # Obtém as entradas armazenadas na sessão

    # Remove as entradas da sessão após exibi-las
    session.pop('entradas', None)

    return render_template('entrada_item.html', itens=itens, entradas=entradas)  # Renderiza o template com os itens



@app.route('/saida', methods=['GET', 'POST'])
def saida_item():
    if request.method == 'POST':  # Se a requisição for POST, processa a saída de itens
        item_id = request.form['item_id']
        quantidade_saida = int(request.form['quantidade'])
        justificativa = request.form['justificativa']  # Coleta a justificativa do formulário

        # Verifica se a quantidade de saída é um número positivo
        if quantidade_saida <= 0:
            return "A quantidade de saída deve ser maior que zero.", 400  # Retorna um erro se a quantidade for inválida

        # Atualiza a quantidade do item no estoque
        item = Item.query.get(item_id)
        if item.quantidade >= quantidade_saida:  # Verifica se há quantidade suficiente no estoque
            item.quantidade -= quantidade_saida
            db.session.commit()  # Confirma a transação

            # Captura a data e hora atuais com o fuso horário correto
            tz = pytz.timezone('America/Sao_Paulo')
            data_hora_atual = datetime.now(tz)

            # Registra a movimentação de saída com o saldo atual, a justificativa e o horário correto
            movimentacao = MovimentacaoEstoque(
                item_id=item_id,
                tipo_movimentacao='saida',
                quantidade=quantidade_saida,
                saldo_atual=item.quantidade,  # Armazena o saldo atualizado após a saída
                justificativa=justificativa,  # Armazena a justificativa fornecida
                data_hora=data_hora_atual  # Armazena a data e hora corretas
            )
            db.session.add(movimentacao)
            db.session.commit()

        else:
            return "Quantidade insuficiente em estoque.", 400  # Retorna mensagem de erro se o estoque for insuficiente

        return redirect(url_for('estoque_atual'))  # Redireciona para a página de estoque

    # Exibe o formulário com os itens disponíveis
    itens = Item.query.all()
    return render_template('saida_item.html', itens=itens)  # Renderiza o template com os itens


# Rota para exibir o estoque atual
@app.route('/estoque')
def estoque_atual():
    busca = request.args.get('busca', '')  # Termo de busca, se houver
    categoria = request.args.get('categoria', '')  # Categoria selecionada, se houver
    
    # Busca inicial de todos os itens
    itens = Item.query.all()
    
    # Aplicar filtro de busca por nome, insensível a acentos
    if busca:
        busca_sem_acentos = remover_acentos(busca).lower()
        itens = [item for item in itens if busca_sem_acentos in remover_acentos(item.nome).lower()]
    
    # Aplicar filtro por categoria, se uma categoria foi selecionada
    if categoria and categoria != 'todas':
        itens = [item for item in itens if item.categoria == categoria]
    
    # Obter todas as categorias únicas para o filtro de categoria no frontend
    categorias = list(set([item.categoria for item in Item.query.all()]))

    return render_template('estoque_atual.html', itens=itens, categorias=categorias)


# Rota para exibir as movimentações de estoque com filtros
@app.route('/movimentacoes', methods=['GET'])


def movimentacoes_estoque():
    periodo = request.args.get('periodo')  # Obtém o filtro de período
    tipo_movimentacao = request.args.get('tipo_movimentacao', 'todos')  # Filtro para o tipo de movimentação
    nome_item = request.args.get('nome_item', '').strip()  # Filtro para o nome do item

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
        query = query.filter(db.extract('month', MovimentacaoEstoque.data_hora) == hoje.month, db.extract('year', MovimentacaoEstoque.data_hora) == hoje.year)
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
                query = query.filter(MovimentacaoEstoque.data_hora >= data_inicio_dt, MovimentacaoEstoque.data_hora <= data_fim_dt)
            except ValueError:
                return "Formato de data inválido, use o formato AAAA-MM-DD.", 400

    # Filtro por tipo de movimentação (entrada ou saída)
    if tipo_movimentacao in ['entrada', 'saida']:
        query = query.filter(MovimentacaoEstoque.tipo_movimentacao == tipo_movimentacao)

    # Executa a query com os filtros aplicados
    movimentacoes = query.order_by(MovimentacaoEstoque.data_hora.desc()).all()

    # Filtro adicional por nome do item
    if nome_item:
        nome_item_normalizado = remover_acentos(nome_item).lower()
        movimentacoes = [m for m in movimentacoes if remover_acentos(m.item.nome).lower().find(nome_item_normalizado) != -1]

    return render_template('movimentacoes.html', movimentacoes=movimentacoes, tz=tz)  # Renderiza o template com as movimentações



#-------------------------------------------------------------------------PROJETOS----------------------------------------------------------------------------------------------------

# Rota para cadastrar um novo projeto
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar_projeto():
    if request.method == 'POST':  # Se a requisição for POST, processa o formulário de cadastro de projeto
        nome = request.form['nome']
        descricao = request.form['descricao']
        prioridade = request.form['prioridade']
        previsao_termino = datetime.strptime(request.form['previsao_termino'], '%Y-%m-%d').date()
        responsavel = request.form['responsavel']
        status = request.form['status']
        orcamento = float(request.form['orcamento']) if request.form['orcamento'] else None

        # Verifica se o orçamento é negativo
        if orcamento is not None and orcamento < 0:
            return render_template('cadastrar_projeto.html', error="O orçamento não pode ser negativo!", nome=nome, descricao=descricao, prioridade=prioridade, previsao_termino=previsao_termino, responsavel=responsavel, status=status, orcamento=orcamento)

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
        db.session.add(novo_projeto)  # Adiciona o projeto ao banco de dados
        db.session.commit()  # Confirma a transação

        return redirect(url_for('acompanhar_status'))  # Redireciona para a página de acompanhamento de status

    return render_template('cadastrar_projeto.html')  # Renderiza o formulário de cadastro de projeto


# Rota para acompanhar o status dos projetos
@app.route('/status', methods=['GET'])
def acompanhar_status():
    nome_filtro = request.args.get('nome', '')  # Filtro por nome de projeto
    data_filtro = request.args.get('data', '')  # Filtro por data

    # Filtros de checkbox de status
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
        query = query.filter(Projeto.previsao_termino < date.today(), Projeto.status != 'Concluído')

    # Filtros para outros status (Concluído, Em andamento, Pendente, Cancelado)
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

    return render_template('acompanhar_status.html', projetos=projetos)  # Renderiza o template com os projetos

# Rota para editar um projeto
@app.route('/editar/<int:projeto_id>', methods=['GET', 'POST'])
def editar_projeto(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)  # Obtém o projeto pelo ID ou retorna 404 se não encontrado

    # Consulta os comentários relacionados ao projeto
    comentarios = Comentario.query.filter_by(projeto_id=projeto_id).all()

    if request.method == 'POST':  # Se a requisição for POST, processa a edição do projeto
        comentario_conteudo = request.form['comentario']

        # Verifica se o comentário tem pelo menos 10 caracteres
        if len(comentario_conteudo) < 10:
            return render_template('editar_projeto.html', projeto=projeto, comentarios=comentarios, error="O comentário deve ter no mínimo 10 caracteres.")

        # Atualiza os dados do projeto
        projeto.prioridade = request.form['prioridade']
        projeto.status = request.form['status']

        # Cria um novo comentário
        novo_comentario = Comentario(conteudo=comentario_conteudo, projeto_id=projeto.id)
        db.session.add(novo_comentario)  # Adiciona o comentário ao banco de dados
        db.session.commit()  # Confirma a transação

        return redirect(url_for('acompanhar_status'))  # Redireciona para a página de acompanhamento de status

    return render_template('editar_projeto.html', projeto=projeto, comentarios=comentarios)  # Renderiza o template de edição de projeto

# Rota para visualizar os comentários de um projeto
@app.route('/comentarios/<int:projeto_id>')
def ver_comentarios(projeto_id):
    projeto = Projeto.query.get_or_404(projeto_id)  # Obtém o projeto pelo ID ou retorna 404 se não encontrado
    comentarios = Comentario.query.filter_by(projeto_id=projeto_id).all()  # Obtém os comentários do projeto
    return render_template('comentarios.html', projeto=projeto, comentarios=comentarios)  # Renderiza o template com os comentários

# Página inicial mostrando quantas cestas podem ser geradas com base nos itens em estoque
@app.route('/cestas')
def cestas():
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
    if all([arroz, feijao, acucar, macarrao, sal, oleo, molho, farinha, sardinha, fuba, cafe]):
        max_cestas = min(
            arroz.quantidade, feijao.quantidade, acucar.quantidade,
            macarrao.quantidade, sal.quantidade, oleo.quantidade,
            molho.quantidade, farinha.quantidade, sardinha.quantidade,
            fuba.quantidade, cafe.quantidade
        )
    else:
        max_cestas = 0

    return render_template('cestas.html', max_cestas=max_cestas)  # Renderiza o template com o número de cestas possíveis


# Rota para gerar cestas básicas
@app.route('/gerar_cestas', methods=['POST'])
def gerar_cestas():
    qtd_cestas = int(request.form['quantidade'])  # Obtém a quantidade de cestas a serem geradas

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

    itens_faltantes = []  # Lista para armazenar itens faltantes

    # Verifica se há quantidade suficiente de cada item para gerar as cestas
    if arroz is None or arroz.quantidade < qtd_cestas:
        quantidade_faltante = 0 if arroz is None else qtd_cestas - arroz.quantidade
        itens_faltantes.append(f'Arroz (faltam {quantidade_faltante} unidades)')
    if feijao is None or feijao.quantidade < qtd_cestas:
        quantidade_faltante = 0 if feijao is None else qtd_cestas - feijao.quantidade
        itens_faltantes.append(f'Feijão (faltam {quantidade_faltante} unidades)')
    if acucar is None or acucar.quantidade < qtd_cestas:
        quantidade_faltante = 0 if acucar is None else qtd_cestas - acucar.quantidade
        itens_faltantes.append(f'Açúcar (faltam {quantidade_faltante} unidades)')
    if macarrao is None or macarrao.quantidade < qtd_cestas:
        quantidade_faltante = 0 if macarrao is None else qtd_cestas - macarrao.quantidade
        itens_faltantes.append(f'Macarrão (faltam {quantidade_faltante} unidades)')
    if sal is None or sal.quantidade < qtd_cestas:
        quantidade_faltante = 0 if sal is None else qtd_cestas - sal.quantidade
        itens_faltantes.append(f'Sal (faltam {quantidade_faltante} unidades)')
    if oleo is None or oleo.quantidade < qtd_cestas:
        quantidade_faltante = 0 if oleo is None else qtd_cestas - oleo.quantidade
        itens_faltantes.append(f'Óleo de soja (faltam {quantidade_faltante} unidades)')
    if molho is None or molho.quantidade < qtd_cestas:
        quantidade_faltante = 0 if molho is None else qtd_cestas - molho.quantidade
        itens_faltantes.append(f'Molho de Tomate (faltam {quantidade_faltante} unidades)')
    if farinha is None or farinha.quantidade < qtd_cestas:
        quantidade_faltante = 0 if farinha is None else qtd_cestas - farinha.quantidade
        itens_faltantes.append(f'Farinha (faltam {quantidade_faltante} unidades)')
    if sardinha is None or sardinha.quantidade < qtd_cestas:
        quantidade_faltante = 0 if sardinha is None else qtd_cestas - sardinha.quantidade
        itens_faltantes.append(f'Sardinha (faltam {quantidade_faltante} unidades)')
    if fuba is None or fuba.quantidade < qtd_cestas:
        quantidade_faltante = 0 if fuba is None else qtd_cestas - fuba.quantidade
        itens_faltantes.append(f'Fubá (faltam {quantidade_faltante} unidades)')
    if cafe is None or cafe.quantidade < qtd_cestas:
        quantidade_faltante = 0 if cafe is None else qtd_cestas - cafe.quantidade
        itens_faltantes.append(f'Café (faltam {quantidade_faltante} unidades)')

    # Se algum item estiver faltando, exibe uma mensagem de erro
    if itens_faltantes:
        flash(f"Os seguintes itens estão faltando ou não possuem quantidade suficiente: {', '.join(itens_faltantes)}", 'danger')
        return redirect(url_for('cestas'))

    # Captura a data e hora atuais com o fuso horário correto
    tz = pytz.timezone('America/Sao_Paulo')
    data_hora_atual = datetime.now(tz)

    # Atualiza o estoque e registra a movimentação de saída com justificativa e data/hora correta
    arroz.quantidade -= qtd_cestas
    feijao.quantidade -= qtd_cestas
    acucar.quantidade -= qtd_cestas
    macarrao.quantidade -= qtd_cestas
    sal.quantidade -= qtd_cestas
    oleo.quantidade -= qtd_cestas
    molho.quantidade -= qtd_cestas
    farinha.quantidade -= qtd_cestas
    sardinha.quantidade -= qtd_cestas
    fuba.quantidade -= qtd_cestas
    cafe.quantidade -= qtd_cestas
    db.session.commit()  # Confirma as alterações no estoque

    # Registrar movimentações de saída com saldo atualizado e data/hora
    movimentacao_arroz = MovimentacaoEstoque(item_id=arroz.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=arroz.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_feijao = MovimentacaoEstoque(item_id=feijao.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=feijao.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_acucar = MovimentacaoEstoque(item_id=acucar.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=acucar.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_macarrao = MovimentacaoEstoque(item_id=macarrao.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=macarrao.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_sal = MovimentacaoEstoque(item_id=sal.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=sal.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_oleo = MovimentacaoEstoque(item_id=oleo.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=oleo.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_molho = MovimentacaoEstoque(item_id=molho.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=molho.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_farinha = MovimentacaoEstoque(item_id=farinha.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=farinha.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_sardinha = MovimentacaoEstoque(item_id=sardinha.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=sardinha.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_fuba = MovimentacaoEstoque(item_id=fuba.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=fuba.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)
    movimentacao_cafe = MovimentacaoEstoque(item_id=cafe.id, tipo_movimentacao='saida', quantidade=qtd_cestas, saldo_atual=cafe.quantidade, justificativa='Geração de cestas básicas', data_hora=data_hora_atual)

    db.session.add_all([movimentacao_arroz, movimentacao_feijao, movimentacao_acucar, movimentacao_macarrao, movimentacao_sal, movimentacao_oleo, movimentacao_molho, movimentacao_farinha, movimentacao_sardinha, movimentacao_fuba, movimentacao_cafe])  # Adiciona todas as movimentações de uma vez
    db.session.commit()  # Confirma as transações

    flash(f'{qtd_cestas} cesta(s) básica(s) gerada(s) com sucesso!', 'success')  # Exibe mensagem de sucesso
    return redirect(url_for('cestas'))



# Inicializa o banco de dados e roda o aplicativo Flask
if __name__ == '__main__':
    with app.app_context():
        db.create_all()  # Cria as tabelas no banco de dados se elas não existirem
    app.run(debug=True)  # Inicia o servidor Flask em modo debug
