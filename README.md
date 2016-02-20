# Fotolog Archiver v 2.0


For the nostalgic in you, a Python script that crawls your fotolog images and guestbook comments.

Based on the original script by will luo, from http://www.wluo.org/fotologarchiver/

### What it does


The script downloads the HTML pages from a fotolog user's account and creates new (SIMPLE) HTML files with the pictures and guestbook entries. These new HTML files, along with the crawled pictures, are stored in a folder in the user's computer.

### Requirements


* Python 2.7
* the Python `requests` library

### Usage

#### Windows users
Once you've installed Python 2.7 and the `requests` library, download and save the script to your computer. To run it, open the command line `(Search > cmd > Enter)`, write the path to the python executable and the path to the script. Something like:

`C:\Python27\python.exe C:\Users\Your-user\Desktop\getfotolog.py`

These paths may vary depending on where you put the files into your computer.

The script will prompt you for a starting URL to start crawling. You must provide a URL in the following form: `http://www.fotolog.com/useraccount/photonumberid/` (the number at the end is necessary). 

The software will then start crawling the files, from the URL you entered until the **oldest** photo is reached. This may take several minutes depending on the number of pictures that were previously uploaded to the account.

After the program completes its task, there should be a file called `start.html` in the same folder where the photos and pages were saved. Now you can open that with your favorite browser and remember old times (:

#### Linux/Mac

You probably know how to run a python script :P just provide the starting URL as described above.

### Known problems/possible improvements

Unfortunately, you can only go from one photo to the previous or the next one; there is no way to see all photos in a calendar grid as provided originally by fotolog. Nevertheless, you can just open any of the HTML files created and use that as a starting point, if you don't want to go through all your timeline.
A
lso, I didn't have the time to remove the user avatars from the guestbook, so they will appear as broken links once fotolog shuts down for good ):