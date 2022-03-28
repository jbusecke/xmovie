import importlib

import pytest
from packaging.version import Version


def _importorskip(modname, minversion=None):
    # https://github.com/pydata/xarray/blob/95bb9ae4233c16639682a532c14b26a3ea2728f3/xarray/tests/__init__.py#L43-L53
    try:
        mod = importlib.import_module(modname)
        has = True
        if minversion is not None:
            if Version(mod.__version__) < Version(minversion):
                raise ImportError("Minimum version not satisfied")
    except ImportError:
        has = False
    func = pytest.mark.skipif(not has, reason=f"requires {modname}")
    return has, func


has_cartopy, requires_cartopy = _importorskip("cartopy")
has_dask, requires_dask = _importorskip("dask")
has_dask_array, requires_dask_array = _importorskip("dask.array")
