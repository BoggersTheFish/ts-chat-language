import unittest
from pathlib import Path

from ts_reasoner.agent_control import GoalStatus
from ts_vertical_slice.agent_parser import parse_agent_text
from ts_vertical_slice.agent_session import HabitatV3Session
from ts_vertical_slice.receipt_v3 import REQUIRED_SECTIONS, write_v3_receipt
from ts_reasoner.agent_runtime import AgentLimits


class HabitatV3LanguageTests(unittest.TestCase):
    def session(self): return HabitatV3Session("/tmp/habitat_v3_tests")

    def load(self, session, rows):
        for row in rows: session.handle(row, save=False)

    def test_topology_goal_and_event_grammar(self):
        parsed=parse_agent_text("The hall connects to the kitchen. The passage from the kitchen to the cellar is blocked. Goal: Open the north door. After two agent steps, the hall-to-kitchen route becomes blocked.")
        self.assertEqual(parsed.status,"ok")
        self.assertEqual([item.kind for item in parsed.directives],["connection","connection","goal","scheduled_event"])

    def test_demo_one_completes_with_receipt_v3(self):
        session=self.session();self.load(session,[
            "Alice is in the hall.","The hall connects to the kitchen.","The kitchen connects to the north door.",
            "The red key is in the kitchen.","The red key unlocks the north door.","The north door is locked.","Goal: Open the north door.",
        ])
        receipt=session.run(20,save=False)
        self.assertEqual(receipt["receipt_schema"],"ts-turn-receipt-v3")
        self.assertTrue(all(key in receipt for key in REQUIRED_SECTIONS))
        self.assertEqual(receipt["decision"]["subtype"],"COMPLETE")
        self.assertTrue(receipt["replay"]["final_run_replay_hash"])

    def test_blocked_direct_route_uses_indirect_route(self):
        session=self.session();self.load(session,["The hall connects to the kitchen.","The kitchen connects to the garden.","The hall does not connect to the garden.","Alice is in the hall.","Goal: Move Alice to the garden."])
        receipt=session.run(10,save=False)
        moves=[row for row in receipt["action_transactions"] if row["committed"]]
        self.assertEqual(len(moves),2)
        self.assertEqual(receipt["decision"]["subtype"],"COMPLETE")

    def test_conflicted_topology_is_not_traversed(self):
        session=self.session();self.load(session,["The hall connects to the kitchen.","The hall does not connect to the kitchen.","Alice is in the hall.","Goal: Move Alice to the kitchen."])
        receipt=session.run(4,save=False)
        self.assertEqual(receipt["decision"]["subtype"],"UNREACHABLE")
        self.assertFalse(receipt["action_transactions"])

    def test_multiple_goal_priority_is_deterministic(self):
        session=self.session();self.load(session,["Alice is in the hall.","The alarm is inactive.","Goal: Activate the alarm.","Goal: Move Alice to the hall."])
        goals=list(session.goals.goals.values());session.goals.goals[goals[0].goal_id]=goals[0].__class__(**{**goals[0].__dict__,"priority":200})
        receipt=session.run(10,save=False)
        ranked=next(row for row in receipt["agent_loop"]["steps"] if row["phase"]=="SELECT_GOAL")
        self.assertEqual(ranked["selected_goal_id"],goals[0].goal_id)

    def test_goal_pause_resume_abandon_is_verifier_gated(self):
        session=self.session();session.handle("Goal: Open the door.",save=False);identity=next(iter(session.goals.goals))
        self.assertTrue(session.goals.transition(identity,GoalStatus.PAUSED,turn=2).approved)
        self.assertTrue(session.goals.transition(identity,GoalStatus.ACTIVE,turn=3).approved)
        self.assertTrue(session.goals.transition(identity,GoalStatus.ABANDONED,turn=4).approved)

    def test_receipt_size_limit_is_explicit(self):
        session=HabitatV3Session("/tmp/habitat_v3_small_receipt",limits=AgentLimits(max_receipt_size=1));receipt=session.handle("Goal: Activate the alarm.",save=False)
        with self.assertRaisesRegex(OverflowError,"MAX_RECEIPT_SIZE"):write_v3_receipt(receipt,Path("/tmp/habitat_v3_small_receipt"))


if __name__=="__main__":unittest.main()
