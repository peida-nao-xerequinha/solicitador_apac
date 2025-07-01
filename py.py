import tkinter as tk
from tkinter import filedialog
import re
import os
from fpdf import FPDF
import sys

# ==============================================================================
# DADOS FIXOS - Altere aqui se necessário
# ==============================================================================
DADOS_FIXOS = {
    "NOME_ESTABELECIMENTO": "NGA 16",
    "CNES_ESTABELECIMENTO": "2087669",
    "MUNICIPIO_RESIDENCIA": "FRANCA",
    "COD_IBGE_MUNICIPIO": "351620",
    "UF": "SP",
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
    "NOME_SOLICITANTE": "REINALDO MELLEM KAIRALA - CRM/SP 30366",
    "DOC_SOLICITANTE": "207274333200006",
    "NOME_AUTORIZADOR": "ELENICE GAKU SASAKI - CRM/SP 57305",
    "COD_ORGAO_EMISSOR": "M351620001",
    "DOC_AUTORIZADOR": "702402512360420",
    "NOME_EXECUTANTE": "NGA 16",
    "CNES_EXECUTANTE": "2087669",
}

# ==============================================================================
# FUNÇÕES DO SCRIPT
# ==============================================================================

def extrair(pattern, texto):
    """Extrai um valor de um texto usando regex."""
    match = re.search(pattern, texto, re.MULTILINE)
    return match.group(1).strip() if match else ""

# SUBSTITUA A SUA FUNÇÃO ANTIGA POR ESTA VERSÃO ATUALIZADA
def extrair_dados_variaveis(bloco):
    """Extrai apenas os dados variáveis de um bloco de texto da APAC."""
    if "NUMERO DO APAC" not in bloco: return None

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
        "ENDERECO": endereco_completo,
        "CEP": extrair(r'CEP:\s+([\d\-]+)', bloco),
        "DATA_SOLICITACAO": extrair(r'INICIO DA VALIDADE DA APAC:\s+([\d/]+)', bloco),
        "DATA_AUTORIZACAO": extrair(r'DATA DA OCORRENCIA:\s+([\d/]+)', bloco),
        "VALIDADE_FIM": extrair(r'FIM DA VALIDADE DO APAC:\s+([\d/]+)', bloco),
        "NUMERO_APAC": extrair(r'NUMERO DO APAC:\s+([\d\-]+)', bloco),
    }
    dados["NOME_RESPONSAVEL"] = ""
    return dados

class APAC_PDF(FPDF):
    def add_apac_page(self, data):
        self.add_page()
        
        self.set_auto_page_break(auto=True, margin=5)

        # --- LÓGICA INTELIGENTE PARA ENCONTRAR O TEMPLATE ---
        if getattr(sys, 'frozen', False):
            # Se o script estiver rodando como um .exe (congelado)
            application_path = os.path.dirname(sys.executable)
        else:
            # Se estiver rodando como um script .py normal
            application_path = os.path.dirname(os.path.abspath(__file__))
        
        template_path = os.path.join(application_path, "template.png")
        # --- FIM DA LÓGICA INTELIGENTE ---

        if os.path.exists(template_path):
            self.image(template_path, x=0, y=0, w=210, h=297)
        else:
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, "ERRO: Arquivo 'template.png' não encontrado!", 1, 1, 'C')
            return
        
        # Define a margem inferior para 0.5 cm (5 mm) para permitir escrita no final da página
        self.set_auto_page_break(auto=True, margin=5)

        # Coloca a imagem do template como fundo da página inteira
        if os.path.exists("template.png"):
            self.image("template.png", x=0, y=0, w=210, h=297) # A4 em mm
        else:
            self.set_font('Arial', 'B', 16)
            self.cell(0, 10, "ERRO: Arquivo 'template.png' não encontrado!", 1, 1, 'C')
            return

        # Define a fonte e cor padrão para os dados
        self.set_font('Arial', '', 10)
        self.set_text_color(0, 0, 0)

        # --- COORDENADAS (x, y) EM MILÍMETROS - VERSÃO FINAL ---
        
        # Bloco 1: Estabelecimento
        self.set_xy(13, 32); self.cell(100, 5, data["NOME_ESTABELECIMENTO"])
        self.set_xy(168, 32); self.cell(50, 5, data["CNES_ESTABELECIMENTO"])
        
        # Bloco 2: Paciente
        self.set_xy(13, 46.5); self.cell(100, 5, data["NOME_PACIENTE"])
        
        # Lógica para o campo "SEXO" com tamanho e posição ajustados
        original_font_size = self.font_size_pt
        self.set_font_size(7)
        if data.get("SEXO") == "MASCULINO":
            self.set_xy(148.8, 47.5); self.cell(w=3, h=3, text="X", border=0, align='C')
        elif data.get("SEXO") == "FEMININO":
            self.set_xy(160.8, 47.5); self.cell(w=3, h=3, text="X", border=0, align='C')
        self.set_font_size(original_font_size)
        
        # Restante dos dados do paciente
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

# SUBSTITUA A SUA FUNÇÃO 'main' ATUAL POR ESTA VERSÃO ATUALIZADA
def main():
    """
    Função principal que orquestra a seleção de arquivos e a geração do PDF.
    """
    root = tk.Tk()
    root.withdraw()

    caminho_txt = filedialog.askopenfilename(title="Selecione o arquivo TXT com os dados das APACs", filetypes=[("Arquivos de Texto", "*.txt")])
    if not caminho_txt:
        print("Operação cancelada.")
        return
        
    if not os.path.exists("template.png"):
        print("\nERRO FATAL: Arquivo 'template.png' não encontrado.")
        print("Por favor, crie a imagem do formulário e a salve na mesma pasta do script.")
        return

    with open(caminho_txt, 'r', encoding='latin-1') as f:
        conteudo = f.read()
    
    blocos = re.split(r'\*BDSIA', conteudo)
    lista_apacs = [bloco for bloco in blocos if "NUMERO DO APAC" in bloco]

    if not lista_apacs:
        print("Nenhum registro de APAC válido foi encontrado no arquivo.")
        return

    print(f"Encontrados {len(lista_apacs)} registros. Iniciando a geração do PDF...")
    
    pdf = APAC_PDF('P', 'mm', 'A4')
    
    for i, bloco in enumerate(lista_apacs):
        dados_variaveis = extrair_dados_variaveis(bloco)
        if dados_variaveis:
            dados_completos = {**DADOS_FIXOS, **dados_variaveis}
            print(f"Adicionando APAC: {dados_completos['NUMERO_APAC']} ({i+1}/{len(lista_apacs)})")
            pdf.add_apac_page(dados_completos)

    # --- LÓGICA DE SALVAMENTO NA PASTA DOWNLOADS ---
    try:
        # Encontra a pasta de Downloads do usuário de forma compatível com Windows/Mac/Linux
        pasta_downloads = os.path.join(os.path.expanduser('~'), 'Downloads')
        
        # Se por acaso a pasta Downloads não existir, salva na pasta atual
        if not os.path.isdir(pasta_downloads):
            pasta_downloads = "." # "." representa a pasta atual

    except Exception:
        # Em caso de qualquer erro, apenas salva na pasta atual
        pasta_downloads = "."

    nome_saida = "apac's.pdf"
    caminho_completo_saida = os.path.join(pasta_downloads, nome_saida)
    
    pdf.output(caminho_completo_saida)
    print(f"\n✅ Processo concluído! PDF final salvo em: {caminho_completo_saida}")
    
if __name__ == "__main__":
    main()