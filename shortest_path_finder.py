# from ryu.base import app_manager
# from ryu.controller.handler import set_ev_cls
# from ryu.ofproto import ofproto_v1_3, ofproto_v1_3_parser
# from ryu.topology import event, switches
# from ryu.topology.api import get_switch, get_link, get_host
# from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER, DEAD_DISPATCHER
# from ryu.controller import ofp_event
# from ryu.lib.packet import packet, ethernet, ether_types
# import networkx as nx 
# from ryu.lib import hub
# from operator import attrgetter

# class ShortestPathFinder(app_manager.RyuApp):
#     OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

#     def __init__(self, *args, **kwargs):
#         super(ShortestPathFinder, self).__init__(*args, **kwargs)

#         self.topology_api_app = self
#         self.switches = None
#         self.links = None
#         self.hosts = None
#         # self.my_next_hop = None
#         # self.my_src = None
#         # self.my_dst = None
#         # self.my_dpid = None
#         self.G = nx.DiGraph() 
#         self.src_lists = []
#         self.datapaths = {}
#         self.monitor_thread = hub.spawn(self._monitor)
#         self.min_weight = [0, 0, 0, 0, 0, 0, 0, 0, 0]
#         self.counter = 0
#         self.count2 = 0
#         # self.dp = 0
#         # self.port_nomber = [0, 0, 0, 0]
#         # self.tx = [0, 0, 0, 0]

#         # self.weight = self.set_weight(self._port_stats_reply_handler(self.event).tx_packets)

#     @set_ev_cls(event.EventSwitchEnter)
#     def get_topology_data(self, ev):
#         switch_list = get_switch(self.topology_api_app, None)
#         self.switches=[switch.dp.id for switch in switch_list]
#         links_list = get_link(self.topology_api_app, None)
#         #self.links=[(link.src.dpid, link.dst.dpid, {'port':link.src.port_no}) for link in links_list]
#         self.links=[(link.src.dpid, link.dst.dpid, {'port':link.src.port_no, 'weight':0.3}) for link in links_list]
#         host_list = get_host(self.topology_api_app, None)
#         self.hosts = [host for host in host_list]

#         self.G.add_nodes_from(self.switches)
#         self.G.add_edges_from(self.links)
# ###################   Important Prints ######################
#         #print(self.G.edges.data())
#         #print("switches:{}, link:{}, hosts:{}".format(self.switches, self.links, self.hosts))
#         #print("hosts:{}".format(self.hosts))
#         #self.G.edges.data('weight', default=0.5)
#         #print(self.G.edges(data=True,default='weight'))
#         #print(self.G.get_edge_data(1,2,default='weight'))
#         #print(nx.get_edge_attributes(self.G,'weight'))
# ##################################################################
# #######################  Add Hosts  ##############################
#         # self.hosts_mac = ['00:00:00:00:00:10','00:00:00:00:00:20',
#         # '00:00:00:00:00:30','00:00:00:00:00:40','00:00:00:00:00:50',
#         # '00:00:00:00:00:60','00:00:00:00:00:70','00:00:00:00:00:80','00:00:00:00:00:90']
#         # i = 0
#         # for hst in self.hosts_mac:
#         #     i = i + 1
#         #     self.G.add_node(hst)
#         #     if(i==5):
#         #         continue
#         #     self.G.add_edge(hst,i,port=1,weight=1)
#         #i_vec = [1, 2, 3, 4, 5, 6, 7, 8, 9]
#         #for j in i_vec:
#         # self.G.add_edge(1,'00:00:00:00:00:10',port=1,weight=1)
#         # self.G.add_edge(2,'00:00:00:00:00:20',port=2,weight=1)
#         # self.G.add_edge(3,'00:00:00:00:00:30',port=2,weight=1)
#         # self.G.add_edge(4,'00:00:00:00:00:40',port=2,weight=1)
#         # self.G.add_edge(6,'00:00:00:00:00:60',port=3,weight=1)
#         # self.G.add_edge(7,'00:00:00:00:00:70',port=2,weight=1)
#         # self.G.add_edge(8,'00:00:00:00:00:80',port=3,weight=1)
#         # self.G.add_edge(9,'00:00:00:00:00:90',port=3,weight=1)

#         #print(self.G.edges.data())
#         #print("")



# ##################################################################

#     @set_ev_cls(ofp_event.EventOFPSwitchFeatures, CONFIG_DISPATCHER)
#     def switch_features_handler(self, ev):
#         datapath = ev.msg.datapath
#         ofproto = datapath.ofproto
#         parser = datapath.ofproto_parser

