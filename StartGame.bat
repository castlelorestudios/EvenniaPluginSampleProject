@echo on
start "Server" "RunUnrealServer"
start "Evennia" "RunEvennia"
timeout 5 > NUL
start "Client" "RunUnrealClient"

