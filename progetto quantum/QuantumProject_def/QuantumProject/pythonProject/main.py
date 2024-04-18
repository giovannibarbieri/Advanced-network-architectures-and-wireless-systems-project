import netsquid as ns

from repeater import Repeater
from midpoint_source import get_EPS_connection
from comunication_protocol import ComunicationProtocol

repeaters = []

def get_network(num_nodes, link_length, p_lr, p_m, t_clock):
    # create the network
    net = ns.nodes.Network("Quantum Repeater Network")

    # create and add the repeaters to the network

    for i in range(num_nodes):
        repeater = Repeater(ID=i, name=f"Repeater_{i}")
        net.add_node(repeater)
        repeaters.append(repeater)

    # create the classical connections
    for i in range(num_nodes - 1):
        for j in range(i + 1, num_nodes):
            channel_i_to_j = ns.components.ClassicalChannel(f"channel_{i}_to_{j}",
                                                            length=link_length,
                                                            models={
                                                                "delay_model": ns.components.models.FibreDelayModel()})
            channel_j_to_i = ns.components.ClassicalChannel(f"channel_{j}_to_{i}",
                                                            length=link_length,
                                                            models={
                                                                "delay_model": ns.components.models.FibreDelayModel()})
            classical_connection_i_to_j = ns.nodes.DirectConnection(f"classical_conn_{i}_to_{j}",
                                                                    channel_i_to_j, channel_j_to_i)

            net.add_connection(node1=repeaters[i], node2=repeaters[j], connection=classical_connection_i_to_j,
                               port_name_node1=f"c{j}", port_name_node2=f"c{i}", label=f"classical_conn_{i}_to_{j}")

    eps_conn_plist = {}
    # create the EPS connection
    for i in range(num_nodes-1):
        for j in range(i + 1, num_nodes):
            eps_conn = get_EPS_connection(p_m=p_m, p_lr=p_lr, t_clock=t_clock, length=link_length)
            net.add_connection(node1=repeaters[i], node2=repeaters[j], connection=eps_conn,
                               port_name_node1=f"q{j}", port_name_node2=f"q{i}", label=f"eps_conn_{i}_to_{j}")
            eps_conn_plist[f"{i}_{j}"] = eps_conn


    protocol = ComunicationProtocol(repeaters, eps_conn_plist, link_length, p_lr, p_m, t_clock)
    protocol.start()

    return net

if __name__ == '__main__':
    ns.set_qstate_formalism(ns.QFormalism.DM)
    num_nodes = 4  # Specify the number of nodes you want in the network
    network = get_network(num_nodes=num_nodes, link_length=30, p_lr=0.9, p_m=0.02, t_clock=10)
    ns.sim_run()