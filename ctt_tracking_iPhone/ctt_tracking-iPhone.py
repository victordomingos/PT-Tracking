import ui
import os
import console

import sqlite3
import sys
from datetime import datetime, timedelta
import requests
from bleach import clean
from bs4 import BeautifulSoup
import os.path
import console
import os
import string
import runpy

# Definir como True em dispositivos com Taptic Engine
USETAPTIC = False

if USETAPTIC:
    from objc_util import *  

    UIImpactFeedbackGenerator = ObjCClass('UIImpactFeedbackGenerator')  
    UINotificationFeedbackGenerator = ObjCClass('UINotificationFeedbackGenerator')  
    UISelectionFeedbackGenerator = ObjCClass('UISelectionFeedbackGenerator')


os.chdir(os.path.expanduser('~/Documents/ctt_tracking_ios'))


__app_name__ = "PT-Tracking para iOS"
__author__ = "Victor Domingos"
__copyright__ = "Copyright 2017 Victor Domingos"
__license__ = "Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)"
__version__ = "2.0.1"
__email__ = "web@victordomingos.com"
__status__ = "alpha"


# ----- Configurar estas variáveis antes de usar -----
MINI_DB_FILE = "mini_db_CTT_Tracking.sqlite"
DB_DOWNLOAD_MODULE = 'download_db_file'
EMPRESA = "Empresa"

EXPEDIDORES = ("Empresa 1", "Empresa 2")

DB_PATH = MINI_DB_FILE

# Aumentar para usar num ecrã maior ou em modo horizontal
TITLE_FONTSIZE = 18
TABLE_FONTSIZE = 10.2


# Ajustar de acordo com as definiçoes da app Pythonista
DARK_MODE = True

# ----------------------------------------------------


TRACKING_URL = "http://www.cttexpresso.pt/feapl_2/app/open/objectSearch/cttexpresso_feapl_132col-cttexpressoObjectSearch.jspx?lang=def&pesqObjecto.objectoId={}&showResults=true"

class remessa:
    def __init__(self, remessa, dias, destino, vols, valor_cobr, estado, chq_recebido, data_depositar, data_exp, data_ult_verif):
        self.remessa = remessa
        self.dias = dias
        self.destino = destino
        self.vols = vols
        self.valor_cobr = valor_cobr
        self.estado = estado
        self.chq_recebido = chq_recebido
        self.data_depositar = data_depositar
        self.data_exp = data_exp
        self.data_ult_verif = data_ult_verif
        

