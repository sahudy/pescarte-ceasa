#  from https://stackoverflow.com/questions/3533528/python-web-crawlers-and-getting-html-source-code/49294529

from urllib import request
import pdfplumber
import requests

import re
import datetime

import bd_req as bd



global_boletim_sem_cotacoes = 0 # boletim nao contem cotacoes
cont_boletim_sem_cotacoes = 0 # conta boletins q nenhum dos pescados tem preço "SEM COTAÇÃO"
cont_ignored = 0 # links corrompidos
cont_sardinha_verdadeira = 0 # numero de vezes que foi lido SARDINHA VERDADEIRA ao inves de VERDEIRA
cont_troca_sardinhas = 0 # numero de vezes que foram trocadis os codigos SARDINHA VERDEIRA - SARV vs. LAGE - SARL
cont_arquivos_somenteleitura = 0 # numero de vezes que um arquivo PDF (boletim) nao conseguiu ser ido
cont_boletim_com_cotacoes = 0 # numero de boletins lidos que contem cotacoes de pescados
cont_boletim_lidos = 0 # numero de boletins lidos 
cont_boletim_sem_pescados = 0 # numero de boletins lidos que nao tem pagina publicada com listagem de pescados


def dataValida(data) :

    data = data.replace('\\', "/")
    separador = ['/','.','-']
    
    for sep in separador:
        date_format = '%d' + sep + '%m' + sep + '%Y'

        try:
            datetime.datetime.strptime(data, date_format)
            return True
        except ValueError:
            pass
    return False


def crawl_pages():
    # cont = 0
    pdf_links = []
    try: 
        for i in range(111,0,-1) : # 111 paginas de arquivos de cotacoes no CEASA 
            # print('Pagina: '+ str(i))
            response = request.urlopen("http://www.ceasa.rj.gov.br/ceasa_portal/view/ListarCotacoes.asp?pagina=" + str(i))
            # set the correct charset below
            page_source = response.read().decode('utf-8')
            pos = 0
            kw_main_tag = '<div class="cotacao">'
            kw_link_tag = '<a target="_blank" href='
            kw_link_endtag = '>Download</a>'

            while True:
                pos = page_source.find(kw_main_tag,pos)

                if pos == -1 :  # 
                    break
                else :
                    pos = page_source.find(kw_link_tag,pos)
                    pos_end = page_source.find(kw_link_endtag,pos)
                    link = page_source[pos+len(kw_link_tag)+1:pos_end-1]
                    pdf_links.append(link)

    except (Exception) as error:  # , urllib.error.URLError
        print(error)

    print(len(pdf_links))
    return pdf_links


def getFileName(link) :

    index = link.lower().find('boletim')
    if (index == -1) :
        return 'arquivos/boletim___' + link[len(link)-35:len(link)]
    return 'arquivos/' + link[index:len(link)].lower()



def download_pdf(link):

    # obtain filename by splitting url and getting
    # last string
    
    file_name = getFileName(link) #link.split('/')[-1]

    print( "Downloading file:%s"%file_name)

    # create response object
    r = requests.get(link, stream = True)

    # download started
    with open(file_name, 'wb') as f:
        for chunk in r.iter_content(chunk_size = 1024*1024):
            if chunk:
                f.write(chunk)

    print( "%s downloaded!\n"%file_name )

    return file_name


def getDescricao(tokens, end_pos) :

    descricao = ''
    if end_pos == 0 : # pelo menos dois elementos
        return tokens[end_pos], ''
    # end_pos >= 1
    for i in range(end_pos):        
        descricao += tokens[i]
        descricao += ' '
    if len(tokens[end_pos].strip()) > 4 or tokens[end_pos].strip() == 'ROSA': # problemas para pegar CONGRO ROSA
        descricao += tokens[end_pos].strip()
        cod = ''
    else :
        cod = tokens[end_pos].strip()

    descricao = descricao.strip()
 # caso da SARDINHA "VERDADEIRA" => SARL
    if descricao == 'SARDINHA VERDEIRA' :
        descricao = 'SARDINHA VERDADEIRA'
        global cont_sardinha_verdadeira
        cont_sardinha_verdadeira += 1
    if cod == 'SARL' and descricao == 'SARDINHA VERDADEIRA' :
        cod = 'SARV'
        # a troca conta uma vez so, preferi contar no 2o caso a seguir
        # global cont_troca_sardinhas
        # cont_troca_sardinhas += 1
    if cod == 'SARV' and descricao == 'SARDINHA LAGE' :
        cod = 'SARL'
        global cont_troca_sardinhas
        cont_troca_sardinhas += 1

    return descricao, cod


