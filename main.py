# main.py voltando aos trabalhos

import tkinter as tk
from tkinter import filedialog, messagebox
from ttkthemes import ThemedTk
from datetime import datetime
import os
import locale
import re
from fpdf import FPDF

# Importa a lógica específica de cada tipo de APAC
from risco_cirurgico import gerar_apac_risco_cirurgico
from oftalmologia import gerar_apac_oftalmologia

# Importa as funções e classes de utilidade
from utils import extrair_dados_variaveis, APAC_PDF, buscar_nome_medico_por_cns, extrair, buscar_descricao_cid, buscar_descricao_cnes_solicitante, extrair_principal_e_cnes, extrair_principal_e_cnes

# ==============================================================================
# VARIÁVEIS DE ESTADO E CONFIGURAÇÕES DA GUI
# ==============================================================================

# Cores e fontes para o tema dark
COR_FUNDO = "#1A1A1A"
COR_TEXTO = "#E0E0E0"
COR_TITULO = "#007BFF"
COR_BOTAO_PADRAO = "#333333"
COR_BOTAO_SELECIONADO = "#4CAF50"
COR_BOTAO_DESABILITADO = "#404040"
COR_BORDA = "#404040"
FONTE_PADRAO = ("Arial", 10, "bold")
FONTE_TITULO = ("Arial", 12, "bold")
FONTE_PEQUENA = ("Arial", 8)
FONTE_OCI_TITULO = ("Arial", 10, "bold")
FONTE_OCI_DESCRICAO = ("Arial", 9)

# DADOS FIXOS GENÉRICOS (recuperados)
DADOS_FIXOS_GENERICOS = {
    "NOME_ESTABELECIMENTO": "NGA 16",
    "MUNICIPIO_RESIDENCIA": "FRANCA",
    "COD_IBGE_MUNICIPIO": "351620",
    "UF": "SP",
    "NOME_EXECUTANTE": "NGA 16",
}

# Variáveis de controle de estado
caminho_arquivo = None
tipo_apac_selecionado = None


# ==============================================================================
# FUNÇÕES DE AÇÃO DA GUI
# ==============================================================================

def carregar_arquivo():
    """Abre uma janela para o usuário selecionar o arquivo TXT."""
    global caminho_arquivo
    caminho_arquivo = filedialog.askopenfilename(
        title="Selecione o arquivo TXT com os dados das APACs",
        filetypes=[("Arquivos de Texto", "*.txt")]
    )
    if caminho_arquivo:
        nome_arquivo = os.path.basename(caminho_arquivo)
        label_btn_carregar.config(text=f"ARQUIVO CARREGADO\n\n{nome_arquivo}", fg=COR_TEXTO)
    else:
        label_btn_carregar.config(text="CARREGAR ARQUIVO\n\nArquivo não carregado", fg="#FF6B6B")
    
    verificar_status_botoes()