class tableSource (object):  
    def __init__(self):
        #self.data = {'remessas':['Light','Medium','Heavy', 'Success','Warning','Error', 'Select' ]}
        self.data = []
        
        self.db_atualizar_tudo()
        
        if USETAPTIC:
            #self.impactgeneratorlight = UIImpactFeedbackGenerator.alloc().initWithStyle_(0)
            #self.impactgeneratormedium = UIImpactFeedbackGenerator.alloc().initWithStyle_(1)
            #self.impactgeneratorheavy = UIImpactFeedbackGenerator.alloc().initWithStyle_(2)
            self.notificationgenerator = UINotificationFeedbackGenerator.alloc().init()
            self.selectiongenerator = UISelectionFeedbackGenerator.alloc().init()
        
        
            #self.impactgeneratorlight.impactOccurred()

    def tableview_number_of_rows(self, tv, s):
        return len(self.data)

    def tableview_number_of_sections(self, tableview):
        return 1
        #return len(self.data.keys())

    def tableview_cell_for_row(self, tv, s, r):
        cell = ui.TableViewCell()
        cell.text_label.text = self.data[r]
        
        cell.text_label.font = ('Helvetica Neue', 14)
        
        #cell.text_label.text_color = 'green'
        cell.accessory_type = 'disclosure_indicator'
        
        selected_cell = ui.View()
        selected_cell.bg_color = '#e0e0e0'
        
        cell.selected_background_view = selected_cell
        
        return cell

    def tableview_title_for_header(self, tableview, section):
        #return list(self.data.keys())[section]
        pass

    def tableview_title_for_footer(self, tableview, section):
        pass

    def tableview_did_select(self, tableview, section, row):
        value = self.data[row]
        
        if USETAPTIC:
            self.selectiongenerator.selectionChanged()
    
    
    
    def adiciona_linha(self, texto, remessa):
        #global DADOS
        
        lista = [texto]
        #DADOS.extend(lista)
        self.data.extend(lista)
    
    
    def db_atualizar_tudo(self):
        """
        Atualizar na base de dados o número de dias desde expedição e os estados
        de todas as remessas ativas (i.e. não arquivadas), exceto as já entregues.
        """
        global DB_PATH
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        hoje = datetime.now()
                     
        c.execute('''SELECT obj_num, destin, data_exp, valor_cobr, vols, estado, data_ult_verif, chq_recebido, data_depositar
                     FROM remessas_movel;''')
        remessas = c.fetchall()
    
        for linha in remessas:
            remessa = linha[0]
            destino = linha[1]
            
            data_ult_verif = linha[6]
            
            chq_recebido = linha[7]
            if chq_recebido != 'N/D':
                chq_recebido = datetime.strptime(linha[7], "%Y-%m-%d %H:%M:%S.%f")
                
            data_depositar = datetime.strptime(linha[8], "%Y-%m-%d %H:%M:%S.%f")
            destino = encurtar_destino(destino)
            
            #data_exp = str(linha[2])
            data_exp = datetime.strptime(linha[2], "%Y-%m-%d %H:%M:%S.%f")
            dias = calcular_dias_desde_envio(data_exp)
         
            valor_cobr = str(linha[3])
            vols = str(linha[4])
            
            estado1 = linha[5]
            if estado1 != 'Objeto entregue':
                estado1 = verificar_estado(remessa)
                if estado1 != "- N/A -":
                    db_update_estado(remessa)
                
            estado = encurtar_estado(estado1)
            
            GUI_txt = ''
            if dias < 10:
                GUI_txt = '  '
                
            GUI_txt = GUI_txt + '{0}  {1} '.format(str(dias), estado)
            
            if chq_recebido == 'N/D' and float(valor_cobr) > 0:
                if calcular_dias_desde_envio(data_exp)>10:
                    GUI_txt = GUI_txt + '⚠️'
                else:
                    GUI_txt = GUI_txt + '⌛️'
                
            if chq_recebido != 'N/D' and float(valor_cobr) > 0:
                if data_depositar < (datetime.now()+timedelta(3)):
                    GUI_txt = GUI_txt + '🛃'
                else:
                    
                    GUI_txt = GUI_txt + '✉️'
            
          
                
            if valor_cobr != "0":
                pass
            else:
                GUI_txt += '     '
                
            GUI_txt += ('  ' + destino)
            
            
            if "✅" not in GUI_txt:
                if data_exp < (hoje-timedelta(1)):  # Se já passou algum tempo desde expedição...
                    pass
            else:
                pass
            
            if valor_cobr != "0":
                GUI_txt += ' {}€'.format(valor_cobr)
            
            if vols != '1':
                GUI_txt += ' ({}v)'.format(vols)
                
            self.adiciona_linha(GUI_txt, remessa)
            GUI_txt =''
            
        conn.commit()
        c.close()
        console.hide_activity()


