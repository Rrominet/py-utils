from pathlib import Path

def isFromADocker() -> bool:
    if Path("/.dockerenv").exists():
        return True

    try:
        cgroup = Path("/proc/1/cgroup").read_text(errors="ignore")
        if any(x in cgroup for x in ("docker", "containerd", "kubepods", "podman", "lxc")):
            return True
    except Exception:
        pass

    try:
        mountinfo = Path("/proc/self/mountinfo").read_text(errors="ignore")
        if any(x in mountinfo for x in ("docker", "containerd", "kubepods", "podman", "overlay")):
            return True
    except Exception:
        pass

    return False
