from legent.environment.env_utils import validate_environment_path, launch_executable, get_default_env_path
import subprocess
env_path = get_default_env_path()
run_args = ["--width", "640", "--height",  "480", "--port", "50051"]


def launch_executable(file_name: str, args) -> subprocess.Popen:
    launch_string = validate_environment_path(get_default_env_path())
    subprocess_args = ["DISPLAY=:7"]+[launch_string] + args
    # std_out_option = DEVNULL means the outputs will not be displayed on terminal.
    # std_out_option = None is default behavior: the outputs are displayed on terminal.
    std_out_option = subprocess.DEVNULL
    try:
        return subprocess.Popen(
            subprocess_args,
            # start_new_session=True means that signals to the parent python process
            # (e.g. SIGINT from keyboard interrupt) will not be sent to the new process on POSIX platforms.
            # This is generally good since we want the environment to have a chance to shutdown,
            # but may be undesirable in come cases; if so, we'll add a command-line toggle.
            # Note that on Windows, the CTRL_C signal will still be sent.
            start_new_session=True,
            stdout=std_out_option,
            stderr=std_out_option,
        )
    except PermissionError as perm:
        # This is likely due to missing read or execute permissions on file.
        raise Exception("EnvironmentException:\n" f"Error when trying to launch environment - make sure " f"permissions are set correctly. For example " f'"chmod -R 755 {launch_string}"') from perm

launch_executable(file_name=env_path, args=run_args)

# ssh -N -L 50051:localhost:50051 H100
# DISPLAY=:7 python launch.py
# DISPLAY=:7 from legent.environment.env_utils import validate_environment_path, launch_executable, get_default_env_path

