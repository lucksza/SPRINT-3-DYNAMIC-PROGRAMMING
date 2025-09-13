## Integrantes


## 1) Objetivo
Organizar e analisar o **consumo diário de insumos** (reagentes e descartáveis) para reduzir a
baixa visibilidade do estoque. A solução simula dados, registra eventos em **fila e pilha**,
oferece **busca sequencial e binária**, **ordena** por **quantidade** e **validade** e emite
**alertas** de estoque próximo do mínimo.


## 2) Modelo de Dados
- `Item`: id, nome, categoria, unidade, lote, validade, estoque_min, estoque_atual.
- `Consumo`: ts (data/hora), item_id, quantidade.
- `MiniDB`: CRUD básico, fila/pilha de consumo e **simulação** controlada por `seed`.

## 3) Algoritmos & Complexidade
| Etapa | Estrutura/Algoritmo | Complexidade |
|---|---|---|
| Registrar consumo | Fila (`append`) + Pilha (`append`) | O(1) amortizado |
| Busca sequencial | Lista não ordenada | O(n) |
| Busca binária | Vetor ordenado | O(log n) |
| Merge Sort | Estável | O(n log n) |
| Quick Sort | Média O(n log n), pior O(n²) | O(n log n) / O(n²) |
| Totais por item | Uma passada nos eventos | O(m) (m = eventos) |

## 4) Amostra de saída (gerada agora)
```
== CONSUMO REGISTRADO (FILAS E PILHAS) ==
Total de eventos: 98
Primeiro da FILA (mais antigo): Consumo(ts=datetime.datetime(2025, 9, 6, 5, 42, 44, 345346), item_id=6, quantidade=20)
Topo da PILHA (mais recente):  Consumo(ts=datetime.datetime(2025, 9, 12, 4, 57, 44, 345346), item_id=3, quantidade=1)

== BUSCAS ==
Sequencial -> 'Seringa 5ml' achado no índice 4 (se -1, não achou)
Binária por validade -> posição 3 pra data 2026-05-11

== ORDENAÇÃO ==
Top 5 por consumo (Merge Sort, crescente):
  Luva Nitrílica M       |   141 cx
  Ponteira 1000µL        |   171 cx
  Ponteira 200µL         |   179 cx
  Swab Nasofaríngeo      |   185 cx
  Microtubo 1,5ml        |   212 cx

Próximos a vencer (Quick Sort, primeiros vencem antes):
  Hemocultivo Aeróbio    | vence em 2025-11-12
  Kit PCR (RT‑qPCR)      | vence em 2025-12-12
  Soro Fisiológico 0,9%  | vence em 2026-01-11
  Álcool 70% Isoprop.    | vence em 2026-05-11
  Microtubo 1,5ml        | vence em 2026-09-13

== ALERTAS ==
Itens encostando no mínimo (<= 120% do min):
  Luva Nitrílica M       | estoque -21 (min 40)
  Swab Nasofaríngeo      | estoque -95 (min 25)
  Microtubo 1,5ml        | estoque -112 (min 30)
  Ponteira 200µL         | estoque -19 (min 50)
  Ponteira 1000µL        | estoque -21 (min 40)
```

## 5) Decisões de Projeto
1. **Somente stdlib** para portabilidade e zero dependências.
2. **Simulação reprodutível** (seed fixa) para facilitar verificação.
3. **Dois métodos de ordenação** para comparação prática (estabilidade x desempenho).
4. **Design simples** para plugar persistência real (ex.: SQLite/SAP) no futuro.


## 6) Estrutura do repositório
```
dynamic_programming_desafio1.py   
README.md
SPRINT-3-DyPr.pdf                         
```
