from operator import attrgetter

from shortest_path_finder import ShortestPathFinder
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub
from simple_switch import SimpleSwitch13
class TrafficCapture(ShortestPathFinder):

    def __init__(self, *args, **kwargs):
        super(TrafficCapture, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.traffic_thread = hub.spawn(self._traffic_capture)

    @set_ev_cls(ofp_event.EventOFPStateChange,
                [MAIN_DISPATCHER, DEAD_DISPATCHER])
    def _state_change_handler(self, ev):
        datapath = ev.datapath
        if ev.state == MAIN_DISPATCHER:
            if datapath.id not in self.datapaths:
                self.logger.debug('register datapath: %016x', datapath.id)
                self.datapaths[datapath.id] = datapath
        elif ev.state == DEAD_DISPATCHER:
            if datapath.id in self.datapaths:
                self.logger.debug('unregister datapath: %016x', datapath.id)
                del self.datapaths[datapath.id]

    def _traffic_capture(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser
        req = ofp_parser.OFPQueueStatsRequest(datapath, 0, ofp.OFPP_ANY,
                                                ofp.OFPQ_ALL)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPQueueStatsReply, MAIN_DISPATCHER)
    def _queue_stats_reply_handler(self, ev):
        body = ev.msg.body
        print("hiiiiiiiiii", body)
        self.logger.info('datapath    port    queue_id '
                         'tx-pkts  tx-bytes tx-error ')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- ')

        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d',
                             ev.msg.datapath.id, stat.port_no, stat.queue_id,
                             stat.tx_packets, stat.tx_bytes, stat.tx_errors)
            