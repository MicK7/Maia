import pytest
import os
from pytest_check import *
from mpi4py import MPI
import sys

from pytest_mpi_check import assert_mpi


# https://stackoverflow.com/questions/59577426/how-to-rename-the-title-of-the-html-report-generated-by-pytest-html-plug-in
@pytest.hookimpl(tryfirst=True)
def pytest_configure(config):

  comm = MPI.COMM_WORLD
  if comm.Get_rank() == 0:
    if not os.path.exists('reports'):
      os.makedirs('reports')
    if not os.path.exists('reports/assets'):
      os.makedirs('reports/assets')
  comm.barrier()

  config.option.htmlpath = 'reports/' + "report_unit_test_{0}.html".format(comm.rank)
  config.option.xmlpath  = 'reports/' + "report_unit_test_{0}.xml" .format(comm.rank)

  pytest.assert_mpi = assert_mpi

@pytest.hookimpl(hookwrapper=True)
def pytest_runtest_makereport(item, call):

  pytest_html = item.config.pluginmanager.getplugin('html')
  outcome = yield
  report = outcome.get_result()
  extra = getattr(report, 'extra', [])
  if report.when == 'call':
    # always add url to report
    extra.append(pytest_html.extras.url('http://www.example.com/'))
    xfail = hasattr(report, 'wasxfail')
    if (report.skipped and xfail) or (report.failed and not xfail):
      # only add additional html on failure
      extra.append(pytest_html.extras.html('<div>Additional HTML</div>'))
    report.extra = extra
