import mpi4py.MPI as MPI
import numpy as np
import itertools

import Converter.Internal as I
import Pypdm.Pypdm        as PDM

from maia import npy_pdm_gnum_dtype as pdm_dtype
from maia.sids import Internal_ext as IE
from maia.utils import py_utils
from maia.utils.parallel import utils as par_utils

def _is_subset_l(subset, L):
  """Return True is subset list is included in L, allowing looping"""
  extended_l = list(L) + list(L)[:len(subset)-1]
  return max([subset == extended_l[i:i+len(subset)] for i in range(len(L))])

def _is_before(l, a, b):
  """Return True is element a is present in list l before element b"""
  for e in l:
    if e==a:
      return True
    if e==b:
      return False
  return False

def _build_ordered_jn_face(face_vtx, face_vtx_opp, start_vtx, start_vtx_opp):
  first_node_idx     = np.where(face_vtx == start_vtx)[0][0]
  opp_first_node_idx = np.where(face_vtx_opp == start_vtx_opp)[0][0]

  ordered_face_vtx     = np.roll(face_vtx, -first_node_idx)
  ordered_face_vtx_opp = np.roll(face_vtx_opp[::-1], opp_first_node_idx + 1)

  return ordered_face_vtx, ordered_face_vtx_opp

def get_pl_face_vtx_local(pl, pl_d, ngon, comm):
  """
  From pl of faces, search in the distributed NGon node the id of vertices
  belonging to the faces. Also seach the id of vertices belonging to plDonor
  faces. Return the two array of vertices ids and the offset array
  of size len(pl) + 1
  This is a distributed fonction
  """

  distri_ngon  = IE.getDistribution(ngon, 'Element').astype(pdm_dtype)

  pdm_distrib = par_utils.partial_to_full_distribution(distri_ngon, comm)
  dist_data = {'FaceVtx' : I.getNodeFromName1(ngon, 'ElementConnectivity')[1]}
  b_stride = np.diff(I.getNodeFromName1(ngon, 'ElementStartOffset')[1]).astype(np.int32)

  # Get the vertex associated to the faces in FaceList
  part_data_pl = dict()
  BTP = PDM.BlockToPart(pdm_distrib, comm, [pl.astype(pdm_dtype)], 1)
  BTP.BlockToPart_Exchange2(dist_data, part_data_pl, 1, b_stride)
  pl_face_vtx = part_data_pl['FaceVtx'][0]

  # Get the vertex associated to the opposite faces in FaceList
  part_data_pld = dict()
  BTP = PDM.BlockToPart(pdm_distrib, comm, [pl_d.astype(pdm_dtype)], 1)
  BTP.BlockToPart_Exchange2(dist_data, part_data_pld, 1, b_stride)
  pld_face_vtx = part_data_pld['FaceVtx'][0]

  face_offset = py_utils.sizes_to_indices(part_data_pl['FaceVtx#PDM_Stride'][0])

  return pl_face_vtx, pld_face_vtx, face_offset

