"""Timestamp-aware scheduling for decoded screen-cast video frames."""

from collections import deque
from dataclasses import dataclass
from typing import Deque, Optional


@dataclass
class ScheduledVideoFrame:
    frame: object
    presentation_time: float
    media_time: Optional[float]


class VideoTimingQueue:
    """Bounded video queue that schedules frames against a monotonic clock."""

    def __init__(self, delay_seconds: float, max_frames: int):
        self._delay_seconds = max(0.0, float(delay_seconds))
        self._max_frames = max(1, int(max_frames))
        self._frames: Deque[ScheduledVideoFrame] = deque()
        self._first_media_time = None
        self._first_arrival_time = None
        self._dropped_frames = 0

    @staticmethod
    def _media_time(frame):
        pts = getattr(frame, "pts", None)
        time_base = getattr(frame, "time_base", None)
        if pts is None or time_base is None:
            return None

        try:
            return float(pts * time_base)
        except (TypeError, ValueError, ArithmeticError):
            return None

    def enqueue(self, frame, arrival_time: float):
        media_time = self._media_time(frame)
        if media_time is not None and self._first_media_time is None:
            self._first_media_time = media_time
            self._first_arrival_time = arrival_time

        if media_time is not None and self._first_media_time is not None:
            relative_media_time = media_time - self._first_media_time
            if relative_media_time < 0:
                media_time = None
                presentation_time = arrival_time + self._delay_seconds
            else:
                presentation_time = (
                    self._first_arrival_time
                    + self._delay_seconds
                    + relative_media_time
                )
        else:
            presentation_time = arrival_time + self._delay_seconds

        self._frames.append(
            ScheduledVideoFrame(
                frame=frame,
                presentation_time=presentation_time,
                media_time=media_time,
            )
        )

        while len(self._frames) > self._max_frames:
            self._frames.popleft()
            self._dropped_frames += 1

    def pop_due(self, now: float):
        """Return the newest due frame and discard older due frames."""
        newest_due = None
        due_count = 0
        while self._frames and self._frames[0].presentation_time <= now:
            newest_due = self._frames.popleft()
            due_count += 1

        if newest_due is None:
            return None

        self._dropped_frames += max(0, due_count - 1)
        return newest_due

    def seconds_until_next(self, now: float):
        if not self._frames:
            return None
        return max(0.0, self._frames[0].presentation_time - now)

    @property
    def dropped_frames(self):
        return self._dropped_frames

    @property
    def queued_frames(self):
        return len(self._frames)

    def reset(self):
        self._frames.clear()
        self._first_media_time = None
        self._first_arrival_time = None
        self._dropped_frames = 0