#         match = parser.OFPMatch()
#         actions = [parser.OFPActionOutput(ofproto.OFPP_CONTROLLER,
#                                           ofproto.OFPCML_NO_BUFFER)]
#         self.add_flow(datapath, 0, match, actions,10)

#     def add_flow(self, datapath, priority, match, actions,timeout, buffer_id=None):
#         hard_timeout= idle_timeout = timeout
#         ofproto = datapath.ofproto
#         parser = datapath.ofproto_parser

#         inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS, 
#                                              actions)]
#         if buffer_id:

#             mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
#                                     priority=priority, match=match,
#                                     instructions=inst,idle_timeout= idle_timeout, hard_timeout=hard_timeout)
#         else:
#             mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
#                                     match=match, instructions=inst,idle_timeout=idle_timeout,hard_timeout= hard_timeout)
#         datapath.send_msg(mod)


#     @set_ev_cls(ofp_event.EventOFPStateChange,
#                 [MAIN_DISPATCHER, DEAD_DISPATCHER])
#     def _state_change_handler(self, ev):
#         datapath = ev.datapath
#         if ev.state == MAIN_DISPATCHER:
#             if datapath.id not in self.datapaths:
#                 self.logger.debug('register datapath: %016x', datapath.id)
#                 self.datapaths[datapath.id] = datapath
#         elif ev.state == DEAD_DISPATCHER:
#             if datapath.id in self.datapaths:
#                 self.logger.debug('unregister datapath: %016x', datapath.id)
#                 del self.datapaths[datapath.id]

#     def _monitor(self):
#         while True:
#             for dp in self.datapaths.values():
#                 self._request_stats(dp)
#             hub.sleep(10)

#     def _request_stats(self, datapath):
#         self.logger.debug('send stats request: %016x', datapath.id)
#         ofproto = datapath.ofproto
#         parser = datapath.ofproto_parser

#         req = parser.OFPPortStatsRequest(datapath, 0, ofproto.OFPP_ANY)
#         datapath.send_msg(req)

#     @set_ev_cls(ofp_event.EventOFPPortStatsReply, MAIN_DISPATCHER)
#     def _port_stats_reply_handler(self, ev):
#         body = ev.msg.body
#         self.logger.info('datapath     port '
#                         'rx-pkts  rx-bytes rx-error '
#                         'tx-pkts  tx-bytes tx-error ')
#         self.logger.info('---------------- -------- '
#                         '-------- -------- -------- '
#                         '-------- -------- --------')
#         # src_switch_dpid = ev.msg.datapath.id
#         # dst_switch_dpid = None
#         # f2 = open('ryu.csv', 'a')
# #        print('count', self.count)
# #        print('received status')
#         #print("hiii {}".format(self.links))
#         # if self.count >= 9:

#         # self.dp[self.count] = ev.msg.datapath.id
#         # print('dpam: {}'.format(self.dp))
#         for stat in sorted(body, key=attrgetter('port_no')):
#             self.logger.info('%016x %8x %8d %8d %8d %8d %8d %8d',
#                                ev.msg.datapath.id, stat.port_no,
#                                stat.rx_packets, stat.rx_bytes, stat.rx_errors,
#                                stat.tx_packets, stat.tx_bytes, stat.tx_errors)
#             # if stat.port_no ==4294967294:
#             #     continue

#             # self.port_nomber[self.count][stat.port_no-1] = stat.port_no
#             # self.tx[self.count][stat.port_no-1] = stat.tx_packets
#         # a = self.tx[self.count]
# #############################################
        

#         # for (u,v) in self.G.edges():    
#             # if(u==ev.msg.datapath.id):
#                 # for stat1 in sorted(body, key=attrgetter('port_no')):
# #                    if (stat1.port_no ==4294967294 or u!=ev.msg.datapath.id):
# #                        continue
# #                    #print(stat1.port_no)
# #                    self.G.add_edge(u,v,port=stat1.port_no,weight=stat1.rx_packets)
# #        print(self.G.edges.data())
       
#         ######### Change the weight of link ############
#         # for (u,v) in self.G.edges():    
#         #     if(u==ev.msg.datapath.id):
#         #         port_num=nx.get_edge_attributes(self.G,'port')
#         #         #print("hiii")
#         #         #print(port_num[(u,v)])
#         #         #print(u,v)
#         #         for stat1 in sorted(body, key=attrgetter('port_no')):
#         #             if ( u!=ev.msg.datapath.id):
#         #                 continue
#         #             if(stat1.port_no == port_num[(u,v)]):
#         #                 #print(stat1.port_no)
#         #                 #print(u,v)
#         #                 self.G.add_edge(u,v,port=stat1.port_no,weight=stat1.rx_packets)
#                         #print("weight of link "+str(u)+"," +str(v)+" changed to "+str(stat1.rx_packets)+" for port "+str(stat1.port_no))
#         #print(self.G.edges.data())

