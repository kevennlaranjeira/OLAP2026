# Relatório de qualidade do data warehouse

Gerado em 01/10/2026 13:46 pelo comando `dw-sme verificar`.

## Volumes carregados

| tabela | linhas |
|---|---|
| linhas_staging | 13.414.534 |
| excluidas_sem_etapa | 2.356 |
| fato_matricula | 13.412.178 |
| fato_fila | 33.792 |
| fato_desfecho | 159.369 |
| dim_tempo | 120 |
| dim_data | 4.384 |
| dim_ano_letivo | 10 |
| dim_territorio | 97 |
| dim_escola | 9.927 |
| dim_etapa | 10 |
| dim_serie | 122 |
| dim_turno | 13 |
| dim_idade | 101 |
| dim_perfil_aluno | 68 |
| dim_deficiencia | 165 |
| dim_situacao_matricula | 85 |


## Resumo

| código | verificação | situação |
|---|---|---|
| Q01 | Integridade referencial | OK |
| Q02 | Versões da dimensão Escola (SCD tipo 2) | OK |
| Q03 | Conservação entre fato de matrícula e fato de desfecho | OK |
| Q04 | Completude da fila por período | OK |
| Q05 | Soma dos distritos contra a linha TOTAL da planilha | ALERTA |
| Q06 | Total da fila contra a soma das categorias | ALERTA |
| Q07 | Reconciliação entre as duas bases (junho) | ALERTA |
| Q08 | Identificação das escolas por ano | OK |
| Q09 | Membros 'não informado' no fato de matrícula | OK |
| Q10 | Limitações do microdado por ano letivo | ALERTA |


## Q01 · Integridade referencial · OK

18 chaves estrangeiras conferidas; 0 linhas órfãs.

| fato | chave | dimensao | orfas |
|---|---|---|---|
| fato_matricula | chave_ano_letivo | dim_ano_letivo | 0 |
| fato_matricula | chave_data_inicio | dim_data | 0 |
| fato_matricula | chave_data_fim | dim_data | 0 |
| fato_matricula | chave_escola | dim_escola | 0 |
| fato_matricula | chave_territorio | dim_territorio | 0 |
| fato_matricula | chave_serie | dim_serie | 0 |
| fato_matricula | chave_turno | dim_turno | 0 |
| fato_matricula | chave_idade | dim_idade | 0 |
| fato_matricula | chave_perfil_aluno | dim_perfil_aluno | 0 |
| fato_matricula | chave_deficiencia | dim_deficiencia | 0 |
| fato_matricula | chave_situacao | dim_situacao_matricula | 0 |
| fato_fila | chave_tempo | dim_tempo | 0 |
| fato_fila | chave_territorio | dim_territorio | 0 |
| fato_fila | chave_etapa | dim_etapa | 0 |
| fato_desfecho | chave_ano_letivo | dim_ano_letivo | 0 |
| fato_desfecho | chave_escola | dim_escola | 0 |
| fato_desfecho | chave_territorio | dim_territorio | 0 |
| fato_desfecho | chave_serie | dim_serie | 0 |


## Q02 · Versões da dimensão Escola (SCD tipo 2) · OK

0 sobreposições de vigência, 0 escolas sem exatamente uma versão atual, 0 matrículas apontando para versão fora da vigência.

| escolas | versoes | versoes_adicionais | escolas_sinteticas |
|---|---|---|---|
| 9.513 | 9.927 | 414 | 566 |


## Q03 · Conservação entre fato de matrícula e fato de desfecho · OK

13.412.178 matrículas no fato de matrícula e 13.412.178 no fato de desfecho.

| matriculas_no_fato_matricula | matriculas_no_fato_desfecho | linhas_desfecho_que_nao_somam |
|---|---|---|
| 13.412.178 | 13.412.178 | 0 |


## Q04 · Completude da fila por período · OK

44 meses publicados no recorte; 0 com menos que 96 distritos x 8 etapas.

