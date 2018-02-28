#!/usr/bin/env python3.6
# encoding: utf-8
"""
Este módulo é parte integrante da aplicação PT Tracking, desenvolvida por
Victor Domingos e distribuída sob os termos da licença Creative Commons
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""
import os.path

__app_name__ = "PT Tracking 2018"

"""
# ----- Configurar estas variáveis antes de usar -----
DB_PATH = os.path.expanduser("~") + "/Dropbox/Projetos-Python/PT Tracking/next_version/ctt_tracking/ctt_tracking/db_CTT_Tracking_pre_alpha.sqlite"
MINI_DB_PATH = os.path.expanduser("~") + "/Dropbox/Projetos-Python/PT Tracking/next_version/ctt_tracking/ctt_trackingmini_db_CTT_Tracking.sqlite"
ZIP_MINI_DB_PATH = os.path.expanduser("~") + "/Dropbox/Projetos-Python/PT Tracking/next_version/ctt_tracking/ctt_trackingmini_db_CTT_Tracking.sqlite.zip"
DEBUG_PATH = os.path.expanduser("~") + "/Dropbox/Projetos-Python/PT Tracking/next_version/ctt_tracking/ctt_tracking/debug.txt"
"""

# ----- Configurar estas variáveis antes de usar -----
DB_PATH = os.path.expanduser("~") + "/Dropbox/PT Tracking/next_version/ctt_tracking/ctt_tracking/db_CTT_Tracking_pre_alpha.sqlite"
MINI_DB_PATH = os.path.expanduser("~") + "/Dropbox/PT Tracking/next_version/ctt_tracking/ctt_trackingmini_db_CTT_Tracking.sqlite"
ZIP_MINI_DB_PATH = os.path.expanduser("~") + "/Dropbox/PT Tracking/next_version/ctt_tracking/ctt_trackingmini_db_CTT_Tracking.sqlite.zip"
DEBUG_PATH = os.path.expanduser("~") + "/Dropbox/PT Tracking/next_version/ctt_tracking/ctt_tracking/debug.txt"




# personalizar com o nome da empresa.
EMPRESA = "NPK"

# Personalizar com os nomes dos expedidores a utilizar.
EXPEDIDORES = ("NPK", "Empresa2")

# Especificar aqui o número correspondente ao expedidor predefinido a
# apresentar no campo de introdução de dados. Usar 0 (zero) se preferir não
# selecionar previamente um expedidor.
INDEX_EXPEDIDOR_PREDEFINIDO = 0


# ----------------------------------------------------


# ----- Texto predefinido para as mensagens de notificação de expedição -----
MSG_SAUDACAO = "Boa tarde,\n\n"

MSG_INTRO = "Informamos que a sua encomenda foi hoje enviada pelo serviço CTT Expresso. O material enviado pode ser acompanhado na página dos CTT, utilizando o código de objeto abaixo indicado."

MSG_INFO_PRINCIPAL = "\n\n\nNúmero de objeto: "

MSG_LINK = "\n\nEm alternativa, poderá utilizar diretamente o seguinte endereço:\nhttp://www.cttexpresso.pt/feapl_2/app/open/objectSearch/cttexpresso_feapl_132col-cttexpressoObjectSearch.jspx?lang=def&pesqObjecto.objectoId={}&showResults=true\n\n\n"

MSG_OUTRO = "A encomenda deverá ser entregue no próximo dia útil, até às 18 horas. Se tal não acontecer, p.f. procure na sua estação de correios, no dia útil seguinte, o objeto com o número acima indicado.\n\nAgradecemos a confiança e esperamos continuar a merecer a sua preferência no futuro.\n\n"
# ---------------------------------------------------------------------------


update_delay = 3600000  # Tempo de espera entre as atualizações automáticas (ms)
NUNCA = 0

#You may define here your locations for logging/debugging purposes.
OUR_LOCATIONS = {'127.0.0.1': 'LocationName',}
