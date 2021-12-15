.. currentmodule:: xmovie

API Reference
=============

:class:`~xmovie.Movie` class
----------------------------


.. autosummary::
   :toctree: api/

   Movie

Presets
-------

Plot functions that can be supplied to the :class:`~xmovie.Movie` constructor
as the second positional argument.

They have a signature of the type:

.. code-block::

    plotfunc(da, fig, timestamp, framedim, **kwargs):
        ...

.. autosummary::
   :toctree: api/

   rotating_globe
   ~xmovie.presets.basic
