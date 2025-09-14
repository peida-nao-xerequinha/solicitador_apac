# risco_cirurgico.py

import os
from tkinter import messagebox
from utils import extrair_dados_variaveis, APAC_PDF, buscar_nome_medico_por_cns

# ==============================================================================
# DADOS FIXOS - ESPECÍFICOS PARA OCI DE RISCO CIRÚRGICO
# ==============================================================================
DADOS_FIXOS_RISCO_CIRURGICO = {
    "PROC_PRINCIPAL_COD": "09.02.01.001-8",
    "PROC_PRINCIPAL_NOME": "OCI AVALIACAO DE RISCO CIRURGICO",
    "PROC_PRINCIPAL_QTD": "1",
    "PROC_SEC1_COD": "02.11.02.003-6",
    "PROC_SEC1_NOME": "ELETROCARDIOGRAMA",
    "PROC_SEC1_QTD": "1",
    "PROC_SEC2_COD": "03.01.01.007-2",
    "PROC_SEC2_NOME": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA",
    "PROC_SEC2_QTD": "2",
    "DESC_DIAGNOSTICO": "RASTREAMENTO DOENÇAS CARDIOVASCULARES",
    "CID10_PRINCIPAL": "Z136",
    "OBSERVACOES": "PRÉ-OPERATÓRIO",
    # Os dados abaixo serão substituídos dinamicamente, mas servem como placeholders
    "DOC_SOLICITANTE": "207274333200006",
    "NOME_AUTORIZADOR": "ELENICE GAKU SASAKI DELLA MOTTA",
    "COD_ORGAO_EMISSOR": "M351620001",
    "DOC_AUTORIZADOR": "702402512360420",
    "CNES_EXECUTANTE": "2087669",
    "NOME_SOLICITANTE": ""
}


def gerar_apac_risco_cirurgico(blocos_apac, dados_fixos_genericos):
    """
    Função de orquestração para gerar APACs de Risco Cirúrgico.
    """
    cnes = extrair_dados_variaveis(blocos_apac[0]).get('CNES_ESTABELECIMENTO')
    pdf = APAC_PDF(orientacao='P', unidade='mm', tamanho='A4')

    for bloco in blocos_apac:
        dados_variaveis = extrair_dados_variaveis(bloco)

        cns_solicitante = dados_variaveis.get('CNS_SOLICITANTE', '')
        cns_autorizador = dados_variaveis.get('CNS_AUTORIZADOR', '')

        nome_solicitante = buscar_nome_medico_por_cns(cns_solicitante)
        nome_autorizador = buscar_nome_medico_por_cns(cns_autorizador)

        if not nome_solicitante or not nome_autorizador:
            messagebox.showerror("Erro", f"Médico solicitante ou autorizador com CNS {cns_solicitante} não encontrado no CSV.")
            return

        dados_fixos_temp = DADOS_FIXOS_RISCO_CIRURGICO.copy()
        dados_fixos_temp["NOME_SOLICITANTE"] = nome_solicitante
        dados_fixos_temp["NOME_AUTORIZADOR"] = nome_autorizador
        
        dados_completos = {**dados_fixos_genericos, **dados_fixos_temp, **dados_variaveis}
        dados_completos["CNES_ESTABELECIMENTO"] = cnes
        pdf.add_apac_page(dados_completos)

    pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
    nome_saida = f"apacs_risco_cirurgico_{cnes}.pdf"
    caminho_completo_saida = os.path.join(pasta_downloads, nome_saida)
    pdf.output(caminho_completo_saida)
    
    return True