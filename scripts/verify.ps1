$ErrorActionPreference = "Stop"

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)]
        [scriptblock]$Command
    )

    & $Command
    if ($LASTEXITCODE -ne 0) {
        exit $LASTEXITCODE
    }
}

Invoke-Checked { python -m ruff check app app.py wsgi.py tests }
Invoke-Checked { python -m compileall app app.py wsgi.py }
Invoke-Checked { python -m pytest -q }
