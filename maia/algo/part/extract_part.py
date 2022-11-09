# =======================================================================================
# ---------------------------------------------------------------------------------------
from    mpi4py import MPI
import  numpy as np

import  maia.pytree as PT
import  maia
from    maia.transfer import utils                as TEU
from    maia.factory  import dist_from_part
from    maia.utils    import np_utils, layouts, py_utils
# from    maia.pytree.sids            import node_inspect       as sids
# from    maia.pytree.maia            import conventions        as conv
# from    maia.transfer.part_to_dist  import data_exchange      as PTD

import Pypdm.Pypdm as PDM
# ---------------------------------------------------------------------------------------
# =======================================================================================



# =======================================================================================
# ---------------------------------------------------------------------------------------
class Extractor:
  def __init__( self,
                part_tree, point_list, location, comm,
                equilibrate=1,
                graph_part_tool="hilbert"):

    self.part_tree        = part_tree
    self.point_list       = point_list
    self.location         = location
    self.equilibrate      = equilibrate
    self.graph_part_tool  = graph_part_tool
    self.exch_tool_box    = list()

    # Get zones by domains
    part_tree_per_dom = dist_from_part.get_parts_per_blocks(part_tree, comm).values()

    # Check : monodomain
    assert(len(part_tree_per_dom)==1)

    # Is there PE node
    if (PT.get_node_from_name(part_tree,'ParentElements') is not None): self.put_pe = True
    else                                                              : self.put_pe = False
    
    # ExtractPart dimension
    select_dim  = { 'Vertex':0 ,'EdgeCenter':1 ,'FaceCenter':2 ,'CellCenter':3}
    assert self.location in select_dim.keys()
    self.dim    = select_dim[self.location]
    assert self.dim in [0,2,3],"[MAIA] Error : dimensions 0 and 1 not yet implemented"
    
    # ExtractPart CGNSTree
    self.extract_part_tree = PT.new_CGNSTree()
    self.extract_part_base = PT.new_CGNSBase('Base', cell_dim=self.dim, phy_dim=3, parent=self.extract_part_tree)

    # Compute extract part of each domain
    for i_domain, part_zones in enumerate(part_tree_per_dom):
      
      # extract part from point list
      extract_part_zone,etb = extract_part_one_domain(part_zones, self.point_list, self.dim, comm,
                                                         equilibrate=self.equilibrate,
                                                         graph_part_tool=self.graph_part_tool,
                                                         put_pe=self.put_pe)
      self.exch_tool_box.append(etb)
      PT.add_child(self.extract_part_base, extract_part_zone)
# ---------------------------------------------------------------------------------------
  

# ---------------------------------------------------------------------------------------
  def exchange_fields(self, fs_container, comm) :
    _exchange_field(self.part_tree, self.extract_part_tree, self.exch_tool_box, fs_container, comm)
    return None
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
  def save_parent_num(self) :
    # Possible to get parent_num from p2p or only from pdm_ep ?
    return None
# ---------------------------------------------------------------------------------------
  
# ---------------------------------------------------------------------------------------
# =======================================================================================




