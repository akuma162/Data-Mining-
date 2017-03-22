# -*- coding: utf-8 -*-
"""
Created on Sun Nov 20 10:29:32 2016

@author: hina
"""
print ()

import networkx
from operator import itemgetter
import matplotlib.pyplot
import pandas as pd
import numpy as np
import networkx.generators.small

# read the data from the amazon-books.txt;
# populate amazonProducts nested dicitonary;
# key = ASIN; value = MetaData associated with ASIN
fhr = open('./amazon-books.txt', 'r', encoding='utf-8', errors='ignore')
amazonBooks = {}
fhr.readline()
for line in fhr:
    cell = line.split('\t')
    MetaData = {}
    MetaData['Id'] = cell[0].strip() 
    ASIN = cell[1].strip()
    MetaData['Title'] = cell[2].strip()
    MetaData['Categories'] = cell[3].strip()
    MetaData['Group'] = cell[4].strip()
    MetaData['Copurchased'] = cell[5].strip()
    MetaData['SalesRank'] = int(cell[6].strip())
    MetaData['TotalReviews'] = int(cell[7].strip())
    MetaData['AvgRating'] = float(cell[8].strip())
    MetaData['DegreeCentrality'] = int(cell[9].strip())
    MetaData['ClusteringCoeff'] = float(cell[10].strip())
    amazonBooks[ASIN] = MetaData
fhr.close()

# read the data from amazon-books-copurchase.adjlist;
# assign it to copurchaseGraph weighted Graph;
# node = ASIN, edge= copurchase, edge weight = category similarity
fhr=open("amazon-books-copurchase.edgelist", 'rb')
copurchaseGraph=networkx.read_weighted_edgelist(fhr)
fhr.close()
print(copurchaseGraph)
# now let's assume a person is considering buying the following book;
# what else can we recommend to them based on copurchase behavior 
# we've seen from other users?

asin = '0689708076'
#Converting the amazonBooks to a data frame
amazonBooks_dataframe= pd.DataFrame(amazonBooks)
amazonBooks_dataframe[asin]['Group']
#All_asin= list containing all the ASINs in the network
all_asin=list(amazonBooks.keys())
#Getting the ASINs of items copurchased
copurchased_asin=amazonBooks[asin]['Copurchased'].split(" ")
#getting the ASINs of the neighbors in the ego network
ego = networkx.ego_graph(copurchaseGraph, asin, radius=1)
ngbs = ego.neighbors(asin)

#useing island method to get nodes based on weights
threshold = 0.6
egotrim = networkx.Graph()
for n1, n2, e in ego.edges(data=True):
    if e['weight'] >= threshold:
        egotrim.add_edge(n1,n2,e)
island_nodes=egotrim.nodes(data=True)
island_nodes_asin=[]
for i in range(egotrim.number_of_nodes()):
    island_nodes_asin.append(island_nodes[i][0])
        
#Calculating Eigenvector centrality and degree Centrality for each node
asin_eigen = networkx.eigenvector_centrality(copurchaseGraph)
asin_degree=networkx.degree(copurchaseGraph)

#Calculating the eigenVector and degree centrality for island nodes
island_nodes_centrality= {}
for i in range(len(island_nodes_asin)):
    if island_nodes_asin[i]!=asin:
        island_nodes_centrality.update({island_nodes_asin[i]:[asin_degree[island_nodes_asin[i]],
                                                          asin_eigen[island_nodes_asin[i]]]})

#getting degree centrality for Neighbours and filtering nodes with degree 
#centrality less than 80
ngbs_deg={}
for i in range(len(ngbs)):
    if asin_degree[ngbs[i]]>=80:
        ngbs_deg.update({ngbs[i]:asin_degree[ngbs[i]]})
        
#consolidating the similar nodes from island method and neighbour nodes 
#with degree centrality>80
extracted_nodes=[]
for i in list(island_nodes_centrality.keys()):
    if island_nodes_centrality[i][0]>=80:
        extracted_nodes.append(i)
for i in list(ngbs_deg.keys()):
    if i not in extracted_nodes:
        extracted_nodes.append(i)
