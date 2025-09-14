# utils.py

import re
import os
import sys
import csv
from fpdf import FPDF
from tkinter import filedialog, messagebox

# ==============================================================================
# FUNÇÕES DE UTILIDADE GERAL
# ==============================================================================

def extrair(pattern, texto, flags=0):
    """Extrai um valor de um texto usando regex, com suporte a flags."""
    match = re.search(pattern, texto, flags)
    return match.group(1).strip() if match else ""

def extrair_principal_e_cnes(bloco):
    """
    Extrai apenas:
    - o primeiro código de procedimento (PROC_PRINCIPAL)
    - o CNES do primeiro procedimento que tiver CNES preenchido
    """
    proc_principal = ""
    cnes_solicitante = ""

    # Captura toda a seção de procedimentos até "MOTIVO DE SAIDA"
    secao = re.search(r'PROCEDIMENTOS REALIZADOS:(.*?)(?=MOTIVO DE SAIDA)', 
                      bloco, re.DOTALL | re.IGNORECASE)
    
    if secao:
        linhas = secao.group(1).split('\n')
        for linha in linhas:
            linha = linha.strip()
            if not linha or "CODIGO" in linha:
                continue

            # Pega o código do procedimento (primeiros 9+1 dígitos)
            if not proc_principal:
                match_codigo = re.search(r'(\d{9}-\d)', linha)
                if match_codigo:
                    proc_principal = match_codigo.group(1).strip()

            # Pega o CNES (último número na linha, se existir)
            if not cnes_solicitante:
                match_cnes = re.search(r'(\d{6,7})\s*$', linha)
                if match_cnes:
                    cnes_solicitante = match_cnes.group(1).strip()

            # Se já encontrou os dois, sai do loop
            if proc_principal and cnes_solicitante:
                break

    return proc_principal, cnes_solicitante


def extrair_dados_variaveis(bloco):
    """Extrai apenas os dados variáveis de um bloco de texto da APAC."""
    if "NUMERO DO APAC" not in bloco:
        return {}
    
    rua = extrair(r'ENDERECO:\s+([^\n]+)', bloco)
    numero = extrair(r'NUMERO:\s+([\d]+)', bloco)
    bairro = extrair(r'BAIRRO:\s+([^\n]+)', bloco)
    endereco_completo = f"{rua}, {numero} - {bairro}"


    dados = {
        "CPF_PACIENTE": extrair(r'CPF:\s+([\d\.\-]+)', bloco),
        "NOME_PACIENTE": extrair(r'NOME:\s+([^\n]+)', bloco),
        "SEXO": extrair(r'SEXO:\s+(MASCULINO|FEMININO)', bloco),
        "DATA_NASCIMENTO": extrair(r'DATA DE NASCIMENTO:\s+([\d/]+)', bloco),
        "RACA_COR": extrair(r'RACA:\s+([^\n]+)', bloco).split(" ")[0],
        "NOME_MAE": extrair(r'NOME DA MAE:\s+([^\n]+)', bloco),
        "NOME_RESPONSAVEL": extrair(r'NOME DO RES:\s+([^\n]+)', bloco),
        "ENDERECO": endereco_completo,
        "CEP": extrair(r'CEP:\s+([\d\-]+)', bloco),
        "DATA_SOLICITACAO": extrair(r'INICIO DA VALIDADE DA APAC:\s+([\d/]+)', bloco),
        "VALIDADE_FIM": extrair(r'FIM DA VALIDADE DO APAC:\s+([\d/]+)', bloco),
        "NUMERO_APAC": extrair(r'NUMERO DO APAC:\s+([\d\-]+)', bloco),
        "CNS_SOLICITANTE": extrair(r'CNS:\s*([\d\s]+)', bloco, re.DOTALL).replace(" ", ""),
        "CNES_ESTABELECIMENTO": extrair(r'CODIGO DA UNIDADE:\s*([\d-]+)', bloco),
        "CID10_PRINCIPAL": extrair(r'C\.I\.D\. PRINCIPAL\s*([A-Z]\d{2,3})', bloco),
    }

    # A lógica de processar procedimentos foi movida para as funções específicas de cada APAC.
    # Por isso, o bloco de código abaixo foi removido.
    # if procedimentos:
    #    ...
    # return dados

    return dados

# O restante do seu arquivo utils.py...

_estabelecimentos_cache = None