def removeToken(lista, token) :

    while True :
        try : 
            lista.remove(token)
        except :
            break

    return lista


def isNumericList(list) :

    for i in range(len(list)) :
        if bd.isNumeric(list[i]) :
            return True
    return False


def splitPrecos(tokens, ngram=2) : # ngram = numero de tokens consecutivos que representam uma unidade (ex: sem + cotacao)
# testes
# print(splitPrecos(['sem','cotacao', '1', '2']))
# print(splitPrecos(['sem','cotacao', '1', 'sem','cotacao']))
# print(splitPrecos([ '1', 'sem','cotacao']))
# print(splitPrecos(['1', 'sem','cotacao', 'sem','cotacao']))
# print(splitPrecos(['sem', 'cotacao', 'sem','cotacao','1']))
# print(splitPrecos(['sem', 'cotacao', 'sem','cotacao']))
# print(splitPrecos(['sem','cotacao']))
# print(splitPrecos(['1', 'sem']))
# print(splitPrecos(['1', '2']))
# print(splitPrecos(['sem','cotacao','1']))
# print(splitPrecos(['1','sem','cotacao']))
# print(splitPrecos(['sem']))
# print(splitPrecos(['1']))

    result = tokens.copy()
    # print('=========')
    # print(tokens)
    aux = []
    # add as posicoes com valores nao numericos
    for t, token in reversed(list(enumerate(tokens))): # em reverso permite apagar com o .pop os ultimos elementos primeiro, assim nao influenciando na ordem das posicoes na lista
        if not bd.isNumeric(token) : # tokens[t]
            result[t] = 'SEM COTACAO' 
            aux.append(t)    # add a posicao a um vetor auxiliar

    # print(aux)
    # busca posicoes consecutivas que indicam um mesmo texto particionado pelo split em varios elementos da lista para "juntar" como um mesmo item da lista (na vdd apagando a partir da segunda palavra), o conteudo em si do que esta escrito nao interessa
    t = 0
    num_repeticoes = 0
    while t < len(aux) -1 : # tem posicoes consecutivas armazenadas, isto verifica tokens que foram separados como SEM COTACAO ou SEM INFORMACAO
        while t < len(aux) -1 and aux[t] - aux[t+1] == 1 and num_repeticoes < ngram :
            num_repeticoes += 1
            t += 1
    
        if num_repeticoes > 0 :
            for i in reversed(range(num_repeticoes)) :
                result.pop(aux[t-i]) # deixa apenas uma ocorrencia sem as repeticoes (fica o ultimo elemento da sequencia)
            num_repeticoes = 0
        t += 1

    return result


def getPrecos(tokens, ini_pos) :

    if tokens.count("R$") > 0 :
        tokens = removeToken(tokens,"R$")

    precos = splitPrecos(tokens[ini_pos:]) 

    if not isNumericList(precos) :
        return -1
    
    return precos


def uppercase (tokens) :

    for i in range(len(tokens)) :
        tokens[i] = tokens[i].upper()

    return tokens

# def buscaPescado(lista,item) :

#     # print(item)
#     for l in lista :
#         # print(l[0])
#         if item == l[0] :
#             return True
#     raise ValueError

def setPescado(conn, cod_pescado,descricao_pescado) :

    pescado = bd.buscaPescadoNoCampoBD(conn,cod_pescado,descricao_pescado)
    # pescados_lista.index(cod_pescado)
    # buscaPescado(pescados_lista,cod_pescado)

    if pescado == None :
        if cod_pescado != '' :
            bd.inserePescadoNoBD(conn,cod_pescado,descricao_pescado)
        else :
            print('pescado sem codigo, nao da para inserir no bd')
    
    return pescado


def insertTokens(conn, f_cotacoes, tokens, data_boletim) :

    try: 
        tokens = uppercase(tokens)
        pos_embalagem = tokens.index('KG')
        if pos_embalagem <= 0 :
            print('Unidade de medida nao eh KG :( ou nao tem descricao do pescado')
            return
        else:
            print('=================')
            descricao, cod_pescado = getDescricao(tokens, pos_embalagem-1)
            # print(descricao)
            # print(cod_pescado)

            cod_pescado = setPescado(conn,cod_pescado,descricao)
            precos = getPrecos(tokens, pos_embalagem +1)
            
            # print(descricao)
            # print('Depois do SetPescado()' )
            # print(cod_pescado)

            if cod_pescado == None:
                # print('tokens com erros')
                print(tokens)
                return

            print('Código: ' + cod_pescado)
            print('Descrição: ' + descricao)
            print('Preços: ')

            if precos == -1 : 
                print('SEM COTAÇÃO')
            else:
                print(precos)
                global global_boletim_sem_cotacoes
                global_boletim_sem_cotacoes = 1 # contem pelo menos 1 cotacao de pescado
                # return 
                bd.insereCotacoesNoBD(conn,f_cotacoes, cod_pescado,data_boletim,precos)

    except (Exception) as error: # , urllib.error.URLError
        print(error)

        
