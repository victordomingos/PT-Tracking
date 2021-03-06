#!/usr/local/bin/python3
# encoding: utf-8
"""
Aplicação de base de dados para registo e acompanhamento de encomendas da
CTT Expresso. Permite automatizar o processo de consulta online do estado
de tracking para várias remessas, bem como manter um registo dos pagamentos
referentes aos envios à cobrança. As remessas que requerem atenção, devido
a atrasos na entrega ou na receção do pagamento correspondente, bem como os
cheques cuja data prevista de depósito se esteja a aproximar são destacadas
na lista principal, por forma a permitir uma intervenção em conformidade.
Adicionalmente, é mantido um histórico facilmente pesquisável de todas as
remessas registadas na base de dados.

Desenvolvido em Python 3 (com muitas noites passadas em claro) por:
        Victor Domingos
        http://victordomingos.com

© 2018 Victor Domingos
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""
import sys
import io
import Pmw
import logging
import tkinter.font
from tkinter import *
from tkinter import ttk
from string import ascii_letters

# Os outros módulos que compõem esta aplicação
from misc_operations import *
from global_setup import *
from global_setup import __app_name__
from extra_tk_classes import *
from callbacks_main import Callbacks
from logging_stuff import *


__author__ = "Victor Domingos"
__copyright__ = "Copyright 2018 Victor Domingos"
__license__ = "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
__version__ = "v.2.13"
__email__ = "web@victordomingos.com"
__status__ = "beta"


class Janela:
    def __init__(self, master):
        global update_delay
        self.master = master
        self.master.createcommand('exit', save_and_exit)
        master.title(__app_name__+ " - "+ __version__)
        master.minsize(width=800, height=600)
        master.maxsize(width=2024, height=2000)

        self.callBacks = Callbacks(self)  # Vai buscar ao módulo externo os métodos que pertenciam a esta classe.

        self.dicas = Pmw.Balloon(self.master, label_background='#f6f6f6',
                                              hull_highlightbackground='#b3b3b3',
                                              state='balloon',
                                              relmouse='both',
                                              yoffset=18,
                                              xoffset=-2,
                                              initwait=1300)

        self.janela_thanks = None
        self.janela_about = None
        self.status_txt = StringVar()
        self.style = ttk.Style(root)
        self.remessa_selecionada = ""
        self.lista_destinatarios = db_get_destinatarios()
        self.obj_num = ""
        self.updates = 0  # Para controlo de função recorrente (self.atualizacao_periodica)

        self.entryform_visible = 0
        self.detalhe_visible = 0
        self.pesquisa_visible = 0
        self.estado_tabela = "Em curso"
        self.var_spin_vols = StringVar(root)
        self.var_spin_vols.set("1")

        style_label = ttk.Style()
        style_label.configure("BW.TLabel", pady=10, foreground="grey25", font=("Helvetica Neue", 16, "bold"))
        style_label.configure("Active.TButton", foreground="white")

        # Barra de ferramentas / botões -------------------------------------------------------------------------------
        self.topframe = ttk.Frame(root, padding="5 8 5 5")
        self.btnFont = tkinter.font.Font(family="Lucida Grande", size=10)
        self.btnTxtColor = "grey22"

        self.btn_emcurso = ttk.Button(self.topframe, width=4, text="✈", command=self.callBacks.ativar_emcurso)
        self.btn_emcurso.grid(column=0, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Em Curso").grid(column=0, row=1)
        self.dicas.bind(self.btn_emcurso, 'Mostrar apenas as remessas que se encontram em curso. (⌘1)')

        self.btn_cobr = ttk.Button(self.topframe, width=4, text="€", command=self.callBacks.ativar_cobr)
        self.btn_cobr.grid(column=1, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Cobrança").grid(column=1, row=1)
        self.dicas.bind(self.btn_cobr, 'Mostrar apenas as remessas com cobrança\nque se encontram em curso. (⌘2)')

        self.btn_arquivo = ttk.Button(self.topframe, text="☰", width=4, command=self.callBacks.ativar_arquivo)
        self.btn_arquivo.grid(column=3, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Arquivo").grid(column=3, row=1)
        self.dicas.bind(self.btn_arquivo, 'Mostrar apenas as remessas arquivadas. (⌘3)')

        self.btn_pag = ttk.Button(self.topframe, text=" ✅", width=4, command=self.callBacks.pag_recebido)
        self.btn_pag.grid(column=7, row=0)
        self.label_pag = ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Cheque Rec.")
        self.label_pag.grid(column=7, row=1)
        self.dicas.bind(self.btn_pag, 'Registar a receção de pagamento\nreferente à remessa selecionada. (⌘R)')

        self.btn_del = ttk.Button(self.topframe, text="❌", width=4, command=self.callBacks.del_remessa)
        self.btn_del.grid(column=8, row=0)
        self.label_del = ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Arquivar")
        self.label_del.grid(column=8, row=1)
        self.dicas.bind(self.btn_del, 'Arquivar a remessa selecionada. (⌘⌫)')

        self.btn_hoje = ttk.Button(self.topframe, text=" ⚡", width=4, command=self.callBacks.copiar_hoje)
        self.btn_hoje.grid(column=9, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Hoje").grid(column=9, row=1)
        self.dicas.bind(self.btn_hoje, 'Copiar a lista dos envios de hoje\npara a Área de Transferência. (⌘T)')

        # ----------- Botão com menu "copiar" --------------
        self.label_menu_btn = ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Copiar…")
        self.menu_btn = ttk.Menubutton (self.topframe, text="•••")
        self.menu_btn.menu  =  Menu (self.menu_btn, tearoff=0)
        self.menu_btn["menu"] =  self.menu_btn.menu

        self.menu_btn.menu.add_command(label="Número de objeto", command=self.callBacks.copiar_obj_num, accelerator="Command+c")
        self.menu_btn.menu.add_command(label="Mensagem de expedição", command=self.callBacks.copiar_msg, accelerator="Command+e")
        # self.menu_btn.menu.add_command(label="Lista de remessas de hoje", command=self.callBacks.copiar_hoje, accelerator="Command+t")
        self.menu_btn.menu.add_separator()
        self.menu_btn.menu.add_command(label="Cheques depositados hoje", command=self.callBacks.copiar_chq_hoje)
        self.menu_btn.menu.add_command(label="Cheques por depositar", command=self.callBacks.copiar_chq_por_depositar)
        self.menu_btn.menu.add_command(label="Cheques ainda não recebidos", command=self.callBacks.copiar_chq_nao_recebidos)
        self.menu_btn.menu.add_separator()
        self.menu_btn.menu.add_command(label="Lista de envios por expedidor", command=self.callBacks.copiar_lista_por_expedidor)
        self.menu_btn.grid(column=10, row=0)
        self.label_menu_btn.grid(column=10, row=1)
        self.dicas.bind(self.menu_btn, 'Clique para selecionar qual a informação\na copiar para a Área de Transferência.')
        # ----------- fim de Botão com menu "copiar" -------------

        self.btn_add = ttk.Button(self.topframe, text="+", width=4, command=self.callBacks.show_entryform)
        self.btn_add.grid(column=13, row=0)
        self.label_add = ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Adicionar")
        self.label_add.grid(column=13, row=1)
        self.dicas.bind(self.btn_add, 'Registar nova remessa. (⌘N)')

        self.text_input_pesquisa = ttk.Entry(self.topframe, width=15)
        self.text_input_pesquisa.grid(column=14, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Pesquisar").grid(column=14, row=1)
        self.dicas.bind(self.text_input_pesquisa, 'Para iniciar a pesquisa, digite\numa palavra ou frase. (⌘F)')

        letras_etc = ascii_letters + "01234567890-., "
        for char in letras_etc:
            keystr = '<KeyRelease-' + char + '>'
            self.text_input_pesquisa.bind(keystr, self.callBacks.ativar_pesquisa)
        self.text_input_pesquisa.bind('<Button-1>', self.callBacks.clique_a_pesquisar)
        self.text_input_pesquisa.bind('<KeyRelease-Escape>', self.callBacks.cancelar_pesquisa)
        self.text_input_pesquisa.bind('<KeyRelease-Mod2-a>', self.text_input_pesquisa.select_range(0, END))

        for col in range(1,15):
            self.topframe.columnconfigure(col, weight=0)
        self.topframe.columnconfigure(5, weight=1)
        self.topframe.columnconfigure(11, weight=1)

        # Tabela de dados ---------------------------------------------------------------------------------------------
        self.mainframe = ttk.Frame(root)

        self.tree = ttk.Treeview(self.mainframe, height=60, selectmode='browse')
        self.tree['columns'] = ('Dias', 'Destinatário', 'Estado', 'Objeto nº', 'Vols', 'Cobrança', 'Cheque rec.', 'Depositar')
        self.tree.pack(side=TOP, fill=BOTH)
        self.tree.column('#0', anchor=W, minwidth=0, stretch=0, width=0)
        self.tree.column('Dias', anchor=E, minwidth=36, stretch=0, width=46)
        self.tree.column('Destinatário', minwidth=100, stretch=1, width=150)
        self.tree.column('Estado', minwidth=110, stretch=1, width=150)
        self.tree.column('Objeto nº', anchor=E, minwidth=100, stretch=0, width=110)
        self.tree.column('Vols', anchor=E, minwidth=35, stretch=0, width=35)
        self.tree.column('Cobrança', anchor=E,minwidth=65, stretch=0, width=65)
        self.tree.column('Cheque rec.', anchor=E, minwidth=85, stretch=0, width=85)
        self.tree.column('Depositar', anchor=E, minwidth=85, stretch=0, width=85)

        # Ordenar por coluna ao clicar no respetivo cabeçalho
        for col in self.tree['columns']:
            self.tree.heading(col, text=col.title(),
                              command=lambda c=col: self.callBacks.sortBy(self.tree, c, 0))

        # Barra de deslocação para a tabela
        self.tree.grid(column=0, row=0, sticky=N+W+E, in_=self.mainframe)
        vsb = AutoScrollbar(orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        vsb.grid(column=1, row=0, sticky=N+S, in_=self.mainframe)
        self.mainframe.grid_columnconfigure(0, weight=1)
        self.mainframe.grid_rowconfigure(0, weight=1)
        ttk.Style().configure('Treeview', font=("Lucida Grande", 11), foreground="grey22", rowheight=20)
        ttk.Style().configure('Treeview.Heading', font=("Lucida Grande", 11), foreground="grey22")

        ttk.Style().configure( '.', relief = 'flat', borderwidth = 0) # Aplicar visual limpo a todas as classes
        self.callBacks.bind_tree()

        # Formulário de introdução de dados (aparece somente quando o utilizador solicita) ----------------------------
        self.bottomframe = ttk.Frame(root, padding="4 8 4 10")

        self.adl_remessa = ttk.Label(self.bottomframe, style="BW.TLabel", text="Adicionar Remessa:\n")
        self.adl_remessa.grid(column=0, row=0, columnspan=7, sticky=W)

        ttk.Label(self.bottomframe, text="Nº Objeto").grid(column=0, row=1, sticky=W)
        self.text_input_obj = ttk.Entry(self.bottomframe, width=13)
        self.text_input_obj.grid(column=0, row=2, sticky=W+E)
        self.text_input_obj.bind("<Return>", lambda x: self.text_input_destin.focus_set())
        self.dicas.bind(self.text_input_obj, 'Introduza aqui o número de objeto\nindicado na guia da transportadora.')

        ttk.Label(self.bottomframe, text="Destinatário").grid(column=1, columnspan=2,  row=1, sticky=W)
        self.text_input_destin = AutocompleteEntry(self.bottomframe, width=30)
        self.text_input_destin.set_completion_list(self.lista_destinatarios)
        self.text_input_destin.grid(column=1, columnspan=2, row=2, sticky=W+E)
        self.text_input_destin.bind("<Return>", self.callBacks.add_remessa)

        ttk.Label(self.bottomframe, text="Cobrança").grid(column=3, row=1)
        self.text_input_cobr = ttk.Entry(self.bottomframe, width=10)
        self.text_input_cobr.grid(column=3, row=2)
        self.text_input_cobr.bind("<Return>", self.callBacks.add_remessa)
        self.dicas.bind(self.text_input_cobr, 'Introduza aqui o montante a cobrar,\ncaso se trate de um envio à cobrança.')

        ttk.Label(self.bottomframe, text="Prazo").grid(column=4, row=1, sticky=W)
        self.text_input_dias = ttk.Entry(self.bottomframe, width=6)
        self.text_input_dias.grid(column=4, row=2, sticky=W)
        self.text_input_dias.bind("<Return>", self.callBacks.add_remessa)
        self.dicas.bind(self.text_input_dias, 'Indique o número de dias para pagamento\n(p. ex.: "PP", "30", "15").')

        ttk.Label(self.bottomframe, text="Vols.").grid(column=5, row=1, sticky=W+E)
        self.spin_vols = ttk.Spinbox(self.bottomframe, from_=1, to=100, format='%.0f', width=6, textvariable=self.var_spin_vols)
        self.spin_vols.grid(column=5, row=2, sticky=W+E)
        self.spin_vols.bind("<Return>", self.callBacks.add_remessa)
        self.spin_vols.selection_clear()
        self.dicas.bind(self.spin_vols, 'Especifique o número de volumes\nque compõem esta remessa.')

        ttk.Label(self.bottomframe, text="Expedidor").grid(column=0, row=3, sticky=W+E)
        self.combo_expedidor = ttk.Combobox(self.bottomframe, width=13, values=(" - Selecionar -",)+EXPEDIDORES, state="readonly")
        self.combo_expedidor.current(INDEX_EXPEDIDOR_PREDEFINIDO)
        self.combo_expedidor.grid(column=0, row=4, sticky=W+E)
        self.combo_expedidor.bind("<<ComboboxSelected>>", self.callBacks.expedir_select)
        self.combo_expedidor.bind("<Return>", self.callBacks.add_remessa)
        self.dicas.bind(self.combo_expedidor, 'Clique aqui para selecionar o expedidor\nresponsável por este envio.')

        ttk.Label(self.bottomframe, text="Observações").grid(column=1, columnspan=4, row=3, sticky=W)
        self.text_input_obs = ttk.Entry(self.bottomframe, width=40)
        self.text_input_obs.grid(column=1, columnspan=4, row=4, sticky=W+E)
        self.dicas.bind(self.text_input_obs, 'Utilize este campo para registar quaisquer informações\nadicionais que possam vir a ser úteis para pesquisa ou\nreferência futura (nº de encomenda, tipo de mercadoria,\npessoa de contacto no local de destino, etc.).')

        ttk.Label(self.bottomframe, text="RMA").grid(column=5, row=3, sticky=W+E)
        self.text_input_rma = ttk.Entry(self.bottomframe, width=13)
        self.text_input_rma.grid(column=5, row=4, sticky=W+E)
        self.dicas.bind(self.text_input_rma, 'Caso este envio seja referente a um processo de garantia,\npode ser indicado aqui o nº de processo, NAR ou RMA do\nfornecedor ou centro técnico.')

        self.btn_adicionar = ttk.Button(self.bottomframe, text="Adicionar", default="active", style="Active.TButton", command=lambda: self.callBacks.add_remessa)
        self.btn_adicionar.grid(column=6, row=2, sticky=W+E, padx="15 0")
        self.dicas.bind(self.btn_adicionar, 'Adicionar à base de dados a informação introduzida. (⏎)')
        self.btn_adicionar.bind("<Return>", self.callBacks.add_remessa)
        self.btn_adicionar.bind('<Button-1>', self.callBacks.add_remessa)

        self.btn_cancelar = ttk.Button(self.bottomframe, text="Cancelar", command=self.callBacks.hide_entryform)
        self.btn_cancelar.grid(column=6, row=4, sticky=W+E, padx="15 0")
        self.dicas.bind(self.btn_cancelar, 'Fechar este painel, sem guardar,\ne regressar à tabela de remessas. (⎋)')

        for col in range(6):
            self.bottomframe.columnconfigure(col, weight=1)

        # Painel de detalhes de remessa (aparece somente quando o utilizador solicita) ----------------------------
        self.detalheframe = ttk.Frame(root, padding="5 8 5 0")

        # Painel de informação (entre a tabela e o formulário de entrada de dados) ------------------------------------
        self.statusframe = ttk.Frame(root, padding="5 5 5 5")
        self.progressbar = NPKProgressBar(self.statusframe)

        self.statusFont = tkinter.font.Font(family="Lucida Grande", size=11)
        self.statusbar = ttk.Label(self.statusframe, font=self.statusFont, foreground=self.btnTxtColor, textvariable=self.status_txt)
        self.statusbar.pack(side=BOTTOM)


        # Ativar layout -----------------------------------------------------------------------------------------------
        self.callBacks.gerar_menu()
        #self.headframe.pack(side=TOP, fill=X)
        self.topframe.pack(side=TOP, fill=X)
        self.mainframe.pack(side=TOP, fill=BOTH)
        self.statusframe.pack(side=BOTTOM, before=self.mainframe, fill=X)
        self.mainframe.after(2000, self.callBacks.atualizacao_periodica)  # inicia processo de atualização automática e periódica
        self.callBacks.ativar_emcurso()


if __name__ == "__main__":
    logging.basicConfig(filename=DEBUG_PATH,
                        filemode='a',
                        format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                        datefmt='%H:%M:%S',
                        level=logging.DEBUG)
    user_info = basicLogInfo()
    logging.debug(user_info.generate_log_string())
    db_inicializar()
    root = Tk()
    root.configure(background='grey95')
    root.geometry('860x650+0+0')
    janela = Janela(root)
    root.bind_all("<Mod2-q>", exit)
    root.mainloop()
