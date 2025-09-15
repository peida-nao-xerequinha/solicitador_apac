# oftalmologia.py

import os
from tkinter import messagebox
from fpdf import FPDF
from datetime import datetime
from utils import (
    extrair_dados_variaveis,
    APAC_PDF,
    buscar_nome_medico_por_cns,
    extrair,
    buscar_descricao_cid,
    # ATUALIZADO: Importa a nova função com o nome correto
    buscar_descricao_cnes,
    extrair_principal_e_cnes
)


# ==============================================================================
# MAPA DE PROCEDIMENTOS - OFTALMOLOGIA
# ==============================================================================

MAPA_PROCEDIMENTOS_OFTALMO = {
    "090501003-5": { 
        "descricao": "OCI AVALIAÇÃO INICIAL EM OFTALMOLOGIA - A PARTIR DE 9 ANOS",
        "secundarios": [
            {"cod": "021106002-0", "nome": "BIOMICROSCOPIA DE FUNDO", "qtd": "1"},
            {"cod": "030101007-2", "nome": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA", "qtd": "2"},
            {"cod": "021106012-7", "nome": "MAPEAMENTO DE RETINA", "qtd": "1"},
            {"cod": "021106023-2", "nome": "TESTE ORTOTOPTICO", "qtd": "1"},
            {"cod": "021106025-9", "nome": "TONOMETRIA", "qtd": "1"},
        ]
    },
    "090501001-9": { 
        "descricao": "OCI AVALIAÇÃO INICIAL EM OFTALMOLOGIA - 0 A 8 ANOS",
        "secundarios": [
            {"cod": "021106002-0", "nome": "BIOMICROSCOPIA DE FUNDO", "qtd": "1"},
            {"cod": "030101007-2", "nome": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA", "qtd": "2"},
            {"cod": "021106012-7", "nome": "MAPEAMENTO DE RETINA", "qtd": "1"},
            {"cod": "021106023-2", "nome": "TESTE ORTOTOPTICO", "qtd": "1"},
        ]
    }
}


# ==============================================================================
# FUNÇÃO PRINCIPAL
# ==============================================================================

def gerar_apac_oftalmologia(blocos_apac, dados_fixos_genericos):
    if not blocos_apac:
        messagebox.showerror("Erro", "Nenhum bloco de APAC foi encontrado no arquivo de texto.")
        return False

    pdf = APAC_PDF(orientacao='P')

    for bloco in blocos_apac:
        # Extrai os dados variáveis de cada bloco
        dados_variaveis = extrair_dados_variaveis(bloco)
        
        # Pula se não encontrar os dados essenciais
        if not dados_variaveis:
            continue
        
        # Extrai o procedimento principal para encontrar o mapa
        proc_principal, _ = extrair_principal_e_cnes(bloco)
        
        # Se o procedimento principal não for encontrado, pula para o próximo bloco
        if not proc_principal:
            messagebox.showwarning("Aviso", "Procedimento principal não encontrado. Pulando este bloco.")
            continue

        # Novo: Busca o mapa de procedimentos com base no proc_principal extraído
        mapa = MAPA_PROCEDIMENTOS_OFTALMO.get(proc_principal)

        if not mapa:
            messagebox.showwarning("Aviso", f"Procedimento principal não mapeado: {proc_principal}. Pulando este bloco.")
            continue

        # Pega o CID e busca a descrição (melhor prática)
        codigo_cid = dados_variaveis.get("CID10_PRINCIPAL", "")
        descricao_cid = buscar_descricao_cid(codigo_cid)

        # Garante que os valores de CNS sejam strings, para evitar TypeErrors
        cns_solicitante = str(dados_variaveis.get("CNS_SOLICITANTE", ""))
        nome_solicitante = str(buscar_nome_medico_por_cns(cns_solicitante))
        
        cns_autorizador = str(dados_variaveis.get("CNS_AUTORIZADOR", ""))
        nome_autorizador = str(buscar_nome_medico_por_cns(cns_autorizador))
        
        # CORREÇÃO: Pega o CNES do estabelecimento diretamente dos dados variáveis
        cod_cnes_executante = dados_variaveis.get("CNES_ESTABELECIMENTO", "")
        # E busca a descrição a partir desse CNES usando a nova função
        desc_cnes_executante = str(buscar_descricao_cnes(cod_cnes_executante))

        # Novo: Usa o 'proc_principal' e 'mapa' para popular os dados
        dados_fixos_temp = {
            "PROC_PRINCIPAL_COD": proc_principal,
            "PROC_PRINCIPAL_NOME": mapa["descricao"],
            "PROC_PRINCIPAL_QTD": "1",
            "NOME_SOLICITANTE": nome_solicitante,
            "DOC_SOLICITANTE": cns_solicitante,
            "NOME_AUTORIZADOR": nome_autorizador,
            "DOC_AUTORIZADOR": cns_autorizador,
            "DESC_DIAGNOSTICO": descricao_cid,
            "CID10_PRINCIPAL": codigo_cid,
            "COD_ORGAO_EMISSOR": "M351620001",
            # CORREÇÃO: Usa a descrição do CNES do estabelecimento extraído do bloco
            "NOME_ESTABELECIMENTO": desc_cnes_executante or dados_fixos_genericos.get("NOME_ESTABELECIMENTO", ""),
        }

        # Adiciona os procedimentos secundários dinamicamente
        for j, sec in enumerate(mapa["secundarios"], start=1):
            dados_fixos_temp[f"PROC_SEC{j}_COD"] = sec["cod"]
            dados_fixos_temp[f"PROC_SEC{j}_NOME"] = sec["nome"]
            dados_fixos_temp[f"PROC_SEC{j}_QTD"] = sec["qtd"]

        dados_completos = {**dados_fixos_genericos, **dados_fixos_temp, **dados_variaveis}
        pdf.add_apac_page(dados_completos)

    # Salvar PDF - MOVIDO PARA FORA DO LOOP
    pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    nome_paciente_limpo = dados_fixos_genericos.get("NOME_PACIENTE", "desconhecido").replace(' ', '_')
    nome_saida = f"apac_oftalmo_{nome_paciente_limpo}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    caminho_saida = os.path.join(pasta_downloads, nome_saida)
    pdf.output(caminho_saida)
    messagebox.showinfo("Sucesso", f"APACs geradas com sucesso!\nSalvas em: {caminho_saida}")
    return True