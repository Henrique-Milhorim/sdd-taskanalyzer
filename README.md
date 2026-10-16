# sdd-taskanalyzer

Módulo **TaskAnalyzer** desenvolvido com *Spec-Driven Development* (SDD) e assistência de IA, com homologação humana. Calcula tempo médio de conclusão, taxa de atraso e indicadores por prioridade a partir de uma lista de tarefas.

> Bootcamp III — Entrega Intermediária (Fase 2) · Henrique Milhorim Alves Mariano

## Estrutura

```
sdd-taskanalyzer/
├── README.md
├── CONTEXT_RULES.md          # Regras de governança para a IA
├── .gitignore
├── requirements.txt
├── specs/task_analyzer_spec.md   # Contrato SDD
├── tests/test_harness.py         # Testes pytest (Cenários 1 e 2 + bordas)
└── src/task_analyzer.py          # Implementação
```

## Como executar

Requer Python 3.11+.

```bash
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
pytest -v
```

Cobertura (opcional): `pip install pytest-cov && pytest --cov=src --cov-report=term-missing`

## Exemplo de uso

```python
from datetime import datetime
from src.task_analyzer import Prioridade, StatusTarefa, Tarefa, analyze_tasks

tarefas = [
    Tarefa("T1", "Deploy", Prioridade.ALTA, StatusTarefa.CONCLUIDA,
           datetime(2026, 1, 5, 9), datetime(2026, 1, 7, 9), datetime(2026, 1, 6, 9)),
]
print(analyze_tasks(tarefas))
```

## Status do build

Testes: 13 passed · Cobertura: 100% (meta ≥ 90%). _(Badge de CI será adicionado na Fase 3.)_

## Fluxo de homologação humana

1. Executar a suíte pytest (100% passando).
2. Conferir conformidade com o contrato e as CONTEXT_RULES.
3. Revisar qualidade (legibilidade, exceções, logs, cobertura ≥ 90%).
4. Testar manualmente casos de borda.
5. Aprovar e fazer commit/merge via Pull Request.
