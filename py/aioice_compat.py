"""Workaround for an aioice matching bug that crashes ICE negotiation.

aioice's Connection.check_incoming() looks up an existing remote candidate by
(host, port) only, then asserts its component matches the local protocol's
component - instead of also matching on component and falling back to
learning a new peer-reflexive candidate (RFC 5245 7.2.1.3) when it doesn't.
This trips whenever RTP/RTCP (or bundled audio/video) traffic ends up
appearing from the same address:port on different ICE components, which
happens in practice when a NAT/AP reuses source ports (observed on the Pi
over campus wifi) - the assertion then raises inside an asyncio callback and
that STUN check is lost, so the connection never completes and times out.

See https://github.com/aiortc/aioice/blob/main/src/aioice/ice.py
(Connection.check_incoming) - this reimplements that method with the lookup
fixed to also require a matching component before reusing a candidate.
"""

from aioice import ice
from aioice.candidate import Candidate
from aioice.utils import random_string

_patched = False


def apply():
    global _patched
    if _patched:
        return
    _patched = True

    def check_incoming(self, message, addr, protocol):
        component = protocol.local_candidate.component

        remote_candidate = None
        for c in self._remote_candidates:
            if c.host == addr[0] and c.port == addr[1] and c.component == component:
                remote_candidate = c
                break

        if remote_candidate is None:
            # 7.2.1.3. Learning Peer Reflexive Candidates
            remote_candidate = Candidate(
                foundation=random_string(10),
                component=component,
                transport="udp",
                priority=message.attributes["PRIORITY"],
                host=addr[0],
                port=addr[1],
                type="prflx",
            )
            self._remote_candidates.append(remote_candidate)

        pair = self._find_pair(protocol, remote_candidate)
        if pair is None:
            pair = ice.CandidatePair(protocol, remote_candidate)
            pair.state = ice.CandidatePair.State.WAITING
            self._check_list.append(pair)
            self.sort_check_list()

        if pair.state in (ice.CandidatePair.State.WAITING, ice.CandidatePair.State.FAILED):
            self.check_start_task(pair)

        if "USE-CANDIDATE" in message.attributes and not self.ice_controlling:
            pair.remote_nominated = True
            if pair.state == ice.CandidatePair.State.SUCCEEDED:
                pair.nominated = True
                self.check_complete(pair)

    ice.Connection.check_incoming = check_incoming
