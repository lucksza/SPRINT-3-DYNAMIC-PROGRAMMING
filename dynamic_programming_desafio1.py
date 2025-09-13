#imports

from __future__ import annotations
from dataclasses import dataclass
from datetime import datetime, timedelta, date
from typing import List, Deque, Dict, Optional, Callable, Any, Tuple
from collections import deque
import random

# ------------------------------
# Modelos de dados
# ------------------------------

@dataclass
class Item:
    id: int
    nome: str
    categoria: str      
    unidade: str        
    lote: str
    validade: date
    estoque_min: int
    estoque_atual: int

@dataclass
class Consumo:
    ts: datetime
    item_id: int
    quantidade: int

# ------------------------------
# Mini banco em memória
# ------------------------------

class MiniDB:
    def __init__(self) -> None:
        self.itens: Dict[int, Item] = {}
        self._prox_id = 1
        self.fila_consumo: Deque[Consumo] = deque()   # FIFO (cronológico)
        self.pilha_consumo: List[Consumo] = []        # LIFO (recentes)

    def add_item(self, nome: str, categoria: str, unidade: str,
                 lote: str, validade: date, estoque_min: int, estoque_atual: int) -> Item:
        item = Item(self._prox_id, nome, categoria, unidade, lote, validade, estoque_min, estoque_atual)
        self.itens[item.id] = item
        self._prox_id += 1
        return item

    def get_item(self, item_id: int) -> Optional[Item]:
        return self.itens.get(item_id)

    def registrar_consumo(self, item_id: int, quantidade: int, quando: Optional[datetime] = None) -> None:
        """Registra um evento na fila e na pilha e debita do estoque."""
        if quando is None:
            quando = datetime.now()
        if item_id not in self.itens:
            raise KeyError("Item inexistente.")
        if quantidade <= 0:
            raise ValueError("Quantidade deve ser > 0.")
        evt = Consumo(ts=quando, item_id=item_id, quantidade=quantidade)
        self.fila_consumo.append(evt)
        self.pilha_consumo.append(evt)
        self.itens[item_id].estoque_atual -= quantidade

    def simular_dias(self, dias: int = 7, eventos_por_dia: int = 10, seed: int = 42) -> None:
        """Gera eventos de consumo aleatórios (reprodutível via seed)."""
        random.seed(seed)
        base = datetime.now() - timedelta(days=dias)
        ids = list(self.itens.keys())
        if not ids:
            raise RuntimeError("Sem itens no banco. Adicione antes de simular.")
        for d in range(dias):
            dia = base + timedelta(days=d)
            for _ in range(eventos_por_dia):
                item_id = random.choice(ids)
                item = self.itens[item_id]
                # Reagente: menor consumo por evento | Descartável: maior
                q = max(1, int(random.gauss(mu=2 if item.categoria == "reagente" else 15,
                                            sigma=1 if item.categoria == "reagente" else 6)))
                quando = dia + timedelta(minutes=random.randint(0, 60 * 10))
                self.registrar_consumo(item_id, q, quando=quando)

# ------------------------------
# Buscas
# ------------------------------

def busca_sequencial(itens: List[Item], chave: Any, key: Callable[[Item], Any]) -> int:
    for i, it in enumerate(itens):
        if key(it) == chave:
            return i
    return -1

def busca_binaria(itens_ordenados: List[Item], chave: Any, key: Callable[[Item], Any]) -> int:
    """Requer que 'itens_ordenados' esteja ordenado pela mesma key."""
    lo, hi = 0, len(itens_ordenados) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        k = key(itens_ordenados[mid])
        if k == chave:
            return mid
        if k < chave:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1

# ------------------------------
# Ordenação
# ------------------------------

def merge_sort(arr: List[Any], key: Callable[[Any], Any]) -> List[Any]:
    if len(arr) <= 1:
        return arr[:]
    mid = len(arr) // 2
    L = merge_sort(arr[:mid], key)
    R = merge_sort(arr[mid:], key)
    i = j = 0
    out: List[Any] = []
    while i < len(L) and j < len(R):
        if key(L[i]) <= key(R[j]):
            out.append(L[i]); i += 1
        else:
            out.append(R[j]); j += 1
    out.extend(L[i:]); out.extend(R[j:])
    return out