def buscar_nome_medico_por_cns(cns, caminho_csv='medicos.csv'):
    """Busca o nome do médico em um arquivo CSV a partir do Cartão Nacional de Saúde (CNS)."""
    if not cns:
        return None
    
    if not os.path.exists(caminho_csv):
        print(f"ERRO: Arquivo '{caminho_csv}' não encontrado.")
        return None

    try:
        with open(caminho_csv, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                if row['cartao_sus'].strip() == cns.strip():
                    return row['nome_completo']
    except Exception as e:
        print(f"ERRO ao ler o arquivo CSV: {e}")
        return None
    return None

def buscar_descricao_cid(codigo_cid):
    """Busca a descrição de um CID em um arquivo CSV."""
    caminho_csv = os.path.join(os.path.dirname(__file__), 'cid_oftalmologia.csv')
    if not os.path.exists(caminho_csv):
        messagebox.showerror("Erro", f"Arquivo CSV não encontrado: {caminho_csv}")
        return None

    with open(caminho_csv, mode='r', encoding='utf-8') as file:
        reader = csv.DictReader(file, delimiter=';')
        for row in reader:
            if row['codigo'].strip().upper() == codigo_cid.strip().upper():
                return row['descricao']
    return "Descrição não encontrada"

def buscar_descricao_cnes_solicitante(cnes_solicitante, caminho_csv='estabelecimentos.csv'):
    """Busca a descrição de um CNES solicitante em um arquivo CSV."""
    if not cnes_solicitante:
        return "" # Retorna string vazia para evitar TypeError

    if not os.path.exists(caminho_csv):
        print(f"ERRO: Arquivo '{caminho_csv}' não encontrado.")
        return "" # Retorna string vazia para evitar TypeError

    try:
        with open(caminho_csv, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                if row['cod_solicitante'].strip() == cnes_solicitante.strip().replace('-', ''):
                    return row['desc_solicitante']
    except Exception as e:
        print(f"ERRO ao ler o arquivo CSV: {e}")
        return "" # Retorna string vazia para evitar TypeError
    return "" # Retorna string vazia para o caso de não encontrar
    
# ==============================================================================
# CLASSE PARA GERAÇÃO DO PDF
# ==============================================================================

class APAC_PDF(FPDF):
    def __init__(self, orientacao='P', unidade='mm', tamanho='A4'):
        super().__init__(orientation=orientacao, unit=unidade, format=tamanho)
        self.set_auto_page_break(auto=True, margin=5)
        
    def add_apac_page(self, data):
        self.add_page()
        
        if getattr(sys, 'frozen', False):
            application_path = os.path.dirname(sys.executable)
        else:
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        template_path = os.path.join(application_path, "template.png")
        
        if os.path.exists(template_path):
            self.image(template_path, x=0, y=0, w=210, h=297)
        else:
            messagebox.showerror("Erro Fatal", "Arquivo 'template.png' não encontrado. Por favor, coloque-o na mesma pasta do executável.")
            return

        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        self.set_xy(13, 32); self.cell(100, 5, data.get("NOME_ESTABELECIMENTO", ""))
        self.set_xy(168, 32); self.cell(50, 5, data.get("CNES_ESTABELECIMENTO", ""))
        self.set_xy(13, 46.5); self.cell(100, 5, data.get("NOME_PACIENTE", ""))
        
        original_font_size = self.font_size_pt
        self.set_font_size(7)
        if data.get("SEXO") == "MASCULINO":
            self.set_xy(148.8, 47.5); self.cell(w=3, h=3, text="X", border=0, align='C')
        elif data.get("SEXO") == "FEMININO":
            self.set_xy(160.8, 47.5); self.cell(w=3, h=3, text="X", border=0, align='C')
        self.set_font_size(original_font_size)
        
        self.set_xy(13, 55.2); self.cell(90, 5, data.get("CPF_PACIENTE", ""))
        self.set_xy(112, 55.2); self.cell(40, 5, data.get("DATA_NASCIMENTO", ""))
        self.set_xy(148, 55.2); self.cell(15, 5, data.get("RACA_COR", ""))
        self.set_xy(13, 62.7); self.cell(100, 5, data.get("NOME_MAE", ""))
        self.set_xy(13, 72.5); self.cell(100, 5, data.get("NOME_RESPONSAVEL", ""))
        self.set_xy(13, 80); self.cell(150, 5, data.get("ENDERECO", ""))
        self.set_xy(13, 88.5); self.cell(50, 5, data.get("MUNICIPIO_RESIDENCIA", ""))
        self.set_xy(130, 88.5); self.cell(50, 5, data.get("COD_IBGE_MUNICIPIO", ""))
        self.set_xy(155, 88.5); self.cell(20, 5, data.get("UF", ""))
        self.set_xy(167, 88.5); self.cell(40, 5, data.get("CEP", ""))

        self.set_xy(11.7, 103); self.cell(40, 5, data.get("PROC_PRINCIPAL_COD", ""))
        self.set_xy(78, 103); self.cell(120, 5, data.get("PROC_PRINCIPAL_NOME", ""))
        self.set_xy(180, 103); self.cell(10, 5, data.get("PROC_PRINCIPAL_QTD", ""))
        self.set_xy(11.7, 118.5); self.cell(40, 5, data.get("PROC_SEC1_COD", ""))
        self.set_xy(78, 118.5); self.cell(120, 5, data.get("PROC_SEC1_NOME", ""))
        self.set_xy(182, 118.5); self.cell(10, 5, data.get("PROC_SEC1_QTD", ""))
        self.set_xy(11.7, 127.5); self.cell(40, 5, data.get("PROC_SEC2_COD", ""))
        self.set_xy(78, 127.5); self.cell(120, 5, data.get("PROC_SEC2_NOME", ""))
        self.set_xy(182, 127.5); self.cell(10, 5, data.get("PROC_SEC2_QTD", ""))
        self.set_xy(11.7, 136.5); self.cell(40, 5, data.get("PROC_SEC3_COD", ""))
        self.set_xy(78, 136.5); self.cell(120, 5, data.get("PROC_SEC3_NOME", ""))
        self.set_xy(182, 136.5); self.cell(10, 5, data.get("PROC_SEC3_QTD", ""))
        self.set_xy(11.7, 145.5); self.cell(40, 5, data.get("PROC_SEC4_COD", ""))
        self.set_xy(78, 145.5); self.cell(120, 5, data.get("PROC_SEC4_NOME", ""))
        self.set_xy(182, 145.5); self.cell(10, 5, data.get("PROC_SEC4_QTD", ""))
        self.set_xy(11.7, 154.5); self.cell(40, 5, data.get("PROC_SEC5_COD", ""))
        self.set_xy(78, 154.5); self.cell(120, 5, data.get("PROC_SEC5_NOME", ""))
        self.set_xy(182, 154.5); self.cell(10, 5, data.get("PROC_SEC5_QTD", ""))

        self.set_xy(14, 173); self.cell(100, 5, data.get("DESC_DIAGNOSTICO", ""))
        self.set_xy(14, 185); self.cell(80, 5, data.get("OBSERVACOES", ""))
        self.set_xy(125, 173); self.cell(80, 5, data.get("CID10_PRINCIPAL", ""))
        
        self.set_xy(13, 222); self.cell(100, 5, data.get("NOME_SOLICITANTE", ""))
        self.set_xy(55, 230); self.cell(60, 5, data.get("DOC_SOLICITANTE", ""))
        self.set_xy(110, 222); self.cell(40, 5, data.get("DATA_SOLICITACAO", ""))
        self.set_xy(18.8, 230.9); self.cell(w=2, h=2, text="X", border=0, align='C')
        
        self.set_xy(13, 246); self.cell(60, 5, data.get("NOME_AUTORIZADOR", ""))
        self.set_xy(105, 246); self.cell(60, 5, data.get("COD_ORGAO_EMISSOR", ""))
        self.set_xy(55, 257.5); self.cell(60, 5, data.get("DOC_AUTORIZADOR", ""))
        self.set_xy(140, 246); self.cell(60, 5, data.get("NUMERO_APAC", ""))
        self.set_xy(13, 270); self.cell(60, 5, data.get("DATA_SOLICITACAO", ""))
        self.set_xy(147, 270); self.cell(60, 5, f"{data.get('DATA_SOLICITACAO', '')}    {data.get('VALIDADE_FIM', '')}")
        self.set_xy(18.8, 257.9); self.cell(w=2, h=2, text="X", border=0, align='C')

        self.set_xy(13, 283); self.cell(100, 5, data.get("NOME_EXECUTANTE", ""))
        self.set_xy(165, 283); self.cell(50, 5, data.get("CNES_ESTABELECIMENTO", ""))