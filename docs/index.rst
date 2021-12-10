xmovie: movies from `xarray`_ objects
=====================================

.. toctree::
   :maxdepth: 2
   :caption: For users
   :hidden:

   examples
   api
   whats-new
   GitHub repository <https://github.com/jbusecke/xmovie>


*A simple way of creating beautiful movies from xarray objects.*


.. figure:: examples/movie_rotating.gif

   Rotating globe :ref:`preset <api:Presets>` example.
   See :doc:`examples/quickstart`.


Overview
--------

With ever-increasing detail, modern scientific observations and model results
lend themselves to visualization in the form of movies.

Not only is a beautiful movie a fantastic way to wake up the crowd on a Friday
afternoon of a weeklong conference, but it can also speed up the discovery
process, since our eyes are amazing image processing devices.

This module aims to facilitate movie rendering from data objects based on
:doc:`xarray objects <xarray:user-guide/data-structures>`.

Xarray already provides :doc:`a way <xarray:user-guide/plotting>`
to create quick and beautiful static images from your data using `Matplotlib`_.
`Various packages <https://matplotlib.org/mpl-third-party/#animations>`_
provide facilities for animating Matplotlib figures.

But it can become tedious to customize plots, particularly when map projections are used.

The main aims of this module are:

- Enable quick but high-quality movie frame creation from existing xarray
  objects with preset plot functions---create a movie with only 2 lines of code.
- Provide high quality, customizable presets to create stunning visualizations with minimal setup.
- Convert your static plot workflow to a movie with only a few lines of code,
  while maintaining all the flexibility of `xarray`_
  and `Matplotlib`_.
- Optionally, use `Dask`_ for parallelized frame rendering.


Installation
------------

.. note::

   For now, ``dask(-core)`` and ``cartopy`` are included with ``xmovie``,
   but they may be optional dependencies in the future.

Conda
~~~~~

The easiest way to install ``xmovie`` is via ``conda``:

.. prompt:: bash

   conda install -c conda-forge xmovie

Pip
~~~

You can also install via ``pip``:

.. prompt:: bash

   pip install xmovie

Latest
~~~~~~

If you want to install the latest version from GitHub, simply run

.. prompt:: bash

   pip install git+https://github.com/jbusecke/xmovie.git

.. note::
   
   If you dont have
   `ssh keys set up <https://help.github.com/en/articles/adding-a-new-ssh-key-to-your-github-account>`_,
   you can use
   
   .. prompt:: bash
   
      git clone https://github.com/jbusecke/xmovie.git`

   and enter your github password.


.. _xarray: https://xarray.pydata.org
.. _Matplotlib: https://matplotlib.org
.. _Dask: https://dask.org
