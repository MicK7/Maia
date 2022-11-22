import maia.pytree as PT
from maia.utils.graph import algo_base
from maia.utils.graph.algo_base import step


class adjacency_iterator:
  def __init__(self, ts):
    self.ts = ts

  def __iter__(self):
    self.idx = 0
    return self

  def __next__(self):
    if self.idx < len(self.ts):
      t = self.ts[self.idx]
      self.idx += 1
      return t
    else:
      return None

class pytree_adaptor:
  def __init__(self, t):
    self.t = t

  def children(self, n):
    return adjacency_iterator(PT.get_children(n))
  def roots(self):
    return adjacency_iterator([self.t])


def depth_first_search(t,v):
  return algo_base.depth_first_search(pytree_adaptor(t),v)


def _value_or_none(l, i):
  if i < len(l):
    return l[i]
  else:
    return None

def _zip_lists(ls):
  sz = max(map(len,ls))
  zipped = []
  for i in range(sz):
    zipped.append([_value_or_none(l, i) for l in ls])
  return zipped

def _get_sorted_children(n):
  if n is None:
    return []
  else:
    return sorted(PT.get_children(n))


class pytree_zip_adaptor:
  def __init__(self, ts):
    self.ts = ts

  def children(self, ns):
    sorted_ns = [_get_sorted_children(n) for n in ns]
    cs = _zip_lists(sorted_ns)
    return adjacency_iterator(cs)
  def roots(self):
    return adjacency_iterator([self.ts])


def zip_depth_first_search(t,v):
  return algo_base.depth_first_search(pytree_zip_adaptor(t),v)