| ano_mes | formato | distritos | etapas | linhas |
|---|---|---|---|---|
| 2015-03 | H | 96 | 8 | 768 |
| 2015-06 | H | 96 | 8 | 768 |
| 2015-09 | H | 96 | 8 | 768 |
| 2015-12 | H | 96 | 8 | 768 |
| 2016-03 | H | 96 | 8 | 768 |
| 2016-06 | H | 96 | 8 | 768 |
| 2016-09 | H | 96 | 8 | 768 |
| 2016-12 | H | 96 | 8 | 768 |
| 2017-03 | H | 96 | 8 | 768 |
| 2017-06 | H | 96 | 8 | 768 |
| 2017-09 | H | 96 | 8 | 768 |
| 2017-12 | H | 96 | 8 | 768 |
| 2018-03 | C | 96 | 8 | 768 |
| 2018-06 | B | 96 | 8 | 768 |
| 2018-09 | B | 96 | 8 | 768 |
| 2018-12 | B | 96 | 8 | 768 |
| 2019-03 | B | 96 | 8 | 768 |
| 2019-06 | B | 96 | 8 | 768 |
| 2019-09 | F | 96 | 8 | 768 |
| 2019-12 | E | 96 | 8 | 768 |
| 2020-03 | E | 96 | 8 | 768 |
| 2020-06 | E | 96 | 8 | 768 |
| 2020-09 | D | 96 | 8 | 768 |
| 2020-12 | A | 96 | 8 | 768 |
| 2021-03 | A | 96 | 8 | 768 |
| 2021-06 | A | 96 | 8 | 768 |
| 2021-09 | A | 96 | 8 | 768 |
| 2021-12 | A | 96 | 8 | 768 |
| 2022-03 | A | 96 | 8 | 768 |
| 2022-06 | A | 96 | 8 | 768 |
| 2022-09 | A | 96 | 8 | 768 |
| 2022-12 | A | 96 | 8 | 768 |
| 2023-02 | A | 96 | 8 | 768 |
| 2023-04 | A | 96 | 8 | 768 |
| 2023-06 | A | 96 | 8 | 768 |
| 2023-08 | A | 96 | 8 | 768 |
| 2023-10 | A | 96 | 8 | 768 |
| 2023-12 | A | 96 | 8 | 768 |
| 2024-02 | A | 96 | 8 | 768 |
| 2024-04 | A | 96 | 8 | 768 |
| 2024-06 | A | 96 | 8 | 768 |
| 2024-08 | A | 96 | 8 | 768 |
| 2024-10 | A | 96 | 8 | 768 |
| 2024-12 | A | 96 | 8 | 768 |


## Q05 · Soma dos distritos contra a linha TOTAL da planilha · ALERTA

2 divergências entre a soma dos distritos e a linha TOTAL publicada, em 2 arquivo(s). Defeito da fonte; o valor por distrito é mantido.

| periodo | arquivo | divergencia |
|---|---|---|
| 2020-06-01 | matriculas-e-demanda-junho-2020.csv | matriculas-e-demanda-junho-2020.csv PRE demanda_com_opcao: soma 2 != TOTAL 0 |
| 2023-06-01 | publicacao-bimestral-junho-2023.csv | publicacao-bimestral-junho-2023.csv CRECHE demanda_com_opcao: soma 2926 != TOTAL 2904 |


## Q06 · Total da fila contra a soma das categorias · ALERTA

24 distritos-etapa em que o total publicado difere da soma das categorias (sem opção até 30 dias, mais de 30 dias, com opção). O total publicado prevalece.

| periodo | arquivo | inconsistencias |
|---|---|---|
| 2020-06-01 | matriculas-e-demanda-junho-2020.csv | 2 |
| 2023-06-01 | publicacao-bimestral-junho-2023.csv | 1 |
| 2023-08-01 | publicacao-bimestral-agosto-2023.csv | 21 |


## Q07 · Reconciliação entre as duas bases (junho) · ALERTA

36 combinações ano x etapa reconciliadas; 7 com diferença acima de 2%. Mediana da diferença absoluta: 0.31%.

| ano | etapa | microdado_ativas_30_06 | planilha_fila | diferenca | fracao_distritos_na_tolerancia |
|---|---|---|---|---|---|
| 2.015 | CRECHE | 240.905 | 240.840 | 0.0003 | 0.9375 |
| 2.015 | FUND_I | 247.485 | 247.019 | 0.0019 | 0.9412 |
| 2.015 | FUND_II | 177.510 | 176.763 | 0.0042 | 0.9294 |
| 2.015 | PRE | 205.020 | 204.715 | 0.0015 | 0.9681 |
| 2.016 | CRECHE | 278.040 | 277.899 | 0.0005 | 0.9792 |
| 2.016 | FUND_I | 247.780 | 247.385 | 0.0016 | 0.9529 |
| 2.016 | FUND_II | 174.934 | 174.302 | 0.0036 | 0.9412 |
| 2.016 | PRE | 215.601 | 215.116 | 0.0023 | 0.9894 |
| 2.017 | CRECHE | 288.366 | 288.294 | 0.0002 | 0.9688 |
| 2.017 | FUND_I | 246.600 | 246.982 | -0.0015 | 0.9294 |
| 2.017 | FUND_II | 167.915 | 168.077 | -0.001 | 0.9176 |
| 2.017 | PRE | 220.818 | 220.175 | 0.0029 | 0.9894 |
| 2.018 | CRECHE | 313.787 | 313.598 | 0.0006 | 0.9479 |
| 2.018 | FUND_I | 233.415 | 232.932 | 0.0021 | 0.9647 |
| 2.018 | FUND_II | 197.399 | 196.769 | 0.0032 | 0.9647 |
| 2.018 | PRE | 219.818 | 219.170 | 0.003 | 0.9681 |
| 2.019 | CRECHE | 334.443 | 333.876 | 0.0017 | 0.9896 |
| 2.019 | FUND_I | 226.024 | 224.959 | 0.0047 | 0.9412 |
| 2.019 | FUND_II | 196.546 | 195.293 | 0.0064 | 0.9176 |
| 2.019 | PRE | 225.479 | 224.549 | 0.0041 | 0.9468 |
| 2.020 | CRECHE | 338.927 | 341.966 | -0.0089 | 0.8646 |
| 2.020 | FUND_I | 222.794 | 222.667 | 0.0006 | 0.9529 |
| 2.020 | FUND_II | 194.908 | 194.893 | 0.0001 | 0.9529 |
| 2.020 | PRE | 232.815 | 232.541 | 0.0012 | 0.9787 |
| 2.022 | CRECHE | 378.954 | 348.975 | 0.0859 | 0.0625 |
| 2.022 | FUND_I | 235.473 | 225.502 | 0.0442 | 0.3882 |
| 2.022 | FUND_II | 198.289 | 195.623 | 0.0136 | 0.2471 |
| 2.022 | PRE | 245.758 | 225.430 | 0.0902 | 0.5319 |
| 2.023 | CRECHE | 373.348 | 338.786 | 0.102 | 0.0104 |
| 2.023 | FUND_I | 230.731 | 230.455 | 0.0012 | 0.9419 |
| 2.023 | FUND_II | 187.283 | 188.820 | -0.0081 | 0.8824 |
| 2.023 | PRE | 230.093 | 225.819 | 0.0189 | 0.5158 |
| 2.024 | CRECHE | 351.906 | 332.464 | 0.0585 | 0.1562 |
| 2.024 | FUND_I | 259.691 | 251.180 | 0.0339 | 0.125 |
| 2.024 | FUND_II | 190.713 | 185.387 | 0.0287 | 0.1765 |
| 2.024 | PRE | 219.686 | 217.912 | 0.0081 | 0.5579 |


