import matplotlib as mpl

mpl.use("Agg")
import re
import os
import sys
import glob
import warnings
import gc
import xarray as xr

from .presets import _check_input, basic
from subprocess import Popen, PIPE, STDOUT
import matplotlib.pyplot as plt

try:
    from tqdm.auto import tqdm

    tqdm_avail = True
except:
    warnings.warn(
        "Optional dependency `tqdm` not found. This will make progressbars a lot nicer. \
    Install with `conda install -c conda-forge tqdm`"
    )
    tqdm_avail = False

# import xarray as xr
# import dask.bag as db
import dask.array as dsa


# is it a good idea to set these here?
# Needs to be dependent on dpi and videosize
plt.rcParams.update({"font.size": 14})


# Data treatment
def _parse_plot_defaults(da, kwargs):
    if isinstance(da, xr.DataArray):
        data = da
    else:
        raise RuntimeError("input of type (%s) not supported yet." % type(da))

    # check these explicitly to avoid any computation if these are set.
    if "vmin" not in kwargs.keys():
        warnings.warn(
            "No `vmin` provided. Data limits are calculated from input. Depending on the input this can take long. Pass `vmin` to avoid this step",
            UserWarning,
        )
        kwargs["vmin"] = data.min().data

    if "vmax" not in kwargs.keys():
        warnings.warn(
            "No `vmax` provided. Data limits are calculated from input. Depending on the input this can take long. Pass `vmax` to avoid this step",
            UserWarning,
        )
        kwargs["vmax"] = data.max().data

    # There is a bug that prevents this from working...Ill have to fix that upstream.
    # defaults["cbar_kwargs"] = dict(extend="neither")
    # This works for now
    kwargs.setdefault("extend", "neither")

    # if any value is dask.array compute them here.
    for k in ["vmin", "vmax"]:
        if isinstance(kwargs[k], dsa.Array):
            kwargs[k] = kwargs[k].compute()

    return kwargs


def _check_plotfunc_output(func, da, **kwargs):
    timestep = 0
    fig = plt.figure()
    oargs = func(da, fig, timestep, **kwargs)
    # I just want the number of output args, delete plot
    plt.close(fig)
    if oargs is None:
        return 0
    else:
        return len(oargs)


def _check_ffmpeg_version():
    p = Popen("ffmpeg -version", stdout=PIPE, shell=True)
    (output, err) = p.communicate()
    p_status = p.wait()
    # Parse version
    if p_status != 0:
        print("No ffmpeg found")
        return None
    else:
        # parse version number
        try:
            found = (
                re.search("ffmpeg version (.+?) Copyright", str(output))
                .group(1)
                .replace(" ", "")
            )
            return found
        except AttributeError:
            # ffmpeg version, Copyright not found in the original string
            found = None
    return found


def _execute_command(command, verbose=False, error=True):
    p = Popen(command, stdout=PIPE, stderr=STDOUT, shell=True)

    if verbose:
        while True:
            out = p.stdout.read(1)
            out_check = out.decode()
            if out_check == "" and p.poll() is not None:
                break
            if out_check != "":
                # only display 10 lines, this cant be that hard?
                sys.stdout.write(out)
                sys.stdout.flush()
    else:
        p.wait()
    if error:
        if p.returncode != 0:
            raise RuntimeError("Command %s failed" % command)
    return p


def _check_ffmpeg_execute(command, verbose=False):
    if _check_ffmpeg_version() is None:
        raise RuntimeError(
            "Could not find an ffmpeg version on the system. \
        Please install ffmpeg with e.g. `conda install -c conda-forge ffmpeg`"
        )
    else:
        try:
            p = _execute_command(command, verbose=verbose)
            return p
        except RuntimeError:
            raise RuntimeError(
                "Something has gone wrong. Use `verbose=True` to check if ffmpeg displays a problem"
            )


# def create_gif_palette(mpath, ppath="palette.png", verbose=False):
#     command = "ffmpeg -y -i %s -vf palettegen %s" % (mpath, ppath)
#     p = _check_ffmpeg_execute(command, verbose=verbose)
#     return p


def convert_gif(
    mpath,
    gpath="movie.gif",
    gif_palette=False,
    resolution=[480, 320],
    verbose=False,
    remove_movie=True,
    gif_framerate=5,
):

    if gif_palette:
        palette_filter = (
            '-filter_complex "[0:v] split [a][b];[a] palettegen [p];[b][p] paletteuse"'
        )
    else:
        palette_filter = ""

    command = "ffmpeg -y -i %s %s -r %i -s %ix%i %s" % (
        mpath,
        palette_filter,
        gif_framerate,
        resolution[0],
        resolution[1],
        gpath,
    )
    p = _check_ffmpeg_execute(command, verbose=verbose)

    print("GIF created at %s" % (gpath))
    if remove_movie:
        if os.path.exists(mpath):
            os.remove(mpath)
    return p


