# Relatório de qualidade do data warehouse

Gerado em 08/10/2026 20:06 pelo comando `dw-sme verificar`.

## Volumes carregados

| tabela | linhas |
|---|---|
| linhas_staging | 13.414.534 |
| excluidas_sem_etapa | 2.356 |
| fato_matricula | 13.412.178 |
| fato_fila | 33.792 |
| fato_desfecho | 159.369 |
| fato_turma | 551.264 |
| fato_populacao | 295.779 |
| dim_tempo | 120 |
| dim_data | 4.384 |
| dim_ano_letivo | 10 |
| dim_territorio | 97 |
| dim_escola | 9.927 |
| dim_etapa | 10 |
| dim_serie | 122 |
| dim_turno | 13 |
| dim_idade | 101 |
| dim_faixa_etaria | 11 |
| dim_setor_censitario | 26.889 |
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
| Q11 | Ocupação das turmas | OK |
| Q12 | População do Censo 2022 | ALERTA |
| Q13 | Hierarquias das dimensões (dependência funcional) | OK |
| Q14 | Conformidade entre as dimensões | OK |


## Q01 · Integridade referencial · OK

27 chaves estrangeiras conferidas; 0 linhas órfãs.

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
| fato_turma | chave_ano_letivo | dim_ano_letivo | 0 |
| fato_turma | chave_escola | dim_escola | 0 |
| fato_turma | chave_territorio | dim_territorio | 0 |
| fato_turma | chave_serie | dim_serie | 0 |
| fato_turma | chave_turno | dim_turno | 0 |
| fato_populacao | chave_tempo | dim_tempo | 0 |
| fato_populacao | chave_setor_censitario | dim_setor_censitario | 0 |
| fato_populacao | chave_territorio | dim_territorio | 0 |
| fato_populacao | chave_faixa_etaria | dim_faixa_etaria | 0 |


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
| 2015 | CRECHE | 240.905 | 240.840 | 0.0003 | 0.9375 |
| 2015 | FUND_I | 247.485 | 247.019 | 0.0019 | 0.9412 |
| 2015 | FUND_II | 177.510 | 176.763 | 0.0042 | 0.9294 |
| 2015 | PRE | 205.020 | 204.715 | 0.0015 | 0.9681 |
| 2016 | CRECHE | 278.040 | 277.899 | 0.0005 | 0.9792 |
| 2016 | FUND_I | 247.780 | 247.385 | 0.0016 | 0.9529 |
| 2016 | FUND_II | 174.934 | 174.302 | 0.0036 | 0.9412 |
| 2016 | PRE | 215.601 | 215.116 | 0.0023 | 0.9894 |
| 2017 | CRECHE | 288.366 | 288.294 | 0.0002 | 0.9688 |
| 2017 | FUND_I | 246.600 | 246.982 | -0.0015 | 0.9294 |
| 2017 | FUND_II | 167.915 | 168.077 | -0.001 | 0.9176 |
| 2017 | PRE | 220.818 | 220.175 | 0.0029 | 0.9894 |
| 2018 | CRECHE | 313.787 | 313.598 | 0.0006 | 0.9479 |
| 2018 | FUND_I | 233.415 | 232.932 | 0.0021 | 0.9647 |
| 2018 | FUND_II | 197.399 | 196.769 | 0.0032 | 0.9647 |
| 2018 | PRE | 219.818 | 219.170 | 0.003 | 0.9681 |
| 2019 | CRECHE | 334.443 | 333.876 | 0.0017 | 0.9896 |
| 2019 | FUND_I | 226.024 | 224.959 | 0.0047 | 0.9412 |
| 2019 | FUND_II | 196.546 | 195.293 | 0.0064 | 0.9176 |
| 2019 | PRE | 225.479 | 224.549 | 0.0041 | 0.9468 |
| 2020 | CRECHE | 338.927 | 341.966 | -0.0089 | 0.8646 |
| 2020 | FUND_I | 222.794 | 222.667 | 0.0006 | 0.9529 |
| 2020 | FUND_II | 194.908 | 194.893 | 0.0001 | 0.9529 |
| 2020 | PRE | 232.815 | 232.541 | 0.0012 | 0.9787 |
| 2022 | CRECHE | 378.954 | 348.975 | 0.0859 | 0.0625 |
| 2022 | FUND_I | 235.473 | 225.502 | 0.0442 | 0.3882 |
| 2022 | FUND_II | 198.289 | 195.623 | 0.0136 | 0.2471 |
| 2022 | PRE | 245.758 | 225.430 | 0.0902 | 0.5319 |
| 2023 | CRECHE | 373.348 | 338.786 | 0.102 | 0.0104 |
| 2023 | FUND_I | 230.731 | 230.455 | 0.0012 | 0.9419 |
| 2023 | FUND_II | 187.283 | 188.820 | -0.0081 | 0.8824 |
| 2023 | PRE | 230.093 | 225.819 | 0.0189 | 0.5158 |
| 2024 | CRECHE | 351.906 | 332.464 | 0.0585 | 0.1562 |
| 2024 | FUND_I | 259.691 | 251.180 | 0.0339 | 0.125 |
| 2024 | FUND_II | 190.713 | 185.387 | 0.0287 | 0.1765 |
| 2024 | PRE | 219.686 | 217.912 | 0.0081 | 0.5579 |


