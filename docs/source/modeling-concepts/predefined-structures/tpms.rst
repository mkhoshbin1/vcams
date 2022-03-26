.. _predefined-tpms:

Triply Periodic Minimal Surfaces
================================
`Triply Periodic Minimal Surfaces (TPMS) <https://en.wikipedia.org/wiki/Triply_periodic_minimal_surface>`__
are a class of 3D minimal surfaces that are used for modeling various porous structures.
Some of them can be described using level-set equations (similar to the ones accepted by TODO)
and because of their usefulness, have been implemented in the library.

Similar to :doc:`shape`, an `abstract base class <https://en.wikipedia.org/wiki/Abstract_type>`__
has been implemented that outlines the necessary properties that must be defined in a subclass.
These include a number of cosmetic properties used for representing the surface in the GUI,
and the *func* method which is a static function that has to be passed to the mask_from_function TODO
method for use. Also, a number of additional parameters are necessary which must be passed as well.

An example of a model based on a TPMS formula is shown in TODO.
Currently, the following surfaces have been implemented:
TODO