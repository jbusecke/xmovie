from __future__ import print_function
from future.utils import iteritems

import warnings
import numpy as np
import xarray as xr
import cartopy.crs as ccrs

# from cartopy._crs import WGS84_SEMIMAJOR_AXIS # this import doesnt work?
import cartopy.feature as cfeature
import shapely.geometry as sgeom
import matplotlib.pyplot as plt


def get_plot_defaults(da):
    if isinstance(da, xr.DataArray):
        data = da
    else:
        raise RuntimeError("input of type (%s) not supported" % type(da))
    defaults = dict([])
    defaults["vmin"] = data.min().data
    defaults["vmax"] = data.max().data
    defaults["cbar_kwargs"] = dict(extend="neither")
    # maybe change to
    return defaults


def check_input(da, fieldname):
    # pick the data_var to plot
    if isinstance(da, xr.Dataset):
        if fieldname is None:
            fieldname = list(da.data_vars)[0]
            warnings.warn(
                "No plot_variable supplied. Defaults to `%s`" % fieldname,
                UserWarning,
            )
        data = da[fieldname]
    elif isinstance(da, xr.DataArray):
        data = da
    else:
        raise RuntimeWarning(
            "Data must be xr.DataArray or xr.Dataset \
        (with `fieldname` specified). Datatype found %s"
            % type(da)
        )
    return data


def _core_plot(ax, data, plotmethod=None, **kwargs):
    """Core plotting functionality"""

    #     check kwargs input
    if plotmethod == "contour":
        kwargs.pop("cbar_kwargs", None)

    # I am probably recoding something from matplotlib...is ther a way to get
    # the plot.something functionslity with a keyword?
    # For now do it the hard way
    if plotmethod is None:
        p = data.plot(ax=ax, **kwargs)
    # doesnt work,...i want this for smoother images
    # elif plotmethod == "imshow":
    #     p = data.plot.imshow(ax=ax, **kwargs)
    elif plotmethod == "contour":
        p = data.plot.contour(ax=ax, **kwargs)
    elif plotmethod == "contourf":
        p = data.plot.contourf(ax=ax, **kwargs)
    else:
        raise RuntimeError(
            "Input '%s' not recognized \
        as plotmode"
            % plotmethod
        )
    return p


def _smooth_boundary_NearsidePerspective(
    central_longitude=0.0,
    central_latitude=0.0,
    satellite_height=35785831,
    false_easting=0,
    false_northing=0,
    globe=None,
):
    proj = ccrs.NearsidePerspective(
        central_longitude=central_longitude,
        central_latitude=central_latitude,
        satellite_height=satellite_height,
        false_easting=false_easting,
        false_northing=false_northing,
        globe=globe,
    )

    # workaround for a smoother outer boundary
    # (https://github.com/SciTools/cartopy/issues/613)

    # Re-implement the cartopy code to figure out the boundary.

    # This is just really a guess....
    WGS84_SEMIMAJOR_AXIS = 6378137.0
    # because I cannot import it above...this should be fixed upstream
    # anyways...

    a = proj.globe.semimajor_axis or WGS84_SEMIMAJOR_AXIS
    h = np.float(satellite_height)
    max_x = a * np.sqrt(h / (2 * a + h))
    coords = ccrs._ellipse_boundary(
        max_x, max_x, false_easting, false_northing, n=361
    )
    proj._boundary = sgeom.LinearRing(coords.T)
    return proj


def _set_bgcolor(fig, ax, pp, fgcolor="0.7", bgcolor="0.1"):
    "Sets the colorscheme for figure, axis and plot object (`pp`)"
    fig.patch.set_facecolor(bgcolor)
    ax.set_facecolor(bgcolor)

    # Use the boundary to blend the edges of the globe into background
    ax.outline_patch.set_edgecolor(bgcolor)
    ax.outline_patch.set_antialiased(True)
    ax.outline_patch.set_linewidth(2)

    try:
        cb = pp.colorbar
    except (AttributeError):
        cb = None

    if cb is not None:
        # COLORBAR
        # set colorbar label plus label color
        cb.set_label(cb.ax.axes.get_ylabel(), color=fgcolor)

        # set colorbar tick color
        cb.ax.yaxis.set_tick_params(color=fgcolor)

        # set colorbar edgecolor
        cb.outline.set_edgecolor(fgcolor)

        # set colorbar ticklabels
        plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color=fgcolor)


