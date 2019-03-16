import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt
import xarray as xr
import dask.bag as db
from .presets import rotating_globe


def frame(pixelwidth, pixelheight, dpi):
    """Creates a Figure sized according to the pixeldimensions"""
    fig = plt.figure()
    fig.set_size_inches(pixelwidth / dpi, pixelheight / dpi)
    return fig


def frame_save(fig, frame, odir=None, frame_name="frame_", dpi=150):
    fig.savefig(
        odir + "/%s%05d.png" % (frame_name, frame),
        dpi=dpi,
        facecolor=fig.get_facecolor(),
        transparent=True,
    )
    plt.close(fig)


class Movie:
    def __init__(
        self,
        da,
        plotfunc,
        framedim="time",
        pixelwidth=1920,
        pixelheight=1080,
        dpi=200,
        **kwargs
    ):
        self.pixelwidth = pixelwidth
        self.pixelheight = pixelheight
        self.dpi = dpi
        self.data = da
        self.framedim = framedim
        self.plotfunc = plotfunc
        self.kwargs = kwargs
        ##
        # add kwargs to plotfunc

    def preview(self, timestep):
        """Creates preview frame of movie Class.

        Parameters
        ----------
        timestep : int
            timestep(frame) for preview.

        Returns
        -------
        matplotlib.figure

        """
        # TODO I could probably define the func with the movie class
        fig = frame(self.pixelwidth, self.pixelheight, self.dpi)
        self.plotfunc(self.data, fig, timestep, **self.kwargs)
        fig.canvas.draw()
        return fig

    def save(self, odir):
        """Save movie frames out to file.

        Parameters
        ----------
        odir : path
            path to output directory

        """

        for fi, ff in enumerate(self.data[self.framedim].data):
            fig = self.preview(fi)
            frame_save(fig, fi, odir=odir, frame_name="frame_", dpi=self.dpi)

    # def save_parallel(
    #     self, odir, da, plotfunc, framedim, partition_size=5, func_kwargs={}
    # ):
    #     """Save movie frames out to file.
    #
    #     Parameters
    #     ----------
    #     odir : path
    #         path to output directory
    #     da : xr.Dataset/xr.DataArray
    #         Input xarray object.
    #     plotfunc : func
    #         plotting function.
    #     framedim : type
    #         Dimension of `da` which represents the frames (e.g. time).
    #     partition_size : type
    #         Size of dask bags to be computed in parallel (the default is 20).
    #     func_kwargs : dict
    #         optional arguments passed to func (the default is {}).
    #
    #     Returns
    #     -------
    #     type
    #         Description of returned object.
    #
    #     """
    #     if isinstance(da, xr.DataArray):
    #         dummy_data = da
    #     elif isinstance(da, xr.Dataset):
    #         dummy_data = da[list(da.data_vars)[0]]
    #     else:
    #         raise ValueError("Input has to be xarray object. Is %s" % type(da))
    #
    #     frames = range(len(dummy_data[framedim].data))
    #     frame_bag = db.from_sequence(frames, partition_size=partition_size)
    #     frame_bag.map(
    #         self.frame_save,
    #         odir=odir,
    #         da=da,
    #         plotfunc=plotfunc,
    #         func_kwargs=func_kwargs,
    #     ).compute(processes=False)
