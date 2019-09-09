import xarray as xr
import numpy as np
import pytest
from xmovie.presets import (
    _check_input,
    _core_plot,
    _smooth_boundary_NearsidePerspective,
)
import matplotlib as mpl
import matplotlib.pyplot as plt
import cartopy.crs as ccrs


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
    if not filled is None:
        assert pp.filled == filled


@pytest.mark.parametrize("lon", [-700, -300, 1, 300, 700])
@pytest.mark.parametrize("lat", [-200, -90, 0, 90, 180])
@pytest.mark.parametrize("sat_height", [35785831, 45785831])
def test_smooth_boundary_NearsidePerspective(lon, lat, sat_height):
    lon = -100
    lat = -40
    sat_height = 35785831
    pr = ccrs.NearsidePerspective(
        central_longitude=lon, central_latitude=lat, satellite_height=sat_height
    )
    # modify the projection with smooth boundary
    pr_mod = _smooth_boundary_NearsidePerspective(pr)

    assert pr.proj4_params == pr_mod.proj4_params
    assert pr.globe == pr_mod.globe
