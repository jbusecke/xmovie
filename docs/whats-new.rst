What's New
==========
v0.3.0 (unreleased)
-------------------

Packaging
~~~~~~~~~
- ``cartopy`` (used in the :func:`~xmovie.rotating_globe` preset)
  and ``dask`` (used for parallel frame saving)
  are now optional extras instead of package requirements
  (:pull:`XX`).
  By `zmoon <https://github.com/zmoon>`_.

Documentation
~~~~~~~~~~~~~
- Sphinx docs build, published to Read the Docs (:pull:`67`).
  By `zmoon <https://github.com/zmoon>`_.

v0.2.0 (2021/4/20)
------------------

New Features
~~~~~~~~~~~~
- Enable saving frames in parallel using `xarray.map_blocks` (:pull:`35`).
  By `Tomas Chor <https://github.com/tomchor>`_ and `Julius Busecke <https://github.com/jbusecke>`_.

- Allow ``framedim`` to handle dimensions other than time (:pull:`32`).
  By `Timothy Smith <https://github.com/timothyas>`_.

Documentation
~~~~~~~~~~~~~
- Example showing ``framedim`` other than time (:pull:`32`).
  By `Timothy Smith <https://github.com/timothyas>`_.

Internal Changes
~~~~~~~~~~~~~~~~
- Add DOI (:pull:`27`).
  By `Julius Busecke <https://github.com/jbusecke>`_.

v0.1.0 (23 October 2020)
------------------------
Changes not documented for this release.

Initial release.
