import networkx as nx
    
class Topology:
    def __init__(self):
        self.__links = None
        self.__switches = None
        self.__hosts = None
        self.__G = None

    def set_switches(self,switches):
        self.__switches = switches

    def set_links(self,links):
        self.__links = links  

    def set_hosts(self,hosts):
        self.__hosts = hosts

    def get_switches(self):
        return self.__switches

    def get_links(self):
        return self.__links

    def get_hosts(self):
        return self.__hosts

    def calculate_shortest_path(self, src_node, dst_node, weight=None):
        self.__G = nx.Graph()

        if self.__switches is None or self.__links is None or self.__hosts:
            raise Exception("topology has not been discovered yet") 
        
        self.__G.add_nodes_from(self.__switches)
        self.__G.add_nodes_from(self.__hosts)
        self.__G.add_edges_from(self.__links, weight=3)
        # self.generate_graph()
        return nx.shortest_path(self.__G, src_node, dst_node, weight='weight')

    def get_graph(self):
        return self.__G
