import json
import tempfile
import unittest

from ts_reasoner.structured_request import ReasoningRequest, StructuredAnswer, VerifierDecision
from ts_vertical_slice.bridge import bridge_meaning_graph
from ts_vertical_slice.parser import parse_to_meaning_graph
from ts_vertical_slice.renderer import render_verified
from ts_vertical_slice.session import VerticalSliceSession


class VerticalSliceTests(unittest.TestCase):
    def session(self): return VerticalSliceSession(tempfile.mkdtemp())

    def test_relational_inference(self):
        r=self.session().handle("Alice is older than Bob. Bob is older than Carol. Who is oldest?")
        self.assertEqual((r.final_status,r.final_response),("ACCEPT","Alice is the oldest."))
        self.assertIn("relation_chain_supported",[x["check_id"] for x in r.verifier_checks])

    def test_boolean_inference(self):
        r=self.session().handle("The alarm activates if the door is open and the system is armed. The door is open. The system is armed. Is the alarm active?")
        self.assertEqual(r.final_response,"The alarm is active.")

    def test_unsupported_inference_rejects(self):
        r=self.session().handle("Alice is an artist. Artists can become wealthy. Is Alice wealthy?")
        self.assertEqual(r.final_status,"REJECT"); self.assertIn("not enough supported",r.final_response)

    def test_ambiguity_needs_user(self):
        r=self.session().handle("Alice gave Sarah her key. Who owns the key?")
        self.assertEqual(r.repair_result,"REPAIR_NEEDS_USER"); self.assertIn("Alice or Sarah",r.final_response)

    def test_plan(self):
        r=self.session().handle("I must verify the backup before deleting the repository. What should happen first?")
        self.assertEqual(r.final_response,"Verify the backup before deleting the repository.")

    def test_direct_relation(self):
        r=self.session().handle("The red key opens the north door. Which door does the red key open?")
        self.assertEqual(r.final_response,"The red key opens the north door.")

    def test_multi_turn_verified_memory(self):
        s=self.session(); s.handle("Alice is older than Bob."); s.handle("Bob is older than Carol."); r=s.handle("Who is oldest?")
        self.assertEqual(r.final_response,"Alice is the oldest."); self.assertEqual(len(s.state.relations),2)

    def test_rejected_claim_does_not_contaminate(self):
        s=self.session(); before=s.state.hash; s.handle("Alice is an artist. Artists can become wealthy. Is Alice wealthy?")
        self.assertEqual(s.state.hash,before); self.assertFalse(s.state.relations)

    def test_ambiguity_does_not_contaminate(self):
        s=self.session(); before=s.state.hash; s.handle("Alice gave Sarah her key. Who owns the key?"); self.assertEqual(s.state.hash,before)

    def test_reset_is_known_empty_state(self):
        s=self.session(); empty=s.state.hash; s.handle("Alice is older than Bob."); self.assertEqual(s.reset(),empty)

    def test_deterministic_replay(self):
        text="Alice is older than Bob. Bob is older than Carol. Who is oldest?"
        a=self.session().handle(text); b=self.session().handle(text)
        self.assertEqual((a.meaning_graph_hash,a.reasoning_request_hash,a.final_response,a.deterministic_replay_hash),(b.meaning_graph_hash,b.reasoning_request_hash,b.final_response,b.deterministic_replay_hash))

    def test_receipt_json_serialises(self):
        r=self.session().handle("The red key opens the north door. Which door does the red key open?")
        self.assertIn("deterministic_replay_hash",json.loads(json.dumps(r.to_dict())))

    def test_bridge_is_stable(self):
        parsed=parse_to_meaning_graph("Alice is older than Bob.")
        a=bridge_meaning_graph(parsed.graph,"Alice is older than Bob."); b=bridge_meaning_graph(parsed.graph,"Alice is older than Bob.")
        self.assertEqual(a.request.canonical_hash,b.request.canonical_hash)

    def test_renderer_blocks_unverified_affirmative(self):
        request=ReasoningRequest("r","x","assert")
        decision=VerifierDecision("ACCEPT","bad",(),StructuredAnswer("recorded"))
        with self.assertRaises(AssertionError): render_verified(decision,request)

    def test_repair_is_bounded(self):
        r=self.session().handle("Alice is older than Bob. Bob is older than Carol. Who is the oldest one?")
        self.assertEqual(r.repair_result,"REPAIR_ACCEPTED"); self.assertEqual(r.final_status,"REPAIR")


if __name__=="__main__": unittest.main()
