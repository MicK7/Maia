from mpi4py import MPI
from h5py   import h5p, h5f, h5fd

import maia.pytree as PT

from .hdf._hdf_cgns import open_from_path,\
                           load_tree_partial, write_tree_partial,\
                           load_data_partial, write_data_partial,\
                           write_link
from .fix_tree      import fix_point_ranges, rm_legacy_nodes,\
                           add_missing_pr_in_bcdataset, check_datasize

def load_data(names, labels):
  """ Function used to determine if the data is heavy or not """
  if len(names) == 1: #First level (Base, CGLibVersion, ...) -> always load + early return
    return True
  if labels[-1] == 'IndexArray_t': # PointList -> do not load
    return False
  if labels[-1] == 'DataArray_t': # Arrays -> it depends
    if labels[-2] in ['GridCoordinates_t', 'FlowSolution_t', 'DiscreteData_t', \
        'ZoneSubRegion_t', 'Elements_t']:
      return False
    if names[-2] in [':elsA#Hybrid']: # Do not load legacy nodes
      return False
    if labels[-2] == 'BCData_t' and labels[-3] == 'BCDataSet_t': # Load FamilyBCDataSet, but not BCDataSet
      return False
  return True

def load_collective_size_tree(filename, comm):

  if comm.Get_rank() == 0:
    size_tree = load_tree_partial(filename, load_data)
    rm_legacy_nodes(size_tree)
    check_datasize(size_tree)
    fix_point_ranges(size_tree)
    add_missing_pr_in_bcdataset(size_tree)
  else:
    size_tree = None

  size_tree = comm.bcast(size_tree, root=0)

  return size_tree

def load_partial(filename, dist_tree, hdf_filter):
  fid = h5f.open(bytes(filename, 'utf-8'), h5f.ACC_RDONLY)

  for path, filter in hdf_filter.items():
    if isinstance(filter, (list, tuple)):
      node = PT.get_node_from_path(dist_tree, path[1:]) #! Path has '/'
      gid = open_from_path(fid, path[1:])
      node[1] = load_data_partial(gid, filter)

def write_partial(filename, dist_tree, hdf_filter, comm):

  if comm.Get_rank() == 0:
    write_tree_partial(dist_tree, filename, load_data)
  comm.barrier()

  fapl = h5p.create(h5p.FILE_ACCESS)
  fapl.set_driver(h5fd.MPIO)
  fapl.set_fapl_mpio(comm, MPI.Info())
  fid = h5f.open(bytes(filename, 'utf-8'), h5f.ACC_RDWR, fapl)

  for path, filter in hdf_filter.items():
    array = PT.get_node_from_path(dist_tree, path[1:])[1] #! Path has '/'
    gid = open_from_path(fid, path[1:])
    write_data_partial(gid, array, filter)
    gid.close()
  
  fid.close()

def read_full(filename):
  return load_tree_partial(filename, lambda X,Y: True)

def write_full(filename, dist_tree, links=[]):
  write_tree_partial(dist_tree, filename, lambda X,Y: True)

  # Add links if any
  fid = h5f.open(bytes(filename, 'utf-8'), h5f.ACC_RDWR)
  for link in links:
    target_dir, target_file, target_node, local_node = link
    parent_node_path = PT.path_head(local_node)
    local_node_name  = PT.path_tail(local_node)
    gid = open_from_path(fid, parent_node_path)
    write_link(gid, local_node_name, target_file, target_node)
  fid.close()

