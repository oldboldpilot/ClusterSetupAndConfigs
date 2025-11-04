#!/usr/bin/env python3.14
"""
Terminal-based UI for cluster setup using Textual framework.
"""

import os
import sys
from pathlib import Path
from typing import Optional
import threading
import queue

from textual.app import App, ComposeResult
from textual.containers import Container, Vertical, Horizontal, ScrollableContainer
from textual.widgets import Header, Footer, Button, Input, Label, Static, DirectoryTree, RichLog
from textual.binding import Binding
from textual.screen import ModalScreen
from textual import on

# Import YAML for validation
try:
    import yaml
except ImportError:
    yaml = None

# Import the cluster setup module
from cluster_setup import ClusterSetup, load_yaml_config


class FilePickerScreen(ModalScreen[Optional[str]]):
    """Modal screen for file selection"""
    
    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
    ]
    
    def __init__(self, starting_path: str = ".") -> None:
        super().__init__()
        self.starting_path = starting_path
    
    def compose(self) -> ComposeResult:
        with Container(id="file-picker-dialog"):
            yield Label("Select Configuration File", id="picker-title")
            yield DirectoryTree(self.starting_path, id="file-tree")
            with Horizontal(id="picker-buttons"):
                yield Button("Select", variant="primary", id="select-btn")
                yield Button("Cancel", variant="default", id="cancel-btn")
    
    @on(Button.Pressed, "#select-btn")
    def select_file(self) -> None:
        tree = self.query_one(DirectoryTree)
        if tree.cursor_node and tree.cursor_node.data and tree.cursor_node.data.path.is_file():
            file_path = str(tree.cursor_node.data.path)
            if file_path.endswith(('.yaml', '.yml')):
                self.dismiss(file_path)
            else:
                self.notify("Please select a YAML file (.yaml or .yml)", severity="warning")
        else:
            self.notify("Please select a valid file", severity="warning")
    
    @on(Button.Pressed, "#cancel-btn")
    def cancel_selection(self) -> None:
        self.action_cancel()
    
    def action_cancel(self) -> None:
        self.dismiss(None)


