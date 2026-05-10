## Multi-step scheduling failure - 2026-05-10

Erro: num pedido com varias acoes agendadas, executei apenas parte da tarefa e misturei chamadas repetidas, em vez de manter uma checklist clara ate completar tudo.

Regra nova: para pedidos com 2+ acoes, criar checklist interna explicita, executar/verificar uma ferramenta de cada vez, confirmar contagem final, e se uma acao nao tiver ferramenta direta usar run_terminal/cron ou perguntar antes de encerrar. Nunca responder como concluido enquanto houver item pendente.

Aplicacao: posts X agendados, pastas agendadas, pesquisas web agendadas e resumos devem ter confirmacao individual + resumo final.

Core patch aplicado: o runtime agora extrai multiplos blocos EVE_TOOL da mesma resposta, executa-os como batch guardado, regista cada resultado, conta verificacoes e obriga a resposta final a respeitar itens falhados/nao verificados.
