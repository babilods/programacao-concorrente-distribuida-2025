import socket
import threading
from datetime import datetime
import json

class SalaReuniao:
    def __init__(self, capacidade_maxima=5):
        self.capacidade_maxima = capacidade_maxima
        self.semaphore = threading.BoundedSemaphore(capacidade_maxima)  # Evita releases excessivos
        self.lock = threading.Lock()
        self.ocupantes = {}
        self.historico = []
    
    def entrar(self, funcionario_id, conn):
        with self.lock:
            if len(self.ocupantes) >= self.capacidade_maxima:
                self._log(f"TENTATIVA {funcionario_id} (Sala cheia)")
                return False
            
            if funcionario_id in self.ocupantes:
                self._log(f"TENTATIVA {funcionario_id} (Já está na sala)")
                return False
                
            if self.semaphore.acquire(blocking=False):
                self.ocupantes[funcionario_id] = {
                    'entrada': datetime.now(),
                    'conn': conn
                }
                self._log(f"ENTRADA {funcionario_id} | Ocupação: {len(self.ocupantes)}/{self.capacidade_maxima}")
                return True
            return False
    
    def sair(self, funcionario_id):
        with self.lock:
            if funcionario_id not in self.ocupantes:
                self._log(f"TENTATIVA SAIDA {funcionario_id} (Não estava na sala)")
                return False
                
            tempo_permanencia = (datetime.now() - self.ocupantes[funcionario_id]['entrada']).total_seconds()
            del self.ocupantes[funcionario_id]
            self.semaphore.release()
            self._log(f"SAÍDA {funcionario_id} | Tempo: {tempo_permanencia:.1f}s | Ocupação: {len(self.ocupantes)}/{self.capacidade_maxima}")
            return True

    def status(self):
        with self.lock:
            return {
                'ocupacao': len(self.ocupantes),
                'capacidade': self.capacidade_maxima,
                'ocupantes': list(self.ocupantes.keys()),
                'historico': self.historico[-10:]  # Últimos 10 registros
            }
    
    def _log(self, mensagem):
        registro = {
            'timestamp': datetime.now().isoformat(),
            'evento': mensagem
        }
        self.historico.append(registro)
        print(f"[{registro['timestamp']}] {mensagem}")

class ServidorReuniao:
    def __init__(self, host='0.0.0.0', port=65432):
        self.host = host
        self.port = port
        self.sala = SalaReuniao()
    
    def _handle_client(self, conn, addr):
        try:
            conn.settimeout(30)
            while True:
                data = conn.recv(1024)
                if not data:
                    break
                    
                try:
                    comando = json.loads(data.decode('utf-8'))
                    resposta = self._processar_comando(comando, conn)
                    conn.sendall(json.dumps(resposta).encode('utf-8'))
                except json.JSONDecodeError:
                    conn.sendall(json.dumps({'erro': 'Formato inválido'}).encode('utf-8'))
        except socket.timeout:
            self.sala._log(f"TIMEOUT {addr}")
        finally:
            conn.close()
    
    def _processar_comando(self, comando, conn):
        acao = comando.get('acao')
        funcionario_id = comando.get('id')
        
        if acao == 'entrar':
            sucesso = self.sala.entrar(funcionario_id, conn)
            return {
                'status': 'sucesso' if sucesso else 'erro',
                'mensagem': 'Entrada permitida' if sucesso else 'Sala cheia ou já está na sala'
            }
        elif acao == 'sair':
            sucesso = self.sala.sair(funcionario_id)
            return {
                'status': 'sucesso' if sucesso else 'erro',
                'mensagem': 'Saída registrada' if sucesso else 'Não estava na sala'
            }
        elif acao == 'status':
            return {
                'status': 'sucesso',
                'data': self.sala.status()
            }
        else:
            return {
                'status': 'erro',
                'mensagem': 'Comando inválido'
            }
    
    def iniciar(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind((self.host, self.port))
            s.listen(5)
            self.sala._log(f"SERVIDOR INICIADO | {self.host}:{self.port}")
            
            try:
                while True:
                    conn, addr = s.accept()
                    threading.Thread(
                        target=self._handle_client,
                        args=(conn, addr),
                        daemon=True
                    ).start()
            except KeyboardInterrupt:
                self.sala._log("SERVIDOR ENCERRADO")
            except Exception as e:
                self.sala._log(f"ERRO: {str(e)}")

if __name__ == "__main__":
    servidor = ServidorReuniao()
    servidor.iniciar()