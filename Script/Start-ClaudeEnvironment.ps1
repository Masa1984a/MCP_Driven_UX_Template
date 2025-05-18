# Notify script start
Write-Host "--- DevContainer Launch & Connection Script ---"
# --- Step 1: Start Podman machine ---
Write-Host "Starting Podman machine 'claudeVM'..."
try {
    # Podman machine start does nothing if already running
    # -q option suppresses output
    podman machine start claudeVM -q
    Write-Host "Podman machine is running or has been started."
} catch {
    Write-Error "Failed to start Podman machine: $($_.Exception.Message)"
    exit 1 # Exit script if an error occurs
}
# --- Step 2: Set default connection ---
Write-Host "Setting default Podman connection to 'claudeVM'..."
try {
    podman system connection default claudeVM
    Write-Host "Default connection set."
} catch {
    # This command may fail if already set or if the machine is not running
    # This might not be fatal in some cases, so treat as a warning
    Write-Warning "Failed to set default Podman connection (may already be set or machine issue): $($_.Exception.Message)"
    # Do not exit script here
}
# --- Step 3: Start DevContainer ---
Write-Host "Starting DevContainer in the current folder..."
try {
    # devcontainer up builds/starts the container and installs necessary tools
    # Progress will be displayed in standard output during execution
    devcontainer up --workspace-folder . --docker-path podman
    Write-Host "DevContainer startup process completed."
} catch {
    Write-Error "Failed to start DevContainer: $($_.Exception.Message)"
    exit 1 # Exit script if an error occurs
}
# --- Step 4: Get DevContainer container ID ---
Write-Host "Searching for DevContainer container ID..."
$currentFolder = (Get-Location).Path
# Identify container using label set by devcontainer up
# Extract only ID from `podman ps` output
# .Trim() removes any unnecessary whitespace from the retrieved string
$containerId = $(podman ps --filter "label=devcontainer.local_folder=$currentFolder" --format "{{.ID}}").Trim()
if (-not $containerId) {
    Write-Error "No DevContainer container ID found for the current folder ('$currentFolder')."
    Write-Error "Please verify that 'devcontainer up' completed successfully and the container is running."
    exit 1 # Exit script if container not found
}
Write-Host "Container ID found: $containerId"
# --- Step 5 & 6: Execute commands in container and enter interactive shell ---
Write-Host "Executing 'claude' command in container ($containerId) and then starting a zsh session..."
try {
    # podman exec -it starts an interactive session
    # zsh -c 'claude; exec zsh' means:
    #   Start zsh in non-interactive mode and execute the following commands
    #   'claude;' -> run the claude command
    #   'exec zsh' -> replace the current process (non-interactive zsh) with an interactive zsh
    # This will automatically display an interactive zsh prompt after the claude command executes.
    podman exec -it $containerId zsh -c 'claude; exec zsh'
    # The current PowerShell session will wait until the zsh session in the container ends.
    Write-Host "Interactive session ended."
} catch {
    Write-Error "Failed to execute command in container: $($_.Exception.Message)"
    exit 1 # Exit script if an error occurs
}
# Notify script end
Write-Host "--- Script Completed ---"