# =======================================================================================
# ---------------------------------------------------------------------------------------
def exchange_field_one_domain(part_zones, part_zone_ep, exch_tool_box, exchange, comm) :
  
  # Part 1 : EXTRACT_PART
  # Part 2 : VOLUME
  for container_name in exchange :
    print("\n================================\ncontainer_name = ",container_name)

    # --- Get all fields names and location ---------------------------------------------
    all_fld_names   = list()
    all_locs        = list()
    all_labels      = list()
    all_ordering    = list()
    all_stride_int  = list()
    all_stride_bool = list()
    all_part_gnum1  = list()
    for part_zone in part_zones:
      container   = PT.request_child_from_name(part_zone, container_name)
      fld_names   = {PT.get_name(n) for n in PT.iter_children_from_label(container, "DataArray_t")}
      py_utils.append_unique(all_fld_names, fld_names)
      py_utils.append_unique(all_locs     , PT.Subset.GridLocation(container))
      py_utils.append_unique(all_labels   , PT.get_label(container))
    if len(part_zones) > 0:
      assert len(all_labels) == len(all_locs) == len(all_fld_names) == 1
      tag = comm.Get_rank()
      loc_and_fields = all_locs[0], list(all_fld_names[0])
    else:
      tag = -1
      loc_and_fields = None
    master = comm.allreduce(tag, op=MPI.MAX) # No check global ?
    gridLocation, flds_in_container_names = comm.bcast(loc_and_fields, master)
    assert(gridLocation in ['Vertex','CellCenter'])
    assert(all_labels[0]in ['FlowSolution_t','ZoneSubRegion_t'])

    

    # --- Get PTP by location -----------------------------------------------------------
    ptp     = exch_tool_box['part_to_part']
    ptp_loc = ptp[gridLocation]
    
    # --- Get parent_elt by location -----------------------------------------------------------
    parent_elt     = exch_tool_box['parent_elt']
    parent_elt_loc = parent_elt[gridLocation]
    


    # Get reordering informations if point_list
    # https://stackoverflow.com/questions/8251541/numpy-for-every-element-in-one-array-find-the-index-in-another-array
    for i_part,part_zone in enumerate(part_zones):
      container   = PT.request_child_from_name(part_zone, container_name)
      point_list_node  = PT.get_child_from_label(container,'IndexArray_t')
      if point_list_node is not None :
        print("\ni_part    = ", i_part)
        
        part_gnum1  = ptp_loc.get_gnum1_come_from()[i_part]['come_from'] # Get partition order
        ref_lnum2   = ptp_loc.get_referenced_lnum2()[i_part] # Get partition order
        point_list  = PT.get_value(point_list_node)[0]
        # print("part_gnum1    = ", part_gnum1)
        # print("ref_lnum2     = ", ref_lnum2.shape)
        # print("point_list    = ", point_list.shape)
        # print("ref_lnum2.shap= ", ref_lnum2.shape)

        # great_field = point_list*-1.
        
        common = np.intersect1d(point_list,ref_lnum2)
        # print('common = ',common)

        sort_idx    = np.argsort(point_list)                 # Sort order of point_list ()
        order       = np.searchsorted(point_list,ref_lnum2,sorter=sort_idx)


        ref_lnum2_idx = np.take(sort_idx, order, mode="clip")
        # print("\n ref_lnum2_idx = ", ref_lnum2_idx)

        stride = point_list[ref_lnum2_idx] == ref_lnum2
        # print('stride        = ',stride.astype(np.int32))


        # print("point_list[ref_lnum2_idx][stride] =",point_list[ref_lnum2_idx][stride])
        # print(great_field[ref_lnum2_idx][stride])
        
        # print("np.max(ref_lnum2_idx) =",np.max(ref_lnum2_idx))
        all_ordering.append(ref_lnum2_idx)
        all_stride_bool.append(stride)
        all_stride_int.append(stride.astype(np.int32))
        all_part_gnum1.append(part_gnum1[stride]) # Select only part1_gnum that is in part2 point_list
        # all_new_pl.append(stride.astype(np.new_point_list))


    # --- FlowSolution node def by zone -------------------------------------------------
    # try :
    FS_ep = PT.new_FlowSolution(container_name, loc=gridLocation, parent=part_zone_ep)
    # Echange gnum to retrieve flowsol new point_list

    req_id = ptp_loc.reverse_iexch( PDM._PDM_MPI_COMM_KIND_P2P,
                                    # PDM._PDM_PART_TO_PART_DATA_DEF_ORDER_PART1_TO_PART2,
                                    PDM._PDM_PART_TO_PART_DATA_DEF_ORDER_GNUM1_COME_FROM,
                                    all_part_gnum1,
                                    part2_stride=all_stride_int)
    part1_strid, part2_gnum = ptp_loc.reverse_wait(req_id)
    # print('\n')
    # print('part2_gnum     = ', part2_gnum[0])
    # print('parent_elt_loc = ', parent_elt_loc)
    # print('common         = ', np.intersect1d(part2_gnum[0],parent_elt_loc))
    sort_idx       = np.argsort(part2_gnum[0])                 # Sort order of point_list ()
    order          = np.searchsorted(part2_gnum[0],parent_elt_loc,sorter=sort_idx)
    parent_elt_idx = np.take(sort_idx, order, mode="clip")
    stride         = part2_gnum[0][parent_elt_idx] == parent_elt_loc
    # print(stride)
    new_point_list = np.where(stride)[0]
    # print('new_point_list         = ', new_point_list)
    # print('parent_elt_loc         = ', parent_elt_loc[new_point_list])
    PT.new_PointList(name='PointList', value=new_point_list+1, parent=FS_ep)
    # print('stride                 = ', stride.astype(np.int32))
    # print('parent_elt_idx         = ', parent_elt_idx)
    # print('parent_elt_idx[stride] = ', parent_elt_idx[stride])

    # except :
    #   FS_ep = PT.get_node_from_name(part_zone_ep,container_name)

    import Converter.Internal as I
    I.printTree(FS_ep)



    # --- Field exchange ----------------------------------------------------------------
    for fld_name in flds_in_container_names:
      print("\nfld_name = ",fld_name)
      fld_path = f"{container_name}/{fld_name}"
      
      # Reordering if ZSR container
      if (all_labels[0]=="ZoneSubRegion_t"): 
        # print("fld_data.shape   = ",[PT.get_node_from_path(part_zone,fld_path)[1].shape for i_part,part_zone in enumerate(part_zones)])
        # print("all_ordering.max = ",[np.max(all_ordering[i_part]) for i_part,part_zone in enumerate(part_zones)])
        fld_data = [PT.get_node_from_path(part_zone,fld_path)[1][all_ordering[i_part]][all_stride_bool[i_part]] 
                    for i_part,part_zone in enumerate(part_zones)]
        # print("fld_data = ",fld_data)
        # print("len(all_stride) = ",len(all_stride))
        # print("all_stride[0].shape = ",all_stride[0].shape)
        # print("all_stride[0].flags = ",all_stride[0].flags)
        req_id = ptp_loc.reverse_iexch( PDM._PDM_MPI_COMM_KIND_P2P,
                                        # PDM._PDM_PART_TO_PART_DATA_DEF_ORDER_PART1_TO_PART2,
                                        PDM._PDM_PART_TO_PART_DATA_DEF_ORDER_GNUM1_COME_FROM,
                                        fld_data,
                                        part2_stride=all_stride_int)
      else :
        fld_data = [PT.get_node_from_path(part_zone,fld_path)[1]
                    for part_zone in part_zones]
        req_id = ptp_loc.reverse_iexch( PDM._PDM_MPI_COMM_KIND_P2P,
                                        PDM._PDM_PART_TO_PART_DATA_DEF_ORDER_PART2,
                                        fld_data,
                                        part2_stride=1)

      part1_strid, part1_data = ptp_loc.reverse_wait(req_id)

      # print('part1_data = ',part1_data[0].astype(np.int32))
      # Interpolation and placement
      i_part = 0
      PT.new_DataArray(fld_name, part1_data[i_part], parent=FS_ep)
      
