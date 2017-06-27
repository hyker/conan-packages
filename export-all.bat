@echo off
for /r %%X in (*export.bat) do (
	setlocal
	cd %%~dpX
	call %%X
	endlocal
)