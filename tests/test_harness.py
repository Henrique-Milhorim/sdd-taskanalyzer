"""Test Harness do TaskAnalyzer (Cenários de Aceite 1 e 2 + casos de borda)."""

from __future__ import annotations

import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from task_analyzer import (  # noqa: E402
    DadosTarefaInvalidosError,
    ListaTarefasVaziaError,
    Prioridade,
    StatusTarefa,
    Tarefa,
    TaskValidationError,
    analisar_tarefas,
    analyze_tasks,
)

BASE = datetime(2026, 1, 5, 9, 0)
FUTURO = datetime(2099, 1, 1, 9, 0)


def _tarefa(
    id_: str,
    prioridade: Prioridade,
    status: StatusTarefa,
    prazo_h: float | None,
    conclusao_h: float | None = None,
    prazo: datetime | None = None,
) -> Tarefa:
    """Cria uma tarefa com offsets em horas a partir de BASE."""
    return Tarefa(
        id=id_,
        titulo=f"Tarefa {id_}",
        prioridade=prioridade,
        status=status,
        data_criacao=BASE,
        prazo_entrega=prazo or BASE + timedelta(hours=prazo_h or 0),
        data_conclusao=(
            BASE + timedelta(hours=conclusao_h)
            if conclusao_h is not None
            else None
        ),
    )


@pytest.fixture
def tarefas_validas() -> list[Tarefa]:
    """8 tarefas: 5 concluídas (3 no prazo, 2 atrasadas) e 3 em andamento."""
    c, a, m, b = (
        Prioridade.CRITICA,
        Prioridade.ALTA,
        Prioridade.MEDIA,
        Prioridade.BAIXA,
    )
    done, doing, todo = (
        StatusTarefa.CONCLUIDA,
        StatusTarefa.EM_ANDAMENTO,
        StatusTarefa.A_FAZER,
    )
    return [
        _tarefa("T1", c, done, 48, 24),  # no prazo, 24h
        _tarefa("T2", a, done, 48, 72),  # atrasada, 72h
        _tarefa("T3", m, done, 100, 50),  # no prazo, 50h
        _tarefa("T4", b, done, 24, 40),  # atrasada, 40h
        _tarefa("T5", c, done, 100, 10),  # no prazo, 10h
        _tarefa("T6", a, doing, None, prazo=FUTURO),
        _tarefa("T7", m, todo, None, prazo=FUTURO),
        _tarefa("T8", b, doing, None, prazo=FUTURO),
    ]


@pytest.fixture
def tarefa_prazo_invalido() -> Tarefa:
    """Tarefa com prazo_entrega anterior à data_criacao."""
    return _tarefa("T-ERRO", Prioridade.ALTA, StatusTarefa.A_FAZER, -5)


# --------------------------- Cenário 1 (Sucesso) ---------------------------
def test_analisar_tarefas_retorna_metricas_corretas(
    tarefas_validas: list[Tarefa],
) -> None:
    relatorio = analyze_tasks(tarefas_validas)

    assert relatorio.total_tarefas == 8
    assert relatorio.total_concluidas == 5
    assert relatorio.total_pendentes == 3
    assert relatorio.tempo_medio_conclusao_horas == pytest.approx(39.2)
    assert relatorio.taxa_atraso_percentual == pytest.approx(40.0)


def test_indicadores_por_prioridade_coerentes(
    tarefas_validas: list[Tarefa],
) -> None:
    ind = analyze_tasks(tarefas_validas).indicadores_por_prioridade

    assert set(ind) == set(Prioridade)
    assert ind[Prioridade.CRITICA].quantidade == 2
    assert ind[Prioridade.CRITICA].tempo_medio_conclusao_horas == pytest.approx(17.0)
    assert ind[Prioridade.CRITICA].taxa_atraso_percentual == pytest.approx(0.0)
    assert ind[Prioridade.ALTA].quantidade == 2
    assert ind[Prioridade.ALTA].tempo_medio_conclusao_horas == pytest.approx(72.0)
    assert ind[Prioridade.ALTA].taxa_atraso_percentual == pytest.approx(100.0)
    assert ind[Prioridade.MEDIA].tempo_medio_conclusao_horas == pytest.approx(50.0)
    assert ind[Prioridade.MEDIA].taxa_atraso_percentual == pytest.approx(0.0)
    assert ind[Prioridade.BAIXA].tempo_medio_conclusao_horas == pytest.approx(40.0)
    assert ind[Prioridade.BAIXA].taxa_atraso_percentual == pytest.approx(100.0)


def test_alias_em_portugues_equivale_a_analyze_tasks(
    tarefas_validas: list[Tarefa],
) -> None:
    assert analisar_tarefas is analyze_tasks


