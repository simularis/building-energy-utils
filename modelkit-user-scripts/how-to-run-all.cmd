
SETLOCAL
set "DEERROOT=%~dp0\.."
REM set "mycmd=call modelkit rake --dry-run"
set "mycmd=call modelkit rake"

set mydirs=^
  SFm_Furnace_1975 ^
  SFm_Furnace_1985 ^
  "SFm_SEER Rated AC_HP_1975" ^
  "SFm_SEER Rated AC_HP_1985"

REM call :compose
REM call :run
call :results
REM call :clean

ENDLOCAL
exit /b


:compose
REM Building the pxv and idf input files
for %%v in (%mydirs%) do (
  cd "%DEERROOT%\Analysis\%%~v"
  %mycmd% compose
  @echo on
)
exit /b

:run
for %%v in (%mydirs%) do (
  cd "%DEERROOT%\Analysis\%%~v"
  %mycmd% run
  @echo on
)
exit /b

:results
for %%v in (%mydirs%) do (
  cd "%DEERROOT%\Analysis\%%~v"
  %mycmd% results
  @echo on
)
exit /b

:clean
for %%v in (%mydirs%) do (
  cd "%DEERROOT%\Analysis\%%~v"
  %mycmd% clean
  @echo on
)
exit /b
