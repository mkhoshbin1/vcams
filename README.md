
![Banner logo for the VCAMS Package](https://github.com/mkhoshbin1/vcams/blob/main/images/logo%20and%20icon/logo/logo_tagline.png?raw=true)


[![PyPI](https://img.shields.io/pypi/v/vcams)](https://pypi.org/p/vcams/)
[![Docs](https://app.readthedocs.org/projects/vcams/badge/?version=latest)](https://vcams.readthedocs.io/en/latest/?badge=latest)
[![License](https://img.shields.io/github/license/mkhoshbin1/vcams)](https://github.com/mkhoshbin1/vcams/blob/main/LICENSE)
[![DOI](https://zenodo.org/badge/391829437.svg)](https://doi.org/10.5281/zenodo.17163176)
[![My Website](https://img.shields.io/badge/Author's_Website-blue.svg)](https://www.mkhoshbin.com)

## Introduction
VCAMS (Voxel-Based Computer-Aided Modeling of Complex Structures)
is a free and open source software for creating complex FEA models using voxels.

This software allows for accurate, fast, and reproducible modelling
and can be used and extended by anyone in accordance with the GNU AGPLv3 license.

Its main features are:

+ **Powerful Library**: The VCAMS library is simple but powerful, allowing for easy scripting
  which makes the results highly reproducible. Also, the scripts can be archived and shared with others.
+ **Simple GUI**: The *VCAMS GUI* is a simple but elegant graphical user interface that
  allows for easy creation of some of the more widely used structures.
+ **Fast**: VCAMS is very fast. It can create a model consisting of one million elements in less than a second!
+ **Thorough Documentation**: There are in-depth articles about all aspects of VCAMS in the online documentation.
+ **Free and Open Source**: VCAMS and its source code are provided free of charge under the GNU AGPLv3 license.
  You can download the source code and the executables on the project's GitHub page.
  
## How it Works
The software revolves around a main class named *VoxelPart* which defines a structure consisting of
a number of rectangular or cuboid elements.
This *VoxelPart* object can then be manipulated using a variety of methods to achieve a complex structure.
Afterward, the user can define custom element and node sets and  boundary conditions for the object.
And finally, the object is exported to an Abaqus™ input file.

## The VCAMS Library
The main part of the software is its powerful library which is
[very easy to install](https://pypi.org/p/vcams/) and has a complete reference guide.
It also comes with a large number of example problems.

## The Graphical User Interface
The graphical user interface (GUI) offers part of the library's functionality
in a simple and convenient manner.
It also allows the model parameters to be exported to a configuration file,
and imported later for modification or re-creation of the models.

## Software Documentation
You can find in-depth articles about modeling concepts, installation and usage,
and example problems in [the online documentation](https://vcams.readthedocs.io).