def formatData(data) :

    data = data.replace('\\','/')
    data = data.replace('.','/')
    data = data.replace('-','/')

    return data


def encontraData(pagina,pos_fim) :

    # dois formatos de data encontrados nos PDF dd/mm/yyyy ou dd.mm.yyyy
    pattern = re.compile("\d+/\d+/\d+")
    match = pattern.search(pagina, 0 , pos_fim)
    if match:
        return formatData(match.group(0))
    else :
        pattern = re.compile("\d+.\d+.\d+")
        match = pattern.search(pagina, 0 , pos_fim)
        if match:
            return formatData(match.group(0))
        else :
            return None


def getTokens(conn, pescados, data_boletim) :

    try:
        f_cotacoes = open("/Users/sahudymontenegro/Downloads/cotacoes_pescados22102021.csv", "a")

        pos = pescados.lower().find('pescados')
        end_kws = ['FONTE:','SEDRAP', 'CEASA', 'DIRTEC']

        if pos == -1 :
            print('PAGINA NAO DE PESCADOS \n')
            return -1

        while (pos > 0):
            pos = pescados.find('\n',pos)
            pos += 1
            pos_end = pescados.find("\n",pos)

            linha = pescados[pos:pos_end].strip()
            # CASO A SER RESOLVIDO: 
            # print(splitPrecos(['6,00', '8', ',', '0', '0', '8', ',', '0', '0']))
            # print(splitPrecos(['6,00', '7', ',', '0', '0', '8', ',', '0', '0']))
            # em alguns poucos casos ao fazer o split da string da tabela em tokens,
            # ele separa da forma acima os numeros, ao inves de: ['7,00', '8,00', '8,50']
            # dai fica: INSERT INTO cotacoes_pescados (cod_pescado, data ) VALUES ('CMRU', '22/06/2017' ,6.00,8,.) 
            # buscar por ',.' no arquivo de messages para localizar ocorrencias
            # solucoes: ou ver pq o split se comporta dessa maneira nesses casos
            #           ou melhorar a splitPrecos() e isNumeric() para atender esses casos
            tokens = linha.split() 

            if len(tokens) == 0 :
                print('FIM da PAGINA: ')
                print('SEM RODAPE NA PAGINA')
                break         
            else:
                if end_kws.count(tokens[0]) > 0:
                   print('FIM da PAGINA: ')
                   print(tokens)
                   break
                # f_cotacoes = 
                insertTokens(conn, f_cotacoes, tokens, data_boletim)
        f_cotacoes.close()

    except Exception as error:
        print(error)
        print('ALGUMA KW DA BUSCA NA PAGINA NO FOI ACHADA!')
        f_cotacoes.close()

    print('\n')
    return 1  