# ---------------------------------------------------------------------------------------
# ---------------------------------------------------------------------------------------

def _exchange_field(part_tree, part_tree_ep, ptp,exchange, comm) :
  """
  Exchange field between part_tree and part_tree_ep
  for exchange vol field 
  """

  # Get zones by domains
  part_tree_per_dom = dist_from_part.get_parts_per_blocks(part_tree, comm).values()

  # Check : monodomain
  assert(len(part_tree_per_dom)==1)
  assert(len(part_tree_per_dom)==len(ptp))

  # Get zone from extractpart
  part_zone_ep = PT.get_all_Zone_t(part_tree_ep)
  assert(len(part_zone_ep)<=1)
  part_zone_ep = part_zone_ep[0]

  # Loop over domains
  for i_domain, part_zones in enumerate(part_tree_per_dom):
    exchange_field_one_domain(part_zones, part_zone_ep, ptp[i_domain], exchange, comm)

# ---------------------------------------------------------------------------------------
# =======================================================================================





# =======================================================================================
# ---------------------------------------------------------------------------------------
def extract_part_one_domain(part_zones, point_list, dim, comm,
                            equilibrate=1,
                            graph_part_tool="hilbert",
                            put_pe=False):
  """
  TODO : AJOUTER LE CHOIX PARTIONNEMENT
  """
  n_part = len(part_zones)
  # print(n_par)
  pdm_ep = PDM.ExtractPart(dim, # face/cells
                           n_part,
                           1, # n_part_out
                           equilibrate,
                           eval(f"PDM._PDM_SPLIT_DUAL_WITH_{graph_part_tool.upper()}"),
                           True,
                           comm)
  # Loop over domain zone : preparing extract part
  adjusted_point_list = list()
  for i_part, part_zone in enumerate(part_zones):
    # Get NGon + NFac
    cx, cy, cz = PT.Zone.coordinates(part_zone)
    vtx_coords = np_utils.interweave_arrays([cx,cy,cz])
    
    ngon  = PT.Zone.NGonNode(part_zone)
    nface = PT.Zone.NFaceNode(part_zone)

    cell_face_idx = PT.get_child_from_name(nface, "ElementStartOffset" )[1]
    cell_face     = PT.get_child_from_name(nface, "ElementConnectivity")[1]
    face_vtx_idx  = PT.get_child_from_name(ngon,  "ElementStartOffset" )[1]
    face_vtx      = PT.get_child_from_name(ngon,  "ElementConnectivity")[1]

    vtx_ln_to_gn, face_ln_to_gn, cell_ln_to_gn = TEU.get_entities_numbering(part_zone)

    # n_cell = cell_ln_to_gn.shape[0]
    n_cell = cell_ln_to_gn.shape[0]
    n_face = face_ln_to_gn.shape[0]
    n_edge = 0
    n_vtx  = vtx_ln_to_gn .shape[0]

    pdm_ep.part_set(i_part,
                    n_cell,
                    n_face,
                    n_edge,
                    n_vtx,
                    cell_face_idx,
                    cell_face    ,
                    None,
                    None,
                    None,
                    face_vtx_idx ,
                    face_vtx     ,
                    cell_ln_to_gn,
                    face_ln_to_gn,
                    None,
                    vtx_ln_to_gn ,
                    vtx_coords)
    # if (comm.Get_rank()==2):
    #   print("point_list[i_part]   = ",point_list[i_part]  )
    #   print("point_list[i_part]-1 = ",point_list[i_part]-1)
    # print(f"[MAIA] point_list[{i_part}].shape[0] = {point_list[i_part].shape[0]}")
    # print(f"[MAIA] point_list[{i_part}].flags = {point_list[i_part].flags}")
    # adjusted_point_list = point_list[i_part] - np.ones(point_list[i_part].shape[0],dtype=np.int32) # -1 because of CGNS norm

    adjusted_point_list.append(point_list[i_part] - 1) # -1 because of CGNS norm


    # if (comm.Get_rank()==0):
    #   print(f"i_part = {i_part} ; point_list[i_part]=",point_list[i_part])

  # print("[MAIA] BEGIN compute extract_part")
  pdm_ep.compute()
  # print("[MAIA] ENDOF compute extract_part")


  # > Reconstruction du maillage de l'extract part --------------------------------------
  n_extract_cell = pdm_ep.n_entity_get(0, PDM._PDM_MESH_ENTITY_CELL  ) #; print(f'[{comm.Get_rank()}][MAIA] n_extract_cell = {n_extract_cell}')
  n_extract_face = pdm_ep.n_entity_get(0, PDM._PDM_MESH_ENTITY_FACE  ) #; print(f'[{comm.Get_rank()}][MAIA] n_extract_face = {n_extract_face}')
  n_extract_edge = pdm_ep.n_entity_get(0, PDM._PDM_MESH_ENTITY_EDGE  ) #; print(f'[{comm.Get_rank()}][MAIA] n_extract_edge = {n_extract_edge}')
  n_extract_vtx  = pdm_ep.n_entity_get(0, PDM._PDM_MESH_ENTITY_VERTEX) #; print(f'[{comm.Get_rank()}][MAIA] n_extract_vtx  = {n_extract_vtx }')
  

  extract_vtx_coords = pdm_ep.vtx_coord_get(0)
  
  size_by_dim = {0: [[n_extract_vtx, 0             , 0]], # not yet implemented
                 1:   None                              , # not yet implemented
                 2: [[n_extract_vtx, n_extract_face, 0]],
                 3: [[n_extract_vtx, n_extract_cell, 0]] }


  # --- ExtractPart zone construction ---------------------------------------------------
  extract_part_zone = PT.new_Zone(PT.maia.conv.add_part_suffix('Zone', comm.Get_rank(), 0),
                                  size=size_by_dim[dim],
                                  type='Unstructured')

  # > Grid coordinates
  cx, cy, cz = layouts.interlaced_to_tuple_coords(extract_vtx_coords)
  extract_grid_coord = PT.new_GridCoordinates(parent=extract_part_zone)
  PT.new_DataArray('CoordinateX', cx, parent=extract_grid_coord)
  PT.new_DataArray('CoordinateY', cy, parent=extract_grid_coord)
  PT.new_DataArray('CoordinateZ', cz, parent=extract_grid_coord)

  # > NGON
  if (dim>=2) :
    ep_face_vtx_idx, ep_face_vtx  = pdm_ep.connectivity_get(0, PDM._PDM_CONNECTIVITY_TYPE_FACE_VTX)
    ngon_n = PT.new_NGonElements( 'NGonElements',
                                  erange  = [1, n_extract_face],
                                  ec      = ep_face_vtx,
                                  eso     = ep_face_vtx_idx,
                                  parent  = extract_part_zone)
  # > NFACES
  if (dim==3) :
    ep_cell_face_idx, ep_cell_face = pdm_ep.connectivity_get(0, PDM._PDM_CONNECTIVITY_TYPE_CELL_FACE)
    nface_n = PT.new_NFaceElements('NFaceElements',
                                    erange  = [n_extract_face+1, n_extract_face+n_extract_cell],
                                    ec      = ep_cell_face,
                                    eso     = ep_cell_face_idx,
                                    parent  = extract_part_zone)

    # Compute ParentElement nodes is requested
    if (put_pe):
      maia.algo.nface_to_pe(extract_part_zone, comm)

    
  # > LN_TO_GN nodes
  ep_vtx_ln_to_gn  = None
  ep_face_ln_to_gn = None
  ep_cell_ln_to_gn = None

  ep_vtx_ln_to_gn  = pdm_ep.ln_to_gn_get(0,PDM._PDM_MESH_ENTITY_VERTEX)

  if (dim>=2) : # NGON
    ep_face_ln_to_gn = pdm_ep.ln_to_gn_get(0,PDM._PDM_MESH_ENTITY_FACE)
    PT.maia.newGlobalNumbering({'Element' : ep_face_ln_to_gn}, parent=ngon_n)
    
  if (dim==3) : # NFACE
    ep_cell_ln_to_gn = pdm_ep.ln_to_gn_get(0,PDM._PDM_MESH_ENTITY_CELL)
    PT.maia.newGlobalNumbering({'Element' : ep_cell_ln_to_gn}, parent=nface_n)

  ln_to_gn_by_dim = { 0: {'Cell': ep_vtx_ln_to_gn },
                      1:   None,                                                  # not yet implemented
                      2: {'Vertex': ep_vtx_ln_to_gn , 'Cell': ep_face_ln_to_gn },
                      3: {'Vertex': ep_vtx_ln_to_gn , 'Cell': ep_cell_ln_to_gn } }
  PT.maia.newGlobalNumbering(ln_to_gn_by_dim[dim], parent=extract_part_zone)

  # - Get PTP by vertex and cell
  ptp = dict()
  ptp['Vertex']       = pdm_ep.part_to_part_get(PDM._PDM_MESH_ENTITY_VERTEX)
  if (dim>=2) : # NGON
    ptp['FaceCenter'] = pdm_ep.part_to_part_get(PDM._PDM_MESH_ENTITY_FACE)
  if (dim==3) : # NFACE
    ptp['CellCenter'] = pdm_ep.part_to_part_get(PDM._PDM_MESH_ENTITY_CELL)
  
  # - Get parent elt
  parent_elt = dict()
  parent_elt['Vertex']       = pdm_ep.parent_ln_to_gn_get(0,PDM._PDM_MESH_ENTITY_VERTEX)
  if (dim>=2) : # NGON
    parent_elt['FaceCenter'] = pdm_ep.parent_ln_to_gn_get(0,PDM._PDM_MESH_ENTITY_FACE)
  if (dim==3) : # NFACE
    parent_elt['CellCenter'] = pdm_ep.parent_ln_to_gn_get(0,PDM._PDM_MESH_ENTITY_CELL)
  # Placement in Extract_part_Tree
  parent_node    = PT.new_node('maia#parents', label='UserDefinedData_t', parent=extract_part_zone)
  PT.new_DataArray('Cell_parent'  , parent_elt['CellCenter']  , parent=parent_node)
  PT.new_DataArray('Vertex_parent', parent_elt['Vertex'], parent=parent_node)

  exch_tool_box = dict()
  exch_tool_box['part_to_part'] = ptp
  exch_tool_box['parent_elt'  ] = parent_elt


  return extract_part_zone, exch_tool_box
