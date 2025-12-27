"""TestRunnerValidator for executing tests before allowing commits.

This module provides functionality to run tests (pytest or configured test command),
parse the output, and return pass/fail status to determine if a commit should be allowed.
"""

import subprocess
import re
from pathlib import Path
from typing import Dict, List, Optional, Union, Any


class TestRunnerValidator:
    """Executes tests and validates results before allowing commits.

    The TestRunnerValidator runs the configured test command (default: pytest),
    parses the output to determine if tests passed or failed, and provides
    clear error messages when tests fail to block commits.

    Attributes:
        test_command: Command to run tests (default: "pytest")
        repo_path: Path to the repository (defaults to current directory)
        timeout: Optional timeout in seconds for test execution
    """

    def __init__(
        self,
        test_command: str = "pytest",
        repo_path: Union[str, Path, None] = None,
        timeout: Optional[int] = None
    ):
        """Initialize the TestRunnerValidator.

        Args:
            test_command: Command to run tests (e.g., "pytest", "python -m pytest -v")
            repo_path: Path to the repository. Defaults to current directory.
            timeout: Optional timeout in seconds for test execution.
        """
        self.test_command = test_command

        if repo_path is None:
            self.repo_path = Path.cwd()
        elif isinstance(repo_path, str):
            self.repo_path = Path(repo_path)
        else:
            self.repo_path = repo_path

        self.timeout = timeout

    def run_tests(self, test_path: Optional[str] = None) -> Dict[str, Any]:
        """Run tests and capture output.

        Args:
            test_path: Optional specific test path to run (e.g., "tests/test_auth.py")

        Returns:
            Dictionary containing:
                - passed: Boolean indicating if tests passed
                - exit_code: Exit code from test command
                - output: stdout from test execution
                - error: stderr from test execution

        Example:
            >>> validator = TestRunnerValidator()
            >>> result = validator.run_tests()
            >>> if result["passed"]:
            ...     print("All tests passed!")
        """
        try:
            # Build command
            cmd_parts = self.test_command.split()
            if test_path:
                cmd_parts.append(test_path)

            # Run the test command
            result = subprocess.run(
                cmd_parts,
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=self.timeout,
                check=False
            )

            return {
                "passed": result.returncode == 0,
                "exit_code": result.returncode,
                "output": result.stdout,
                "error": result.stderr
            }

        except subprocess.TimeoutExpired:
            return {
                "passed": False,
                "exit_code": -1,
                "output": "",
                "error": f"Test execution timed out after {self.timeout} seconds"
            }

        except FileNotFoundError as e:
            return {
                "passed": False,
                "exit_code": -1,
                "output": "",
                "error": f"Test command not found: {e}"
            }

        except PermissionError as e:
            return {
                "passed": False,
                "exit_code": -1,
                "output": "",
                "error": f"Permission denied running tests: {e}"
            }

        except subprocess.SubprocessError as e:
            return {
                "passed": False,
                "exit_code": -1,
                "output": "",
                "error": f"Error running tests: {e}"
            }

        except Exception as e:
            return {
                "passed": False,
                "exit_code": -1,
                "output": "",
                "error": f"Unexpected error running tests: {e}"
            }

    def parse_output(self, output: str, exit_code: int) -> Dict[str, Any]:
        """Parse test output to extract test results.

        Args:
            output: Test output string to parse
            exit_code: Exit code from test execution

        Returns:
            Dictionary containing:
                - passed: Boolean indicating if tests passed
                - total_tests: Total number of tests run
                - failed_tests: Number of failed tests
                - warnings: Number of warnings
                - failed_test_names: List of failed test names
                - error: Error message if any

        Example:
            >>> validator = TestRunnerValidator()
            >>> result = validator.parse_output("===== 10 passed in 2.34s =====", 0)
            >>> print(result["total_tests"])
            10
        """
        result = {
            "passed": exit_code == 0,
            "total_tests": 0,
            "failed_tests": 0,
            "warnings": 0,
            "failed_test_names": [],
            "error": None
        }

        # Parse pytest output
        # Pattern: "===== X passed, Y failed in Z.ZZs ====="
        summary_pattern = r"=+\s*(?:(\d+)\s+failed,?\s*)?(?:(\d+)\s+passed)?,?\s*(?:(\d+)\s+warning)?.*?in\s+[\d.]+s\s*=+"
        match = re.search(summary_pattern, output)

        if match:
            failed = int(match.group(1)) if match.group(1) else 0
            passed = int(match.group(2)) if match.group(2) else 0
            warnings = int(match.group(3)) if match.group(3) else 0

            result["failed_tests"] = failed
            result["total_tests"] = passed + failed
            result["warnings"] = warnings
            result["passed"] = failed == 0 and exit_code == 0

        # Check for "no tests ran" scenario
        if "no tests ran" in output.lower() or "no tests collected" in output.lower():
            result["passed"] = False
            result["error"] = "No tests were found or ran"

        # Extract failed test names
        # Pattern: "FAILED path/to/test.py::test_name - Error"
        failed_pattern = r"FAILED\s+([\w/._-]+::[\w_]+)"
        failed_matches = re.findall(failed_pattern, output)
        result["failed_test_names"] = failed_matches

        # Check for errors in output
        if exit_code != 0 and result["total_tests"] == 0:
            # Likely an error occurred
            error_patterns = [
                r"ERROR:\s*(.+)",
                r"Error:\s*(.+)",
                r"FAILED.*-\s*(.+)",
            ]
            for pattern in error_patterns:
                error_match = re.search(pattern, output, re.MULTILINE)
                if error_match:
                    result["error"] = error_match.group(1).strip()
                    break

        return result

    def validate(self) -> Dict[str, Any]:
        """Validate that tests pass before allowing commit.

        This is the main method that should be called to check if a commit
        should be allowed. It runs tests, parses output, and returns a
        clear decision with error messages.

        Returns:
            Dictionary containing:
                - can_commit: Boolean indicating if commit should be allowed
                - passed: Boolean indicating if tests passed
                - message: Human-readable message about test results
                - error_details: Detailed error information if tests failed
                - total_tests: Total number of tests run
                - failed_tests: Number of failed tests

        Example:
            >>> validator = TestRunnerValidator()
            >>> result = validator.validate()
            >>> if result["can_commit"]:
            ...     print("Ready to commit!")
            ... else:
            ...     print(f"Cannot commit: {result['message']}")
        """
        # Run the tests
        test_result = self.run_tests()

        # Parse the output
        parsed = self.parse_output(test_result["output"], test_result["exit_code"])

        # Determine if commit should be allowed
        can_commit = test_result["passed"] and parsed["passed"]

        # Generate message
        if can_commit:
            message = f"All tests passed! ({parsed['total_tests']} tests)"
            if parsed["warnings"] > 0:
                message += f" with {parsed['warnings']} warning(s)"
        else:
            if test_result["error"]:
                message = f"Tests failed with error: {test_result['error']}"
            elif parsed["error"]:
                message = f"Tests failed: {parsed['error']}"
            elif parsed["failed_tests"] > 0:
                message = f"Tests failed: {parsed['failed_tests']} of {parsed['total_tests']} tests failed"
            else:
                message = "Tests failed with unknown error"

        # Compile detailed error information
        error_details = None
        if not can_commit:
            error_details = {
                "exit_code": test_result["exit_code"],
                "failed_count": parsed["failed_tests"],
                "total_count": parsed["total_tests"],
                "failed_tests": parsed["failed_test_names"],
                "error_message": test_result["error"] or parsed["error"],
                "output": test_result["output"]
            }

        return {
            "can_commit": can_commit,
            "passed": parsed["passed"],
            "message": message,
            "error_details": error_details,
            "total_tests": parsed["total_tests"],
            "failed_tests": parsed["failed_tests"]
        }

    def get_error_message(self) -> str:
        """Get a clear error message when tests fail.

        Returns:
            A formatted error message suitable for displaying to users.

        Example:
            >>> validator = TestRunnerValidator()
            >>> result = validator.validate()
            >>> if not result["can_commit"]:
            ...     print(validator.get_error_message())
        """
        result = self.validate()

        if result["can_commit"]:
            return ""

        message_parts = ["❌ Cannot commit: Tests must pass before committing."]
        message_parts.append("")
        message_parts.append(result["message"])

        if result["error_details"] and result["error_details"]["failed_tests"]:
            message_parts.append("")
            message_parts.append("Failed tests:")
            for test_name in result["error_details"]["failed_tests"]:
                message_parts.append(f"  - {test_name}")

        return "\n".join(message_parts)