def readPDF(pdf_links):

    conn = bd.connectDB()
    for link in pdf_links:

        data_boletim = None
        try: 
            file_name = download_pdf(link)
            flag = -1 # para marcar quando a pagina inicial dos pescados nao é a prevista (padrao, q eh pag 12)
            with pdfplumber.open(file_name) as pdf:

                global global_boletim_sem_cotacoes 
                global_boletim_sem_cotacoes = 0 # inicializa supondo que o boletim nao tem cotacoes de pescados 
               # para achar data na primeira pagina
                page1 = pdf.pages[0] 
                page1_dados = page1.extract_text().strip()
                data_boletim = encontraData(page1_dados,500)
                if data_boletim == None :
                    print('SEM DATA NO PDF') # MESMO CASO NA PRATICA! VALE o contador cont_somente_leitura 
                                             # na teoria poderia ter um boletim sem data na primeira pagina
                    flag = -3
                else :  
                    print(data_boletim)  
                    bd.insereDataBoletimNoBD(conn, data_boletim, link)

                    global cont_boletim_lidos
                    cont_boletim_lidos += 1

                    # tabelas de pescados
                    pag_ini = 11 # pagina 12 
                    while pag_ini < len(pdf.pages) and flag != 1:
                        page12 = pdf.pages[pag_ini]
                        page12_dados = page12.extract_text().strip()
                        print('***** Página 12 *****')
                        cod = getTokens(conn, page12_dados, data_boletim)
                        if cod == -1: # sem tokens retornados - marca que a página de pescados nao conseguiu ser lida
                            pag_ini += 1
                        else : 
                            flag = 1 # acima entramos na pagina dos pescados
                            page13 = pdf.pages[pag_ini +1]
                            page13_dados = page13.extract_text().strip()
                            print('***** Página 13 *****')
                            cod = getTokens(conn, page13_dados, data_boletim)

                            if global_boletim_sem_cotacoes == 0:
                                print('boletim sem cotacoes de pescados (tabela) ' + data_boletim + '\n\n')
                                global cont_boletim_sem_cotacoes
                                cont_boletim_sem_cotacoes += 1
                            else :
                                global cont_boletim_com_cotacoes # neste ponto li pelo menos uma pagina de pescados
                                cont_boletim_com_cotacoes += 1

                            if cod == -1 :
                                flag = -2 # marca que a segunda página de pescados nao conseguiu ser lida
                            break


                if flag == -1 : # nunca conseguiu ler uma pagina inicial de pescados
                    print ('NAO DEU PARA LER DADOS DE PESCADOS DESTE ARQUIVO\n')
                    print(link)
                    global cont_boletim_sem_pescados
                    cont_boletim_sem_pescados += 1
                elif flag == -2 : # teve uma pagina de pescados apenas no PDF (pelos testes este caso nao aconteceu)
                    print ('NAO DEU PARA UMA SEGUNDA PAGINA DESTE ARQUIVO\n')
                    print(link)
                elif flag == -3 : # nao conseguiu ler o arquivo
                    print ('NAO DEU PARA LER A DATA NO PDF OU O PDF É IMAGEM\n')
                    print(link + '\n\n')
                    global cont_arquivos_somenteleitura 
                    cont_arquivos_somenteleitura += 1
                # else conseguiu ler as paginas de pescado

        except :
            print("Exception ignored\n")
            print(link + '\n\n')
            global cont_ignored
            cont_ignored += 1
            pass
    if conn is not None:
        conn.close()
        print('Database connection closed.')






#  main 
# pdf_links = ['http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=2663&nomeArquivo=boletim diario de precos 04 08 2021.pdf','http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=23&nomeArquivo=boletim diario de precos 04 07 2012 (8).pdf','http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=50&nomeArquivo=boletim%20diario%20de%20precos%2008%2008%202012%20copia.pdf'];

# pdf_links = ['http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=49&nomeArquivo=boletim%20diario%20de%20precos%2007%2008%202012.pdf', 'http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=50&nomeArquivo=boletim%20diario%20de%20precos%2008%2008%202012%20copia.pdf']
# pdf_links = [
#     # 'http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=209&nomeArquivo=boletim%20diario%20de%20precos%2009%2004%202013.pdf',
#     ]
# pdf_links = ['http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=2092&nomeArquivo=Boletim diario de precos  13 01 2020.pdf', 'http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=1255&nomeArquivo=Boletim%20diario%20de%20precos%20%2025%2004%202017.pdf']
# 
# pdf_links = ['http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=1232&nomeArquivo=Boletim diuario de precos  21 03 2017.pdf']
# pdf_links = ['http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=33&nomeArquivo=boletim diario de precos 16 05 2012.pdf']
# pdf_links = ['http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=90&nomeArquivo=boletim%20diario%20de%20precos%2004%2010%202012.pdf']
#     # 'http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=1311&nomeArquivo=Boletim%20diario%20de%20precos%20%2010%2007%202017.pdf']

# pdf_links = ['http://arquivos.proderj.rj.gov.br/ceasa1_imagens/ceasa_portal/view/download.asp?sessao=cotacao&id=734&nomeArquivo=boletim%20diario%20de%20precos%2030%2003%202015.pdf']

pdf_links = crawl_pages()
readPDF(pdf_links)

print("Numero de links extraidos da CEASA: ")
print(len(pdf_links))

print("Numero de links de boletins sem acesso (link corrompido): ")
print(cont_ignored)
print("Numero de arquivos que nao conseguiram ser lidos (de somente leitura): ")
print(cont_arquivos_somenteleitura)
print("Numero de arquivos que  conseguiram ser lidos (consegui ler a data pelo menos - nao eh de somente leitura): ")
print(cont_boletim_lidos)
print("Numero de boletins com cotacoes (ou pelo menos uma cotacao): ")
print(cont_boletim_com_cotacoes)
print("Numero de boletins sem cotacoes na tabela completa: ")
print(cont_boletim_sem_cotacoes)
print("Numero de boletins que nao contem listagem dos pescados: ")
print(cont_boletim_sem_pescados)

print("Numero de vezes que SARDINHA VERDADEIRA foi trocado por SARDINHA VERDEIRA: ")
print(cont_sardinha_verdadeira)
print("Numero de vezes que trocou codigos entre SARV E SARL: ")  # (divida por 2): ")
print(cont_troca_sardinhas)