def gerar_apacs():
    """Inicia o processo de geração das APACs com base na seleção do usuário."""
    if not caminho_arquivo:
        messagebox.showerror("Erro", "Por favor, carregue um arquivo primeiro.")
        return
    
    if not tipo_apac_selecionado:
        messagebox.showerror("Erro", "Por favor, selecione um tipo de APAC.")
        return

    try:
        with open(caminho_arquivo, 'r', encoding='latin-1') as f:
            conteudo = f.read()

        blocos = re.split(r'\*BDSIA', conteudo)
        lista_apacs = [bloco for bloco in blocos if "NUMERO DO APAC" in bloco]

        if not lista_apacs:
            messagebox.showerror("Erro", "Nenhum registro de APAC válido foi encontrado no arquivo.")
            return

        # A lógica de agrupamento por CNES foi transferida para as funções específicas.
        # Agora, basta chamar a função apropriada passando a lista completa de blocos.
        if tipo_apac_selecionado == "oftalmologia":
            # Extrai o CNES do primeiro bloco para usar como base para os dados fixos
            proc_principal, cnes_solicitante = extrair_principal_e_cnes(lista_apacs[0])
            dados_fixos_cnes = DADOS_FIXOS_GENERICOS.copy()
            dados_fixos_cnes["COD_ESTABELECIMENTO"] = cnes_solicitante
            dados_fixos_cnes["NOME_ESTABELECIMENTO"] = buscar_descricao_cnes_solicitante(cnes_solicitante)
            gerar_apac_oftalmologia(lista_apacs, dados_fixos_cnes)

        elif tipo_apac_selecionado == "risco_cirurgico":
            # Extrai o CNES do primeiro bloco para usar como base para os dados fixos
            proc_principal, cnes_solicitante = extrair_principal_e_cnes(lista_apacs[0])
            dados_fixos_cnes = DADOS_FIXOS_GENERICOS.copy()
            dados_fixos_cnes["COD_ESTABELECIMENTO"] = cnes_solicitante
            dados_fixos_cnes["NOME_ESTABELECIMENTO"] = buscar_descricao_cnes_solicitante(cnes_solicitante)
            gerar_apac_risco_cirurgico(lista_apacs, dados_fixos_cnes)
        
        messagebox.showinfo("Deu bom!", f"Processo de geração concluído. Arquivos PDF salvos em: {os.path.join(os.path.expanduser('~'), 'Downloads')}")

    except Exception as e:
        messagebox.showerror("Erro", f"Ocorreu um erro ao processar o arquivo: {e}")

def selecionar_tipo_apac(tipo):
    """Controla a seleção visual e lógica das opções de APAC."""
    global tipo_apac_selecionado
    tipo_apac_selecionado = tipo
    
    label_risco_cirurgico.config(bg=COR_BOTAO_PADRAO)
    label_oftalmologia.config(bg=COR_BOTAO_PADRAO)
    
    if tipo == "risco_cirurgico":
        label_risco_cirurgico.config(bg=COR_BOTAO_SELECIONADO)
    elif tipo == "oftalmologia":
        label_oftalmologia.config(bg=COR_BOTAO_SELECIONADO)
        
    verificar_status_botoes()

def verificar_status_botoes():
    """Habilita o botão 'Gerar' se as condições forem atendidas."""
    if caminho_arquivo and tipo_apac_selecionado:
        label_btn_gerar.config(state=tk.NORMAL, bg=COR_TITULO, relief="raised")
    else:
        label_btn_gerar.config(state=tk.DISABLED, bg=COR_BOTAO_DESABILITADO, relief="flat")

def atualizar_relogio():
    """Atualiza a data e hora na barra inferior."""
    agora = datetime.now()
    dia_semana = agora.strftime("%A").capitalize()
    data_completa = agora.strftime("%d/%m/%Y %H:%M:%S")
    relogio_label.config(text=f"DESENVOLVIDO POR PH  |  {dia_semana}, {data_completa}")
    root.after(1000, atualizar_relogio)

# ==============================================================================
# CONSTRUÇÃO DA INTERFACE GRÁFICA
# ==============================================================================
locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

root = ThemedTk(theme="black")
root.title("Gerador de APAC")
root.geometry("600x320")
root.configure(bg=COR_FUNDO)

titulo_top_frame = tk.Frame(root, bg=COR_BORDA, bd=2)
titulo_top_frame.pack(side="top", fill="x")
titulo_top = tk.Label(
    titulo_top_frame,
    text="Secretaria Municipal de Saúde de Franca/SP\nGerador de APAC's",
    bg=COR_BORDA,
    fg=COR_TEXTO,
    font=FONTE_TITULO
)
titulo_top.pack(fill="x", padx=10, pady=5)

main_frame = tk.Frame(root, bg=COR_FUNDO)
main_frame.pack(fill="both", expand=True, padx=20, pady=20)
main_frame.grid_columnconfigure(0, weight=1)
main_frame.grid_columnconfigure(1, weight=1)

