"""Deterministic single-CPU scheduler with a simple contiguous-free-capacity RAM model.

All time values are integer milliseconds. No context switching overhead.
A process keeps its allocated RAM until it completes.
"""

from collections import deque


def simulate(processes, algorithm="Round Robin", quantum=2, total_ram=512):
    if algorithm not in ("Round Robin", "Priority Scheduling"):
        raise ValueError("Choose Round Robin or Priority Scheduling.")
    if not isinstance(quantum, int) or quantum < 1:
        raise ValueError("Time quantum must be at least 1 ms.")
    if not isinstance(total_ram, int) or total_ram < 1:
        raise ValueError("Total RAM must be at least 1 MB.")
    if not processes:
        raise ValueError("Add at least one process before running.")
    if len(processes) > 30:
        raise ValueError("Maximum 30 processes are supported in this demo.")

    jobs = []
    seen = set()
    for position, item in enumerate(processes):
        try:
            pid = str(item["pid"]).strip()
            arrival = int(item["arrival"])
            burst = int(item["burst"])
            priority = int(item["priority"])
            memory = int(item["memory"])
        except (KeyError, ValueError, TypeError) as exc:
            raise ValueError(
                "Each process needs PID, arrival, burst, priority and memory."
            ) from exc
        if not pid or pid.lower() in seen:
            raise ValueError("Process IDs must be unique and non-empty.")
        if arrival < 0 or burst < 1 or priority < 1 or memory < 1:
            raise ValueError("Arrival >= 0; burst, priority and memory >= 1.")
        if memory > total_ram:
            raise ValueError(
                f"{pid} needs {memory} MB but total RAM is {total_ram} MB."
            )
        seen.add(pid.lower())
        jobs.append(
            {
                "pid": pid,
                "arrival": arrival,
                "burst": burst,
                "priority": priority,
                "memory": memory,
                "order": position,
                "remaining": burst,
                "completion": None,
            }
        )

    jobs.sort(key=lambda p: (p["arrival"], p["order"]))
    if sum(p["burst"] for p in jobs) + max(p["arrival"] for p in jobs) > 12000:
        raise ValueError(
            "Simulation too long. Reduce arrival or burst times (12,000 ms max)."
        )
    lookup = {p["pid"]: p for p in jobs}
    ready = deque()
    memory_wait = deque()  # FIFO admission: a large waiting job cannot be bypassed
    resident = set()
    next_index = 0
    time = 0
    completed = 0
    running = None
    used_quantum = 0
    events = []

    def used_ram():
        return sum(lookup[pid]["memory"] for pid in resident)

    def arrive():
        nonlocal next_index
        while next_index < len(jobs) and jobs[next_index]["arrival"] <= time:
            memory_wait.append(jobs[next_index]["pid"])
            next_index += 1

    def admit():
        while memory_wait:
            pid = memory_wait[0]
            if lookup[pid]["memory"] + used_ram() > total_ram:
                break
            memory_wait.popleft()
            resident.add(pid)
            ready.append(pid)

    while completed < len(jobs):
        arrive()
        admit()
        if running is None and ready:
            if algorithm == "Round Robin":
                running = ready.popleft()
            else:
                running = min(
                    ready,
                    key=lambda pid: (
                        lookup[pid]["priority"],
                        lookup[pid]["arrival"],
                        lookup[pid]["order"],
                    ),
                )
                ready.remove(running)
            used_quantum = 0

        executing = running
        start = time
        time += 1
        if running is not None:
            lookup[running]["remaining"] -= 1
            used_quantum += 1
            if lookup[running]["remaining"] == 0:
                lookup[running]["completion"] = time
                resident.remove(running)
                completed += 1
                running = None
                used_quantum = 0

        # Bring in arrivals at this instant before adding an expired RR slice
        # to the tail of the queue. RAM is freed immediately upon completion.
        arrive()
        admit()
        if (
            running is not None
            and algorithm == "Round Robin"
            and used_quantum >= quantum
        ):
            ready.append(running)
            running = None
            used_quantum = 0

        states = {}
        for p in jobs:
            pid = p["pid"]
            if p["completion"] is not None:
                state = "Completed"
            elif pid == executing:
                state = "Running"  # running during [start, time)
            elif p["arrival"] > time:
                state = "New"
            elif pid in memory_wait:
                state = "Waiting for RAM"
            elif pid in resident:
                state = "Ready"
            else:
                state = "New"
            states[pid] = state

        events.append(
            {
                "start": start,
                "end": time,
                "pid": executing if executing is not None else "IDLE",
                "ready": list(ready),
                "memory_wait": list(memory_wait),
                "resident": sorted(resident),
                "used_ram": used_ram(),
                "free_ram": total_ram - used_ram(),
                "remaining": {p["pid"]: p["remaining"] for p in jobs},
                "states": states,
            }
        )

    results = []
    for p in sorted(jobs, key=lambda x: x["order"]):
        tat = p["completion"] - p["arrival"]
        results.append(
            {
                "pid": p["pid"],
                "completion": p["completion"],
                "turnaround": tat,
                "waiting": tat - p["burst"],
            }
        )
    return events, results


def make_segments(events):
    """Group consecutive CPU ticks into labelled Gantt blocks."""
    blocks = []
    for event in events:
        pid = event["pid"]
        if blocks and blocks[-1]["pid"] == pid and blocks[-1]["end"] == event["start"]:
            blocks[-1]["end"] = event["end"]
        else:
            blocks.append({"pid": pid, "start": event["start"], "end": event["end"]})
    return blocks
