"""
Code execution service — multi-backend.

Priority order:
  1. Piston API (if PISTON_API_URL is set, e.g. self-hosted or with API key)
  2. Local subprocess execution (sandboxed with timeouts)

Supports 10 languages: javascript, typescript, python, java, cpp, go, rust,
csharp, kotlin, ruby.
"""

import logging
import os
import subprocess
import tempfile
import time
import platform

import requests

logger = logging.getLogger('hints.execution')

# ─────────────────────────────────────────────────────────────
#  Language configuration
# ─────────────────────────────────────────────────────────────

LANGUAGE_MAP = {
    'javascript': {'piston': 'javascript', 'version': '18.15.0', 'ext': '.js',   'cmd': ['node']},
    'typescript': {'piston': 'typescript', 'version': '5.0.3',   'ext': '.ts',   'cmd': ['npx', 'ts-node']},
    'python':     {'piston': 'python',     'version': '3.10.0',  'ext': '.py',   'cmd': ['python']},
    'java':       {'piston': 'java',       'version': '15.0.2',  'ext': '.java', 'cmd': None},  # needs compile step
    'cpp':        {'piston': 'c++',        'version': '10.2.0',  'ext': '.cpp',  'cmd': None},  # needs compile step
    'go':         {'piston': 'go',         'version': '1.16.2',  'ext': '.go',   'cmd': ['go', 'run']},
    'rust':       {'piston': 'rust',       'version': '1.68.2',  'ext': '.rs',   'cmd': None},  # needs compile step
    'csharp':     {'piston': 'csharp',     'version': '6.12.0',  'ext': '.cs',   'cmd': None},
    'kotlin':     {'piston': 'kotlin',     'version': '1.8.20',  'ext': '.kt',   'cmd': None},
    'ruby':       {'piston': 'ruby',       'version': '3.0.1',   'ext': '.rb',   'cmd': ['ruby']},
}


