from xmovie.core import (
    create_frame,
    _combine_ffmpeg_command,
    _execute_command,
    _check_ffmpeg_execute,
    frame_save,
    write_movie,
    convert_gif,
    Movie,
)
from xmovie.presets import rotating_globe_dark, rotating_globe
import pytest
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import xarray as xr
import os
import cv2


@pytest.mark.parametrize("w", [400, 1024, 4000])
@pytest.mark.parametrize("h", [400, 1024, 4000])
@pytest.mark.parametrize("dpi", [43, 150, 300])
def test_create_frame(w, h, dpi):
    fig = create_frame(w, h, dpi)
    assert fig.get_figwidth() * dpi == w
    assert fig.get_figheight() * dpi == h


@pytest.mark.parametrize("w", [400, 1024])
@pytest.mark.parametrize("h", [400, 1024])
@pytest.mark.parametrize("dpi", [43, 150])
@pytest.mark.parametrize("frame", [0, 10, 100, 1000])
@pytest.mark.parametrize("frame_pattern", ["frame_%05d.png", "test%05d.png"])
def test_frame_save(tmpdir, frame, frame_pattern, dpi, w, h):
    # Create Figure
    # fig = plt.figure()
    fig = create_frame(w, h, dpi)
    frame_save(fig, frame, odir=tmpdir, frame_pattern=frame_pattern, dpi=dpi)
    filename = tmpdir.join(frame_pattern % frame)
    img = Image.open(filename.strpath)
    pixel_w, pixel_h = img.size
    # # Check if figure was properly closed
    assert filename.exists()
    assert not plt.fignum_exists(fig.number)
    assert pixel_w == w
    assert pixel_h == h


def test_check_ffmpeg_version():
    # ooof I will have to check this with the ci, one which has ffmpeg and one
    # which doesnt...Check xarray how to do this.
    pass


@pytest.mark.parametrize(
    "dir, fname, path", [("", "file", "file"), ("foo", "file", "foo/file")]
)
@pytest.mark.parametrize("frame_pattern", ["frame_%05d.png", "test%05d.png"])
def test_combine_ffmpeg_command(dir, fname, path, frame_pattern):
    fixed_options = " -y -c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p -framerate 20"
    cmd = _combine_ffmpeg_command(dir, fname, frame_pattern=frame_pattern)
    assert cmd == 'ffmpeg -i "%s" %s "%s"' % (
        os.path.join(dir, frame_pattern),
        fixed_options,
        path,
    )
    # TODO: needs more testing for the decomp of the movie filename.


def test_execute_command():
    a = _execute_command("ls -l")
    assert a.returncode == 0

    with pytest.raises(RuntimeError):
        _execute_command("ls -l?")


def test_check_ffmpeg_execute():
    # Same issue as `test_check_ffmpeg_version`

    a = _check_ffmpeg_execute("ls -l")
    assert a.returncode == 0

    with pytest.raises(RuntimeError):
        _check_ffmpeg_execute("ls -l?")


def test_dataarray():
    """Create a little test dataset"""
    x = np.arange(4)
    y = np.arange(5)
    t = np.arange(2)
    data = np.random.rand(len(x), len(y), len(t))
    return xr.DataArray(data, coords=[("x", x), ("y", y), ("time", t)])


@pytest.mark.parametrize("moviename", ["movie.mp4", "shmoovie.mp4"])
@pytest.mark.parametrize("remove_frames", [True, False])
def test_movie_write_movie(tmpdir, moviename, remove_frames):

    frame_pattern = "frame_%05d.png"  # the default
    m = tmpdir.join(moviename)
    mpath = m.strpath

    da = test_dataarray()
    mov = Movie(da)
    mov.save_frames_serial(tmpdir)
    filenames = [tmpdir.join(frame_pattern % ff) for ff in range(len(da.time))]
    write_movie(tmpdir, moviename, remove_frames=remove_frames)

    if remove_frames:
        assert all([~fn.exists() for fn in filenames])
    else:
        assert all([fn.exists() for fn in filenames])
    assert m.exists()  # could test more stuff here I guess.


@pytest.mark.parametrize("moviename", ["movie.mp4"])
@pytest.mark.parametrize("gif_palette", [True, False])
@pytest.mark.parametrize("gifname", ["movie.gif"])
@pytest.mark.parametrize("remove_movie", [True, False])
def test_convert_gif(tmpdir, moviename, remove_movie, gif_palette, gifname):
    m = tmpdir.join(moviename)
    mpath = m.strpath
    g = tmpdir.join(gifname)
    gpath = g.strpath

    da = test_dataarray()
    mov = Movie(da)
    mov.save_frames_serial(tmpdir)

    write_movie(tmpdir, moviename)

    convert_gif(
        mpath, gpath=gpath, gif_palette=gif_palette, remove_movie=remove_movie
    )

    if remove_movie:
        assert ~m.exists()
    else:
        assert m.exists()

    assert g.exists()

    # TODO: Better error message when framedim is not available.
    # This takes forever with all these options...
    # Check the overwrite option