## Q08 · Identificação das escolas por ano · OK

Maior fração de matrículas em escola com chave sintética num ano: 5.2%.

| ano | qualidade_codigo_escola | matriculas | fracao_escola_sintetica |
|---|---|---|---|
| 2015 | CONFIAVEL | 1.235.613 | 0 |
| 2016 | CONFIAVEL | 1.278.812 | 0 |
| 2017 | CONFIAVEL | 1.316.629 | 0 |
| 2018 | CONFIAVEL | 1.387.366 | 0 |
| 2019 | CONFIAVEL | 1.408.911 | 0 |
| 2020 | CONFIAVEL | 1.230.064 | 0 |
| 2021 | CONFIAVEL | 1.410.684 | 0 |
| 2022 | CONSISTENTE_NO_ANO | 1.559.624 | 0.0141 |
| 2023 | CORROMPIDO | 1.160.436 | 0.0409 |
| 2024 | CORROMPIDO | 1.424.039 | 0.0518 |


## Q09 · Membros 'não informado' no fato de matrícula · OK

Fração das matrículas que caem no membro desconhecido de cada dimensão, por ano.

| ano | sem_territorio | sem_idade | sem_turno | sem_data_inicio |
|---|---|---|---|---|
| 2015 | 0 | 0 | 0 | 0 |
| 2016 | 0 | 0 | 0 | 0 |
| 2017 | 0 | 0 | 0 | 0 |
| 2018 | 0 | 0 | 0 | 0 |
| 2019 | 0 | 0 | 0 | 0 |
| 2020 | 0 | 0.0055 | 0 | 0.0001 |
| 2021 | 0 | 0.012 | 0 | 1 |
| 2022 | 0 | 0.0063 | 0 | 0.0002 |
| 2023 | 0 | 0.0001 | 0 | 0 |
| 2024 | 0 | 0.0067 | 0 | 0.0001 |


## Q10 · Limitações do microdado por ano letivo · ALERTA

5 de 10 anos com alguma limitação registrada na dimensão Ano Letivo.

| ano | qualidade_codigo_escola | observacao |
|---|---|---|
| 2015 | CONFIAVEL |  |
| 2016 | CONFIAVEL |  |
| 2017 | CONFIAVEL |  |
| 2018 | CONFIAVEL |  |
| 2019 | CONFIAVEL |  |
| 2020 | CONFIAVEL | Retrato publicado antes do fim do ano letivo: 41% das matrículas ainda em curso, o que subestima aprovação, reprovação e abandono. |
| 2021 | CONFIAVEL | Turno não publicado; derivado do código da turma ou do horário. Datas e duração da matrícula não publicadas. 9.8% das idades estimadas só pelo ano de nascimento. |
| 2022 | CONSISTENTE_NO_ANO | Código da escola fora do padrão no arquivo publicado: 98.6% das matrículas ligadas ao código real pelo nome, tipo e distrito; o restante com chave sintética. 17.4% das idades estimadas só pelo ano de nascimento. |
| 2023 | CORROMPIDO | Código da escola corrompido no arquivo publicado: 95.9% das matrículas ligadas ao código real pelo nome, tipo e distrito; o restante com chave sintética. Retrato publicado antes do fim do ano letivo: 50% das matrículas ainda em curso, o que subestima aprovação, reprovação e abandono. |
| 2024 | CORROMPIDO | Código da escola corrompido no arquivo publicado: 94.8% das matrículas ligadas ao código real pelo nome, tipo e distrito; o restante com chave sintética. |


## Q11 · Ocupação das turmas · OK

