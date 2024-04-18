import math
import random

import netsquid as ns

from midpoint_source import MSProtocol
from quantum_processing_protocol import QuantumProcessingProtocol

__all__ = ['ComunicationProtocol']


class ComunicationProtocol(ns.protocols.NodeProtocol):
    STOP_SIGNAL = "stop"
    SEND_BITS = "send_bits"
    SEND_BITS_EVT_TYPE = ns.pydynaa.EventType("send_bits", "send_bits")
    STOP_EVT_TYPE = ns.pydynaa.EventType("stop", "stop")

    def __init__(self, repeaters, eps_conn_plist, link_length, p_lr, p_m, t_clock):
        super().__init__(node=repeaters[0], name=None)

        self.repeaters = repeaters
        self.eps_conn_plist = eps_conn_plist
        self.t_clock = t_clock
        self.link_length = link_length
        self.p_lr = p_lr
        self.p_m = p_m

        self.add_signal(self.STOP_SIGNAL, self.STOP_EVT_TYPE)
        self.add_signal(self.SEND_BITS, self.SEND_BITS_EVT_TYPE)

    def run(self):
        while(True):
            print("start new comunication")
            node_a, node_b = random.sample(range(0, 4), 2)
            if (node_a < node_b):
                i = node_a
                j = node_b
            else:
                i = node_b
                j = node_a
            K_attempts = math.ceil(1 / (self.p_m * self.p_lr))

            protocol1 = QuantumProcessingProtocol(node=self.repeaters[int(node_a)], name=f"PP_{int(node_a)}",
                                                   K_attempts=K_attempts, t_clock=self.t_clock,
                                                   link_length=self.link_length, connection=self.eps_conn_plist[f"{i}_{j}"],
                                                   port=f"q{node_b}", port2=f"c{node_b}")

            protocol2 = QuantumProcessingProtocol(node=self.repeaters[int(node_b)], name=f"PP_{int(node_b)}",
                                                   K_attempts=K_attempts, t_clock=self.t_clock,
                                                   link_length=self.link_length, connection=None, port=f"q{node_a}",
                                                   port2=f"c{node_a}")
            protocol1.start()
            protocol2.start()

            ev_expr = self.await_signal(sender=protocol2, signal_label=QuantumProcessingProtocol.STOP_SIGNAL)
            yield ev_expr