#         ######### find the shortest path for all src and dst ############
#         # self.counter = self.counter +1
#         # if(self.counter == 9):
#         #     self.counter = 0
#         #     print(self.src_lists)
#         #     for src in self.src_lists:
#         #         for dst in self.src_lists:
#         #             path = nx.shortest_path(self.G, src, dst,'weight')
#         #             self.set_path_in_switchs(path,src,dst,ev.msg.datapath)
#         #     print("setting paths done!")
        



# ##############################################
#         # if self.tx[self.count][-1] == 0:
#         #     del a[-1]
#         # self.min_weight[self.count] = min(a)
# #        self.count += 1
#         # print('port', self.port_nomber, 'tx', self.tx, 'minimum', self.min_weight)


        # self.G[src_switch_dpid][dst_switch_dpid]['weight'] ==  self.set_weight(self.tx)
    
#     # def set_weight(self, tx_packets):
#     #     return tx_packets


# ##########################################################
# ################  set path in switchs ####################

#     # def set_path_in_switchs(self,path,src,dst,datapath):
#     #     vec = [1, 2, 3, 4, 5, 6, 7, 8, 9]
#     #     ofproto = datapath.ofproto
#     #     parser = datapath.ofproto_parser
#     #     for dpid in vec:
#     #         out_port = None
#     #         datapath.id = dpid
#     #         if dpid not in path:
#     #             # print('i am not in path')
#     #             continue
#     #         elif dpid != path[-1]:
#     #             next_hop = path[path.index(dpid)+1]
#     #             # print('i am next hop', next_hop)
#     #             out_port = self.G[dpid][next_hop]['port']
#     #             # print('i am out port {} to next hop {}'.format(out_port, next_hop))
#     #         else:
#     #             # print('last ', path[-1])
#     #             out_port = self.G[dpid][dst]['port']
#     #             # print('i am port {} to dst'.format((out_port)))

#     #         # print('i am Graph G {}'.format(self.G[dpid].items()))

#     #         actions = [parser.OFPActionOutput(out_port)]
#     #         # print('i am action ->', actions)

#     #         if out_port != ofproto.OFPP_FLOOD:
#     #             match = parser.OFPMatch(eth_src=src, eth_dst=dst)
#     #             # print('i am match ->', match)
#     #             self.add_flow(datapath, 1, match, actions,0)
#     #             # print('no buffer')

#     #         # data = None
#     #         # if msg.buffer_id != ofproto.OFP_NO_BUFFER:
#     #         #     data = msg.data
#     #         #     # print('i am data ->', data)
            
#     #         out = parser.OFPPacketOut(datapath=datapath, in_port=5, actions=actions)
#     #         # print('i am out message', out)
#     #         # print('i am buffer_id', msg.buffer_id)
#     #         if out is not None:
#     #             datapath.send_msg(out)
#     #             # print('sended')

# ###################################################################



#     @set_ev_cls(ofp_event.EventOFPPacketIn, MAIN_DISPATCHER)
#     def _packet_in_handler(self, ev):
#         if ev.msg.msg_len < ev.msg.total_len:
#             self.logger.debug("packet truncated: only %s of %s bytes",
#                               ev.msg.msg_len, ev.msg.total_len)
#         msg = ev.msg
#         datapath = msg.datapath
#         ofproto = datapath.ofproto
#         parser = datapath.ofproto_parser
#         in_port = msg.match['in_port']

#         pkt = packet.Packet(msg.data)
#         eth = pkt.get_protocols(ethernet.ethernet)[0]

#         if eth.ethertype == ether_types.ETH_TYPE_LLDP:
#             return 

#         dpid = datapath.id
#         print('i am dpid', dpid)    

#         src = eth.src
#         dst = eth.dst

#         #print(src)

#         if src not in self.G: 
#             print("This Mac Address is not in Graph")
#             self.G.add_node(src)
#             print('src {} added to G'.format(src)) 
#             self.G.add_edge(dpid, src, port=in_port,weight=1)
#             # print('link added between dpid {}, src {}'.format(dpid, src))
#             self.G.add_edge(src,dpid,weight=1)
#             self.src_lists.append(src)
#             print('link added between src {} , dpid {}'.format(src, dpid))  
#         # for i in self.dp:
#         #     print('dp: {}'.format(i))

#         # print('received packet')
# #        print('count2', self.count2)
#         # if self.count2 >= 9:
#         #     self.count2 = 0
#         # print(self.dp[self.count2])
#         # for j in range(3):
#         #     print('port: {}, weight: {}'.format(self.port_nomber[self.count2][j], self.tx[self.count2][j]))
#         #     self.min_weight = min(self.tx[self.count2])
#         #     print('minimum', self.min_weight)
#         # self.count2 += 1
#         # print('miniiiiii', self.min_weight)
#         # index2 = self.dp.index(dpid)
#         # print('index', index2)

