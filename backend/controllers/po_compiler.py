from pathlib import Path
from fastapi import HTTPException
import subprocess
import sys
import os
from config.config import Config

class POCompilerController:
    def __init__(self, po_dir: Path, po_file: str, mo_file: str):
        self.po_dir = po_dir
        self.po_file = po_file
        self.mo_file = mo_file
        
        # Set path to msgfmt based on OS
        self.msgfmt_path = self._get_msgfmt_path()

    def _get_msgfmt_path(self):
        # Determine the correct msgfmt path based on the operating system
        paths_to_try = []
        
        if sys.platform == "win32":
            # Windows paths
            paths_to_try = [
                Config.msgfmt_path,
                "msgfmt.exe"
            ]
        else:
            # Linux/macOS paths
            paths_to_try = [
                "/usr/bin/msgfmt",
                "/usr/local/bin/msgfmt",
                "/opt/homebrew/bin/msgfmt",
                "msgfmt"  
            ]
        
        # Check which path exists
        for path in paths_to_try:
            if os.path.exists(path):
                return path
                
        # Return the first option if none exist (will trigger proper error later)
        return paths_to_try[0]

    def compile_po(self):
        po_path = self.po_dir / self.po_file
        mo_path = self.po_dir / self.mo_file

        if not po_path.exists():
            raise HTTPException(
                status_code=404,
                detail=f".po file not found: {po_path}"
            )

        try:
            # Run msgfmt command to compile PO to MO
            cmd = [
                self.msgfmt_path,
                "-o", str(mo_path),
                str(po_path)
            ]
            
            result = subprocess.run(
                cmd,
                cwd=str(self.po_dir),  # Execute in the PO directory
                capture_output=True,
                text=True,
                check=True  # Raise exception on non-zero exit
            )
            
            # Verify MO file was created
            if not mo_path.exists():
                raise RuntimeError("Compilation succeeded but MO file was not created")
            
            return {
                "status": "success",
                "message": f"Compiled {po_path.name} → {mo_path.name}",
                "mo_path": str(mo_path),
                "output": result.stdout.strip() or "No output from msgfmt"
            }
            
        except subprocess.CalledProcessError as e:
            # Extract clean error message
            error_detail = e.stderr.strip() or f"Exit code {e.returncode}"
            raise HTTPException(
                status_code=500,
                detail=f"{error_detail}"
            )
        except FileNotFoundError:
            raise HTTPException(
                status_code=500,
                detail=(
                    f"msgfmt not found at '{self.msgfmt_path}'. "
                    "Please install gettext:\n"
                    "Windows: Install from https://mlocati.github.io/articles/gettext-iconv-windows.html\n"
                    "macOS: brew install gettext\n"
                    "Linux: apt-get install gettext"
                )
            )
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail=f"Unexpected error: {str(e)}"
            )