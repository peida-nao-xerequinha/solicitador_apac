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

def extrair_dados_variaveis(bloco):
    """Extrai apenas os dados variáveis de um bloco de texto da APAC."""
    if "NUMERO DO APAC" not in bloco:
        return None

    # Extrai as partes separadas do endereço
    rua = extrair(r'ENDERECO:\s+([^\n]+)', bloco)
    numero = extrair(r'NUMERO:\s+([\d]+)', bloco)
    bairro = extrair(r'BAIRRO:\s+([^\n]+)', bloco)

    # Junta as partes para formar o endereço completo
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
        "DATA_AUTORIZACAO": extrair(r'DATA DA OCORRENCIA:\s+([\d/]+)', bloco),
        "VALIDADE_FIM": extrair(r'FIM DA VALIDADE DO APAC:\s+([\d/]+)', bloco),
        "NUMERO_APAC": extrair(r'NUMERO DO APAC:\s+([\d\-]+)', bloco),
        # Extrai o CNS do profissional solicitante
        "CNS_SOLICITANTE": extrair(r'MEDICO SOLICITANTE:.*?CNS:\s+([\d]+)', bloco, re.DOTALL),
        # Extrai o CNS do profissional autorizador
        "CNS_AUTORIZADOR": extrair(r'AUTORIZADOR:.*?CNS:\s+([\d]+)', bloco, re.DOTALL),
        # Extrai o código CNES para usar na criação do arquivo
        "CNES_ESTABELECIMENTO": extrair(r'CODIGO DA UNIDADE:\s+([\d-]+)', bloco)
    }
    return dados

def buscar_nome_medico_por_cns(cns, caminho_csv='medicos.csv'):
    """Busca o nome do médico em um arquivo CSV a partir do Cartão Nacional de Saúde (CNS)."""
    if not os.path.exists(caminho_csv):
        print(f"ERRO: Arquivo '{caminho_csv}' não encontrado.")
        return None

    try:
        with open(caminho_csv, mode='r', encoding='utf-8') as file:
            reader = csv.DictReader(file, delimiter=';')
            for row in reader:
                if row['cartao_sus'] == cns:
                    return row['nome_completo']
    except Exception as e:
        print(f"ERRO ao ler o arquivo CSV: {e}")
        return None
    return None

# ==============================================================================
# CLASSE PARA GERAÇÃO DO PDF
# ==============================================================================

