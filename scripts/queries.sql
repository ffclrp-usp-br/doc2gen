


SELECT * FROM compras_compra AS C INNER JOIN compras_demanda AS D ON (C.id = D.compra_id)


# Itens e Pesquisa de uma determinada compra
SELECT * FROM compras_pesquisa AS P INNER JOIN compras_item AS I ON (P.codigo_contabiliza = I.codigo_contabiliza AND P.codigo_bem = I.codigo_bem) 
WHERE P.compra_id = 4;

# Itens e Pesquisa de um determinado item
SELECT * FROM compras_pesquisa AS P INNER JOIN compras_item AS I ON (P.codigo_contabiliza = I.codigo_contabiliza AND P.codigo_bem = I.codigo_bem) 
WHERE P.id = 103;


# Dada uma compra, apresentar os dados da compra, os itens e as pesquisas associadas a cada item
SELECT * FROM compras_compra AS C INNER JOIN compras_demanda AS D ON (C.id = D.compra_id) INNER JOIN compras_item AS I ON (D.id = I.demanda_id) 
INNER JOIN compras_pesquisa AS P ON (I.codigo_contabiliza = P.codigo_contabiliza AND I.codigo_bem = P.codigo_bem) 
WHERE C.id = 4; 


