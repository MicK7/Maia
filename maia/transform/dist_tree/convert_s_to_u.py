#coding:utf-8
import Converter.Internal as I
import numpy              as np
import copy

import Pypdm.Pypdm as PDM

from maia.distribution       import distribution_function           as MDIDF
from maia.cgns_io.hdf_filter import range_to_slab                   as HFR2S

###############################################################################
def convert_ijk_to_index(i,j,k,Ni,Nj,Nk):
  """
  Convert (i,j,k) indices from structured grid to unstructured index
  This fonction allows (i,j,k) that defines node or cell
  Ni is the number of nodes or cells in the direction i
  Nj is the number of nodes or cells in the direction j
  Nk is the number of nodes or cells in the direction k
  WARNING : (i,j,k) begins at (1,1,1)
  WARNING : index begins at 1
  """
  return(i+(j-1)*Ni+(k-1)*Ni*Nj)
###############################################################################

###############################################################################
def convert_ijk_to_faceIndices(i,j,k,nCell,nVtx,nbFacesi,nbFacesj):
  # WARNING : (i,j,k) begins at (1,1,1)
  # WARNING : faces begin at 1
  # nCell = [Ni,Nj,Nk]
  # nVtx  = [Ni,Nj,Nk]
  # nbFacesi = nVtx[0]*nCell[1]*nCell[2]
  # nbFacesj = nVtx[1]*nCell[0]*nCell[2]
  fi = convert_ijk_to_faceiIndex(i,j,k,nCell,nVtx)
  fj = convert_ijk_to_facejIndex(i,j,k,nCell,nVtx,nbFacesi)
  fk = convert_ijk_to_facekIndex(i,j,k,nCell,nVtx,nbFacesi,nbFacesj)
  return(fi,fj,fk)
###############################################################################

###############################################################################
def convert_ijk_to_faceiIndex(i,j,k,nCell,nVtx):
  # WARNING : (i,j,k) begins at (1,1,1)
  # WARNING : faces begin at 1
  # nCell = [Ni,Nj,Nk]
  # nVtx  = [Ni,Nj,Nk]
  fi = i + (j-1)*nVtx[0]  + (k-1)*nVtx[0]*nCell[1]
  return(fi)
###############################################################################

###############################################################################
def convert_ijk_to_facejIndex(i,j,k,nCell,nVtx,nbFacesi):
  # WARNING : (i,j,k) begins at (1,1,1)
  # WARNING : faces begin at 1
  # nCell = [Ni,Nj,Nk]
  # nVtx  = [Ni,Nj,Nk]
  # nbFacesi = nVtx[0]*nCell[1]*nCell[2]
  fj = nbFacesi + i + (j-1)*nCell[0] + (k-1)*nVtx[1]*nCell[0]
  return(fj)
###############################################################################

###############################################################################
def convert_ijk_to_facekIndex(i,j,k,nCell,nVtx,nbFacesi,nbFacesj):
  # WARNING : (i,j,k) begins at (1,1,1)
  # WARNING : faces begin at 1
  # nCell = [Ni,Nj,Nk]
  # nVtx  = [Ni,Nj,Nk]
  # nbFacesi = nVtx[0]*nCell[1]*nCell[2]
  # nbFacesj = nVtx[1]*nCell[0]*nCell[2]
  fk = nbFacesj + nbFacesi + i + (j-1)*nCell[0] + (k-1)*nCell[0]*nCell[1]
  return(fk)
###############################################################################

###############################################################################
def compute_fi_from_ijk(i,j,k):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (i,j  ,k  )
  n2 = (i,j+1,k  )
  n3 = (i,j+1,k+1)
  n4 = (i,j  ,k+1)
  # Neighbour cells of the face
  left  = (i-1,j,k)
  right = (i  ,j,k)
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def compute_fi_from_imaxjk(imax,j,k):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (imax,j  ,k  )
  n2 = (imax,j+1,k  )
  n3 = (imax,j+1,k+1)
  n4 = (imax,j  ,k+1)
  # Neighbour cell of the face
  left  = (imax-1,j,k)
  right = 0
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def compute_fi_from_iminjk(imin,j,k):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (imin,j  ,k  )
  n2 = (imin,j  ,k+1)
  n3 = (imin,j+1,k+1)
  n4 = (imin,j+1,k  )
  # Neighbour cell of the face
  left  = (imin,j,k)
  right = 0
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def compute_fj_from_ijk(i,j,k):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (i  ,j,k  )
  n2 = (i  ,j,k+1)
  n3 = (i+1,j,k+1)
  n4 = (i+1,j,k  )
  # Neighbour cells of the face
  left  = (i,j-1,k)
  right = (i,j  ,k)
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def compute_fj_from_ijmaxk(i,jmax,k):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (i  ,jmax,k  )
  n2 = (i  ,jmax,k+1)
  n3 = (i+1,jmax,k+1)
  n4 = (i+1,jmax,k  )
  # Neighbour cell of the face
  left  = (i,jmax-1,k)
  right = 0
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def compute_fj_from_ijmink(i,jmin,k):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (i  ,jmin,k  )
  n2 = (i+1,jmin,k  )
  n3 = (i+1,jmin,k+1)
  n4 = (i  ,jmin,k+1)
  # Neighbour cell of the face
  left  = (i,jmin,k)
  right = 0
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def compute_fk_from_ijk(i,j,k):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (i  ,j  ,k)
  n2 = (i+1,j  ,k)
  n3 = (i+1,j+1,k)
  n4 = (i  ,j+1,k)
  # Neighbour cells of the face
  left  = (i,j,k  )
  right = (i,j,k-1)
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def compute_fk_from_ijkmax(i,j,kmax):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (i  ,j  ,kmax)
  n2 = (i+1,j  ,kmax)
  n3 = (i+1,j+1,kmax)
  n4 = (i  ,j+1,kmax)
  # Neighbour cell of the face
  left  = (i,j,kmax-1)
  right = 0
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def compute_fk_from_ijkmin(i,j,kmin):
  # WARNING : (i,j,k) begins at (1,1,1)
  # Nodes of the face
  n1 = (i  ,j  ,kmin)
  n2 = (i+1,j  ,kmin)
  n3 = (i+1,j+1,kmin)
  n4 = (i  ,j+1,kmin)
  # Neighbour cell of the face
  left  = (i,j,kmin)
  right = 0
  return(n1,n2,n3,n4,left,right)
###############################################################################

