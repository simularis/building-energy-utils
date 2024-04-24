set "newname=newclone"
git clone https://github.com/simularis/DEER-Prototypes-EnergyPlus.git %newname%
cd %newname%
git remote rename origin solaris

git remote add dnv https://github.com/sound-data/DEER-Prototypes-EnergyPlus.git
git fetch dnv

REM Note that lines beginning with REM (remark) are comments and are not executed.

REM To create a new branch starting from the currently active one:
REM git branch %newname%

REM To checkout a specific branch, uncomment the next line and specify the branch name:
git checkout main

REM To open up the Git Gui application, enter this command:
REM git gui
