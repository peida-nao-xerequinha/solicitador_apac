# risco_cirurgico.py

import os
from tkinter import messagebox
from fpdf import FPDF
from datetime import datetime
from utils import (
    extrair_dados_variaveis,
    extrair_principal_e_cnes,
    APAC_PDF,
    buscar_nome_medico_por_cns,
    buscar_descricao_cnes,
    buscar_descricao_cid
)

# ============================================================================== 
# CONFIGURAÇÃO FIXA PARA RISCO CIRÚRGICO
# ==============================================================================

PROC_PRINCIPAL = {
    "cod": "020101001-0",
    "descricao": "OCI AVALIACAO DE RISCO CIRURGICO",
    "qtd": "1"
}

PROC_SECUNDARIOS = [
    {"cod": "021402001-0", "nome": "ELETROCARDIOGRAMA", "qtd": "1"},
    {"cod": "030101007-2", "nome": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA", "qtd": "2"},
]

# ============================================================================== 
# FUNÇÃO PRINCIPAL
# ==============================================================================

def gerar_apac_risco_cirurgico(blocos_apac, dados_fixos_genericos):
    if not blocos_apac:
        messagebox.showerror("Erro", "Nenhum bloco de APAC foi encontrado no arquivo de texto.")
        return False
    
    pdf = APAC_PDF(orientacao='P')

    # CNES padrão do estabelecimento
    cnes_padrao = str(dados_fixos_genericos.get("COD_ESTABELECIMENTO", "2087669"))
    desc_cnes_padrao = str(buscar_descricao_cnes(cnes_padrao))

    for bloco in blocos_apac:
        # Extrai dados variáveis do bloco
        dados_variaveis = extrair_dados_variaveis(bloco)
        if not dados_variaveis:
            continue

        # Tenta extrair o CNES do bloco (caso exista)
        _, cnes_solicitante = extrair_principal_e_cnes(bloco)
        if not cnes_solicitante:
            cnes_solicitante = cnes_padrao
        desc_cnes_solicitante = str(buscar_descricao_cnes(cnes_solicitante))

        cid_principal = dados_variaveis.get("CID10_PRINCIPAL", "")
        desc_cid_principal = buscar_descricao_cid(cid_principal)

        cns_solicitante = str(dados_variaveis.get("CNS_SOLICITANTE", ""))
        nome_solicitante = str(buscar_nome_medico_por_cns(cns_solicitante))
        
        cns_autorizador = str(dados_variaveis.get("CNS_AUTORIZADOR", ""))
        nome_autorizador = str(buscar_nome_medico_por_cns(cns_autorizador))

        dados_fixos_temp = {
            "PROC_PRINCIPAL_COD": PROC_PRINCIPAL["cod"],
            "PROC_PRINCIPAL_NOME": PROC_PRINCIPAL["descricao"],
            "PROC_PRINCIPAL_QTD": PROC_PRINCIPAL["qtd"],
            "NOME_SOLICITANTE": nome_solicitante,
            "DOC_SOLICITANTE": cns_solicitante,
            "NOME_AUTORIZADOR": nome_autorizador,
            "DOC_AUTORIZADOR": cns_autorizador,
            "NOME_ESTABELECIMENTO": dados_fixos_genericos.get("NOME_ESTABELECIMENTO", ""),
            "CNES_SOLICITANTE": cnes_solicitante,
            "NOME_ESTAB_SOLICITANTE": desc_cnes_solicitante,
            "COD_ORGAO_EMISSOR": "M351620001",
            "OBSERVACOES": "Avaliação cardiológica pré-operatória",
        }

        for j, sec in enumerate(PROC_SECUNDARIOS, start=1):
            dados_fixos_temp[f"PROC_SEC{j}_COD"] = sec["cod"]
            dados_fixos_temp[f"PROC_SEC{j}_NOME"] = sec["nome"]
            dados_fixos_temp[f"PROC_SEC{j}_QTD"] = sec["qtd"]

        # Combina todos os dados
        dados_completos = {
            **dados_fixos_genericos,
            **dados_fixos_temp,
            **dados_variaveis,
            "DESC_DIAGNOSTICO": desc_cid_principal,
            "CID10_PRINCIPAL": cid_principal
        }
        
        # Debug real para CNES
       # print(f"CNES do solicitante usado: {cnes_solicitante}, descrição: {desc_cnes_solicitante}")

        pdf.add_apac_page(dados_completos)

    # Salvar PDF
    pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    nome_paciente_limpo = dados_fixos_genericos.get("NOME_PACIENTE", "desconhecido").replace(' ', '_')
    nome_saida = f"apac_risco_cirurgico_{nome_paciente_limpo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    caminho_saida = os.path.join(pasta_downloads, nome_saida)
    pdf.output(caminho_saida)
    messagebox.showinfo("Sucesso", f"APACs geradas com sucesso!\nSalvas em: {caminho_saida}")
    return True
