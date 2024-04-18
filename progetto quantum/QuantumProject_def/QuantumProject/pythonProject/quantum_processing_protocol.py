import netsquid as ns

from midpoint_source import MSProtocol

__all__ = ['QuantumProcessingProtocol']


class QuantumProcessingProtocol(ns.protocols.NodeProtocol):
    STOP_SIGNAL = "stop"
    SEND_BITS = "send_bits"
    SEND_BITS_EVT_TYPE = ns.pydynaa.EventType("send_bits", "send_bits")
    STOP_EVT_TYPE = ns.pydynaa.EventType("stop", "stop")

    def __init__(self, node, name=None, K_attempts=200, t_clock=10, link_length=25, connection=None, port=None, port2=None):
        super().__init__(node=node, name=name)
        self.add_subprotocol(MSProtocol(self.node, K_attempts=K_attempts, link_length=link_length, t_clock=t_clock, port = port, port2 = port2,
                                        connection=connection, mem_position=0), name="MSProtocol_0")
        self.add_subprotocol(MSProtocol(self.node, K_attempts=K_attempts, link_length=link_length, t_clock=t_clock, port = port, port2 = port2,
                                        connection=connection, mem_position=1), name="MSProtocol_1")
        self.port2 = port2
        self.connection = connection
        self.end = True
        self.add_signal(self.STOP_SIGNAL, self.STOP_EVT_TYPE)
        self.add_signal(self.SEND_BITS, self.SEND_BITS_EVT_TYPE)

    @staticmethod
    def _get_purification_program():
        # create a program that will be used to purify the qubits
        program = ns.components.QuantumProgram(num_qubits=2)
        q1, q2 = program.get_qubit_indices(2)
        program.apply(ns.components.INSTR_CX, qubit_indices=[q1, q2])
        program.apply(ns.components.INSTR_MEASURE, [q2], output_key="M0")
        return program

    def _get_fidelity(self, position):
        qubits = self.node.qmemory.peek(positions=[position])[0].qstate.qubits
        fidelity = ns.qubits.qubitapi.fidelity(qubits, ns.qubits.ketstates.b00, squared=True)
        return fidelity

    def run(self):

        # first thing to do is to create the entangled pair on the first memory slot
        self.subprotocols["MSProtocol_0"].start()

        # wait for the first MSProtocol to finish
        ev_expr = self.await_signal(sender=self.subprotocols["MSProtocol_0"], signal_label=MSProtocol.ENTANGLED_SIGNAL)
        yield ev_expr

        # start the second MSProtocol to entangle the second qubit
        self.subprotocols["MSProtocol_1"].start()

        # wait for the second MSProtocol to finish
        ev_expr = self.await_signal(sender=self.subprotocols["MSProtocol_1"], signal_label=MSProtocol.ENTANGLED_SIGNAL)
        yield ev_expr

        # get the fidelity of the qubits
        #fidelity_0 = self._get_fidelity(0)
        #fidelity_1 = self._get_fidelity(1)

        #print(f"[{ns.sim_time()}] Repeater {self.node.ID}: Both qubits are entangled with fidelity {fidelity_0} and {fidelity_1}")

        # at this point we have two entangled qubits in the memory
        prog = self._get_purification_program()

        self.node.qmemory.execute_program(prog, qubit_mapping=[0, 1], error_on_fail=True)
        yield self.await_program(self.node.qmemory)

        # we collect the measurement result
        outcome = prog.output["M0"][0]

        # we send the measurement result to the other node
        self.node.ports[self.port2].tx_output(ns.components.Message(items=outcome))

        # we wait for the measurement result from the other node
        yield self.await_port_input(self.node.ports[self.port2])
        msg = self.node.ports[self.port2].rx_input()
        outcome_other = msg.items[0]

        # we check if the measurement results are the same

        if self.connection is not None:
            if outcome == outcome_other:
                print(f"[{ns.sim_time()}] Purification successful")
                # print the new qubit fidelity with respect to the bell state
                #print(f"[{ns.sim_time()}] Fidelity of the new qubit pair with respect to the Bell state: {self._get_fidelity(position=0)}")
        if outcome != outcome_other:
            print(f"[{ns.sim_time()}] Purification failed")
            # discard the qubit from memory
            self.node.qmemory.pop(positions=0)
            self.send_signal(self.STOP_SIGNAL, result=None)
            return

        # -------------teleportation protocol-----------------

        qubit_teleportation = ns.qubits.create_qubits(1)[0]

        if self.connection is not None:
            print("STARTING TELEPORTATION PROTOCOL")
            ns.qubits.operate(qubit_teleportation, ns.X)
            qubit_0 = self.node.qmemory.peek(positions=[0])[0]
            # stato |0>
            """
            print("PRIMO QUBIT ENTANGLE")
            print(qubit_0.qstate.qrepr)
            print("QUBIT DA INVIARE")
            print(qubit_teleportation.qstate.qrepr)
            """
            ns.qubits.operate([qubit_teleportation, qubit_0], ns.CNOT)
            ns.qubits.operate(qubit_teleportation, ns.H)
            """
            print("QUBIT ENTANGLE DOPO MODIFICHE")
            print(qubit_0.qstate.qrepr)
            """
            m0, _ = ns.qubits.measure(qubit_teleportation)
            m1, _ = ns.qubits.measure(qubit_0)

            print("MEASUREMENTS:  ", m0,m1)
            self.node.ports[self.port2].tx_output(ns.components.Message(items=[m0,m1]))
            self.send_signal(self.SEND_BITS, result=None)
        else:
            print("STARTING TELEPORTATION PROTOCOL: WAITING FOR MEASUREMENT FROM CLASSICAL CHANNEL")
            yield self.await_port_input(self.node.ports[self.port2])
            msg = self.node.ports[self.port2].rx_input()
            measured = msg.items
            print("measured: "+str(measured))

            qubit_entangled = self.node.qmemory.peek(positions=[0])[0]
            """
            print("Before correction: ")
            print(qubit_entangled.qstate.qrepr)
            print("stato: "+str(qubit_entangled.qstate.qubits))
            """
            if measured[1] == 1:
                print("correzione X")
                ns.qubits.operate(qubit_entangled, ns.X)
            if measured[0] == 1:
                print("correzione Z")
                ns.qubits.operate(qubit_entangled, ns.Z)

            """
            print("After correction: "+str(qubit_entangled.qstate.qrepr))
            print("Qstate: "+str(qubit_entangled.qstate.qubits))
            """
            fidelity = ns.qubits.qubitapi.fidelity(qubit_entangled, reference_state=ns.qubits.ketstates.s1, squared=True)
            print("Fidelity: "+str(fidelity))

            self.send_signal(self.STOP_SIGNAL, result=None)