from xmovie.core import frame, _combine_ffmpeg_command, _execute_command
import pytest


@pytest.mark.parametrize("w", [400, 1024, 4000])
@pytest.mark.parametrize("h", [400, 1024, 4000])
@pytest.mark.parametrize("dpi", [43, 150, 300])
def test_frame(w, h, dpi):
    fig = frame(w, h, dpi)
    assert fig.get_figwidth() * dpi == w
    assert fig.get_figheight() * dpi == h
    pass


@pytest.mark.parametrize("frame", [0, 10, 100, 1000])
@pytest.mark.parametrize("pattern", ["frame_%05d.png", "test%05d.png"])
def test_frame_save(frame, pattern):
    pass


def test_check_ffmpeg_version():
    pass


@pytest.mark.parametrize(
    "dir, fname, path", [("", "file", "file"), ("foo", "file", "foo/file")]
)
def test_combine_ffmpeg_command(dir, fname, path):
    fixed_options = " -y -c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p -framerate 20"
    moviename = "movie.mp4"
    cmd = _combine_ffmpeg_command(dir, moviename, fname)
    assert cmd == 'ffmpeg -i "%s" %s %s' % (path, fixed_options, moviename)
    # TODO: needs more testing for the decomp of the movie filename.


def test_execute_command():
    a = _execute_command("ls -l")
    assert a.returncode == 0

    with pytest.raises(RuntimeError):
        _execute_command("ls -l?")


def test_check_ffmpeg_execute():
    pass


def test_create_gif_palette():
    pass


def test_convert_gif():
    pass


def test_write_movie():
    pass


def test_Movie():
    pass