@pytest.mark.parametrize("frame_pattern", ["frame_%05d.png", "test%05d.png"])
@pytest.mark.parametrize("pixelwidth", [100, 500, 1920])
@pytest.mark.parametrize("pixelheight", [100, 500, 1080])
# combine them and also add str specs like 'HD' '1080' '4k'
@pytest.mark.parametrize("framedim", ["time", "x", "wrong"])
@pytest.mark.parametrize("dpi", [50, 200])
@pytest.mark.parametrize("plotfunc", [None, rotating_globe])
def test_Movie(
    plotfunc, framedim, frame_pattern, dpi, pixelheight, pixelwidth
):
    da = test_dataarray()
    kwargs = dict(
        plotfunc=plotfunc,
        framedim=framedim,
        frame_pattern=frame_pattern,
        pixelwidth=pixelwidth,
        pixelheight=pixelheight,
        dpi=dpi,
    )
    if framedim == "wrong":
        with pytest.raises(ValueError):
            mov = Movie(da, **kwargs)
    else:
        mov = Movie(da, **kwargs)

        if plotfunc is None:
            assert mov.plotfunc == rotating_globe_dark
        else:
            assert mov.plotfunc == plotfunc
        assert mov.framedim == framedim
        assert mov.pixelwidth == pixelwidth
        assert mov.pixelheight == pixelheight
        assert mov.dpi == dpi


@pytest.mark.parametrize("frame_pattern", ["frame_%05d.png", "test%05d.png"])
def test_movie_save_frames_serial(tmpdir, frame_pattern):
    da = test_dataarray()
    mov = Movie(da, frame_pattern=frame_pattern)
    mov.save_frames_serial(tmpdir)
    filenames = [tmpdir.join(frame_pattern % ff) for ff in range(len(da.time))]
    assert all([fn.exists() for fn in filenames])


def compare_images(impath1, impath2):
    # Check if two images as the same (pixel by pixel)
    im1 = cv2.imread(impath1)
    im2 = cv2.imread(impath2)
    if im1.shape == im2.shape:
        difference = cv2.subtract(im1, im2)
        b, g, r = cv2.split(difference)
        if (
            cv2.countNonZero(b) == 0
            and cv2.countNonZero(g) == 0
            and cv2.countNonZero(r) == 0
        ):
            return True
        else:
            return False
    else:
        return False


# TODO: parametrize all kinds of options for plotting...


@pytest.mark.parametrize("progress", [False, True])
@pytest.mark.parametrize("partition_size", [1, 5])
def test_movie_save_frames_parallel(tmpdir, progress, partition_size):

    # da = test_dataarray() # THis is not long enugh to produce those weird glitches

    # need a longer
    da = xr.tutorial.open_dataset("air_temperature").air.isel(
        time=slice(0, 10)
    )

    frame_pattern_ser = "frame_ser_%05d.png"
    frame_pattern_par = "frame_par_%05d.png"

    mov_ser = Movie(da, frame_pattern=frame_pattern_ser)
    mov_par = Movie(da, frame_pattern=frame_pattern_par)

    mov_ser.save_frames_serial(tmpdir, progress=progress)
    mov_par.save_frames_parallel(
        tmpdir, progress=progress, partition_size=partition_size
    )

    filenames_ser = [
        tmpdir.join(frame_pattern_ser % ff) for ff in range(len(da.time))
    ]
    assert all([fn.exists() for fn in filenames_ser])
    filenames_par = [
        tmpdir.join(frame_pattern_par % ff) for ff in range(len(da.time))
    ]
    assert all([fn.exists() for fn in filenames_par])

    print(filenames_ser[0])
    print(filenames_par[0])
    assert all(
        [
            compare_images(a.strpath, b.strpath)
            for a, b in zip(filenames_ser, filenames_par)
        ]
    )


@pytest.mark.parametrize("filename", ["movie.mp4", "movie.gif"])
@pytest.mark.parametrize("gif_palette", [True, False])
@pytest.mark.parametrize("parallel", [True, False])
def test_movie_save(tmpdir, filename, gif_palette, parallel):
    # Need more tests for progress, verbose, overwriting
    path = tmpdir.join(filename)
    da = test_dataarray()
    mov = Movie(da)
    mov.save(path.strpath, gif_palette=gif_palette, parallel=parallel)

    assert path.exists()
    # I should also check if no other files were created. For later
