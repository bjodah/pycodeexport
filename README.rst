pycodeexport
============

.. image:: https://travis-ci.org/bjodah/pycodeexport.png?branch=master
   :target: https://travis-ci.org/bjodah/pycodeexport
   :alt: Build status on Travis-CI
.. image:: http://hera.physchem.kth.se:9090/api/badges/bjodah/pycodeexport/status.svg
   :target: http://hera.physchem.kth.se:9090/bjodah/pycodeexport
   :alt: Build status on self-hosted Drone instance

pycodeexport bundles python convenience classes and functions for code-generation.
Developed to ease on-the-fly compilation (meta-programming) of math related problems 
using the SymPy package. Note that this package has an alpha development status.

Installation
------------
Example using pip (modify to your own needs):

::

   $ python3 -m pip install --user pycodeexport


Templating
----------
Mako_ comes highly recommended as a template engine. 
For easier usage, a convenience method is provided in ``pycodeexport.util``.
The ``Code`` classes in ``pycodeexport.codeexport`` use this too.

.. _Mako: http://www.makotemplates.org/


Examples
--------
Look at ``examples/*_main.py`` which show how pycodeexport can be used.

You may also look at other projects:

 - pycompilation_

.. _pycompilation: http://github.com/bjodah/pycompilation


License
-------
Open Source. Released under the very permissive simplified (2-clause) BSD license. 
See `LICENSE <LICENSE>`_ for further details.
