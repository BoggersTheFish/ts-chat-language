import json
import tempfile
import unittest

from ts_vertical_slice.habitat import semantic_id
from ts_vertical_slice.session import VerticalSliceSession


class HabitatV2IntegrationTests(unittest.TestCase):
    def session(self): return VerticalSliceSession(tempfile.mkdtemp())

    def test_semantic_merge_retains_observations(self):
        s=self.session();s.handle("The door is open.");s.handle("The door is open.")
        items=[x for x in s.state.world.items.values() if x.subject_id=="door" and x.predicate=="open"]
        self.assertEqual(len(items),1);self.assertEqual(items[0].observation_count,2);self.assertEqual(len(items[0].provenance_ids),2)

    def test_repeated_question_does_not_mutate(self):
        s=self.session();s.handle("The door is open.");s.handle("Is the door open?");before=s.state.hash;s.handle("Is the door open?");self.assertEqual(s.state.hash,before)

    def test_signed_true(self):
        s=self.session();s.handle("The door is open.");r=s.handle("Is the door open?")
        self.assertEqual((r.final_status,r.decision_subtype,r.final_response),("ACCEPT","CONCLUSION_VERIFIED","The door is open."))

    def test_signed_false(self):
        s=self.session();s.handle("The door is not open.");r=s.handle("Is the door open?")
        self.assertEqual(r.final_response,"The door is not open.");self.assertEqual(r.signed_world_state["door|open|"]["status"],"SUPPORTED_FALSE")

    def test_negative_query(self):
        s=self.session();s.handle("The door is not open.");r=s.handle("Is the door not open?");self.assertEqual(r.final_status,"ACCEPT")

    def test_conflict_preserved_and_rejected(self):
        s=self.session();s.handle("The door is open.");s.handle("The door is not open.");r=s.handle("Is the door open?")
        self.assertEqual((r.final_status,r.decision_subtype),("REJECT","REJECT_CONFLICTED"));self.assertEqual(len(s.state.world.conflicts()),1)

    def test_unknown_rejects(self):
        r=self.session().handle("Is the door open?");self.assertEqual((r.final_status,r.decision_subtype),("REJECT","REJECT_UNSUPPORTED"))

    def test_event_supersedes_temporal_state(self):
        s=self.session();s.handle("The door is closed.");event=s.handle("Alice opens the door.");r=s.handle("Is the door open?")
        self.assertEqual(r.final_status,"ACCEPT");self.assertTrue(event.memory_update["superseded_semantic_ids"]);self.assertTrue(event.state_transitions)

    def test_close_event_produces_supported_false(self):
        s=self.session();s.handle("The door is open.");s.handle("Bob closes the door.");r=s.handle("Is the door open?");self.assertEqual(r.response_template,"ACCEPT_SIGNED_FALSE")

    def test_ownership_transfer(self):
        s=self.session();s.handle("Alice owns the red key.");s.handle("Alice gives the red key to Sarah.");r=s.handle("Who owns the red key?")
        self.assertEqual(r.final_response,"Sarah owns the red key.")

    def test_invalid_give_does_not_contaminate(self):
        s=self.session();before=s.state.hash;r=s.handle("Alice gives the red key to Sarah.");self.assertEqual(r.final_status,"REJECT");self.assertEqual(s.state.hash,before)

    def test_location_containment_chain(self):
        s=self.session();s.handle("The key is inside the box.");s.handle("The box is in the kitchen.");r=s.handle("Where is the key?")
        self.assertEqual(r.final_response,"The key is inside the box, and the box is in the kitchen.")

    def test_two_step_causal_chain(self):
        r=self.session().handle("If the door opens, the sensor activates. If the sensor activates and the system is armed, the alarm activates. The door opens. The system is armed. Is the alarm active?")
        self.assertEqual(r.final_status,"ACCEPT");self.assertEqual(len(r.causal_derivations),2);self.assertIn("derived through",r.final_response)

    def test_causal_missing_antecedent_rejects(self):
        r=self.session().handle("If the door opens, the sensor activates. Is the sensor active?");self.assertEqual(r.final_status,"REJECT")

    def test_irrelevant_age_cluster_dormant(self):
        s=self.session();s.handle("Alice is older than Bob.");s.handle("The door is open.");r=s.handle("Is the door open?")
        age=semantic_id("fact","alice","older_than","bob")
        self.assertIn(age,r.cluster_activation["dormant_semantic_ids"]);self.assertNotIn(age,[item["semantic_id"] for item in r.reasoning_request["habitat"]["facts"]])

    def test_plan_verified(self):
        s=self.session()
        for text in ("Alice is in the hall.","The box is in the kitchen.","The red key is inside the box.","The north door is locked.","The red key unlocks the north door."):s.handle(text)
        r=s.handle("How can Alice open the north door?")
        self.assertEqual((r.final_status,r.decision_subtype),("ACCEPT","PLAN_VERIFIED"));self.assertEqual(len(r.planning["chosen_plan"]),5);self.assertTrue(all(all(c["passed"] for c in step["precondition_checks"]) for step in r.planning["chosen_plan"]))

    def test_impossible_plan_rejects(self):
        s=self.session();s.handle("Alice is in the hall.");s.handle("The north door is locked.");r=s.handle("How can Alice open the north door?")
        self.assertEqual((r.final_status,r.decision_subtype),("REJECT","REJECT_UNREACHABLE"))

    def test_receipt_v2_serializes(self):
        r=self.session().handle("The door is open.");payload=json.loads(json.dumps(r.to_dict()))
        self.assertEqual(payload["receipt_schema"],"ts-turn-receipt-v2");self.assertIn("semantic_merge",payload);self.assertIn("cluster_activation",payload)

    def test_replay_is_deterministic(self):
        sequence=("The door is closed.","Alice opens the door.","Is the door open?")
        hashes=[]
        for _ in range(2):
            s=self.session()
            for text in sequence:r=s.handle(text,save=False)
            hashes.append((r.deterministic_replay_hash,s.state.hash))
        self.assertEqual(hashes[0],hashes[1])

    def test_support_ids_are_unique(self):
        s=self.session();s.handle("The door is open.");s.handle("The door is open.");r=s.handle("Is the door open?")
        self.assertTrue(all(len(check["support_ids"])==len(set(check["support_ids"])) for check in r.verifier_checks))


if __name__=="__main__":unittest.main()
