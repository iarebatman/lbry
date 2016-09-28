import logging

from twisted.internet import defer
from twisted.internet.task import LoopingCall

log = logging.getLogger(__name__)


class BlobAvailabilityTracker(object):
    """
    Class to track peer counts for known blobs, and to discover new popular blobs

    Attributes:
        availability (dict): dictionary of peers for known blobs
    """

    def __init__(self, blob_manager, peer_finder, dht_node):
        self.availability = {}
        self.last_mean_availability = 0.0
        self._blob_manager = blob_manager
        self._peer_finder = peer_finder
        self._dht_node = dht_node
        self._check_popular = LoopingCall(self._update_most_popular)
        self._check_mine = LoopingCall(self._update_mine)

    def start(self):
        log.info("Starting blob tracker")
        self._check_popular.start(30)
        self._check_mine.start(120)

    def stop(self):
        if self._check_popular.running:
            self._check_popular.stop()
        if self._check_mine.running:
            self._check_mine.stop()

    def _update_peers_for_blob(self, blob):
        def _save_peer_info(blob_hash, peers):
            v = {blob_hash: peers}
            self.availability.update(v)
            return v

        d = self._peer_finder.find_peers_for_blob(blob)
        d.addCallback(lambda r: [[c.host, c.port, c.is_available()] for c in r])
        d.addCallback(lambda peers: _save_peer_info(blob, peers))
        return d

    def _update_most_popular(self):
        def _get_most_popular():
            dl = []
            for (hash, _) in self._dht_node.get_most_popular_hashes(100):
                encoded = hash.encode('hex')
                dl.append(self._update_peers_for_blob(encoded))
            return defer.DeferredList(dl)
        d = _get_most_popular()
        d.addCallback(lambda _: self._get_mean_peers())

    def _update_mine(self):
        def _get_peers(blobs):
            dl = []
            for hash in blobs:
                dl.append(self._update_peers_for_blob(hash))
            return defer.DeferredList(dl)
        d = self._blob_manager.get_all_verified_blobs()
        d.addCallback(_get_peers)
        d.addCallback(lambda _: self._get_mean_peers())

    def _get_mean_peers(self):
        num_peers = [len(self.availability[blob]) for blob in self.availability]
        mean = float(sum(num_peers)) / float(max(1, len(num_peers)))
        self.last_mean_availability = mean