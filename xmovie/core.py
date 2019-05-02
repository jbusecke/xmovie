import re
import os
import sys
import glob
import warnings
import gc

from .presets import rotating_globe_dark
from subprocess import Popen, PIPE, STDOUT

import matplotlib as mpl

mpl.use("Agg")
import matplotlib.pyplot as plt

try:
    from tqdm import tqdm

    tqdm_avail = True
except:
    warnings.warn(
        "Optional dependency `tqdm` not found. This will make progressbars a lot nicer. \
    Install with `conda install -c conda-forge tqdm`"
    )
    tqdm_avail = False

# import xarray as xr
# import dask.bag as db


# is it a good idea to set these here?
# Needs to be dependent on dpi and videosize
plt.rcParams.update({"font.size": 16})


def create_frame(pixelwidth, pixelheight, dpi):
    """Creates a Figure sized according to the pixeldimensions"""
    fig = plt.figure()
    fig.set_size_inches(pixelwidth / dpi, pixelheight / dpi)
    return fig


def frame_save(fig, frame, odir=None, frame_pattern="frame_%05d.png", dpi=100):
    fig.savefig(
        os.path.join(odir, frame_pattern % (frame)),
        dpi=dpi,
        facecolor=fig.get_facecolor(),
        transparent=True,
    )
    plt.close(fig)
    # this might have already fixed my problem, unit testing FTW
    del fig
    # this was recommended here to remove fig from memory, can it help with
    # the problem with dask processing?
    gc.collect(2)
    # for now I just want to wipe ALL. This might impact performance?


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


def _combine_ffmpeg_command(
    sourcefolder, moviename, frame_pattern="frame_%05d.png"
):
    options = " -y -c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p -framerate 20"
    # we need `-y` because i can not properly diagnose the errors here...
    command = 'ffmpeg -i "%s" %s "%s"' % (
        os.path.join(sourcefolder, frame_pattern),
        options,
        moviename,
    )
    return command


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


def create_gif_palette(mpath, ppath="palette.png", verbose=False):
    command = "ffmpeg -y -i %s -vf palettegen %s" % (mpath, ppath)
    p = _check_ffmpeg_execute(command, verbose=verbose)
    return p


def convert_gif(
    mpath,
    gpath="movie.gif",
    ppath="palette.png",
    resolution=[480, 320],
    verbose=False,
    remove_movie=True,
    remove_palette=True,
):
    command = (
        "ffmpeg -y -i %s -i %s -filter_complex paletteuse -r 10 -s %ix%i %s"
        % (mpath, ppath, resolution[0], resolution[1], gpath)
    )
    p = _check_ffmpeg_execute(command, verbose=verbose)

    print("GIF created at %s" % (gpath))
    if remove_movie:
        try:
            os.remove(mpath)
        except:
            warnings.warn("movie removal failed")
            pass

    if remove_palette:
        try:
            os.remove(ppath)
        except:
            warnings.warn("palette removal failed")
            pass
    return p


def write_movie(
    sourcefolder,
    moviename,
    frame_pattern="frame_%05d.png",
    remove_frames=True,
    verbose=False,
    overwrite_existing=False,
):
    path = os.path.join(sourcefolder, moviename)
    if os.path.exists(path):
        if not overwrite_existing:
            raise RuntimeError(
                "File `%s` already exists. Set `overwrite_existing` to True to overwrite."
                % (path)
            )
    command = _combine_ffmpeg_command(
        sourcefolder, moviename, frame_pattern=frame_pattern
    )
    p = _check_ffmpeg_execute(command, verbose=verbose)

    print("Movie created at %s" % (moviename))
    if remove_frames:
        try:
            rem_name = frame_pattern.replace("%05d", "*")
            for f in glob.glob(os.path.join(sourcefolder, rem_name)):
                os.remove(f)
        except:
            warnings.warn("frame removal failed")
            pass

    return p


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
        **kwargs
    ):
        self.pixelwidth = pixelwidth
        self.pixelheight = pixelheight
        self.dpi = dpi
        self.frame_pattern = frame_pattern
        self.data = da
        self.framedim = framedim
        if plotfunc is None:
            self.plotfunc = rotating_globe_dark
        else:
            self.plotfunc = plotfunc
        self.kwargs = kwargs
        ##
        # add kwargs to plotfunc
        # Check input
        if self.framedim not in list(self.data.dims):
            raise ValueError(
                "Framedim (%s) not found in input data" % self.framedim
            )

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
        fig = create_frame(self.pixelwidth, self.pixelheight, self.dpi)
        self.plotfunc(self.data, fig, timestep, **self.kwargs)
        return fig

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
            fig = self.preview(fi)
            frame_save(
                fig,
                fi,
                odir=odir,
                frame_pattern=self.frame_pattern,
                dpi=self.dpi,
            )

    def save(
        self,
        filename,
        remove_frames=True,
        remove_movie=True,
        progress=False,
        verbose=False,
        overwrite_existing=False,
    ):
        """Short summary.

        Parameters
        ----------
        filename : str
            Pathname to final movie/animation.
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
            Switch to show all shell output. Mostly for debugging (the default is False).
        """

        # parse out directory and filename
        dirname = os.path.dirname(filename)
        filename = os.path.basename(filename)

        # detect gif filename

        isgif = "gif" in filename
        if isgif:
            giffile = filename
            moviefile = filename.replace("gif", "mp4")
            gpath = os.path.join(dirname, giffile)
            ppath = os.path.join(dirname, "palette.png")
        else:
            moviefile = filename

        mpath = os.path.join(dirname, moviefile)

        # print frames
        self.save_frames(dirname, progress=progress)

        # Create movie
        write_movie(
            dirname,
            moviefile,
            frame_pattern=self.frame_pattern,
            remove_frames=remove_frames,
            verbose=verbose,
            overwrite_existing=overwrite_existing,
        )

        # Create gif
        if isgif:
            create_gif_palette(mpath, ppath=ppath, verbose=verbose)
            convert_gif(
                mpath,
                gpath=gpath,
                ppath=ppath,
                resolution=[480, 320],
                verbose=verbose,
                remove_movie=remove_movie,
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
