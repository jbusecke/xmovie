import matplotlib as mpl
mpl.use('Agg')
import matplotlib.pyplot as plt
import xarray as xr
import dask.bag as db
from .presets import rotating_globe
#
# import cartopy.crs as ccrs
# import cartopy.feature as cfeature
# import numpy as np


class Movie:
    def __init__(self, pixelwidth=1920, pixelheight=1080, dpi=200):
        self.pixelwidth = pixelwidth
        self.pixelheight = pixelheight
        self.dpi = dpi

    def frame(self):
        """Creates a Figure sized according to the pixeldimensions"""
        fig = plt.figure()
        fig.set_size_inches(self.pixelwidth / self.dpi,
                            self.pixelheight / self.dpi)
        return fig

    def frame_render(self, da, func, timestamp, func_kwargs={}):
        fig = self.frame()
        func(da, fig, timestamp, **func_kwargs)
        fig.canvas.draw()
        return fig

    def frame_save(self, frame, odir=None, da=None, plotfunc=None,
                   frame_name='frame_', **kwargs):
        fig = self.frame_render(da, plotfunc, frame, **kwargs)

        fig.savefig(odir + '/%s%05d.png' % (frame_name, frame), dpi=self.dpi)
        plt.close(fig)

    def save(self, odir, da, plotfunc, framedim, func_kwargs={}):
        """Save movie frames out to file.

        Parameters
        ----------
        odir : path
            path to output directory
        da : xr.Dataset/xr.DataArray
            Input xarray object.
        plotfunc : func
            plotting function.
        framedim : type
            Dimension of `da` which represents the frames (e.g. time).
        func_kwargs : dict
            optional arguments passed to func (the default is {}).

        Returns
        -------
        type
            Description of returned object.

        """
        if isinstance(da, xr.DataArray):
            dummy_data = da
        elif isinstance(da, xr.Dataset):
            dummy_data = da[list(da.data_vars)[0]]

        # frame_axis = dummy_data.get_axis_num(framedim)
        for fi, ff in enumerate(da[framedim].data):
            self.frame_save(fi, odir=odir, da=da, plotfunc=plotfunc,
                            func_kwargs=func_kwargs)


    def save_parallel(self, odir, da, plotfunc, framedim, partition_size=5,
                      func_kwargs={}):
        """Save movie frames out to file.

        Parameters
        ----------
        odir : path
            path to output directory
        da : xr.Dataset/xr.DataArray
            Input xarray object.
        plotfunc : func
            plotting function.
        framedim : type
            Dimension of `da` which represents the frames (e.g. time).
        partition_size : type
            Size of dask bags to be computed in parallel (the default is 20).
        func_kwargs : dict
            optional arguments passed to func (the default is {}).

        Returns
        -------
        type
            Description of returned object.

        """
        if isinstance(da, xr.DataArray):
            dummy_data = da
        elif isinstance(da, xr.Dataset):
            dummy_data = da[list(da.data_vars)[0]]
        else:
            raise ValueError('Input has to be xarray object. Is %s' %type(da))

        frames = range(len(dummy_data[framedim].data))
        frame_bag = db.from_sequence(frames, partition_size=partition_size)
        frame_bag.map(self.frame_save, odir=odir, da=da, plotfunc=plotfunc,
                      func_kwargs=func_kwargs).compute(processes=False)

    def preview(self, da, plotfunc, timestep, func_kwargs={}):
        """Creates preview frame of movie Class.

        Parameters
        ----------
        da : xr.Dataset/xr.DataArray
            Input xarray object.
        plotfunc : func
            plotting function.
        timestep : int
            timestep(frame) for preview.
        func_kwargs : dict
            optional arguments passed to func (the default is {}).

        Returns
        -------
        type
            Description of returned object.

        """
        # TODO I could probably define the func with the movie class

        self.frame_render(da, plotfunc, timestep, func_kwargs=func_kwargs)
