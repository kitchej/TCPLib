param (
    [switch]$b, # If '-b' included, build/install only and skip tests
    [switch]$t  # If '-t' included, test only and skip build/install
                # If both included, will default to testing only
)

function run_tests{
   coverage run -m pytest -x -v
   coverage html
}

./.venv/scripts/Activate.ps1
$version = $version = py -c "import tomllib; print(tomllib.load(open('pyproject.toml','rb'))['project']['version'])"
$filepath = "dist\tcplib-$version-py3-none-any.whl"

if ($t) {
    run_tests
    exit
}

py -m build
pip install --force-reinstall $filepath

if (-not $b) {
    run_tests
}