#         if dst not in self.G:
#             out_port = ofproto.OFPP_FLOOD
#             print('flooded ! in our senario this is ERROR, Return')
#             return
#         else:
#             path = nx.shortest_path(self.G, src, dst,'weight') #, weight=self.min_weight[index2]
#             print('shortest path between {} and {} is {}'.format(src, dst, path))
#             # for switches in path:
#             out_port = None
#             if dpid not in path:
#                 # print('i am not in path')
#                 return
#             elif dpid != path[-1]:
#                 # self.my_next_hop = path[path.index(dpid)+1]
#                 # self.my_src =src
#                 # self.my_dst = dst
#                 # self.my_dpid = dpid
#                 next_hop = path[path.index(dpid)+1]
#                 # print('i am next hop', next_hop)
#                 out_port = self.G[dpid][next_hop]['port']
#                 # print('i am out port {} to next hop {}'.format(out_port, next_hop))
#             else:
#                 # print('last ', path[-1])
#                 out_port = self.G[dpid][dst]['port']
#                 # print('i am port {} to dst'.format((out_port)))

#         # print('i am Graph G {}'.format(self.G[dpid].items()))

#         actions = [parser.OFPActionOutput(out_port)]
#         # print('i am action ->', actions)

#         if out_port != ofproto.OFPP_FLOOD:
#             match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
#             # print('i am match ->', match)
#             if msg.buffer_id != ofproto.OFP_NO_BUFFER:
#                 self.add_flow(datapath, 1, match, actions, 10, msg.buffer_id)
#                 # print('I have Buffer')
#             else:
#                 self.add_flow(datapath, 1, match, actions, 10)
#                 # print('no buffer')

#         # data = None
#         # if msg.buffer_id != ofproto.OFP_NO_BUFFER:
#         #     data = msg.data
#         #     # print('i am data ->', data)
            
#         out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
#                                     in_port=in_port, actions=actions)
#         # print('i am out message', out)
#         # print('i am buffer_id', msg.buffer_id)
#         if out is not None:
#             datapath.send_msg(out)
#             # print('sended')




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

class ShortestPathFinder(app_manager.RyuApp):
    OFP_VERSIONS = [ofproto_v1_3.OFP_VERSION]

    def __init__(self, *args, **kwargs):
        super(ShortestPathFinder, self).__init__(*args, **kwargs)

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
        ofproto = datapath.ofproto
        parser = datapath.ofproto_parser

        inst = [parser.OFPInstructionActions(ofproto.OFPIT_APPLY_ACTIONS,
                                             actions)]
        if buffer_id:
            mod = parser.OFPFlowMod(datapath=datapath, buffer_id=buffer_id,
                                    priority=priority, match=match,
                                    instructions=inst)
        else:
            mod = parser.OFPFlowMod(datapath=datapath, priority=priority,
                                    match=match, instructions=inst)#, idle_timeout=idle_timeout, hard_timeout=hard_timeout)
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
        # dp = ev.msg.datapath.id
        # dp_id = format(dp, "d".zfill(1))
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
                print(self.A)
                self.tx_pkts[stat.port_no-2][src_switch_dpid-1] = stat.tx_packets
                print(self.tx_pkts)
                # print('A', self.A)
            
        # filename = "test/test"+str(id)+".txt"
        # f = open("")
            
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
        # print('src {} dst{}'.format(src, dst), type(src))
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
            # self.n_nodes.append(self.nn)
            # print(self.n_nodes)
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

            # out_port = None
            # if dpid not in path:
            #     return
            # elif dpid != path[-1]:
            #     next_hop = path[path.index(dpid)+1]
            #     print('i am next hop', next_hop)
            #     out_port = self.G[dpid][next_hop]['port']
            # else:
            #     out_port = self.G[dpid][dst]['port']
            
        # print('i am Graph G {}'.format(self.G[dpid].items()))

        actions = [parser.OFPActionOutput(out_port)]

        if out_port != ofproto.OFPP_FLOOD:
            match = parser.OFPMatch(in_port=in_port, eth_src=src, eth_dst=dst)
            if msg.buffer_id != ofproto.OFP_NO_BUFFER:
                self.add_flow(datapath, 1, match, actions, msg.buffer_id)
            else:
                self.add_flow(datapath, 1, match, actions)

        out = parser.OFPPacketOut(datapath=datapath, buffer_id=msg.buffer_id,
                                    in_port=in_port, actions=actions)
        if out is not None:
            datapath.send_msg(out)