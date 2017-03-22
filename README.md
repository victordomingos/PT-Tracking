# PT-Tracking
Aplicação de base de dados para registo e acompanhamento de encomendas da CTT Expresso. Permite automatizar o processo de consulta online do estado de tracking para várias remessas, bem como manter um registo dos pagamentos referentes aos envios à cobrança. As remessas que requerem atenção, devido a atrasos na entrega ou na receção do pagamento correspondente, bem como os cheques cuja data prevista de depósito se esteja a aproximar são destacadas na lista principal, por forma a permitir uma intervenção em conformidade. Adicionalmente, é mantido um histórico facilmente pesquisável de todas as remessas registadas na base de dados.

## Dependências

Esta aplicação foi desenvolvida em Python 3, tkinter e sqlite3, com muitas noites passadas em claro :-) 

Requer adicionalmente os seguintes módulos externos:

  - BeautifulSoup 4.4.1
  - bleach 1.4.2
  - requests 2.9.1
  - terminaltables 2.1.0
  - html5lib 0.999999
  
Foi testada apenas em Mac, no entanto, com pequenas modificações, deverá funcionar sem problemas em Windows ou Linux. Em sistemas operativos antigos, alguns ícones Unicode poderão não aparecer corretamente. Em ambiente Mac, é altamente recomendável usar o ActiveTCL 8.5.18, conforme as notas de lançamento da linguagem Python, de modo a assegurar a compatibilidade e estabilidade do tkinter no OS X.
