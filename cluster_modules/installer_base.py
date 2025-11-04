"""
Base installer class for software components

Provides common installation patterns and utilities.
"""

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional

from .core import ClusterCore


class InstallerBase(ABC):
    """Abstract base class for software installers"""
    
    def __init__(self, core: ClusterCore):
        """
        Initialize installer
        
        Args:
            core: ClusterCore instance
        """
        self.core = core
    
    @abstractmethod
    def install(self):
        """Install the software component"""
        pass
    
    @abstractmethod
    def configure(self):
        """Configure the software component"""
        pass
    
    @abstractmethod
    def verify(self) -> bool:
        """Verify installation
        
        Returns:
            True if installation is successful
        """
        pass
    
    def is_installed(self, command: str) -> bool:
        """Check if a command/package is installed
        
        Args:
            command: Command name to check
            
        Returns:
            True if command exists
        """
        result = self.core.run_command(f"which {command}", check=False)
        return result.returncode == 0
    
    def ensure_directory(self, path: Path, mode: int = 0o755):
        """Ensure directory exists with proper permissions
        
        Args:
            path: Directory path
            mode: Permission mode (default: 0o755)
        """
        path.mkdir(mode=mode, parents=True, exist_ok=True)
    
    def update_bashrc(self, lines: list, marker: str):
        """Add lines to ~/.bashrc if not already present
        
        Args:
            lines: List of lines to add
            marker: Unique marker to identify the section
        """
        bashrc = Path.home() / ".bashrc"
        
        # Check if already added
        if bashrc.exists():
            with open(bashrc, 'r') as f:
                content = f.read()
                if marker in content:
                    return
        
        # Append lines
        with open(bashrc, 'a') as f:
            f.write('\n')
            for line in lines:
                f.write(line + '\n')
