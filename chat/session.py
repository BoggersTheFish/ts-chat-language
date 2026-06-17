"""TS-Chat session: one compile-render loop per turn."""

from __future__ import annotations

from ts_lang.compiler import compile_utterance
from ts_lang.graph_diff import diff_meaning_graphs
from ts_lang.types import TurnReceipt
from ts_render.renderer import render_response
from ts_render.response_plan import plan_response
from ts_state.conversation import ConversationState


class TSChatSession:
    def __init__(self) -> None:
        self.state = ConversationState()
        self.last_receipt: TurnReceipt | None = None

    def handle(self, user_text: str) -> TurnReceipt:
        turn = compile_utterance(user_text, self.state)
        next_turn_id = self.state.turn_counter + 1
        graph_diff = diff_meaning_graphs(
            self.state.last_meaning_graph,
            turn.meaning_graph,
            previous_turn_id=self.state.turn_counter if self.state.last_meaning_graph else None,
            current_turn_id=next_turn_id,
        )
        graph_diff_dict = graph_diff.to_dict()

        self.state.apply_compiled_turn(turn, graph_diff=graph_diff_dict)
        plan = plan_response(turn, self.state)
        reply = render_response(plan, self.state)

        receipt = TurnReceipt(
            turn_id=self.state.turn_counter,
            user_text=user_text,
            compiled_turn=turn,
            response_plan=plan,
            rendered_reply=reply,
            state_snapshot=self.state.to_dict(),
            graph_diff=graph_diff,
        )

        self.state.record_turn(
            user_text=user_text,
            bot_text=reply.text,
            compiled_turn=turn,
            response_plan=plan.to_dict(),
            graph_diff=graph_diff_dict,
        )
        self.last_receipt = receipt
        return receipt