# ------------------------ Cenário 2 (Exceção/Erro) -------------------------
def test_analisar_tarefas_levanta_erro_para_prazo_invalido(
    tarefa_prazo_invalido: Tarefa,
) -> None:
    with pytest.raises(DadosTarefaInvalidosError) as exc:
        analyze_tasks([tarefa_prazo_invalido])

    assert "T-ERRO" in str(exc.value)
    assert "prazo_entrega" in str(exc.value)


def test_erro_para_data_conclusao_anterior_a_criacao() -> None:
    tarefa = _tarefa("T-X", Prioridade.BAIXA, StatusTarefa.CONCLUIDA, 48, -2)

    with pytest.raises(TaskValidationError) as exc:
        analyze_tasks([tarefa])

    assert "T-X" in str(exc.value)
    assert "data_conclusao" in str(exc.value)


def test_excecoes_especificas_herdam_de_task_validation_error() -> None:
    assert issubclass(DadosTarefaInvalidosError, TaskValidationError)
    assert issubclass(ListaTarefasVaziaError, TaskValidationError)


# ------------------------------ Casos de borda -----------------------------
def test_lista_vazia_levanta_lista_tarefas_vazia_error() -> None:
    with pytest.raises(ListaTarefasVaziaError):
        analyze_tasks([])


def test_apenas_pendentes_retorna_zero_e_registra_aviso(
    caplog: pytest.LogCaptureFixture,
) -> None:
    tarefas = [
        _tarefa("P1", Prioridade.ALTA, StatusTarefa.A_FAZER, None, prazo=FUTURO),
        _tarefa("P2", Prioridade.BAIXA, StatusTarefa.EM_ANDAMENTO, None, prazo=FUTURO),
    ]

    with caplog.at_level(logging.WARNING):
        relatorio = analyze_tasks(tarefas)

    assert relatorio.tempo_medio_conclusao_horas == 0.0
    assert relatorio.taxa_atraso_percentual == 0.0
    assert relatorio.total_concluidas == 0
    assert relatorio.total_pendentes == 2
    assert any(r.levelno == logging.WARNING for r in caplog.records)


def test_tarefa_em_aberto_com_prazo_vencido_conta_como_atraso() -> None:
    tarefas = [
        _tarefa("A1", Prioridade.CRITICA, StatusTarefa.EM_ANDAMENTO, 24),
        _tarefa("A2", Prioridade.CRITICA, StatusTarefa.CONCLUIDA, 48, 10),
    ]

    relatorio = analyze_tasks(tarefas)

    assert relatorio.taxa_atraso_percentual == pytest.approx(50.0)
    assert relatorio.tempo_medio_conclusao_horas == pytest.approx(10.0)


def test_tarefas_canceladas_sao_excluidas_dos_calculos() -> None:
    tarefas = [
        _tarefa("C1", Prioridade.ALTA, StatusTarefa.CANCELADA, 1),
        _tarefa("C2", Prioridade.ALTA, StatusTarefa.CONCLUIDA, 48, 12),
    ]

    relatorio = analyze_tasks(tarefas)

    assert relatorio.total_tarefas == 1
    assert relatorio.taxa_atraso_percentual == pytest.approx(0.0)
    assert relatorio.indicadores_por_prioridade[Prioridade.ALTA].quantidade == 1


def test_apenas_canceladas_retorna_zeros() -> None:
    relatorio = analyze_tasks(
        [_tarefa("C1", Prioridade.BAIXA, StatusTarefa.CANCELADA, 10)]
    )

    assert relatorio.total_tarefas == 0
    assert relatorio.tempo_medio_conclusao_horas == 0.0
    assert relatorio.taxa_atraso_percentual == 0.0


def test_fusos_horarios_diferentes_calculam_horas_corretas() -> None:
    from datetime import timezone

    brasilia = timezone(timedelta(hours=-3))
    criacao = datetime(2026, 1, 5, 9, 0, tzinfo=brasilia)
    tarefa = Tarefa(
        id="TZ",
        titulo="Fuso",
        prioridade=Prioridade.MEDIA,
        status=StatusTarefa.CONCLUIDA,
        data_criacao=criacao,
        prazo_entrega=datetime(2026, 1, 7, 12, 0, tzinfo=timezone.utc),
        data_conclusao=datetime(2026, 1, 5, 20, 0, tzinfo=timezone.utc),
    )

    relatorio = analyze_tasks([tarefa])

    # 09:00 (-03) = 12:00 UTC -> conclusão 20:00 UTC = 8h
    assert relatorio.tempo_medio_conclusao_horas == pytest.approx(8.0)
    assert relatorio.taxa_atraso_percentual == pytest.approx(0.0)


def test_grande_volume_de_tarefas() -> None:
    tarefas = [
        _tarefa(f"V{i}", Prioridade.MEDIA, StatusTarefa.CONCLUIDA, 48, 24)
        for i in range(10_000)
    ]

    relatorio = analyze_tasks(tarefas)

    assert relatorio.total_concluidas == 10_000
    assert relatorio.tempo_medio_conclusao_horas == pytest.approx(24.0)
