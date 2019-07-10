@echo on
(
set /p uepath=
)< Config.txt
start "Client" "%uepath%\Engine\Binaries\Win64\UE4Editor.exe" "%cd%\EvenniaSampleProject.uproject" 127.0.0.1 -game -log -nosteam