## Q08 · Identificação das escolas por ano · OK

Maior fração de matrículas em escola com chave sintética num ano: 5.2%.

| ano | qualidade_codigo_escola | matriculas | fracao_escola_sintetica |
|---|---|---|---|
| 2.015 | CONFIAVEL | 1.235.613 | 0 |
| 2.016 | CONFIAVEL | 1.278.812 | 0 |
| 2.017 | CONFIAVEL | 1.316.629 | 0 |
| 2.018 | CONFIAVEL | 1.387.366 | 0 |
| 2.019 | CONFIAVEL | 1.408.911 | 0 |
| 2.020 | CONFIAVEL | 1.230.064 | 0 |
| 2.021 | CONFIAVEL | 1.410.684 | 0 |
| 2.022 | CONSISTENTE_NO_ANO | 1.559.624 | 0.0141 |
| 2.023 | CORROMPIDO | 1.160.436 | 0.0409 |
| 2.024 | CORROMPIDO | 1.424.039 | 0.0518 |


## Q09 · Membros 'não informado' no fato de matrícula · OK

Fração das matrículas que caem no membro desconhecido de cada dimensão, por ano.

| ano | sem_territorio | sem_idade | sem_turno | sem_data_inicio |
|---|---|---|---|---|
| 2.015 | 0 | 0 | 0 | 0 |
| 2.016 | 0 | 0 | 0 | 0 |
| 2.017 | 0 | 0 | 0 | 0 |
| 2.018 | 0 | 0 | 0 | 0 |
| 2.019 | 0 | 0 | 0 | 0 |
| 2.020 | 0 | 0.0055 | 0 | 0.0001 |
| 2.021 | 0 | 0.012 | 0 | 1 |
| 2.022 | 0 | 0.0063 | 0 | 0.0002 |
| 2.023 | 0 | 0.0001 | 0 | 0 |
| 2.024 | 0 | 0.0067 | 0 | 0.0001 |


## Q10 · Limitações do microdado por ano letivo · ALERTA

5 de 10 anos com alguma limitação registrada na dimensão Ano Letivo.

| ano | qualidade_codigo_escola | observacao |
|---|---|---|
| 2.015 | CONFIAVEL |  |
| 2.016 | CONFIAVEL |  |
| 2.017 | CONFIAVEL |  |
| 2.018 | CONFIAVEL |  |
| 2.019 | CONFIAVEL |  |
| 2.020 | CONFIAVEL | Retrato publicado antes do fim do ano letivo: 41% das matrículas ainda em curso, o que subestima aprovação, reprovação e abandono. |
| 2.021 | CONFIAVEL | Turno não publicado; derivado do código da turma ou do horário. Datas e duração da matrícula não publicadas. 9.8% das idades estimadas só pelo ano de nascimento. |
| 2.022 | CONSISTENTE_NO_ANO | Código da escola fora do padrão no arquivo publicado: 98.6% das matrículas ligadas ao código real pelo nome, tipo e distrito; o restante com chave sintética. 17.4% das idades estimadas só pelo ano de nascimento. |
| 2.023 | CORROMPIDO | Código da escola corrompido no arquivo publicado: 95.9% das matrículas ligadas ao código real pelo nome, tipo e distrito; o restante com chave sintética. Retrato publicado antes do fim do ano letivo: 50% das matrículas ainda em curso, o que subestima aprovação, reprovação e abandono. |
| 2.024 | CORROMPIDO | Código da escola corrompido no arquivo publicado: 94.8% das matrículas ligadas ao código real pelo nome, tipo e distrito; o restante com chave sintética. |

