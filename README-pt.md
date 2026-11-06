# WorkCoord — Engenharia de Agentes Orientada por Evidências

**Trabalho concluído não é necessariamente um resultado validado.**

O WorkCoord é um projeto público independente para investigar como contexto governado, investigação estruturada, coordenação de tarefas e evidências verificáveis podem melhorar o trabalho de agentes de IA em software.

## Por que existe?

Agentes podem tomar decisões baseadas em documentos antigos, trabalhar simultaneamente na mesma tarefa, usar testes de outra revisão ou declarar uma correção concluída sem comprovar o comportamento completo. O objetivo não é adicionar o máximo de mecanismos; é encontrar o **menor processo suficiente para cada problema**.

O modelo separa três dimensões: **conhecimento**, **estado do trabalho** e **autorização**. Uma hipótese não se torna validada porque o agente está confiante. Uma tarefa concluída não autoriza alterações de produção.

## O que será demonstrado?

O ambiente **FlowDesk** é inteiramente fictício: uma API, fila, worker e notificações. O estudo compara um agente único, dois agentes com coordenação convencional e dois agentes com verificações de contexto, posse e evidências.

O protocolo propõe 72 execuções exploratórias, **ainda não realizadas**. Não há alegação de melhoria de desempenho até termos resultados reais e auditáveis. Testes determinísticos de invariantes não medem inteligência de modelos.

## Navegação

- [README completo em inglês](README.md)
- [Arquitetura](docs/architecture.md)
- [Método de pesquisa](docs/research-method.md)
- [Desenho experimental](docs/experimental-design.md)
- [Política de publicação](docs/publication-policy.md)

O projeto não reutiliza material privado e não pretende substituir plataformas maduras de orquestração.

## Intelligence setorizada — demonstração sintética

A [demonstração executável](docs/intelligence-walkthrough.md) começa por um registro antigo do worker, segue a dependência até a fila, encontra contraprovas atuais e revisa a hipótese de investigação. Perspectiva, profundidade, identidade de fontes, limitações e caracteres lidos permanecem explícitos. Execute `PYTHONPATH=src python -m workcoord_lab.intelligence_demo` na raiz do checkout. **Não é uma avaliação com agentes reais nem uma prova de ganho de eficiência.**

## Comparação de contexto — três estratégias

O [experimento sintético](docs/context-comparison-v0.md) compara corpus completo, setor local e expansão por dependências com o mesmo avaliador, inclusive casos em que a seleção perde informação decisiva. Mede recuperação de contraprovas e caracteres consultados, com diagnóstico provisório por regras anotadas manualmente. **Ainda não mede a qualidade das decisões de agentes reais nem ganhos de custo ou tokens.**

## Próxima prova: expandir, aprofundar, permanecer ou suspender

O [ensaio adaptativo sintético](docs/adaptive-evidence-v0.md) testa `STAY`, `DEEPEN`, `EXPAND` e `HOLD`, incluindo um HOLD **evitável** e dois mundos com a mesma informação disponível mas causas ocultas distintas. A avaliação não premia desistências indevidas nem confunde uma hipótese plausível com evidência completa. O avaliador continua público e todos os sinais são fictícios: **não se trata de benchmark com agentes reais**.

## Research Quality v0 — rigor científico proporcional

Uma [verificação consultiva de pesquisa](docs/research-quality-v0.md) identifica problemas de proveniência, disponibilidade temporal, observação posterior à decisão, controles ausentes, métricas que não comprovam a hipótese e promoção indevida de conclusões. As modalidades `QUICK`, `STRUCTURED` e `CRITICAL` mantêm o rigor proporcional ao risco. Há 14 cenários fictícios públicos; uma aprovação significa **desenho admissível**, nunca hipótese cientificamente validada, autorização de ação ou ganho de desempenho comprovado.

## Problem & Decision v0 — teste verde não fecha o problema

A [demonstração executável](docs/problem-decision-v0.md) separa o mapa hierárquico de problemas, critérios obrigatórios, alternativas de solução, custos assumidos, aplicação e comprovação. O caso principal tem testes técnicos verdes e status de trabalho `DONE`, mas falta uma observação comportamental obrigatória: **a conclusão fica em HOLD**. A rota `QUICK` não exige matriz extensa de alternativas. Nenhum resultado concede autorização de execução ou validação científica; os cenários são fictícios e públicos.

## Cognitive Perspectives v0 — quatro perspectivas, um problema

A [demonstração pública](docs/cognitive-perspectives-v0.md) usa quatro perspectivas **consultivas** (Pesquisa, Engenharia, Eficiência e Risco) sobre o mesmo problema, com um checkpoint canônico. Diferencia setores técnicos de perguntas cognitivas, preserva contraprovas e bloqueia consenso fictício, mesmo quando três perspectivas apoiam e apenas uma contesta. A rota `QUICK` evita a obrigatoriedade de quatro análises em tarefas simples. As perspectivas são registros escritos no cenário fictício, **não quatro agentes, revisão independente ou autorização para executar**.

## Knowledge & Learning v0 — conclusões têm genealogia

A [prova executável](docs/knowledge-genealogy-v0.md) preserva revisões de fonte, observações favoráveis e contrárias, retrações com justificativa e dependências entre conclusões. Uma conclusão antes consultivamente admissível volta para `HOLD` quando a sua fonte é substituída; um novo arquivo ou uma nova observação não restauram a validade sem revisão explícita. A cadeia de hashes e o replay permitem comparar cortes históricos, **mas não autenticam fontes nem realizam aprendizado de modelo**. São 19 casos fictícios públicos, sem agentes reais.
