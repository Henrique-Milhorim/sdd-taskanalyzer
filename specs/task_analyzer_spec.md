# Especificação SDD — Módulo TaskAnalyzer

**Autor:** Henrique Milhorim Alves Mariano · Análise e Desenvolvimento de Sistemas · Campus Asa Norte

## 1. Visão Geral e Contrato de Negócio

### 1.1 Propósito
O TaskAnalyzer processa um conjunto de tarefas e gera indicadores objetivos de produtividade:

- **Tempo médio de conclusão:** média, em horas, entre criação e conclusão das tarefas finalizadas.
- **Taxa de atraso:** percentual de tarefas que ultrapassaram o prazo de entrega.
- **Indicadores por prioridade:** quantidade, taxa de atraso e tempo médio por nível (Crítica, Alta, Média, Baixa).

### 1.2 Entidade de entrada: `Tarefa`

| Campo | Tipo | Descrição |
|---|---|---|
| id | str | Identificador único |
| titulo | str | Descrição curta |
| prioridade | Prioridade (enum) | CRITICA \| ALTA \| MEDIA \| BAIXA |
| status | StatusTarefa (enum) | A_FAZER \| EM_ANDAMENTO \| CONCLUIDA \| CANCELADA |
| data_criacao | datetime | Criação |
| prazo_entrega | datetime | Prazo limite |
| data_conclusao | Optional[datetime] | Conclusão; `None` se não concluída |

### 1.3 Entidade de saída: `RelatorioAnalise`

| Campo | Tipo | Descrição |
|---|---|---|
| total_tarefas | int | Tarefas válidas (exclui canceladas) |
| total_concluidas | int | Tarefas concluídas |
| total_pendentes | int | Tarefas válidas não concluídas |
| tempo_medio_conclusao_horas | float | Média de horas entre criação e conclusão |
| taxa_atraso_percentual | float | Percentual de tarefas em atraso |
| indicadores_por_prioridade | dict[Prioridade, IndicadorPrioridade] | Métricas por prioridade |

`IndicadorPrioridade`: `quantidade: int`, `taxa_atraso_percentual: float`, `tempo_medio_conclusao_horas: float`.

### 1.4 Assinatura pública

```python
def analyze_tasks(tarefas: list[Tarefa]) -> RelatorioAnalise:
    """Calcula métricas de produtividade a partir das tarefas."""
```

`analisar_tarefas` é mantido como alias de `analyze_tasks`.

### 1.5 Restrições de negócio

- Tarefas `CANCELADA` são excluídas de todos os cálculos.
- Tarefas sem `data_conclusao` não entram no tempo médio, mas contam como atraso "em aberto" se `prazo_entrega` já passou.
- Sem tarefas concluídas: `tempo_medio_conclusao_horas = 0.0` e aviso via `logging` (nunca divisão por zero).
- `prazo_entrega` deve ser posterior a `data_criacao`; `data_conclusao` não pode ser anterior a `data_criacao`.
- A lista de entrada não pode ser vazia.

### 1.6 Exceções

- `TaskValidationError` — exceção base.
- `ListaTarefasVaziaError(TaskValidationError)` — lista vazia.
- `DadosTarefaInvalidosError(TaskValidationError)` — campo viola regra de negócio.

### 1.7 Definição da taxa de atraso
`taxa = atrasadas / avaliáveis × 100`, onde *avaliáveis* são as tarefas concluídas ou em aberto com prazo vencido. Tarefas em aberto dentro do prazo ainda não têm desfecho e não entram no denominador. Sem tarefas avaliáveis, a taxa é `0.0`.

## 2. Cenários de Aceite

**Cenário 1 (Sucesso).** *Dado* 8 tarefas válidas — 5 concluídas (3 no prazo, 2 em atraso) e 3 em andamento, nas quatro prioridades — *quando* o analisador for executado, *então* retorna o tempo médio correto das 5 concluídas, `taxa_atraso_percentual = 40%` e indicadores por prioridade coerentes.

**Cenário 2 (Exceção).** *Dada* uma tarefa com `prazo_entrega` anterior a `data_criacao`, *quando* o analisador for executado, *então* lança `DadosTarefaInvalidosError` com mensagem indicando a tarefa e o campo.

**Casos de borda.** Lista vazia → `ListaTarefasVaziaError`; apenas pendentes → médias `0.0` com aviso em log; apenas canceladas → zeros; fusos horários diferentes; grande volume.

## 3. Test Harness
Testes pytest em `tests/test_harness.py`, com fixtures `tarefas_validas` e `tarefa_prazo_invalido`, `pytest.approx` para floats, `pytest.raises` para exceções e cobertura ≥ 90%.