class APAC_PDF(FPDF):
    def __init__(self, orientacao='P', unidade='mm', tamanho='A4'):
        super().__init__(orientation=orientacao, unit=unidade, format=tamanho)
        
        # Define a margem inferior para 0.5 cm (5 mm) para permitir escrita no final da página
        self.set_auto_page_break(auto=True, margin=5)
        
    def add_apac_page(self, data):
        self.add_page()
        
        # --- LÓGICA INTELIGENTE PARA ENCONTRAR O TEMPLATE ---
        if getattr(sys, 'frozen', False):
            # Se o script estiver rodando como um .exe (congelado)
            application_path = os.path.dirname(sys.executable)
        else:
            # Se estiver rodando como um script .py normal
            application_path = os.path.dirname(os.path.abspath(__file__))
            
        template_path = os.path.join(application_path, "template.png")
        
        if os.path.exists(template_path):
            self.image(template_path, x=0, y=0, w=210, h=297)
        else:
            messagebox.showerror("Erro Fatal", "Arquivo 'template.png' não encontrado. Por favor, coloque-o na mesma pasta do executável.")
            return

        # Define a fonte e cor padrão para os dados
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)
        
        # --- PREENCHIMENTO DOS CAMPOS ---
        
        # Bloco 1: Estabelecimento
        self.set_xy(13, 32); self.cell(100, 5, data["NOME_ESTABELECIMENTO"])
        self.set_xy(168, 32); self.cell(50, 5, data["CNES_ESTABELECIMENTO"])
        
        # Bloco 2: Paciente
        self.set_xy(13, 46.5); self.cell(100, 5, data["NOME_PACIENTE"])
        
        original_font_size = self.font_size_pt
        self.set_font_size(7)
        if data.get("SEXO") == "MASCULINO":
            self.set_xy(148.8, 47.5); self.cell(w=3, h=3, text="X", border=0, align='C')
        elif data.get("SEXO") == "FEMININO":
            self.set_xy(160.8, 47.5); self.cell(w=3, h=3, text="X", border=0, align='C')
        self.set_font_size(original_font_size)
        
        self.set_xy(13, 55.2); self.cell(90, 5, data.get("CPF_PACIENTE", ""))
        self.set_xy(112, 55.2); self.cell(40, 5, data["DATA_NASCIMENTO"])
        self.set_xy(148, 55.2); self.cell(15, 5, data["RACA_COR"])
        self.set_xy(13, 62.7); self.cell(100, 5, data["NOME_MAE"])
        self.set_xy(13, 68.5); self.cell(100, 5, data["NOME_RESPONSAVEL"])
        self.set_xy(13, 80); self.cell(150, 5, data["ENDERECO"])
        self.set_xy(13, 88.5); self.cell(50, 5, data["MUNICIPIO_RESIDENCIA"])
        self.set_xy(130, 88.5); self.cell(50, 5, data["COD_IBGE_MUNICIPIO"])
        self.set_xy(155, 88.5); self.cell(20, 5, data["UF"])
        self.set_xy(167, 88.5); self.cell(40, 5, data["CEP"])

        # Bloco 3: Procedimentos
        self.set_xy(11.7, 103); self.cell(40, 5, data["PROC_PRINCIPAL_COD"])
        self.set_xy(80, 103); self.cell(120, 5, data["PROC_PRINCIPAL_NOME"])
        self.set_xy(180, 103); self.cell(10, 5, data["PROC_PRINCIPAL_QTD"])
        self.set_xy(11.7, 118.5); self.cell(40, 5, data["PROC_SEC1_COD"])
        self.set_xy(80, 118.5); self.cell(120, 5, data["PROC_SEC1_NOME"])
        self.set_xy(182, 118.5); self.cell(10, 5, data["PROC_SEC1_QTD"])
        self.set_xy(11.7, 127.5); self.cell(40, 5, data["PROC_SEC2_COD"])
        self.set_xy(80, 127.5); self.cell(120, 5, data["PROC_SEC2_NOME"])
        self.set_xy(182, 127.5); self.cell(10, 5, data["PROC_SEC2_QTD"])

        # Bloco 4: Justificativa
        self.set_xy(14, 173); self.cell(100, 5, data["DESC_DIAGNOSTICO"])
        self.set_xy(14, 185); self.cell(80, 5, data["OBSERVACOES"])
        self.set_xy(125, 173); self.cell(50, 5, data["CID10_PRINCIPAL"])
        
        # Bloco 5: Solicitação
        self.set_xy(13, 222); self.cell(100, 5, data["NOME_SOLICITANTE"])
        self.set_xy(55, 230); self.cell(60, 5, data["DOC_SOLICITANTE"])
        self.set_xy(110, 222); self.cell(40, 5, data["DATA_SOLICITACAO"])
        self.set_xy(18.8, 230.9); self.cell(w=2, h=2, text="X", border=0, align='C')
        
        # Bloco 6: Autorização
        self.set_xy(13, 246); self.cell(60, 5, data["NOME_AUTORIZADOR"])
        self.set_xy(105, 246); self.cell(60, 5, data["COD_ORGAO_EMISSOR"])
        self.set_xy(55, 257.5); self.cell(60, 5, data["DOC_AUTORIZADOR"])
        self.set_xy(140, 246); self.cell(60, 5, data["NUMERO_APAC"])
        self.set_xy(13, 270); self.cell(60, 5, data["DATA_SOLICITACAO"])
        self.set_xy(147, 270); self.cell(60, 5, f"{data['DATA_SOLICITACAO']}    {data['VALIDADE_FIM']}")
        self.set_xy(18.8, 257.9); self.cell(w=2, h=2, text="X", border=0, align='C')

        # Bloco 7: Executante
        self.set_xy(13, 283); self.cell(100, 5, data["NOME_EXECUTANTE"])
        self.set_xy(165, 283); self.cell(50, 5, data["CNES_EXECUTANTE"])