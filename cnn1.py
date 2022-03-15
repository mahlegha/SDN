from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link, get_host
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
from ryu.controller import ofp_event
from ryu.lib.packet import packet, ethernet, ether_types
import networkx as nx 
from ryu.lib import hub
from operator import attrgetter
import numpy as np
import scipy.io as sio
from datetime import datetime
import tensorflow as tf
from tensorflow.keras.models import load_model

class CNNPathFinder(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(CNNPathFinder, self).__init__(*args, **kwargs)

        self.topology_api_app = self
        self.switches = None
        self.links = None
        self.hosts =None
        self.tx_pkts = np.zeros(shape=(6,9))
        self.A = np.zeros(shape=(6,9))
        self.B = np.zeros(shape=(6,9))
        self.C = np.zeros(shape=(6,9))
        self.D = np.zeros(shape=(1,11))
        self.Z = np.zeros(shape=(1,6,9))
        self.W = np.zeros(shape=(1,1,11))
        self.X1 = []
        self.X2 = None
        self.X = None
        self.Y1 = []
        self.Y = None
        self.trained = load_model('trained.h5')
        self.nn = 0
        self.n_nodes = []

        self.G = nx.DiGraph() 
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        self.switches=[switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        self.links=[(link.src.dpid, link.dst.dpid, {'port':link.src.port_no}) for link in links_list]
        host_list = get_host(self.topology_api_app, None)
        self.hosts = [host for host in host_list]

        self.G.add_nodes_from(self.switches)
        self.G.add_edges_from(self.links)

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None,timeout=0):
        hard_timeout= idle_timeout = timeout
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst, idle_timeout=idle_timeout, hard_timeout=hard_timeout)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst, idle_timeout=idle_timeout, hard_timeout=hard_timeout)
        datapath.send_msg(mod)

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

    def _monitor(self):
        while True:
            for dp in self.datapaths.values():
                self._request_stats(dp)
            hub.sleep(10)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        # self.logger.info(body)
        self.logger.debug('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error ')
        self.logger.debug('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        src_switch_dpid = ev.msg.datapath.id
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.debug('%016x %8x %8d %8d',
                                src_switch_dpid, stat.port_no,
                                stat.tx_packets, stat.tx_errors)
            if stat.port_no == 1 or stat.port_no ==4294967294:
                continue 
            else:         
                self.A[stat.port_no-2][src_switch_dpid-1] = stat.tx_packets - self.tx_pkts[stat.port_no-2][src_switch_dpid-1]
                print(self.A)
                self.tx_pkts[stat.port_no-2][src_switch_dpid-1] = stat.tx_packets
                print(self.tx_pkts)
            
    @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
    def _packet_in_handler(self, ev):
        if ev.msg.msg_len < ev.msg.total_len:
            self.logger.debug("packet truncated: only %s of %s bytes",
                              ev.msg.msg_len, ev.msg.total_len)
        msg = ev.msg
        datapath = msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser
        in_port = msg.match['in_port']

        pkt = packet.Packet(msg.data)
        eth = pkt.get_protocols(ethernet.ethernet)[0]

        if eth.ethertype == ether_types.ETH_TYPE_LLDP:
            return 

        dpid = datapath.id
        print('i am dpid', dpid)    

        src = eth.src
        dst = eth.dst
        self.hosts = ['00:00:00:00:00:10','00:00:00:00:00:20','00:00:00:00:00:30','00:00:00:00:00:40',
                      '00:00:00:00:00:60','00:00:00:00:00:70','00:00:00:00:00:80','00:00:00:00:00:90']

        if src in self.hosts:
            s_sw = int(src[15])
            print('s_sw {}'.format(s_sw))
        else:
            return
        if dst in self.hosts:
            d_sw = int(dst[15])
            print('d_sw {}'.format(d_sw))
        else:
            return
        
        self.B[3][s_sw-1] = 1
        self.B[4][d_sw-1] = 1
        if isinstance(self.nn, int):
            self.B[5][self.nn-1] = 1
        else: 
            self.B[5][dpid-1] = 1     #it should start from begining
        self.C = self.A + self.B
        print(self.C)
        self.C[:3][:] = self.C[:3][:]/1302.0
        self.C = self.C.reshape(-1,6,9,1)
        # print(self.C)
        
        if src not in self.G: 
            self.G.add_node(src)
            self.G.add_edge(dpid, src, port=in_port)
            self.G.add_edge(src,dpid)
            
        if dst not in self.G:
            out_port = ofproto.OFPP_FLOOD
        else:
            start = datetime.now()
            n_node = self.trained.predict(self.C)
            end = datetime.now()
            print('elapsed time: {}'.format(end-start))
            self.nn = np.argmax(n_node) + 1
            print('self.nn: {}'.format(self.nn))
            if self.nn == 10:
                self.nn = dpid
            elif self.nn == 11:
                print('not in path!')
                self.B[:][:] = 0
                self.C[:][:] = 0
                return

            self.B[:][:] = 0
            self.C[:][:] = 0
            out_port = None
            if dpid == self.nn:
                print('start an other path')
                return
            if dpid == d_sw: #and self.nn == 10:
                out_port = self.G[dpid][dst]['port']
                print('i am out portak {}'.format(out_port))
            else:
                out_port = self.G[dpid][self.nn]['port']
                print('i am out port {}'.format(out_port))

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id, 10)
            else:
                self.add_flow(datapath, 1, match, actions, 10)

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=in_port, actions=actions)
        if out is not None:
            datapath.send_msg(out)