class ClusterSetupUI(App):
    """Textual UI for cluster setup"""
    
    CSS = """
    Screen {
        align: center middle;
    }
    
    #main-container {
        width: 100%;
        height: 100%;
        padding: 1 2;
    }
    
    #title {
        text-align: center;
        text-style: bold;
        color: $accent;
        margin: 1 0;
    }
    
    .section {
        border: solid $primary;
        padding: 1 2;
        margin: 1 0;
        height: auto;
    }
    
    .section-title {
        text-style: bold;
        color: $accent;
        margin-bottom: 1;
    }
    
    .field-label {
        width: 20;
        margin: 0 1 0 0;
    }
    
    .field-row {
        height: auto;
        margin: 1 0;
    }
    
    Input {
        width: 60;
    }
    
    #config-file-input {
        width: 50;
    }
    
    #browse-btn {
        margin-left: 1;
        min-width: 12;
    }
    
    #config-info {
        margin-top: 1;
        padding: 1;
        background: $surface;
        color: $text-muted;
        height: auto;
    }
    
    #action-buttons {
        align: center middle;
        margin: 2 0;
        height: auto;
    }
    
    Button {
        margin: 0 1;
    }
    
    #log-container {
        height: 20;
        border: solid $primary;
        margin: 1 0;
    }
    
    #log-title {
        text-style: bold;
        color: $accent;
        padding: 0 1;
    }
    
    RichLog {
        height: 100%;
    }
    
    #file-picker-dialog {
        width: 80;
        height: 80%;
        border: thick $background 80%;
        background: $surface;
        padding: 1 2;
    }
    
    #picker-title {
        text-style: bold;
        color: $accent;
        text-align: center;
        margin-bottom: 1;
    }
    
    #file-tree {
        height: 1fr;
        margin: 1 0;
    }
    
    #picker-buttons {
        align: center middle;
        height: auto;
        margin-top: 1;
    }
    """
    
    BINDINGS = [
        Binding("q", "quit", "Quit"),
        Binding("ctrl+c", "quit", "Quit"),
    ]
    
    def __init__(self):
        super().__init__()
        self.config_file: Optional[str] = None
        self.password: Optional[str] = None
        self.setup_thread: Optional[threading.Thread] = None
        self.setup_running = False
        self.log_queue = queue.Queue()
    
    def compose(self) -> ComposeResult:
        yield Header()
        with ScrollableContainer(id="main-container"):
            yield Label("Cluster Setup - Slurm & OpenMPI", id="title")
            
            # Configuration file section
            with Vertical(classes="section"):
                yield Label("Configuration File", classes="section-title")
                with Horizontal(classes="field-row"):
                    yield Label("YAML Config:", classes="field-label")
                    yield Input(placeholder="Path to cluster_config.yaml", id="config-file-input")
                    yield Button("Browse...", id="browse-btn")
                yield Static("", id="config-info")
            
            # Password section
            with Vertical(classes="section"):
                yield Label("Authentication", classes="section-title")
                with Horizontal(classes="field-row"):
                    yield Label("Password:", classes="field-label")
                    yield Input(placeholder="Password for worker nodes", password=True, id="password-input")
                yield Label("⚠ Required for automatic worker setup via SSH", id="password-note")
            
            # Action buttons
            with Horizontal(id="action-buttons"):
                yield Button("Setup Cluster", variant="primary", id="setup-btn")
                yield Button("Validate Config", variant="default", id="validate-btn")
                yield Button("Clear", variant="default", id="clear-btn")
            
            # Log output
            with Vertical(id="log-container"):
                yield Label("Setup Log", id="log-title")
                yield RichLog(id="setup-log", wrap=True, highlight=True, markup=True)
        
        yield Footer()
    
    def on_mount(self) -> None:
        """Set up the UI after mounting"""
        self.query_one("#setup-log", RichLog).write("Welcome to Cluster Setup UI")
        self.query_one("#setup-log", RichLog).write("Select a configuration file to begin...")
        
        # Set focus to config file input
        self.query_one("#config-file-input", Input).focus()
    
    @on(Button.Pressed, "#browse-btn")
    def show_file_picker(self) -> None:
        """Show file picker dialog"""
        current_path = self.query_one("#config-file-input", Input).value
        starting_path = str(Path(current_path).parent) if current_path else "."
        
        def handle_selection(file_path: Optional[str]) -> None:
            if file_path:
                self.query_one("#config-file-input", Input).value = file_path
                self.validate_config_file(file_path)
        
        self.push_screen(FilePickerScreen(starting_path), handle_selection)
    
    @on(Input.Changed, "#config-file-input")
    def config_file_changed(self, event: Input.Changed) -> None:
        """Handle config file input change"""
        if event.value and Path(event.value).exists():
            self.validate_config_file(event.value)
    
    @on(Input.Changed, "#password-input")
    def password_changed(self, event: Input.Changed) -> None:
        """Handle password input change"""
        self.password = event.value if event.value else None
    
    def validate_config_file(self, file_path: str) -> bool:
        """Validate the configuration file"""
        log = self.query_one("#setup-log", RichLog)
        config_info = self.query_one("#config-info", Static)
        
        try:
            if not Path(file_path).exists():
                config_info.update("[red]✗[/red] File not found")
                log.write(f"[red]Error:[/red] File not found: {file_path}")
                return False
            
            # Load and validate YAML
            config = load_yaml_config(file_path)
            
            master = config.get('master')
            workers = config.get('workers', [])
            username = config.get('username', 'current user')
            
            # Handle new format where master and workers contain IP and OS info
            master_ip = master.get('ip') if isinstance(master, dict) else master
            worker_list = []
            if isinstance(workers, list):
                for w in workers:
                    if isinstance(w, dict):
                        worker_list.append(w.get('ip'))
                    else:
                        worker_list.append(w)
            else:
                worker_list = workers
            
            if not master or not workers:
                config_info.update("[red]✗[/red] Invalid config: missing master or workers")
                log.write("[red]Error:[/red] Config must contain 'master' and 'workers' fields")
                return False
            
            # Display config info
            info_text = f"[green]✓[/green] Valid configuration\n"
            info_text += f"  Master: {master_ip}\n"
            info_text += f"  Workers: {', '.join(str(w) for w in worker_list)}\n"
            info_text += f"  Username: {username}"
            config_info.update(info_text)
            
            log.write(f"[green]✓[/green] Configuration file validated: {file_path}")
            log.write(f"  Master: {master}")
            log.write(f"  Workers: {len(workers)} node(s)")
            
            self.config_file = file_path
            return True
            
        except Exception as e:
            config_info.update(f"[red]✗[/red] Error: {str(e)}")
            log.write(f"[red]Error:[/red] Failed to validate config: {e}")
            return False
    
    @on(Button.Pressed, "#validate-btn")
    def validate_button_pressed(self) -> None:
        """Handle validate button press"""
        config_file = self.query_one("#config-file-input", Input).value
        if not config_file:
            self.notify("Please select a configuration file", severity="warning")
            return
        
        self.validate_config_file(config_file)
    
    @on(Button.Pressed, "#clear-btn")
    def clear_form(self) -> None:
        """Clear the form"""
        self.query_one("#config-file-input", Input).value = ""
        self.query_one("#password-input", Input).value = ""
        self.query_one("#config-info", Static).update("")
        self.query_one("#setup-log", RichLog).clear()
        self.query_one("#setup-log", RichLog).write("Form cleared. Ready for new configuration.")
        self.config_file = None
        self.password = None
    
    @on(Button.Pressed, "#setup-btn")
    def start_setup(self) -> None:
        """Start the cluster setup process"""
        if self.setup_running:
            self.notify("Setup is already running", severity="warning")
            return
        
        config_file = self.query_one("#config-file-input", Input).value
        password = self.query_one("#password-input", Input).value
        
        if not config_file:
            self.notify("Please select a configuration file", severity="error")
            return
        
        if not Path(config_file).exists():
            self.notify("Configuration file not found", severity="error")
            return
        
        if not password:
            response = self.notify(
                "No password provided. Automatic worker setup will be skipped. Continue?",
                severity="warning",
                timeout=5
            )
        
        # Validate config one more time
        if not self.validate_config_file(config_file):
            self.notify("Invalid configuration file", severity="error")
            return
        
        # Start setup in background thread
        self.setup_running = True
        self.query_one("#setup-btn", Button).disabled = True
        self.notify("⚙ Cluster setup started...", severity="information")
        
        log = self.query_one("#setup-log", RichLog)
        log.write("\n[bold cyan]" + "="*60 + "[/bold cyan]")
        log.write("[bold cyan]⚙ CLUSTER SETUP STARTED[/bold cyan]")
        log.write("[bold cyan]" + "="*60 + "[/bold cyan]\n")
        log.write("[yellow]Setup is now running. This may take several minutes...[/yellow]\n")
        
        self.setup_thread = threading.Thread(
            target=self.run_setup,
            args=(config_file, password),
            daemon=True
        )
        self.setup_thread.start()
        
        # Start log monitoring
        self.set_interval(0.1, self.check_log_queue)
    
    def run_setup(self, config_file: str, password: Optional[str]) -> None:
        """Run the cluster setup in a background thread"""
        try:
            # Redirect stdout to capture setup output
            import io
            from contextlib import redirect_stdout, redirect_stderr
            
            # Load config
            config = load_yaml_config(config_file)
            master = config.get('master')
            workers = config.get('workers', [])
            username = config.get('username')
            
            # Handle new format where master and workers contain IP and OS info
            if isinstance(master, dict):
                master = master.get('ip')
            
            if isinstance(workers, str):
                workers = workers.split()
            elif isinstance(workers, list) and workers and isinstance(workers[0], dict):
                # Extract IPs from list of dicts
                workers = [w.get('ip') if isinstance(w, dict) else w for w in workers]
            
            # Validate required fields
            if not master or not workers:
                self.log_queue.put(("error", "Invalid config: missing master or workers"))
                self.log_queue.put(("complete", False))
                return
            
            # Create setup instance
            setup = ClusterSetup(master, workers, username, password)
            
            # Capture output
            output_buffer = io.StringIO()
            
            def capture_and_queue(text):
                output_buffer.write(text + "\n")
                self.log_queue.put(("info", text))
            
            # Override print for setup
            original_print = print
            
            def custom_print(*args, **kwargs):
                text = " ".join(str(arg) for arg in args)
                self.log_queue.put(("info", text))
                original_print(*args, **kwargs)
            
            # Monkey patch print temporarily
            import builtins
            builtins.print = custom_print
            
            try:
                # Run setup
                setup.run_full_setup(config_file=config_file)
                self.log_queue.put(("success", "\n✓ Cluster setup completed successfully!"))
            finally:
                # Restore original print
                builtins.print = original_print
            
        except Exception as e:
            self.log_queue.put(("error", f"\n✗ Setup failed: {str(e)}"))
            import traceback
            self.log_queue.put(("error", traceback.format_exc()))
        finally:
            self.log_queue.put(("done", None))
    
    def check_log_queue(self) -> None:
        """Check for new log messages"""
        try:
            while True:
                msg_type, message = self.log_queue.get_nowait()
                
                if msg_type == "done":
                    self.setup_running = False
                    self.query_one("#setup-btn", Button).disabled = False
                    
                    # Show completion notification
                    log = self.query_one("#setup-log", RichLog)
                    log.write("\n[bold cyan]" + "="*60 + "[/bold cyan]")
                    log.write("[bold green]✓ SETUP PROCESS COMPLETED[/bold green]")
                    log.write("[bold cyan]" + "="*60 + "[/bold cyan]\n")
                    log.write("[yellow]The cluster setup script has finished executing.[/yellow]")
                    log.write("[yellow]Check the log above for details and any errors.[/yellow]")
                    log.write("[yellow]You can close this window or start a new setup.[/yellow]\n")
                    
                    # Show notification
                    self.notify("✓ Cluster setup completed!", severity="information", timeout=10)
                    return
                
                log = self.query_one("#setup-log", RichLog)
                
                if msg_type == "error":
                    log.write(f"[red]{message}[/red]")
                elif msg_type == "success":
                    log.write(f"[green]{message}[/green]")
                else:
                    log.write(message)
                    
        except queue.Empty:
            pass


def main():
    """Main entry point for the UI"""
    app = ClusterSetupUI()
    app.run()


if __name__ == '__main__':
    main()
