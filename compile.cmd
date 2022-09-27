c:
cd \projects\ba-parse
del /f /q .\output\*.exe
.\venv\Scripts\auto-py-to-exe -c c:\projects\ba-parse\auto-py-to-exe.json
move .\output\main.exe .\output\ba-parse.exe


