import threading
from game import SeegaGame
import Pyro5.api

@Pyro5.api.expose
class SeegaRPCServer(object):
    """
    Servidor RPC do jogo Seega usando Pyro5.

    Gerencia o estado do jogo, jogadores, mensagens e expõe métodos remotos
    para interação com clientes (jogadores) via rede.
    """
    def __init__(self):
        """
        Inicializa o servidor, criando a instância do jogo, lista de jogadores,
        mensagens por jogador e um lock para controle de concorrência.
        """
        self.game = SeegaGame()
        self.players = []  # 0 -> X, 1 -> O
        self.messages = {0: [], 1: []}
        self.lock = threading.Lock()

    def register_player(self):
        """
        Registra um novo jogador no servidor.

        Returns:
            int: ID do jogador (0 para 'X', 1 para 'O'), ou -1 se o servidor estiver cheio.
        """
        with self.lock:
            if len(self.players) < 2:
                pid = len(self.players)
                self.players.append(pid)
                self.messages[pid] = []
                return pid
            return -1

    def get_symbol(self, pid):
        """
        Retorna o símbolo do jogador (X ou O) com base no seu ID.

        Args:
            pid (int): ID do jogador.

        Returns:
            str: 'X' se pid == 0, 'O' se pid == 1.
        """
        return 'X' if pid == 0 else 'O'

    def place_piece(self, x, y, pid):
        """
        Realiza a colocação de uma peça no tabuleiro durante a primeira fase do jogo.

        Args:
            x (int): Linha do tabuleiro.
            y (int): Coluna do tabuleiro.
            pid (int): ID do jogador realizando a ação.

        Returns:
            list: Lista de mensagens com o resultado da ação para serem enviadas ao cliente.
        """
        msgs = []
        with self.lock:
            if self.game.turn != self.get_symbol(pid):
                return ["Não é sua vez."]
            success, msg = self.game.place_piece(x, y)
            print("\n[DEBUG] Após place_piece:")
            self.game.print_board()
            if not success:
                return [msg]
            symbol = self.get_symbol(pid)
            msgs.append(f"MOVE {x} {y} {symbol}")
            msgs.append(f"TURN {self.game.turn} {self.game.phase}")
            winner = self.game.check_win()
            if winner:
                msgs.append(f"GAME_OVER {winner} venceu!")
            for m in msgs:
                self._broadcast(m)
        return msgs
    
    def snapshot(self):
        """
        Retorna uma cópia do estado atual do tabuleiro.

        Returns:
            list: Tabuleiro 5x5 como lista de listas.
        """
        return [[cell for cell in row] for row in self.game.board]
    
    def move_piece(self, x1, y1, x2, y2, pid):
        """
        Realiza a movimentação de uma peça durante a segunda fase do jogo.

        Args:
            x1, y1 (int): Coordenadas de origem da peça.
            x2, y2 (int): Coordenadas de destino da peça.
            pid (int): ID do jogador realizando a ação.

        Returns:
            list: Lista de mensagens para atualizar os clientes.
        """
        msgs = []
        with self.lock:
            if self.game.turn != self.get_symbol(pid):
                return ["Não é sua vez."]

            before = self.snapshot()
            success, msg = self.game.move_piece(x1, y1, x2, y2)
            print("\n[DEBUG] Após move_piece:")
            self.game.print_board()
            after = self.snapshot()

            if not success:
                return [msg]   

            symbol = self.get_symbol(pid)
            msgs.append(f"MOVE {x1} {y1} {x2} {y2} {symbol}")
            msgs.append(f"TURN {self.game.turn} {self.game.phase}")

            # Detecta peças capturadas comparando o tabuleiro antes/depois
            for i in range(5):
                for j in range(5):
                    if before[i][j] != ' ' and after[i][j] == ' ' and (i != x1 or j != y1):
                        msgs.append(f"CAPTURE {i} {j}")

            winner = self.game.check_win()
            if winner:
                msgs.append(f"GAME_OVER {winner} venceu!")
            for m in msgs:
                self._broadcast(m)
        return msgs

    def chat(self, pid, message):
        """
        Envia uma mensagem de chat para todos os jogadores.

        Args:
            pid (int): ID do jogador enviando a mensagem.
            message (str): Mensagem de texto.

        Returns:
            bool: True se enviada com sucesso.
        """
        symbol = self.get_symbol(pid)
        self._broadcast(f"CHAT {symbol}: {message}")
        return True

    def resign(self, pid):
        """
        Permite que um jogador desista da partida, declarando o adversário como vencedor.

        Args:
            pid (int): ID do jogador desistente.

        Returns:
            bool: True se enviado o aviso de desistência.
        """
        winner = self.get_symbol(1 - pid)
        self._broadcast(f"GAME_OVER Jogador {winner} venceu por desistência.")
        return True

    def poll_messages(self, pid):
        """
        Retorna todas as mensagens pendentes para um jogador.

        Args:
            pid (int): ID do jogador.

        Returns:
            list: Lista de mensagens para o jogador.
        """
        with self.lock:
            msgs = self.messages.get(pid, [])[:]
            self.messages[pid] = []
            return msgs

    def _broadcast(self, msg):
        """
        Envia uma mensagem para todos os jogadores conectados.

        Args:
            msg (str): Mensagem a ser enviada.
        """
        for pid in self.messages:
            self.messages[pid].append(msg)

def main():
    """
    Inicializa o servidor Pyro5, registra o objeto do servidor e
    inicia o loop de requisições.
    """
    daemon = Pyro5.api.Daemon()
    server_obj = SeegaRPCServer()
    uri = daemon.register(server_obj) 
    print("Servidor Seega Pyro5 iniciado.")
    print("URI:", uri)
    with open("seega_uri.txt", "w") as f:
        f.write(str(uri))
    daemon.requestLoop()

if __name__ == '__main__':
    main()