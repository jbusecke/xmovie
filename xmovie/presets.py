import warnings
import numpy as np
import xarray as xr
from cartopy.mpl import geoaxes
import cartopy.crs as ccrs
import cartopy.feature as cfeature

import shapely.geometry as sgeom
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker


def _check_input(da, fieldname):
    # pick the data_var to plot
    if isinstance(da, xr.Dataset):
        if fieldname is None:
            fieldname = list(da.data_vars)[0]
            warnings.warn(
                "No `fieldname` supplied. Defaults to `%s`" % fieldname, UserWarning
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


# plotting basics
def _core_plot(ax, data, plotmethod=None, **kwargs):
    """Core plotting functionality"""

    # Deactivate cbar for contours (not sure this should be hardcoded...)
    if plotmethod == "contour":
        kwargs.pop("cbar_kwargs", None)

    # I am probably recoding something from matplotlib...is there a way to get
    # the plot.something functionslity with a keyword?
    # For now do it the hard way
    if plotmethod is None:
        p = data.plot(ax=ax, **kwargs)
    # doesnt work,...i want this for smoother images
    elif plotmethod == "imshow":
        # p = data.plot.imshow(ax=ax, **kwargs)
        # testing interpolation
        p = data.plot.imshow(ax=ax, interpolation="gaussian", **kwargs)
        # print(p.get_interpolation())
    elif plotmethod == "pcolormesh":
        p = data.plot.pcolormesh(ax=ax, **kwargs)
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


def _base_plot(ax, base_data, timestamp, framedim, plotmethod=None, **kwargs):
    data = base_data.isel({framedim:timestamp})
    p = _core_plot(ax, data, plotmethod=plotmethod, **kwargs)
    return p


# projections utilities and hacks
def _smooth_boundary_NearsidePerspective(projection):
    # workaround for a smoother outer boundary
    # (https://github.com/SciTools/cartopy/issues/613)
    # Re-implement the cartopy code to figure out the boundary.

    # This is just really a guess....
    WGS84_SEMIMAJOR_AXIS = 6378137.0
    # because I cannot import it above...this should be fixed upstream
    # anyways...

    a = projection.globe.semimajor_axis or WGS84_SEMIMAJOR_AXIS
    h = projection.proj4_params["h"]
    false_easting = projection.proj4_params["x_0"]
    false_northing = projection.proj4_params["y_0"]
    max_x = a * np.sqrt(h / (2 * a + h))
    coords = ccrs._ellipse_boundary(max_x, max_x, false_easting, false_northing, n=361)
    projection._boundary = sgeom.LinearRing(coords.T)
    return projection


# def _smooth_boundary_globe(projection):
#     # workaround for a smoother outer boundary
#     # (https://github.com/SciTools/cartopy/issues/613)
#
#     # Re-implement the cartopy code to figure out the boundary.
#     a = np.float(projection.globe.semimajor_axis or 6378137.0)
#     b = np.float(projection.globe.semiminor_axis or a)
#     coords = ccrs._ellipse_boundary(a * 0.99999, b * 0.99999, n=361)
#
#     # Update the projection's boundary.
#     projection._boundary = sgeom.polygon.LinearRing(coords.T)
#     return projection


# Styling of the plot elements
def _style_dict_raw():
    return {
        "standard": {
            "bgcolor": "1.0",
            "fgcolor": "0.7",
            "blend_outline_patch": False,
            "landcolor": "0.2",
            "coastcolor": "0.3",
        },
        "dark": {
            "bgcolor": "0.1",
            "fgcolor": "0.7",
            "blend_outline_patch": True,
            "landcolor": "0.2",
            "coastcolor": "0.3",
        },
    }


def _style_dict(style=None):
    # set default style
    if style is None:
        style = "standard"
    # define parameters for styles
    style_dict = _style_dict_raw()
    return style_dict[style]


def _set_style(fig, ax, pp, style):
    "Sets the colorscheme for figure, axis and plot object (`pp`) according to style"
    # check if ax is 'normal' or cartopy projection
    is_geoax = False
    if isinstance(ax, geoaxes.GeoAxesSubplot):
        is_geoax = True

    # parse styles
    style_dict = _style_dict(style)
    supported_styles = list(_style_dict_raw().keys())
    if (style not in supported_styles) and (style is not None):
        raise ValueError(
            "Given value for `style`(%s) not supported. \
        Currently support [%s]"
            % (style, supported_styles)
        )
    # can I declare these in an automated fashinon?
    bgcolor = style_dict.pop("bgcolor", None)
    fgcolor = style_dict.pop("fgcolor", None)
    blend_outline_patch = style_dict.pop("blend_outline_patch", None)

    fig.patch.set_facecolor(bgcolor)
    if is_geoax:
        ax.background_patch.set_facecolor(bgcolor)
    else:
        ax.set_facecolor(bgcolor)

    # Use the boundary to blend the edges of the globe into background
    if blend_outline_patch:
        if is_geoax:
            ax.outline_patch.set_edgecolor(bgcolor)
            ax.outline_patch.set_antialiased(True)
            ax.outline_patch.set_linewidth(2)

    # modify colorbar
    try:
        cb = pp.colorbar
    except (AttributeError):
        cb = None

    if cb is not None:
        # set colorbar label plus label color
        cb.set_label(cb.ax.axes.get_ylabel(), color=fgcolor)

        # set colorbar tick color
        cb.ax.yaxis.set_tick_params(color=fgcolor)

        # set colorbar edgecolor
        cb.outline.set_edgecolor(fgcolor)

        # set colorbar ticklabels
        plt.setp(plt.getp(cb.ax.axes, "yticklabels"), color=fgcolor)


def _add_land(ax, style):
    if not isinstance(ax, geoaxes.GeoAxesSubplot):
        raise ValueError("Cannot add land on non-cartopy axes. Got ($s)" % type(ax))
    style_dict = _style_dict(style)
    feature = cfeature.NaturalEarthFeature(
        name="land", category="physical", scale="50m", facecolor=style_dict["landcolor"]
    )
    ax.add_feature(feature)


def _add_coast(ax, style):
    if not isinstance(ax, geoaxes.GeoAxesSubplot):
        raise ValueError("Cannot add land on non-cartopy axes. Got ($s)" % type(ax))
    style_dict = _style_dict(style)
    feature = cfeature.NaturalEarthFeature(
        name="coastline",
        category="physical",
        scale="50m",
        edgecolor=style_dict["coastcolor"],
        facecolor="none",
    )
    ax.add_feature(feature)


### Presets (should proabably put all others into a submodule)
def basic(
    da, fig, timestamp, framedim="time", plotmethod=None, plot_variable=None, subplot_kw=None, **kwargs
):
    """Basic plot using the default xarray plot method for this DataArray."""

    # create axis
    ax = fig.subplots(subplot_kw=subplot_kw)
    data = _check_input(da, plot_variable)
    pp = _base_plot(ax, data, timestamp, framedim, plotmethod=plotmethod, **kwargs)
    return ax, pp


def rotating_globe(
    da,
    fig,
    timestamp,
    framedim="time",
    plotmethod=None,
    plot_variable=None,
    overlay_variables=None,
    lon_start=-110,
    lon_rotations=0.5,
    lat_start=25,
    lat_rotations=0,
    land=False,
    gridlines=False,
    coastline=True,
    style=None,
    debug=False,
    **kwargs
):
    """
    Rotating globe plot.

    Parameters
    ----------
    da : DataArray
        Data to be plotted.
    fig : Figure
        Figure to plot on.
    timestamp : int
        Used to select the animation frame using :meth:`~xarray.DataArray.isel`
        with dimension `framedim`.
    framedim : str
        Dimension name along which frames will be generated.
    plotmethod : str, optional
        Method of :attr:`xarray.DataArray.plot` to use.
    plot_variable : str, optional
        Variable to plot. Not needed for :class:`~xarray.DataArray`.
    overlay_variables
        Currently unused.
    lon_start : float
        Central longitude at the beginning of the animation.
    lon_rotations : float
        Number of longitude rotations to be completed in the animation.
    lat_start : float
        As in `lon_start`.
    lat_rotations : float
        As in `lon_rotations`.
    land : bool
        Plot the land.
    gridlines : bool
        Plot lat/lon gridlines.
    coastline : bool
        Plot the coastlines.
    style : {'standard', 'dark'}
    debug : bool
        Currently unused.
    **kwargs
        Passed on to the xarray plotting method.
    """

    # rotate lon_rotations times throughout movie and start at lon_start
    lon = np.linspace(0, 360 * lon_rotations, len(da[framedim])) + lon_start
    # Same for lat
    lat = np.linspace(0, 360 * lat_rotations, len(da[framedim])) + lat_start

    # proj = ccrs.Orthographic(lon[timestamp], lat[timestamp])
    # proj = _smooth_boundary_globe(proj)
    # This looks more like a 3D globe in my opinion
    proj = ccrs.NearsidePerspective(
        central_longitude=lon[timestamp], central_latitude=lat[timestamp]
    )
    proj = _smooth_boundary_NearsidePerspective(proj)

    subplot_kw = dict(projection=proj)

    # mapping style kwargs
    map_style_kwargs = dict(transform=ccrs.PlateCarree())
    kwargs.update(map_style_kwargs)

    # create axis (TODO:this should be handled by the basic preset )
    ax = fig.subplots(subplot_kw=subplot_kw)
    data = _check_input(da, plot_variable)
    pp = _base_plot(ax, data, timestamp, framedim, plotmethod=plotmethod, **kwargs)

    _set_style(fig, ax, pp, style=style)

    ax.set_title("")
    ax.set_global()

    # set style (TODO: move this to the basic function including the set style)
    if land:
        _add_land(ax, style)

    if coastline:
        _add_coast(ax, style)

    if gridlines:
        gl = ax.gridlines()
        # Increase gridline res
        gl.n_steps = 500
        # for now fixed locations
        gl.xlocator = mticker.FixedLocator(range(-180, 181, 30))
        gl.ylocator = mticker.FixedLocator(range(-90, 91, 30))
    else:
        gl = None
    # i should output this to test the preset. Maybe a dict output for the pp and gl (and potentially others)?

    # need a way to do that for the outline too

    # possibly for future versions, but I need a way to increase results
    # ax.outline_patch.set_visible(False)
    return ax, pp


def rotating_globe_dark(da, fig, timestamp, **kwargs):
    warnings.warn(
        "This preset will be deprecated in the future. \
    Use `rotating_globe` with `style=`dark`` instead`",
        DeprecationWarning,
    )
    return rotating_globe(da, fig, timestamp, style="dark", **kwargs)
