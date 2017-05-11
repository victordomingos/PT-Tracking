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


© 2017 Victor Domingos
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

import re
import sqlite3
import tkinter.font
import os
import sys
import webbrowser
import shlex
from datetime import time, datetime, timedelta
from tkinter import *
from tkinter import ttk
from tkinter import messagebox
from string import ascii_letters


# Nota: Os seguintes módulos requerem instalação prévia
from terminaltables import AsciiTable # a remover e substituir por uma visualização gráfica
from bleach import clean
from bs4 import BeautifulSoup
import requests

# Os outros módulos que compõem esta aplicação
from misc_operations import *
from global_setup import *
from extra_tk_classes import *
from about_window import *

__app_name__ = "PT Tracking 2017"
__author__ = "Victor Domingos"
__copyright__ = "Copyright 2016 Victor Domingos"
__license__ = "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
__version__ = "v.2.9"
__email__ = "web@victordomingos.com"
__status__ = "beta"

entryform_visible = 0
detalhe_visible = 0
pesquisa_visible = 0
estado_tabela = "Em curso"
NUNCA = 0


class Janela:
    def __init__(self, master):
        global update_delay
        self.master = master
        self.master.createcommand('exit', save_and_exit)
        master.title(__app_name__+ " - "+ __version__)
        master.minsize(width=800, height=600)
        master.maxsize(width=1024, height=2000)
        self.janela_thanks = None
        self.janela_about = None
        self.status_txt = StringVar()
        self.style = ttk.Style(root)
        self.remessa_selecionada = ""
        self.lista_destinatarios = db_get_destinatarios()
        self.obj_num = ""
        self.updates = 0  # Para controlo de função recorrente (self.atualizacao_periodica)


        style_label = ttk.Style()
        style_label.configure("BW.TLabel", pady=10, foreground="grey25", font=("Helvetica Neue", 16, "bold"))
        style_label.configure("Active.TButton", foreground="white")


        # Cabeçalho da aplicação  -------------------------------------------------------------------------------------
        #self.headframe = ttk.Frame(root, padding="3 8 3 3")
        """
        head_label3 = ttk.Label(self.headframe, text="head text3 RIGHT")
        head_label3.pack(side=RIGHT)
        """


        # Barra de ferramentas / botões -------------------------------------------------------------------------------
        self.topframe = ttk.Frame(root, padding="5 8 5 5")
        self.btnFont = tkinter.font.Font(family="Lucida Grande", size=10)
        self.btnTxtColor = "grey22"

        self.btn_emcurso = ttk.Button(self.topframe, width=4, text="✈", command=self.ativar_emcurso)

        self.btn_emcurso.grid(column=0, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Em Curso").grid(column=0, row=1)

        self.btn_cobr = ttk.Button(self.topframe, width=4, text="€", command=self.ativar_cobr)
        self.btn_cobr.grid(column=1, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Cobrança").grid(column=1, row=1)

        self.btn_arquivo = ttk.Button(self.topframe, text="☰", width=4, command=self.ativar_arquivo)
        self.btn_arquivo.grid(column=3, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Arquivo").grid(column=3, row=1)

        self.btn_pag = ttk.Button(self.topframe, text=" ✅", width=4, command=self.pag_recebido)
        self.btn_pag.grid(column=7, row=0)
        self.label_pag = ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Cheque Rec.")
        self.label_pag.grid(column=7, row=1)

        self.btn_del = ttk.Button(self.topframe, text="❌", width=4, command=self.del_remessa)
        self.btn_del.grid(column=8, row=0)
        self.label_del = ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Arquivar")
        self.label_del.grid(column=8, row=1)

        self.btn_hoje = ttk.Button(self.topframe, text=" ⚡", width=4, command=self.copiar_hoje)
        self.btn_hoje.grid(column=9, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Hoje").grid(column=9, row=1)


        # ----------- Botão com menu "copiar" --------------
        self.label_menu_btn = ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Copiar…")
        self.menu_btn = ttk.Menubutton (self.topframe, text="•••")
        self.menu_btn.menu  =  Menu (self.menu_btn, tearoff=0)
        self.menu_btn["menu"] =  self.menu_btn.menu

        self.menu_btn.menu.add_command(label="Número de objeto", command=self.copiar_obj_num, accelerator="Command+c")
        self.menu_btn.menu.add_command(label="Mensagem de expedição", command=self.copiar_msg, accelerator="Command+e")
        # self.menu_btn.menu.add_command(label="Lista de remessas de hoje", command=self.copiar_hoje, accelerator="Command+t")
        self.menu_btn.menu.add_separator()
        self.menu_btn.menu.add_command(label="Cheques depositados hoje", command=self.copiar_chq_hoje)
        self.menu_btn.menu.add_command(label="Cheques por depositar", command=self.copiar_chq_por_depositar)
        self.menu_btn.menu.add_command(label="Cheques ainda não recebidos", command=self.copiar_chq_nao_recebidos)
        self.menu_btn.menu.add_separator()
        self.menu_btn.menu.add_command(label="Lista de envios por expedidor", command=self.copiar_lista_por_expedidor)
        self.menu_btn.grid(column=10, row=0)
        self.label_menu_btn.grid(column=10, row=1)
        # ----------- fim de Botão com menu "copiar" -------------


        self.btn_add = ttk.Button(self.topframe, text="+", width=4, command=self.show_entryform)
        self.btn_add.grid(column=13, row=0)
        self.label_add = ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Adicionar")
        self.label_add.grid(column=13, row=1)

        self.text_input_pesquisa = ttk.Entry(self.topframe, width=15)

        self.text_input_pesquisa.grid(column=14, row=0)
        ttk.Label(self.topframe, font=self.btnFont, foreground=self.btnTxtColor, text="Pesquisar").grid(column=14, row=1)

        letras_etc = ascii_letters + "01234567890-., "
        for char in letras_etc:
                keystr = '<KeyRelease-' + char + '>'
                self.text_input_pesquisa.bind(keystr, self.ativar_pesquisa)
        self.text_input_pesquisa.bind('<Button-1>', self.clique_a_pesquisar)
        self.text_input_pesquisa.bind('<KeyRelease-Escape>', self.cancelar_pesquisa)
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
                        command=lambda c=col: self.sortBy(self.tree, c, 0))

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
        self.bind_tree()

        # Formulário de introdução de dados (aparece somente quando o utilizador solicita) ----------------------------
        self.bottomframe = ttk.Frame(root, padding="4 8 4 10")

        self.adl_remessa = ttk.Label(self.bottomframe, style="BW.TLabel", text="Adicionar Remessa:\n")
        self.adl_remessa.grid(column=0, row=0, columnspan=7, sticky=W)

        ttk.Label(self.bottomframe, text="Nº Objeto").grid(column=0, row=1, sticky=W)
        self.text_input_obj = ttk.Entry(self.bottomframe, width=13)
        self.text_input_obj.grid(column=0, row=2, sticky=W+E)
        self.text_input_obj.bind("<Return>", lambda x: self.text_input_destin.focus_set())

        ttk.Label(self.bottomframe, text="Destinatário").grid(column=1, columnspan=2,  row=1, sticky=W)
        self.text_input_destin = AutocompleteEntry(self.bottomframe, width=30)
        self.text_input_destin.set_completion_list(self.lista_destinatarios)
        self.text_input_destin.grid(column=1, columnspan=2, row=2, sticky=W+E)
        self.text_input_destin.bind("<Return>", self.add_remessa)

        ttk.Label(self.bottomframe, text="Cobrança").grid(column=3, row=1)
        self.text_input_cobr = ttk.Entry(self.bottomframe, width=10)
        self.text_input_cobr.grid(column=3, row=2)
        self.text_input_cobr.bind("<Return>", self.add_remessa)

        ttk.Label(self.bottomframe, text="Prazo").grid(column=4, row=1, sticky=W)
        self.text_input_dias = ttk.Entry(self.bottomframe, width=6)
        self.text_input_dias.grid(column=4, row=2, sticky=W)
        self.text_input_dias.bind("<Return>", self.add_remessa)

        ttk.Label(self.bottomframe, text="Vols.").grid(column=5, row=1, sticky=W+E)
        self.text_input_vols = ttk.Entry(self.bottomframe, width=6)
        self.text_input_vols.grid(column=5, row=2, sticky=W+E)
        self.text_input_vols.bind("<Return>", self.add_remessa)


        ttk.Label(self.bottomframe, text="Expedidor").grid(column=0, row=3, sticky=W+E)
        self.combo_expedidor = ttk.Combobox(self.bottomframe, width=13, values=(" - Selecionar -",)+EXPEDIDORES, state="readonly")
        self.combo_expedidor.current(0)
        self.combo_expedidor.grid(column=0, row=4, sticky=W+E)
        self.combo_expedidor.bind("<<ComboboxSelected>>", self.expedir_select)
        self.combo_expedidor.bind("<Return>", self.add_remessa)


        ttk.Label(self.bottomframe, text="Observações").grid(column=1, columnspan=4, row=3, sticky=W)
        self.text_input_obs = ttk.Entry(self.bottomframe, width=40)
        self.text_input_obs.grid(column=1, columnspan=4, row=4, sticky=W+E)


        ttk.Label(self.bottomframe, text="RMA").grid(column=5, row=3, sticky=W+E)
        self.text_input_rma = ttk.Entry(self.bottomframe, width=13)
        self.text_input_rma.grid(column=5, row=4, sticky=W+E)


        self.btn_adicionar = ttk.Button(self.bottomframe, text="Adicionar", default="active", style="Active.TButton", command=lambda: self.add_remessa)
        self.btn_adicionar.grid(column=6, row=2, sticky=W+E)
        self.btn_adicionar.bind("<Return>", self.add_remessa)
        self.btn_adicionar.bind('<Button-1>', self.add_remessa)

        self.btn_cancelar = ttk.Button(self.bottomframe, text="Cancelar", command=self.hide_entryform)
        self.btn_cancelar.grid(column=6, row=4, sticky=W+E)

        for col in range(6):
                self.bottomframe.columnconfigure(col, weight=1)


        # Painel de detalhes de remessa (aparece somente quando o utilizador solicita) ----------------------------
        self.detalheframe = ttk.Frame(root, padding="5 8 5 5")



        # Painel de informação (entre a tabela e o formulário de entrada de dados) ------------------------------------
        self.statusframe = ttk.Frame(root, padding="5 5 5 5")
        #self.progress_bar = ttk.Progressbar(self.statusframe, orient ="horizontal", length = 50, mode ="determinate")
        #self.progress_bar["maximum"] = 100
        #self.progress_bar["value"] = 50

        #self.progress_bar.place(in_=self.statusframe, relx=1,  y=100, anchor="se", relwidth=1, bordermode="outside")

        self.statusFont = tkinter.font.Font(family="Lucida Grande", size=11)
        self.statusbar = ttk.Label(self.statusframe, font=self.statusFont, foreground=self.btnTxtColor, textvariable=self.status_txt)
        self.statusbar.pack(side=BOTTOM)


        # Ativar layout -----------------------------------------------------------------------------------------------
        self.gerar_menu()
        #self.headframe.pack(side=TOP, fill=X)
        self.topframe.pack(side=TOP, fill=X)
        self.mainframe.pack(side=TOP, fill=BOTH)
        self.statusframe.pack(side=BOTTOM, before=self.mainframe, fill=X)
        self.mainframe.after(2000, self.atualizacao_periodica)  # inicia processo de atualização automática e periódica
        self.ativar_emcurso()

    def expedir_select(self, event):
        self.combo_expedidor.selection_clear()


    def atualizacao_periodica(self):
        """ Atualiza automaticamente de forma periódica a informação com o
                estado atual das remessas ativas. Caso a interface não esteja
                em utilização, é atualizada também a informação no ecrã.
                A atualização só é efetuada no horário de expediente, com o
                objetivo de reduzir o número consultas ao servidor.
        """
        global update_delay
        global detalhe_visible
        global entryform_visible
        global pesquisa_visible

        agora = datetime.now()
        agora_hora = agora.time()
        if time(9,30) <= agora_hora <= time(20,00):
                self.updates +=1

                print("atualizacao_periodica() em curso... ", datetime.now().time(), "-", self.updates)
                s_status = "A obter estados atualizados para as remessas em curso."
                self.status_txt.set(s_status)
                db_atualizar_tudo()
                criar_mini_db()

                s_status = "Atualização completa!"
                self.status_txt.set(s_status)

                # apenas atualizar a tabela com os novos dados, caso não esteja em curso uma operação do utilizador:
                if (not detalhe_visible) and (not entryform_visible) and (not pesquisa_visible):
                        self.regressar_tabela()

                # Agendar nova atualização apenas até ser atingido o seguinte limite:
                if self.updates <= 900:
                        self.mainframe.after(update_delay, self.atualizacao_periodica)
        else:
                print("atualizacao_periodica(): Fora do horário de serviço. Atualização adiada.", agora_hora)


    def nada(self, *event):
        """ # Hacking moment: Uma função que não faz nada, para quando isso dá jeito...
        """
        pass

    def bind_tree(self):
        self.tree.bind('<<TreeviewSelect>>', self.selectItem_popup)
        self.tree.bind('<Double-1>', self.mostrar_detalhe)
        self.tree.bind("<Button-2>", self.popupMenu)
        self.tree.bind("<Button-3>", self.popupMenu)

    def unbind_tree(self):
        self.tree.bind('<<TreeviewSelect>>', self.nada)
        self.tree.bind('<Double-1>', self.nada)
        self.tree.bind("<Button-2>", self.nada)
        self.tree.bind("<Button-3>", self.nada)


    def selectItem_popup(self, event):
        """ # Hacking moment: Uma função que junta duas funções, para assegurar a sequência...
        """
        self.selectItem()
        self.popupMenu(event)

    def popupMenu(self, event):
        """action in event of button 3 on tree view"""
        # select row under mouse
        self.hide_detalhe()
        #self.selectItem()
        iid = self.tree.identify_row(event.y)
        x, y = event.x_root, event.y_root
        if iid:
            if x!=0 and y!=0:
                # mouse pointer over item
                self.tree.selection_set(iid)
                self.tree.focus(iid)
                self.contextMenu.post(event.x_root, event.y_root)
                print("popupMenu(): x,y = ", event.x_root, event.y_root)
            else:
                print("popupMenu(): wrong values for event - x=0, y=0")
        else:
            print("popupMenu(): Else - No code here yet! (mouse not over item)")
            # mouse pointer not over item
            # occurs when items do not fill frame
            # no action required
            pass



    def thanks(self,*event):
        self.janela_thanks = thanks_window()

    def about(self,*event):
        self.janela_about = about_window()

    """
    def fechar_janela_ativa(self):
        root.protocol("WM_DELETE_WINDOW", save_and_exit)
        pass
    """


    def gerar_menu(self):
        # Menu da janela principal
        self.menu = Menu(root)
        root.config(menu=self.menu)

        self.menuRemessa = Menu(self.menu)

        self.menu.add_cascade(label="Remessa", menu=self.menuRemessa)
        self.menuRemessa.add_command(label="Nova remessa ", command=self.show_entryform, accelerator="Command+n")
        self.menuRemessa.add_command(label="Arquivar remessa", command=self.del_remessa, accelerator="Command+BackSpace")
        self.menuRemessa.add_separator()
        self.menuRemessa.add_command(label="Copiar número de objeto", command=self.copiar_obj_num, accelerator="Command+c")
        self.menuRemessa.add_command(label="Copiar mensagem de expedição", command=self.copiar_msg, accelerator="Command+e")
        self.menuRemessa.add_command(label="Copiar lista de remessas de hoje", command=self.copiar_hoje, accelerator="Command+t")
        self.menuRemessa.add_separator()
        self.menuRemessa.add_command(label="Pesquisar...", command=self.clique_a_pesquisar, accelerator="Command+f")
        self.menuRemessa.add_separator()
        self.menuRemessa.add_command(label="Abrir no site da transportadora", command=self.abrir_url_browser, accelerator="Command+o")
        self.menuRemessa.add_command(label="Informações", command=self.mostrar_detalhe, accelerator="Command+i")
        self.menuRemessa.bind_all("<Command-n>", self.show_entryform)
        self.menuRemessa.bind_all("<Command-t>", self.copiar_hoje)
        self.menuRemessa.bind_all("<Command-c>", self.copiar_obj_num)
        self.menuRemessa.bind_all("<Command-e>", self.copiar_msg)
        self.menuRemessa.bind_all("<Command-f>", self.clique_a_pesquisar)
        self.menuRemessa.bind_all("<Command-i>", self.mostrar_detalhe)
        self.menuRemessa.bind_all("<Command-o>", self.abrir_url_browser)

        self.menuCobr = Menu(self.menu)
        self.menu.add_cascade(label="Cobrança", menu=self.menuCobr)
        self.menuCobr.add_command(label="Cheque recebido", command=self.pag_recebido, accelerator="Command+r")
        self.menuCobr.add_command(label="Cheque depositado", command=self.chq_depositado, accelerator="Command+b")
        self.menuCobr.add_separator()

        self.submenuCopiar = Menu(self.menuCobr)
        self.menuCobr.add_cascade(label="Copiar lista de cheques", menu=self.submenuCopiar)
        self.submenuCopiar.add_command(label="Depositados hoje", command=self.copiar_chq_hoje)
        self.submenuCopiar.add_command(label="Por depositar", command=self.copiar_chq_por_depositar)
        self.submenuCopiar.add_command(label="Ainda não recebidos", command=self.copiar_chq_nao_recebidos)
        self.submenuCopiar.add_separator()
        self.submenuCopiar.add_command(label="Todos os cheques depositados (inclui arquivo)", command=self.copiar_chq_depositados)

        # self.menuCobr.add_separator()
        # self.menuCobr.add_command(label="Exportar relatório de cobranças", state="disabled")
        self.menuCobr.bind_all("<Command-r>", self.pag_recebido)
        self.menuCobr.bind_all("<Command-b>", self.chq_depositado)

        self.menuVis = Menu(self.menu)
        self.menu.add_cascade(label="Visualização", menu=self.menuVis)
        self.menuVis.add_command(label="Mostrar todas as remessas em curso", command=self.ativar_emcurso, accelerator="Command-1")
        self.menuVis.add_command(label="Mostrar remessas com cobrança", command=self.ativar_cobr, accelerator="Command-2")
        self.menuVis.add_command(label="Mostrar remessas arquivadas", command=self.ativar_arquivo, accelerator="Command-3")
        self.menuVis.bind_all("<Command-KeyPress-1>", self.ativar_emcurso)
        self.menuVis.bind_all("<Command-KeyPress-2>", self.ativar_cobr)
        self.menuVis.bind_all("<Command-KeyPress-3>", self.ativar_arquivo)

        self.windowmenu = Menu(self.menu, name='window')
        self.menu.add_cascade(menu=self.windowmenu, label='Janela')
        self.windowmenu.add_separator()
        #self.windowmenu.add_command(label="Fechar", command=self.fechar_janela_ativa, accelerator="Command-w") ###fechar janela ativa cmd-w


        self.helpmenu = Menu(self.menu)
        self.menu.add_cascade(label="Help", menu=self.helpmenu)
 #       helpmenu.add_command(label="Preferências", command=About)
        self.helpmenu.add_command(label="Acerca de "+__app_name__, command=about_window)
        self.helpmenu.add_command(label="Agradecimentos", command=self.thanks)
        self.helpmenu.add_separator()
        self.helpmenu.add_command(label="Contactar a CTT Expresso", command=lambda: webbrowser.open("http://www.cttexpresso.pt/home/contactos.html", new=1, autoraise=True))
        self.helpmenu.add_command(label="Agendar recolha na CTT Expresso", command=lambda: webbrowser.open("http://www.cttexpresso.pt/apoio-a-clientes/ferramentas/marcar-recolhas.html", new=1, autoraise=True))
        self.helpmenu.add_command(label="Abrir página Customer Web Shipment", command=lambda: webbrowser.open("http://web.cttexpresso.pt:8082/default.aspx", new=1, autoraise=True))
        self.helpmenu.add_separator()
        self.helpmenu.add_command(label="Suporte da aplicação "+__app_name__, command=lambda: webbrowser.open("http://victordomingos.com/contactos/", new=1, autoraise=True))
        self.helpmenu.add_separator()
        self.helpmenu.add_command(label="Visitar página do autor", command=lambda: webbrowser.open("http://victordomingos.com", new=1, autoraise=True))
        #root.createcommand('::tk::mac::ShowPreferences', prefs_function)
        #root.bind('<<about-idle>>', about_dialog)
        #root.bind('<<open-config-dialog>>', config_dialog)
        root.createcommand('tkAboutDialog', about_window)


        #----------------Menu contextual tabela principal---------------------
        self.contextMenu = Menu(self.menu)
        self.contextMenu.add_command(label="Informações", command=self.mostrar_detalhe)
        self.contextMenu.add_command(label="Abrir no site da transportadora", command=self.abrir_url_browser)
        self.contextMenu.add_separator()
        self.contextMenu.add_command(label="Copiar número de objeto", command=self.copiar_obj_num)
        self.contextMenu.add_command(label="Copiar mensagem de expedição", command=self.copiar_msg)
        self.contextMenu.add_separator()
        self.contextMenu.add_command(label="Arquivar/restaurar remessa", command=self.del_remessa)
        self.contextMenu.add_separator()
        self.contextMenu.add_command(label="Registar cheque recebido", command=self.pag_recebido)
        self.contextMenu.add_command(label="Registar cheque depositado", command=self.chq_depositado)


    # Janela.métodos -----------------------------------------------------------------------------------------------***
    def popupMsg(self, x, y, msg):
        """
        Mostrar um painel de notificação com uma mensagem
        """
        self.popupframe = ttk.Frame(root, padding="15 15 15 15")
        self.msglabel = ttk.Label(self.popupframe, font=self.statusFont, foreground=self.btnTxtColor, text=msg)
        self.msglabel.pack()
        for i in range(1,10,2):
            self.popupframe.place(x=x,  y=y+i, anchor="n", bordermode="outside")
            self.popupframe.update()
        self.popupframe.after(1500, self.popupframe.destroy)


    def isNumeric(self, s):
        """
        test if a string s is numeric
        """
        for c in s:
            if c in "1234567890.":
                numeric = True
            else:
                return False
        return numeric


    def changeNumeric(self, data):
        """
        if the data to be sorted is numeric change to float
        """
        new_data = []
        if self.isNumeric(data[0][0]):
            # change child to a float
            for child, col in data:
                new_data.append((float(child), col))
            return new_data
        return data


    def sortBy(self, tree, col, descending):
        """
        sort tree contents when a column header is clicked
        """
        # grab values to sort
        data = [(tree.set(child, col), child) for child in tree.get_children('')]
        # if the data to be sorted is numeric change to float
        data =  self.changeNumeric(data)
        # now sort the data in place
        data.sort(reverse=descending)
        for ix, item in enumerate(data):
            tree.move(item[1], '', ix)
        # switch the heading so that it will sort in the opposite direction
        tree.heading(col, command=lambda col=col: self.sortBy(tree, col, int(not descending)))


    def obterDetalhes(self):
        """
        Mostrar detalhes da remessa selecionada (após duplo-clique na linha correspondente)
        """
        global DB_PATH
        self.hide_entryform()
        curItem = self.tree.focus()
        tree_linha = self.tree.item(curItem)
        tree_obj_num = tree_linha["values"][3]
        tree_destin = tree_linha["values"][1]
        self.status_txt.set("Remessa selecionada: {} ({})".format(tree_obj_num, tree_destin))
        self.remessa_selecionada = tree_obj_num

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT *
                     FROM remessas
                     WHERE (obj_num = ?);''', (tree_obj_num,))
        detalhes = c.fetchone()
        conn.commit()
        c.close()
        return detalhes


    def ativar_emcurso(self, *event):
        global estado_tabela
        estado_tabela = "Em curso"
        s_status="A obter estados atualizados para as remessas em curso."
        self.status_txt.set(s_status)
        self.liga_arquivar()
        self.hide_entryform()
        self.hide_detalhe()
        self.text_input_pesquisa.delete(0, END)

        if self.updates:
            db_atualizar_tudo()
            criar_mini_db()
            self.updates += 1

        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute ("""SELECT *
                      FROM remessas
                      WHERE (arquivado = 0);""")
        for i in self.tree.get_children():  # Limpar tabela antes de obter registos atualizados da base de dados
            self.tree.delete(i)
        n_remessas, volumes, com_cobranca = 0, 0, 0
        tot_cobr = 0.0
        impar = "impar"
        tag_cor = " "
        hoje = datetime.now()
        for row in c:  # Preencher cada linha da tabela com os valores obtidos da base de dados
            data_exp = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S.%f")
            dias = calcular_dias_desde_envio(data_exp)

            tag_cor = impar
            if row[2] == "Objeto com tentativa de entrega":
                tag_cor = "falhou_entrega"
            elif data_exp < (hoje-timedelta(0)) and (row[2] != "Objeto entregue"):  # Se já passou algum tempo desde expedição e objeto não foi entregue...
                tag_cor = "antigo"

            if row[5] == "0":  # se remessa sem cobrança
                data_r_chq = " "
                data_dep_chq = " "
            else:  # se remessa com cobrança
                dt_data_dep_chq = datetime.strptime(row[7], "%Y-%m-%d %H:%M:%S.%f")
                data_dep_chq = datetime.strftime(dt_data_dep_chq,"%Y-%m-%d")

                if row[6] != "N/D":  # Se já chegou o cheque
                    dt_data_r_chq = datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S.%f")
                    data_r_chq = datetime.strftime(dt_data_r_chq,"%Y-%m-%d")

                    if dt_data_dep_chq < (hoje+timedelta(3)):  # Se data a depositar é nos próximos dias...
                            tag_cor = "depositar"

                else:  # Se ainda não chegou o cheque
                    data_r_chq = row[6]
                    if data_exp < (hoje-timedelta(15)):  # Se já passou algum tempo desde expedição...
                        tag_cor = "falta_chq"


            self.tree.insert("", n_remessas, tag=tag_cor, text ="Texto_nao_sei_que",
                            values=(dias,
                            row[1],  # destin
                            row[2],  # Estado
                            row[3],  # Obj nº
                            row[8],  # Nº de volumes
                            row[5],  # Cobrança
                            data_r_chq,  # Data de recebimento de cheque
                            data_dep_chq,  #Data prevista de depósito
                            ))


            n_remessas += 1
            volumes += int(row[8])
            if float(row[5]) > 0.0:
                com_cobranca += 1
                tot_cobr += float(row[5])
        c.close()

        self.tree.tag_configure('falta_chq', background='peach puff') # Se falta cheque e cobrança já antiga -> laranja
        self.tree.tag_configure('depositar', background='dodger blue') # Se já veio cheque e é dia de depositar -> magenta
        self.tree.tag_configure('falhou_entrega', background='orange red') # Se objeto nao entregue -> vermelho
        self.tree.tag_configure('antigo', background='yellow') # Se objeto nao entregue -> vermelho

        s_status = "Em curso:  {} remessas com um total de {} volumes. {} remessas com cobrança ({:,.2f}€).".format(n_remessas, volumes, com_cobranca, tot_cobr).replace(',', ' ')
        self.status_txt.set(s_status)


    def ativar_cobr(self, *event):
        global estado_tabela
        estado_tabela = "Cobrança"
        self.liga_arquivar()
        self.hide_entryform()
        self.hide_detalhe()
        self.text_input_pesquisa.delete(0, END)
        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute ("""SELECT *
                      FROM remessas
                      WHERE (valor_cobr > 0) AND (arquivado = 0);""")
        for i in self.tree.get_children():  # Limpar tabela antes de obter registos atualizados da base de dados
            self.tree.delete(i)
        n_remessas = 0
        volumes = 0
        com_cobranca = 0
        com_cobr_rec = 0
        cobr_atrasadas = 0
        valor_cobr_rec = 0.0
        tot_cobr = 0.0
        impar = "impar"
        tag_cor = " "
        hoje = datetime.now()
        for row in c:  # Preencher cada linha da tabela com os valores obtidos da base de dados
            data_exp = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S.%f")
            dias = calcular_dias_desde_envio(data_exp)

            tag_cor = impar
            if row[2] == "Objeto com tentativa de entrega":
                tag_cor = "falhou_entrega"
            elif data_exp < (hoje-timedelta(0)) and (row[2] != "Objeto entregue"):  # Se já passou algum tempo desde expedição e objeto não foi entregue...
                tag_cor = "antigo"

            if row[5] == "0":  # se remessa sem cobrança
                data_r_chq = " "
                data_dep_chq = " "
            else:  # se remessa com cobrança
                dt_data_dep_chq = datetime.strptime(row[7], "%Y-%m-%d %H:%M:%S.%f")
                data_dep_chq = datetime.strftime(dt_data_dep_chq,"%Y-%m-%d")

                if row[6] != "N/D":  # Se já chegou o cheque
                    dt_data_r_chq = datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S.%f")
                    data_r_chq = datetime.strftime(dt_data_r_chq,"%Y-%m-%d")
                    com_cobr_rec += 1
                    valor_cobr_rec += float(row[5])

                    if dt_data_dep_chq < (hoje+timedelta(3)):  # Se data a depositar é nos próximos dias...
                        tag_cor = "depositar"

                else:  # Se ainda não chegou o cheque
                    data_r_chq = row[6]
                    if data_exp < (hoje-timedelta(15)):  # Se já passou algum tempo desde expedição...
                        tag_cor = "falta_chq"
                        cobr_atrasadas += 1


            self.tree.insert("", n_remessas, tag=tag_cor, text ="Texto_nao_sei_que",
                             values=(dias,
                             row[1],  # destin
                             row[2],  # Estado
                             row[3],  # Obj nº
                             row[8],  # Nº de volumes
                             row[5],  # Cobrança
                             data_r_chq,  # Data de recebimento de cheque
                             data_dep_chq,  #Data prevista de depósito
                             ))

            n_remessas += 1
            volumes += int(row[8])
            if float(row[5]) > 0.0:
                com_cobranca += 1
                tot_cobr += float(row[5])
        c.close()

        self.tree.tag_configure('falta_chq', background='peach puff') # Se falta cheque e cobrança já antiga -> laranja
        self.tree.tag_configure('depositar', background='dodger blue') # Se já veio cheque e é dia de depositar -> magenta
        self.tree.tag_configure('falhou_entrega', background='orange red') # Se objeto nao entregue -> vermelho
        self.tree.tag_configure('antigo', background='yellow') # Se objeto nao entregue -> vermelho

        remessas_s_cobr_rec = n_remessas - com_cobr_rec
        valor_a_aguardar_chq = tot_cobr - valor_cobr_rec
        s_status = "Com cobrança:  {} remessas ({:,.2f}€).".format(n_remessas, tot_cobr).replace(',', ' ')
        if remessas_s_cobr_rec > 0:
            str_chq_falta = "  Falta receber {} cheques ({:,.2f}€).".format(remessas_s_cobr_rec, valor_a_aguardar_chq).replace(',', ' ')
            s_status = s_status + str_chq_falta

        if cobr_atrasadas > 0:
            str_cobr_atr = "  Há {} cobranças atrasadas!".format(cobr_atrasadas)
            s_status = s_status + str_cobr_atr

        #     Depositar hoje {} cheques.
        self.status_txt.set(s_status)




    def liga_chq_recebido(self):
        """
        Transforma o botão de "Depósito" em "Cheque"
        """
        self.btn_pag.config(text=" ✅", command=self.pag_recebido)
        self.label_pag.config(text="Cheque Rec.")

    def liga_depositar_chq(self):
        """
        Transforma o botão de "Cheque" em "Depositar"
        """
        self.btn_pag .config(text=" ⏬", command=self.chq_depositado)
        self.label_pag.config(text="Depositar")


    def liga_restaurar(self):
        """
        Transforma o botão de "Arquivar" em "Restaurar"
        """
        self.btn_del.config(text=" ⤴️")
        self.label_del.config(text="Restaurar")


    def liga_arquivar(self):
        """
        Transforma o botão de "Restaurar" em "Arquivar"
        """
        self.btn_del.config(text="❌")
        self.label_del.config(text="Arquivar")


    def ativar_arquivo(self, *event):
        global estado_tabela
        estado_tabela = "Arquivo"
        self.hide_entryform()
        self.hide_detalhe()
        self.liga_restaurar()
        self.text_input_pesquisa.delete(0, END)

        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        c.execute ("""SELECT *
                      FROM remessas
                      WHERE (arquivado = 1)
                      ORDER BY data_exp DESC;""")
        for i in self.tree.get_children():  # Limpar tabela antes de obter registos atualizados da base de dados
            self.tree.delete(i)
        n_remessas = 0
        volumes = 0
        com_cobranca = 0
        tot_cobr = 0.0
        stag = "par"
        for row in c:  # Preencher cada linha da tabela com os valores obtidos da base de dados
            data_exp = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S.%f")
            dias = calcular_dias_desde_envio(data_exp)

            if row[5] == "0":  # Se remessa sem cobrança
                data_r_chq = " "
                data_dep_chq = " "
            else:  # Se remessa com cobrança
                cobr = row[5]
                dt_data_dep_chq = datetime.strptime(row[7], "%Y-%m-%d %H:%M:%S.%f")
                data_dep_chq = datetime.strftime(dt_data_dep_chq,"%Y-%m-%d")
                if row[6] != "N/D":  # Se ainda não chegou o cheque
                        dt_data_r_chq = datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S.%f")
                        data_r_chq = datetime.strftime(dt_data_r_chq,"%Y-%m-%d")
                else:  # Se já chegou o cheque
                        data_r_chq = row[6]


            self.tree.insert("", n_remessas, tag=stag, text ="Texto_nao_sei_que",
                             values=(dias,
                                     row[1],  # destin
                                     row[2],  # Estado
                                     row[3],  # Obj nº
                                     row[8],  # Nº de volumes
                                     row[5],  # Cobrança
                                     data_r_chq,  # Data de recebimento de cheque
                                     data_dep_chq,  #Data prevista de depósito
                                     ))

            n_remessas += 1
            volumes += int(row[8])
            if float(row[5]) > 0.0:
                com_cobranca += 1
                tot_cobr += float(row[5])

        c.close()

        s_status = "{} volumes arquivados. {} remessas. {} com cobrança (total: {:,.2f}€).".format(volumes, n_remessas, com_cobranca, tot_cobr).replace(',', ' ')
        self.status_txt.set(s_status)


    def cancelar_pesquisa(self, event):
        global pesquisa_visible
        pesquisa_visible = 0
        self.tree.focus_set()
        self.regressar_tabela()


    def ativar_pesquisa(self, event):
        global pesquisa_visible
        pesquisa_visible = 1
        #estado_tabela = "Pesquisa"
        self.liga_arquivar()
        self.hide_entryform()
        self.hide_detalhe()

        termo_pesquisa = self.text_input_pesquisa.get()
        termo_pesquisa = termo_pesquisa.strip()

        # regressar ao campo de pesquisa caso não haja texto a pesquisar (resolve questão do atalho de teclado)
        if termo_pesquisa == "":
            return

        self.status_txt.set("A pesquisar: {}".format(termo_pesquisa))

        conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
        c = conn.cursor()
        termo = "%" + termo_pesquisa + "%"
        c.execute ("""SELECT *
                      FROM remessas
                      WHERE (destin LIKE ?) OR (obj_num LIKE ?) OR (rma LIKE ?) OR (obs LIKE ?) OR (expedidor LIKE ?) OR (data_exp LIKE ?) OR (valor_cobr LIKE ?)
                      ORDER BY data_exp DESC;""",
                      (termo, termo, termo, termo, termo, termo, termo))
        for i in self.tree.get_children():  # Limpar tabela antes de obter registos atualizados da base de dados
            self.tree.delete(i)
        n_remessas = 0
        volumes = 0
        com_cobranca = 0
        tot_cobr = 0.0
        impar = "par"
        for row in c:  # Preencher cada linha da tabela com os valores obtidos da base de dados
            data_exp = datetime.strptime(row[4], "%Y-%m-%d %H:%M:%S.%f")
            dias = calcular_dias_desde_envio(data_exp)

            if row[5] == "0":  # Se remessa sem cobrança
                data_r_chq = " "
                data_dep_chq = " "
            else:  # Se remessa com cobrança
                cobr = row[5]
                dt_data_dep_chq = datetime.strptime(row[7], "%Y-%m-%d %H:%M:%S.%f")
                data_dep_chq = datetime.strftime(dt_data_dep_chq,"%Y-%m-%d")
                if row[6] != "N/D":  # Se ainda não chegou o cheque
                    dt_data_r_chq = datetime.strptime(row[6], "%Y-%m-%d %H:%M:%S.%f")
                    data_r_chq = datetime.strftime(dt_data_r_chq,"%Y-%m-%d")
                else:  # Se já chegou o cheque
                    data_r_chq = row[6]

            self.tree.insert("", n_remessas, tag=impar, text ="Texto_nao_sei_que",
                             values=(dias,
                                     row[1],  # destin
                                     row[2],  # Estado
                                     row[3],  # Obj nº
                                     row[8],  # Nº de volumes
                                     row[5],  # Cobrança
                                     data_r_chq,  # Data de recebimento de cheque
                                     data_dep_chq,  #Data prevista de depósito
                                     ))


            n_remessas += 1
            volumes += int(row[8])
            if float(row[5]) > 0.0:
                com_cobranca += 1
                tot_cobr += float(row[5])
        c.close()
        #self.tree.tag_configure('par', background='grey96') # Linhas pares em cor diferente
        s_status = "Pesquisa: {}. Encontradas {} remessas. Total de {} volumes. {} remessas com cobrança (total: {:,.2f}€).".format('"'+termo_pesquisa.upper()+'"', n_remessas, volumes, com_cobranca, tot_cobr).replace(',', ' ')
        self.status_txt.set(s_status)


    # Verificar dados, formatar corretamente e adicionar à base de dados ----------------------------------------------
    def add_remessa(self, event):
        global DB_PATH
        add_obj = self.text_input_obj.get().strip()
        add_destin = self.text_input_destin.get().strip()
        add_cobr = self.text_input_cobr.get().strip()
        add_dias = self.text_input_dias.get().strip()
        add_vols = self.text_input_vols.get().strip()
        add_rma = self.text_input_rma.get().strip()
        add_obs = self.text_input_obs.get().strip()
        add_expedidor = self.combo_expedidor.get()
        agora = datetime.now()
        self.bottomframe.focus_set()

        # Validar dados do formulário e verificar se todos os campos obrigatórios estão preenchidos.
        pattern = r"^[A-Za-z]{2,2}[0-9]{9,9}[A-Za-z]{2,2}$"
        if (add_obj == ""):
            self.status_txt.set("Para adicionar uma remessa é necessário introduzir o número de objeto.")
            self.text_input_obj.focus_set()
            return
        elif (re.match(pattern, add_obj) == None):
            self.status_txt.set("Número de objeto inválido!")
            self.text_input_obj.focus_set()
            return
        else:
            add_obj = add_obj.upper()

        if (add_destin == ""):
            self.status_txt.set("Para adicionar uma remessa é necessário introduzir o nome do destinatário.")
            self.text_input_destin.focus_set()
            return


        if add_vols == "":
            add_vols = "1"
        else:
            try:
                num = int(add_vols)
            except ValueError:
                self.status_txt.set("O número de volumes deve ser um valor inteiro.")
                self.text_input_vols.focus_set()
                return


        if (add_expedidor not in EXPEDIDORES):
            self.status_txt.set("Por favor selecione o expedidor.")
            self.combo_expedidor.focus_set()
            return


        if add_cobr == "":
            add_cobr = "0"
        else:
            add_cobr = add_cobr.replace(",", ".")  # pontos --> virgulas nos valores dos cheques
            try:
                num = float(add_cobr)
            except ValueError:
                self.status_txt.set("O montante a cobrar deve ser um valor inteiro ou decimal.")
                self.text_input_cobr.focus_set()
                return

        if (float(add_cobr) == 0):
            num_dias = 0
        else:
            if add_dias == "":
                self.status_txt.set("""Por favor, introduza o prazo de pagamento ("PP" ou o número de dias) para esta remessa com cobrança.""")
                self.text_input_dias.focus_set()
                return
            elif add_dias.upper() == "PP":
                num_dias = 1
            else:
                try:
                    num_dias = int(add_dias)
                except ValueError:
                    self.status_txt.set("""O prazo de pagamento deve ser introduzido como "PP" (pronto pagamento) ou indicando o número de dias.""")
                    self.text_input_vols.focus_set()
                    return
        data_dep = calcular_data_deposito(agora, num_dias)
        # reunir variáveis que faltam #TODO


        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        try:
            c.execute("""INSERT INTO remessas
                         VALUES ((SELECT max(id) FROM remessas)+1,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?);""", (
                                add_destin,
                                "- Informação não disponível -",
                                add_obj,
                                agora,
                                add_cobr,
                                "N/D",
                                data_dep,
                                add_vols,
                                add_rma,
                                add_expedidor,
                                add_obs,
                                0,
                                NUNCA,
                                NUNCA,
                                agora,
                                "N/D"
                                ))
        except sqlite3.IntegrityError:
            self.status_txt.set("""O objeto com o nº indicado já existe na base de dados.""")
            self.text_input_vols.focus_set()
            return
        conn.commit()
        c.close()
        self.lista_destinatarios = db_get_destinatarios()
        criar_mini_db()

        remessa = "({}, {})".format(add_obj, add_destin)
        self.status_txt.set("Nova remessa adicionada! {}".format(remessa))
        self.text_input_obj.focus_set()
        self.clear_text()


    # Registar pagamento recebido -------------------------------------------------------------------------------------

    def pag_recebido(self, *event):
        """
        Registar a receção de meio de pagamento (p.ex. cheque)
        """
        global DB_PATH
        self.atualizar_remessa_selecionada()

        if self.remessa_selecionada == "":
            messagebox.showwarning("", "Nenhuma remessa selecionada.")
            root.focus_force()
            return

        remessa = self.remessa_selecionada
        agora = datetime.now()

        curItem = self.tree.focus()
        tree_linha = self.tree.item(curItem)
        tree_cobr = float(tree_linha["values"][5])
        tree_data = tree_linha["values"][6]

        if (tree_cobr > 0) and (tree_data == "N/D"):
            try:
                self.status_txt.set("A registar pagamento recebido referente à remessa {}. Por favor, verificar a data para depósito do cheque.".format(remessa))
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""UPDATE remessas
                             SET chq_recebido = ?, data_ult_alt = ?
                             WHERE (valor_cobr != 0) AND (chq_recebido == ?) AND (obj_num = ?);""",
                             (agora, agora, "N/D", remessa))
                conn.commit()
                c.close()
            except:
                msg = "Não foi possível registar na base de dados o pagamento da remessa."
                self.status_txt.set(msg)
                messagebox.showwarning("Atenção", msg)
                root.focus_force()
        else:
            msg = "Não foi possível registar na base de dados o pagamento da remessa. Verifique se é mesmo uma remessa com cobrança e se o cheque correspondente não foi ainda depositado."
            self.status_txt.set(msg)
            messagebox.showwarning("Atenção", msg)
            root.focus_force()
        criar_mini_db()
        self.remessa_selecionada = ""
        self.regressar_tabela()


    def chq_depositado(self, *event):
        """
        Registar a data aquando do depósito do cheque no banco e arquivar a remessa.
        """
        global DB_PATH
        self.atualizar_remessa_selecionada()

        if self.remessa_selecionada == "":
            messagebox.showwarning("", "Nenhuma remessa selecionada.")
            root.focus_force()
            return

        remessa = self.remessa_selecionada
        agora = datetime.now()

        curItem = self.tree.focus()
        tree_linha = self.tree.item(curItem)
        tree_cobr = float(tree_linha["values"][5])
        tree_data = tree_linha["values"][6]

        if (tree_cobr > 0) and (tree_data != "N/D"):
            try:
                conn = sqlite3.connect(DB_PATH)
                c = conn.cursor()
                c.execute("""UPDATE remessas
                             SET data_depositado = ?, data_ult_alt = ?, arquivado = ?
                             WHERE (valor_cobr > 0) AND (chq_recebido != ?) AND (obj_num = ?);""",
                             (agora, agora, 1, "N/D", remessa))
                conn.commit()
                c.close()
                self.status_txt.set("A registar o depósito do cheque referente à remessa {}. Remessa arquivada!".format(remessa))
            except:
                msg = "Não foi possível registar na base de dados o depósito deste cheque."
                self.status_txt.set(msg)
                messagebox.showinfo("Atenção", msg)
                root.focus_force()
        else:
            msg = "Não foi possível registar na base de dados o pagamento da remessa. Verifique se é mesmo uma remessa com cobrança e se foi registada a receção do cheque."
            self.status_txt.set(msg)
            messagebox.showwarning("", msg)
            root.focus_force()
        criar_mini_db()
        self.remessa_selecionada = ""
        self.regressar_tabela()


    def copiar_hoje(self, event=None):
        """ Gerar lista de envios de hoje, pré-formatada para copiar e enviar via email
        """
        global DB_PATH
        objeto, destino, vols, cobr = "","","",""

        self.btn_hoje.configure(state="disabled")

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT obj_num, destin, vols, valor_cobr
                     FROM remessas
                     WHERE data_exp >= datetime("now", "-12 hours")
                     ORDER BY destin ASC, valor_cobr ASC;''')
        remessas = c.fetchall()
        c.close()

        texto_completo = "Encomendas expedidas hoje:\n\n"
        for linha in remessas:
            destino = linha[1]
            objeto = linha[0]
            vols = str(linha[2])
            cobr = str(linha[3])

            if vols == "1":
                    vols = vols + " volume"
            else:
                    vols = vols + " volumes"
            if cobr == "0":
                    cobr = "s/cobrança"
            else:
                    cobr = cobr + " €"
            texto = objeto + " – " + destino + " (" + vols + ", " + cobr + ")\n"
            texto_completo = texto_completo + texto
        texto_completo += "\n"
        os.system("echo %s | pbcopy" % shlex.quote(texto_completo))
        self.remessa_selecionada = ""
        self.regressar_tabela()

        x, y = int(root.winfo_width()/2), 76
        self.popupMsg(x, y, "Lista de remessas de hoje copiada para a Área de Transferência!")
        self.status_txt.set("Lista de remessas de hoje copiada para a Área de Transferência!")
        self.btn_hoje.configure(state="enabled")


    def copiar_obj_num(self, event=None):
        """ Copiar nº de objeto para a Área de Transferência """
        self.atualizar_remessa_selecionada()
        os.system("echo '%s' | pbcopy" % self.remessa_selecionada)
        x, y = int(root.winfo_width()/2), 76
        self.popupMsg(x, y, "Número de objeto copiado para a Área de Transferência!")
        self.status_txt.set("Número de objeto copiado para a Área de Transferência!")


    def copiar_msg(self, event=None):
        """ Copiar notificação de expedição para a Área de Transferência (para
                colar em nova mensagem de email)
        """
        self.atualizar_remessa_selecionada()
        info_principal = MSG_INFO_PRINCIPAL + self.remessa_selecionada
        link = MSG_LINK.format(self.remessa_selecionada)
        texto_completo = MSG_SAUDACAO + MSG_INTRO + info_principal + link + MSG_OUTRO
        os.system("echo %s | pbcopy" % shlex.quote(texto_completo))
        x, y = int(root.winfo_width()/2), 76
        self.popupMsg(x, y, "Texto da mensagem copiado para a Área de Transferência!")
        self.status_txt.set("Texto da mensagem copiado para a Área de Transferência!")


    def copiar_chq_hoje(self, event=None):
        """ Gerar lista de cheques depositados hoje, pré-formatada para copiar e enviar via email
        """
        global DB_PATH
        objeto, destino, cobr = "","",""

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT obj_num, destin, valor_cobr
                     FROM remessas
                     WHERE data_depositado >= datetime("now", "-12 hours")
                     ORDER BY destin ASC, valor_cobr DESC;''')
        remessas = c.fetchall()
        c.close()

        texto_completo = "Cheques depositados hoje:\n\n"
        montante_total = 0
        for linha in remessas:
            destino = linha[1]
            objeto = linha[0]
            cobr = str(linha[2])
            montante_total += float(linha[2])

            cobr = cobr + " €"
            texto = destino + " - " + cobr + " (" + objeto + ")\n"
            texto_completo = texto_completo + texto
        texto_completo += "\nTotal depositado: {:,.2f} euros.\n".format(float(montante_total)).replace(',', ' ')

        os.system("echo %s | pbcopy" % shlex.quote(texto_completo))
        self.remessa_selecionada = ""
        self.regressar_tabela()

        x, y = int(root.winfo_width()/2), 76
        self.popupMsg(x, y, "Lista de cheques depositados hoje copiada para a Área de Transferência!")
        self.status_txt.set("Lista de cheques depositados hoje copiada para a Área de Transferência!")


    def copiar_chq_por_depositar(self, event=None):
        """ Gerar lista de cheques ainda não depositados, pré-formatada para copiar e enviar via email
        """
        global DB_PATH
        objeto, destino, cobr, data_depositar = "","","",""

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT obj_num, destin, valor_cobr, data_depositar
                     FROM remessas
                     WHERE (valor_cobr > 0) AND (data_depositado = 0) AND (chq_recebido != "N/D")
                     ORDER BY data_depositar ASC, destin ASC;''')
        remessas = c.fetchall()
        c.close()

        texto_completo = "Cheques ainda não depositados:\n\n"
        montante_total = 0
        numero_cheques = 0
        for linha in remessas:
            destino = linha[1]
            objeto = linha[0]
            cobr = str(linha[2])
            montante_total += float(linha[2])
            numero_cheques += 1
            dt_data_depositar = datetime.strptime(linha[3], "%Y-%m-%d %H:%M:%S.%f")
            data_depositar = datetime.strftime(dt_data_depositar,"%Y-%m-%d")

            cobr = cobr + " €"
            texto = destino + " - " + cobr + ", previsto para " + data_depositar + " (" + objeto + ")\n"
            texto_completo += texto

        texto_completo += "\nTotal ainda por depositar: {:,.2f} euros ({} cheques).\n".format(float(montante_total), numero_cheques).replace(',', ' ')

        texto_rodape = "\n\nNota: datas estimadas automaticamente com base nos respetivos registos de expedição."
        texto_completo += texto_rodape
        texto_completo += "\n"
        os.system("echo %s | pbcopy" % shlex.quote(texto_completo))
        self.remessa_selecionada = ""
        self.regressar_tabela()
        x, y = int(root.winfo_width()/2), 76
        self.popupMsg(x, y, "Lista de cheques por depositar copiada para a Área de Transferência!")
        self.status_txt.set("Lista de cheques por depositar copiada para a Área de Transferência!")


    def copiar_chq_nao_recebidos(self, event=None):
        """ Gerar lista de cheques ainda não recebidos, pré-formatada para copiar e enviar via email
        """
        global DB_PATH
        objeto, destino, cobr, data_depositar = "","","",""

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT obj_num, destin, valor_cobr, data_depositar
                     FROM remessas
                     WHERE (arquivado = 0) AND (valor_cobr > 0) AND (chq_recebido = "N/D")
                     ORDER BY destin ASC, data_depositar ASC;''')
        remessas = c.fetchall()
        c.close()

        texto_completo = "Cheques ainda não recebidos:\n\n"
        numero_cheques = 0
        montante_total = 0
        for linha in remessas:
            destino = linha[1]
            objeto = linha[0]
            cobr = str(linha[2])
            montante_total += float(linha[2])
            numero_cheques += 1
            dt_data_depositar = datetime.strptime(linha[3], "%Y-%m-%d %H:%M:%S.%f")
            data_depositar = datetime.strftime(dt_data_depositar,"%Y-%m-%d")

            cobr = cobr + " €"
            texto = destino + " - " + cobr + ", previsto para " + data_depositar + " (" + objeto + ")\n"
            texto_completo += texto

        texto_completo += "\nTotal em cheques ainda não recebidos: {:,.2f} euros ({} cheques).\n".format(float(montante_total), numero_cheques).replace(',', ' ')

        texto_rodape = "\n\nNota: datas estimadas automaticamente com base nos respetivos registos de expedição."
        texto_completo += texto_rodape
        texto_completo += "\n"
        os.system("echo %s | pbcopy" % shlex.quote(texto_completo))
        self.remessa_selecionada = ""
        self.regressar_tabela()
        x, y = int(root.winfo_width()/2), 76
        self.popupMsg(x, y, "Lista de cheques ainda não recebidos copiada para a Área de Transferência!")
        self.status_txt.set("Lista de cheques ainda não recebidos copiada para a Área de Transferência!")


    def copiar_lista_por_expedidor(self, event=None):
        """ Gerar lista de todos os cheques já depositados, pré-formatada para copiar e enviar via email
        """
        global DB_PATH
        objeto, destino, cobr = "","",""

        texto_completo = ""
        for expedidor in EXPEDIDORES:
            conn = sqlite3.connect(DB_PATH)
            texto_completo_expedidor = "\n\n\n" + 17*"=" + "[ Envios referentes ao expedidor: " + expedidor + " ]"+ 17*"=" + "\n\n"
            c = conn.cursor()
            c.execute('''SELECT data_exp, obj_num, destin, vols, valor_cobr
                         FROM remessas
                         WHERE expedidor = ?
                         ORDER BY data_exp ASC, destin ASC;''',
                         (expedidor,)
                                )
            remessas = c.fetchall()
            c.close()

            num_remessas = len(remessas)
            total_vols, remessas_com_cobr, total_remessas_multiplos, total_vols_multiplos, total_simples = 0, 0, 0, 0, 0
            ano, mes = 0, 0
            str_data, str_ano, str_mes, resumo_mes = "", "", "", ""
            ano_diferente, mes_diferente = True, True
            remessas_mes, vols_mes, remessas_cobr_mes, remessas_mult_mes, remessas_simples_mes, vols_mult_mes = 0, 0, 0, 0, 0, 0

            linha_atual, linha_atual_expedidor = 0, 0
            for linha in remessas:
                remessas_mes +=1
                prefixos = ""
                dt_data_expedido = datetime.strptime(linha[0], "%Y-%m-%d %H:%M:%S.%f")
                data_expedido = datetime.strftime(dt_data_expedido,"%Y-%m-%d")
                destino = linha[2]
                objeto = linha[1]
                cobr = float(linha[4])
                vols = linha[3]
                total_vols += vols

                ano_i = dt_data_expedido.year
                mes_i = dt_data_expedido.month

                if ano_i != ano:
                    ano_diferente = True
                    str_ano = str(ano_i)
                    ano = ano_i
                else:
                    ano_diferente = False

                if mes_i != mes:
                    str_mes = str(mes_i)
                    mes = mes_i
                    mes_diferente = True
                else:
                    mes_diferente = False


                if ano_diferente or mes_diferente: # Caso mude mês ou ano
                    if (linha_atual!=0) :  # Se é a última remessa do mês, mostra o resumo mensal.
                        resumo_mes = "    -   -   -\n    Resumo do mês (" + expedidor + "):"
                        txt_mes_remessas = "\n\n    Remessas: " + str(remessas_mes)
                        txt_mes_num_vols     = " (" + str(vols_mes) + " volumes)"
                        txt_mes_simples      = "\n       - Remessas tipo Simples: " + str(remessas_simples_mes)
                        txt_mes_multiplos    = "\n       - Remessas tipo Múltiplo: " + str(remessas_mult_mes) + " (" + str(vols_mult_mes) + " volumes)"
                        txt_mes_num_cobr     = "\n    Envios com cobrança: " + str(remessas_cobr_mes)
                        resumo_mes = resumo_mes + txt_mes_remessas + txt_mes_num_vols + txt_mes_simples + txt_mes_multiplos + txt_mes_num_cobr + "\n\n"
                        texto_completo_expedidor += resumo_mes

                    else:
                        print("nem é a primeira remessa do mês, nem chegou o fim do mês!", linha_atual, linha_atual_expedidor, num_remessas)

                    linha_atual = 0
                    if (linha_atual_expedidor != num_remessas-1):  # Se é a primeira remessa do mês, mostra a data.
                        str_data = "\n\n  " + str_ano + "-" + str_mes + "\n" + 60*"-"+ "\n"
                        texto_completo_expedidor += str_data
                        print("adicionada data para:", str_ano, str_mes)
                        print("linha_atual:", linha_atual)
                        remessas_mes, vols_mes, remessas_cobr_mes, remessas_mult_mes, remessas_simples_mes, vols_mult_mes = 0, 0, 0, 0, 0, 0



                # Aqui começa a listar todas as remessas do mês...
                if cobr > 0.0:
                    remessas_com_cobr += 1
                    remessas_cobr_mes += 1
                    prefixos += "C "
                else:
                    prefixos += "  "

                vols_mes += vols

                if vols > 1:
                    total_remessas_multiplos +=1
                    total_vols_multiplos += vols
                    remessas_mult_mes +=1
                    vols_mult_mes += vols
                    prefixos += "M "
                else:
                    total_simples += 1
                    remessas_simples_mes += 1
                    prefixos += "  "


                txt_cobr = str(cobr) + " €"
                texto_linha = prefixos + data_expedido + " - " + objeto + " - " + destino + " (" + str(vols) + "vols., cobrança: " + txt_cobr + ")\n"
                texto_completo_expedidor += texto_linha

                linha_atual += 1
                linha_atual_expedidor += 1

            remessas_mes +=1
            #mostra resumo do mês para o último mês
            resumo_mes = "    -   -   -\n    Resumo do mês (" + expedidor + "):"
            txt_mes_remessas = "\n\n    Remessas: " + str(remessas_mes)
            txt_mes_num_vols     = " (" + str(vols_mes) + " volumes)"
            txt_mes_simples      = "\n       - Remessas tipo Simples: " + str(remessas_simples_mes)
            txt_mes_multiplos    = "\n       - Remessas tipo Múltiplo: " + str(remessas_mult_mes) + " (" + str(vols_mult_mes) + " volumes)"
            txt_mes_num_cobr     = "\n    Envios com cobrança: " + str(remessas_cobr_mes)
            resumo_mes = resumo_mes + txt_mes_remessas + txt_mes_num_vols + txt_mes_simples + txt_mes_multiplos + txt_mes_num_cobr + "\n\n"
            texto_completo_expedidor += resumo_mes

            # No final, apresenta um resumo global para o expedidor atual...
            txt_num_remessas = "\nResumo Global (" + expedidor +"):\n\nRemessas: " + str(num_remessas)
            txt_num_vols     = " (" + str(total_vols) + " volumes)"
            txt_simples      = "\n   - Remessas tipo Simples: " + str(total_simples)
            txt_multiplos    = "\n   - Remessas tipo Múltiplo: " + str(total_remessas_multiplos) + " (" + str(total_vols_multiplos) + " volumes)"
            txt_num_cobr     = "\nEnvios com cobrança: " + str(remessas_com_cobr)


            texto_completo_expedidor += "\n\n------------------"
            texto_completo_expedidor += txt_num_remessas + txt_num_vols + txt_simples + txt_multiplos + txt_num_cobr + "\n\n\n\n"
            texto_completo += texto_completo_expedidor



        texto_completo += "\n"
        os.system("echo %s | pbcopy" % shlex.quote(texto_completo))
        self.remessa_selecionada = ""
        self.regressar_tabela()
        x, y = int(root.winfo_width()/2), 76
        self.popupMsg(x, y, "Lista de envios copiada para a Área de Transferência!")
        self.status_txt.set("Lista de envios copiada para a Área de Transferência!")



    def copiar_chq_depositados(self, event=None):
        """ Gerar lista de todos os objetos já expedidos, por ordem cronológica, agrupados por expedidor.
        """
        global DB_PATH
        objeto, destino, cobr, data_depositado = "","","",""

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT obj_num, destin, valor_cobr, data_depositado
                     FROM remessas
                     WHERE (valor_cobr > 0) AND (chq_recebido != "N/D") AND (data_depositado != 0)
                     ORDER BY data_depositado DESC, destin ASC;''')
        remessas = c.fetchall()
        c.close()

        texto_completo = "Cheques já depositados:\n\n"
        for linha in remessas:
            destino = linha[1]
            objeto = linha[0]
            cobr = str(linha[2])
            dt_data_depositado = datetime.strptime(linha[3], "%Y-%m-%d %H:%M:%S.%f")
            data_depositado = datetime.strftime(dt_data_depositado,"%Y-%m-%d")

            cobr = cobr + " €"
            texto = destino + " - " + cobr + ", depositado em " + data_depositado + " (" + objeto + ")\n"
            texto_completo += texto

        texto_completo += "\n"
        os.system("echo %s | pbcopy" % shlex.quote(texto_completo))
        self.remessa_selecionada = ""
        self.regressar_tabela()
        x, y = int(root.winfo_width()/2), 76
        self.popupMsg(x, y, "Lista de cheques já depositados copiada para a Área de Transferência!")
        self.status_txt.set("Lista de cheques já depositados copiada para a Área de Transferência!")


    def del_remessa(self):
        global estado_tabela
        self.status_txt.set("Nenhuma remessa selecionada!")
        remessa = self.remessa_selecionada
        if estado_tabela == "Arquivo":
            db_restaurar_remessa(remessa)
            self.status_txt.set("Todas as remessas nesta vista já se encontram arquivadas! A remessa {} foi restaurada.".format(remessa))
        if pesquisa_visible:
            if self.arquivado:
                db_restaurar_remessa(remessa)
                self.status_txt.set("A restaurar a remessa {}.".format(remessa))
            else:
                db_del_remessa(remessa)
                self.status_txt.set("A arquivar remessa {}".format(remessa))
        else:
            db_del_remessa(remessa)
            self.status_txt.set("A arquivar remessa {}".format(remessa))
        criar_mini_db()
        self.remessa_selecionada = ""
        self.regressar_tabela()


    def regressar_tabela(self):
        global estado_tabela

        if estado_tabela == "Cobrança":
            self.ativar_cobr()
        elif estado_tabela == "Arquivo":
            self.ativar_arquivo()
        else:
            self.ativar_emcurso()



    def selectItem(self, *event):
        """
        Obter remessa selecionada (após clique de rato na linha correspondente)
        """
        global DB_PATH
        self.hide_entryform()
        self.hide_detalhe()
        curItem = self.tree.focus()
        tree_linha = self.tree.item(curItem)

        tree_obj_num = tree_linha["values"][3]
        tree_destin = tree_linha["values"][1]
        self.status_txt.set("Remessa selecionada: {} ({})".format(tree_obj_num, tree_destin))
        self.remessa_selecionada = tree_obj_num

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT arquivado, valor_cobr, chq_recebido
                     FROM remessas
                     WHERE (obj_num = ?);''',
                     (tree_obj_num,))
        estado = c.fetchone()
        conn.commit()
        c.close()

        self.arquivado = estado[0]
        valor_cobr = estado[1]
        chq_recebido = estado[2]

        if self.arquivado:
            self.liga_restaurar()
        else:
            self.liga_arquivar()

        if valor_cobr == "0":
            self.btn_pag.state(["disabled"])
            self.label_pag.config(text="(S/Cobrança)")
        else:
            self.btn_pag.state(["!disabled"])
            if chq_recebido == "N/D":
                self.liga_chq_recebido()
            else:
                self.liga_depositar_chq()


    def clique_a_pesquisar(self, event):
        self.text_input_pesquisa.focus_set()
        self.status_txt.set("Por favor, introduza o texto a pesquisar na base de dados.")


    def clear_text(self):
        try:
            self.text_input_obj.delete(0, END)
            self.text_input_destin.delete(0, END)
            self.text_input_cobr.delete(0, END)
            self.text_input_dias.delete(0, END)
            self.text_input_vols.delete(0, END)
            self.text_input_rma.delete(0, END)
            self.text_input_obs.delete(0, END)
            self.combo_expedidor.current(0)
        except Exception as e:
            print("This is a very misterious clear_text() error! But what kind of program would be happy without having some kind of bug like this?...")
            print("Exception:", e)


    def show_entryform(self, *event):
        global entryform_visible

        if entryform_visible:
            self.hide_entryform()
            self.ativar_emcurso()
            self.btn_add.configure(state="enabled")
            return
        else:
            entryform_visible = 1
            self.btn_add.configure(state="disabled")
            # Formulário de entrada de dados (fundo da janela)
            self.hide_detalhe()
            self.statusframe.lift()
            self.status_txt.set("A introduzir dados referentes a nova remessa...")

            for y in range(-10,1,2):
                self.bottomframe.update()
                self.bottomframe.place(in_=self.statusframe, relx=1,  y=y**2, anchor="se", relwidth=1, bordermode="outside")
            self.bottomframe.lift()
            self.text_input_obj.focus_set()
            self.bottomframe.bind_all("<Escape>", self.hide_entryform)


    def hide_entryform(self, *event):
        global entryform_visible
        if entryform_visible:
            entryform_visible = 0
            self.btn_add.configure(state="enabled")
            self.status_txt.set("Cancelando introdução de dados.")
            self.clear_text()
            self.statusframe.lift()
            for y in range(0,11,2):
                self.bottomframe.place(in_=self.statusframe, relx=1,  y=y**2, anchor="se", relwidth=1, bordermode="outside")
                self.bottomframe.update()
            self.bottomframe.place_forget()

    def abrir_url_browser(self,*event):
        self.unbind_tree()
        self.atualizar_remessa_selecionada()
        abrir_url(self.remessa_selecionada)
        root.after(300, self.bind_tree)


    def atualizar_remessa_selecionada(self):
        curItem = self.tree.focus()
        tree_linha = self.tree.item(curItem)
        try:
            tree_obj_num = tree_linha["values"][3]
        except Exception as e:
            print("self.atualizar_remessa_selecionada() > Exception:", e)
            self.remessa_selecionada = ""
            messagebox.showwarning("", "Nenhuma remessa selecionada.")
            root.focus_force()
            return
        else:
            tree_destin = tree_linha["values"][1]
            self.status_txt.set("Remessa selecionada: {} ({})".format(tree_obj_num, tree_destin))
            self.remessa_selecionada = tree_obj_num


    def mostrar_detalhe(self, *event):
        global DB_PATH
        global detalhe_visible
        self.unbind_tree()

        if detalhe_visible:
            self.hide_detalhe()
            return

        detalhe_visible = 1
        self.hide_entryform()
        self.atualizar_remessa_selecionada()

        db_update_estado(self.remessa_selecionada)

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT *
                     FROM remessas
                     WHERE (obj_num = ?);''',
                     (self.remessa_selecionada,))
        detalhes = c.fetchone()
        conn.commit()
        c.close()

        #db_id = detalhes[0]              # INTEGER PRIMARY KEY AUTOINCREMENT,
        destin = detalhes[1]             # TEXT NOT NULL,
        estado = detalhes[2]             # TEXT,
        obj_num = detalhes[3]            # TEXT UNIQUE NOT NULL,

        dt_data_exp = datetime.strptime(detalhes[4], "%Y-%m-%d %H:%M:%S.%f")
        data_exp = datetime.strftime(dt_data_exp,"%Y-%m-%d")

        valor_cobr = detalhes[5]         # TEXT,

        if (valor_cobr != 0) and (detalhes[6] != "N/D"):
            dt_chq_recebido = datetime.strptime(detalhes[6], "%Y-%m-%d %H:%M:%S.%f")
            chq_recebido = datetime.strftime(dt_chq_recebido,"%Y-%m-%d")
        else:
            chq_recebido = "N/D"

        if (valor_cobr != 0) and (detalhes[7] != 0) and (detalhes[7] != None):
            dt_data_depositar = datetime.strptime(detalhes[7], "%Y-%m-%d %H:%M:%S.%f")
            data_depositar = datetime.strftime(dt_data_depositar,"%Y-%m-%d")
        else:
            data_depositar = "N/D"

        vols = detalhes[8]               # INTEGER,
        rma = detalhes[9]                # TEXT,
        expedidor = detalhes[10]         # TEXT NOT NULL,
        obs = detalhes[11]               # TEXT,
        arquivado = detalhes[12]         # BOOLEAN,

        if detalhes[13] != 0:
            dt_data_depositado = datetime.strptime(detalhes[13], "%Y-%m-%d %H:%M:%S.%f")
            data_depositado = datetime.strftime(dt_data_depositado,"%Y-%m-%d")
        else:
            data_depositado = detalhes[13]

        dt_data_ult_alt = datetime.strptime(detalhes[15], "%Y-%m-%d %H:%M:%S.%f")
        data_ult_alt = datetime.strftime(dt_data_ult_alt,"%Y-%m-%d")

        dt_data_ult_verif = datetime.strptime(detalhes[14], "%Y-%m-%d %H:%M:%S.%f")
        data_ult_verif = datetime.strftime(dt_data_ult_verif,"%Y-%m-%d")

        estado_detalhado = detalhes[16]  # TEXT

        self.dfl_remessa = ttk.Label(self.detalheframe, style="BW.TLabel", text="Detalhes da Remessa:  {}\n".format(destin))

        self.dlf_obj_num = ttk.Label(self.detalheframe, text="Nº Objeto: {}".format(obj_num))
        self.dfl_exp = ttk.Label(self.detalheframe, text="Data de expedição:  {}".format(data_exp))
        self.dfl_vols = ttk.Label(self.detalheframe, text="Nº de volumes: {}".format(vols))

        self.dfl_remessa.grid(column=0, row=0, columnspan=7, sticky=W)
        self.dlf_obj_num.grid(column=0, row=1, sticky=W)
        self.dfl_exp.grid(column=0, row=2, sticky=W)
        self.dfl_vols.grid(column=0, row=3, sticky=W)

        if obs != "":
            self.dfl_obs = ttk.Label(self.detalheframe, text="Observações: {}".format(obs))
            self.dfl_obs.grid(column=0, row=4, columnspan=3, sticky=W)

        str_valor_cobr = "Remessa sem cobrança" if valor_cobr == "0" else "Cobrança: {:,.2f}€".format(float(valor_cobr))
        self.dfl_cobr = ttk.Label(self.detalheframe, text=str_valor_cobr)
        self.dfl_rma = ttk.Label(self.detalheframe, text="Processo RMA: {}".format(rma))

        str_arquivado = "Não" if arquivado == 0 else arquivado

        self.dfl_arquivo = ttk.Label(self.detalheframe, text="Remessa arquivada: {}".format(str_arquivado))

        self.dfl_cobr.grid(column=1, row=1, sticky=W)
        self.dfl_rma.grid(column=1, row=2, sticky=W)
        self.dfl_arquivo.grid(column=1, row=3, sticky=W)


        ttk.Label(self.detalheframe, text="Expedidor: {}".format(expedidor)).grid(column=0, row=6, sticky=W)

        if valor_cobr !="0":
            str_chq_recebido = "Não" if chq_recebido == "N/D" else chq_recebido
            self.dfl_chq_rec = ttk.Label(self.detalheframe, text="Cheque recebido:  {}".format(str_chq_recebido))
            self.dfl_data_depositar = ttk.Label(self.detalheframe, text="Depósito previsto:  {}".format(data_depositar))
            str_data_depositado = "Não" if data_depositado == 0 else data_depositado
            self.dfl_data_depositado = ttk.Label(self.detalheframe, text="Depósito efetuado: {}".format(str_data_depositado))
            self.dfl_chq_rec.grid(column=2, row=1, sticky=W)
            self.dfl_data_depositar.grid(column=2, row=2, sticky=W)
            self.dfl_data_depositado.grid(column=2, row=3, sticky=W)

        ttk.Separator(self.detalheframe).grid(column=0, row=7, pady=14, padx=3, columnspan=7, sticky=W+E)

        self.S = AutoScrollbar(self.detalheframe)
        self.T = Text(self.detalheframe, height=19, width=100)
        self.S.grid(column=7, row=8, sticky=W+N+S)
        self.T.grid(column=0, columnspan=7, row=8,sticky=W+N+E)
        self.S.config(command=self.T.yview)
        self.T.config(yscrollcommand=self.S.set)
        self.T.insert(END, estado_detalhado, 'tabela')
        self.T.tag_config('tabela', foreground='#476042', justify="center", font=('Andale Mono', 12, 'bold'))

        self.btn_fechar_det = ttk.Button(self.detalheframe, text="Fechar", command=self.hide_detalhe)
        self.btn_fechar_det.grid(column=6, row=1, sticky=W+E)

        self.btn_arquivar_det = ttk.Button(self.detalheframe, text="Arquivar", command=self.del_remessa)
        self.btn_arquivar_det.grid(column=6, row=2, sticky=W+E)

        self.btn_ver_web = ttk.Button(self.detalheframe, text="Ver na Web", command=self.abrir_url_browser)
        self.btn_ver_web.grid(column=6, row=3, sticky=W+E)

        for col in range(6):
            self.detalheframe.columnconfigure(col, weight=1)

        # animação de entrada do painel de detalhes:
        for y in range(-14,1,2):
            self.detalheframe.update()
            self.detalheframe.place(in_=self.statusframe, relx=1,  y=y**2, anchor="se", relwidth=1, bordermode="outside")

        self.detalheframe.lift()
        self.status_txt.set("A mostrar detalhes de remessa: {} ({})".format(obj_num, destin))
        self.detalheframe.bind_all("<Escape>", self.hide_detalhe)
        root.after(300, self.bind_tree)



    def hide_detalhe(self, *event):
        global detalhe_visible
        self.statusframe.lift()

        if detalhe_visible:
            detalhe_visible = 0
            # animação de saída do painel de detalhes:
            for y in range(0,14,2):
                    self.detalheframe.place(in_=self.statusframe, relx=1,  y=y**2, anchor="se", relwidth=1, bordermode="outside")
                    self.detalheframe.update()

            for widget in self.detalheframe.winfo_children():
                    widget.destroy()
            self.detalheframe.update()
            self.detalheframe.place_forget()

            self.status_txt.set("Regressando ao painel principal.")
        else:
            self.detalheframe.place_forget()

        self.bind_tree()



if __name__ == "__main__":
    print("\nBem-vindo(a) ao {} ({})!\n".format(__app_name__, __version__))
    print(__copyright__)
    print(__license__)
    print("\n\n - A inicializar base de dados principal.")
    db_inicializar()
    print(" - A atualizar base de dados para dispositivos móveis.")
    criar_mini_db()
    print(" - A preparar interface gráfica.")
    print("   * ", end="", flush=True)
    root = Tk()
    print("* ", end="", flush=True)
    root.configure(background='grey95')
    print("* ", end="", flush=True)
    root.geometry('860x650')
    print("* ", end="", flush=True)
    janela = Janela(root)
    print("*", end="", flush=True)
    root.bind_all("<Mod2-q>", exit)
    print("\n\n - Até já! :-)\n\n")
    root.mainloop()