class ExecutionService:
    """
    Unified code execution service.
    Tries Piston API first, falls back to local subprocess.
    """

    PISTON_API_URL = os.getenv('PISTON_API_URL', '')
    PISTON_API_KEY = os.getenv('PISTON_API_KEY', '')
    TIMEOUT_SECONDS = 10

    # ─── Piston backend ───

    def _execute_piston(self, code: str, language: str, stdin: str = '') -> dict:
        """Execute via Piston API."""
        runtime = LANGUAGE_MAP[language]
        payload = {
            'language': runtime['piston'],
            'version': runtime['version'],
            'files': [{'content': code}],
            'stdin': stdin,
            'run_timeout': self.TIMEOUT_SECONDS * 1000,
            'compile_timeout': self.TIMEOUT_SECONDS * 1000,
        }
        headers = {}
        if self.PISTON_API_KEY:
            headers['Authorization'] = self.PISTON_API_KEY

        start = time.monotonic()
        try:
            resp = requests.post(self.PISTON_API_URL, json=payload,
                                 headers=headers, timeout=15)
            resp.raise_for_status()
        except requests.exceptions.Timeout:
            return self._err('Execution timed out.', time.monotonic() - start, language,
                             piston_service_error=True)
        except requests.exceptions.ConnectionError:
            return self._err('Cannot reach execution service.', time.monotonic() - start, language,
                             piston_service_error=True)
        except requests.exceptions.HTTPError as exc:
            code_num = exc.response.status_code if exc.response is not None else '?'
            return self._err(f'Execution service error (HTTP {code_num}).', time.monotonic() - start, language,
                             piston_service_error=True)
        except requests.exceptions.RequestException:
            return self._err('Unexpected execution error.', time.monotonic() - start, language,
                             piston_service_error=True)

        elapsed = time.monotonic() - start
        data = resp.json()
        run_result = data.get('run', {})
        compile_result = data.get('compile', {})

        stdout = run_result.get('stdout', '') or ''
        stderr = run_result.get('stderr', '') or ''
        exit_code = run_result.get('code', -1)

        if compile_result and compile_result.get('code', 0) != 0:
            stderr = compile_result.get('stderr', '') or compile_result.get('stdout', '') or stderr
            exit_code = compile_result.get('code', 1)

        return {
            'success': exit_code == 0 and not stderr.strip(),
            'stdout': stdout,
            'stderr': stderr,
            'execution_time': elapsed,
            'language': language,
        }

    # ─── Local subprocess backend ───

    def _execute_local(self, code: str, language: str, stdin: str = '') -> dict:
        """
        Execute code locally via subprocess.
        Supports: python, javascript, ruby, go, typescript, cpp, java, rust, kotlin, csharp.
        Uses tempfiles and process timeouts for safety.
        """
        lang_cfg = LANGUAGE_MAP[language]
        ext = lang_cfg['ext']
        start = time.monotonic()

        try:
            with tempfile.TemporaryDirectory(prefix='hintcode_') as tmpdir:
                # Write source to tempfile
                filename = 'Main' + ext if language == 'java' else 'code' + ext
                filepath = os.path.join(tmpdir, filename)
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(code)

                # Build command
                cmd = self._build_command(language, filepath, tmpdir)
                if cmd is None:
                    return self._err(
                        f'{language} is not available for local execution. '
                        f'Set PISTON_API_URL for full language support.',
                        time.monotonic() - start, language
                    )

                # Execute
                result = subprocess.run(
                    cmd,
                    input=stdin,
                    capture_output=True,
                    text=True,
                    timeout=self.TIMEOUT_SECONDS,
                    cwd=tmpdir,
                    env={**os.environ, 'HOME': tmpdir, 'TMPDIR': tmpdir},
                )

                elapsed = time.monotonic() - start
                return {
                    'success': result.returncode == 0 and not result.stderr.strip(),
                    'stdout': result.stdout or '',
                    'stderr': result.stderr or '',
                    'execution_time': elapsed,
                    'language': language,
                }

        except subprocess.TimeoutExpired:
            return self._err('Time Limit Exceeded (10s).', time.monotonic() - start, language)
        except FileNotFoundError as e:
            return self._err(
                f'{language} runtime not found on this system. '
                f'Install it or set PISTON_API_URL for remote execution. ({e})',
                time.monotonic() - start, language
            )
        except Exception as e:
            logger.exception("Local execution error for %s", language)
            return self._err(f'Execution error: {str(e)[:200]}', time.monotonic() - start, language)

    def _build_command(self, language: str, filepath: str, tmpdir: str):
        """Build the shell command for local execution."""
        is_win = platform.system() == 'Windows'
        python_cmd = 'python' if is_win else 'python3'

        if language == 'python':
            return [python_cmd, filepath]
        elif language == 'javascript':
            return ['node', filepath]
        elif language == 'typescript':
            return ['npx', 'ts-node', filepath]
        elif language == 'ruby':
            return ['ruby', filepath]
        elif language == 'go':
            return ['go', 'run', filepath]
        elif language == 'cpp':
            out_path = os.path.join(tmpdir, 'a.exe' if is_win else 'a.out')
            compile_result = subprocess.run(
                ['g++', '-o', out_path, filepath],
                capture_output=True, text=True, timeout=self.TIMEOUT_SECONDS, cwd=tmpdir
            )
            if compile_result.returncode != 0:
                raise Exception(f'Compilation Error:\n{compile_result.stderr}')
            return [out_path]
        elif language == 'java':
            compile_result = subprocess.run(
                ['javac', filepath],
                capture_output=True, text=True, timeout=self.TIMEOUT_SECONDS, cwd=tmpdir
            )
            if compile_result.returncode != 0:
                raise Exception(f'Compilation Error:\n{compile_result.stderr}')
            classname = os.path.splitext(os.path.basename(filepath))[0]
            return ['java', '-cp', tmpdir, classname]
        elif language == 'rust':
            out_path = os.path.join(tmpdir, 'code.exe' if is_win else 'code')
            compile_result = subprocess.run(
                ['rustc', '-o', out_path, filepath],
                capture_output=True, text=True, timeout=self.TIMEOUT_SECONDS, cwd=tmpdir
            )
            if compile_result.returncode != 0:
                raise Exception(f'Compilation Error:\n{compile_result.stderr}')
            return [out_path]
        elif language == 'kotlin':
            jar_path = os.path.join(tmpdir, 'code.jar')
            compile_result = subprocess.run(
                ['kotlinc', filepath, '-include-runtime', '-d', jar_path],
                capture_output=True, text=True, timeout=30, cwd=tmpdir
            )
            if compile_result.returncode != 0:
                raise Exception(f'Compilation Error:\n{compile_result.stderr}')
            return ['java', '-jar', jar_path]
        elif language == 'csharp':
            # Try dotnet-script or csc
            return ['dotnet-script', filepath]
        else:
            return None

    # ─── Public API ───

    def execute(self, code: str, language: str, stdin: str = '') -> dict:
        """
        Execute code. Tries Piston first if configured, else local subprocess.
        """
        lang_key = language.lower().strip()
        if lang_key not in LANGUAGE_MAP:
            supported = ', '.join(sorted(LANGUAGE_MAP))
            return self._err(
                f"Unsupported language: '{language}'. Supported: {supported}",
                0, language
            )

        logger.info("Executing %s code — %d bytes", lang_key, len(code))

        # Try Piston API if configured
        if self.PISTON_API_URL:
            result = self._execute_piston(code, lang_key, stdin)
            # Fall back to local execution only when the Piston *service itself*
            # was unreachable or returned an HTTP-level error (e.g. 401 whitelist,
            # 5xx, timeout). Real execution results — whether the user's code passed
            # or failed — are returned directly so error messages are preserved.
            if not result.get('piston_service_error'):
                return result
            logger.warning("Piston service error (%s), falling back to local execution",
                           result.get('stderr', '').strip())

        # Fallback to local execution
        return self._execute_local(code, lang_key, stdin)

    @staticmethod
    def _err(message: str, elapsed: float, language: str, piston_service_error: bool = False) -> dict:
        return {
            'success': False,
            'stdout': '',
            'stderr': message,
            'execution_time': elapsed,
            'language': language,
            'piston_service_error': piston_service_error,
        }


# Module-level singleton
piston_service = ExecutionService()
