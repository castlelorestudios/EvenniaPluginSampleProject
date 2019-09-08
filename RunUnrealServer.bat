@echo on
(
set /p uepath=
)< Config.txt
start "Server" "%uepath%\Engine\Binaries\Win64\UE4Editor.exe" "%cd%\EvenniaSampleProject.uproject" EvenniaMenu -server -log -nosteam