def get_extended_pl(pl, pl_d, face_vtx_idx_pl, face_vtx_pl, comm, faces_to_skip=None):

  pl_vtx = np.unique(face_vtx_pl).astype(pdm_dtype)
  if faces_to_skip is not None:
    idx_to_extract = py_utils.multi_arange(face_vtx_idx_pl[:-1][~faces_to_skip], \
                                           face_vtx_idx_pl[1:][~faces_to_skip])
    restricted_pl_vtx = np.unique(face_vtx_pl[idx_to_extract]).astype(pdm_dtype)
  else:
    restricted_pl_vtx = pl_vtx

  #Map each vertex of pl_vtx to the couple (face, face_opp) if its belong to face
  pl_vtx_local_dict = {key: [] for key in pl_vtx}
  for iface, face_pair in enumerate(zip(pl, pl_d)):
    for vtx in face_vtx_pl[face_vtx_idx_pl[iface]:face_vtx_idx_pl[iface+1]]:
      pl_vtx_local_dict[vtx].append(face_pair)

  # Exchange to locally have the list of *all* jn faces related to vertex
  p_stride = np.array([len(pl_vtx_local_dict[vtx]) for vtx in pl_vtx], dtype=np.int32)

  part_data = dict()
  part_data["vtx_to_face"]   = [np.empty(np.sum(p_stride), dtype=np.int)]
  part_data["vtx_to_face_d"] = [np.empty(np.sum(p_stride), dtype=np.int)]
  offset = 0
  for vtx in pl_vtx:
    n = len(pl_vtx_local_dict[vtx])
    part_data["vtx_to_face"][0][offset:offset+n] = [t[0] for t in pl_vtx_local_dict[vtx]]
    part_data["vtx_to_face_d"][0][offset:offset+n] = [t[1] for t in pl_vtx_local_dict[vtx]]
    offset += n

  PTB = PDM.PartToBlock(comm, [pl_vtx], pWeight=None, partN=1,
                        t_distrib=0, t_post=2, t_stride=1)
  dist_data = dict()
  PTB.PartToBlock_Exchange(dist_data, part_data, [p_stride])


  #Recreate stride for all vertex
  first, count, total = PTB.getBeginNbEntryAndGlob()
  b_stride = np.zeros(count, np.int32)
  b_stride[PTB.getBlockGnumCopy() - first - 1] = dist_data['vtx_to_face#Stride']

  dist_data.pop('vtx_to_face#Stride')
  dist_data.pop('vtx_to_face_d#Stride')
  part_data = dict()

  BTP = PDM.BlockToPart(PTB.getDistributionCopy(), comm, [restricted_pl_vtx], 1)
  BTP.BlockToPart_Exchange2(dist_data, part_data, 1, b_stride)

  extended_pl, unique_idx = np.unique(part_data["vtx_to_face"][0], return_index=True)
  extended_pl_d = part_data["vtx_to_face_d"][0][unique_idx]

  return extended_pl, extended_pl_d

