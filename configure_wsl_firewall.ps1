# Configure Windows Firewall for OpenMPI on WSL
# This script must be run as Administrator in PowerShell on Windows

Write-Host "=== WSL Hyper-V Firewall Configuration ==="
Write-Host "Configuring WSL Hyper-V VM firewall to allow inbound connections..."
Write-Host "This is CRITICAL for MPI cross-cluster communication on WSL!"

# Enable WSL Hyper-V VM to accept inbound connections
# Reference: https://learn.microsoft.com/en-us/windows/wsl/networking
try {
    # Get all WSL VM settings
    $vmSettings = Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore

    if ($vmSettings) {
        Write-Host "`nFound WSL Hyper-V VM settings:"
        foreach ($vm in $vmSettings) {
            Write-Host "  VM: $($vm.Name)"
            Write-Host "  Current DefaultInboundAction: $($vm.DefaultInboundAction)"

            # Set to Allow for each WSL instance
            Set-NetFirewallHyperVVMSetting -Name $vm.Name -DefaultInboundAction Allow -PolicyStore ActiveStore
            Write-Host "  Updated DefaultInboundAction: Allow" -ForegroundColor Green
        }
    } else {
        Write-Host "No Hyper-V VM settings found. WSL may not be running." -ForegroundColor Yellow
    }
} catch {
    Write-Host "Error configuring Hyper-V VM firewall: $_" -ForegroundColor Red
    Write-Host "This may require WSL to be running and administrator privileges."
}

Write-Host "`n=== Standard Firewall Rules ==="

# Get WSL IP address
try {
    $wslIP = (wsl hostname -I 2>$null).Trim()
    if ([string]::IsNullOrWhiteSpace($wslIP)) {
        $wslIP = "Not detected (WSL may not be running)"
    }
} catch {
    $wslIP = "Not detected"
}
Write-Host "WSL IP Address: $wslIP"

# Define port ranges for OpenMPI
$mpiPorts = @(
    @{Name="OpenMPI-BTL-TCP"; Protocol="TCP"; Port="50000-50100"; Description="OpenMPI BTL TCP Communication"},
    @{Name="OpenMPI-OOB-TCP"; Protocol="TCP"; Port="50100-50200"; Description="OpenMPI OOB/PRRTE Communication"}
)

Write-Host "`nConfiguring Windows Firewall rules for OpenMPI on WSL..."

foreach ($portRule in $mpiPorts) {
    $ruleName = "WSL2-$($portRule.Name)"

    # Remove existing rule if it exists
    $existingRule = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
    if ($existingRule) {
        Write-Host "Removing existing rule: $ruleName"
        Remove-NetFirewallRule -DisplayName $ruleName
    }

    # Create inbound rule
    Write-Host "Creating inbound rule: $ruleName"
    New-NetFirewallRule -DisplayName $ruleName `
        -Direction Inbound `
        -LocalPort $portRule.Port `
        -Protocol $portRule.Protocol `
        -Action Allow `
        -Profile Any `
        -Description $portRule.Description

    # Create outbound rule
    Write-Host "Creating outbound rule: $ruleName (Outbound)"
    New-NetFirewallRule -DisplayName "$ruleName-Outbound" `
        -Direction Outbound `
        -LocalPort $portRule.Port `
        -Protocol $portRule.Protocol `
        -Action Allow `
        -Profile Any `
        -Description "$($portRule.Description) (Outbound)"
}

Write-Host "`n=== Port Forwarding Configuration ==="
Write-Host "For WSL2 to receive connections from outside Windows host,"
Write-Host "you may need to configure port forwarding using netsh."
Write-Host "`nExample command to forward ports (run as Administrator):"
Write-Host "netsh interface portproxy add v4tov4 listenport=50000 listenaddress=0.0.0.0 connectport=50000 connectaddress=$wslIP"
Write-Host "`nTo forward the full range, you would need to run this for each port."
Write-Host "However, for local cluster testing within WSL, firewall rules should suffice."

Write-Host "`n=== Verification ==="
Write-Host "Configuration completed successfully!" -ForegroundColor Green
Write-Host "`nIMPORTANT: The Hyper-V VM firewall setting is CRITICAL for MPI to work!"
Write-Host "Without 'DefaultInboundAction Allow', MPI daemon communication will fail."

Write-Host "`nRun the following in WSL to verify MPI:"
Write-Host "  mpirun -np 6 --host 192.168.1.147,192.168.1.139,192.168.1.96 \"
Write-Host "    --oversubscribe --map-by node \"
Write-Host "    --mca btl_tcp_if_include 192.168.1.0/24 hostname"

Write-Host "`n=== Manual Port Forwarding (if needed) ==="
Write-Host "If you need external access to the cluster, run this script:"
Write-Host "  .\setup_wsl_port_forwarding.ps1"

Write-Host "`n=== To Verify Hyper-V VM Settings ==="
Write-Host "Run: Get-NetFirewallHyperVVMSetting -PolicyStore ActiveStore"
Write-Host "All WSL VMs should show: DefaultInboundAction : Allow"
