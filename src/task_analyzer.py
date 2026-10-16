"""Módulo TaskAnalyzer: calcula métricas de produtividade a partir de tarefas.

Implementa o contrato definido em ``specs/task_analyzer_spec.md``. Utiliza
apenas a biblioteca padrão do Python (3.11+), sem persistência de dados.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional

logger = logging.getLogger(__name__)

SEGUNDOS_POR_HORA: float = 3600.0


# --------------------------------------------------------------------------
# Exceções
# --------------------------------------------------------------------------
class TaskValidationError(Exception):
    """Erro base para violações de validação do TaskAnalyzer."""


class ListaTarefasVaziaError(TaskValidationError):
    """Lançada quando a lista de tarefas recebida está vazia."""


class DadosTarefaInvalidosError(TaskValidationError):
    """Lançada quando um campo de uma tarefa viola uma regra de negócio."""


# --------------------------------------------------------------------------
# Entidades
# --------------------------------------------------------------------------
class Prioridade(Enum):
    """Níveis de prioridade de uma tarefa."""

    CRITICA = "CRITICA"
    ALTA = "ALTA"
    MEDIA = "MEDIA"
    BAIXA = "BAIXA"


class StatusTarefa(Enum):
    """Estados possíveis de uma tarefa."""

    A_FAZER = "A_FAZER"
    EM_ANDAMENTO = "EM_ANDAMENTO"
    CONCLUIDA = "CONCLUIDA"
    CANCELADA = "CANCELADA"


@dataclass(frozen=True)
class Tarefa:
    """Tarefa de entrada do analisador.

    Attributes:
        id: Identificador único da tarefa.
        titulo: Descrição curta da tarefa.
        prioridade: Nível de prioridade.
        status: Estado atual da tarefa.
        data_criacao: Data e hora de criação.
        prazo_entrega: Data e hora limite para conclusão.
        data_conclusao: Data e hora de conclusão; ``None`` se não concluída.
    """

    id: str
    titulo: str
    prioridade: Prioridade
    status: StatusTarefa
    data_criacao: datetime
    prazo_entrega: datetime
    data_conclusao: Optional[datetime] = None


@dataclass(frozen=True)
class IndicadorPrioridade:
    """Métricas segmentadas por nível de prioridade.

    Attributes:
        quantidade: Total de tarefas válidas da prioridade.
        taxa_atraso_percentual: Percentual de tarefas em atraso (0 a 100).
        tempo_medio_conclusao_horas: Média de horas de criação a conclusão.
    """

    quantidade: int = 0
    taxa_atraso_percentual: float = 0.0
    tempo_medio_conclusao_horas: float = 0.0


@dataclass(frozen=True)
class RelatorioAnalise:
    """Relatório de saída do analisador.

    Attributes:
        total_tarefas: Total de tarefas válidas (exclui canceladas).
        total_concluidas: Tarefas concluídas.
        total_pendentes: Tarefas válidas ainda não concluídas.
        tempo_medio_conclusao_horas: Média geral de horas até a conclusão.
        taxa_atraso_percentual: Percentual geral de tarefas em atraso.
        indicadores_por_prioridade: Métricas por nível de prioridade.
    """

    total_tarefas: int
    total_concluidas: int
    total_pendentes: int
    tempo_medio_conclusao_horas: float
    taxa_atraso_percentual: float
    indicadores_por_prioridade: dict[Prioridade, IndicadorPrioridade] = field(
        default_factory=dict
    )


# --------------------------------------------------------------------------
# Funções auxiliares (SRP)
# --------------------------------------------------------------------------
def _validar_tarefa(tarefa: Tarefa) -> None:
    """Valida as regras de negócio de uma tarefa.

    Args:
        tarefa: Tarefa a ser validada.

    Raises:
        DadosTarefaInvalidosError: Se ``prazo_entrega`` não for posterior a
            ``data_criacao`` ou se ``data_conclusao`` for anterior a
            ``data_criacao``.
    """
    if tarefa.prazo_entrega <= tarefa.data_criacao:
        raise DadosTarefaInvalidosError(
            f"Tarefa '{tarefa.id}': campo 'prazo_entrega' deve ser posterior "
            f"a 'data_criacao'."
        )
    if (
        tarefa.data_conclusao is not None
        and tarefa.data_conclusao < tarefa.data_criacao
    ):
        raise DadosTarefaInvalidosError(
            f"Tarefa '{tarefa.id}': campo 'data_conclusao' não pode ser "
            f"anterior a 'data_criacao'."
        )


def _esta_concluida(tarefa: Tarefa) -> bool:
    """Indica se a tarefa está concluída com data de conclusão registrada."""
    return (
        tarefa.status is StatusTarefa.CONCLUIDA
        and tarefa.data_conclusao is not None
    )


def _horas_ate_conclusao(tarefa: Tarefa) -> float:
    """Calcula as horas entre criação e conclusão de uma tarefa concluída."""
    assert tarefa.data_conclusao is not None  # garantido por _esta_concluida
    delta = tarefa.data_conclusao - tarefa.data_criacao
    return delta.total_seconds() / SEGUNDOS_POR_HORA


def _esta_atrasada(tarefa: Tarefa) -> bool:
    """Indica se a tarefa ultrapassou o prazo de entrega.

    Tarefas concluídas atrasam se concluídas após o prazo; tarefas em aberto
    atrasam se o prazo já passou no momento da análise.
    """
    if _esta_concluida(tarefa):
        assert tarefa.data_conclusao is not None
        return tarefa.data_conclusao > tarefa.prazo_entrega
    agora = datetime.now(tarefa.prazo_entrega.tzinfo)
    return agora > tarefa.prazo_entrega


def _media_horas(tarefas: list[Tarefa]) -> float:
    """Calcula o tempo médio de conclusão (horas) das tarefas concluídas.

    Returns:
        Média em horas, ou 0.0 se não houver tarefas concluídas.
    """
    horas = [_horas_ate_conclusao(t) for t in tarefas if _esta_concluida(t)]
    if not horas:
        return 0.0
    return sum(horas) / len(horas)


def _taxa_atraso(tarefas: list[Tarefa]) -> float:
    """Calcula o percentual de tarefas em atraso.

    O universo avaliável são as tarefas com desfecho de prazo definido:
    concluídas ou em aberto com prazo já vencido. Tarefas em aberto dentro
    do prazo ainda não podem ser classificadas.

    Returns:
        Percentual de 0 a 100, ou 0.0 se não houver tarefas avaliáveis.
    """
    atrasadas = [t for t in tarefas if _esta_atrasada(t)]
    avaliaveis = [t for t in tarefas if _esta_concluida(t) or _esta_atrasada(t)]
    if not avaliaveis:
        return 0.0
    return len(atrasadas) / len(avaliaveis) * 100.0


def _indicador_prioridade(tarefas: list[Tarefa]) -> IndicadorPrioridade:
    """Monta o indicador de um grupo de tarefas de mesma prioridade."""
    return IndicadorPrioridade(
        quantidade=len(tarefas),
        taxa_atraso_percentual=_taxa_atraso(tarefas),
        tempo_medio_conclusao_horas=_media_horas(tarefas),
    )


def _indicadores_por_prioridade(
    tarefas: list[Tarefa],
) -> dict[Prioridade, IndicadorPrioridade]:
    """Calcula os indicadores para cada nível de prioridade."""
    return {
        prioridade: _indicador_prioridade(
            [t for t in tarefas if t.prioridade is prioridade]
        )
        for prioridade in Prioridade
    }


# --------------------------------------------------------------------------
# API pública
# --------------------------------------------------------------------------
def analyze_tasks(tarefas: list[Tarefa]) -> RelatorioAnalise:
    """Calcula métricas de produtividade a partir das tarefas.

    Tarefas CANCELADA são excluídas de todos os cálculos.

    Args:
        tarefas: Lista de tarefas a analisar.

    Returns:
        Relatório com totais, tempo médio, taxa de atraso e indicadores por
        prioridade.

    Raises:
        ListaTarefasVaziaError: Se a lista recebida estiver vazia.
        DadosTarefaInvalidosError: Se alguma tarefa violar regra de negócio.
    """
    if not tarefas:
        logger.error("Lista de tarefas vazia recebida.")
        raise ListaTarefasVaziaError("A lista de tarefas não pode ser vazia.")

    validas = [t for t in tarefas if t.status is not StatusTarefa.CANCELADA]
    logger.info(
        "Analisando %d tarefas (%d canceladas excluídas).",
        len(validas),
        len(tarefas) - len(validas),
    )

    for tarefa in validas:
        try:
            _validar_tarefa(tarefa)
        except DadosTarefaInvalidosError:
            logger.error("Tarefa '%s' inválida.", tarefa.id)
            raise

    concluidas = [t for t in validas if _esta_concluida(t)]
    if not concluidas:
        logger.warning(
            "Nenhuma tarefa concluída: tempo médio de conclusão será 0.0."
        )

    return RelatorioAnalise(
        total_tarefas=len(validas),
        total_concluidas=len(concluidas),
        total_pendentes=len(validas) - len(concluidas),
        tempo_medio_conclusao_horas=_media_horas(validas),
        taxa_atraso_percentual=_taxa_atraso(validas),
        indicadores_por_prioridade=_indicadores_por_prioridade(validas),
    )


# Alias em português conforme assinatura da especificação da Fase 1.
analisar_tarefas = analyze_tasks
