"""Progress indicators for command line interfaces.

This module provides utilities for displaying progress indicators in the terminal,
including colored check marks, spinners, and other visual feedback elements.
"""

import sys
from typing import Optional


# ANSI color codes
class Colors:
    """ANSI color codes for terminal output."""

    GREEN = "\033[92m"
    YELLOW = "\033[93m"
    RED = "\033[91m"
    BLUE = "\033[94m"
    BOLD = "\033[1m"
    RESET = "\033[0m"


class ProgressIndicator:
    """Progress indicator utilities for command line interfaces."""

    _current_message = ""
    _indent_level = 0

    @staticmethod
    def step_start(message: str) -> None:
        """Display the start of a processing step.

        Args:
            message: The message to display
        """
        ProgressIndicator._current_message = message
        # Just store the message, don't print anything yet
        sys.stdout.flush()

    @staticmethod
    def step_complete(message: Optional[str] = None) -> None:
        """Display a successful completion with a green check mark.

        Args:
            message: Optional additional message to display after the check mark
        """
        check_mark = f"{Colors.GREEN}✓{Colors.RESET}"
        if message:
            sys.stdout.write(f"{check_mark} {message}\n")
        else:
            sys.stdout.write(f"{check_mark} {ProgressIndicator._current_message}\n")
        sys.stdout.flush()

    @staticmethod
    def step_warning(message: str) -> None:
        """Display a warning with a yellow exclamation mark.

        Args:
            message: The warning message to display
        """
        warning_mark = f"{Colors.YELLOW}!{Colors.RESET}"
        sys.stdout.write(f"{warning_mark} {message}\n")
        sys.stdout.flush()

    @staticmethod
    def step_error(message: str) -> None:
        """Display an error with a red X mark.

        Args:
            message: The error message to display
        """
        error_mark = f"{Colors.RED}✗{Colors.RESET}"
        sys.stdout.write(f"{error_mark} {message}\n")
        sys.stdout.flush()

    @staticmethod
    def section_header(title: str) -> None:
        """Display a section header with blue bold text.

        Args:
            title: The section title to display
        """
        sys.stdout.write(f"\n{Colors.BLUE}{Colors.BOLD}{title}{Colors.RESET}\n")
        sys.stdout.write(f"{'-' * len(title)}\n")
        sys.stdout.flush()

    @staticmethod
    def bullet_item(message: str) -> None:
        """Display a bullet point item.

        Args:
            message: The message to display with a bullet point
        """
        bullet = f"{Colors.BLUE}•{Colors.RESET}"
        sys.stdout.write(f"{bullet} {message}\n")
        sys.stdout.flush()