def _combine_ffmpeg_command(
    sourcefolder, moviename, framerate, frame_pattern, ffmpeg_options
):
    # we need `-y` because i can not properly diagnose the errors here...
    command = 'ffmpeg -r %i -i "%s" -y %s -r %i "%s"' % (
        framerate,
        os.path.join(sourcefolder, frame_pattern),
        ffmpeg_options,
        framerate,
        os.path.join(sourcefolder, moviename),
    )
    return command


def write_movie(
    sourcefolder,
    moviename,
    frame_pattern="frame_%05d.png",
    remove_frames=True,
    verbose=False,
    ffmpeg_options="-c:v libx264 -preset veryslow -crf 15 -pix_fmt yuv420p",
    framerate=20,
):

    command = _combine_ffmpeg_command(
        sourcefolder, moviename, framerate, frame_pattern, ffmpeg_options
    )
    p = _check_ffmpeg_execute(command, verbose=verbose)

    print("Movie created at %s" % (moviename))
    if remove_frames:
        rem_name = frame_pattern.replace("%05d", "*")
        for f in glob.glob(os.path.join(sourcefolder, rem_name)):
            if os.path.exists(f):
                os.remove(f)
    return p


# def create_frame(pixelwidth, pixelheight, dpi):
#     """Creates a Figure sized according to the pixeldimensions"""
#     fig = plt.figure()
#     fig.set_size_inches(pixelwidth / dpi, pixelheight / dpi)
#     return fig


def frame_save(fig, frame, odir=None, frame_pattern="frame_%05d.png", dpi=100):
    fig.savefig(
        os.path.join(odir, frame_pattern % (frame)),
        dpi=dpi,
        facecolor=fig.get_facecolor(),
        transparent=True,
    )
    # I am trying everything to *wipe* this figure, hoping that it could
    # help with the dask glitches I experienced earlier.
    # TBD if this is all needed...how this might affect performance.
    plt.close(fig)
    del fig
    gc.collect(2)


