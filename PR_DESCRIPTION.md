# 🔒 Security Fix: Replace unsafe `preexec_fn` with `start_new_session`

🎯 **What:**
Replaced `preexec_fn=os.setsid` with `start_new_session=True` in `subprocess.Popen` within `commando/core/audit.py`.

⚠️ **Risk:**
Using `preexec_fn` in Python can lead to severe security and stability issues in multi-threaded applications. Specifically, if a thread holds a lock or forks concurrently, running an arbitrary callable via `preexec_fn` just before `exec()` can cause the child process to deadlock, potentially leading to denial of service or unexpected program crashes. This is a well-documented risk in the Python standard library.

🛡️ **Solution:**
Python 3.2+ introduced the `start_new_session` parameter to `subprocess.Popen` specifically to handle the common use case of running `os.setsid` safely. By switching to `start_new_session=True`, the child process continues to start in a new process group without risking deadlocks from concurrent threading operations, ensuring safe and reliable dynamic auditing (e.g., via `strace`).
