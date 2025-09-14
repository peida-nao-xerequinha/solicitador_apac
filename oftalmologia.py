# oftalmologia.py

import os
from tkinter import messagebox
from utils import extrair_dados_variaveis, APAC_PDF, buscar_nome_medico_por_cns, extrair, buscar_descricao_cid

# ==============================================================================
# DADOS FIXOS - ESPECÍFICOS PARA OCI DE OFTALMOLOGIA
# ==============================================================================
DADOS_FIXOS_OFTALMOLOGIA = {
    "PROC_PRINCIPAL_COD": "03.01.01.007-2",
    "PROC_PRINCIPAL_NOME": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA",
    "PROC_PRINCIPAL_QTD": "1",
    "PROC_SEC1_COD": "02.04.01.026-0",
    "PROC_SEC1_NOME": "TONOMETRIA",
    "PROC_SEC1_QTD": "1",
    "PROC_SEC2_COD": "02.04.01.009-0",
    "PROC_SEC2_NOME": "BIOMICROSCOPIA",
    "PROC_SEC2_QTD": "1",
    "OBSERVACOES": "Paciente com glaucoma.",
    "DESC_DIAGNOSTICO": "" # Será preenchido com a descrição do CID
}


def gerar_apac_oftalmologia(blocos_apac, dados_fixos_genericos):
    """
    Função de orquestração para gerar APACs de Oftalmologia.
    """
    primeiro_bloco = extrair_dados_variaveis(blocos_apac[0]) or {}
    cnes = primeiro_bloco.get('CNES_ESTABELECIMENTO', '')

    pdf = APAC_PDF(orientacao='P', unidade='mm', tamanho='A4')
    
    for bloco in blocos_apac:
        dados_variaveis = extrair_dados_variaveis(bloco) or {}

        # CID principal
        cid = dados_variaveis.get('CID10_PRINCIPAL', '')
        descricao_cid = buscar_descricao_cid(cid) if cid else ''
        cid_completo = f"{cid} - {descricao_cid}" if cid and descricao_cid else cid

        # Médicos
        cns_solicitante = dados_variaveis.get('CNS_SOLICITANTE', '')
        cns_autorizador = dados_variaveis.get('CNS_AUTORIZADOR', '')
        
        nome_solicitante = buscar_nome_medico_por_cns(cns_solicitante)
        nome_autorizador = buscar_nome_medico_por_cns(cns_autorizador)
        
        if not nome_solicitante or not nome_autorizador:
            messagebox.showerror(
                "Erro", 
                f"Médico solicitante ({cns_solicitante}) ou autorizador ({cns_autorizador}) não encontrado no CSV."
            )
            return

        # Preenche dados fixos e variáveis
        dados_fixos_temp = DADOS_FIXOS_OFTALMOLOGIA.copy()
        dados_fixos_temp.update({
            "NOME_SOLICITANTE": nome_solicitante,
            "DOC_SOLICITANTE": cns_solicitante,
            "NOME_AUTORIZADOR": nome_autorizador,
            "DOC_AUTORIZADOR": cns_autorizador,
            "DESC_DIAGNOSTICO": descricao_cid,
            "CID10_PRINCIPAL": cid_completo,
        })
        
        # Junta tudo
        dados_completos = {**dados_fixos_genericos, **dados_fixos_temp, **dados_variaveis}
        dados_completos["CNES_ESTABELECIMENTO"] = cnes

        # Adiciona página no PDF
        pdf.add_apac_page(dados_completos)
    
    # Salvar no diretório Downloads
    pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
    nome_saida = f"apacs_oftalmologia_{cnes}.pdf"
    caminho_completo_saida = os.path.join(pasta_downloads, nome_saida)
    pdf.output(caminho_completo_saida)

    return True