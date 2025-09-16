# oftalmologia.py

import os
from tkinter import messagebox
from fpdf import FPDF
from datetime import datetime
from collections import defaultdict
from utils import (
    extrair_dados_variaveis,
    APAC_PDF,
    buscar_nome_medico_por_cns,
    extrair,
    buscar_descricao_cid,
    buscar_descricao_cnes,
    extrair_principal_e_cnes
)


# ======================================================================
# MAPA DE PROCEDIMENTOS - OFTALMOLOGIA
# ======================================================================

MAPA_PROCEDIMENTOS_OFTALMO = {
    "090501003-5": {
        "descricao": "OCI AVAL. INICIAL EM OFTALMO - A PARTIR DE 9 ANOS",
        "secundarios": [
            {"cod": "021106002-0", "nome": "BIOMICROSCOPIA DE FUNDO", "qtd": "1"},
            {"cod": "030101007-2", "nome": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA", "qtd": "2"},
            {"cod": "021106012-7", "nome": "MAPEAMENTO DE RETINA", "qtd": "1"},
            {"cod": "021106023-2", "nome": "TESTE ORTOTOPTICO", "qtd": "1"},
            {"cod": "021106025-9", "nome": "TONOMETRIA", "qtd": "1"},
        ]
    },
    "090501001-9": {
        "descricao": "OCI AVAL. INICIAL EM OFTALMO - 0 A 8 ANOS",
        "secundarios": [
            {"cod": "021106002-0", "nome": "BIOMICROSCOPIA DE FUNDO", "qtd": "1"},
            {"cod": "030101007-2", "nome": "CONSULTA MEDICA EM ATENCAO ESPECIALIZADA", "qtd": "2"},
            {"cod": "021106012-7", "nome": "MAPEAMENTO DE RETINA", "qtd": "1"},
            {"cod": "021106023-2", "nome": "TESTE ORTOTOPTICO", "qtd": "1"},
        ]
    }
}


# ======================================================================
# FUNÇÃO PRINCIPAL
# ======================================================================

def gerar_apac_oftalmologia(blocos_apac, dados_fixos_genericos):
    if not blocos_apac:
        messagebox.showerror("Erro", "Nenhum bloco de APAC foi encontrado no arquivo de texto.")
        return False

    erros = []
    pdfs_por_cnes = {}
    resumo_por_cnes = defaultdict(lambda: {"total": 0, "procedimentos": defaultdict(int)})

    for bloco in blocos_apac:
        dados_variaveis = extrair_dados_variaveis(bloco)
        if not dados_variaveis:
            continue

        proc_principal, cod_cnes_solicitante = extrair_principal_e_cnes(bloco)

        if not proc_principal:
            numero_apac = dados_variaveis.get("NUMERO_APAC", "DESCONHECIDO")
            erros.append(f"{numero_apac} - Procedimento principal não encontrado")
            continue

        mapa = MAPA_PROCEDIMENTOS_OFTALMO.get(proc_principal)
        if not mapa:
            numero_apac = dados_variaveis.get("NUMERO_APAC", "DESCONHECIDO")
            erros.append(f"{numero_apac} - Procedimento principal não mapeado ({proc_principal})")
            continue

        # Dados complementares
        codigo_cid = dados_variaveis.get("CID10_PRINCIPAL", "")
        descricao_cid = buscar_descricao_cid(codigo_cid)

        cns_solicitante = str(dados_variaveis.get("CNS_SOLICITANTE", "")).replace(" ", "")
        nome_solicitante = buscar_nome_medico_por_cns(cns_solicitante) or ""

        cns_autorizador = str(dados_variaveis.get("CNS_AUTORIZADOR", "")).replace(" ", "")
        nome_autorizador = buscar_nome_medico_por_cns(cns_autorizador) or ""

        cod_cnes_executante = dados_variaveis.get("CNES_ESTABELECIMENTO", "") or ""
        desc_cnes_executante = buscar_descricao_cnes(cod_cnes_executante) or ""
        desc_cnes_solicitante = buscar_descricao_cnes(cod_cnes_solicitante) if cod_cnes_solicitante else ""

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
            "NOME_ESTABELECIMENTO": desc_cnes_executante,
            "CNES_ESTABELECIMENTO": cod_cnes_executante,
            "NOME_ESTAB_SOLICITANTE": desc_cnes_solicitante,
            "CNES_SOLICITANTE": cod_cnes_solicitante,
            "OBSERVACOES": "Avaliação oftalmológica de rotina",
        }

        for j, sec in enumerate(mapa["secundarios"], start=1):
            dados_fixos_temp[f"PROC_SEC{j}_COD"] = sec["cod"]
            dados_fixos_temp[f"PROC_SEC{j}_NOME"] = sec["nome"]
            dados_fixos_temp[f"PROC_SEC{j}_QTD"] = sec["qtd"]

        dados_completos = {**dados_fixos_genericos, **dados_fixos_temp, **dados_variaveis}

        # Cria PDF para o CNES
        if cod_cnes_solicitante not in pdfs_por_cnes:
            pdfs_por_cnes[cod_cnes_solicitante] = APAC_PDF(orientacao='P')

        # Adiciona página
        pdfs_por_cnes[cod_cnes_solicitante].add_apac_page(dados_completos)

        # Atualiza resumo
        resumo_por_cnes[cod_cnes_solicitante]["total"] += 1
        resumo_por_cnes[cod_cnes_solicitante]["procedimentos"][mapa["descricao"]] += 1

    # -----------------------
    # Salvar PDFs separados
    # -----------------------
    pasta_downloads = os.path.join(os.path.expanduser("~"), "Downloads")
    for cnes, pdf in pdfs_por_cnes.items():
        nome_paciente_limpo = dados_fixos_genericos.get("NOME_PACIENTE", "desconhecido").replace(' ', '_')
        nome_saida = f"apac_oftalmo_{nome_paciente_limpo}_{cnes}_{datetime.now().strftime('%Y%m%d%H%M%S')}.pdf"
        caminho_saida = os.path.join(pasta_downloads, nome_saida)
        try:
            pdf.output(caminho_saida)
        except Exception as e:
            messagebox.showerror("Erro", f"Falha ao salvar PDF para CNES {cnes}: {e}")

    # -----------------------
    # Salvar arquivo de erros
    # -----------------------
    if erros:
        caminho_erros = os.path.join(pasta_downloads, f"apac_erros_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt")
        with open(caminho_erros, "w", encoding="utf-8") as f:
            f.write("\n".join(erros))

    # -----------------------
    # Salvar contagem detalhada
    # -----------------------
    if resumo_por_cnes:
        caminho_contagem = os.path.join(
            pasta_downloads,
            f"apac_contagem_{datetime.now().strftime('%Y%m%d%H%M%S')}.txt"
        )

        numeros_apac = []
        for bloco in blocos_apac:
            dados_variaveis = extrair_dados_variaveis(bloco)
            if not dados_variaveis:
                continue
            num = dados_variaveis.get("NUMERO_APAC", "")
            if num:
                numeros_apac.append(num)

        menor_apac, maior_apac = "", ""
        if numeros_apac:
            nums_ordenados = sorted(numeros_apac, key=lambda x: x[:-1])
            menor_apac, maior_apac = nums_ordenados[0], nums_ordenados[-1]

        with open(caminho_contagem, "w", encoding="utf-8") as f:
            total_geral = 0
            for cnes, dados in resumo_por_cnes.items():
                f.write(f"CNES {cnes}: {dados['total']} APAC(s)\n")
                for proc, qtd in dados["procedimentos"].items():
                    f.write(f"{proc}: {qtd}\n")
                f.write("\n")
                total_geral += dados['total']

            f.write(f"Total Geral: {total_geral}\n\n")

            if menor_apac and maior_apac:
                f.write(f"APAC Inicial: {menor_apac}\n")
                f.write(f"APAC Final: {maior_apac}\n")

    # -----------------------
    # Mensagem final
    # -----------------------
    msg = "APACs de oftalmologia geradas com sucesso.\n\n"
    msg += f"Arquivos salvos em: {pasta_downloads}\n"
    if erros:
        msg += f"\nAlguns blocos apresentaram problemas. Consulte o arquivo de erros."
    messagebox.showinfo("Processo Concluído", msg)

    return True
