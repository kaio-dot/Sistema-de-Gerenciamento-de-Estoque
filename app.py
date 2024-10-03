from flask import Flask, render_template, request, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app)

# Produto
class Produto:
    def __init__(self, nome, preco, codigo, estoque):
        self.nome = nome
        self.preco = preco
        self.codigo = codigo
        self.estoque = estoque

    def __repr__(self):
        return f'Produto({self.nome}, {self.preco}, {self.codigo}, {self.estoque})'

    @staticmethod
    def carregar_produtos():
        produtos = []
        try:
            with open('produtos.txt', 'r') as arquivo:
                for linha in arquivo:
                    nome, preco, codigo, estoque = linha.strip().split(';')
                    produtos.append(Produto(nome, preco, codigo, estoque))
        except FileNotFoundError:
            pass
        return produtos

    @staticmethod
    def atualizar_estoque(codigo, novo_estoque):
        produtos = Produto.carregar_produtos()
        for produto in produtos:
            if produto.codigo == codigo:
                produto.estoque = str(novo_estoque)
                # Atualiza o arquivo com o novo estoque
                with open('produtos.txt', 'w') as arquivo:
                    for p in produtos:
                        arquivo.write(f'{p.nome};{p.preco};{p.codigo};{p.estoque}\n')
                return True
        return False

# Classe para gerenciar vendas
class Venda:
    vendas_dia = []

    @staticmethod
    def registrar_venda(codigo_produto, quantidade, metodo_pagamento):
        produto = next((p for p in Produto.carregar_produtos() if p.codigo == codigo_produto), None)
        if produto and int(produto.estoque) >= quantidade:
            # Atualiza o estoque
            novo_estoque = int(produto.estoque) - quantidade
            if Produto.atualizar_estoque(codigo_produto, novo_estoque):
                valor_venda = float(produto.preco.replace(',', '.')) * quantidade
                venda_info = {
                    "codigo": codigo_produto,
                    "quantidade": quantidade,
                    "metodo_pagamento": metodo_pagamento,
                    "valor": valor_venda
                }
                Venda.vendas_dia.append(venda_info)
                return f'Venda registrada com sucesso! Total: R$ {valor_venda:.2f}'
        return 'Estoque insuficiente ou produto não encontrado.'

# Carrinho de compras
carrinho = []

# Rota para adicionar produto ao carrinho
@app.route('/adicionar_carrinho', methods=['POST'])
def adicionar_carrinho():
    dados = request.get_json()
    nome_produto = dados['nome_produto']
    quantidade = dados['quantidade']
    
    # Lê os produtos do arquivo
    with open('produtos.txt', 'r') as file:
        produtos = [linha.strip().split(';') for linha in file.readlines()]

    # Procura o produto pelo nome
    for produto in produtos:
        if produto[0] == nome_produto:  # Supondo que o nome do produto está na primeira coluna
            # Substitui vírgula por ponto e converte
            preco = float(produto[1].replace(',', '.'))  # Supondo que o preço está na segunda coluna
            total = preco * quantidade
            
            # Retorna o nome do produto e o preço unitário
            return jsonify({
                'nome_produto': nome_produto,
                'preco_unitario': preco,  # Retorna o preço unitário
                'total': total  # Se precisar do total aqui, mas o total é calculado no frontend
            }), 200
    
    return jsonify({"erro": "Produto não encontrado"}), 404

# Rota para cadastro de produtos
@app.route('/cadastro', methods=['POST'])
def cadastro():
    nome = request.form.get('nome')
    preco = request.form.get('preco')
    codigo = request.form.get('codigo')
    estoque = request.form.get('estoque')

    if not nome or not preco or not codigo or not estoque:
        return jsonify({'status': 'error', 'message': 'Dados incompletos'}), 400

    # Adiciona o produto ao arquivo produtos.txt
    with open('produtos.txt', 'a') as arquivo:
        arquivo.write(f'{nome};{preco};{codigo};{estoque}\n')
        
    return jsonify({'status': 'success', 'message': 'Produto cadastrado com sucesso'}), 200

# Rota para atualização de estoque
@app.route('/atualizar_estoque', methods=['POST'])
def processar_formulario():
    nome_produto = request.form['nome_produto']
    novo_estoque = request.form['estoque']

    try:
        novo_estoque = int(novo_estoque)
    except ValueError:
        return jsonify({'status': 'error', 'message': 'Estoque inválido. Insira um número.'}), 400

    mensagem = atualizar_estoque(nome_produto, novo_estoque)

    if 'atualizado' in mensagem:
        return jsonify({'status': 'success', 'message': mensagem}), 200
    else:
        return jsonify({'status': 'error', 'message': mensagem}), 400

# Função para atualizar estoque
def atualizar_estoque(nome_produto, novo_estoque):
    try:
        with open('produtos.txt', 'r') as arquivo:
            linhas = arquivo.readlines()
    except FileNotFoundError:
        return "Arquivo produtos.txt não encontrado."

    encontrado = False
    novas_linhas = []

    for linha in linhas:
        dados = linha.strip().split(';')
        if len(dados) >= 4 and dados[0].strip() == nome_produto.strip():
            dados[3] = str(novo_estoque)
            encontrado = True
        novas_linhas.append(';'.join(dados))

    if not encontrado:
        return f'Nome de produto "{nome_produto}" não encontrado.'

    with open('produtos.txt', 'w') as arquivo:
        for linha in novas_linhas:
            arquivo.write(linha + '\n')

    return f'Estoque do produto "{nome_produto}" atualizado para {novo_estoque}.'

