import os
import subprocess
from research_agent.constant import GITHUB_AI_TOKEN, AI_USER, BASE_IMAGES
import time
from research_agent.inno.util import run_command_in_container

def init_container(workplace_name, container_name, test_pull_name = 'test_pull_1010', task_name = 'test_task', git_clone = False, setup_package = 'setup_package'):
    # get the current working directory's subfolder path
    workplace = os.path.join(os.getcwd(), workplace_name)

    # check if the container exists
    container_check_command = ["docker", "ps", "-a", "--filter", f"name={container_name}", "--format", "{{.Names}}"]
    existing_container = subprocess.run(container_check_command, capture_output=True, text=True)

    os.makedirs(workplace, exist_ok=True)
    # cp_command = ["cp", "tcp_server.py", workplace]
    if not os.path.exists(os.path.join(workplace, 'tcp_server.py')):
        unzip_command = ["tar", "-xzvf", f"packages/{setup_package}.tar.gz", "-C", workplace]
        subprocess.run(unzip_command)
    if git_clone:
        if not os.path.exists(os.path.join(workplace, 'metachain')):
            git_command = ["cd", workplace, "&&", "git", "clone", "-b", test_pull_name, f"https://{AI_USER}:{GITHUB_AI_TOKEN}@github.com/tjb-tech/metachain.git"]
            git_command = " ".join(git_command)
            
            result = subprocess.run(git_command, shell=True)
            if result.returncode != 0:
                raise Exception(f"Failed to clone the repository. Please check your internet connection and try again.")
            # create a new branch
        new_branch_name = f"{test_pull_name}_{task_name}"
        create_branch_command = f"cd {workplace}/metachain && git checkout -b {new_branch_name}"
        result = subprocess.run(create_branch_command, shell=True, capture_output=True, text=True)
        if result.returncode != 0:
            print(Exception(f"Failed to create and switch to new branch. Error: {result.stderr}"))
            switch_branch_command = f"cd {workplace}/metachain && git checkout {new_branch_name}"
            result = subprocess.run(switch_branch_command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise Exception(f"Failed to switch to new branch. Error: {result.stderr}")
            else:
                print(f"Successfully switched to new branch: {new_branch_name}")
        else:
            print(f"Successfully created and switched to new branch: {new_branch_name}")

    if existing_container.stdout.strip() == container_name:
        # check if the container is running
        running_check_command = ["docker", "ps", "--filter", f"name={container_name}", "--format", "{{.Names}}"]
        running_container = subprocess.run(running_check_command, capture_output=True, text=True)

        if running_container.stdout.strip() == container_name:
            print(f"Container '{container_name}' is already running. Skipping creation.")
            return  # container is already running, skip creation
        else:
            # container exists but is not running, start it
            start_command = ["docker", "start", container_name]
            subprocess.run(start_command)
            print(f"Container '{container_name}' has been started.")
            return
    
    # if the container does not exist, create and start a new container
    docker_command = [
        "docker", "run", "-d", "--name", container_name, "--user", "root",
        "-v", f"{workplace}:/{workplace_name}",
        "-w", f"/{workplace_name}", "-p", "12345:12345", BASE_IMAGES,
        "/bin/bash", "-c", 
        f"python3 /{workplace_name}/tcp_server.py --workplace {workplace_name}"
    ]
    # execute the docker command
    result = subprocess.run(docker_command, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"Failed to start container: {result.stderr}")
    if wait_for_container_ready(container_name, timeout=180):  # Increased to 180 seconds (3 minutes)
        print(f"Container '{container_name}' has been created and started.")

def wait_for_container_ready(container_name, timeout=180):
    """using subprocess to check if the container is running"""
    start_time = time.time()
    check_interval = 2  # Check every 2 seconds
    max_retries = 5  # Retry tcp_server check multiple times
    tcp_server_retries = 0
    
    while time.time() - start_time < timeout:
        elapsed = int(time.time() - start_time)
        result = subprocess.run(
            ["docker", "inspect", "--format", "{{.State.Running}}", container_name],
            capture_output=True,
            text=True
        )
        
        if result.returncode != 0:
            # Container might not exist yet
            print(f"[{elapsed}s] Container '{container_name}' not found yet, waiting...")
            time.sleep(check_interval)
            continue
        
        if "true" in result.stdout.lower():
            # Container is running, check tcp_server
            print(f"[{elapsed}s] Container '{container_name}' is running, checking tcp_server...")
            try:
                result = run_command_in_container('ps aux')
                if "tcp_server.py" in result.get('result', ''):
                    print(f"[{elapsed}s] Container '{container_name}' is ready!")
                    return True
                else:
                    tcp_server_retries += 1
                    if tcp_server_retries < max_retries:
                        print(f"[{elapsed}s] tcp_server not ready yet, retrying... ({tcp_server_retries}/{max_retries})")
                        time.sleep(check_interval)
                    else:
                        # After max retries, if container is running, consider it ready
                        print(f"[{elapsed}s] Container is running, proceeding (tcp_server may start later)")
                        return True
            except Exception as e:
                tcp_server_retries += 1
                error_msg = str(e)
                if tcp_server_retries < max_retries:
                    print(f"[{elapsed}s] Error checking tcp_server (retry {tcp_server_retries}/{max_retries}): {error_msg}")
                    time.sleep(check_interval)
                else:
                    # Check if it's a connection error
                    if "Connection reset" in error_msg or "Connection refused" in error_msg or "104" in error_msg:
                        print(f"[{elapsed}s] tcp_server connection error, but container is running")
                        # Give extra time for tcp_server to start
                        time.sleep(10)
                        try:
                            result = run_command_in_container('ps aux')
                            if "tcp_server.py" in result.get('result', ''):
                                print(f"[{elapsed}s] Container '{container_name}' is ready!")
                                return True
                        except:
                            pass
                    # Container is running, even if tcp_server check fails
                    print(f"[{elapsed}s] Container is running, proceeding despite tcp_server check failure")
                    return True
        else:
            print(f"[{elapsed}s] Container '{container_name}' exists but not running yet...")
            
        time.sleep(check_interval)
    
    # Get container logs for debugging
    try:
        logs = subprocess.run(
            ["docker", "logs", "--tail", "50", container_name],
            capture_output=True,
            text=True,
            timeout=5
        )
        log_output = logs.stdout if logs.returncode == 0 else "Could not retrieve logs"
    except:
        log_output = "Could not retrieve logs"
    
    raise TimeoutError(
        f"Container {container_name} failed to start within {timeout} seconds.\n"
        f"Last 50 lines of container logs:\n{log_output}"
    )