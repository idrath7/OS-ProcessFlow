import unittest
from scheduler import simulate, make_segments


class SchedulerTests(unittest.TestCase):
    def setUp(self):
        self.jobs = [
            dict(pid="P1", arrival=0, burst=5, priority=2, memory=120),
            dict(pid="P2", arrival=0, burst=3, priority=1, memory=80),
            dict(pid="P3", arrival=0, burst=4, priority=3, memory=160),
            dict(pid="P4", arrival=0, burst=2, priority=4, memory=100),
        ]

    def test_round_robin(self):
        events, results = simulate(self.jobs, "Round Robin", 2, 512)
        self.assertEqual(
            [(x["pid"], x["start"], x["end"]) for x in make_segments(events)],
            [
                ("P1", 0, 2),
                ("P2", 2, 4),
                ("P3", 4, 6),
                ("P4", 6, 8),
                ("P1", 8, 10),
                ("P2", 10, 11),
                ("P3", 11, 13),
                ("P1", 13, 14),
            ],
        )
        self.assertEqual([r["waiting"] for r in results], [9, 8, 9, 6])
        self.assertEqual([r["completion"] for r in results], [14, 11, 13, 8])

    def test_priority(self):
        events, results = simulate(self.jobs, "Priority Scheduling", 2, 512)
        self.assertEqual(
            [s["pid"] for s in make_segments(events)], ["P2", "P1", "P3", "P4"]
        )
        self.assertEqual([r["waiting"] for r in results], [3, 0, 8, 12])

    def test_memory_wait_and_release(self):
        events, _ = simulate(self.jobs[:2], "Round Robin", 2, 120)
        self.assertLessEqual(max(e["used_ram"] for e in events), 120)
        self.assertTrue(any("P2" in e["memory_wait"] for e in events))
        self.assertEqual(events[-1]["used_ram"], 0)

    def test_arrivals(self):
        jobs = [
            dict(pid="A", arrival=2, burst=2, priority=2, memory=50),
            dict(pid="B", arrival=4, burst=1, priority=1, memory=50),
        ]
        events, results = simulate(jobs, "Round Robin", 2, 512)
        self.assertEqual(
            make_segments(events)[0], {"pid": "IDLE", "start": 0, "end": 2}
        )
        self.assertEqual([r["completion"] for r in results], [4, 5])

    def test_reject_oversize(self):
        with self.assertRaises(ValueError):
            simulate(self.jobs, total_ram=100)


if __name__ == "__main__":
    unittest.main(verbosity=2)
