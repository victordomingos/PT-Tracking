#!/usr/bin/env python3.6
# encoding: utf-8
"""
Este módulo é parte integrante da aplicação PT Tracking, desenvolvida por
Victor Domingos e distribuída sob os termos da licença Creative Commons
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

import os.path

__app_name__ = "PT Tracking 2017"


# ----- Configurar estas variáveis antes de usar -----
DB_PATH = os.path.expanduser("~") + "/Dropbox/PT-Tracking/db_PT_Tracking_pre_alpha.sqlite"
MINI_DB_PATH = os.path.expanduser("~") + "/Dropbox/PT-Tracking/mini_db_PT_Tracking.sqlite"
ZIP_MINI_DB_PATH = os.path.expanduser("~") + "/Dropbox/PT-Tracking/mini_db_PT_Tracking.sqlite.zip"
EMPRESA = "Nome da Empresa" # personalizar com o nome da empresa.
EXPEDIDORES = ("Expedidor 1", "Expedidor 2") # Personalizar com os nomes dos expedidores a utilizar.
# ----------------------------------------------------


# ----- Texto predefinido para as mensagens de notificação de expedição -----
MSG_SAUDACAO = "Olá!\n\n"

MSG_INTRO = "Informamos que a sua encomenda foi hoje enviada. O material enviado pode ser acompanhado na página da transportadora, utilizando o código de objeto abaixo indicado."

MSG_INFO_PRINCIPAL = "\n\n\nNúmero de objeto: "

# Colocar aqui o endereço da transportadora (as chavetas {} são substituídas pelo número de objeto)
MSG_LINK = "\n\nEm alternativa, poderá utilizar diretamente o seguinte endereço:\n{}\n\n\n"

MSG_OUTRO = "A encomenda deverá ser entregue no próximo dia útil. Se tal não acontecer, p.f. contacte-nos.\n\n"
# ---------------------------------------------------------------------------


update_delay = 3600000  # Tempo de espera entre as atualizações automáticas (ms)
NUNCA = 0
