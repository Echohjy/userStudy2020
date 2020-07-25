### At the very beginning, many thanks for participating in our study.
This document is aimed to help you build the environment required for running the study. 
As a whole, the whole program is written in Python, along with pyqt5 and vtk.

<br>

# Mac User

If you have installed python3 and pip, then skip to *C*.

Else if you have installed python but not pip, skip to *B*.

Else, start from *A*.

----


### A. Install homebrew
1. Open the Terminal app. Type `ruby -e "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/master/install)"` 
You’ll see messages in the Terminal explaining what you need to do to complete the installation process.

### B. Install python and pip
1. Open the Terminal. Enter `brew install python`
2. Enter `curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py`

### C. Install pyqt5 and vtk

1. Open the Terminal and enter: `pip install pyqt5` and `pip install vtk`

### D. Run the program

1. In the Terminal, navigate to the study code folder. Enter: `python3 controller.py`

2. CHEERS! You should have seen the interface now!





# Windows User
Please first check your machine is 64-bit rather than 32-bit. The project requires 64-bit Windows.

How to check:

1. Open a file explorer window.
2. On the left, right-click This PC.
3. In the context menu, select Properties. Then the System Properties window opens.
4. In the System Properties window, find your System type.


-----

If you have installed python and pip, then skip to *C*.

Else if you have installed python but not pip, skip to *B*.

Else, start from *A*.

----

If your operating system is 64-bit, then you could start setting up the environment. 

### A. Install Python
1. Install python from the official website: 
https://www.python.org/downloads/release/python-382/
Scroll down and select the version: *Windows x86-64 executable installer*

    REMEMBER TO INSTALL PYTHON IN A FILE YOU KNOW

2. Enter into the folder you have installed
    e.g. C:\Users\yourname\AppData\Local\Programs\Python\Python38


3. Add python path to the python executable file to the Path variable.

    a. start the *RUN* box and enter *sysdm.cpl*

    b. this should open up the *System Properties* window. Go to the *Advanced* tab and click the *Environment Variables* button

    c. In the *System variable* window, find the *Path* variable and click *Edit* button

    d. Position your cursor at the end of the Variable value line and add the path to the *python.exe* file, preceeded with the semicolon character (;) For example, we add the following value: *;C:\Users\yourname\AppData\Local\Programs\Python\Python38*

### B. Install pip

1. Open a command prompt and navigate to the study code folder

2. Run the following command: *python get-pip.py*

3. Add pip path into Path variable. Same procedure with StepA3. The example value would be: *;C:\Users\yourname\AppData\Local\Programs\Python\Python38\Scripts*

### C. Install pyqt5 and vtk

1. Open a command prompt and enter: *pip install pyqt5* and *pip install vtk*

### D. Run the program

1. Download the whole directory from this page.

2. In the command prompt, navigate to the study code folder. Enter: *python controller.py*

3. CHEERS! You should have seen the interface now!
