# Kit Instagram @tabelapp.economia

São 15 posts de 19/11 a 3/12, com publicação automática pela API oficial do Instagram. Tudo com ferramentas gratuitas.

## Como funciona
1. As artes e os Reels ficam em `midia/`.
2. O GitHub Pages deixa esses arquivos num endereço público (de graça). A API do Instagram exige isso.
3. O GitHub Actions roda `publicar.py` a cada 10 minutos (também de graça) e publica o que chegou na hora.
4. Seu computador não precisa ficar ligado.

## O que é manual (15 minutos no total)
- **Perfil:** bio, foto, destaques e link. Siga `perfil/PERFIL.md`.
- **Fixar** P01, P02 e P03 no topo do perfil depois que saírem.
- **Stories diários**, com os modelos de `stories/`. Enquetes e caixinhas só funcionam pelo app.
- **Música nos Reels (opcional):** os Reels saem com áudio silencioso. Se quiser uma música em alta, publique o Reel pelo app em vez da automação e remova o post do calendário.

## O que depende de dados reais
P05 e P11 (comparações), P06 (café) e P12 (bastidores) usam preços e números reais do Supabase do Tabelapp.
Enquanto os dados não forem preenchidos, eles ficam em `previa/` com a marca MODELO e **não são publicados**.
O Claude Code busca os dados, mostra para você aprovar e só depois gera as artes.

**Atenção:** as comparações mostram o nome real dos mercados. Use só preços reais e com data. Se tiver dúvida jurídica sobre comparar lojas pelo nome, ela entra na lista de perguntas para o advogado. Enquanto isso, dá para trocar o nome por "Mercado do Centro", "Mercado do Valparaíso" etc.

## Opcional: Tabelinha no Reel do café
Salve uma imagem da Tabelinha (gerada no Flow, de preferência com fundo transparente) como `ferramentas/base/tabelinha.png` e rode `gerar.py` de novo.

## Calendário
| Post | Data | Tipo | Conteúdo |
| --- | --- | --- | --- |
| P01 | qui 19/11 12:00 | Carrossel | O que é o Tabelapp (fixar) |
| P02 | qui 19/11 12:10 | Carrossel | Como funciona (fixar) |
| P03 | qui 19/11 12:20 | Carrossel | Parceiro Fundador (fixar) |
| P04 | sex 20/11 12:00 | Reel | Você compara preço? |
| P05 | sáb 21/11 12:00 | Carrossel | Comparação 1: cesta da semana (dados reais) |
| P06 | seg 23/11 18:30 | Reel | Investigação do café (dados reais) |
| P07 | ter 24/11 12:00 | Imagem | Convite para testadores |
| P08 | qua 25/11 18:30 | Carrossel | Black Friday: 5 dicas |
| P09 | qui 26/11 12:00 | Imagem | Nota fiscal em PDF |
| P10 | sex 27/11 08:00 | Imagem | Black Friday: o desconto é de verdade? |
| P11 | sáb 28/11 12:00 | Carrossel | Comparação 2: depois da Black Friday (dados reais) |
| P12 | seg 30/11 18:30 | Reel | Bastidores com números reais |
| P13 | ter 1/12 12:00 | Imagem | Economia local |
| P14 | qua 2/12 18:30 | Reel | 3 erros que encarecem o carrinho |
| P15 | qui 3/12 12:00 | Imagem | Lançamento: "Em breve" ou "Já disponível" |

Todas as legendas estão em `calendario.json` e, para ler com calma, em `legendas.md`.

## Plano B, sem automação
Se a configuração da API travar, use o **Meta Business Suite** (grátis, do próprio Instagram). Ele agenda posts e Reels com as mesmas artes e legendas.

## Comandos úteis
```
python ferramentas/gerar.py                 # gera/atualiza as artes
python ferramentas/publicar.py --status     # o que já saiu e o que está pendente
python ferramentas/publicar.py --simular    # testa sem publicar
```
