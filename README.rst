NOTE: PRE ALPHA DO NOT USE

============
pycodeexport
============

.. image:: https://travis-ci.org/bjodah/pycodeexport.png?branch=master
   :target: https://travis-ci.org/bjodah/pycodeexport

pycodeexport bundles python convenience classes and functions for code-generation.
Developed with on the fly compilation (meta-programming) of math related problems 
using the SymPy package.

Installation
============
Example using pip (modify to your own needs):

    1. ``pip install --user --upgrade -r https://raw.github.com/bjodah/pycodeexport/master/requirements.txt``
    2. ``pip install --user --upgrade https://github.com/bjodah/pycodeexport/archive/master.tar.gz``


Templating
==========

Mako comes highly recommended as a template engine. For easier usage, a convenience method is provided in ``pycodeexport.util``.
The Code classes in ``pycodeexport.codeexport`` use this too.



Examples
========
Look at ``examples/*_main.py`` which show how pycodeexport can be used.

You may also look at other projects:

 - pycompilation_

.. _pycompilation: http://github.com/bjodah/pycompilation


License
=======
Open Source. Released under the very permissive simplified (2-clause) BSD license. 
See LICENSE.txt for further details.
