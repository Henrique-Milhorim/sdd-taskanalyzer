# CONTEXT_RULES — Governança de Contexto para Agentes de IA

Projeto: **TaskAnalyzer** · Autor: Henrique Milhorim Alves Mariano

Estas regras são fornecidas a qualquer assistente de IA antes da geração de código.

## Diretrizes Arquiteturais (Obrigatórias)

- Python 3.11+ como versão mínima obrigatória.
- Type hints em todas as funções, métodos e atributos.
- Entidades modeladas com `dataclasses` do módulo padrão.
- Princípio Single Responsibility (SRP) e código limpo (PEP 8).
- Docstrings no padrão Google para módulos, classes e funções.
- Funções pequenas, coesas e com um único propósito.
- Tratamento de exceções específico, com mensagens claras.
- Logs estruturados com o módulo padrão `logging` (INFO/WARNING/ERROR).
- Código legível e manutenível, com nomes descritivos.
- Cobertura de testes automatizados ≥ 90% das linhas do módulo.

## Proibições Explícitas (Regras Restritivas)

- Não utilizar bibliotecas externas não autorizadas (apenas stdlib + pytest).
- Não alterar, remover ou adaptar os cenários de teste fornecidos.
- Não modificar a estrutura de pastas definida no projeto.
- Não persistir dados em arquivos ou bancos de dados.
- Não alterar a assinatura das funções públicas sem autorização.
- Não gerar código sem os testes correspondentes.
- Não inserir código duplicado ou sem necessidade.
- Não assumir comportamentos de negócio não especificados neste contrato.
- Não expor detalhes internos por meio de nomes/docstrings de funções públicas.

## Fluxo de validação

Cenários escritos → Testes automatizados (pytest) → Validação do código gerado por IA → Homologação humana.

Nenhum código gerado por IA é aceito sem passar integralmente por essa cadeia.
