from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link
from topo.topology import Topology
from ryu.controller.handler import CONFIG_DISPATCHER, MAIN_DISPATCHER
from ryu.controller import ofp_event

class ShortestPathFinder(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(ShortestPathFinder, self).__init__(*args, **kwargs)
        self.topology_api_app = self
        self.topology = Topology()
        
    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        switches=[switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        links=[(link.src.dpid,link.dst.dpid, {'port_src': link.src.port_no, 'port_dst': link.dst.port_no}) for link in links_list]
        
        #links=[(link.src.dpid,link.dst.dpid,{'port_src':link.src.port_no,'port_dst':link.dst.port_no}) for link in links_list]

        self.topology.set_links(links)
        self.topology.set_switches(switches)

        print ("switches:{} , links:{}".format(self.topology.get_switches(),self.topology.get_links()))

    