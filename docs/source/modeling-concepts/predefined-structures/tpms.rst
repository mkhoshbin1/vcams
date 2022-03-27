.. _predefined-tpms:

Triply Periodic Minimal Surfaces
================================
`Triply Periodic Minimal Surfaces (TPMS) <https://en.wikipedia.org/wiki/Triply_periodic_minimal_surface>`__
are a class of 3D minimal surfaces that are used for modeling various porous structures.
Some of them can be described using level-set equations
(similar to the ones accepted by the :func:`~vcams.mask.function.mask_from_function` function)
and because of their usefulness, have been implemented in the library.

Similar to :doc:`shape`, an `abstract base class <https://en.wikipedia.org/wiki/Abstract_type>`__
has been implemented that outlines the necessary properties that must be defined in a subclass.
These include a number of cosmetic properties used for representing the surface in the GUI,
and the *func* method which is a static function that has to be passed to
the :func:`~vcams.mask.function.mask_from_function` function for use.
Also, a number of additional parameters are necessary which must be passed as well.
An example of a model created based on a Gyroid TPMS is shown in :doc:`Example C-5 </examples/example-c5>`.

Currently, the following surfaces have been implemented:

+ :class:`The Schwarz Primitive (P) TPMS <vcams.mask.tpms.TpmsSchwarzP>`
+ :class:`The Schwarz Diamond (D) TPMS <vcams.mask.tpms.TpmsSchwarzD>`
+ :class:`The Schwarz Gyroid (G) TPMS <vcams.mask.tpms.TpmsSchwarzG>`

If you would like to add more surfaces to VCAMS, check out our contributing guidelines.