def _search_by_intersection(pl_face_vtx_idx, pl_face_vtx, pld_face_vtx):
  """
  """
  #But : trouver la liste des noeuds qui sont l'intersection de 2 faces
  n_face = len(pl_face_vtx_idx) - 1
  pl_vtx_local     = np.unique(pl_face_vtx)
  pl_vtx_local_opp = np.zeros_like(pl_vtx_local)
  face_is_treated  = np.zeros(n_face, dtype=np.bool)

  #Noeud -> liste des faces auxquelles il appartient
  pl_vtx_local_dict = {key: [] for key in pl_vtx_local}
  for iface in range(n_face):
    for vtx in pl_face_vtx[pl_face_vtx_idx[iface]:pl_face_vtx_idx[iface+1]]:
      pl_vtx_local_dict[vtx].append(iface)

  #print('pl_vtx_local_dict', pl_vtx_local_dict)

  #Invert dictionnary to have couple of faces -> list of vertices
  interfaces_to_nodes = dict()
  for key, val in pl_vtx_local_dict.items():
    for pair in itertools.combinations(sorted(val), 2):
      try:
        interfaces_to_nodes[pair].append(key)
      except KeyError:
        interfaces_to_nodes[pair] = [key]

  vtx_g_to_l = {v:i for i,v in enumerate(pl_vtx_local)}

  for interface, vtx in interfaces_to_nodes.items():
    #interface (FA,FB) vtx = (vtx1, vtx2)
    step = 0
    opp_face_vtx_a = pld_face_vtx[pl_face_vtx_idx[interface[0]]:pl_face_vtx_idx[interface[0]+1]]
    opp_face_vtx_b = pld_face_vtx[pl_face_vtx_idx[interface[1]]:pl_face_vtx_idx[interface[1]+1]]
    opp_vtx = np.intersect1d(opp_face_vtx_a, opp_face_vtx_b)

    # Si les sommets se suivent, on peut retrouver l'ordre
    if _is_subset_l(vtx, pl_face_vtx[pl_face_vtx_idx[interface[0]]:pl_face_vtx_idx[interface[0]+1]]):
      step = -2*(_is_before(opp_face_vtx_a, opp_vtx[0], opp_vtx[-1])) + 1
    elif _is_subset_l(vtx[::-1], pl_face_vtx[pl_face_vtx_idx[interface[0]]:pl_face_vtx_idx[interface[0]+1]]):
      step = -2*(not _is_before(opp_face_vtx_a, opp_vtx[0], opp_vtx[-1])) + 1
    elif _is_subset_l(vtx, pl_face_vtx[pl_face_vtx_idx[interface[1]]:pl_face_vtx_idx[interface[1]+1]]):
      step = -2*(not _is_before(opp_face_vtx_b, opp_vtx[0], opp_vtx[-1])) + 1
    elif _is_subset_l(vtx[::-1], pl_face_vtx[pl_face_vtx_idx[interface[1]]:pl_face_vtx_idx[interface[1]+1]]):
      step = -2*(_is_before(opp_face_vtx_b, opp_vtx[0], opp_vtx[-1])) + 1

    # Skip non continous vertices
    if step != 0:
      l_vertices = [vtx_g_to_l[v] for v in vtx]
      assert len(opp_vtx) == len(l_vertices)
      pl_vtx_local_opp[l_vertices] = opp_vtx[::step]

      for face in interface:
        if not face_is_treated[face]:
          face_vtx     = pl_face_vtx[pl_face_vtx_idx[face]:pl_face_vtx_idx[face+1]]
          opp_face_vtx = pld_face_vtx[pl_face_vtx_idx[face]:pl_face_vtx_idx[face+1]]
          ordered_vtx, ordered_vtx_opp = _build_ordered_jn_face(
              face_vtx, opp_face_vtx, vtx[0], pl_vtx_local_opp[l_vertices[0]])
          pl_vtx_local_opp[[vtx_g_to_l[k] for k in ordered_vtx]] = ordered_vtx_opp

      face_is_treated[list(interface)] = True

  someone_changed = True
  while (face_is_treated.prod() == 0 and someone_changed):
    someone_changed = False
    for face in np.where(~face_is_treated)[0]:
      face_vtx   = pl_face_vtx [pl_face_vtx_idx[face]:pl_face_vtx_idx[face+1]]
      l_vertices = [vtx_g_to_l[v] for v in face_vtx]
      for i, vtx_opp in enumerate(pl_vtx_local_opp[l_vertices]):
        #Get any already deduced opposed vertex
        if vtx_opp != 0:
          opp_face_vtx = pld_face_vtx[pl_face_vtx_idx[face]:pl_face_vtx_idx[face+1]]
          ordered_vtx, ordered_vtx_opp = _build_ordered_jn_face(
              face_vtx, opp_face_vtx, pl_vtx_local[l_vertices[i]], vtx_opp)

          pl_vtx_local_opp[[vtx_g_to_l[k] for k in ordered_vtx]] = ordered_vtx_opp
          face_is_treated[face] = True
          someone_changed = True
          break

  return pl_vtx_local, pl_vtx_local_opp, face_is_treated

