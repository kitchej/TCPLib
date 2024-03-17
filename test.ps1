if (Test-Path env:VIRTUAL_ENV)
{
    cd tests
    pytest
    cd ..
}
else{
    ./venv/scripts/Activate.ps1
    cd tests
    pytest
    cd ..
    deactivate
}

