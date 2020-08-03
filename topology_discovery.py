from ryu.base import app_manager
from ryu.controller.handler import set_ev_cls
from ryu.topology import event, switches
from ryu.topology.api import get_switch, get_link

class TopoDiscovery(app_manager.RyuApp):
    def __init__(self, *args, **kwargs):
        super(TopoDiscovery, self).__init__(*args, **kwargs)
        print("I'm simplest ryu app")
        self.topology_api_app = self

    @set_ev_cls(event.EventSwitchEnter)
    def get_topology_data(self, ev):
        switch_list = get_switch(self.topology_api_app, None)
        switches=[switch.dp.id for switch in switch_list]
        links_list = get_link(self.topology_api_app, None)
        links=[(link.src.dpid,link.dst.dpid,{'port_src':link.src.port_no,'port_dst':link.dst.port_no}) for link in links_list]

        print ("switches:{} , links:{}".format(switches,links))
        return switches,links