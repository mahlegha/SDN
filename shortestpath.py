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

class ShortestPathFinder(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ShortestPathFinder, self).__init__(*args, **kwargs)

        self.topology_api_app = self
        self.switches = None
        self.links = None
        self.hosts =None
        self.A = np.zeros(shape=(6,10))
        self.B = np.zeros(shape=(6,10))
        self.C = np.zeros(shape=(6,10))
        self.D = np.zeros(shape=(6,10))
        self.Z = np.zeros(shape=(1,6,10))
        self.W = np.zeros(shape=(1,1,10))
        self.X1 = []
        self.X2 = None
        self.X = None
        self.Y1 = []
        self.Y = None
        self.nn = 0
        self.tx_pkts = np.zeros(shape=(6,10))
        # self.pkts = np.zeros(shape=(4,9))
        self.G = nx.DiGraph() 
        self.datapaths = {}
        self.min_weight = 0
        self.monitor_thread = hub.spawn(self._monitor)

        # self.weight = self.set_weight(self._port_stats_reply_handler(self.event).tx_packets)

    @set_ev_cls(event.EventSwitchEnter, MAIN_DISPATCHER)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        self.switches=[switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        self.links=[(link.src.dpid, link.dst.dpid, {'port':link.src.port_no, 'weight':1}) for link in links_list]
        host_list = get_host(self.topology_api_app, None)
        self.hosts = [host for host in host_list]

        self.G.add_nodes_from(self.switches)
        self.G.add_edges_from(self.links)

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
        self.logger.debug('switch           port     '
                         'tx-pkts  tx-error ')
        self.logger.debug('---------------- -------- '
                         '-------- -------- --------')
        src_switch_dpid = ev.msg.datapath.id
        dst_switch_dpid = None
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.debug('%016x %8x %8d %8d',
                                src_switch_dpid, stat.port_no,
                                stat.tx_packets, stat.tx_errors)
            if stat.port_no == 1 or stat.port_no ==4294967294:
                continue 
            else:         
                self.A[stat.port_no-2][src_switch_dpid-1] = stat.tx_packets - self.tx_pkts[stat.port_no-2][src_switch_dpid-1]
                # print(self.A)
                self.tx_pkts[stat.port_no-2][src_switch_dpid-1] = stat.tx_packets
                # print(self.tx_pkts)
            for dst, value in self.G[src_switch_dpid].items():
                if int(value['port']) == int(stat.port_no):
                    dst_switch_dpid = dst
            if dst_switch_dpid == None:
                return
            self.G[src_switch_dpid][dst_switch_dpid]['weight'] = self.set_weight(self.A[stat.port_no-2][src_switch_dpid-1])
        
    def set_weight(self, tx_packets):
        return tx_packets

    # def _send_flow_stats_request(self, datapath):
    #     ofp = datapath.ofproto
    #     ofp_parser = datapath.ofproto_parser

    #     cookie = cookie_mask = 0
    #     match = ofp_parser.OFPMatch()
    #     req = ofp_parser.OFPFlowStatsRequest(datapath, 0,
    #                                             ofp.OFPTT_ALL,
    #                                             ofp.OFPP_ANY, ofp.OFPG_ANY,
    #                                             cookie, cookie_mask,
    #                                             match)
    #     datapath.send_msg(req)

    # @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    # def flow_stats_reply_handler(self, ev):
    #     body = ev.msg.body
    #     self.pkts[:][:] = 0
    #     self.logger.info('switch  packet_count    byte_count             '
    #                      'match  instructions ')
    #     self.logger.info('---------------- -------- '
    #                      '-------- -------- --------')
    #     src_switch_dpid = ev.msg.datapath.id
    #     for stat in sorted(body, key=attrgetter('match')):
    #         self.logger.info('%8d %16d %10d\n %s\n %s',
    #                         ev.msg.datapath.id, stat.packet_count, stat.byte_count,
    #                         stat.match, stat.instructions)
    #         if stat.match.items() and stat.match.items()[0][0]=='in_port':
    #             print('stat.match[inport]: {}'.format(stat.match.items()[0][1]))
    #             self.pkts[stat.match.items()[0][1]-1][src_switch_dpid-1] = stat.packet_count
    #             # if self.pkts[stat.match.items()[0][1]-1][src_switch_dpid-1] != 0:
    #             #     self.pkts[stat.match.items()[0][1]-1][src_switch_dpid-1] += stat.packet_count
    #         else:
    #             continue
    #         print(self.pkts)

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
        print('i am switch', dpid)    

        src = eth.src
        dst = eth.dst
        self.hosts = ['00:00:00:00:00:10','00:00:00:00:00:20','00:00:00:00:00:30','00:00:00:00:00:40',
                      '00:00:00:00:00:60','00:00:00:00:00:70','00:00:00:00:00:80','00:00:00:00:00:90'] 
        
        links_list = get_link(self.topology_api_app, None)
        self.links=[(link.src.dpid, link.dst.dpid, {'port':link.src.port_no, 'weight':self.min_weight}) for link in links_list]


        # if self.A[4,dpid-1] == 0:
        #     min_weight = min(self.A[:3,dpid-1])
        #     print('min_weight is {}'.format(min_weight))
        #     min_weight /= 100000
        # else:
        #     min_weight = min(self.A[:4,dpid-1])
        #     print('min_weight is {}'.format(min_weight))
        #     min_weight /= 100000
        # print(self.A[:4,dpid-1])

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
        # if dpid == s_sw:
        #     self.B[5][s_sw-1] = 1
        # elif dpid == d_sw:
        #     self.B[5][d_sw-1] = 1
        # else:
        if isinstance(self.nn, int):
            self.B[5][self.nn-1] = 1
        # if self.nn not in range(1,10): #self.nn = 00:00:00:00:00:30 it means that it recieved to dst before
        else: 
            self.B[5][dpid-1] = 1     #it should start from begining
        self.C = self.A + self.B
        print(self.C)  
        if src not in self.G: 
            self.G.add_node(src)
            self.G.add_edge(dpid, src, port=in_port, weight=1)
            self.G.add_edge(src, dpid, weight=1)
        
        if dst not in self.G:
            out_port = ofproto.OFPP_FLOOD
        else:
            start = datetime.now()
            path = nx.shortest_path(self.G, src, dst, weight='weight')
            end = datetime.now()
            print('elapsed time: {}'.format(end - start))
            print('shortest path between {} and {} is {}'.format(src, dst, path))
            print('i am Graph G {}'.format(self.G[dpid].items()))
            # if dpid not in path:
            #     print('i am not in path')
            #     # self.B[5][:] = 0
            #     # self.B[5][dpid] = 1
            #     # self.C = self.A + self.B
            #     # self.D[0][9] = 1
            #     # self.W = np.concatenate((self.W, self.D[None]), axis=0)
            #     # print(self.W, self.W.shape)
            #     # sio.savemat('next_hop16.mat', {'w':self.W})
            #     # self.Z = np.concatenate((self.Z, self.C[None]), axis=0)
            #     # # print(self.Z, self.Z.shape)
            #     # sio.savemat('matrix_state16.mat', {'z':self.Z})
            
            #     # self.B[3][:] = 0
            #     # self.B[4][:] = 0
            #     # self.B[5][:] = 0
            #     # self.C[:][:] = 0
            #     # self.D[0][:] = 0
            #     return
            # next_hop = path[path.index(dpid)+1]
            self.nn = path[path.index(dpid)+1]
            print('self.next_node: {}'.format(self.nn))
            # if self.nn == dst:
            #     self.B[5][:] = 0
            #     self.B[5][d_sw] = 1
            if dpid != d_sw:
                # self.D[0][self.nn-1] = 1
                # self.W = np.concatenate((self.W, self.D[None]), axis=0)
                # print(self.W, self.W.shape)
                # sio.savemat('next_hop16.mat', {'w':self.W})
                out_port = self.G[dpid][self.nn]['port']
                print('out_port: {}'.format(out_port))
            elif dpid == d_sw:
                # self.D[0][9] = 1
                # self.W = np.concatenate((self.W, self.D[None]), axis=0)
                # print(self.W, self.W.shape)
                # sio.savemat('next_hop16.mat', {'w':self.W})
                out_port = self.G[dpid][dst]['port']
                print('out_port: {}'.format(out_port))


            # # for switches in path:
            # out_port = None
            # if dpid not in path:
            #     # print('i am not in path')
            #     return
            # elif dpid != path[-1]:
            #     print('i am dpid {}'.format(dpid))
            #     next_hop = path[path.index(dpid)+1]
            #     print('i am next hop', next_hop)
            #     if next_hop != path[-1]:
            #         # comment these for cnn
            #         self.D[0][next_hop-1] = 1
            #         self.W = np.concatenate((self.W, self.D[None]), axis=0)
            #         # print(self.W, self.W.shape)
            #         sio.savemat('next_hop.mat', {'w':self.W})
            #     if next_hop == path[-1]:
            #         self.D[0][:] = 0
            #         self.W = np.concatenate((self.W, self.D[None]), axis=0)
            #         # print(self.W, self.W.shape)
            #         sio.savemat('next_hop.mat', {'w':self.W})
            #     out_port = self.G[dpid][next_hop]['port']
            #     # print('i am out port {} to next hop {}'.format(out_port, next_hop))
            # else:
            #     # print('last ', path[-1])
            #     print('i am dpid {}'.format(dpid))
            #     out_port = self.G[dpid][dst]['port']



            # comment these when running with cnn
            # self.B[3][s_sw-1] = 1
            # self.B[4][d_sw-1] = 1
            # self.B[5][dpid-1] = 1
            # self.C = self.A + self.B
            # self.Z = np.concatenate((self.Z, self.C[None]), axis=0)
            # print(self.Z, self.Z.shape)
            # sio.savemat('matrix_state16.mat', {'z':self.Z})
         
            self.B[3][:] = 0
            self.B[4][:] = 0
            self.B[5][:] = 0
            self.C[:][:] = 0
            self.D[0][:] = 0
        # print('i am Graph G {}'.format(self.G[dpid].items()))

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