def _search_with_geometry(zone, pl_face_vtx, pld_face_vtx, owner, comm):
  pl_vtx_local     = np.unique(pl_face_vtx)
  pl_vtx_local_opp = np.zeros_like(pl_vtx_local)

  vtx_g_to_l = {v:i for i,v in enumerate(pl_vtx_local)}
  distri_vtx = IE.getDistribution(zone, 'Vertex')
  distri_full = par_utils.partial_to_full_distribution(distri_vtx, comm)

  if comm.Get_rank() == owner:
    assert len(pl_face_vtx) == len(pld_face_vtx)
    n_face_vtx = len(pl_face_vtx)
    requested_vtx = np.concatenate([pl_face_vtx, pld_face_vtx])
    dest_ranks = np.searchsorted(distri_full, requested_vtx-1, 'right')-1
    sorting_idx = np.argsort(dest_ranks)
    sizes  = np.bincount(dest_ranks, minlength = comm.Get_size())
    sizes3 = 3*sizes
    requested_vtx_s = requested_vtx[sorting_idx].astype(np.int)

    received_coords = np.empty((len(requested_vtx),3), np.float, order='C')
  else:
    sizes  = None
    sizes3 = None
    requested_vtx_s = None
    received_coords = None

  n_vtx_to_send = comm.scatter(sizes, root=owner)

  idx_to_send = np.empty(n_vtx_to_send, dtype=np.int)
  comm.Scatterv([requested_vtx_s, sizes], idx_to_send, root=owner)

  grid_co = I.getNodeFromType1(zone, 'GridCoordinates_t')
  cx      = I.getNodeFromName1(grid_co, 'CoordinateX')[1][idx_to_send-distri_vtx[0]-1]
  cy      = I.getNodeFromName1(grid_co, 'CoordinateY')[1][idx_to_send-distri_vtx[0]-1]
  cz      = I.getNodeFromName1(grid_co, 'CoordinateZ')[1][idx_to_send-distri_vtx[0]-1]

  coords_to_send = np.array([cx, cy, cz], order='F').transpose()
  comm.Gatherv(coords_to_send, [received_coords, sizes3], owner)

  #Now proc master has all the coordinates
  if comm.Get_rank() == owner:
    inverted_sorting_idx = np.empty_like(sorting_idx)
    for i,k in enumerate(sorting_idx):
      inverted_sorting_idx[k] = i

    face_vtx_coords     = received_coords[inverted_sorting_idx[0:n_face_vtx]]
    opp_face_vtx_coords = received_coords[inverted_sorting_idx[n_face_vtx:2*n_face_vtx]]

    # first_vtx     = np.lexsort((face_vtx_coords.T))[0]
    # opp_first_vtx = np.lexsort((opp_face_vtx_coords.T))[0]

    # Unique should sort array following the same key (axis=0 is important!)
    sorted_face_vtx_coords, indices, counts = np.unique(face_vtx_coords, axis=0, return_index = True, return_counts = True)
    sorted_opp_face_vtx_coords, opp_indices = np.unique(opp_face_vtx_coords, axis=0, return_index=True)
    assert len(sorted_face_vtx_coords) == len(sorted_opp_face_vtx_coords)
    # Search first unique element and use it as starting vtx
    idx = 0
    counts_it = iter(counts)
    while (next(counts_it) != 1):
      idx += 1
    first_vtx     = indices[idx]
    opp_first_vtx = opp_indices[idx]

    #Todo change interface to allow start_vtx_indx, and start_vtx_opp_index to avoid np.where
    ordered_vtx, ordered_vtx_opp = _build_ordered_jn_face(
        pl_face_vtx, pld_face_vtx, requested_vtx[first_vtx], requested_vtx[opp_first_vtx+n_face_vtx])

    pl_vtx_local_opp[[vtx_g_to_l[k] for k in ordered_vtx]] = ordered_vtx_opp

  return pl_vtx_local, pl_vtx_local_opp


