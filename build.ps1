./venv/scripts/Activate.ps1
py -m build
pip uninstall TCP-Lib --yes
pip install --force-reinstall "dist/TCP_Lib-2.0.0-py3-none-any.whl"
./venv/scripts/Activate.ps1