from xmovie.core import (
    create_frame,
    _combine_ffmpeg_command,
    _execute_command,
    _check_ffmpeg_execute,
    frame_save,
    write_movie,
    create_gif_palette,
    convert_gif,
    Movie,
)
from xmovie.presets import rotating_globe_dark, rotating_globe
import pytest
import matplotlib.pyplot as plt
from PIL import Image
import numpy as np
import xarray as xr


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
def test_combine_ffmpeg_command(dir, fname, path):
    fixed_options = " -y -c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p -framerate 20"
    moviename = "movie.mp4"
    cmd = _combine_ffmpeg_command(dir, moviename, fname)
    assert cmd == 'ffmpeg -i "%s" %s "%s"' % (path, fixed_options, moviename)
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


@pytest.mark.parametrize("moviename", ["movie.mp4"])
@pytest.mark.parametrize("frame_pattern", ["frame_%05d.png", "test%05d.png"])
@pytest.mark.parametrize("palettename", ["palette.png", "test.png"])
@pytest.mark.parametrize("gifname", ["movie.gif", "shmoovie.gif"])
@pytest.mark.parametrize("remove_frames", [True, False])
@pytest.mark.parametrize("remove_movie", [True, False])
@pytest.mark.parametrize("remove_palette", [True, False])
def test_write_movie_gif(
    tmpdir,
    moviename,
    palettename,
    gifname,
    frame_pattern,
    remove_frames,
    remove_movie,
    remove_palette,
):
    da = test_dataarray()
    mov = Movie(da, frame_pattern=frame_pattern)
    mov.save_frames(tmpdir.strpath)
    mpath = tmpdir.join(moviename)
    ppath = tmpdir.join(palettename)
    gpath = tmpdir.join(gifname)
    filenames = [tmpdir.join(frame_pattern % ff) for ff in range(len(da.time))]
    write_movie(
        tmpdir.strpath,
        mpath.strpath,
        frame_pattern=frame_pattern,
        remove_frames=remove_frames,
    )
    create_gif_palette(mpath.strpath, ppath.strpath)
    convert_gif(
        mpath.strpath,
        gpath=gpath.strpath,
        ppath=ppath.strpath,
        remove_movie=remove_movie,
        remove_palette=remove_palette,
    )

    if remove_frames:
        assert all([~fn.exists() for fn in filenames])
    else:
        assert all([fn.exists() for fn in filenames])

    if remove_movie:
        assert ~mpath.exists()
    else:
        assert mpath.exists()

    if remove_palette:
        assert ~ppath.exists()
    else:
        assert ppath.exists()

    assert gpath.exists()

    # TODO: Better error message when framedim is not available.
    # This takes forever with all these options...
    # Check the overwrite option


# plotfunc=None,


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