def generate_jn_vertex_list(zone, ngon, jn, comm):

  #Suppose jn location == face
  distri_jn = IE.getDistribution(jn, 'Index')

  pl   = I.getNodeFromName1(jn, 'PointList')[1][0]
  pl_d = I.getNodeFromName1(jn, 'PointListDonor')[1][0]

  pl_face_vtx, pld_face_vtx, face_offset = get_pl_face_vtx_local(pl, pl_d, ngon, comm)

  #Raccord single face
  if distri_jn[2] == 1:
    is_root = (distri_jn[1] - distri_jn[0]) != 0
    owner   = comm.allgather(is_root).index(True)

    pl_vtx_local, pl_vtx_local_opp = _search_with_geometry(zone, pl_face_vtx, pld_face_vtx, owner, comm)
    assert np.all(pl_vtx_local_opp != 0)
    pl_vtx_local_list     = [pl_vtx_local.astype(pdm_dtype)]
    pl_vtx_local_opp_list = [pl_vtx_local_opp.astype(pdm_dtype)]

  else:
    pl_vtx_local, pl_vtx_local_opp, face_is_treated = _search_by_intersection(face_offset, pl_face_vtx, pld_face_vtx)

    undermined_vtx = (pl_vtx_local_opp == 0)
    pl_vtx_local_list     = [pl_vtx_local[~undermined_vtx].astype(pdm_dtype)]
    pl_vtx_local_opp_list = [pl_vtx_local_opp[~undermined_vtx].astype(pdm_dtype)]

    #Face isolée:  raccord avec plusieurs faces mais 1 seule connue par le proc (ou sans voisines)
    if comm.allreduce(not np.all(face_is_treated), op=MPI.LOR) and distri_jn[2] != 1:

      extended_pl, extended_pl_d = get_extended_pl(pl, pl_d, face_offset, pl_face_vtx, comm, face_is_treated)
      pl_face_vtx_e, pld_face_vtx_e, face_offset_e = get_pl_face_vtx_local(extended_pl, extended_pl_d, ngon, comm)

      pl_vtx_local2, pl_vtx_local_opp2, _ = _search_by_intersection(face_offset_e, pl_face_vtx_e, pld_face_vtx_e)
      assert np.all(pl_vtx_local_opp2 != 0)
      pl_vtx_local_list    .append(pl_vtx_local2.astype(pdm_dtype))
      pl_vtx_local_opp_list.append(pl_vtx_local_opp2.astype(pdm_dtype))

  #Now merge vertices appearing more than once
  part_data = {'pl_vtx_opp' : pl_vtx_local_opp_list}
  PTB = PDM.PartToBlock(comm, pl_vtx_local_list, pWeight=None, partN=len(pl_vtx_local_list),
                        t_distrib=0, t_post=1, t_stride=0)
  pl_vtx = PTB.getBlockGnumCopy()
  dist_data = dict()
  PTB.PartToBlock_Exchange(dist_data, part_data)
  distri_jn_vtx_full =  par_utils.gather_and_shift(len(pl_vtx), comm, dtype=pdm_dtype)
  distri_jn_vtx =  distri_jn_vtx_full[[comm.Get_rank(), comm.Get_rank()+1, comm.Get_size()]]

  return pl_vtx, dist_data['pl_vtx_opp'], distri_jn_vtx

def generate_vertex_joins(dist_zone, comm):
  """For now only one zone is supported"""

  ngons = [elem for elem in I.getNodesFromType1(dist_zone, 'Elements_t') if elem[1][0] == 22]
  assert len(ngons) == 1
  ngon = ngons[0]

  for zgc in I.getNodesFromType1(dist_zone, 'ZoneGridConnectivity_t'):
    zgc_vtx = I.newZoneGridConnectivity(I.getName(zgc) + '#Vtx', dist_zone)
    #Todo : do not apply algo to opposite jn, juste invert values !
    for gc in I.getNodesFromType1(zgc, 'GridConnectivity_t'):
      pl_vtx, pl_vtx_opp, distri_jn = generate_jn_vertex_list(dist_zone, ngon, gc, comm)

      jn_vtx = I.newGridConnectivity(I.getName(gc)+'#Vtx', I.getValue(gc), ctype='Abutting1to1', parent=zgc_vtx)
      I.newGridLocation('Vertex', jn_vtx)
      IE.newDistribution({'Index' : distri_jn}, jn_vtx)
      I.newPointList('PointList',      pl_vtx.reshape(1,-1), parent=jn_vtx)
      I.newPointList('PointListDonor', pl_vtx_opp.reshape(1,-1), parent=jn_vtx)
      I.newIndexArray('PointList#Size', [1, distri_jn[2]], parent=jn_vtx)

  # Cas 1 seul sommet
  # print("Found is", found, interface)
  # print(_is_subset_l([3,4], [3,4,3,5]))
  # one_neighbor = {key :val for key, val in interfaces_to_nodes.items() if len(val)==1}
  # for interface, vtx in one_neighbor.items():
    # opp_face_vtx_a = part_data_pld['FaceVtx'][0][face_offset[interface[0]]:face_offset[interface[0]+1]]
    # opp_face_vtx_b = part_data_pld['FaceVtx'][0][face_offset[interface[1]]:face_offset[interface[1]+1]]
    # opp_vtx = np.intersect1d(opp_face_vtx_a, opp_face_vtx_b)
    # assert len(opp_vtx) == 1
    # pl_vtx_local_opp[vtx_g_to_l[vtx[0]]] = opp_vtx[0]
