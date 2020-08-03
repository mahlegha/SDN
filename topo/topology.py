import networkx as nx

class Topology:
    def __init__(self):
        self.__links = None
        self.__switches = None
        self.__G = None

    def set_switches(self,switches):
        self.__switches = switches

    def set_links(self,links):
        self.__links = links        

    def get_switches(self):
        return self.__switches

    def get_links(self):
        return self.__links

    