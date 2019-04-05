# xmovie
A simple way of creating movies from [xarray](https://github.com/pydata/xarray) objects.

With ever increasing detail, modern scientific observations and model results
lend themselves to visualization in the form of movies.

Not only is a beautiful movie a fantastic way to wake up the crowd on a Friday
afternoon of a weeklong conference, but it can also speed up the discovery
process, since our eyes are amazing image processing devices.

This module aims to facilitate movie rendering from data object based on
[xarray](https://github.com/pydata/xarray) objects. It is already possible to
get very quick and beautiful static images from xarray, but movies can still
present a hassle.

The main aims of this module are:

- Enable quick but high quality movie frame creation from existing xarray
objects with preset plot functions.
- Convert your static plot workflow to a movie with only a few lines of code, while maintaining all the flexibility of [xarray](https://github.com/pydata/xarray) and [matplotlib](https://matplotlib.org/).


<!-- - Use [dask](https://github.com/dask/dask) for computationally efficient
frame rendering.
- WIP: Use [ffmpeg](https://www.ffmpeg.org/) to enable movie rendering from dataset
to finished movie file in jupyter notebooks (my preferred workflow). -->

## Installation
Clone this repository with `$ git clone git@github.com:jbusecke/xmovie.git` and
install it from source `$ python setup.py install`

>If you dont have [ssh keys](https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account) set up, you can use `$ git clone https://github.com/jbusecke/xmovie.git` and enter your github password.

## Presets for quick movies
Using the presets of __xmovie__ making a movie is very easy:

```python
from xmovie import Movie
from xmovie.presets import rotating_globe_dark

ds = xr.tutorial.open_dataset('air_temperature').load().isel(time=slice(0,150))
mov = Movie(ds)
```

Preview single frames in the movie with the `Movie.preview` function:
```
# preview 10th frame
mov.preview(10);
# preview 100th frame. Note the rotation
mov.preview(100);
```
!['10th frame'](docs/pics/preview1.png)!['100th frame'](docs/pics/preview2.png)

and save out each frame as a picture
```
mov.save('.') # saves to current directory
```

### Convert images to movies
In the commandline you can now convert the frames to a movie file using [ffmpeg]()

```
$ ffmpeg -y -i "frame_%05d.png" -c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p -framerate 20 movie.mp4
```
> from a notebook simply use a `!` before the command to execute a shell command:
```
# convert to movie file
! ffmpeg -y -i "frame_%05d.png" -c:v libx264 -preset veryslow -crf 10 -pix_fmt yuv420p -framerate 20 movie.mp4
```

### Convert to gif
To convert your movie file into a gif do
```
# convert to gif
! ffmpeg -y -i movie.mp4 -vf palettegen palette.png
! ffmpeg -y -i movie.mp4 -i palette.png -filter_complex paletteuse -r 10 -s 480x320 movie.gif
```

Just clean up all the image files
```
!rm *.png
```
and enjoy your masterpiece.

!['spin spin spin'](docs/gifs/movie.gif)

## Modify plots
The preset plot-functions each have a unique set of keyword arguments for custom looks, but they all support the `xarray` plotting modes via the `plotmethod` keyword:
```
mov = Movie(ds, rotating_globe_dark, plotmethod='contourf', coastline=False, land=True)
mov.save('.')
```
!['spin spin spin'](docs/gifs/movie_contf.gif)

```
mov = Movie(ds, rotating_globe_dark, plotmethod='contour', coastline=False, land=True)
mov.save('.')
```
!['spin spin spin'](docs/gifs/movie_cont.gif)

```
ds = xr.tutorial.open_dataset('rasm').Tair

# Interpolate time for smoother animation
ds['time'].data = np.arange(len(ds['time']))
ds = ds.interp(time=np.linspace(0,10, 60))

mov = Movie(ds, rotating_globe_dark,
            cmap='RdYlBu_r',
            x='xc',
            y='yc', #accepts keyword arguments from the xarray plotting interface
            lat_start=45, # Custom keywords from `rotating_globe_dark
            lon_rotations=0.2)
mov.save('.')
```

!['rasm_spinning'](docs/gifs/movie_rasm.gif)



### Custom Plots
You can customize any plot based on an xarray data structure and a 'frame-dimension' (usually time, or another dimension that will evolve with time in the movie).

Take this example:

```
# some awesome static plot
import matplotlib.pyplot as plt
fig = plt.figure(figsize=[10,5])
tt = 40

station = dict(x=100, y=150)
ds_station = ds.sel(**station)

(ax1, ax2) = fig.subplots(ncols=2)
ds.isel(time=tt).plot(ax=ax1)
ax1.plot(station['x'], station['y'], marker='*', color='k' ,markersize=15)
ax1.text(station['x']+4, station['y']+4, 'Station', color='k' )
ds_station.isel(time=slice(0,tt)).plot(ax=ax2)

ax2.set_xlim(ds.time.min(), ds.time.max())
ax2.set_ylim(ds_station.min(), ds_station.max())

ax1.set_aspect(1)
ax1.set_facecolor('0.5')
ax2.set_aspect(0.2)
ax1.set_title('');
ax2.set_title('Data at station');
fig.subplots_adjust(wspace=0.4)
```

!['static_example'](docs/pics/static.png)

All that is needed to wrap this into a function with the signature `func(ds, fig, timestamp, **kwargs)`, where `ds` is an xarray Dataset or DataArray, `fig` is a `matplotlib.figure` object and `timestamp` is an integer which indicates the movie frame.

```
def custom_plotfunc(ds, fig, tt):
    station = dict(x=100, y=150)
    ds_station = ds.sel(**station)

    (ax1, ax2) = fig.subplots(ncols=2)

    # Colorlimits need to be fixed or your video is going to cause seizures.
    # This is the only modification from the code above!
    ds.isel(time=tt).plot(ax=ax1, vmin=ds.min(), vmax=ds.max(), cmap='RdBu_r')
     
    ax1.plot(station['x'], station['y'], marker='*', color='k' ,markersize=15)
    ax1.text(station['x']+4, station['y']+4, 'Station', color='k' )
    ds_station.isel(time=slice(0,tt)).plot(ax=ax2)

    ax2.set_xlim(ds.time.min(), ds.time.max())
    ax2.set_ylim(ds_station.min(), ds_station.max())

    ax1.set_aspect(1)
    ax1.set_facecolor('0.5')
    ax2.set_aspect(0.2)
    ax1.set_title('');
    ax2.set_title('Data at station');
    fig.subplots_adjust(wspace=0.4)

mov_custom = Movie(ds, custom_plotfunc)
mov_custom.preview(2)
```
!['sweet_custom_plots'](docs/gifs/movie_custom.gif)

> Note: This animation looks terrible as a gif if using the suggested settings
> above. Instead use `! ffmpeg -y -i {moviename}.mp4 {moviename}.gif`
