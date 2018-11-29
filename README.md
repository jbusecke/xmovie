# xmovie
A simple way of creating movies from [xarray](https://github.com/pydata/xarray) objects

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
objects with preset plotfunctions.
- Provide full customization of plots including animation of plot parameters
in time.
- Use [dask](https://github.com/dask/dask) for computationally efficient
frame rendering.
- WIP: Use [ffmpeg](https://www.ffmpeg.org/) to enable movie rendering from dataset
to finished movie file in jupyter notebooks (my preferred workflow).
