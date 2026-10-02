from fractions import Fraction
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "py"))

from ui.video_timing import VideoTimingQueue


class FakeFrame:
    def __init__(self, pts):
        self.pts = pts
        self.time_base = Fraction(1, 1000)


def test_queue_delays_frames_using_arrival_time():
    queue = VideoTimingQueue(delay_seconds=0.25, max_frames=10)
    first = FakeFrame(1000)
    second = FakeFrame(1016)

    queue.enqueue(first, arrival_time=10.0)
    queue.enqueue(second, arrival_time=10.016)

    assert queue.pop_due(10.249) is None
    assert queue.pop_due(10.250).frame is first
    assert queue.pop_due(10.266).frame is second


def test_queue_does_not_schedule_timestamp_jump_in_the_future():
    queue = VideoTimingQueue(delay_seconds=0.25, max_frames=10)
    first = FakeFrame(1000)
    jumped = FakeFrame(100000)

    queue.enqueue(first, arrival_time=10.0)
    queue.enqueue(jumped, arrival_time=10.016)

    assert queue.pop_due(10.266).frame is jumped


def test_queue_keeps_newest_due_frame_and_counts_dropped_frames():
    queue = VideoTimingQueue(delay_seconds=0.0, max_frames=10)
    frames = [FakeFrame(pts) for pts in (0, 16, 32)]

    for index, frame in enumerate(frames):
        queue.enqueue(frame, arrival_time=index * 0.016)

    assert queue.pop_due(1.0).frame is frames[-1]
    assert queue.dropped_frames == 2


def test_queue_drops_oldest_frames_at_capacity():
    queue = VideoTimingQueue(delay_seconds=0.0, max_frames=2)
    frames = [FakeFrame(pts) for pts in (0, 16, 32)]

    for index, frame in enumerate(frames):
        queue.enqueue(frame, arrival_time=index * 0.016)

    assert queue.queued_frames == 2
    assert queue.dropped_frames == 1
    assert queue.pop_due(1.0).frame is frames[-1]


def test_queue_reset_discards_previous_stream_frames():
    queue = VideoTimingQueue(delay_seconds=0.25, max_frames=10)
    queue.enqueue(FakeFrame(0), arrival_time=10.0)
    queue.reset()

    assert queue.queued_frames == 0
    assert queue.dropped_frames == 0