###############################################################################
def fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                     leftijk,rightijk,nVtx,nCell,
                                     faceNgon,faceLeftCell,faceRightCell):
  # WARNING : (i,j,k) begins at (1,1,1)
  n1 = convert_ijk_to_index(n1ijk[0],n1ijk[1],n1ijk[2],nVtx[0],nVtx[1],nVtx[2])
  n2 = convert_ijk_to_index(n2ijk[0],n2ijk[1],n2ijk[2],nVtx[0],nVtx[1],nVtx[2])
  n3 = convert_ijk_to_index(n3ijk[0],n3ijk[1],n3ijk[2],nVtx[0],nVtx[1],nVtx[2])
  n4 = convert_ijk_to_index(n4ijk[0],n4ijk[1],n4ijk[2],nVtx[0],nVtx[1],nVtx[2])
  faceNgon[4*counter:4*(counter+1)] = [n1,n2,n3,n4]
  left = convert_ijk_to_index(leftijk[0],leftijk[1],leftijk[2],nCell[0],nCell[1],nCell[2])
  faceLeftCell[counter] = left
  if rightijk == 0:
    right = 0
  else:
    right = convert_ijk_to_index(rightijk[0],rightijk[1],rightijk[2],nCell[0],nCell[1],nCell[2])
  faceRightCell[counter] = right
    
###############################################################################

###############################################################################
def compute_nbFacesAllSlabsPerZone(slabListVtx,nVtx):
  nbFacesAllSlabsPerRank = 0
  for slabVtx in slabListVtx:
    nbFacesPerSlab = 0
    iS,iE, jS,jE, kS,kE = [item+1 for bounds in slabVtx for item in bounds]
    # print(iS,iE,jS,jE,kS,kE)
    # print([i for i in range(iS,iE)])
    if iE == nVtx[0]+1:
      supI = iE-1
    else:
      supI = iE    
    if jE == nVtx[1]+1:
      supJ = jE-1
    else:
      supJ = jE
    if kE == nVtx[2]+1:
      supK = kE-1
    else:
      supK = kE
    
    #> iMin faces treatment
    if iS == 1:
      infI = iS+1
      nbFacesPerSlab += (supJ-jS)*(supK-kS)
    else:
      infI = iS
      
    #> jMin faces treatment
    if jS == 1:
      infJ = jS+1
      nbFacesPerSlab += (supI-iS)*(supK-kS)
    else:
      infJ = jS
      
    #> kMin faces treatment
    if kS == 1:
      infK = kS+1
      nbFacesPerSlab += (supI-iS)*(supJ-jS)
    else:
      infK = kS
    
    #> interior faces treatment with only interior edges
    nbFacesPerSlab += 3*(supI-infI)*(supJ-infJ)*(supK-infK)
    
    #> interior faces treatment with at least one exterior edge
    if iS == 1:
      nbFacesPerSlab += (supJ-infJ)*(supK-kS)
      nbFacesPerSlab += (supK-infK)*(supJ-jS)
    if jS == 1:
      nbFacesPerSlab += (supI-infI)*(supK-kS)
      nbFacesPerSlab += (supK-infK)*(supI-infI)
    if kS == 1:
      nbFacesPerSlab += (supI-infI)*(supJ-infJ)
      nbFacesPerSlab += (supJ-infJ)*(supI-infI)
    
    #> iMax faces treatment
    if iE == nVtx[0]+1:
      nbFacesPerSlab += (supJ-jS)*(supK-kS)
          
    #> jMax faces treatment
    if jE == nVtx[1]+1:
      nbFacesPerSlab += (supI-iS)*(supK-kS)
          
    #> kMax faces treatment
    if kE == nVtx[2]+1:
      nbFacesPerSlab += (supI-iS)*(supJ-jS)
      
    nbFacesAllSlabsPerRank += nbFacesPerSlab  
  
  return nbFacesAllSlabsPerRank

###############################################################################

