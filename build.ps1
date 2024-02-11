py -m build

if (Test-Path env:VIRTUAL_ENV)
{
    pip uninstall TCP-Lib --yes
    pip install --force-reinstall "dist/TCP_Lib-0.0.1-py3-none-any.whl"
}
else{
    ./venv/scripts/Activate.ps1
    pip uninstall TCP-Lib --yes
    pip install --force-reinstall "dist/TCP_Lib-0.0.1-py3-none-any.whl"
    deactivate
}

