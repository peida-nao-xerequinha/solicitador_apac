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
    buscar_descricao_cnes_solicitante
)


# ==============================================================================
# MAPA DE PROCEDIMENTOS - OFTALMOLOGIA
# ==============================================================================

MAPA_PROCEDIMENTOS_OFTALMO = {
    "090501003-5": {  # A partir de 9 anos - CORRIGIDO (sem pontos)
        "descricao": "OCI AVALIAÇÃO INICIAL EM OFTALMOLOGIA - A PARTIR DE 9 ANOS",
        "secundarios": [
            {"cod": "021106002-0", "nome": "BIOMICROSCOPIA DE FUNDO", "qtd": "1"},
            {"cod": "030101007-2", "nome": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA", "qtd": "2"},
            {"cod": "021106012-7", "nome": "MAPEAMENTO DE RETINA", "qtd": "1"},
            {"cod": "021106023-2", "nome": "TESTE ORTOTOPTICO", "qtd": "1"},
            {"cod": "021106025-9", "nome": "TONOMETRIA", "qtd": "1"},
        ]
    },
    "090501001-9": {  # 0 a 8 anos
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
        dados_variaveis = extrair_dados_variaveis(bloco)
        if not dados_variaveis:
            continue

        # Extrai o código do procedimento principal e remove espaços e hífens.
        codigo_principal = extrair(r'PROCEDIMENTO PRINCIPAL:\s*([\d-]+)', bloco).replace(" ", "").replace("-", "")
        
        mapa = MAPA_PROCEDIMENTOS_OFTALMO.get(codigo_principal)

        if not mapa:
            messagebox.showwarning("Aviso", f"Procedimento principal não mapeado: {codigo_principal}. Pulando este bloco.")
            continue

        codigo_cid = extrair(r'C\.I\.D\. PRINCIPAL\s*([A-Z]\d+)', bloco)
        descricao_cid = buscar_descricao_cid(codigo_cid)

        # Usando dados do bloco para preencher campos
        cns_solicitante = extrair(r'CNS:\s*([\d]+)', bloco, re.DOTALL)
        nome_solicitante = buscar_nome_medico_por_cns(cns_solicitante)
        
        cns_autorizador = dados_fixos_genericos.get("CNS_AUTORIZADOR", "")
        nome_autorizador = buscar_nome_medico_por_cns(cns_autorizador)
        
        # A informação do CNES solicitante já vem de main.py, então vamos usá-la
        cod_cnes_solicitante = dados_fixos_genericos.get("COD_ESTABELECIMENTO", "")
        desc_cnes_solicitante = buscar_descricao_cnes_solicitante(cod_cnes_solicitante)

        dados_fixos_temp = {
            "PROC_PRINCIPAL_COD": codigo_principal,
            "PROC_PRINCIPAL_NOME": mapa["descricao"],
            "PROC_PRINCIPAL_QTD": "1",
            "NOME_SOLICITANTE": nome_solicitante,
            "DOC_SOLICITANTE": cns_solicitante,
            "NOME_AUTORIZADOR": nome_autorizador,
            "DOC_AUTORIZADOR": cns_autorizador,
            "DESC_DIAGNOSTICO": descricao_cid,
            "CID10_PRINCIPAL": codigo_cid,
            "COD_ORGAO_EMISSOR": "M351620001",
            "NOME_ESTABELECIMENTO": desc_cnes_solicitante or dados_fixos_genericos.get("NOME_ESTABELECIMENTO", ""),
        }

        # Adiciona os procedimentos secundários dinamicamente
        for i, sec in enumerate(mapa["secundarios"], start=1):
            dados_fixos_temp[f"PROC_SEC{i}_COD"] = sec["cod"]
            dados_fixos_temp[f"PROC_SEC{i}_NOME"] = sec["nome"]
            dados_fixos_temp[f"PROC_SEC{i}_QTD"] = sec["qtd"]

        dados_completos = {**dados_fixos_genericos, **dados_fixos_temp, **dados_variaveis}
        pdf.add_apac_page(dados_completos)

    # Salvar PDF
    pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    nome_saida = f"apac_oftalmo_{dados_fixos_genericos.get('NOME_PACIENTE', 'desconhecido').replace(' ', '_')}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    caminho_saida = os.path.join(pasta_downloads, nome_saida)
    pdf.output(caminho_saida)
    messagebox.showinfo("Sucesso", f"APACs geradas com sucesso!\nSalvas em: {caminho_saida}")
    return True