# ---------------------------------------------------------------------------------------
# =======================================================================================



# =======================================================================================
# ---------------------------------------------------------------------------------------
def extract_part_from_point_list(part_tree, point_list, location, comm, equilibrate=1, exchange=None, graph_part_tool='hilbert'):
  """Extract vertex/edges/faces/cells from the ZSR node from the provided partitioned CGNSTree.

  ExtractPart is returned as an independant partitioned CGNSTree. 

  Important:
    - Input tree must be unstructured and have a ngon connectivity.
    - Partitions must come from a single initial domain on input tree.

  Note:
    Once created, fields from provided partitionned CGNSTree
    can be exchanged using
    ``_exchange_field(part_tree, iso_part_tree, containers_name, comm)``

  Args:
    part_tree     (CGNSTree)    : Partitioned tree from which ExtractPart is computed. Only U-NGon
      connectivities are managed.
    iso_field     (str)         : Path to the ZSR field.
    comm          (MPIComm)     : MPI communicator
    iso_val       (float, optional) : Value to use to compute isosurface. Defaults to 0.
    containers_name   (list of str) : List of the names of the FlowSolution_t nodes to transfer
      on the output isosurface tree.
    **options: Options related to plane extraction.
  Returns:
    isosurf_tree (CGNSTree): Surfacic tree (partitioned)

  Extraction can be controled thought the optional kwargs:

    - ``elt_type`` (str) -- Controls the shape of elements used to describe
      the isosurface. Admissible values are ``TRI_3, QUAD_4, NGON_n``. Defaults to ``TRI_3``.

  Example:
    .. literalinclude:: snippets/test_algo.py
      :start-after: #compute_iso_surface@start
      :end-before: #compute_iso_surface@end
      :dedent: 2
  """

  # Get zones by domains
  part_tree_per_dom = dist_from_part.get_parts_per_blocks(part_tree, comm).values()

  # Check : monodomain
  assert(len(part_tree_per_dom)==1)

  # Is there PE node
  if (PT.get_node_from_name(part_tree,'ParentElements') is not None): put_pe = True
  else                                                              : put_pe = False
  
  # ExtractPart dimension
  select_dim  = { 'Vertex':0 ,'EdgeCenter':1 ,'FaceCenter':2 ,'CellCenter':3}
  dim         = select_dim[location]
  assert dim in [0,2,3],"[MAIA] Error : dimensions 0 and 1 not yet implemented"
  
  # ExtractPart CGNSTree
  extract_part_tree = PT.new_CGNSTree()
  extract_part_base = PT.new_CGNSBase('Base', cell_dim=dim, phy_dim=3, parent=extract_part_tree)


  # Compute extract part of each domain
  # pdm_ep=list()
  exch_tool_box = list()
  for i_domain, part_zones in enumerate(part_tree_per_dom):
    extract_part_zone,etb = extract_part_one_domain(part_zones, point_list, dim, comm,
                                                    equilibrate=equilibrate,
                                                    graph_part_tool=graph_part_tool,
                                                    put_pe=put_pe)
    exch_tool_box.append(etb)
    PT.add_child(extract_part_base, extract_part_zone)

  # Exchange fields between two parts
  if exchange is not None:
    _exchange_field(part_tree, extract_part_tree, exch_tool_box, exchange, comm)
  

  return extract_part_tree
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
def create_extractor_from_point_list(part_tree, point_list, location, comm, equilibrate=1, graph_part_tool='hilbert'):

  return Extractor(part_tree, point_list, location, comm,
                   equilibrate=equilibrate,
                   graph_part_tool=graph_part_tool)
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# =======================================================================================





