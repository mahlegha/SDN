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

class ShortestPathFinder(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ShortestPathFinder, self).__init__(*args, **kwargs)

        self.topology_api_app = self
        self.switches = None
        self.links = None
        self.hosts = None
        
        self.G = nx.DiGraph() 
        self.datapaths = {}
        self.monitor_thread = hub.spawn(self._monitor)

        # self.weight = self.set_weight(self._port_stats_reply_handler(self.event).tx_packets)

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        self.switches=[switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        self.links=[(link.src.dpid, link.dst.dpid, {'port':link.src.port_no}) for link in links_list]
        host_list = get_host(self.topology_api_app, None)
        self.hosts = [host for host in host_list]

        self.G.add_nodes_from(self.switches)
        self.G.add_edges_from(self.links, )

        # print("switches:{}, link:{}, hosts:{}".format(self.switches, self.links, self.hosts))

    @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
    def switch_features_handler(self, ev):
        datapath = ev.msg.datapath
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        match = parser.OFPMatch()
        actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
                                          ofproto.OFPCML_NO_BUFFER)]
        self.add_flow(datapath, 0, match, actions)

    def add_flow(self, datapath, priority, match, actions, buffer_id=None,timeout=0)
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
        self.logger.info('datapath         port     '
                         'rx-pkts  rx-bytes rx-error '
                         'tx-pkts  tx-bytes tx-error ')
        self.logger.info('---------------- -------- '
                         '-------- -------- -------- '
                         '-------- -------- --------')
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
                                ev.msg.datapath.id, stat.port_no,
                                stat.rx_packets, stat.rx_bytes, stat.rx_errors,
                                stat.tx_packets, stat.tx_bytes, stat.tx_errors)
            
    # def set_weight(self, tx_packets):
    #     return tx_packets

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

        if src not in self.G: 
            self.G.add_node(src)
            # print('src {} added to G'.format(src)) 
            self.G.add_edge(dpid, src, port=in_port)
            print('link added between dpid {}, src {}'.format(dpid, src))
            print('port between dpid{} src {} is {}'.format(dpid, src, self.G[dpid][src]['port']))
            self.G.add_edge(src,dpid)
            # print('link added between src {} , dpid {}'.format(src, dpid))  
        # for i in self.dp:
        #     print('dp: {}'.format(i))


        
        if dst not in self.G:
            out_port = ofproto.OFPP_FLOOD
            # print('flooded')
        else:
            path = nx.shortest_path(self.G, src, dst) #, weight=self.min_weight[index2]
            print('shortest path between {} and {} is {}'.format(src, dst, path))
            # for switches in path:
            out_port = None
            if dpid not in path:
                # print('i am not in path')
                return
            elif dpid != path[-1]:
                next_hop = path[path.index(dpid)+1]
                # print('i am next hop', next_hop)
                out_port = self.G[dpid][next_hop]['port']
                # print('i am out port {} to next hop {}'.format(out_port, next_hop))
            else:
                # print('last ', path[-1])
                out_port = self.G[dpid][dst]['port']
                # print('i am port {} to dst'.format((out_port)))

        # print('i am Graph G {}'.format(self.G[dpid].items()))

        actions = [parser.OFPActionOutput(out_port)]
        # print('i am action ->', actions)

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
            # print('i am match ->', match)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id, 10)
                # print('I have Buffer')
            else:
                self.add_flow(datapath, 1, match, actions, 10)
                # print('no buffer')

        # data = None
        # if msg.buffer_id != ofproto.OFP_NO_BUFFER:
        #     data = msg.data
        #     # print('i am data ->', data)
            
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=in_port, actions=actions)
        # print('i am out message', out)
        # print('i am buffer_id', msg.buffer_id)
        if out is not None:
            datapath.send_msg(out)
            # print('sended')