class Movie:
    def __init__(
        self,
        da,
        plotfunc=None,
        framedim="time",
        pixelwidth=1920,
        pixelheight=1080,
        dpi=200,
        frame_pattern="frame_%05d.png",
        fieldname=None,
        input_check=True,
        **kwargs
    ):
        self.pixelwidth = pixelwidth
        self.pixelheight = pixelheight
        self.dpi = dpi
        self.width = self.pixelwidth / self.dpi
        self.height = self.pixelheight / self.dpi
        self.frame_pattern = frame_pattern
        self.data = da
        self.framedim = framedim
        if plotfunc is None:
            self.plotfunc = basic
        else:
            self.plotfunc = plotfunc
        # set sensible defaults
        self.raw_kwargs = kwargs

        # Check input

        # optional checks (these might need to be deactivated when using custom
        # plot functions.)
        if input_check:
            if isinstance(self.data, xr.Dataset):
                raise ValueError(
                    "xmovie presets do not yet support the input of xr.Datasets. \
                In order to use datasets as inputs, set `input_check` to False. \
                Note that this requires you to manually set colorlimits etc."
                )

            # Set defaults
            self.kwargs = _parse_plot_defaults(self.data, self.raw_kwargs)
        else:
            self.kwargs = self.raw_kwargs

        # Mandatory checks
        # Check if `framedim` exists.
        if self.framedim not in list(self.data.dims):
            raise ValueError("Framedim (%s) not found in input data" % self.framedim)
        # Check the output of plotfunc
        self.plotfunc_n_outargs = _check_plotfunc_output(
            self.plotfunc, self.data, **self.kwargs
        )

    def render_frame(self, timestep):
        """renders complete figure (frame) for given timestep.

        Parameters
        ----------
        timestep : type
            Description of parameter `timestep`.

        Returns
        -------
        type
            Description of returned object.

        """
        fig = plt.figure(figsize=[self.width, self.height])
        # create_frame(self.pixelwidth, self.pixelheight, self.dpi)
        # produce dummy output for ax and pp if the plotfunc does not provide them
        if self.plotfunc_n_outargs == 2:
            # this should be the case for all presets provided by xmovie
            ax, pp = self.plotfunc(self.data, fig, timestep, **self.kwargs)
        else:
            warnings.warn(
                "The provided `plotfunc` does not provide the expected number of output arguments.\
            Expected a function `ax,pp =plotfunc(...)` but got %i output arguments. Inserting dummy values. This should not affect output. ",
                UserWarning,
            )
            _ = self.plotfunc(self.data, fig, timestep, **self.kwargs)
            ax, pp = None, None
        return fig, ax, pp

    def preview(self, timestep):
        """Creates preview frame of movie Class.

        Parameters
        ----------
        timestep : int
            timestep(frame) for preview.

        """
        with plt.rc_context(
            {"figure.dpi": self.dpi, "figure.figsize": [self.width, self.height]}
        ):
            fig, ax, pp = self.render_frame(timestep)

    def save_frames(self, odir, progress=False):
        """Save movie frames as picture files.

        Parameters
        ----------
        odir : path
            path to output directory
        progress : type
            Show progress bar. Requires

        """
        # create range of frames
        frame_range = range(len(self.data[self.framedim].data))
        if tqdm_avail and progress:
            frame_range = tqdm(frame_range)
        elif ~tqdm_avail and progress:
            warnings.warn("Cant show progess bar at this point. Install tqdm")

        for fi in frame_range:
            fig, ax, pp = self.render_frame(fi)
            frame_save(
                fig, fi, odir=odir, frame_pattern=self.frame_pattern, dpi=self.dpi
            )

    def save(
        self,
        filename,
        remove_frames=True,
        remove_movie=True,
        progress=False,
        verbose=False,
        overwrite_existing=False,
        framerate=15,
        ffmpeg_options="-c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p",
        gif_palette=False,
        gif_resolution_factor=0.5,
        gif_framerate=10,
    ):
        """Save out animation from Movie object.

        Parameters
        ----------
        filename : str
            Pathname to final movie/animation. Output is dependent on filetype:
            Creates movie for `*.mp4` and gif for `*.gif`
        remove_frames : Bool
            Optional removal of frame pictures (the default is True; False will
            leave all picture files in folder).
        remove_movie : Bool
            As `remove_frames` but for movie file. Only applies when filename
            is given as `.gif` (the default is True).
        progress : Bool
            Experimental switch to show progress output. This will be refined
            in future version (the default is False).
        verbose : Bool
            Experimental switch to show output of ffmpeg commands. Useful for
            debugging but can quickly flood your notebook
            (the default is False).
        overwrite_existing : Bool
            Set to overwrite existing files with `filename`
            (the default is False).
        framerate : int
            Frames per second for the output movie file. Only relevant for '.mp4' files.
            (the default is 15)
        ffmpeg_options: str
            Encoding options to pass to ffmpeg call.
            Defaults to : `"-c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p"`
        gif_palette : Bool
            Use a gif colorpalette to improve quality. Can lead to artifacts
            in very contrasty situations (the default is False).
        gif_resolution_factor : float
            Factor used to reduce gif resolution compared to movie.
            Use 1.0 to put out the same resolutions for both products.
            (the default is 0.5).
        gif_framerate : int
            As `framerate` but for the gif output file. Only relevant to `.gif` files.
            (the default is 10)
        """

        # parse out directory and filename
        dirname = os.path.dirname(filename)
        filename = os.path.basename(filename)

        # detect gif filename

        isgif = ".gif" in filename
        if isgif:
            giffile = filename
            moviefile = filename.replace("gif", "mp4")
            gpath = os.path.join(dirname, giffile)
        else:
            moviefile = filename

        mpath = os.path.join(dirname, moviefile)

        # check existing files
        if os.path.exists(mpath):
            if not overwrite_existing:
                raise RuntimeError(
                    "File `%s` already exists. Set `overwrite_existing` to True to overwrite."
                    % (mpath)
                )
        if isgif:
            if os.path.exists(gpath):
                if not overwrite_existing:
                    raise RuntimeError(
                        "File `%s` already exists. Set `overwrite_existing` to True to overwrite."
                        % (gpath)
                    )

        # print frames
        self.save_frames(dirname, progress=progress)

        # Create movie
        write_movie(
            dirname,
            moviefile,
            frame_pattern=self.frame_pattern,
            remove_frames=remove_frames,
            verbose=verbose,
            framerate=framerate,
            ffmpeg_options=ffmpeg_options,
        )

        # Create gif
        if isgif:
            # if ppath:
            #     create_gif_palette(mpath, ppath=ppath, verbose=verbose)
            convert_gif(
                mpath,
                gpath=gpath,
                resolution=[480, 320],
                gif_palette=gif_palette,
                verbose=verbose,
                remove_movie=remove_movie,
                gif_framerate=gif_framerate,
            )

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
