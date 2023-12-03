import cartopy.crs as ccrs
import matplotlib as mpl
import matplotlib.pyplot as plt
import numpy as np
import pytest
import xarray as xr

from xmovie.presets import (
    _check_input,
    _core_plot,
    _smooth_boundary_NearsidePerspective,
)


def test_check_input():
    # this should be done with a more sophisticated example
    ds = xr.Dataset(
        {
            "a": xr.DataArray(np.arange(20), dims=["x"]),
            "b": xr.DataArray(np.arange(4), dims=["y"]),
        }
    )
    xr.testing.assert_identical(ds["a"], _check_input(ds, None))
    xr.testing.assert_identical(ds["b"], _check_input(ds, "b"))
    xr.testing.assert_identical(ds["a"], _check_input(ds["a"], None))
    xr.testing.assert_identical(ds["a"], _check_input(ds["a"], "b"))


@pytest.mark.parametrize(
    "plotmethod, expected_type, filled",
    [
        (None, mpl.collections.QuadMesh, None),
        ("contour", mpl.contour.QuadContourSet, False),
        ("contourf", mpl.contour.QuadContourSet, True),
    ],
)
def test_core_plot(plotmethod, expected_type, filled):
    da = xr.DataArray(np.random.rand(4, 6))
    fig, ax = plt.subplots()
    pp = _core_plot(ax, da, plotmethod=plotmethod)
    assert isinstance(pp, expected_type)
    if filled is not None:
        assert pp.filled == filled