551.264 turmas; 0 anos em que o fato de turma não conserva as matrículas ou as turmas do fato de matrícula; 0.00% das matrículas em turma sem nome publicado.

| ano | matriculas | matriculas_no_fato_turma | turmas_distintas | linhas_fato_turma | matriculas_sem_nome_de_turma | alunos_por_turma_junho |
|---|---|---|---|---|---|---|
| 2015 | 1.235.613 | 1.235.613 | 46.668 | 46.668 | 0 | 21 |
| 2016 | 1.278.812 | 1.278.812 | 48.813 | 48.813 | 0 | 21 |
| 2017 | 1.316.629 | 1.316.629 | 51.362 | 51.362 | 0 | 20 |
| 2018 | 1.387.366 | 1.387.366 | 54.472 | 54.472 | 0 | 20 |
| 2019 | 1.408.911 | 1.408.911 | 56.382 | 56.382 | 0 | 20 |
| 2020 | 1.230.064 | 1.230.064 | 58.892 | 58.892 | 0 | 19 |
| 2021 | 1.410.684 | 1.410.684 | 61.014 | 61.014 | 0 |  |
| 2022 | 1.559.624 | 1.559.624 | 58.837 | 58.837 | 0 | 20 |
| 2023 | 1.160.436 | 1.160.436 | 57.659 | 57.659 | 72 | 18 |
| 2024 | 1.424.039 | 1.424.039 | 57.165 | 57.165 | 0 | 19 |


## Q12 · População do Censo 2022 · ALERTA

11.434.513 pessoas em 26.889 setores e 96 distritos; 0 setores sem distrito correspondente na SME; 6543 valores não publicados.

| ano_mes | setores | distritos | setores_sem_distrito_da_sme | valores_nao_publicados | pessoas |
|---|---|---|---|---|---|
| 2022-07 | 26.889 | 96 | 0 | 6.543 | 11.434.513 |


## Q13 · Hierarquias das dimensões (dependência funcional) · OK

23 relações A ≤ B conferidas; 0 membros pertencem a mais de um pai.

| dimensao | nivel | agregado_em | violacoes |
|---|---|---|---|
| dim_data | data | ano+mes | 0 |
| dim_data | ano+mes | ano+trimestre | 0 |
| dim_data | ano+trimestre | ano+semestre | 0 |
| dim_data | ano+semestre | ano | 0 |
| dim_tempo | ano+mes | ano+trimestre | 0 |
| dim_tempo | ano+trimestre | ano+semestre | 0 |
| dim_tempo | ano+semestre | ano | 0 |
| dim_tempo | ano+mes | ano+bimestre | 0 |
| dim_tempo | ano+bimestre | ano | 0 |
| dim_territorio | distrito | dre | 0 |
| dim_territorio | dre | municipio | 0 |
| dim_territorio | municipio | uf | 0 |
| dim_escola | chave_escola | tipo_escola | 0 |
| dim_escola | tipo_escola | rede | 0 |
| dim_serie | chave_serie | codigo_etapa | 0 |
| dim_serie | codigo_etapa | nivel | 0 |
| dim_serie | chave_serie | ciclo | 0 |
| dim_etapa | codigo | nivel | 0 |
| dim_turno | turno | jornada | 0 |
| dim_idade | idade | faixa_escolar | 0 |
| dim_idade | idade | grupo_etario | 0 |
| dim_idade | idade | faixa_ibge | 0 |
| dim_setor_censitario | cd_setor | distrito | 0 |


## Q14 · Conformidade entre as dimensões · OK

8 regras de conformidade; 0 violações do modelo, 0 distritos do IBGE sem correspondente na SME.

| regra | violacoes | falha_do_modelo |
|---|---|---|
| Série -> Etapa: todo código de etapa da Série existe na Etapa | 0 | True |
| Série -> Etapa: nome da etapa e nível iguais nas duas dimensões | 0 | True |
| Idade -> Faixa Etária: toda faixa IBGE da Idade existe na Faixa Etária | 0 | True |
| Idade -> Faixa Etária: limites da faixa contêm a idade | 0 | True |
| Data/Tempo -> Ano Letivo: todo ano letivo existe em Tempo | 0 | True |
| Data -> Tempo: todo mês de Tempo existe em Data | 0 | True |
| Escola -> Território: todo distrito de escola existe em Território | 0 | True |
| Setor Censitário -> Território: distrito do IBGE sem correspondente na SME (ver Q12) | 0 | False |

