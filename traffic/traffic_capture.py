from operator import attrgetter

from ryu.app import simple_switch_13
from ryu.controller import ofp_event
from ryu.controller.handler import MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller.handler import set_ev_cls
from ryu.lib import hub


class TrafficCapture(simple_switch_13.SimpleSwitch13):

    def __init__(self, *args, **kwargs):
        super(TrafficCapture, self).__init__(*args, **kwargs)
        self.datapaths = {}
        self.traffic_thread = hub.spawn(self._traffic_capture)

    def _traffic_capture(self):
        while True:
            for dp in self.datapaths.values():
                self._send_queue_stats_request(dp)
            hub.sleep(10)

    def _send_queue_stats_request(self, datapath):
        ofp = datapath.ofproto
        ofp_parser = datapath.ofproto_parser

        req = ofp_parser.OFPQueueStatsRequest(datapath, 0, ofp.OFPP_ANY,
                                                ofp.OFPQ_ALL)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPQueueStatsReply, MAIN_DISPATCHER)
    def queue_stats_reply_handler(self, ev):
        queues = []
        for stat in ev.msg.body:
            queues.append('port_no=%d queue_id=%d '
                            'tx_bytes=%d tx_packets=%d tx_errors=%d '
                            'duration_sec=%d duration_nsec=%d' %
                            (stat.port_no, stat.queue_id,
                            stat.tx_bytes, stat.tx_packets, stat.tx_errors,
                            stat.duration_sec, stat.duration_nsec))
        self.logger.debug('QueueStats: %s', queues)