# Setup WSL2 Port Forwarding for OpenMPI
# This script must be run as Administrator in PowerShell on Windows
# Run this if you need external machines to connect to your WSL cluster

param(
    [switch]$Remove = $false
)

# Get WSL IP address
$wslIP = (wsl hostname -I).Trim()
Write-Host "WSL IP Address: $wslIP"

# Define port ranges for OpenMPI
$portStart = 50000
$portEnd = 50200

if ($Remove) {
    Write-Host "`nRemoving WSL port forwarding rules..."
    for ($port = $portStart; $port -le $portEnd; $port++) {
        netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>&1 | Out-Null
    }
    Write-Host "Port forwarding rules removed."
    Write-Host "`nCurrent port forwarding rules:"
    netsh interface portproxy show all
    exit
}

Write-Host "`n=== Setting up WSL2 Port Forwarding ==="
Write-Host "This will forward ports $portStart-$portEnd to WSL..."
Write-Host "Warning: This creates $(($portEnd - $portStart + 1)) forwarding rules."

$confirm = Read-Host "`nDo you want to continue? (yes/no)"
if ($confirm -ne "yes") {
    Write-Host "Cancelled."
    exit
}

# Clear existing rules in this range
Write-Host "`nClearing existing rules..."
for ($port = $portStart; $port -le $portEnd; $port++) {
    netsh interface portproxy delete v4tov4 listenport=$port listenaddress=0.0.0.0 2>&1 | Out-Null
}

# Add new rules
Write-Host "Adding port forwarding rules (this may take a minute)..."
$progressCount = 0
$totalPorts = $portEnd - $portStart + 1

for ($port = $portStart; $port -le $portEnd; $port++) {
    netsh interface portproxy add v4tov4 `
        listenport=$port `
        listenaddress=0.0.0.0 `
        connectport=$port `
        connectaddress=$wslIP 2>&1 | Out-Null

    $progressCount++
    if ($progressCount % 50 -eq 0) {
        $percent = [math]::Round(($progressCount / $totalPorts) * 100)
        Write-Host "  Progress: $percent% ($progressCount/$totalPorts ports)"
    }
}

Write-Host "`n=== Port Forwarding Setup Complete ==="
Write-Host "Ports $portStart-$portEnd are now forwarded to WSL at $wslIP"

Write-Host "`n=== Verification ==="
Write-Host "To verify, check the forwarding rules:"
Write-Host "  netsh interface portproxy show all | Select-String -Pattern '50'"

Write-Host "`n=== Important Notes ==="
Write-Host "1. These rules will be cleared when Windows restarts"
Write-Host "2. If WSL IP changes, you need to re-run this script"
Write-Host "3. To remove these rules, run:"
Write-Host "   .\setup_wsl_port_forwarding.ps1 -Remove"

Write-Host "`n=== Testing ==="
Write-Host "In WSL, you can now test MPI across your cluster:"
Write-Host "  mpirun -np 6 --hostfile ~/.openmpi/hostfile hostname"
