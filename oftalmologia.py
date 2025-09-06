# oftalmologia.py

from utils import extrair_dados_variaveis, APAC_PDF, buscar_nome_medico_por_cns

# ==============================================================================
# DADOS FIXOS - ESPECÍFICOS PARA OCI DE OFTALMOLOGIA
# ==============================================================================
DADOS_FIXOS_OFTALMOLOGIA = {
    "PROC_PRINCIPAL_COD": "04.05.01.002-8",
    "PROC_PRINCIPAL_NOME": "OCI DE OFTALMOLOGIA",
    "PROC_PRINCIPAL_QTD": "1",
    "PROC_SEC1_COD": "02.04.03.001-0",
    "PROC_SEC1_NOME": "MAPEAMENTO DE RETINA",
    "PROC_SEC1_QTD": "1",
    "PROC_SEC2_COD": "03.01.01.007-2",
    "PROC_SEC2_NOME": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA",
    "PROC_SEC2_QTD": "1",
    "DESC_DIAGNOSTICO": "AVALIACAO DE RETINA",
    "CID10_PRINCIPAL": "H353",
    "OBSERVACOES": "ROTINA ANUAL",
    "NOME_SOLICITANTE": "ANA LUIZA TEIXEIRA - CRM/SP 85934",
    "DOC_SOLICITANTE": "207274333200006",
    "NOME_AUTORIZADOR": "MARIO ROBERTO ALVES - CRM/SP 78563",
    "COD_ORGAO_EMISSOR": "M351620002",
    "DOC_AUTORIZADOR": "702402512360420",
    "NOME_EXECUTANTE": "NGA 16",
    "CNES_EXECUTANTE": "2087669",
}

def gerar_apac_oftalmologia(caminho_arquivo):
    """
    Função de orquestração para gerar APACs de Oftalmologia.
    """
    # A lógica de processamento e geração será feita no main.py
    # Essa função irá apenas sinalizar que está pronta.
    print(f"Lógica de geração para Oftalmologia acionada com o arquivo: {caminho_arquivo}")
    return True