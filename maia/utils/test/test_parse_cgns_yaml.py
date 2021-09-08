import os
import pytest
import re
import fnmatch
import numpy as np
from Converter import Internal as CI
from maia.sids import Internal_ext as IE
from maia.sids.cgns_keywords import Label as CGL

from maia.utils import parse_yaml_cgns
from maia.utils import parse_cgns_yaml

dir_path = os.path.dirname(os.path.realpath(__file__))

def test_parse_cgns_yaml():
  with open(os.path.join(dir_path, "cubeU_join_bnd-ref.yaml"), 'r') as f:
    yt0 = f.read()
  # print(f"yt0 = {yt0}")
  t = parse_yaml_cgns.to_cgns_tree(yt0)
  CI.printTree(t)
  lines = parse_cgns_yaml.to_yaml(t)
  # for l in lines:
  #   print(f"l: {l}")
  yt1 = '\n'.join(lines)
  with open("cubeU_join_bnd-run.yaml", "w") as f:
    f.write(yt1)
  assert(yt0 == yt1)
