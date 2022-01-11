import psycopg2


def connectDB() :
    
    try: 

        conn = psycopg2.connect(
            host="localhost",
            database="pea_pescarte_cotacoespeixes",
            user="postgres",
            password="21452123888")
        
        return conn

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
    # # finally:
    #     if conn is not None:
    #         conn.close()
    #         print('Database connection closed.')



def isNumeric(txt) :

    for i in range(len(txt)) :
        if not (txt[i].isdigit() or txt[i] == ',') :
            return False
    return True
    

def insereDataBoletimNoBD (conn, data_boletim, link) :
    try :
        # create a cursor
        # cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database - insert into cotacoes:' )

        sql = "SET datestyle to DMY, SQL; "
        sql =  sql + "INSERT INTO cotacoes VALUES ('" + data_boletim + "', '" + link + "') ON CONFLICT (data) DO NOTHING;"

        f = open("/Users/sahudymontenegro/Downloads/cotacoes22102021.csv", "a")
        f.write(data_boletim + ", " + link + "\n")
        f.close()


        # cur.execute(sql) 
        # conn.commit()

        # close the communication with the PostgreSQL
        # cur.close()

    except (Exception ,psycopg2.DatabaseError) as error:
        print(error)
        pass
    # finally:
        # if conn is not None:
        #     conn.close()
        #     print('Database connection closed.')


def formatNumber(n) :
    return n.replace(',','.')  # cast: int()
    
# def formatCotacoes(precos) :
#     campos = ''
#     valores = ''
#     for i, p in list(enumerate(precos)) :
#         if i == 0 and isNumeric(p) :
#             campos += ',minimo'
#             valores += ', ' + formatNumber(p)
#         if i == 1 and isNumeric(p) :
#             campos += ',mais_comum'
#             valores += ', ' + formatNumber(p)
#         if i == 2 and isNumeric(p) :
#             campos += ',maximo'
#             valores += ', ' + formatNumber(p)
#     print(campos)
#     return campos, valores

def formatCotacoes(precos) :
    valores = ''
    for i, p in list(enumerate(precos)) :
        if i == 0 and isNumeric(p) :
            valores += ',' + formatNumber(p)
        elif i== 0 :
            valores += ','
        if i == 1 and isNumeric(p) :
            valores += ',' + formatNumber(p)
        elif i == 1 :
            valores += ','
        if i == 2 and isNumeric(p) :
            valores += ',' + formatNumber(p)
        elif i == 2 :
            valores += ','
    for i in range(3 - valores.count(',')) :
        valores += ','

    return valores


def insereCotacoesNoBD(conn,f, cod_pescado,data_boletim,precos) :
    
    try: 
        valores = formatCotacoes(precos)

        # create a cursor
        # cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database - insert into cotacoes_pescados:' )

        # sql = "SET datestyle to DMY, SQL; "
        sql = "INSERT INTO cotacoes_pescados (cod_pescado, data "
        # sql += campos
        sql += ") VALUES ('" + cod_pescado + "', '" 
        sql += data_boletim + "'" 
        sql += valores + ") ON CONFLICT (cod_pescado,data) DO NOTHING;"
        print(sql)
        # cur.execute(sql) 
        # conn.commit()

        # close the communication with the PostgreSQL
        # cur.close()

        f.write(cod_pescado + ", " + data_boletim + valores + "\n")
        # print("eh aqui? end")

        # return f

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        return -1


def inserePescadoNoBD(conn, cod_pescado,descricao) :
    try :
        # create a cursor
        # cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database - insert into pescados:' )
        sql = "INSERT INTO pescados VALUES ('" + cod_pescado + "', '" + descricao + "')"
        print(sql)
        # cur.execute(sql) 
        # conn.commit()

        # close the communication with the PostgreSQL
        # cur.close()

        f = open("/Users/sahudymontenegro/Downloads/pescados22102021.csv", "a")
        f.write(cod_pescado + ", " + descricao + "\n")
        f.close()

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
        # pass


def buscaPescadoNoCampoBD(conn, cod, desc) :

    try :
        # create a cursor
        cur = conn.cursor()

        # execute a statement
        print('PostgreSQL database - tabela pescados:' ) # + 'SELECT ' + campo + ' FROM pescados')

        sql = "SELECT cod_pescado FROM pescados WHERE cod_pescado = '"
        sql += cod + "' OR descricao = '"
        sql += desc + "'"
        print(sql)
        cur.execute(sql) #+ campo + 

        # display the PostgreSQL database server version
        pescado = cur.fetchone()[0]
        print(pescado)
        # close the communication with the PostgreSQL
        cur.close()

        return pescado

    except (Exception, psycopg2.DatabaseError) as error:
        print(error)
