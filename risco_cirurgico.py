# risco_cirurgico.py

import os
import re
from tkinter import messagebox
from fpdf import FPDF
from datetime import datetime
from utils import (
    extrair_dados_variaveis,
    APAC_PDF,
    buscar_nome_medico_por_cns,
    buscar_descricao_cnes_solicitante,
    extrair
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
    # Verifica se há blocos para processar. Se não houver, retorna False.
    if not blocos_apac:
        messagebox.showerror("Erro", "Nenhum bloco de APAC foi encontrado no arquivo de texto.")
        return False
    
    # Cria a instância do objeto PDF aqui, ANTES do loop.
    # Isso garante que a variável 'pdf' esteja sempre definida.
    pdf = APAC_PDF(orientacao='P')

    for i, bloco in enumerate(blocos_apac, 1):
        cns_solicitante = extrair(r'CNS:\s*([\d\s]+)', bloco, re.DOTALL).replace(" ", "")
        
        if not cns_solicitante:
            print(f"[ERRO] Bloco {i}: CNS do solicitante não encontrado. Pulando...")
            continue

        nome_solicitante = str(buscar_nome_medico_por_cns(cns_solicitante))

        if not nome_solicitante:
            print(f"[ERRO] Bloco {i}: Médico solicitante não encontrado para o CNS={cns_solicitante}")
            continue

        # Novo: Tenta extrair o CNS do autorizador de cada bloco
        cns_autorizador = extrair(r'AUTORIZADOR:.*?CNS:\s*([\d\s]+)', bloco, re.DOTALL).replace(" ", "")
        # Novo: Garante que o nome do autorizador seja uma string, mesmo se o CNS for vazio ou não encontrado
        nome_autorizador = str(buscar_nome_medico_por_cns(cns_autorizador))

        cod_cnes_solicitante = dados_fixos_genericos.get("COD_ESTABELECIMENTO", "")
        desc_cnes_solicitante = str(buscar_descricao_cnes_solicitante(cod_cnes_solicitante))
        
        # Agora extrai os dados variáveis.
        dados_variaveis = extrair_dados_variaveis(bloco)
        # Garante que as chaves de CNS estejam no dicionário, mesmo que vazias.
        # Isso é necessário porque a linha de extração foi removida de utils.py
        dados_variaveis["CNS_AUTORIZADOR"] = cns_autorizador
        
        if not dados_variaveis:
            print(f"[ERRO] Bloco {i}: Dados variáveis não encontrados. Pulando...")
            continue
        
        # O CNS do autorizador agora vem do bloco e não do dados_fixos_genericos

        dados_fixos_temp = {
            "PROC_PRINCIPAL_COD": PROC_PRINCIPAL["cod"],
            "PROC_PRINCIPAL_NOME": PROC_PRINCIPAL["descricao"],
            "PROC_PRINCIPAL_QTD": PROC_PRINCIPAL["qtd"],
            "NOME_SOLICITANTE": nome_solicitante,
            "DOC_SOLICITANTE": cns_solicitante,
            "NOME_AUTORIZADOR": nome_autorizador,
            "DOC_AUTORIZADOR": cns_autorizador,
            "NOME_ESTABELECIMENTO": desc_cnes_solicitante or dados_fixos_genericos.get("NOME_ESTABELECIMENTO", ""),
            "COD_ORGAO_EMISSOR": "M351620001",
        }

        for j, sec in enumerate(PROC_SECUNDARIOS, start=1):
            dados_fixos_temp[f"PROC_SEC{j}_COD"] = sec["cod"]
            dados_fixos_temp[f"PROC_SEC{j}_NOME"] = sec["nome"]
            dados_fixos_temp[f"PROC_SEC{j}_QTD"] = sec["qtd"]

        dados_completos = {**dados_fixos_genericos, **dados_fixos_temp, **dados_variaveis}
        # Adiciona a página da APAC ao objeto PDF
        pdf.add_apac_page(dados_completos)

    # Salvar PDF
    # Esta parte do código agora tem a garantia de que 'pdf' foi definido.
    pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    nome_saida = f"apac_risco_cirurgico_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
    caminho_saida = os.path.join(pasta_downloads, nome_saida)
    pdf.output(caminho_saida)
    messagebox.showinfo("Sucesso", f"APACs geradas com sucesso!\nSalvas em: {caminho_saida}")
    return True