#Creating a Union of CoPurchased books and the extracted books
one_level_recom=set(extracted_nodes)|set(copurchased_asin)        
#Getting nodes, neighbors and copurchased for second level recommendations
second_level_nodes=[]
second_level_ngbs=[]
second_level_copurchase=[]
#second_level_nodes=nodes most similar to the nodes in one_level_recom
#second_level_ngbs=nodes which are closest to nodes in one_level_recom
for i in one_level_recom:
    ego = networkx.ego_graph(copurchaseGraph, i, radius=1)
    if list(ego.neighbors(i)) not in second_level_ngbs:
        second_level_ngbs.append(ego.neighbors(i))
    threshold = 0.6
    egotrim = networkx.Graph()
    for n1, n2, e in ego.edges(data=True):
        if e['weight'] >= threshold:
            egotrim.add_edge(n1,n2,e)
    island_nodes=egotrim.nodes(data=True)
    for j in range(egotrim.number_of_nodes()):
        second_level_nodes.append(island_nodes[j][0])
#second_level_copurchase=nodes copurchased with the nodes in one_level_recom
    second_level_copurchase.append(amazonBooks[i]['Copurchased'].split(" "))
#x= list for consolidating the asins in second_level_nodes,
#   second_level_ngbs and second_level_copurchase
x=[]
for i in range(len(second_level_copurchase)):
    for j in range(len(second_level_copurchase[i])):
        if second_level_copurchase[i][j] not in x:
            x.append(second_level_copurchase[i][j])
for i in range(len(second_level_ngbs)):
    for j in range(len(second_level_ngbs[i])):
        if second_level_ngbs[i][j] not in x:
            x.append(second_level_ngbs[i][j])    
for i in range(len(second_level_nodes)):
    if second_level_nodes[i] not in x:
        x.append(second_level_nodes[i])

#Getting the EigenVector and Degree Centrality for 2nd level recommendations
#second_level_centrality= Dictionary for containing the degree centrality
# and eigenvector centrality of all the asins in x
second_level_centrality={}
for i in range(len(x)):
    if x[i]!=asin:
        second_level_centrality.update({x[i]:[asin_degree[x[i]],
                                          asin_eigen[x[i]]]})
#rec_keys=Extracting the keys in second_level_centrality
rec_keys=list(second_level_centrality.keys())
#two_level_pot_rec= dictionary for holding the asins which have eigenvector>=1e-06
# and degree centrality >10
two_level_pot_rec={}
for i in range(len(second_level_centrality)):
    key=rec_keys[i]
    if second_level_centrality[key][1]>=1e-06:
        two_level_pot_rec.update({key:second_level_centrality[key]})

for i in range(len(second_level_centrality)):
    key=rec_keys[i]
    if second_level_centrality[key][0]>=10:
        two_level_pot_rec.update({key:second_level_centrality[key]})

two_level_asin=list(two_level_pot_rec.keys())        
#temp_recom= Unifying the recomendations from one_level_recom and two_level_asin
temp_recom=list(set(one_level_recom)|set(two_level_asin))
#recommendation= final recommendations
recommendations={}
#filter the recommended books which have TotalReviews>=100 and AvgRating>=3.5
for i in temp_recom:
    if amazonBooks[i]['TotalReviews']>=100 and amazonBooks[i]['AvgRating']>=3.5:
        recommendations.update({i:[amazonBooks[i]['Title'],
                                amazonBooks[i]['TotalReviews'],
                                 amazonBooks[i]['AvgRating']]})

recom_key=list(recommendations.keys())
#Print the Title, Averge Ratings and Total Reviews for the recommended books
print ("Looking for Recommendations for Customer Purchasing this Book:")
print ("--------------------------------------------------------------")
print("Here are some other Books you make like")
print()
for i in recom_key:
    print("Title:",amazonBooks[i]['Title'],", Average Rating:",amazonBooks[i]['AvgRating'],", ",amazonBooks[i]['TotalReviews'],"Customers have rated this book")

    
    # example code to start looking at metadata associated with this book
#print ("ASIN = ", asin) 
#print ("Title = ", amazonBooks[asin]['Title'])
#print ("SalesRank = ", amazonBooks[asin]['SalesRank'])
#print ("TotalReviews = ", amazonBooks[asin]['TotalReviews'])
#print ("AvgRating = ", amazonBooks[asin]['AvgRating'])
#print ("DegreeCentrality = ", amazonBooks[asin]['DegreeCentrality'])
#print ("ClusteringCoeff = ", amazonBooks[asin]['ClusteringCoeff'])