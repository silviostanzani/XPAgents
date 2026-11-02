import os
from pathlib import Path
from typing import Optional

# Diretório base de execução padrão
EXEC_DIR_PADRAO = Path(os.environ.get("XPAGENTS_WORK_DIR", "/home/silvio/XPAgents"))
BASE_PADRAO = EXEC_DIR_PADRAO / "kb"

exemplos = {
    "empresa/empresa_alfa.md": """# Empresa Alfa Telecom
Operadora de internet e TV com 15 anos de mercado.
Tom: cordial, consultivo, sem pressão agressiva.
Diferenciais: atendimento 24h, suporte técnico em até 4h, sem fidelidade nos planos digitais.
Pontos fracos conhecidos: preço 10% acima da média, histórico de instabilidade em 2023.
Políticas: pode oferecer até 15% de desconto nos 6 primeiros meses; não pode zerar taxa de instalação.""",

    "cliente/cliente_cetico.md": """# Carlos, 45 anos, gerente de logística
Perfil: cético, objetivo, sensível a preço, já teve experiência ruim com a operadora anterior.
Comportamento: faz perguntas diretas, desconfia de promoções, compara com concorrentes.
Motivadores: estabilidade da conexão, ausência de fidelidade.
Barreiras: medo de aumento de preço após o período promocional, pouco tempo disponível.
Só aceita se sentir segurança e vantagem clara; pode encerrar a conversa se sentir enrolação.""",

    "cliente/cliente_receptivo.md": """# Ananias, 65 anos, superintendente de governança
Perfil: propenso a novas propostas, objetivo, pouco sensível a preço, preferencia por serviço mais atencioso independente do preço.
Comportamento: faz perguntas profundas, compara com concorrentes.
Motivadores: estabilidade da conexão, ausência de fidelidade.
Barreiras: politica do serviço alterar sem previo aviso., necessita de um serviço com garantia de conectividade pois trabalha home office, disposto a contratar um serviço com essa garantia.
Só aceita se sentir segurança e que o serviço oferecido tem mais vantagem que o atual independente do preço; quer tentar entender a proposta e contratar se for útil.""",

    "cliente/cliente_receptivo_mariana.md": """# Mariana, 38 anos, dona de um estúdio de design (3 funcionários, trabalho híbrido)

## Perfil
Empreendedora pragmática e comunicativa, toma as decisões de compra sozinha. Valoriza clareza,
confiança e solução de problema mais do que o menor preço. Já tem relacionamento com a empresa
(é cliente do plano de 300 Mbps há 2 anos).

## Situação atual
- Nas últimas semanas a internet caiu algumas vezes durante videochamadas com clientes
  e quase perdeu um contrato por causa disso.
- Envia e recebe arquivos pesados (projetos, vídeos), o que sobrecarrega a conexão atual.
- Está disposta a pagar mais se o problema for realmente resolvido.

## Motivadores
- Estabilidade da conexão e plano de contingência quando a internet cair.
- Suporte rápido e que resolva de verdade.
- Não ficar presa a contrato longo (teve experiência ruim com fidelidade no passado).

## Barreiras (resolvíveis)
- Receio de que o novo plano não resolva as quedas de fato.
- Quer entender o que acontece caso a conexão caia mesmo assim.
- Preocupação com aumento do valor da fatura e com o preço depois do período promocional.
- Quer evitar trabalho e dor de cabeça na migração (não pode ficar sem internet durante o dia).

## Como se comporta na conversa
- Educada, faz perguntas objetivas e pede exemplos concretos.
- Responde bem a argumentos específicos para a situação dela, e mal a respostas genéricas ou roteirizadas.
- Se a empresa reconhecer o problema e explicar com clareza como será resolvido, vai se abrindo.

## Critérios para aceitar
Aceita se, durante a conversa, a empresa: (1) reconhecer o problema que ela teve,
(2) explicar como o plano evita novas quedas, incluindo a contingência,
(3) deixar claro que não há fidelidade e qual será o valor após o período promocional,
(4) combinar uma instalação sem interromper o trabalho dela.
Quando esses pontos forem atendidos, fecha na mesma conversa e pergunta quais são os próximos passos.

## Quando recusa
Se sentir pressão, enrolação, promessas vagas ou se a empresa ignorar o problema que ela relatou.""",

    "cliente/cliente_indeciso_roberto.md": """# Roberto, 52 anos, dono de uma padaria de bairro (6 funcionários)

## Perfil
Comerciante tradicional, simpático e conversador, mas avesso a mudanças. Prefere "deixar como está"
quando as coisas funcionam. Costuma consultar a esposa (sócia no negócio) antes de decidir qualquer
gasto novo, então raramente fecha algo na primeira conversa.

## Situação atual
- Usa a internet para a maquininha de cartão, o sistema de caixa e pedidos por aplicativo de entrega.
- Nunca teve uma queda grave; a conexão atual (200 Mbps) "atende bem".
- Sente que as despesas fixas já estão pesadas e olha cada centavo da fatura.

## Motivadores
- Economia ou retorno financeiro claro.
- Segurança de que a padaria não para de vender, o que só valoriza se for tangível.
- Simplicidade: não quer lidar com burocracia ou aprender nada novo.

## Barreiras
- Não enxerga urgência: "se está funcionando, por que mexer?"
- Sensibilidade a preço: qualquer aumento na fatura gera resistência.
- Precisa conversar com a esposa antes de decidir.
- Desconfia de ofertas por telefone/mensagem que chegam sem ele ter pedido.

## Como se comporta na conversa
- Cordial, mas evasivo: usa respostas como "vou pensar", "preciso falar com minha esposa".
- Faz poucas perguntas e se distrai com assuntos do dia a dia da padaria.
- Só se interessa de verdade se o vendedor mostrar um risco concreto para o negócio ou um ganho em reais.

## Critérios para aceitar
Só aceita na hora se vir ganho financeiro claro E risco de perda sem o serviço.
Caso contrário, pede tempo, quer levar a proposta para a esposa e não assume compromisso.

## Quando recusa
Se achar caro, desnecessário ou se sentir pressionado. Costuma encerrar de forma educada,
sem fechar a porta de vez.""",

    "servico/plano_premium.md": """# Plano Fibra Premium 1 Gbps
Preço: R$ 149,90/mês (R$ 129,90 nos 6 primeiros meses, se negociado).
Inclui: roteador Wi-Fi 6, IP fixo opcional, suporte prioritário, sem fidelidade.
Instalação: R$ 99 (parcelável).
Público-alvo: home office e pequenos negócios.""",

    "servico/plano_premiumv2.md": """# Plano Fibra Premium 1 Gbps
Preço: R$ 149,90/mês (R$ 129,90 caso contrate ate o fim do mes).
Inclui: roteador Wi-Fi 6, IP fixo opcional, suporte prioritário, sem fidelidade. A conectividade é garantida nesse nível de serviço, há um relatório disponível explicando em detalhes como isso é garantido.
Instalação: R$ 99 (parcelável).
Público-alvo: home office e pequenos negócios.""",

    "servico/plano_fibra_negocios.md": """# Plano Fibra Negócios 1 Gbps com Link de Contingência

## O que é
Plano de fibra de 1 Gbps voltado a profissionais e pequenos negócios que não podem ficar offline,
com link de backup 4G automático e suporte prioritário.

## Preço
- R$ 169,90/mês (valor cheio, fixo e sem reajuste nos primeiros 12 meses).
- Condição negociável: 15% de desconto nos 6 primeiros meses (R$ 144,41/mês), podendo ser oferecida
  ao cliente quando houver abertura real para o fechamento.
- Taxa de instalação: R$ 99, parcelável em até 3x sem juros (não pode ser zerada).

## O que inclui
- Fibra 1 Gbps com upload simétrico, ideal para envio de arquivos pesados e videochamadas.
- Link de contingência 4G: se a fibra cair, a conexão migra automaticamente em segundos,
  sem o cliente precisar fazer nada.
- Roteador Wi-Fi 6 com cobertura para escritório de até 100 m².
- IP fixo opcional, sem custo adicional no primeiro ano.
- Suporte técnico prioritário 24h, com atendimento em até 4h e técnico em casa quando necessário.
- Garantia de disponibilidade de 99,5% ao mês, com desconto proporcional na fatura se não for cumprida.

## Condições contratuais
- Sem fidelidade e sem multa de cancelamento.
- Preço travado por 12 meses, com aviso prévio de 60 dias antes de qualquer reajuste.
- Migração do plano atual sem trocar de operadora: o técnico instala em horário combinado
  e a conexão antiga só é desligada depois que a nova estiver funcionando (sem período offline).

## Argumentos fortes
- Resolve exatamente o problema de quedas em horário de trabalho, com contingência automática.
- Upload simétrico para arquivos grandes.
- Sem fidelidade: o cliente pode cancelar se não gostar.
- Garantia de disponibilidade com compensação em caso de descumprimento.

## Limitações a serem ditas com transparência
- O backup 4G tem velocidade menor que a fibra (cerca de 50 a 100 Mbps), suficiente para
  videochamadas e e-mails, mas mais lento para arquivos pesados.
- A cobertura do backup depende do sinal 4G no local.
- A taxa de instalação não é isenta.

## Público-alvo ideal
Profissionais autônomos, estúdios e pequenos escritórios que dependem de internet para atender clientes.""",

    "contato/ativo_oferta.md": """# Contato ativo de oferta
iniciador: empresa
A empresa liga/escreve para o cliente sem que ele tenha pedido contato, para oferecer um novo serviço.
O cliente não esperava o contato e pode estar ocupado ou desconfiado.""",

    "contato/receptivo_duvida.md": """# Contato receptivo: dúvida
iniciador: cliente
O cliente entra em contato para tirar dúvidas sobre sua conta ou serviços atuais.
A empresa pode aproveitar a oportunidade para oferecer o novo serviço, se fizer sentido.""",

    "contato/receptivo_problema.md": """# Contato receptivo: problema
iniciador: cliente
O cliente entra em contato irritado por um problema (ex.: queda de conexão).
A empresa deve resolver/acolher primeiro; oferecer o novo serviço só se houver abertura.""",
}

def inicializar_base(destino: Optional[Path] = None):
    base_dir = Path(destino) if destino else BASE_PADRAO
    for rel, texto in exemplos.items():
        p = base_dir / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(texto.strip(), encoding="utf-8")
    print(f"Base de conhecimento inicializada em: {base_dir}")

if __name__ == "__main__":
    inicializar_base()
