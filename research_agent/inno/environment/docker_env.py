import os
import os.path as osp
import subprocess
from constant import BASE_IMAGES, AI_USER, GITHUB_AI_TOKEN, GPUS, PLATFORM
import time
import socket
import json
from pathlib import Path
import shutil
from dataclasses import dataclass, field
from typing import Optional, Union, Dict
from functools import update_wrapper
from inspect import signature

wd = Path(__file__).parent.resolve()


# ============================================================
# CONFIG
# ============================================================
@dataclass
class DockerConfig:
    container_name: str
    workplace_name: str
    communication_port: int
    test_pull_name: str = field(default='main')
    task_name: Optional[str] = field(default=None)
    git_clone: bool = field(default=False)
    setup_package: Optional[str] = field(default=None)
    local_root: str = field(default=os.getcwd())


# ============================================================
# UTILITY: Port Availability Checker
# ============================================================
def is_port_available(port: int) -> bool:
    """
    Check if a port is available by trying to bind to it.
    
    Returns:
        True if port is available, False otherwise
    """
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False


def find_available_port(start_port: int, max_attempts: int = 100) -> int:
    """
    Find an available port starting from start_port.
    
    Args:
        start_port: The port to start checking from
        max_attempts: Maximum number of ports to check
        
    Returns:
        An available port number, or raises Exception if none found
    """
    for i in range(max_attempts):
        port = start_port + i
        if is_port_available(port):
            return port
    raise Exception(f"Could not find an available port starting from {start_port} after {max_attempts} attempts")


