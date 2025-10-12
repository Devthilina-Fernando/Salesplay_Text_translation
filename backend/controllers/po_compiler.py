"""
PO to MO file compiler controller.

This module handles compilation of .po files to .mo files using msgfmt.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Dict

from fastapi import HTTPException

from config.config import Config
from config.logger import logger


class POCompilerController:
    """Controller for PO/MO file compilation."""

    def __init__(self, po_dir: Path, po_file: str, mo_file: str):
        """
        Initialize PO compiler controller.
        
        Args:
            po_dir: Directory containing PO files.
            po_file: Name of the PO file.
            mo_file: Name of the MO file to create.
        """
        self.po_dir = po_dir
        self.po_file = po_file
        self.mo_file = mo_file
        self.msgfmt_path = self._get_msgfmt_path()

    def _get_msgfmt_path(self) -> str:
        """
        Determine the correct msgfmt path based on OS.
        
        Returns:
            Path to msgfmt executable.
        """
        paths_to_try = []

        if sys.platform == "win32":
            # Windows paths
            paths_to_try = [
                Config.msgfmt_path if Config.msgfmt_path else None,
                "msgfmt.exe",
            ]
        else:
            # Linux/macOS paths
            paths_to_try = [
                "/usr/bin/msgfmt",
                "/usr/local/bin/msgfmt",
                "/opt/homebrew/bin/msgfmt",
                "msgfmt",
            ]

        # Filter out None values
        paths_to_try = [p for p in paths_to_try if p is not None]

        # Check which path exists
        for path in paths_to_try:
            if os.path.exists(path):
                logger.info(f"Found msgfmt at: {path}")
                return path

        # Return first option if none exist (will trigger error later)
        return paths_to_try[0] if paths_to_try else "msgfmt"

    def compile_po(self) -> Dict[str, str]:
        """
        Compile PO file to MO file.
        
        Returns:
            Dictionary with compilation status and details.
            
        Raises:
            HTTPException: If compilation fails or files not found.
        """
        po_path = self.po_dir / self.po_file
        mo_path = self.po_dir / self.mo_file

        # Validate PO file exists
        if not po_path.exists():
            error_msg = f".po file not found: {po_path}"
            logger.error(error_msg)
            raise HTTPException(status_code=404, detail=error_msg)

        try:
            # Build msgfmt command
            cmd = [
                self.msgfmt_path,
                "-o",
                str(mo_path),
                str(po_path),
            ]

            logger.info(
                "Compiling PO file",
                extra={
                    "po_file": str(po_path),
                    "mo_file": str(mo_path),
                    "command": " ".join(cmd),
                },
            )

            # Execute msgfmt
            result = subprocess.run(
                cmd,
                cwd=str(self.po_dir),
                capture_output=True,
                text=True,
                check=True,
            )

            # Verify MO file was created
            if not mo_path.exists():
                raise RuntimeError("Compilation succeeded but MO file was not created")

            logger.info(f"Successfully compiled {po_path.name} → {mo_path.name}")

            return {
                "status": "success",
                "message": f"Compiled {po_path.name} → {mo_path.name}",
                "mo_path": str(mo_path),
                "output": result.stdout.strip() or "Compilation successful",
            }

        except subprocess.CalledProcessError as e:
            error_detail = e.stderr.strip() or f"Exit code {e.returncode}"
            logger.error(
                "PO compilation failed",
                extra={
                    "error": error_detail,
                    "returncode": e.returncode,
                },
            )
            raise HTTPException(status_code=500, detail=error_detail)

        except FileNotFoundError:
            error_msg = (
                f"msgfmt not found at '{self.msgfmt_path}'. "
                "Please install gettext:\n"
                "Windows: https://mlocati.github.io/articles/gettext-iconv-windows.html\n"
                "macOS: brew install gettext\n"
                "Linux: apt-get install gettext"
            )
            logger.error("msgfmt executable not found")
            raise HTTPException(status_code=500, detail=error_msg)

        except Exception as e:
            logger.error(f"Unexpected compilation error: {str(e)}", exc_info=True)
            raise HTTPException(status_code=500, detail=f"Unexpected error: {str(e)}")