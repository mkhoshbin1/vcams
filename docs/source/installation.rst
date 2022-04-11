.. _installation:

Installation
============
The software can be used as both a plugin to the Abaqus software or as a library for developing Abaqus scripts. Installation for either mode is very straightforward.

.. _installation_gui:

Installing the GUI Version
--------------------------
The GUI is shipped as a single portable executable (.exe file)
which contains the library and all of the dependencies.

To use the GUI version of VCAMS, you only need to download the last release from GitHub (TODO).
The program is portable and does not need any installation.
You can just open the executable file and use the program.

It is currently compiled only for Microsoft Windows,
but can be easily built from the source code on most platforms.


.. _installation_library:

Installing the VCAMS Library
----------------------------
For more advanced use cases, you need to obtain and use the main library.
This can be done either from the Python Package Index (TODO),
or by using the code from the GitHub repository (TODO).

Installing from PyPI
++++++++++++++++++++
The last version of the library is always available on PyPI
and can be installed or updated using the *pip* command.
This has the advantage that all dependencies will be installed
and updated which greatly simplifies the process.

It is generally a good practice to install libraries inside
a `virtual environment <https://docs.python.org/3/tutorial/venv.html>`__.
This allows for the library and its dependencies to be separate from
all other third-party libraries that are installed on Python.

Assuming that Python 3 is installed and is accessible using the ``py`` command,
and also assuming that you are using Microsoft Windows [1]_,
you can open a Powershell terminal in the the desired folder and then enter the following command:

.. code-block:: powershell

  # Create the virtual environment.
  py -m venv "venv"
  # Wait for the command to finish. It may take a while.
  # Activate the virtual environment.
  .\venv\Scripts\Activate.ps1

Now you can see the name of the virtual environment on the left side of the terminal.
This means that this version of Python is separate from the base version installed on your machine,
and everything will be confined to that folder which will prevent a lot of future complications.
Remember to activate the virtual environment everytime you want to use the library.

No you can install the program using the following command (TODO):

.. code-block:: powershell

  pip install vcams

Now the vcams library and all of its dependencies are installed in your virtual environment
and you can import vcams into your scripts. See the :ref:`examples` section for sample scripts.

Using the code from the Repository
++++++++++++++++++++++++++++++++++
Another method for using the library is downloading its source code directly from the GitHub repository.
To do this, you can download (or clone) the source code from the main branch or one of the releases
and then adding the folder containing the code the path of your Python program.

Note that for this to work, you need to install all of the packages in the library's
*requirements.txt* file. For most users, we don't recommend this method as it can get complicated.


.. [1] Linux users can use bash. The only difference is that they must
       use the file named *activate* instead of *Activate.ps1*.