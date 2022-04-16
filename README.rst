whl
===

Quickly makes Python wheels_ from a bunch of .py files without needing a ``setup.py`` at all.

**You probably don't want to use this**. It's intentionally minimal for my own use-cases, and doesn't have many features yet (no support for entrypoints, dependencies, extras). If all you're looking for is a fast build, then consider using [`flit build --format wheel`](https://flit.pypa.io/en/latest/) with a ``pyproject.toml`` file which is almost as fast.

Usage
-----

For a single file distribution:

.. code-block:: python

   python whl.py path/to/myfile.py

For a package (directory with an ``__init__.py`` file in it):

.. code-block:: python

   python whl.py path/to/dir

``whl.py`` will look in some sensible places to autodetect the package name/version.

Rationale
---------

If all you want to do is package some ``.py`` file(s) into a ``.whl``, that's essentially just making a zipfile. Executing a setuptools_ / distutils_ style installer script or a PEP517_ / PEP518_ style build system is bloated with features which you don't need, and it can be done much cheaper/faster:

.. code-block:: bash

   $ time python whl.py mypkg
   ./mypkg-0.1-py2.py3-none-any.whl
   python whl.py mypkg  0.06s user 0.02s system 86% cpu 0.091 total

Compared with doing things the correct_ way:

.. code-block:: bash

   $ time python -m build --wheel .
   * Creating venv isolated environment...
   ...
   <blah blah>
   ...
   Successfully built mypkg-0.1-py2.py3-none-any.whl
   python -m build --wheel .  5.05s user 0.53s system 96% cpu 5.776 total

.. _wheels: https://packaging.python.org/en/latest/guides/distributing-packages-using-setuptools/#wheels
.. _correct: https://pypi.org/project/build/
.. _setuptools: https://setuptools.pypa.io/en/latest/
.. _distutils: https://docs.python.org/3/library/distutils.html
.. _PEP517: https://peps.python.org/pep-0517/
.. _PEP518: https://peps.python.org/pep-0518/
