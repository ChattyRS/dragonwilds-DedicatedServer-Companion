@echo off

for /f "usebackq delims=" %%i in (`
  PowerShell -Command "get-date" -format "yyyy-MM-dd_HHmmss"
`) do set _timestamp=%%i

cd %~dp0

set "source=.\RSDragonwilds\Saved\SaveGames\Chinchompa.sav"
set "dest_dir=\\DS1522\Media\Saves\Dragonwilds\"

copy "%source%" "%dest_dir%Chinchompa_%_timestamp%.sav"

echo File copied and renamed to Chinchompa_%_timestamp%.sav successfully.