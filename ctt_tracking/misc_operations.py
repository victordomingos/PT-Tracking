#!/usr/bin/env python3.6
# encoding: utf-8
"""
Este módulo é parte integrante da aplicação PT Tracking, desenvolvida por
Victor Domingos e distribuída sob os termos da licença Creative Commons
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)
"""

import sqlite3
import webbrowser
import sys
import os, errno
import zipfile
import json
import logging
import textwrap as tw

from datetime import datetime, timedelta
from typing import List
from os.path import basename
from terminaltables import AsciiTable

import requests

from bleach import clean
from bs4 import BeautifulSoup

from global_setup import *


def db_inicializar():
    print(" - A abrir base de dados...\n  ", DB_PATH)
    conn = sqlite3.connect(DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    c = conn.cursor()
    print(" - A localizar ou criar tabela de remessas...")
    try:
        c.execute("""CREATE TABLE IF NOT EXISTS remessas (
                id                INTEGER PRIMARY KEY AUTOINCREMENT,
                destin            TEXT NOT NULL,
                estado            TEXT,
                obj_num           TEXT UNIQUE NOT NULL,
                data_exp          DATETIME,
                valor_cobr        TEXT,
                chq_recebido      TEXT,
                data_depositar    TEXT,
                vols              INTEGER,
                rma               TEXT,
                expedidor         TEXT NOT NULL,
                obs               TEXT,
                arquivado         BOOLEAN,
                data_depositado   DATETIME,
                data_ult_verif    DATETIME,
                data_ult_alt      DATETIME DEFAULT CURRENT_TIMESTAMP,
                estado_detalhado  TEXT
                );""")
    except:
        print(" - Não foi possível criar tabela principal na base de dados.")
        tkMessageBox.FunctionName("Alerta", "Não foi possível criar tabela principal na base de dados.")
        return False
    conn.commit()
    c.close()


def criar_mini_db():
    try:
        os.remove(MINI_DB_PATH) # Apagar ficheiro antigo.
    except OSError as excepcao:
        if excepcao.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured

    conn_mini = sqlite3.connect(MINI_DB_PATH, detect_types=sqlite3.PARSE_DECLTYPES)
    c_mini = conn_mini.cursor()
    try:
        c_mini.execute("""CREATE TABLE IF NOT EXISTS remessas_movel (
            id                INTEGER PRIMARY KEY AUTOINCREMENT,
            destin            TEXT NOT NULL,
            estado            TEXT,
            obj_num           TEXT UNIQUE NOT NULL,
            data_exp          DATETIME,
            valor_cobr        TEXT,
            chq_recebido      TEXT,
            data_depositar    TEXT,
            vols              INTEGER,
            data_ult_verif    DATETIME
            );""")
    except Exception as erro:
            print(erro)
    conn_mini.commit()
    c_mini.close()


    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()

        c.execute("""SELECT destin,
                            estado,
                            obj_num,
                            data_exp,
                            valor_cobr,
                            chq_recebido,
                            data_depositar,
                            vols,
                            data_ult_verif
                     FROM remessas
                     WHERE arquivado = 0;""")

        for row in c:  # Preencher cada linha da tabela com os valores obtidos da base de dados
            destin = row[0]
            estado = row[1]
            obj_num = row[2]
            data_exp = row[3]
            valor_cobr = row[4]
            chq_recebido = row[5]
            data_depositar = row[6]
            vols = row[7]
            data_ult_verif = row[8]
            try:
                conn_mini = sqlite3.connect(MINI_DB_PATH)
                c_mini = conn_mini.cursor()

                c_mini.execute("""INSERT INTO remessas_movel 
                             VALUES ((SELECT max(id) FROM remessas_movel)+1,?,?,?,?,?,?,?,?,?);""", (
                                    destin,
                                    estado,
                                    obj_num,
                                    data_exp,
                                    valor_cobr,
                                    chq_recebido,
                                    data_depositar,
                                    vols,
                                    data_ult_verif
                                    ))
                conn_mini.commit()
                c_mini.close()
            except Exception as erro:
                print("criar_mini_db():", erro)

        conn.commit()
        c.close()

    except Exception as erro:
        print("criar_mini_db():", erro)


    print('Creating archive...')
    try:
        import zlib
        compression = zipfile.ZIP_DEFLATED
    except:
        compression = zipfile.ZIP_STORED

    modes = { zipfile.ZIP_DEFLATED: 'deflated', zipfile.ZIP_STORED: 'stored', }

    zf = zipfile.ZipFile(ZIP_MINI_DB_PATH, mode='w')
    try:
        print('adding sqlite file with compression mode', modes[compression])
        zf.write(MINI_DB_PATH, basename(MINI_DB_PATH), compress_type=compression)
    finally:
        print('closing')
        zf.close()

    try:
        os.remove(MINI_DB_PATH) # Apagar ficheiro.
    except OSError as excepcao:
        if excepcao.errno != errno.ENOENT: # errno.ENOENT = no such file or directory
            raise # re-raise exception if a different error occured



# Adicionar uma nova coluna à base de dados (p/ expansão de funcionalidade)
def db_add_coluna():
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute("""ALTER TABLE remessas 
                 ADD COLUMN estado_detalhado TEXT DEFAULT " ";""")  # linha a ser personalizada antes de usar
    conn.commit()
    c.close()


def db_get_destinatarios():
    """ Obter lista de destinatários já utilizados anteriormente a partir da base de dados """
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""SELECT DISTINCT destin, count(*)
                          FROM remessas  
                          GROUP BY destin
                          ORDER BY count(*) DESC;""")
        dados = cursor.fetchall()
        coluna = 0
        coluna = [linha[coluna] for linha in dados]
        conn.commit()
        cursor.close()
        return coluna
    except:
        print(" - Não foi possível obter a lista de destinatarios da base de dados!")
        return []


def db_update_estado(remessa):
    """
    Atualizar na base de dados estado e estado detalhado para uma remessa
    a partir do seu nº de objeto
    """
    estado = verificar_estado(remessa)
    if estado not in ("- N/A -", "Objeto não encontrado"):
        try:
            estado_detalhado = json.dumps(obter_estado_detalhado2(remessa))
        except:
            return []
        agora = datetime.now()
        try:
            conn = sqlite3.connect(DB_PATH)
            c = conn.cursor()
            c.execute("""UPDATE remessas 
                         SET estado = ?, estado_detalhado = ?, data_ult_verif = ? 
                         WHERE obj_num = ?;""",
                         (estado, estado_detalhado, agora, remessa))
            conn.commit()
            c.close()
            return estado
        except:
            logging.debug(" - Não foi possível atualizar na base de dados o estado da remessa {}!".format(remessa))
            return "Informação indisponível"


def db_del_remessa(remessa):
    """
    Arquivar uma remessa ativa a partir do seu nº de objeto
    """
    agora = datetime.now()

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""UPDATE remessas 
                     SET arquivado = ?, data_ult_alt = ? 
                     WHERE obj_num = ?;""",
                     (1, agora, remessa))
        conn.commit()
        c.close()
    except:
        print(" - Não foi possível arquivar na base de dados a remessa {}!".format(remessa))