# =======================================================================================
# --- EXTRACT PART FROM ZSR -------------------------------------------------------------

# ---------------------------------------------------------------------------------------
def extract_part_from_zsr(part_tree, zsr_path, comm,
                          equilibrate=1, exchange=None, graph_part_tool='hilbert'):

  # Get zones by domains
  part_tree_per_dom = dist_from_part.get_parts_per_blocks(part_tree, comm).values()

  # Check : monodomain
  assert(len(part_tree_per_dom)==1)

  # Is there PE node
  if (PT.get_node_from_name(part_tree,'ParentElements') is not None): put_pe = True
  else                                                              : put_pe = False
  
  # ExtractPart dimension
  select_dim  = { 'Vertex':0 ,'EdgeCenter':1 ,'FaceCenter':2 ,'CellCenter':3}
  ZSR_node    = PT.get_node_from_name(part_tree,zsr_path)
  assert ZSR_node is not None 
  dim         = select_dim[PT.get_value(PT.get_child_from_name(ZSR_node,'GridLocation'))]
  assert dim in [0,2,3],"[MAIA] Error : dimensions 0 and 1 not yet implemented"
  
  # ExtractPart CGNSTree
  extract_part_tree = PT.new_CGNSTree()
  extract_part_base = PT.new_CGNSBase('Base', cell_dim=dim, phy_dim=3, parent=extract_part_tree)


  # Compute extract part of each domain
  # pdm_ep=list()
  exch_tool_box   =list()
  for i_domain, part_zones in enumerate(part_tree_per_dom):
    
    # Get point_list for each partitioned zone in the domain
    point_list = list()
    for part_zone in part_zones:
      # Get point_list from zsr node
      zsr_node    = PT.get_node_from_path(part_zone, zsr_path)
      zsr_pl_node = PT.get_child_from_name(zsr_node, "PointList")
      point_list.append(PT.get_value(zsr_pl_node)[0])

    # extract part from point list
    extract_part_zone,etb = extract_part_one_domain(part_zones, point_list, dim, comm,
                                                       equilibrate=equilibrate,
                                                       graph_part_tool=graph_part_tool,
                                                       put_pe=put_pe)
    exch_tool_box.append(etb)
    PT.add_child(extract_part_base, extract_part_zone)

  # exchange_zsr_fields(part_tree, extract_part_tree, zsr_path, exch_tool_box, comm)  

  # Exchange fields between two parts
  if exchange is None         : exchange = list()
  if zsr_path not in exchange : exchange.append(zsr_path)

  if exchange is not None:
    _exchange_field(part_tree, extract_part_tree, exch_tool_box, exchange, comm)
  

  return extract_part_tree
# ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
def create_extractor_from_zsr(part_tree, zsr_path, comm, equilibrate=1, graph_part_tool='hilbert'):

  # Get zones by domains
  part_tree_per_dom = dist_from_part.get_parts_per_blocks(part_tree, comm).values()
  assert(len(part_tree_per_dom)==1)

  # zsr node and location
  ZSR_node    = PT.get_node_from_name(part_tree,zsr_path)
  assert ZSR_node is not None 
  location    = PT.get_value(PT.get_child_from_name(ZSR_node,'GridLocation'))

  # Get point_list or each partitioned zone
  for i_domain, part_zones in enumerate(part_tree_per_dom):
    point_list = list()
    for part_zone in part_zones:
      # Get point_list from zsr node
      zsr_node    = PT.get_node_from_path(part_zone, zsr_path)
      zsr_pl_node = PT.get_child_from_name(zsr_node, "PointList")
      point_list.append(PT.get_value(zsr_pl_node)[0])

  return Extractor(part_tree, point_list, location, comm,
                   equilibrate=equilibrate,
                   graph_part_tool=graph_part_tool)
# ---------------------------------------------------------------------------------------

# --- END EXTRACT PART FROM ZSR ---------------------------------------------------------
# =======================================================================================







# =======================================================================================
# ---------------------------------------------------------------------------------------
# # ---------------------------------------------------------------------------------------
# def extract_part_from_bnd():
#   return extract_part_tree

# def create_extractor_from_bnd():
#   # get point list
#   return Extractor
# # ---------------------------------------------------------------------------------------


# ---------------------------------------------------------------------------------------
# =======================================================================================

