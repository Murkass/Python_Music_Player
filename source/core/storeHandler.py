import json
import os

class StoreHandler:
    """
    Gerencia o armazenamento de dados do aplicativo.
    Responsável por salvar e carregar dados em arquivos JSON.
    """
    
    def __init__(self, store_path: str = "source/core/store.json"):
        """
        Inicializa o handler com o caminho do arquivo de armazenamento.
        
        Args:
            store_path: Caminho do arquivo store.json
        """
        self.store_path = store_path
        self.store_data = self._load_store()
    
    def _load_store(self) -> dict:
        """Carrega os dados do JSON ou cria uma nova estrutura."""
        if os.path.exists(self.store_path):
            try:
                with open(self.store_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data if data else {}
            except (json.JSONDecodeError, IOError):
                return {}
        return {}
    
    def _save_store(self) -> bool:
        """Salva os dados no JSON."""
        try:
            os.makedirs(os.path.dirname(self.store_path) or ".", exist_ok=True)
            with open(self.store_path, 'w', encoding='utf-8') as f:
                json.dump(self.store_data, f, indent=4, ensure_ascii=False)
            return True
        except IOError as e:
            print(f"Erro ao salvar dados: {e}")
            return False
        
    def set_storageData(self, storage, values) -> bool:
        self.store_data[storage] = values

    def set_keydata(self, storage: str , key: str, value) -> bool:
        """
        Define um valor para uma chave específica e salva os dados.
        
        Args:
            storage: Armazenamento para o valor
            key: Chave para armazenar o valor
            value: Valor a ser armazenado
            
        Returns:
            True se salvo com sucesso, False caso contrário
        """
        if storage not in self.store_data:
            self.store_data[storage] = {}
        self.store_data[storage][key] = value
        return self._save_store()
    
    def get_data(self, storage: str, key: str):
        """
        Obtém um valor para uma chave específica.
        
        Args:
            storage: Armazenamento do valor
            key: Chave do valor
            
        Returns:
            O valor armazenado ou None se não encontrado
        """
        return self.store_data.get(storage, {}).get(key)
    