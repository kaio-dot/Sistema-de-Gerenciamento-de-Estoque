from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_cors import CORS 

app = Flask(__name__)
CORS(app)

app = Flask(__name__)

class Produto:
    def __init__(self, nome, preco, codigo):
        self.nome = nome
        self.preco = preco
        self.codigo = codigo

    def __repr__(self):
        return f'Produto({self.nome}, {self.preco}, {self.codigo})'
    
    def salvar(self):
        with open('produtos.txt', 'a') as arquivo:
            arquivo.write(f'{self.nome},{self.preco},{self.codigo}\n')
    
    @staticmethod
    def carregar_produtos():
        produtos = []
        try:
            with open('produtos.txt', 'r') as arquivo:
                for linha in arquivo:
                    nome, preco, codigo = linha.strip().split(',')
                    produtos.append(Produto(nome, preco, codigo))
        except FileNotFoundError:
            pass  # Se o arquivo não existir, retorna uma lista vazia
        return produtos
    
@app.route('/cadastro', methods=['POST'])
def cadastro():
    # Captura e processa os dados do formulário
    nome = request.form.get('nome')
    preco = request.form.get('preco')
    codigo = request.form.get('codigo')

    if not nome or not preco or not codigo:
        return jsonify({'status': 'error', 'message': 'Dados incompletos'}), 400

    produto = Produto(nome, preco, codigo)
    produto.salvar()
    return jsonify({'status': 'success', 'message': 'Produto cadastrado com sucesso'}), 200

if __name__ == '__main__':
    app.run(debug=True)


