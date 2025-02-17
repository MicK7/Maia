import pytest
from   pytest_mpi_check._decorator import mark_mpi_test
import numpy as np

import maia.pytree as PT

import maia

from maia.algo.part import connectivity_utils as CU

def as_partitioned(zone):
  #TODO : factorize me
  PT.rm_nodes_from_name(zone, ":CGNS#Distribution")
  predicate = lambda n : PT.get_label(n) in ['Zone_t', 'DataArray_t', 'IndexArray_t', 'IndexRange_t'] \
      and PT.get_value(n).dtype == np.int64
  for array in PT.iter_nodes_from_predicate(zone, predicate, explore='deep'):
    array[1] = array[1].astype(np.int32)


@mark_mpi_test(1)
class Test_cell_vtx_connectivity:

  @pytest.mark.parametrize("elt_kind", ['NFACE_n' ,'Poly'])
  def test_ngon3d(self, elt_kind, sub_comm):
    tree = maia.factory.generate_dist_block(3, elt_kind, sub_comm)
    zone = PT.get_all_Zone_t(tree)[0]
    as_partitioned(zone)
    cell_vtx_idx, cell_vtx = CU.cell_vtx_connectivity(zone)
    expected_cell_vtx = np.array([1,2,4,5,10,11,13,14,      2,3,5,6,11,12,14,15,  
                                  4,5,7,8,13,14,16,17,      5,6,8,9,14,15,17,18,
                                  10,11,13,14,19,20,22,23,  11,12,14,15,20,21,23,24, 
                                  13,14,16,17,22,23,25,26,  14,15,17,18,23,24,26,27])
    assert cell_vtx_idx.size == 2**3+1
    assert (np.diff(cell_vtx_idx) == 8).all()
    assert (cell_vtx == expected_cell_vtx).all()

  @pytest.mark.parametrize("elt_kind", ['TETRA_4' ,'QUAD_4'])
  def test_elts(self, elt_kind, sub_comm):
    tree = maia.factory.generate_dist_block(3, elt_kind, sub_comm)
    zone = PT.get_all_Zone_t(tree)[0]
    as_partitioned(zone)
    dim_zone = 2 if elt_kind in ['QUAD_4'] else 3

    cell_vtx_idx, cell_vtx = CU.cell_vtx_connectivity(zone, dim_zone)

    elt = PT.get_node_from_label(zone, 'Elements_t')
    assert cell_vtx_idx.size == PT.Element.Size(elt) + 1
    assert (np.diff(cell_vtx_idx) == 4).all()
    assert (cell_vtx == PT.get_node_from_name(elt, 'ElementConnectivity')[1]).all()

  def test_struct(self, sub_comm):
    zone = PT.new_Zone(type='Structured')
    with pytest.raises(NotImplementedError):
      CU.cell_vtx_connectivity(zone)

