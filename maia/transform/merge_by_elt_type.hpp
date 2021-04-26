#pragma once


#include "cpp_cgns/cgns.hpp"
#include "mpi.h"


namespace maia {

auto merge_by_elt_type(cgns::tree& b, MPI_Comm comm) -> void;

} // maia
