# pescarte-ceasa
Este repositório contém uma ferramenta automática de extração de dados da web e de leitura de arquivos PDF. A extração de dados é feita a partir dos boletins de cotações de pescado do site do CEASA/RJ, vinculado à Secretaria de Estado de Agricultura, Pecuária, Pesca e Abastecimento Rio de Janeiro (http://www.ceasa.rj.gov.br/ceasa_portal/).

Para a coleta das cotações diárias dos diferentes tipos de peixes, implementamos um web crawler e a leitura de arquivos PDF. Para esta implementação, selecionamos a linguagem de programação Python e utilizamos as bibliotecas requests, para a coleta de dados do site do Ceasa e pdfplumber, para a leitura e extração dos preços de interesse dos arquivos PDF. Os dados estão armazenados em um banco de dados no PostgreSQL.