bloco_carregar_frame = tk.Frame(main_frame, bg=COR_FUNDO)
bloco_carregar_frame.grid(row=0, column=0, padx=10, pady=5, sticky="ew")
bloco_carregar_frame.grid_columnconfigure(0, weight=1)

label_btn_carregar = tk.Label(
    bloco_carregar_frame,
    text="CARREGAR ARQUIVO\n\nArquivo não carregado",
    height=5,
    bg=COR_TITULO,
    fg=COR_TEXTO,
    font=FONTE_PEQUENA,
    relief="raised",
    justify="center"
)
label_btn_carregar.pack(fill="x")
label_btn_carregar.bind("<Button-1>", lambda e: carregar_arquivo())

bloco_risco_cirurgico_frame = tk.Frame(main_frame, bg=COR_FUNDO)
bloco_risco_cirurgico_frame.grid(row=0, column=1, padx=10, pady=5, sticky="ew")
bloco_risco_cirurgico_frame.grid_columnconfigure(0, weight=1)

label_risco_cirurgico = tk.Label(
    bloco_risco_cirurgico_frame,
    text="OCI DE RISCO CIRÚRGICO\n\nTEXTO EXPLICATIVO",
    bg=COR_BOTAO_PADRAO,
    fg=COR_TEXTO,
    font=FONTE_PADRAO,
    padx=10,
    pady=10,
    relief="raised",
    justify="center"
)
label_risco_cirurgico.pack(fill="x")
label_risco_cirurgico.bind("<Button-1>", lambda e: selecionar_tipo_apac("risco_cirurgico"))

bloco_gerar_frame = tk.Frame(main_frame, bg=COR_FUNDO)
bloco_gerar_frame.grid(row=1, column=0, padx=10, pady=5, sticky="ew")
bloco_gerar_frame.grid_columnconfigure(0, weight=1)

label_btn_gerar = tk.Label(
    bloco_gerar_frame,
    text="GERAR APAC'S",
    height=5,
    bg=COR_BOTAO_DESABILITADO,
    fg=COR_TEXTO,
    font=FONTE_PEQUENA,
    relief="flat",
    state=tk.DISABLED,
    justify="center"
)
label_btn_gerar.pack(fill="x")
label_btn_gerar.bind("<Button-1>", lambda e: gerar_apacs())

bloco_oftalmologia_frame = tk.Frame(main_frame, bg=COR_FUNDO)
bloco_oftalmologia_frame.grid(row=1, column=1, padx=10, pady=5, sticky="ew")
bloco_oftalmologia_frame.grid_columnconfigure(0, weight=1)

label_oftalmologia = tk.Label(
    bloco_oftalmologia_frame,
    text="OCI OFTALMOLÓGICA\n\nTEXTO EXPLICATIVO",
    bg=COR_BOTAO_PADRAO,
    fg=COR_TEXTO,
    font=FONTE_PADRAO,
    padx=10,
    pady=10,
    relief="raised",
    justify="center"
)
label_oftalmologia.pack(fill="x")
label_oftalmologia.bind("<Button-1>", lambda e: selecionar_tipo_apac("oftalmologia"))

footer_frame = tk.Frame(root, bg=COR_BORDA, bd=2)
footer_frame.pack(side="bottom", fill="x")

assinatura_label = tk.Label(
    footer_frame,
    text="Desenvolvido por PH",
    bg=COR_BORDA,
    fg=COR_TEXTO,
    font=FONTE_PEQUENA
)
assinatura_label.pack(side="left", padx=10, pady=5)

relogio_label = tk.Label(
    footer_frame,
    text="",
    bg=COR_BORDA,
    fg=COR_TEXTO,
    font=FONTE_PEQUENA
)
relogio_label.pack(side="right", padx=10, pady=5)

locale.setlocale(locale.LC_ALL, 'pt_BR.UTF-8')

atualizar_relogio()
root.mainloop()