def db_restaurar_remessa(remessa):
    """
    Reativar uma remessa arquivada a partir do seu nº de objeto
    """
    agora = datetime.now()

    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        c.execute("""UPDATE remessas 
                     SET arquivado = ?, data_ult_alt = ? 
                     WHERE obj_num = ?;""",
                     (0, agora, remessa))
        conn.commit()
        c.close()
    except:
        print(" - Não foi possível restaurar na base de dados a remessa {}!".format(remessa))


def db_atualizar_tudo():
    """
    Atualizar na base de dados o número de dias desde expedição e os estados
    de todas as remessas ativas (i.e. não arquivadas), exceto as já entregues.
    """
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    c.execute('''SELECT obj_num 
                 FROM remessas 
                 WHERE arquivado = 0 AND estado != "Objeto entregue" AND data_ult_verif <= datetime("now", "-5 minutes");''')
    remessas = c.fetchall()
    for linha in remessas:
        remessa = linha[0]
        estado = verificar_estado(remessa)
        if estado not in ("- N/A -", "Objeto não encontrado"):
            db_update_estado(remessa)
    conn.commit()
    c.close()


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


def obter_estado_detalhado2(remessa: str) -> List[str]:
    """ Verificar extrado de tracking detalhado do objeto nos CTT
    Ex: obter_estado_detalhado("EA746000000PT")
    """
    tracking_code = remessa
    ctt_url = "https://www.ctt.pt/feapl_2/app/open/objectSearch/objectSearch.jspx"
    estado = "- N/A -"

    try:
        response = requests.post(ctt_url, data={'objects': tracking_code}).content
        sopa = BeautifulSoup(response, "html.parser")
        tabela_html = sopa.select("table #details_0 td table")[0]
        tabela_detalhes = []

        for tr in tabela_html.select("tr"):
            linha = [td.text.strip() for td in tr.select('td')]

            if len(linha) == 6:
                linha = linha[1:]

            if len(linha) == 1:
                dia = linha[0].split(',')[0]
                data = linha[0].split(',')[1]
                linha = [ dia, data, '', '', '']
                tabela_detalhes.insert(-1, linha)
            elif len(linha) == 5:
                tabela_detalhes.append(linha)

        estado_detalhado = [linha for linha in tabela_detalhes if linha != []]  # Remover todas as linhas em branco
    except Exception as e:
        print(e)
        print("obter_estado_detalhado2({}) - Não foi possível obter estado " \
              "detalhado a partir da web.".format(tabela_detalhes))
        estado_detalhado = []

    return estado_detalhado


def txt_wrap(texto, chars):
    if len(texto) >= chars:
        wrapped_txt = tw.fill(texto, chars)
        return(wrapped_txt)
    else:
        return texto


# Funções externas (globais à aplicação) ==============================================================================

def abrir_url(remessa):
    url = "http://www.cttexpresso.pt/feapl_2/app/open/cttexpresso/objectSearch/objectSearch.jspx?lang=def&objects={}&showResults=true".format(remessa)
    webbrowser.open(url, new=1, autoraise=True)


def save_and_exit():
    """
    Rotina a ser executada quando o utilizador termina a aplicação
    """
    print(" - Arrumando as coisas e encerrando a aplicação...")
    # Guardar ficheiros e base de dados se aplicável
    sys.exit()


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


def comeca_por_dia_da_semana(texto: str) -> bool:
    dias_da_semana = ("segunda-feira", "terça-feira", "quarta-feira",
                      "quinta-feira", "sexta-feira", "sábado", "domingo",
                      "monday", "tuesday", "wednesday",
                      "thursday", "friday", "saturday", "sunday",
                      )

    if texto.lower().split(", ")[0] in dias_da_semana:
        return True
    else:
        return False

