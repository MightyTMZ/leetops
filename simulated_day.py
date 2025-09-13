import random
import datetime

INCIDENTS = [
    {
        "name": "Database Outage",
        "description": "Production database is not responding. Users see 500 errors on login.",
        "severity": "Critical",
        "time_to_resolve": (20, 60)
    },
    {
        "name": "Memory Leak",
        "description": "API pods are crashing due to OOMKilled errors. Service degraded.",
        "severity": "High",
        "time_to_resolve": (30, 90)
    },
    {
        "name": "Disk Full",
        "description": "Logging service has filled up /var/log. Writes are failing.",
        "severity": "Medium",
        "time_to_resolve": (15, 40)
    },
    {
        "name": "Bad Deployment",
        "description": "A new release is causing 404 errors on several endpoints.",
        "severity": "Critical",
        "time_to_resolve": (10, 30)
    },
    {
        "name": "Slow Queries",
        "description": "User reports of slowness. Investigation reveals unindexed DB queries.",
        "severity": "Low",
        "time_to_resolve": (30, 120)
    },
    {
        "name": "SSL Certificate Expired",
        "description": "Frontend cert expired. Users cannot access the site securely.",
        "severity": "High",
        "time_to_resolve": (15, 45)
    }
]

def random_time_between(start, end):
    """Return a random datetime between two datetimes"""
    delta = end - start
    random_minute = random.randint(0, int(delta.total_seconds() // 60))
    return start + datetime.timedelta(minutes=random_minute)

def simulate_job_day(name="Engineer"):
    print(f"📅 Simulating a 9–5 on-call day for {name}...\n")
    log = []

    # Workday boundaries
    start_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time(9, 0))
    end_of_day = datetime.datetime.combine(datetime.date.today(), datetime.time(17, 0))

    # Pick 3–6 random incidents
    num_incidents = random.randint(3, 6)
    incidents_today = random.sample(INCIDENTS, num_incidents)

    # Assign random times for incidents
    incident_times = sorted(
        [random_time_between(start_of_day, end_of_day) for _ in range(num_incidents)]
    )

    for idx, (incident, incident_time) in enumerate(zip(incidents_today, incident_times), 1):
        time_str = incident_time.strftime("%H:%M")
        print(f"[{time_str}] Incident {idx}: {incident['name']} ({incident['severity']})")
        print(f"    ➤ {incident['description']}")

        est = random.randint(*incident['time_to_resolve'])
        actual = est + random.randint(-5, 15)
        status = "Resolved" if actual <= incident['time_to_resolve'][1] + 10 else "Escalated"

        print(f"    Estimated: {est} mins | Actual: {actual} mins | Outcome: {status}\n")

        log.append({
            "time": time_str,
            "incident": incident['name'],
            "severity": incident['severity'],
            "estimated_time": est,
            "actual_time": actual,
            "status": status
        })

    print("==== 📝 End of Day Report ====")
    for entry in log:
        print(f"[{entry['time']}] {entry['incident']} | {entry['status']} in {entry['actual_time']} mins")

    return log

if __name__ == "__main__":
    simulate_job_day("Eric")