def _smooth_boundary_globe(projection):
    # workaround for a smoother outer boundary
    # (https://github.com/SciTools/cartopy/issues/613)

    # Re-implement the cartopy code to figure out the boundary.
    a = np.float(projection.globe.semimajor_axis or 6378137.0)
    b = np.float(projection.globe.semiminor_axis or a)
    coords = ccrs._ellipse_boundary(a * 0.99999, b * 0.99999, n=361)

    # Update the projection's boundary.
    projection._boundary = sgeom.polygon.LinearRing(coords.T)
    return projection


def _base_plot(ax, base_data, timestamp, plotmethod=None, **kwargs):
    # core plot call with updated defaults

    # set sensible defaults for each plotmethod
    plt_kwargs = get_plot_defaults(base_data)

    # update with supplied kwargs and map_style_kwargs
    plt_kwargs.update(kwargs)

    # need to convert time to input variable
    data = base_data.isel(time=timestamp)
    p = _core_plot(ax, data, plotmethod=plotmethod, **plt_kwargs)
    return p


def rotating_globe(
    da,
    fig,
    timestamp,
    framedim="time",
    plotmethod=None,
    plot_variable=None,
    overlay_variables=None,
    lon_start=0,
    lon_rotations=-1,
    lat_start=35,
    lat_rotations=0.05,
    land=False,
    coastline=True,
    **kwargs,
):

    # rotate lon_rotations times throughout movie and start at lon_start
    lon = np.linspace(0, 360 * lon_rotations, len(da.time)) + lon_start
    # Same for lat
    lat = np.linspace(0, 360 * lat_rotations, len(da.time)) + lat_start

    proj = ccrs.Orthographic(lon[timestamp], lat[timestamp])

    proj = _smooth_boundary_globe(proj)

    subplot_kw = dict(projection=proj)
    # create axis
    ax = fig.subplots(subplot_kw=subplot_kw)

    # mapping style kwargs
    map_style_kwargs = dict(transform=ccrs.PlateCarree())
    kwargs.update(map_style_kwargs)

    data = check_input(da, plot_variable)

    _base_plot(ax, data, timestamp, plotmethod=plotmethod, **kwargs)
    ax.set_title("")
    ax.set_global()
    # the order should be optional? (I can pass z_order for each...)
    if land:
        feature = cfeature.NaturalEarthFeature(
            name="land", category="physical", scale="50m", facecolor="0.2"
        )
        ax.add_feature(feature)

    if coastline:
        feature = cfeature.NaturalEarthFeature(
            name="coastline",
            category="physical",
            scale="50m",
            edgecolor="0.3",
            facecolor="none",
        )
        ax.add_feature(feature)
    gl = ax.gridlines()
    # Increase gridline res
    gl.n_steps = 500
    # need a way to do that for the outline too

    # possibly for future versions, but I need a way to increase results
    # ax.outline_patch.set_visible(False)


def rotating_globe_dark(
    da,
    fig,
    timestamp,
    framedim="time",
    plotmethod=None,
    plot_variable=None,
    overlay_variables=None,
    lon_start=-10,
    lon_rotations=-0.5,
    lat_start=15,
    lat_rotations=0.05,
    land=False,
    coastline=True,
    **kwargs,
):

    # split kwargs out
    # title = kwargs.pop("title", "")

    # rotate lon_rotations times throughout movie and start at lon_start
    lon = np.linspace(0, 360 * lon_rotations, len(da.time)) + lon_start
    # Same for lat
    lat = np.linspace(0, 360 * lat_rotations, len(da.time)) + lat_start

    projection = _smooth_boundary_NearsidePerspective(
        lon[timestamp], lat[timestamp]
    )
    # projection = ccrs.NearsidePerspective(lon[timestamp], lat[timestamp])

    subplot_kw = dict(projection=projection)
    # create axis
    ax = fig.subplots(subplot_kw=subplot_kw)

    # mapping style kwargs
    map_style_kwargs = dict(transform=ccrs.PlateCarree())
    kwargs.update(map_style_kwargs)
    data = check_input(da, plot_variable)

    # the order should be optional? (I can pass z_order for each...)
    if land:
        feature = cfeature.NaturalEarthFeature(
            name="land", category="physical", scale="50m", facecolor="0.2"
        )
        ax.add_feature(feature)

    if coastline:
        feature = cfeature.NaturalEarthFeature(
            name="coastline",
            category="physical",
            scale="50m",
            edgecolor="0.3",
            facecolor="none",
        )
        ax.add_feature(feature)

    ax.background_patch.set_facecolor("k")

    pp = _base_plot(ax, data, timestamp, plotmethod=plotmethod, **kwargs)

    _set_bgcolor(fig, ax, pp)
    ax.set_global()
    # TODO: I need to figure out how to allow a title...
    # but that will flicker like crazy
    # ax.set_title(title)
    ax.set_title("")