# Rota para processar a venda
@app.route('/realizar_venda', methods=['POST'])
def processar_venda():
    nome_produto = request.form['nome_produto']
    quantidade = int(request.form['quantidade'])
    metodo_pagamento = request.form['metodo_pagamento']

    # Busca o produto pelo nome em vez do código
    produto = next((p for p in Produto.carregar_produtos() if p.nome == nome_produto), None)
    if produto and int(produto.estoque) >= quantidade:
        # Atualiza o estoque
        novo_estoque = int(produto.estoque) - quantidade
        if Produto.atualizar_estoque(produto.codigo, novo_estoque):  # A atualização ainda usa o código do produto internamente
            valor_venda = float(produto.preco.replace(',', '.')) * quantidade
            venda_info = {
                "nome_produto": nome_produto,
                "quantidade": quantidade,
                "metodo_pagamento": metodo_pagamento,
                "valor": valor_venda
            }
            Venda.vendas_dia.append(venda_info)
            return jsonify({'status': 'success', 'message': f'Venda registrada com sucesso! Total: R$ {valor_venda:.2f}'}), 200

    return jsonify({'status': 'error', 'message': 'Estoque insuficiente ou produto não encontrado.'}), 400

# Rota para finalizar a compra
@app.route('/finalizar_compra', methods=['POST'])
def finalizar_compra():
    dados_carrinho = request.get_json()
    carrinho = dados_carrinho.get('carrinho', [])
    metodo_pagamento = dados_carrinho.get('metodo_pagamento')

    if not carrinho:
        return jsonify({'status': 'error', 'message': 'Carrinho vazio'}), 400

    vendas_realizadas = []
    erros = []

    for item in carrinho:
        nome_produto = item['nome_produto']  # Usando nome do produto ao invés de código
        quantidade = int(item['quantidade'])

        # Busca o produto pelo nome em vez de código
        produto = next((p for p in Produto.carregar_produtos() if p.nome == nome_produto), None)

        if produto:
            # Verifica se há estoque suficiente
            if int(produto.estoque) >= quantidade:
                # Atualiza o estoque
                novo_estoque = int(produto.estoque) - quantidade
                if Produto.atualizar_estoque(produto.codigo, novo_estoque):  # Ainda utiliza o código internamente
                    # Calcula o valor da venda
                    valor_venda = float(produto.preco.replace(',', '.')) * quantidade
                    venda_info = {
                        "nome_produto": nome_produto,
                        "quantidade": quantidade,
                        "metodo_pagamento": metodo_pagamento,
                        "valor": valor_venda
                    }
                    Venda.vendas_dia.append(venda_info)
                    vendas_realizadas.append(venda_info)
                else:
                    erros.append(f"Erro ao atualizar estoque para o produto {nome_produto}")
            else:
                erros.append(f'Estoque insuficiente para o produto: {nome_produto}')
        else:
            erros.append(f'Produto {nome_produto} não encontrado')

    # Se houver vendas registradas
    if vendas_realizadas:
        response = {'status': 'success', 'message': 'Compra finalizada com sucesso!', 'vendas': vendas_realizadas}
        if erros:
            response['errors'] = erros
        return jsonify(response), 200
    else:
        # Se não houver vendas bem-sucedidas
        return jsonify({'status': 'error', 'message': 'Nenhuma venda realizada', 'errors': erros}), 400

# Rota para listar produtos
@app.route('/produtos', methods=['GET'])
def listar_produtos():
    produtos = Produto.carregar_produtos()
    lista_produtos = [
        {
            "nome": p.nome,
            "preco": p.preco,
            "codigo": p.codigo,
            "estoque": p.estoque
        } for p in produtos
    ]
    return jsonify(lista_produtos), 200

# Rota inicial
@app.route('/')
def home():
    return render_template('index.html')

# Rota para carregar produtos
@app.route('/carregar_produtos', methods=['GET'])
def carregar_produtos():
    produtos = Produto.carregar_produtos()
    produtos_json = [{'nome': p.nome, 'preco': p.preco, 'codigo': p.codigo, 'estoque': p.estoque} for p in produtos]
    return jsonify(produtos_json)

# Lista para armazenar as vendas
vendas = []

# Função para calcular o resumo das vendas
def obter_resumo_vendas():
    resumo = {
        'total_vendas': len(vendas),
        'vendas_fiado': sum(1 for venda in vendas if venda['metodo_pagamento'] == 'fiado'),
        'vendas_dinheiro': sum(1 for venda in vendas if venda['metodo_pagamento'] == 'dinheiro'),
        'vendas_cartao': sum(1 for venda in vendas if venda['metodo_pagamento'] == 'cartao'),
        'vendas_pix': sum(1 for venda in vendas if venda['metodo_pagamento'] == 'pix'),
        'valor_total': sum(venda['valor_total'] for venda in vendas)
    }
    return resumo

vendas = []  # Lista para armazenar as vendas

@app.route('/adicionar_venda', methods=['POST'])
def adicionar_venda():
    dados = request.get_json()
    metodo_pagamento = dados.get('metodo_pagamento')
    valor_total = dados.get('valor_total')
    
    # Adiciona a venda à lista
    vendas.append({
        'metodo_pagamento': metodo_pagamento,
        'valor_total': valor_total
    })
    
    return jsonify({'mensagem': 'Venda adicionada com sucesso!'}), 200

@app.route('/vendas_dia', methods=['GET'])
def vendas_dia():
    resumo_vendas = obter_resumo_vendas()  # Chama a função que retorna o resumo
    return jsonify(resumo_vendas), 200

if __name__ == '__main__':
    app.run(port=5000, debug=True)
