import tkinter as tk
from tkinter import scrolledtext, messagebox
import threading
import time
import Pyro5.api
from queue import Queue

def get_pyro_proxy():
    """
    Lê o URI do servidor salvo em 'seega_uri.txt' e retorna um proxy Pyro5.

    Returns:
        Pyro5.api.Proxy: Proxy conectado ao servidor Seega.
    """
    with open("seega_uri.txt") as f:
        uri = f.read().strip()
    return Pyro5.api.Proxy(uri)

class SeegaClientRPC:
    """
    Cliente gráfico para o jogo Seega, utilizando Tkinter para interface e Pyro5 para comunicação RPC.

    Responsável por:
    - Gerenciar eventos da interface gráfica (Tkinter).
    - Enviar e receber ações de jogo via RPC ao servidor.
    - Atualizar o tabuleiro, chat e status do jogo em tempo real.

    Atributos:
        master (tk.Tk): Janela principal.
        player_id (int): ID do jogador (0 ou 1).
        my_symbol (str): Símbolo do jogador ('X' ou 'O').
        queue (Queue): Fila para mensagens do servidor.
        placing_phase (bool): True se o jogo está na fase de colocação de peças.
        selected (tuple|None): Posição selecionada para movimentação.
    """

    def __init__(self, master):
        """
        Inicializa o cliente, conecta ao servidor, registra jogador, cria interface gráfica e inicia polling de mensagens.

        Args:
            master (tk.Tk): Janela principal da interface gráfica.
        """
        self.master = master
        self.master.title("Seega - Cliente Pyro")
        self.master.configure(bg="#f0f0f0")
        self.selected = None
        self.placing_phase = True
        self.queue = Queue()
        with get_pyro_proxy() as proxy:
            self.player_id = proxy.register_player()
        if self.player_id == -1:
            messagebox.showerror("Erro", "Servidor cheio. Tente mais tarde.")
            master.destroy()
            return

        self.my_symbol = 'X' if self.player_id == 0 else 'O'

        self.create_widgets()
        threading.Thread(target=self.poll_messages_loop, daemon=True).start()
        self.master.after(5, self.process_gui_queue)

    def create_widgets(self):
        """
        Cria e organiza os widgets da interface gráfica, incluindo tabuleiro, chat, campos de entrada e botões.
        """
        self.status_label = tk.Label(
            self.master, text=f"Você é o jogador {self.my_symbol}",
            font=("Arial", 12, "bold"), bg="#f0f0f0", fg="#333")
        self.status_label.pack(pady=(10, 5))

        main_frame = tk.Frame(self.master, bg="#f0f0f0")
        main_frame.pack(padx=10, pady=5)

        self.board_frame = tk.Frame(main_frame, bg="#f0f0f0")
        self.board_frame.grid(row=0, column=0, padx=10)

        self.cells = [
            [tk.Button(
                self.board_frame, text="", width=4, height=2,
                font=("Arial", 12, "bold"), bg="#ffffff", relief=tk.FLAT,
                command=lambda x=i, y=j: self.cell_click(x, y))
             for j in range(5)]
            for i in range(5)
        ]
        for i in range(5):
            for j in range(5):
                self.cells[i][j].grid(row=i, column=j, padx=2, pady=2)

        right_frame = tk.Frame(main_frame, bg="#f0f0f0")
        right_frame.grid(row=0, column=1, sticky="n")

        self.log = scrolledtext.ScrolledText(
            right_frame, width=40, height=20, font=("Courier", 10),
            bg="#fafafa", state='disabled')
        self.log.pack(pady=5)

        bottom_frame = tk.Frame(right_frame, bg="#f0f0f0")
        bottom_frame.pack(fill='x')

        self.entry = tk.Entry(bottom_frame, width=30, font=("Arial", 10))
        self.entry.pack(side='left', padx=(0, 5), pady=5)

        self.send_btn = tk.Button(
            bottom_frame, text="Enviar", command=self.send_message,
            bg="#4CAF50", fg="white", relief=tk.FLAT)
        self.send_btn.pack(side='right')

        self.quit_btn = tk.Button(
            right_frame, text="Desistir", command=self.send_resign,
            bg="#d32f2f", fg="white", relief=tk.FLAT)
        self.quit_btn.pack(pady=(10, 0), fill='x')

    def poll_messages_loop(self):
        """
        Thread de polling contínuo para buscar mensagens/atualizações do servidor e colocá-las na fila.
        """
        with get_pyro_proxy() as proxy:
            while True:
                try:
                    msgs = proxy.poll_messages(self.player_id)
                    receive_time = time.time()
                    for msg in msgs:
                        self.queue.put((msg, receive_time))
                    time.sleep(0.5)
                except Exception as e:
                    print(f"[Erro no polling]: {e}")
                    break

    def process_gui_queue(self):
        """
        Processa a fila de mensagens vinda do servidor, atualizando a interface conforme necessário.
        """
        while not self.queue.empty():
            msg, t = self.queue.get()
            self.process_message(msg, t)
        self.master.after(5, self.process_gui_queue)

    def process_message(self, msg, received_time=None):
        """
        Processa mensagens do servidor (movimentos, status, chat, capturas e finalização de jogo).

        Args:
            msg (str): Mensagem recebida do servidor.
            received_time (float, opcional): Timestamp de recebimento.
        """
        if msg.startswith("MOVE"):
            parts = msg.split()
            if len(parts) == 4:
                _, x, y, sym = parts
                x, y = int(x), int(y)
                self.update_cell(x, y, sym)
            elif len(parts) == 6:
                _, x1, y1, x2, y2, sym = parts
                x1, y1, x2, y2 = int(x1), int(y1), int(x2), int(y2)
                self.update_cell(x1, y1, '')     
                self.update_cell(x2, y2, sym)    
            if self.selected:
                x1, y1 = self.selected
                self.cells[x1][y1].config(bg="#ffffff")
                self.selected = None

        elif msg.startswith("TURN"):
            parts = msg.split()
            sym = parts[1]
            phase = int(parts[2]) if len(parts) > 2 else 1
            self.placing_phase = (phase == 1)
            self.status_label.config(text=f"É a vez de {sym}")
        elif msg.startswith("CHAT"):
            self.log_message(msg)
        elif msg.startswith("GAME_OVER"):
            self.status_label.config(text="Jogo encerrado!")
            self.show_victory_popup(msg)
        elif msg.startswith("CAPTURE"):
            _, x, y = msg.split()
            self.update_cell(int(x), int(y), '')
        else:
            self.log_message(msg)

    def update_cell(self, x, y, symbol):
        """
        Atualiza visualmente o texto e cor de uma célula do tabuleiro.

        Args:
            x (int): Linha da célula.
            y (int): Coluna da célula.
            symbol (str): Símbolo a ser exibido ('X', 'O', ou '').
        """
        fg = "#000000"
        if symbol == "X": fg = "#d32f2f"
        elif symbol == "O": fg = "#1976d2"
        self.cells[x][y].config(text=symbol, fg=fg, bg="#ffffff", relief=tk.FLAT)

    def log_message(self, msg):
        """
        Adiciona uma mensagem ao log do chat na interface.

        Args:
            msg (str): Mensagem a ser exibida.
        """
        self.log.config(state='normal')
        self.log.insert(tk.END, msg + "\n")
        self.log.yview(tk.END)
        self.log.config(state='disabled')

    def cell_click(self, x, y):
        """
        Manipula clique do usuário em uma célula, lidando com fases de colocação e movimentação.

        Args:
            x (int): Linha clicada.
            y (int): Coluna clicada.
        """
        threading.Thread(target=self._handle_click_logic, args=(x, y), daemon=True).start()

    def _handle_click_logic(self, x, y):
        """
        Lógica de tratamento do clique (colocação/movimentação), com chamadas RPC ao servidor.

        Args:
            x (int): Linha.
            y (int): Coluna.
        """
        try:
            if self.placing_phase:
                with get_pyro_proxy() as proxy:
                    responses = proxy.place_piece(x, y, self.player_id)
                for r in responses:
                    self.queue.put((r, time.time()))
            elif self.selected is None:
                if self.cells[x][y].cget("text") == self.my_symbol:
                    self.selected = (x, y)
                    self.master.after(0, lambda: self.cells[x][y].config(bg="#add8e6"))
            else:
                x1, y1 = self.selected
                with get_pyro_proxy() as proxy:
                    responses = proxy.move_piece(x1, y1, x, y, self.player_id)
                for r in responses:
                    self.queue.put((r, time.time()))
        except Exception as e:
            self.master.after(0, lambda: self.log_message(f"[Erro ao clicar]: {e}"))

    def send_message(self):
        """
        Envia a mensagem digitada pelo usuário no campo de texto do chat para o servidor.
        """
        msg = self.entry.get()
        if msg:
            threading.Thread(target=self._send_chat_rpc, args=(msg,), daemon=True).start()
            self.entry.delete(0, tk.END)

    def _send_chat_rpc(self, msg):
        """
        Executa a chamada RPC de envio de chat para o servidor.

        Args:
            msg (str): Mensagem do usuário.
        """
        try:
            with get_pyro_proxy() as proxy:
                proxy.chat(self.player_id, msg)
        except Exception as e:
            self.master.after(0, lambda: self.log_message(f"[Erro ao enviar mensagem]: {e}"))

    def send_resign(self):
        """
        Pede confirmação do usuário e, se confirmado, envia resignação ao servidor.
        """
        if messagebox.askyesno("Confirmar", "Tem certeza que deseja desistir?"):
            threading.Thread(target=self._resign_rpc, daemon=True).start()

    def _resign_rpc(self):
        """
        Executa a chamada RPC de resignação ao servidor.
        """
        try:
            with get_pyro_proxy() as proxy:
                proxy.resign(self.player_id)
        except Exception as e:
            self.master.after(0, lambda: self.log_message(f"[Erro ao desistir]: {e}"))

    def show_victory_popup(self, msg):
        """
        Exibe um popup ao final do jogo, informando vitória ou derrota.

        Args:
            msg (str): Mensagem do servidor com o resultado do jogo.
        """
        cleaned = msg.replace("GAME_OVER", "").strip()
        if self.my_symbol in cleaned:
            result = "Parabéns, você venceu!"
        else:
            result = "Você perdeu. Mais sorte na próxima!"
        result += f"\n\n{cleaned}"
        messagebox.showinfo("Fim de Jogo", result)

if __name__ == '__main__':
    root = tk.Tk()
    app = SeegaClientRPC(root)
    root.mainloop()