def quick_sort(arr: List[Any], key: Callable[[Any], Any]) -> List[Any]:
    if len(arr) <= 1:
        return arr[:]
    pivot = key(arr[len(arr)//2])
    menores = [x for x in arr if key(x) < pivot]
    iguais  = [x for x in arr if key(x) == pivot]
    maiores = [x for x in arr if key(x) > pivot]
    return quick_sort(menores, key) + iguais + quick_sort(maiores, key)

# ------------------------------
# Relatórios
# ------------------------------

def total_consumido_por_item(db: MiniDB) -> Dict[int, int]:
    soma: Dict[int, int] = {i: 0 for i in db.itens.keys()}
    for evt in db.fila_consumo:
        soma[evt.item_id] += evt.quantidade
    return soma

def itens_ordenados_por_consumo(db: MiniDB, metodo: str = "merge") -> List[Tuple[Item, int]]:
    tot = total_consumido_por_item(db)
    pares = [(db.itens[i], q) for i, q in tot.items()]
    keyf = lambda par: par[1]
    return merge_sort(pares, keyf) if metodo == "merge" else quick_sort(pares, keyf)

def itens_ordenados_por_validade(db: MiniDB, metodo: str = "quick") -> List[Item]:
    keyf = lambda it: it.validade
    return merge_sort(list(db.itens.values()), keyf) if metodo == "merge" else quick_sort(list(db.itens.values()), keyf)

def itens_perto_do_minimo(db: MiniDB, margem: float = 0.15) -> List[Item]:
    out: List[Item] = []
    for it in db.itens.values():
        limite = int(it.estoque_min * (1 + margem))
        if it.estoque_atual <= limite:
            out.append(it)
    return out

# ------------------------------
# Dados de exemplo
# ------------------------------

def montar_banco_demo() -> MiniDB:
    db = MiniDB()
    hoje = date.today()
    db.add_item("Soro Fisiológico 0,9%", "reagente", "ml", "L123", hoje + timedelta(days=120),  500, 1500)
    db.add_item("Kit PCR (RT-qPCR)",     "reagente", "un", "K776", hoje + timedelta(days=90),    50,  140)
    db.add_item("Hemocultivo Aeróbio",   "reagente", "un", "H222", hoje + timedelta(days=60),    30,   60)
    db.add_item("Luva Nitrílica M",      "descartável", "cx", "LN55", hoje + timedelta(days=720), 40,  120)
    db.add_item("Seringa 5ml",           "descartável", "cx", "S5ML", hoje + timedelta(days=720), 35,  110)
    db.add_item("Swab Nasofaríngeo",     "descartável", "cx", "SW12", hoje + timedelta(days=540), 25,   90)
    db.add_item("Álcool 70% Isoprop.",   "reagente", "ml", "A70I", hoje + timedelta(days=240),  800, 2200)
    db.add_item("Microtubo 1,5ml",       "descartável", "cx", "MT15", hoje + timedelta(days=365), 30,  100)
    db.add_item("Ponteira 200µL",        "descartável", "cx", "PT20", hoje + timedelta(days=365), 50,  160)
    db.add_item("Ponteira 1000µL",       "descartável", "cx", "PT10", hoje + timedelta(days=365), 40,  150)
    return db


def demo() -> None:
    db = montar_banco_demo()
    db.simular_dias(dias=7, eventos_por_dia=14, seed=7)

    print("== CONSUMO REGISTRADO ==")
    print(f"Eventos na fila: {len(db.fila_consumo)}")
    print(f"Primeiro da fila: {db.fila_consumo[0]}")
    print(f"Topo da pilha: {db.pilha_consumo[-1]}")
    print()

    # Buscas
    itens = list(db.itens.values())
    alvo = "Seringa 5ml"
    idx = busca_sequencial(itens, chave=alvo, key=lambda it: it.nome)
    print("== BUSCAS ==")
    print(f"Sequencial -> '{alvo}' no índice {idx} (se -1, não achou)")

    ordenados_valid = merge_sort(itens, key=lambda it: it.validade)
    if ordenados_valid:
        chave_valid = ordenados_valid[3].validade
        pos = busca_binaria(ordenados_valid, chave=chave_valid, key=lambda it: it.validade)
        print(f"Binária por validade -> posição {pos} para {chave_valid}")
    print()

    # Ordenação
    print("== ORDENAÇÃO ==")
    por_consumo = itens_ordenados_por_consumo(db, metodo="merge")
    print("Top 5 por consumo (crescente, maiores no fim):")
    for it, q in por_consumo[-5:]:
        print(f"- {it.nome:<22} | {q:>5} {it.unidade}")
    print()

    vencendo = itens_ordenados_por_validade(db, metodo="quick")
    print("Próximos a vencer:")
    for it in vencendo[:5]:
        print(f"- {it.nome:<22} | vence em {it.validade.isoformat()}")
    print()

    # Alertas
    print("== ALERTAS ==")
    alerta = itens_perto_do_minimo(db, margem=0.20)
    if not alerta:
        print("Sem alertas.")
    else:
        for it in alerta:
            print(f"- {it.nome:<22} | estoque {it.estoque_atual} (min {it.estoque_min})")

    # Busca binária por NOME
    try:
        termo = input("\n[Busca Binária] Digite o nome exato (ou Enter para pular): ").strip()
        if termo:
            itens_por_nome = merge_sort(list(db.itens.values()), key=lambda it: it.nome.lower())
            pos = busca_binaria(itens_por_nome, chave=termo.lower(), key=lambda it: it.nome.lower())
            if pos >= 0:
                it = itens_por_nome[pos]
                print(f"Encontrado -> ID {it.id} | {it.nome} | {it.categoria} | {it.unidade} | "
                      f"lote {it.lote} | validade {it.validade.isoformat()} | "
                      f"estoque {it.estoque_atual} (min {it.estoque_min})")
            else:
                print("Item não encontrado.")
    except Exception as e:
        print(f"Erro na busca binária: {e}")

if __name__ == "__main__":
    demo()