def find_container_using_port(port: int) -> Optional[str]:
    """
    Find the Docker container using a specific port.
    
    Returns:
        Container name if found, None otherwise
    """
    try:
        # Check all running containers
        result = subprocess.run(
            ["docker", "ps", "--format", "{{.Names}}"],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            return None
            
        container_names = result.stdout.strip().split('\n')
        
        for container_name in container_names:
            if not container_name:
                continue
            ports = check_container_ports(container_name)
            if ports and ports[0] == port:
                return container_name
    except Exception:
        pass
    
    return None


# ============================================================
# UTILITY: Reliable Port Checker (FIXED)
# ============================================================
def check_container_ports(container_name: str):
    """
    Uses `docker port` (the only reliable method) to determine port mappings.

    Returns:
        (host_port:int, container_port:int) or None
    """
    result = subprocess.run(
        ["docker", "port", container_name],
        capture_output=True,
        text=True
    )

    output = result.stdout.strip()
    if not output:
        return None

    # Example lines:
    # 8000/tcp -> 0.0.0.0:7020
    # 8000/tcp -> [::]:7020
    lines = output.split("\n")

    for line in lines:
        if "->" not in line:
            continue

        container_part, host_part = line.split("->")

        container_port = container_part.split("/")[0].strip()
        host_port = host_part.split(":")[-1].strip()

        return (int(host_port), int(container_port))

    return None


# ============================================================
# DOCKER ENV CLASS (FULLY FIXED & OPTIMIZED)
# ============================================================
class DockerEnv:
    def __init__(self, config: Union[DockerConfig, Dict]):
        if isinstance(config, Dict):
            config = DockerConfig(**config)

        self.workplace_name = config.workplace_name
        self.local_workplace = osp.join(config.local_root, config.workplace_name)
        self.docker_workplace = f"/{config.workplace_name}"
        self.container_name = config.container_name
        self.test_pull_name = config.test_pull_name
        self.task_name = config.task_name
        self.git_clone = config.git_clone
        self.setup_package = config.setup_package
        self.communication_port = config.communication_port

    # ============================================================
    # INIT CONTAINER (unchanged except for stability)
    # ============================================================
    def init_container(self):
        container_check_command = [
            "docker", "ps", "-a", "--filter",
            f"name={self.container_name}", "--format", "{{.Names}}"
        ]
        existing_container = subprocess.run(
            container_check_command, capture_output=True, text=True
        )

        os.makedirs(self.local_workplace, exist_ok=True)

        # extract package if needed
        if self.setup_package is not None:
            unzip_command = [
                "tar", "-xzvf",
                f"packages/{self.setup_package}.tar.gz",
                "-C", self.local_workplace
            ]
            subprocess.run(unzip_command)

        # optional Git clone workflow
        if self.git_clone:
            repo_path = os.path.join(self.local_workplace, 'metachain')
            if not os.path.exists(repo_path):
                git_command = (
                    f"cd {self.local_workplace} && "
                    f"git clone -b {self.test_pull_name} "
                    f"https://{AI_USER}:{GITHUB_AI_TOKEN}@github.com/tjb-tech/metachain.git"
                )

                result = subprocess.run(git_command, shell=True)
                if result.returncode != 0:
                    raise Exception("Failed to clone repo.")

            new_branch_name = f"{self.test_pull_name}_{self.task_name}"
            branch_cmd = (
                f"cd {repo_path} && git checkout -b {new_branch_name}"
            )

            result = subprocess.run(
                branch_cmd, shell=True, capture_output=True, text=True
            )
            if result.returncode != 0:
                fallback_switch = (
                    f"cd {repo_path} && git checkout {new_branch_name}"
                )
                subprocess.run(fallback_switch, shell=True)

        # container exists?
        if existing_container.stdout.strip() == self.container_name:
            running_check = [
                "docker", "ps", "--filter",
                f"name={self.container_name}", "--format", "{{.Names}}"
            ]
            running_container = subprocess.run(
                running_check, capture_output=True, text=True
            )

            if running_container.stdout.strip() == self.container_name:
                print(f"Container '{self.container_name}' is already running.")
                return

            # exists but stopped → start it
            start_command = ["docker", "start", self.container_name]
            subprocess.run(start_command)
            print(f"Container '{self.container_name}' started.")
            return

        # Check if Docker image exists, pull if needed
        image_check = subprocess.run(
            ["docker", "images", "-q", BASE_IMAGES],
            capture_output=True,
            text=True
        )
        if not image_check.stdout.strip():
            print(f"Docker image '{BASE_IMAGES}' not found locally. Pulling...")
            pull_result = subprocess.run(
                ["docker", "pull", BASE_IMAGES],
                capture_output=True,
                text=True
            )
            if pull_result.returncode != 0:
                raise Exception(f"Failed to pull Docker image '{BASE_IMAGES}': {pull_result.stderr}")
            print(f"Docker image '{BASE_IMAGES}' pulled successfully.")

        # Check port availability before creating container
        if not is_port_available(self.communication_port):
            conflicting_container = find_container_using_port(self.communication_port)
            print(f"Port {self.communication_port} is not available.", end=" ")
            
            if conflicting_container:
                print(f"Container '{conflicting_container}' is using this port.")
                print(f"Attempting to find an available port...")
            else:
                print("Another process may be using this port.")
                print(f"Attempting to find an available port...")
            
            # Try to find an available port automatically
            try:
                new_port = find_available_port(self.communication_port + 1, max_attempts=50)
                print(f"Switching from port {self.communication_port} to port {new_port}.")
                self.communication_port = new_port
            except Exception as e:
                error_msg = f"Port {self.communication_port} is already in use."
                if conflicting_container:
                    error_msg += f" Container '{conflicting_container}' is using this port."
                    error_msg += f" You can stop it with: docker stop {conflicting_container}"
                else:
                    error_msg += " Another process may be using this port."
                error_msg += f" Could not find an available alternative port: {str(e)}"
                raise Exception(error_msg)
        
        # create new container
        gpu_cmd = ["--gpus", GPUS] if GPUS else []
        docker_command = [
            "docker", "run", "-d",
            "--platform", PLATFORM,
            "--userns=host",
        ] + gpu_cmd + [
            "--name", self.container_name,
            "--user", "root",
            "-v", f"{self.local_workplace}:{self.docker_workplace}",
            "-w", f"{self.docker_workplace}",
            "-p", f"{self.communication_port}:8000",
            "--restart", "unless-stopped",
            BASE_IMAGES
        ]

        print(docker_command)

        result = subprocess.run(docker_command, capture_output=True, text=True)
        if result.returncode != 0:
            # Check if it's a port conflict
            if "port is already allocated" in result.stderr or "bind" in result.stderr.lower():
                # Try to find which container is using the port
                conflicting_container = find_container_using_port(self.communication_port)
                
                error_msg = f"Port {self.communication_port} is already in use."
                if conflicting_container:
                    error_msg += f" Container '{conflicting_container}' is using this port."
                    error_msg += f" You can stop it with: docker stop {conflicting_container}"
                else:
                    error_msg += " Another process may be using this port."
                
                error_msg += f" Alternatively, change the PORT environment variable or the system will try to find an available port."
                
                # Try to find an available port automatically
                try:
                    new_port = find_available_port(self.communication_port + 1, max_attempts=50)
                    print(f"Port {self.communication_port} is in use. Automatically switching to port {new_port}.")
                    self.communication_port = new_port
                    
                    # Retry with the new port
                    docker_command = [
                        "docker", "run", "-d",
                        "--platform", PLATFORM,
                        "--userns=host",
                    ] + gpu_cmd + [
                        "--name", self.container_name,
                        "--user", "root",
                        "-v", f"{self.local_workplace}:{self.docker_workplace}",
                        "-w", f"{self.docker_workplace}",
                        "-p", f"{self.communication_port}:8000",
                        "--restart", "unless-stopped",
                        BASE_IMAGES
                    ]
                    result = subprocess.run(docker_command, capture_output=True, text=True)
                    if result.returncode != 0:
                        raise Exception(f"Failed to create container even with alternative port {new_port}: {result.stderr}")
                except Exception as e:
                    # If auto-port finding fails, raise the original error with helpful message
                    raise Exception(error_msg) from e
            else:
                raise Exception(f"Failed to create container: {result.stderr}")

        if self.wait_for_container_ready(timeout=180):  # Increased to 180 seconds (3 minutes)
            print(f"Container '{self.container_name}' created & ready.")

    # ============================================================
    # WAIT FOR CONTAINER TO BE READY (FIXED)
    # ============================================================
    def wait_for_container_ready(self, timeout=180):
        start = time.time()
        check_interval = 2  # Check every 2 seconds instead of 1
        max_retries = 3  # Retry tcp_server check multiple times
        tcp_server_retries = 0

        while time.time() - start < timeout:
            elapsed = int(time.time() - start)
            
            # ---- check running state ----
            state = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Running}}", self.container_name],
                capture_output=True,
                text=True
            )
            
            # Check if container exists (might be starting)
            if state.returncode != 0:
                # Container might not exist yet, wait a bit
                print(f"[{elapsed}s] Container '{self.container_name}' not found yet, waiting...")
                time.sleep(check_interval)
                continue

            if "true" in state.stdout.lower():
                # Container is running, check if services are ready
                print(f"[{elapsed}s] Container '{self.container_name}' is running, checking services...")

                # ---- check ports using NEW stable method ----
                port_info = check_container_ports(self.container_name)
                if port_info:
                    host_port, container_port = port_info
                    self.communication_port = host_port

                    # ---- check tcp server inside container (with retries) ----
                    try:
                        result = self.run_command("ps aux")
                        if "tcp_server.py" in result.get("result", ""):
                            print(f"[{elapsed}s] Container '{self.container_name}' is ready!")
                            return True
                        else:
                            tcp_server_retries += 1
                            if tcp_server_retries < max_retries:
                                print(f"[{elapsed}s] tcp_server not ready yet, retrying... ({tcp_server_retries}/{max_retries})")
                                time.sleep(check_interval)
                            else:
                                # After max retries, if container is running and port is accessible, consider it ready
                                print(f"[{elapsed}s] tcp_server check failed after {max_retries} retries")
                                print(f"[{elapsed}s] Container is running and port is accessible, proceeding...")
                                return True
                    except Exception as e:
                        tcp_server_retries += 1
                        error_msg = str(e)
                        if tcp_server_retries < max_retries:
                            print(f"[{elapsed}s] Error while checking tcp_server (retry {tcp_server_retries}/{max_retries}): {error_msg}")
                            time.sleep(check_interval)
                        else:
                            # Check if it's a connection error (tcp_server might not be ready yet)
                            if "Connection reset" in error_msg or "Connection refused" in error_msg or "104" in error_msg:
                                print(f"[{elapsed}s] tcp_server connection error after {max_retries} retries")
                                print(f"[{elapsed}s] Container is running, but tcp_server may need more time to start")
                                # Give it extra time for tcp_server to start
                                time.sleep(10)
                                # Try one final time
                                try:
                                    result = self.run_command("ps aux")
                                    if "tcp_server.py" in result.get("result", ""):
                                        print(f"[{elapsed}s] Container '{self.container_name}' is ready!")
                                        return True
                                except:
                                    pass
                                # If container is running and port is accessible, proceed anyway
                                print(f"[{elapsed}s] Proceeding with container (tcp_server may start later)")
                                return True
                            else:
                                # Other errors, wait and retry
                                print(f"[{elapsed}s] Error checking tcp_server: {error_msg}")
                                time.sleep(check_interval)
            else:
                # Container exists but not running yet
                print(f"[{elapsed}s] Container '{self.container_name}' exists but not running yet...")

            time.sleep(check_interval)

        # Get container logs for debugging
        try:
            logs = subprocess.run(
                ["docker", "logs", "--tail", "50", self.container_name],
                capture_output=True,
                text=True,
                timeout=5
            )
            log_output = logs.stdout if logs.returncode == 0 else "Could not retrieve logs"
        except:
            log_output = "Could not retrieve logs"

        raise TimeoutError(
            f"Container {self.container_name} failed to start within {timeout} seconds.\n"
            f"Container state: {state.stdout if 'state' in locals() else 'unknown'}\n"
            f"Last 50 lines of container logs:\n{log_output}"
        )

    # ============================================================
    # STOP CONTAINER
    # ============================================================
    def stop_container(self):
        result = subprocess.run(
            ["docker", "stop", self.container_name],
            capture_output=True,
            text=True
        )
        if result.returncode != 0:
            raise Exception(f"Failed to stop container: {result.stderr}")

    # ============================================================
    # COMMAND RUNNER OVER TCP
    # ============================================================
    def run_command(self, command, stream_callback=None):
        hostname = "localhost"
        port = self.communication_port
        buffer_size = 4096

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((hostname, port))
            s.sendall(command.encode())

            partial_line = ""

            while True:
                chunk = s.recv(buffer_size)
                if not chunk:
                    break

                data = partial_line + chunk.decode('utf-8')
                lines = data.split("\n")

                for line in lines[:-1]:
                    if not line:
                        continue
                    try:
                        response = json.loads(line)
                        if response['type'] == 'chunk':
                            if stream_callback:
                                stream_callback(response['data'])
                        elif response['type'] == 'final':
                            return {
                                "status": response["status"],
                                "result": response["result"]
                            }
                    except json.JSONDecodeError:
                        print("Invalid JSON:", line)

                partial_line = lines[-1]

        return {"status": -1, "result": "Connection closed without final response"}


# ============================================================
# DECORATOR: BIND ENV
# ============================================================
def with_env(env: DockerEnv):
    def decorator(func):
        def wrapped(*args, **kwargs):
            return func(env=env, *args, **kwargs)

        update_wrapper(wrapped, func)

        wrapped.__signature__ = signature(func).replace(
            parameters=[p for p in signature(func).parameters.values() if p.name != 'env']
        )

        if func.__doc__:
            try:
                doc = func.__doc__
                if "{docker_workplace}" in doc:
                    doc = doc.format(docker_workplace=env.docker_workplace)
                if "{local_workplace}" in doc:
                    doc = doc.format(local_workplace=env.local_workplace)
                wrapped.__doc__ = doc
            except Exception:
                wrapped.__doc__ = func.__doc__

        return wrapped
    return decorator


# ============================================================
# SIMPLE CHECKERS
# ============================================================
def check_container_exist(container_name: str):
    result = subprocess.run(
        ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    return container_name in result.stdout.strip()


def check_container_running(container_name: str):
    result = subprocess.run(
        ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"],
        capture_output=True,
        text=True
    )
    return container_name in result.stdout.strip()
