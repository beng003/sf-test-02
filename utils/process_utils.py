# process_utils.py
import psutil
import os
import platform

def find_process_by_port(port):
    for proc in psutil.process_iter(['pid', 'name']):
        try:
            connections = proc.connections(kind='inet')
            for conn in connections:
                if conn.laddr.port == port:
                    return proc.pid
        except (psutil.AccessDenied, psutil.NoSuchProcess):
            continue
    return None

def kill_process(pid):
    try:
        if platform.system() == "Windows":
            os.system(f"taskkill /PID {pid} /F")
        else:
            os.system(f"kill -9 {pid}")
        print(f"Process with PID {pid} has been terminated.")
    except Exception as e:
        print(f"Error terminating process with PID {pid}: {e}")

def kill_port_process(port:int):
    pid = find_process_by_port(port)
    
    if pid:
        print(f"Process found using port {port}: PID {pid}")
        kill_process(pid)
    else:
        print(f"No process found using port {port}")