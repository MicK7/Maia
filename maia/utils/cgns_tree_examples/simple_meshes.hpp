#pragma once 

/* Maillage "one_quad"
Le maillage utilisé est le suivant:
           _      y      j
         /_/|     |_ x   |_ i
        |_|/     /      /
                z      k     
Les ids des noeuds sont les suivants: (ordre fortran, indexé à 0):
           ________________
          /2               /3
         /                /|
        /__|____________ / |
       6|              7|  |
        |  |            |  |
        |               |  |
        |  |            |  |
        |   _ _ _ _ _ _ | _|
        |   0           |  /1
        | /             | /
        |_______________|/
        4               5

Le noeud 0 est en (3.,0.,0.) et le côté du cube est 1.
*/

/* Maillage "six_quads"
Le maillage utilisé est le suivant:
           _ _ _
         /_/_/_/|     y      j
        |_|_|_|/|     |_ x   |_ i
        |_|_|_|/     /      /
                    z      k

Les ids des noeuds sont les suivants (ordre fortran, indexé à 0):
           ________________________________________________
          /8              /9              /10              /11
         /               /               /                /|
        /__|____________/__|____________/__|____________ / |
      20|             21|             22|             23|  |
        |  |            |  |            |  |            |  |
        |       /3/     |      /4/      |       /5/     |  |
        |  |            |  |            |  |            |  |
        |   _ _ _ _ _ _ |   _ _ _ _ _ _ |   _ _ _ _ _ _ | _|
        |   4           |   5           |   6           |  /7
        | /             | /             | /             | /|
        |__|____________|__|____________|__|____________|/ |
      16|             17|             18|             19|  |
        |  |            |  |            |  |            |  |
        |       /0/     |       /1/     |       /2/     |  |
        |  |            |  |            |  |            |  |
        |   _ _ _ _ _ _ |   _ _ _ _ _ _ |   _ _ _ _ _ _ | _|
        |   0           |   1           |   2           |  /3
        | /             | /             | /             | /
        |_______________|_______________|_______________|/
       12              13              14               15

Le noeud 0 est en (0.,0.,0.) et le côté de chaque cube est 1.
*/

/*
vector<int> face_vtx_i = {
   0, 4,16,12,   1, 5,17,13,   2, 6,18,14,   3, 7,19,15,
   4, 8,20,16,   5, 9,21,17,   6,10,22,18,   7,11,23,19
};
vector<int> face_vtx_j = {
   0,12,13, 1,   1,13,14, 2,   2,14,15, 3,
   4,16,17, 5,   5,17,18, 6,   6,18,19, 7,
   8,20,21, 9,   9,21,22,10,  10,22,23,11
};
vector<int> face_vtx_k = {
   0, 1, 5, 4,   1, 2, 6, 5,   2, 3, 7, 6,
   4, 5, 9, 8,   5, 6,10, 9,   6, 7,11,10,
  12,13,17,16,  13,14,18,17,  14,15,19,18,
  16,17,21,20,  17,18,22,21,  18,19,23,22
};
vector<int> face_cell_i = { 
  -1, 0      ,   0, 1      ,   1, 2      ,   2,-1,
  -1, 3      ,   3, 4      ,   4, 5      ,   5,-1
};
vector<int> face_cell_j = { 
  -1, 0      ,  -1, 1      ,  -1, 2,
   0, 3      ,   1, 4      ,   2  5,
   3,-1      ,   4,-1      ,   5,-1
};
vector<int> face_cell_k = { 
  -1, 0      ,  -1, 1      ,  -1, 2      ,  
  -1, 3      ,  -1, 4      ,  -1, 5      ,  
   0,-1      ,   1,-1      ,   2,-1      ,
   3,-1      ,   4,-1      ,   5,-1      ,
};
*/
