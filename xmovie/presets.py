import warnings

import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import numpy as np
import shapely.geometry as sgeom
import xarray as xr


def _check_input(da, fieldname):
    # pick the data_var to plot
    if isinstance(da, xr.Dataset):
        if fieldname is None:
            fieldname = list(da.data_vars)[0]
            warnings.warn("No `fieldname` supplied. Defaults to `%s`" % fieldname, UserWarning)
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
    data = base_data.isel({framedim: timestamp})
    p = _core_plot(ax, data, plotmethod=plotmethod, **kwargs)
    return p


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
    ax.set_facecolor(bgcolor)

    # modify colorbar
    try:
        cb = pp.colorbar
    except AttributeError:
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


# Presets (should proabably put all others into a submodule)


def basic(
    da, fig, timestamp, framedim="time", plotmethod=None, plot_variable=None, subplot_kw=None, **kwargs
):
    """Basic plot using the default xarray plot method for this DataArray."""

    # create axis
    ax = fig.subplots(subplot_kw=subplot_kw)
    data = _check_input(da, plot_variable)
    pp = _base_plot(ax, data, timestamp, framedim, plotmethod=plotmethod, **kwargs)
    return ax, pp
