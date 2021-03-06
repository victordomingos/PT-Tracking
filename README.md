# PT-Tracking
Aplicação de base de dados para registo e acompanhamento de encomendas da CTT Expresso. Permite automatizar o processo de consulta online do estado de tracking para várias remessas, bem como manter um registo dos pagamentos referentes aos envios à cobrança. As remessas que requerem atenção, devido a atrasos na entrega ou na receção do pagamento correspondente, bem como os cheques cuja data prevista de depósito se esteja a aproximar são destacadas na lista principal, por forma a permitir uma intervenção em conformidade. Adicionalmente, é mantido um histórico facilmente pesquisável de todas as remessas registadas na base de dados.

![captura de ecra 2017-04-6 as 18 43 44](https://cloud.githubusercontent.com/assets/18650184/24768034/13b5f4f4-1af9-11e7-8b8c-5ac8411e5469.png)


![captura de ecra 2018-02-23 as 17 45 38](https://user-images.githubusercontent.com/18650184/36608350-785248f6-18c1-11e8-8a95-ef36b0cd10a6.png)


## Dependências

Esta aplicação foi desenvolvida em Python 3, tkinter e sqlite3, com muitas noites passadas em claro :-) 

Requer adicionalmente os seguintes módulos externos:

  - BeautifulSoup 4.4.1
  - bleach 1.4.2
  - requests 2.9.1
  - terminaltables 2.1.0
  - html5lib 0.999999
  - Pmw 2.0.1

Para instalar facilmente estas dependências, pode ser utilizado o seguinte comando:

`pip3.6 install -r requirements.txt`

Foi testada apenas em Mac, no entanto, com pequenas modificações, deverá funcionar sem problemas em Windows ou Linux. Em sistemas operativos antigos, alguns ícones Unicode poderão não aparecer corretamente. Em ambiente Mac, é altamente recomendável usar o ActiveTCL 8.5.18, conforme as notas de lançamento da linguagem Python, de modo a assegurar a compatibilidade e estabilidade do tkinter no OS X.


## Como usar

Para iniciar a aplicação, basta executar o ficheiro `ctt_tracking/ctt_tracking.py` com o interpretador Python 3.6 ou superior.

## Versão para iPhone e iPad

Na pasta `ctt_tracking_iPhone/` encontra-se uma versão adaptada para iPhone, que corre em ambiente Pythonista 3. Requer alguma configuração prévia, incluindo instalação de dependências. Esta é uma versão bastante simplificada, apresentando apenas as remessas em curso, obtidas a partir de uma mini-base de dados gerada pela aplicação principal de desktop, com uma representação iconográfica dos estados de entrega e de receção de valores de cobrança. Deve por isso ser encarada como uma versao alpha.

<p align="center">
<img style="border:1px solid grey" src="https://cloud.githubusercontent.com/assets/18650184/24814278/f2faddee-1bc8-11e7-99a2-2535f62e6f58.png" width="320">
</p>
