import requests
import console
import time
import os
import runpy
import time
from zipfile import ZipFile
import io
import gzip

os.chdir(os.path.expanduser('~/Documents/ctt_tracking_ios'))

# personalizar a linha seguinte com o URL da mini_db no Dropbox, por exemplo:
ZIP_MINI_DB = 'mini_db_PT_Tracking.sqlite.zip?raw=1'

#print("\nA obter base de dados atualizada...")
console.show_activity()
pedido = requests.get(ZIP_MINI_DB)
ficheiro = ZipFile(io.BytesIO(pedido.content))
console.hide_activity()
ficheiro.extract('mini_db_PT_Tracking.sqlite')
