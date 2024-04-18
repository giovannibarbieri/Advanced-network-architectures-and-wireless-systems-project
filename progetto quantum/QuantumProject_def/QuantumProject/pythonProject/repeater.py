"""
This module contains the implementation of a quantum repeater node
"""

import netsquid as ns

class Repeater(ns.nodes.Node):
    """
    This class implements a quantum repeater node
    """

    def __init__(self, ID, name):
        """
        Initialize a Repeater.
        """
        super().__init__(name=name, ID=ID, port_names=["q0", "q1", "q2", "q3", "c0", "c1", "c2", "c3"])
        # self.qmemory = ns.components.QuantumMemory("qmemory", num_positions=2)

        physical_instructions = [
            ns.components.PhysicalInstruction(ns.components.INSTR_CX, duration=1., parallel=True),
            ns.components.PhysicalInstruction(ns.components.INSTR_MEASURE, duration=1., parallel=True)
        ]
        qproc = ns.components.QuantumProcessor("qproc", num_positions=2, phys_instructions=physical_instructions)

        self.qmemory = qproc

