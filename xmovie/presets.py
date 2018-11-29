import numpy as np
import xarray as xr
import cartopy.crs as ccrs
import cartopy.feature as cfeature


def get_plot_defaults(da):
    if isinstance(da, xr.DataArray):
        data = da
    else:
        raise RuntimeError('input of type (%s) not supported' % type(da))
    defaults = dict([])
    defaults['vmin'] = data.min().data
    defaults['vmax'] = data.max().data
    defaults['cbar_kwargs'] = dict(extend='neither')
    return defaults


def check_input(da, fieldname):
    # pick the data_var to plot
    if isinstance(da, xr.Dataset):
        if fieldname is None:
            fieldname = list(da.data_vars)[0]
            print('No plot_variable supplied. Defaults to `%s`' % fieldname)
        data = da[fieldname]
    elif isinstance(da, xr.DataArray):
        data = da
    else:
        raise RuntimeWarning('Data must be xr.DataArray or xr.Dataset \
        (with `fieldname` specified). Datatype found %s' % type(da))
    return data


def _core_plot(ax, data, plotmethod=None, **kwargs):
    """Core plotting functionality"""

    #     check kwargs input
    if plotmethod == 'contour':
        kwargs.pop('cbar_kwargs', None)

    # I am probably recoding something from matplotlib...is ther a way to get
    # the plot.something functionslity with a keyword?
    # For now do it the hard way
    if plotmethod is None:
        p = data.plot(ax=ax, **kwargs)
    elif plotmethod == 'contour':
        p = data.plot.contour(ax=ax, **kwargs)
    elif plotmethod == 'contourf':
        p = data.plot.contourf(ax=ax, **kwargs)
    else:
        raise RuntimeError("Input '%s' not recognized \
        as plotmode" % plotmethod)
    return p


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

def rotating_globe(da, fig, timestamp,
                   framedim='time',
                   plotmethod=None, plot_variable=None,
                   overlay_variables=None,
                   lon_start=0, lon_rotations=-1,
                   lat_start=35, lat_rotations=0.05,
                   **kwargs):

    # rotate lon_rotations times throughout movie and start at lon_start
    lon = np.linspace(0, 360*lon_rotations, len(da.time)) + lon_start
    # Same for lat
    lat = np.linspace(0, 360*lat_rotations, len(da.time)) + lat_start

    subplot_kw = dict(projection=ccrs.Orthographic(lon[timestamp],
                                                   lat[timestamp]))
    # create axis
    ax = fig.subplots(subplot_kw=subplot_kw)

    # mapping style kwargs
    map_style_kwargs = dict(transform=ccrs.PlateCarree())

    data = check_input(da, plot_variable)

    _base_plot(ax, data, timestamp, plotmethod=plotmethod,
               **kwargs, **map_style_kwargs)
    ax.set_title('')
    ax.set_global()
    ax.coastlines()
    ax.gridlines()