###############################################################################
def compute_faceNumber_faceNgon_leftCell_rightCell_forAllFaces(slabListVtx,nVtx,nCell,
                                                               nbFacesi,nbFacesj,
                                                               faceNumber,faceNgon,
                                                               faceLeftCell,faceRightCell):
  counter = 0
  for slabVtx in slabListVtx:
    iS,iE, jS,jE, kS,kE = [item+1 for bounds in slabVtx for item in bounds]
    # print(iS,iE,jS,jE,kS,kE)

    if iE == nVtx[0]+1:
      supI = iE-1
    else:
      supI = iE    
    if jE == nVtx[1]+1:
      supJ = jE-1
    else:
      supJ = jE
    if kE == nVtx[2]+1:
      supK = kE-1
    else:
      supK = kE
      
    #> iMin faces treatment
    if iS == 1:
      infI = iS+1
      for j in range(jS,supJ):
        for k in range(kS,supK):
          faceNumber[counter] = convert_ijk_to_faceiIndex(1,j,k,nCell,nVtx)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fi_from_iminjk(1,j,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
    else:
      infI = iS
      
    #> jMin faces treatment
    if jS == 1:
      infJ = jS+1
      for i in range(iS,supI):
        for k in range(kS,supK):
          faceNumber[counter] = convert_ijk_to_facejIndex(i,1,k,nCell,nVtx,nbFacesi)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fj_from_ijmink(i,1,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
    else:
      infJ = jS
      
    #> kMin faces treatment
    if kS == 1:
      infK = kS+1
      for i in range(iS,supI):
        for j in range(jS,supJ):
          faceNumber[counter] = convert_ijk_to_facekIndex(i,j,1,nCell,nVtx,nbFacesi,nbFacesj)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fk_from_ijkmin(i,j,1)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
    else:
      infK = kS
    
    #> interior faces treatment with only interior edges
    for i in range(infI,supI):
      for j in range(infJ,supJ):
        for k in range(infK, supK):
          (fi,fj,fk) = convert_ijk_to_faceIndices(i,j,k,nCell,nVtx,nbFacesi,nbFacesj)
          #>> i face treatment
          faceNumber[counter] = fi
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fi_from_ijk(i,j,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
          #>> j face treatment
          faceNumber[counter] = fj
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fj_from_ijk(i,j,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
          #>> i face treatment
          faceNumber[counter] = fk
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fk_from_ijk(i,j,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
    
    #> interior faces treatment with at least one exterior edge
    #>> i=1 edge
    if iS == 1:
      for j in range(infJ,supJ):
        for k in range(kS,supK):
          faceNumber[counter] = convert_ijk_to_facejIndex(1,j,k,nCell,nVtx,nbFacesi)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fj_from_ijk(1,j,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
      for k in range(infK,supK):
        for j in range(jS,supJ):
          faceNumber[counter] = convert_ijk_to_facekIndex(1,j,k,nCell,nVtx,nbFacesi,nbFacesj)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fk_from_ijk(1,j,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
    #>> j=1 edge
    if jS == 1:
      for i in range(infI,supI):
        for k in range(kS,supK):
          faceNumber[counter] = convert_ijk_to_faceiIndex(i,1,k,nCell,nVtx)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fi_from_ijk(i,1,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
      for k in range(infK,supK):
        for i in range(infI,supI):
          faceNumber[counter] = convert_ijk_to_facekIndex(i,1,k,nCell,nVtx,nbFacesi,nbFacesj)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fk_from_ijk(i,1,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
    #>> k=1 edge
    if kS == 1:
      for j in range(infJ,supJ):
        for i in range(infI,supI):
          faceNumber[counter] = convert_ijk_to_facejIndex(i,j,1,nCell,nVtx,nbFacesi)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fj_from_ijk(i,j,1)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
      for i in range(infI,supI):
        for j in range(infJ,supJ):
          faceNumber[counter] = convert_ijk_to_faceiIndex(i,j,1,nCell,nVtx)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fi_from_ijk(i,j,1)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1

    #> iMax faces treatment
    if iE == nVtx[0]+1:
      for j in range(jS,supJ):
        for k in range(kS,supK):
          faceNumber[counter] = convert_ijk_to_faceiIndex(nVtx[0],j,k,nCell,nVtx)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fi_from_imaxjk(nVtx[0],j,k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
          
    #> jMax faces treatment
    if jE == nVtx[1]+1:
      for i in range(iS,supI):
        for k in range(kS,supK):
          faceNumber[counter] = convert_ijk_to_facejIndex(i,nVtx[1],k,nCell,nVtx,nbFacesi)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fj_from_ijmaxk(i,nVtx[1],k)
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
          
    #> kMax faces treatment
    if kE == nVtx[2]+1:
      for i in range(iS,supI):
        for j in range(jS,supJ):
          faceNumber[counter] = convert_ijk_to_facekIndex(i,j,nVtx[2],nCell,nVtx,nbFacesi,nbFacesj)
          (n1ijk,n2ijk,n3ijk,n4ijk,leftijk,rightijk) = compute_fk_from_ijkmax(i,j,nVtx[2])
          fill_faceNgon_leftCell_rightCell(counter,n1ijk,n2ijk,n3ijk,n4ijk,
                                           leftijk,rightijk,nVtx,nCell,
                                           faceNgon,faceLeftCell,faceRightCell)
          counter+=1
###############################################################################

###############################################################################
def compute_faceList_from_vertexRange(pointRange,iRank,nRank,nCellS,nVtxS):
    sizeS = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
    rangeS = MDIDF.uniform_distribution_at(sizeS.prod(), iRank, nRank)
    slabListS = HFR2S.compute_slabs(sizeS, rangeS)
    sizeU = rangeS[1]-rangeS[0]
    faceList = np.empty((1,sizeU),dtype=np.int32)
    counter = 0
    for slabS in slabListS:
      iS,iE, jS,jE, kS,kE = [item+1 for bounds in slabS for item in bounds]
      if pointRange[0,0] == pointRange[0,1]:
      #>> face i
        i = pointRange[0,0]
        for k in range(kS,kE):
          for j in range(jS,jE):
            faceList[0][counter] = convert_ijk_to_faceiIndex(i,j,k,nCellS,nVtxS)
            counter += 1
      elif pointRange[1,0] == pointRange[1,1]:
      #>> face j
        nbFacesi = nVtxS[0]*nCellS[1]*nCellS[2]
        j = pointRange[1,0]
        for k in range(kS,kE):
          for i in range(iS,iE):
            faceList[0][counter] = convert_ijk_to_facejIndex(i,j,k,nCellS,nVtxS,nbFacesi)
            counter += 1
      elif pointRange[2,0] == pointRange[2,1]:
      #>> face k
        nbFacesi = nVtxS[0]*nCellS[1]*nCellS[2]
        nbFacesj = nVtxS[1]*nCellS[0]*nCellS[2]
        k = pointRange[2,0]
        for j in range(jS,jE):
          for i in range(iS,iE):
            faceList[0][counter] = convert_ijk_to_facekIndex(i,j,k,nCellS,nVtxS,nbFacesi,nbFacesj)
            counter += 1
      else:
        raise ValueError("The PointRange '{}' is bad defined".format(pointRange))
    return(faceList)
###############################################################################

###############################################################################
def compute_vertexList_from_vertexRange(pointRange,iRank,nRank,nVtxS):
    sizeS = np.abs(pointRange[:,1] - pointRange[:,0]) + 1
    rangeS = MDIDF.uniform_distribution_at(sizeS.prod(), iRank, nRank)
    slabListS = HFR2S.compute_slabs(sizeS, rangeS)
    sizeU = rangeS[1]-rangeS[0]
    vertexList = np.empty((1,sizeU),dtype=np.int32)
    counter = 0
    for slabS in slabListS:
      iS,iE, jS,jE, kS,kE = [item+1 for bounds in slabS for item in bounds]
      if pointRange[0,0] == pointRange[0,1]:
      #>> face i
        i = pointRange[0,0]
        for k in range(kS,kE):
          for j in range(jS,jE):
            vertexList[0][counter] = convert_ijk_to_index(i,j,k,nVtxS[0],nVtxS[1],nVtxS[2])
            counter += 1
      elif pointRange[1,0] == pointRange[1,1]:
      #>> face j
        j = pointRange[1,0]
        for k in range(kS,kE):
          for i in range(iS,iE):
            vertexList[0][counter] = convert_ijk_to_index(i,j,k,nVtxS[0],nVtxS[1],nVtxS[2])
            counter += 1
      elif pointRange[2,0] == pointRange[2,1]:
      #>> face k
        k = pointRange[2,0]
        for j in range(jS,jE):
          for i in range(iS,iE):
            vertexList[0][counter] = convert_ijk_to_index(i,j,k,nVtxS[0],nVtxS[1],nVtxS[2])
            counter += 1
      else:
        raise ValueError("The PointRange '{}' is bad defined".format(pointRange))
    return(vertexList)
###############################################################################

###############################################################################
def compute_cellList_from_vertexRange(pointRange,iRank,nRank,nCellS):
    sizeS = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
    rangeS = MDIDF.uniform_distribution_at(sizeS.prod(), iRank, nRank)
    slabListS = HFR2S.compute_slabs(sizeS, rangeS)
    sizeU = rangeS[1]-rangeS[0]
    cellList = np.empty((1,sizeU),dtype=np.int32)
    counter = 0
    for slabS in slabListS:
      iS,iE, jS,jE, kS,kE = [item+1 for bounds in slabS for item in bounds]
      if pointRange[0,0] == pointRange[0,1]:
      #>> face i
        i = pointRange[0,0]
        if i>nCellS[0]:
          i -= 1
        for k in range(kS,kE):
          for j in range(jS,jE):
            cellList[0][counter] = convert_ijk_to_index(i,j,k,nCellS[0],nCellS[1],nCellS[2])
            counter += 1
      elif pointRange[1,0] == pointRange[1,1]:
      #>> face j
        j = pointRange[1,0]
        if j>nCellS[1]:
          j -= 1
        for k in range(kS,kE):
          for i in range(iS,iE):
            cellList[0][counter] = convert_ijk_to_index(i,j,k,nCellS[0],nCellS[1],nCellS[2])
            counter += 1
      elif pointRange[2,0] == pointRange[2,1]:
      #>> face k
        k = pointRange[2,0]
        if k>nCellS[2]:
          k -= 1
        for j in range(jS,jE):
          for i in range(iS,iE):
            cellList[0][counter] = convert_ijk_to_index(i,j,k,nCellS[0],nCellS[1],nCellS[2])
            counter += 1
      else:
        raise ValueError("The PointRange '{}' is bad defined".format(pointRange))
    return(cellList)
###############################################################################

###############################################################################
def compute_faceList_from_faceRange(pointRange,iRank,nRank,nCellS,nVtxS,gridLocationS):
    sizeS = np.abs(pointRange[:,1] - pointRange[:,0]) + 1
    rangeS = MDIDF.uniform_distribution_at(sizeS.prod(), iRank, nRank)
    slabListS = HFR2S.compute_slabs(sizeS, rangeS)
    sizeU = rangeS[1]-rangeS[0]
    faceList = np.empty((1,sizeU),dtype=np.int32)
    counter = 0
    for slabS in slabListS:
      iS,iE, jS,jE, kS,kE = [item+1 for bounds in slabS for item in bounds]
      if gridLocationS == "IFaceCenter":
      #>> face i
        i = pointRange[0,0]
        for k in range(kS,kE):
          for j in range(jS,jE):
            faceList[0][counter] = convert_ijk_to_faceiIndex(i,j,k,nCellS,nVtxS)
            counter += 1
      elif gridLocationS == "JFaceCenter":
      #>> face j
        nbFacesi = nVtxS[0]*nCellS[1]*nCellS[2]
        j = pointRange[1,0]
        for k in range(kS,kE):
          for i in range(iS,iE):
            faceList[0][counter] = convert_ijk_to_facejIndex(i,j,k,nCellS,nVtxS,nbFacesi)
            counter += 1
      elif gridLocationS == "KFaceCenter":
      #>> face k
        nbFacesi = nVtxS[0]*nCellS[1]*nCellS[2]
        nbFacesj = nVtxS[1]*nCellS[0]*nCellS[2]
        k = pointRange[2,0]
        for j in range(jS,jE):
          for i in range(iS,iE):
            faceList[0][counter] = convert_ijk_to_facekIndex(i,j,k,nCellS,nVtxS,nbFacesi,nbFacesj)
            counter += 1
      else:
        raise ValueError("The GridLocation '{}' is bad defined".format(gridLocationS))
    return(faceList)
###############################################################################

###############################################################################
def isSameAxis(x,y):
  if abs(x) == abs(y):
     return(1)
  else:
     return(0)
###############################################################################

###############################################################################
def compute_transformMatrix(transform):
  transformMatrix = np.empty((3,3),dtype=np.int32,order='F')
  transformMatrix[0][0] = np.sign(transform[0])*isSameAxis(transform[0],1)
  transformMatrix[0][1] = np.sign(transform[1])*isSameAxis(transform[1],1)
  transformMatrix[0][2] = np.sign(transform[2])*isSameAxis(transform[2],1)
  
  transformMatrix[1][0] = np.sign(transform[0])*isSameAxis(transform[0],2)
  transformMatrix[1][1] = np.sign(transform[1])*isSameAxis(transform[1],2)
  transformMatrix[1][2] = np.sign(transform[2])*isSameAxis(transform[2],2)
  
  transformMatrix[2][0] = np.sign(transform[0])*isSameAxis(transform[0],3)
  transformMatrix[2][1] = np.sign(transform[1])*isSameAxis(transform[1],3)
  transformMatrix[2][2] = np.sign(transform[2])*isSameAxis(transform[2],3)
    
  return(transformMatrix)
###############################################################################

###############################################################################
def convert_i1j1k1_to_i2j2k2(i1,j1,k1,iS1,jS1,kS1,iS2,jS2,kS2,T):
  vector = np.array([i1-iS1,j1-jS1,k1-kS1])
  [i2,j2,k2] = np.matmul(T,vector,order='F') + np.array([iS2,jS2,kS2])
  
  return(i2,j2,k2)
###############################################################################

###############################################################################
def compute_faceList2_from_vertexRanges(pointRange1,pointRange2,T,nCell2,nVtx2):
  [iS1,jS1,kS1] = pointRange1[:,0]
  [iS2,jS2,kS2] = pointRange2[:,0]
  size1 = np.maximum(np.abs(pointRange1[:,1] - pointRange1[:,0]), 1)
  bounds1 = MDIDF.uniform_distribution_at(size1.prod(), iRank, nRank)
  slabList = HFR2S.compute_slabs(size1, bounds1)
  size2 = bounds1[1]-bounds1[0]
  faceList2 = np.empty((1,size2),dtype=np.int32)
  if T[0].sum() < 0:
    correcti2 = -1
  else:
    correcti2 = 0
  if T[1].sum() < 0:
    correctj2 = -1
  else:
    correctj2 = 0
  if T[2].sum() < 0:
    correctk2 = -1
  else:
    correctk2 = 0
  counter = 0
  for slab in slabList:
    iS,iE, jS,jE, kS,kE = [item+1 for bounds in slab for item in bounds]
    if pointRange2[0,0] == pointRange2[0,1]:
    #>> face i2
      for k1 in range(kS,kE):
        for j1 in range(jS,jE):
          for i1 in range(iS,iE):
            (i2,j2,k2) = convert_i1j1k1_to_i2j2k2(i1,j1,k1,iS1,jS1,kS1,iS2,jS2,kS2,T)
            j2 += correctj2
            k2 += correctk2
            faceList2[0][counter] = convert_ijk_to_faceiIndex(i2,j2,k2,nCell2,nVtx2)
            counter += 1
    elif pointRange2[1,0] == pointRange2[1,1]:
    #>> face j2
      nbFacesi2 = nVtx2[0]*nCell2[1]*nCell2[2]
      for k1 in range(kS,kE):
        for j1 in range(jS,jE):
          for i1 in range(iS,iE):
            (i2,j2,k2) = convert_i1j1k1_to_i2j2k2(i1,j1,k1,iS1,jS1,kS1,iS2,jS2,kS2,T)
            i2 += correcti2
            k2 += correctk2
            faceList2[0][counter] = convert_ijk_to_facejIndex(i2,j2,k2,nCell2,nVtx2,nbFacesi2)
            counter += 1
    elif pointRange2[2,0] == pointRange2[2,1]:
    #>> face k2
      nbFacesi2 = nVtx2[0]*nCell2[1]*nCell2[2]
      nbFacesj2 = nVtx2[1]*nCell2[0]*nCell2[2]
      for k1 in range(kS,kE):
        for j1 in range(jS,jE):
          for i1 in range(iS,iE):
            (i2,j2,k2) = convert_i1j1k1_to_i2j2k2(i1,j1,k1,iS1,jS1,kS1,iS2,jS2,kS2,T)
            i2 += correcti2
            j2 += correctj2
            faceList2[0][counter] = convert_ijk_to_facekIndex(i2,j2,k2,nCell2,nVtx2,nbFacesi2,nbFacesj2)
            counter += 1
    else:
      raise ValueError("The PointRange2 '{}' is bad defined".format(pointRange2))    
    
  return(faceList2)
###############################################################################

###############################################################################
def compute_vertexList2_from_vertexRanges(pointRange1,pointRange2,T,nCell2,nVtx2):
  [iS1,jS1,kS1] = pointRange1[:,0]
  [iS2,jS2,kS2] = pointRange2[:,0]
  size1 = np.abs(pointRange1[:,1] - pointRange1[:,0]) + 1
  bounds1 = MDIDF.uniform_distribution_at(size1.prod(), iRank, nRank)
  slabList = HFR2S.compute_slabs(size1, bounds1)
  size2 = bounds1[1]-bounds1[0]
  vertexList2 = np.empty((1,size2),dtype=np.int32)
  counter = 0
  for slab in slabList:
    iS,iE, jS,jE, kS,kE = [item+1 for bounds in slab for item in bounds]
    for k1 in range(kS,kE):
      for j1 in range(jS,jE):
        for i1 in range(iS,iE):
          (i2,j2,k2) = convert_i1j1k1_to_i2j2k2(i1,j1,k1,iS1,jS1,kS1,iS2,jS2,kS2,T)
          vertexList2[0][counter] = convert_ijk_to_index(i2,j2,k2,nVtx2[0],nVtx2[1],nVtx2[2])
          counter += 1
    
  return(vertexList2)
###############################################################################

###############################################################################
def compute_cellList2_from_vertexRanges(pointRange1,pointRange2,T,nCell2,nVtx2):
  [iS1,jS1,kS1] = pointRange1[:,0]
  [iS2,jS2,kS2] = pointRange2[:,0]
  size1 = np.maximum(np.abs(pointRange1[:,1] - pointRange1[:,0]), 1)
  bounds1 = MDIDF.uniform_distribution_at(size1.prod(), iRank, nRank)
  slabList = HFR2S.compute_slabs(size1, bounds1)
  size2 = bounds1[1]-bounds1[0]
  cellList2 = np.empty((1,size2),dtype=np.int32)
  if T[0].sum() < 0:
    correcti2 = -1
  else:
    correcti2 = 0
  if T[1].sum() < 0:
    correctj2 = -1
  else:
    correctj2 = 0
  if T[2].sum() < 0:
    correctk2 = -1
  else:
    correctk2 = 0
  counter = 0
  for slab in slabList:
    iS,iE, jS,jE, kS,kE = [item+1 for bounds in slab for item in bounds]
    if pointRange2[0,0] == pointRange2[0,1]:
    #>> face i2
      for k1 in range(kS,kE):
        for j1 in range(jS,jE):
          for i1 in range(iS,iE):
            (i2,j2,k2) = convert_i1j1k1_to_i2j2k2(i1,j1,k1,iS1,jS1,kS1,iS2,jS2,kS2,T)
            j2 += correctj2
            k2 += correctk2
            cellList2[0][counter] = convert_ijk_to_index(i2,j2,k2,nCell2[0],nCell2[1],nCell2[2])
            counter += 1
    elif pointRange2[1,0] == pointRange2[1,1]:
    #>> face j2
      for k1 in range(kS,kE):
        for j1 in range(jS,jE):
          for i1 in range(iS,iE):
            (i2,j2,k2) = convert_i1j1k1_to_i2j2k2(i1,j1,k1,iS1,jS1,kS1,iS2,jS2,kS2,T)
            i2 += correcti2
            k2 += correctk2
            cellList2[0][counter] = convert_ijk_to_index(i2,j2,k2,nCell2[0],nCell2[1],nCell2[2])
            counter += 1
    elif pointRange2[2,0] == pointRange2[2,1]:
    #>> face k2
      for k1 in range(kS,kE):
        for j1 in range(jS,jE):
          for i1 in range(iS,iE):
            (i2,j2,k2) = convert_i1j1k1_to_i2j2k2(i1,j1,k1,iS1,jS1,kS1,iS2,jS2,kS2,T)
            i2 += correcti2
            j2 += correctj2
            cellList2[0][counter] = convert_ijk_to_index(i2,j2,k2,nCell2[0],nCell2[1],nCell2[2])
            counter += 1
    else:
      raise ValueError("The PointRange2 '{}' is bad defined".format(pointRange2))    
    
  return(cellList2)
###############################################################################

###############################################################################
def compute_dZones2ID(distTree):
  return{I.getName(zone):z for z, zone in enumerate(I.getZones(distTree))}

###############################################################################

###############################################################################
def compute_dJoins2ID(distree,dZones2ID):
  dJoins2ID    = {}
  counterJoins = 0
  for zone in I.getZones(distTree):
    zoneName = I.getName(zone)
    zoneID   = dZones2ID[zoneName]
    zoneGC = I.getNodesFromType1(zone, 'ZoneGridConnectivity_t')
    joins  = I.getNodesFromType1(zoneGC, 'GridConnectivity_t')
    joins += I.getNodesFromType1(zoneGC, 'GridConnectivity1to1_t')
    for join in joins:
      zoneDonorName = I.getValue(join)
      zoneDonorID   = dZones2ID[zoneDonorName]
      if zoneID < zoneDonorID:
        pointRange = I.getValue(I.getNodeFromName1(join, 'PointRange'))
        strPointRange = ""
        for dim1 in range(pointRange.shape[0]):
          for dim2 in range(pointRange.shape[1]):
            strPointRange += "_{0}".format(pointRange[dim1][dim2])
            joinName = str(zoneID)+"_"+str(zoneDonorID)+strPointRange
            dJoins2ID[joinName] = counterJoins
            counterJoins += 1
  return dJoins2ID

###############################################################################

###############################################################################
def correctPointRanges(pointRange,pointRangeDonor,transform,zoneID,zoneDonorID):
  newPointRange      = np.empty(pointRange.shape,dtype=np.int32)
  newPointRangeDonor = np.empty(pointRange.shape,dtype=np.int32)
  for d in range(pointRange.shape[0]):
    dDonor = abs(transform[d])-1
    nbPointd = pointRange[d][1] - pointRange[d][0]
    nbPointDonord = np.sign(transform[d])*(pointRangeDonor[dDonor][1] - pointRangeDonor[dDonor][0])
    if nbPointd == nbPointDonord:
      newPointRange[d][0]      = pointRange[d][0]
      newPointRange[d][1]      = pointRange[d][1]
      newPointRangeDonor[d][0] = pointRangeDonor[dDonor][0]
      newPointRangeDonor[d][1] = pointRangeDonor[dDonor][1]
    else:
      if zoneID < zoneDonorID:
        newPointRange[d][0]      = pointRange[d][0]
        newPointRange[d][1]      = pointRange[d][1]
        newPointRangeDonor[d][0] = pointRangeDonor[dDonor][1]
        newPointRangeDonor[d][1] = pointRangeDonor[dDonor][0]
      else:
        newPointRange[d][0]      = pointRange[d][1]
        newPointRange[d][1]      = pointRange[d][0]
        newPointRangeDonor[d][0] = pointRangeDonor[dDonor][0]
        newPointRangeDonor[d][1] = pointRangeDonor[dDonor][1]
        
  return (newPointRange,newPointRangeDonor)
###############################################################################

###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
###############################################################################
# Début convertion DistTreeS en DistTreeU

def convert_s_to_u(distTreeS,comm,attendedGridLocationBC="FaceCenter",attendedGridLocationGC="FaceCenter"):

  nRank = comm.Get_size()
  iRank = comm.Get_rank()

  dZones2ID = compute_dZones2ID(distTreeS)
  
  #> Create skeleton of distTreeU
  distTreeU = I.newCGNSTree()
  baseS = I.getNodeFromType1(distTreeS,'CGNSBase_t')
  baseU = I.newCGNSBase(I.getName(baseS),parent=distTreeU)
  I.setValue(baseU,I.getValue(baseS))
  for zoneS in I.getZones(distTreeS):
    zoneSName = I.getName(zoneS)
    zoneSDims = I.getValue(zoneS)
    nCellS = zoneSDims[:,1]
    nVtxS  = zoneSDims[:,0]
    nCellTotS = nCellS.prod()
    nVtxTotS  = nVtxS.prod()
  
  #> Calcul du nombre faces totales en i, j et k
    nbFacesi = nVtxS[0]*nCellS[1]*nCellS[2]
    nbFacesj = nVtxS[1]*nCellS[0]*nCellS[2]
    nbFacesk = nVtxS[2]*nCellS[0]*nCellS[1]
    nbFacesTot = nbFacesi + nbFacesj + nbFacesk
  
  #> with Zones
    nCellU = np.prod(nCellS)
    nVtxU  = np.prod(nVtxS)
    zoneUSize = [[nVtxU,nCellU,0]]
    zoneU = I.newZone(zoneSName, zoneUSize, 'Unstructured', None, baseU)
  
  #> with GridCoordinates
    gridCoordinatesS = I.getNodeFromType1(zoneS,"GridCoordinates_t")
    CoordinateXS = I.getNodeFromName1(gridCoordinatesS,"CoordinateX")
    CoordinateYS = I.getNodeFromName1(gridCoordinatesS,"CoordinateY")
    CoordinateZS = I.getNodeFromName1(gridCoordinatesS,"CoordinateZ")
    gridCoordinatesU = I.newGridCoordinates(parent=zoneU)
    I.newDataArray('CoordinateX', I.getValue(CoordinateXS), gridCoordinatesU)
    I.newDataArray('CoordinateY', I.getValue(CoordinateYS), gridCoordinatesU)
    I.newDataArray('CoordinateZ', I.getValue(CoordinateZS), gridCoordinatesU)
  
  #> with FlowSolutions
    for flowSolutionS in I.getNodesFromType1(zoneS,"FlowSolution_t"):
      flowSolutionU = I.newFlowSolution(I.getName(flowSolutionS),parent=zoneU)
      gridLocationS = I.getNodeFromType1(zoneS,"GridLocation_t")
      if gridLocationS:
        I.newGridLocation(I.getValue(gridLocationS),flowSolutionU)
      else:
        I.newGridLocation("CellCenter",flowSolutionU)
      for dataS in I.getNodesFromType1(flowSolutionS,"DataArray_t"):
        I.newDataArray(I.getName(dataS),I.getValue(dataS),flowSolutionU)
  
  #> with NgonElements
    #>> Definition en non structure des faces
    vtxRangeS  = MDIDF.uniform_distribution_at(nVtxTotS, iRank, nRank)
    slabListVtxS  = HFR2S.compute_slabs(zoneS[1][:,0], vtxRangeS)
    nbFacesAllSlabsPerZone = compute_nbFacesAllSlabsPerZone(slabListVtxS, nVtxS)  
    faceNumber    = -np.ones(  nbFacesAllSlabsPerZone, dtype=np.int32)
    faceNgon      = -np.ones(4*nbFacesAllSlabsPerZone, dtype=np.int32)
    faceLeftCell  = -np.ones(  nbFacesAllSlabsPerZone, dtype=np.int32)
    faceRightCell = -np.ones(  nbFacesAllSlabsPerZone, dtype=np.int32)
    compute_faceNumber_faceNgon_leftCell_rightCell_forAllFaces(slabListVtxS,nVtxS,nCellS,
                                                               nbFacesi,nbFacesj,
                                                               faceNumber,faceNgon,
                                                               faceLeftCell,faceRightCell)   
    #>> PartToBlock pour ordonner et equidistribuer les faces
    #>>> Creation de l'objet partToBlock
    #>>> PDM_part_to_block_distrib_t t_distrib = 0 ! Numerotation recalculee sur tous les procs
    #>>> PDM_part_to_block_post_t    t_post    = 0 ! Pas de traitement sur les valeurs
    #>>> PDM_stride_t                t_stride  = 1 ! Stride variable car variable en sortie...
    partToBlockObject = PDM.PartToBlock(comm, [faceNumber], None, 1, 0, 0, 1)
    #>>> Premier echange pour le ParentElements
    pFieldStride1 = dict()  
    pFieldStride1["faceLeftCell"] = []
    pFieldStride1["faceLeftCell"].append(faceLeftCell)
    pFieldStride1["faceRightCell"] = []
    pFieldStride1["faceRightCell"].append(faceRightCell)
    pStride1 = []
    pStride1.append(np.ones(nbFacesAllSlabsPerZone,dtype='int32'))  
    dFieldStride1 = dict()  
    partToBlockObject.PartToBlock_Exchange(dFieldStride1, pFieldStride1, pStride1)
    #>>> Deuxieme echange pour l'ElementConnectivity
    pFieldStride4 = dict()
    pFieldStride4["faceNgon"] = []
    pFieldStride4["faceNgon"].append(faceNgon)
    pStride4 = []
    pStride4.append(4*np.ones(nbFacesAllSlabsPerZone,dtype='int32'))
    dFieldStride4 = dict()
    partToBlockObject.PartToBlock_Exchange(dFieldStride4, pFieldStride4, pStride4)
    #>>> Distribution des faces  
    facesDistribution = partToBlockObject.getDistributionCopy()
    # >> Creation du noeud NGonElements
    ngon = I.newElements('NGonElements', 'NGON', dFieldStride4["faceNgon"],
                         [1,nbFacesTot], parent=zoneU)
    nbFacesLoc = dFieldStride1["faceLeftCell"].shape[0]
    pe = np.empty((nbFacesLoc,2),dtype=np.int32)
    for i in range(nbFacesLoc):
      pe[i][0] = dFieldStride1["faceLeftCell"][i]
      pe[i][1] = dFieldStride1["faceRightCell"][i]
    I.newParentElements(pe,ngon)
    startOffset = facesDistribution[iRank]
    endOffset   = startOffset + nbFacesLoc+1
    I.newDataArray("ElementStartOffset",4*np.arange(startOffset,endOffset),ngon)
    I.newIndexArray('ElementConnectivity#Size', [nbFacesTot*4], ngon)
  
  #> with ZoneBC
    zoneBCS = I.getNodeFromType1(zoneS,"ZoneBC_t")
    if zoneBCS is not None:
      zoneBCU = I.newZoneBC(zoneU)
      for bcS in I.getNodesFromType1(zoneBCS,"BC_t"):
        gridLocationNodeS = I.getNodeFromType1(bcS, "GridLocation_t")
        if gridLocationNodeS is None:
          gridLocationS = "Vertex"
        else:
          gridLocationS = I.getValue(gridLocationNodeS)
        bcU = copy.deepcopy(bcS)
        I._rmNodesByType(bcU,"GridLocation_t")
        I._rmNodesByType(bcU,"IndexRange_t")
        I._rmNodesByName(bcU,":CGNS#Distribution")
        pointRange = I.getValue(I.getNodeFromName1(bcS, 'PointRange'))
        if gridLocationS == "Vertex":
          if attendedGridLocationBC == "FaceCenter":
            pointList = compute_faceList_from_vertexRange(pointRange,iRank,nRank,nCellS,nVtxS)
            sizeS     = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          elif attendedGridLocationBC == "Vertex":
            pointList = compute_vertexList_from_vertexRange(pointRange,iRank,nRank,nVtxS)
            sizeS     = np.abs(pointRange[:,1] - pointRange[:,0]) + 1
          elif attendedGridLocationBC == "CellCenter":
            pointList = compute_cellList_from_vertexRange(pointRange,iRank,nRank,nCellS)
            sizeS     = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          else:
            raise ValueError("attendedGridLocationBC is '{}' but allowed values are 'Vertex', 'FaceCenter' or 'CellCenter'".format(attendedGridLocationBC))
        elif "FaceCenter" in gridLocationS:
          if attendedGridLocationBC == "FaceCenter":
            pointList = compute_faceList_from_faceRange(pointRange,iRank,nRank,nCellS,nVtxS,gridLocationS)
            sizeS     = np.abs(pointRange[:,1] - pointRange[:,0]) + 1
          # elif attendedGridLocationBC == "Vertex":
          #   pointList = compute_vertexList_from_vertexRange(pointRange,iRank,nRank,nVtxS)
          #   sizeS     = np.abs(pointRange[:,1] - pointRange[:,0]) + 1
          # elif attendedGridLocationBC == "CellCenter":
          #   pointList = compute_cellList_from_vertexRange(pointRange,iRank,nRank,nCellS)
          #   sizeS     = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          else:
            print("Not yet implemented !!!")
          #   raise ValueError("attendedGridLocationBC is '{}' but allowed values are 'Vertex', 'FaceCenter' or 'CellCenter'".format(attendedGridLocationBC))
        sizeU = sizeS.prod()
        I.newPointList(value=pointList,parent=bcU)
        I.newGridLocation(attendedGridLocationBC,bcU)
        I.newIndexArray('PointList#Size', [1, sizeU], bcU)
        I.addChild(zoneBCU,bcU)
      
  #> with ZoneGC
    zoneGCS = I.getNodeFromType1(zoneS,"ZoneGridConnectivity_t")
    if zoneGCS is not None:
      zoneGCU = I.newZoneGridConnectivity(parent=zoneU)
      joinsS  = I.getNodesFromType1(zoneGCS, "GridConnectivity1to1_t")
      zoneID  = dZones2ID[zoneSName]
      for gcS in joinsS:
        gridLocationNodeS = I.getNodeFromType1(gcS, "GridLocation_t")
        if gridLocationNodeS is not None:
          if I.getValue(gridLocationNodeS) != "Vertex":
            raise ValueError("'GridLocation' value for a 'GridConnectivity1to1_t' node could only be 'Vertex'.")
        gcU = copy.deepcopy(gcS)
        I._rmNodesByType(gcU,"GridLocation_t")
        I._rmNodesByType(gcU,"IndexRange_t")
        I._rmNodesByName(gcU,":CGNS#Distribution")
        I._rmNodesByName(gcU,"Transform")
        I._setType(gcU, 'GridConnectivity_t')
        I.newGridConnectivityType('Abutting1to1', gcU) 
        pointRange      = I.getValue(I.getNodeFromName1(gcS, 'PointRange'))
        pointRangeDonor = I.getValue(I.getNodeFromName1(gcS, 'PointRangeDonor'))
        transform = I.getValue(I.getNodeFromName1(gcS, 'Transform'))
        zoneDonorName = I.getValue(gcS)
        zoneDonorID   = dZones2ID[zoneDonorName]
        (pointRange,pointRangeDonor) = correctPointRanges(pointRange,pointRangeDonor,transform,zoneID,zoneDonorID)
        I.setValue(I.getNodeFromName1(gcS, 'PointRange')     ,pointRange)
        I.setValue(I.getNodeFromName1(gcS, 'PointRangeDonor'),pointRangeDonor)
        zoneSDimsDonor = I.getValue(I.getNodeFromName1(baseS,zoneDonorName))
        nCellSDonor = zoneSDimsDonor[:,1]
        nVtxSDonor  = zoneSDimsDonor[:,0]
        T = compute_transformMatrix(transform)
        if zoneID == zoneDonorID:
        # raccord périodique sur la même zone
          if attendedGridLocationGC == "FaceCenter":
            pointList      = compute_faceList_from_vertexRange(pointRange     ,iRank,nRank,nCellS,nVtxS)
            pointListDonor = compute_faceList_from_vertexRange(pointRangeDonor,iRank,nRank,nCellS,nVtxS)
            sizeS = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          elif attendedGridLocationGC == "Vertex":
            pointList      = compute_vertexList_from_vertexRange(pointRange     ,iRank,nRank,nVtxS)
            pointListDonor = compute_vertexList_from_vertexRange(pointRangeDonor,iRank,nRank,nVtxS)
            sizeS = np.abs(pointRange[:,1] - pointRange[:,0]) + 1
          elif attendedGridLocationGC == "CellCenter":
            pointList      = compute_cellList_from_vertexRange(pointRange     ,iRank,nRank,nCellS)
            pointListDonor = compute_cellList_from_vertexRange(pointRangeDonor,iRank,nRank,nCellS)
            sizeS = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          else:
            raise ValueError("attendedGridLocationGC is '{}' but allowed values are 'Vertex', 'FaceCenter' or 'CellCenter'".format(attendedGridLocationGC))
        elif zoneID < zoneDonorID:
          if attendedGridLocationGC == "FaceCenter":
            pointList      = compute_faceList_from_vertexRange(pointRange,iRank,nRank,nCellS,nVtxS)
            pointListDonor = compute_faceList2_from_vertexRanges(pointRange,pointRangeDonor,T,nCellSDonor,nVtxSDonor)
            sizeS          = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          elif attendedGridLocationGC == "Vertex":
            pointList      = compute_vertexList_from_vertexRange(pointRange,iRank,nRank,nVtxS)
            pointListDonor = compute_vertexList2_from_vertexRanges(pointRange,pointRangeDonor,T,nCellSDonor,nVtxSDonor)
            sizeS          = np.abs(pointRange[:,1] - pointRange[:,0]) + 1
          elif attendedGridLocationGC == "CellCenter":
            pointList      = compute_cellList_from_vertexRange(pointRange,iRank,nRank,nCellS)
            pointListDonor = compute_cellList2_from_vertexRanges(pointRange,pointRangeDonor,T,nCellSDonor,nVtxSDonor)
            sizeS = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          else:
            raise ValueError("attendedGridLocationGC is '{}' but allowed values are 'Vertex', 'FaceCenter' or 'CellCenter'".format(attendedGridLocationGC))
        else:
          if attendedGridLocationGC == "FaceCenter":
            pointListDonor = compute_faceList_from_vertexRange(pointRangeDonor,iRank,nRank,nCellSDonor,nVtxSDonor)
            pointList      =compute_faceList2_from_vertexRanges(pointRangeDonor,pointRange,np.transpose(T),nCellS,nVtxS)
            sizeS          = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          elif attendedGridLocationGC == "Vertex":
            pointListDonor = compute_vertexList_from_vertexRange(pointRangeDonor,iRank,nRank,nVtxSDonor)
            pointList      = compute_vertexList2_from_vertexRanges(pointRangeDonor,pointRange,np.transpose(T),nCellS,nVtxS)
            sizeS          = np.abs(pointRange[:,1] - pointRange[:,0]) + 1
          elif attendedGridLocationGC == "CellCenter":
            pointListDonor = compute_cellList_from_vertexRange(pointRangeDonor,iRank,nRank,nCellSDonor)
            pointList      = compute_cellList2_from_vertexRanges(pointRangeDonor,pointRange,np.transpose(T),nCellS,nVtxS)
            sizeS = np.maximum(np.abs(pointRange[:,1] - pointRange[:,0]), 1)
          else:
            raise ValueError("attendedGridLocationGC is '{}' but allowed values are 'Vertex', 'FaceCenter' or 'CellCenter'".format(attendedGridLocationGC))
        sizeU = sizeS.prod()
        I.newPointList(value=pointList,parent=gcU)
        I.newPointList('PointListDonor',value=pointListDonor,parent=gcU)
        I.newGridLocation(attendedGridLocationGC,gcU)
        I.newIndexArray('PointList#Size', [1, sizeU], gcU)
        I.addChild(zoneGCU,gcU)
      
  # #> with ZoneGC
  # TO DO
  
  #> with FlowEquationSet
  for flowEquationSetS in I.getNodesFromType1(baseS,"FlowEquationSet_t"):
    I.addChild(baseU,flowEquationSetS)
  
  #> with ReferenceState
  for referenceStateS in I.getNodesFromType1(baseS,"ReferenceState_t"):
    I.addChild(baseU,referenceStateS)
  
  #> with Family
  for familyS in I.getNodesFromType1(baseS,"Family_t"):
    I.addChild(baseU,familyS)
  
