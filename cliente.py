import socket
import time
import random
import threading
import json
from datetime import datetime

class Funcionario:
    def __init__(self, nome, host='127.0.0.1', port=65432):
        self.nome = nome
        self.host = host
        self.port = port
        self.id = f"{nome}_{random.randint(1000,9999)}"
        self.na_sala = False
        self.max_tentativas = 3
        self.timeout = 5.0
    
    def _enviar_comando(self, acao):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.settimeout(self.timeout)
                s.connect((self.host, self.port))
                
                comando = {
                    'acao': acao,
                    'id': self.id,
                    'timestamp': datetime.now().isoformat()
                }
                
                s.sendall(json.dumps(comando).encode('utf-8'))
                resposta = json.loads(s.recv(1024).decode('utf-8'))
                return resposta
        except Exception as e:
            self._log(f"Erro de comunicação: {str(e)}")
            return {'status': 'erro', 'mensagem': str(e)}
    
    def entrar_na_sala(self):
        tentativas = 0
        while tentativas < self.max_tentativas and not self.na_sala:
            tentativas += 1
            resposta = self._enviar_comando('entrar')
            
            if resposta.get('status') == 'sucesso':
                self.na_sala = True
                self._log(f"Entrou na sala (tentativa {tentativas})")
                
                # Simula tempo na sala
                tempo_na_sala = random.uniform(2, 5)
                time.sleep(tempo_na_sala)
                
                self.sair_da_sala()
                return
            else:
                espera = random.uniform(1, 3)
                self._log(f"Falha ao entrar: {resposta.get('mensagem')} (Tentando novamente em {espera:.1f}s)")
                time.sleep(espera)
        
        if not self.na_sala:
            self._log(f"Desistiu após {tentativas} tentativas")
    
    def sair_da_sala(self):
        if not self.na_sala:
            return
            
        resposta = self._enviar_comando('sair')
        if resposta.get('status') == 'sucesso':
            self.na_sala = False
            self._log("Saiu da sala")
        else:
            self._log(f"Erro ao sair: {resposta.get('mensagem')}")
    
    def _log(self, mensagem):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {self.nome} ({self.id}): {mensagem}")

class Simulador:
    def __init__(self, num_funcionarios=5):
        self.funcionarios = [
            Funcionario(nome) for nome in [
                "Ana", "Bruno", "Carlos", "Daniela", "Eduardo",
                "Fernanda", "Gustavo", "Helena", "Igor", "Julia"
            ][:num_funcionarios]
        ]
    
    def iniciar(self):
        threads = []
        for func in self.funcionarios:
            t = threading.Thread(target=func.entrar_na_sala)
            t.start()
            threads.append(t)
            time.sleep(random.uniform(0.1, 0.5))
        
        for t in threads:
            t.join()

if __name__ == "__main__":
    print("=== SIMULADOR DE SALA DE REUNIÃO ===")
    
    try:
        num_funcionarios = int(input("Número de funcionários a simular (1-10): "))
        if not 1 <= num_funcionarios <= 10:
            raise ValueError
    except ValueError:
        print("Entrada inválida. Usando padrão (5)")
        num_funcionarios = 5
    
    simulador = Simulador(num_funcionarios)
    simulador.iniciar()