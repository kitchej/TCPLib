param (
    [switch]$b, # If '-b' included, build/install only and skip tests
    [switch]$t # If '-t' included, test only and skip build/install
)

./.venv/scripts/Activate.ps1
$version = $version = py -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
$filepath = "dist/tcplib-$version-py3-none-any.whl"

if ($t) {
    pytest -x -v
    exit
}

py -m build
pip install --force-reinstall $filepath

if (-not $b) {
    pytest -x -v
}