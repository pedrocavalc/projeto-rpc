# Projeto RPC
# 🕹️ Seega - Jogo de Tabuleiro Multiplayer em Python (Pyro5/RPC)
Este projeto é uma implementação multiplayer do jogo de tabuleiro Seega, usando Tkinter para a interface gráfica e Pyro5 (RPC) para a comunicação cliente-servidor.

---

## 📦 Tecnologias Utilizadas
- 🐍 Python 3

- 🎨 Tkinter (GUI)

- 🔥 Pyro5 (RPC)

- 🧠 Lógica de jogo customizada

---

# 🎮 Regras Básicas do Seega
O tabuleiro é 5x5.

- Fase 1: cada jogador posiciona suas 12 peças alternadamente (2 por turno, não pode colocar no centro).

- Fase 2: os jogadores movem peças uma casa por vez (horizontal/vertical).

- Capturas: ocorre quando uma peça inimiga é cercada por duas suas (linha ou coluna).

- Vitória ocorre se:

  - Um jogador perder todas as peças,

  - Um jogador fizer uma linha/coluna com 5 peças,

  - O oponente desistir.

---

## 🚀 Como Rodar
### 1. Clone o repositório
```bash
git clone https://github.com/seu-usuario/seega-python.git
cd seega-python
```

### 2. Requisitos
Python 3.9+

Tkinter (já incluso na instalação padrão do Python)

Pyro5

Instale o Pyro5:

```bash
pip install Pyro5
```
### 3. Executar o servidor
```bash
python server.py
```

O servidor irá exibir o URI do Pyro5 (ele salva automaticamente no arquivo seega_uri.txt).
Deixe o servidor rodando.

4. Executar os clientes (em janelas separadas)
Abra dois terminais e execute:

```bash
python ui.py
```
Cada cliente irá se conectar automaticamente ao servidor pelo URI.

🖥️ Rodar como executável (Opcional)

Os executáveis estarão na pasta dist. Rode primeiro o server.exe, depois abra duas vezes o ui.exe para os clientes.

📝 Estrutura dos Arquivos
- ui.py — Cliente gráfico (Tkinter)

- server.py — Servidor Pyro5

- game.py — Lógica do jogo Seega

- seega_uri.txt — Arquivo auxiliar para conexão (criado automaticamente)
