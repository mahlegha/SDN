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
        
#        self.A = np.zeros(shape=(7,9))
#        self.B = np.zeros(shape=(7,9))
#        self.C = np.zeros(shape=(7,9))
#        self.D = np.zeros(shape=(1,10))
#        self.Z = np.zeros(shape=(1,7,9))
#        self.W = np.zeros(shape=(1,1,10))
        
        self.A = np.zeros(shape=(7,9))
        # self.A[0][1]=1
        # self.A[1][0]=1
        # self.A[0][3]=1
        # self.A[3][0]=1
        # self.A[1][2]=1
        # self.A[2][1]=1
        # self.A[1][4]=1
        # self.A[4][1]=1
        # self.A[2][5]=1
        # self.A[5][2]=1
        # self.A[3][4]=1
        # self.A[4][3]=1
        # self.A[3][6]=1
        # self.A[6][3]=1
        # self.A[4][5]=1
        # self.A[5][4]=1
        # self.A[4][7]=1
        # self.A[7][4]=1
        # self.A[5][8]=1
        # self.A[8][5]=1
        # self.A[6][7]=1
        # self.A[7][6]=1
        # self.A[7][8]=1
        # self.A[8][7]=1
        self.B = np.zeros(shape=(7,9))
        self.C = np.zeros(shape=(7,9))
        self.D = np.zeros(shape=(1,10))
        self.Z = np.zeros(shape=(1,7,9))
        self.W = np.zeros(shape=(1,1,10))
        
        self.tx_pkts = np.zeros(shape=(7,9))
        self.nn = 0
        self.G = nx.DiGraph() 
        self.datapaths = {}
        self.min_weight = 0
        self.monitor_thread = hub.spawn(self._monitor)

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
            hub.sleep(7.5)

    # def _request_stats(self, datapath):
    #     self.logger.debug('send stats request: %016x', datapath.id)
    #     parser = datapath.ofproto_parser

    #     req = parser.OFPFlowStatsRequest(datapath)
    #     datapath.send_msg(req)

    def _request_stats(self, datapath):
        self.logger.debug('send stats request: %016x', datapath.id)
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
        datapath.send_msg(req)

    # @set_ev_cls(ofp_event.EventOFPFlowStatsReply, MAIN_DISPATCHER)
    # def _flow_stats_reply_handler(self, ev):
    #     body = ev.msg.body
    #     self.logger.debug('datapath         in-port  eth-dst           out-port packets')
    #     self.logger.debug('---------------------------------------------------------------------- ')
    #     src_switch_dpid = ev.msg.datapath.id
    #     dst_switch_dpid = None
    #     temp = 0
    #     ports = []
    #     for stat in sorted([flow for flow in body if flow.priority == 1],
    #                        key=lambda flow: (flow.instructions[0].actions[0].port)): #(flow.match['in_port'], flow.match['eth_dst']) 
    #         self.logger.debug('%016x %8x %17s %8x %8d', ev.msg.datapath.id, stat.match['in_port'], 
    #                          stat.match['eth_dst'], stat.instructions[0].actions[0].port, stat.packet_count)                
    #         if stat.match['in_port'] == stat.instructions[0].actions[0].port:
    #             continue
    #         if stat.instructions[0].actions[0].port == temp:
    #             self.A[stat.instructions[0].actions[0].port-1][src_switch_dpid-1] += stat.packet_count
    #         else:
    #             self.A[stat.instructions[0].actions[0].port-1][src_switch_dpid-1] = stat.packet_count
    #         temp = stat.instructions[0].actions[0].port 
    #         for dst, value in self.G[src_switch_dpid].items():
    #             if int(value['port']) == int(stat.instructions[0].actions[0].port):
    #                 dst_switch_dpid = dst
    #         if dst_switch_dpid == None:
    #             return
    #         self.G[src_switch_dpid][dst_switch_dpid]['weight'] = self.set_weight(self.A[stat.instructions[0].actions[0].port-1][src_switch_dpid-1])
    #         ports.append(stat.instructions[0].actions[0].port)
    #     for i in range(1,5):    
    #         if i not in ports:
    #             self.A[i-1][src_switch_dpid-1] = 0
    #             for dst, value in self.G[src_switch_dpid].items():
    #                 if int(value['port']) == i:
    #                     dst_switch_dpid = dst
    #                     self.G[src_switch_dpid][dst_switch_dpid]['weight'] = self.set_weight(1.0)

    @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
    def _port_stats_reply_handler(self, ev):
        body = ev.msg.body
        self.logger.debug('switch           port       tx-pkts     tx-error ')
        self.logger.debug('----------------------------------------------------------------')
        src_switch_dpid = ev.msg.datapath.id
        dst_switch_dpid = None
        i = 0
        for stat in sorted(body, key=attrgetter('port_no')):
            self.logger.debug('%016x %8x %8d %8d', src_switch_dpid, stat.port_no,
                                stat.tx_packets, stat.tx_errors)
            if stat.port_no ==4294967294:
                continue 
            else: 
                self.A[stat.port_no-1][src_switch_dpid-1] = stat.tx_packets - self.tx_pkts[stat.port_no-1][src_switch_dpid-1]
                self.tx_pkts[stat.port_no-1][src_switch_dpid-1] = stat.tx_packets
            for dst, value in self.G[src_switch_dpid].items():
                if int(value['port']) == int(stat.port_no):
                    dst_switch_dpid = dst
            if dst_switch_dpid == None:
                return
            self.G[src_switch_dpid][dst_switch_dpid]['weight'] = self.set_weight(self.A[stat.port_no-1][src_switch_dpid-1])
            i += 1
            if i != stat.port_no:
                self.A[i-1][src_switch_dpid-1] = 0
                for dst, value in self.G[src_switch_dpid].items():
                    if int(value['port']) == i:
                        dst_switch_dpid = dst
                        self.G[src_switch_dpid][dst_switch_dpid]['weight'] = self.set_weight(1.0)
        print(datetime.now())
        print(self.A)
                

            
    def set_weight(self, tx_packets):
        return tx_packets

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
        print('switch', dpid)    

        src = eth.src
        dst = eth.dst
        self.hosts = ['00:00:00:00:00:10','00:00:00:00:00:20','00:00:00:00:00:30','00:00:00:00:00:40',
                      '00:00:00:00:00:60','00:00:00:00:00:70','00:00:00:00:00:80','00:00:00:00:00:90'] 
        
        links_list = get_link(self.topology_api_app, None)
        self.links=[(link.src.dpid, link.dst.dpid, {'port':link.src.port_no, 'weight':self.min_weight}) for link in links_list]

        if src in self.hosts:
            s_sw = int(src[15])
            # print('s_sw {}'.format(s_sw))
        else:
            return
        if dst in self.hosts:
            d_sw = int(dst[15])
            # print('d_sw {}'.format(d_sw))
        else:
            return

        self.B[4][s_sw-1] = 1
        self.B[5][d_sw-1] = 1
        self.B[6][dpid-1] = 1
        # if isinstance(self.nn, int):
        #     self.B[6][self.nn-1] = 1
        # else: 
        #     self.B[6][dpid-1] = 1     #it should start from begining
        self.C = self.A + self.B
        # print(self.C)
        
        if src not in self.G: 
            self.G.add_node(src)
            self.G.add_edge(dpid, src, port=in_port, weight=1)
            self.G.add_edge(src, dpid, weight=1)
        
        if dst not in self.G:
            out_port = ofproto.OFPP_FLOOD
            print('flooooooooooooooooooooooooded')
            self.B[4][:] = 0
            self.B[5][:] = 0
            self.B[6][:] = 0
            self.C[:][:] = 0
            self.D[0][:] = 0
            
        else:
            start = datetime.now()
            path = list(nx.dijkstra_path(self.G, src, dst, weight='weight'))
            end = datetime.now()
            print('elapsed time: {}'.format(end - start))
            if dpid not in path:
                # print('i am not in path')
                path = list(nx.dijkstra_path(self.G, dpid, dst, weight='weight'))
                print(datetime.now())
                print('shortest path between {} and {} is {}'.format(dpid, d_sw, path[:-1]))
                # self.B[4][:] = 0
                # self.B[5][:] = 0
                # self.B[6][:] = 0
                # self.C[:][:] = 0
                # self.D[0][:] = 0
                # return
            else:
                print(datetime.now())
                print('shortest path between {} and {} is {}'.format(s_sw, d_sw, path[1:-1]))
            # print('i am Graph G {}'.format(self.G[dpid].items()))
            # print('path: {}'.format(path))
            print('\n\n')
            self.nn = path[path.index(dpid)+1]
            if dpid != d_sw:
                self.D[0][self.nn-1] = 1
                self.W = np.concatenate((self.W, self.D[None]), axis=0)
                sio.savemat('next_hop.mat', {'w':self.W})
                out_port = self.G[dpid][self.nn]['port']
                # print('out_port: {}'.format(out_port))
            else:
                self.D[0][9] = 1    #recieved to dst
                self.W = np.concatenate((self.W, self.D[None]), axis=0)
                sio.savemat('next_hop.mat', {'w':self.W})
                out_port = self.G[dpid][dst]['port']
                # print('out_port: {}'.format(out_port))

            self.Z = np.concatenate((self.Z, self.C[None]), axis=0)
            sio.savemat('matrix_state.mat', {'z':self.Z})
         
            self.B[4][:] = 0
            self.B[5][:] = 0
            self.B[6][:] = 0
            self.C[:][:] = 0
            self.D[0][:] = 0

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id, 15)
            else:
                self.add_flow(datapath, 1, match, actions, 15)
        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=in_port, actions=actions)
        if out is not None:
            datapath.send_msg(out)
