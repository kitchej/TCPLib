if (Test-Path env:VIRTUAL_ENV)
{
    pytest tests/
}
else{
    ./venv/scripts/Activate.ps1
    pytest tests/
    deactivate
}

