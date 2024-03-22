if (Test-Path env:VIRTUAL_ENV)
{
    ./build.ps1
    ./test.ps1
}
else{
    ./venv/scripts/Activate.ps1
    ./build.ps1
    ./test.ps1
    deactivate
}