def db_update_estado(remessa):
    """
    Atualizar na base de dados estado e estado detalhado para uma remessa
    a partir do seu nº de objeto
    """
    global DB_PATH
    estado = verificar_estado(remessa)
    if estado != "- N/A -":
        
        agora = datetime.now()
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""UPDATE remessas_movel 
                         SET estado = ?, data_ult_verif = ? 
                         WHERE obj_num = ?;""", 
                         (estado, agora, remessa))
            conn.commit()
            c.close()
        except:
            print(" - Não foi possível atualizar na base de dados o estado da remessa {}!".format(remessa))



def encurtar_estado(estado):
    if estado in ['- N/A -',
                  'Objeto não encontrado', 
                  'Informação não existente']:
        estado = '❔'
        
    elif estado in ['Objeto aceite', 
                    'Recolha']:
        estado = '🚀'
        
    elif estado in ['Objeto expedido', 
                    'Objeto em distribuição']:
        estado = '🚚'
    else:
        estado = estado.replace('Objeto entregue', '✅')
        estado = estado.replace('Objeto com tentativa de entrega', '⚠️')
        estado = estado.replace('Objeto não entregue', '❌')
    
    if estado not in '✅⚠️🚚❔❌🚀':
        estado = '⚙️'
        
    return estado


def encurtar_destino(destino):
    destino = destino.replace(' - ', ' ')
    destino = destino.replace(', ', ' ')
    destino = destino.replace('. ', '.')
    destino = destino.replace('Maria ', 'Mª ')
    destino = destino.replace('António ', 'Ant.')
    destino = destino.replace('Escola ', 'Esc.')
    destino = destino.replace('Lda.', 'Lda')
    return destino
    
        
def verificar_estado(tracking_code: str) -> str:
    """ Verificar estado de objeto nos CTT
    Ex: verificar_estado("EA746000000PT")
    """
    ctt_url = "https://www.ctt.pt/feapl_2/app/open/objectSearch/objectSearch.jspx"
    estado = "- N/A -"
    try:
        response = requests.post(ctt_url, data={'objects': tracking_code}).content
        sopa = BeautifulSoup(response, "html.parser")
        tabela = sopa.find(id='objectSearchResult').find('table')
        celulas = tabela('td')
        estado = celulas[4].renderContents()
        estado = clean(estado, tags=[], strip=True).strip()
        if estado == "":  # se valor do ult. estado estiver vazio, usar as celulas da tabela seguinte para ler estado
            estado = celulas[9].renderContents()
            estado = clean(estado, tags=[], strip=True).strip()
    except Exception as e:
        print(e)
        print("verificar_estado({}) - Não foi possível obter estado atualizado a partir da web.".format(estado))
    return estado


def calcular_dias_desde_envio(data_expedicao1):
    """ Calcular número de dias que passaram desde que a encomenda foi enviada
    Ex: calcular_dias_desde_envio(data)
    Nota: Requer data no formato datetime.today()
    """
    hoje = datetime.today()
    diferenca = hoje - data_expedicao1
    return diferenca.days   # nº de dias que já passaram


def calcular_data_deposito(data_expedicao2, dias1):
    """ Calcular data prevista do cheque com base na data de expedição
    e condição de pagamento
    Ex: Calcular_data_deposito(data, 30)
    Nota: Requer e devolve data no formato datetime.today()
    """
    if dias1 <= 0:
        return data_expedicao2
    else:
        # d2 == data prevista para o cheque ser depositado
        d2 = data_expedicao2 + timedelta(dias1)
        return d2


if __name__ == "__main__":
    #global DADOS
    #DADOS = []
    
    #db_atualizar_tudo()
    runpy.run_module(DB_DOWNLOAD_MODULE)
    #db_atualizar_tudo()
    
    '''
    fontededados = ui.ListDataSource(DADOS)
    
    v = ui.load_view('GUI-ctt-tracking-ios')
    v['tabela'].data_source = fontededados
    v['tabela'].delegate = fontededados
    #v['tabela'].font = ('Menlo Regular', 16)
    fontededados.font =  ('Helvetica Neue', 14)
    v.present('sheet')
    
    '''

    view = ui.TableView()  
    source = tableSource()  
    view.row_height = 32
    view.data_source = source  
    view.delegate = source  
    view.name = 'PT-Tracking'
    view.present(hide_title_bar=False)
    
