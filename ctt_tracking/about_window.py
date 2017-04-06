import sqlite3
import os.path
import os
from tkinter import *
from tkinter import ttk

from global_setup import *


__app_name__ = "PT Tracking 2016"
__author__ = "Victor Domingos"
__copyright__ = "Copyright 2017 Victor Domingos"
__license__ = "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
__version__ = "v.2.8"
__email__ = "web@victordomingos.com"
__status__ = "Beta"


class thanks_window:
    def __init__(self):
        self.about_w = 320
        self.about_h = 370
        os.chdir(os.path.dirname(__file__))
        file_path = os.getcwd() + "/credits.txt"

        self.thanksRoot = Toplevel()
        self.thanksRoot.title("Agradecimentos")
        self.thanksRoot.focus()

        self.thanksRoot.update_idletasks()
        w = self.thanksRoot.winfo_screenwidth()
        h = self.thanksRoot.winfo_screenheight()
        self.size = tuple(int(_) for _ in self.thanksRoot.geometry().split('+')[0].split('x'))
        self.x = int(w/2 - self.about_w/2)
        self.y = int(h/3 - self.about_h/2)
        self.thanksRoot.configure(background='grey92')
        self.thanksRoot.geometry("{}x{}+{}+{}".format(self.about_w,self.about_h,self.x,self.y))
        self.thanksframe = ttk.Frame(self.thanksRoot, padding="10 10 10 10")
        self.thanksframe_bottom = ttk.Frame(self.thanksRoot, padding="10 10 10 10")


        file = open(file_path, "r")
        texto = file.read()
        file.close()
        self.campo_texto = Text(self.thanksframe, height=20)
        self.campo_texto.insert(END, texto)
        self.campo_texto.tag_configure("center", justify='center')
        self.campo_texto.tag_add("center", 1.0, "end")
        self.campo_texto.pack(side=TOP)


        self.close_button = ttk.Button(self.thanksframe_bottom, text="Obrigado!", command=self.thanksRoot.protocol("WM_DELETE_WINDOW"))
        self.close_button.pack()
        self.thanksframe.pack(side=TOP)
        self.thanksframe_bottom.pack(side=BOTTOM)
            
       

class about_window:
    def __init__(self):
        about_w = 320
        about_h = 370
        global EMPRESA
        global DB_PATH
        remessas = 0
        vols = 0
        destinos = 0
        cobr = 0.0

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute('''SELECT vols, valor_cobr 
                     FROM remessas;''')

        for row in c:
            remessas +=1
            vols += row[0]
            cobr += float(row[1])
        conn.commit()
        c.close()

        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""SELECT DISTINCT destin 
                     FROM remessas;""")
        for row in c:
            destinos +=1
        conn.commit()
        c.close()

        str_remessas= "{} remessas processadas".format(remessas)
        str_vols = "{} volumes expedidos".format(vols)
        str_cobr = "À cobrança: {:,.2f} €".format(cobr).replace(',', ' ')
        str_destinos = "{} destinatários ".format(destinos)

        popupRoot = Toplevel()
        popupRoot.title("")
        popupRoot.focus()

        popupRoot.update_idletasks()
        w = popupRoot.winfo_screenwidth()
        h = popupRoot.winfo_screenheight()
        size = tuple(int(_) for _ in popupRoot.geometry().split('+')[0].split('x'))
        x = int(w/2 - about_w/2)
        y = int(h/3 - about_h/2)
        popupRoot.configure(background='grey92')
        popupRoot.geometry("{}x{}+{}+{}".format(about_w,about_h,x,y))

        pframe_topo = ttk.Frame(popupRoot, padding="10 10 10 2")
        pframe_meio = ttk.Frame(popupRoot, padding="10 2 2 10")
        pframe_fundo = ttk.Frame(popupRoot, padding="10 2 10 10")
        
        os.chdir(os.path.dirname(__file__))
        icon_path = os.getcwd()
        icon_path += "/images/icon.gif"
        icon = PhotoImage(file=icon_path)
        label = ttk.Label(pframe_topo, image=icon)
        label.image = icon
        label.pack(side=TOP)
        label.bind('<Button-1>', thanks)


        appfont = font.Font(size=15, weight='bold')
        copyfont = font.Font(size=10)
        
        #---------- TOPO -----------
        app_lbl = ttk.Label(pframe_topo, font=appfont, text=__app_name__)
        assin_lbl = ttk.Label(pframe_topo,text="\nO gestor avançado de logística da {}.\n".format(EMPRESA))
        version_lbl = ttk.Label(pframe_topo, font=copyfont, text="Versão {}\n\n\n".format(__version__))

        #---------- MEIO -----------
        stats_lbl1 = ttk.Label(pframe_meio, text=str_remessas)
        stats_lbl2 = ttk.Label(pframe_meio, text=str_vols)
        stats_lbl3 = ttk.Label(pframe_meio, text=str_destinos)
        stats_lbl4 = ttk.Label(pframe_meio, text=str_cobr)


        #---------- FUNDO -----------
        copyright_lbl = ttk.Label(pframe_fundo, font=copyfont, text="\n\n\n© 2017 Victor Domingos")
        license_lbl = ttk.Label(pframe_fundo, font=copyfont, text=__license__)


        app_lbl.pack()
        assin_lbl.pack()
        version_lbl.pack()

        stats_lbl1.pack()
        stats_lbl2.pack()
        stats_lbl3.pack()
        stats_lbl4.pack()

        copyright_lbl.pack()
        license_lbl.pack()
        pframe_topo.pack(side=TOP)
        pframe_meio.pack(side=TOP)
        pframe_fundo.pack(side=TOP)
        
        pframe_topo.focus()

        popupRoot.mainloop()
    
    
     
def thanks(*event):
    janela_thanks = thanks_window()


def about(*event):
    janela_thanks.destroy()
    janela_about = about_window()
    
