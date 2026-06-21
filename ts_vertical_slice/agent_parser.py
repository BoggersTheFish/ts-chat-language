"""Closed deterministic Habitat v3 language parser."""

from __future__ import annotations

import re
from dataclasses import asdict, dataclass
from typing import Any

from ts_reasoner.typed_support import canonical_hash
from ts_lang.meaning_graph import semantic_slug


@dataclass(frozen=True)
class AgentDirective:
    directive_id: str
    kind: str
    data: dict[str, Any]
    rule_id: str
    original_span: str
    source_ids: tuple[str, ...]
    provenance_ids: tuple[str, ...]

    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class AgentParseResult:
    directives: tuple[AgentDirective, ...]
    warnings: tuple[str, ...]
    status: str

    def to_dict(self) -> dict[str, Any]:
        return {"directives":[item.to_dict() for item in self.directives],"warnings":self.warnings,"status":self.status}


def entity(value: str) -> str:
    return semantic_slug(re.sub(r"^(?:the|a|an)\s+", "", value.strip(), flags=re.I))


def sentences(text: str) -> list[str]:
    return [item.strip() for item in re.split(r"(?<=[.!?])\s+|\n+", text.strip()) if item.strip()]


def parse_agent_text(text: str) -> AgentParseResult:
    directives=[];warnings=[]
    def add(kind:str,data:dict[str,Any],rule:str,span:str)->None:
        stable={"kind":kind,"data":data,"rule":rule,"span":span.strip()};identity="directive:"+canonical_hash(stable)[:20];provenance="provenance:"+canonical_hash({"directive":identity,"span":span})[:20]
        directives.append(AgentDirective(identity,kind,data,rule,span,(identity,),(provenance,)))
    for sentence in sentences(text):
        plain=sentence.rstrip(".?!").strip();m=None
        # Goal lifecycle and inspection grammar.
        m=re.fullmatch(r"Goal:\s*(?:Open|Close|Activate|Deactivate)\s+(?:the\s+)?(.+)",plain,re.I)
        if m:
            verb=re.search(r"Goal:\s*(\w+)",plain,re.I).group(1).lower();predicate="open" if verb in {"open","close"} else "active";polarity="negative" if verb in {"close","deactivate"} else "positive"
            add("goal",{"owner_agent_id":"alice","predicate":predicate,"subject_id":entity(m.group(1)),"object_id":"","desired_polarity":polarity,"priority":100},"agent.goal.imperative",sentence);continue
        m=re.fullmatch(r"Goal:\s*Move\s+([A-Z][\w-]*)\s+to\s+(?:the\s+)?(.+)",plain)
        if m:
            add("goal",{"owner_agent_id":entity(m.group(1)),"predicate":"at","subject_id":entity(m.group(1)),"object_id":entity(m.group(2)),"desired_polarity":"positive","priority":100},"agent.goal.move",sentence);continue
        m=re.fullmatch(r"([A-Z][\w-]*)\s+(?:wants|must)\s+(?:the\s+)?(.+?)\s+(open|closed|active|inactive)",plain,re.I)
        if m:
            state=m.group(3).lower();predicate="open" if state in {"open","closed"} else "active";polarity="negative" if state in {"closed","inactive"} else "positive"
            add("goal",{"owner_agent_id":entity(m.group(1)),"predicate":predicate,"subject_id":entity(m.group(2)),"object_id":"","desired_polarity":polarity,"priority":100},"agent.goal.want_state",sentence);continue
        m=re.fullmatch(r"([A-Z][\w-]*)\s+must\s+get\s+(?:the\s+)?(.+)",plain)
        if m:
            add("goal",{"owner_agent_id":entity(m.group(1)),"predicate":"carries","subject_id":entity(m.group(1)),"object_id":entity(m.group(2)),"desired_polarity":"positive","priority":100},"agent.goal.acquire",sentence);continue
        m=re.fullmatch(r"Make sure\s+(?:the\s+)?(.+?)\s+is\s+(active|open|closed|inactive)",plain,re.I)
        if m:
            state=m.group(2).lower();add("goal",{"owner_agent_id":"alice","predicate":"open" if state in {"open","closed"} else "active","subject_id":entity(m.group(1)),"object_id":"","desired_polarity":"negative" if state in {"closed","inactive"} else "positive","priority":100},"agent.goal.ensure",sentence);continue
        m=re.fullmatch(r"Stop trying to\s+(open|close)\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("goal_command",{"operation":"abandon","predicate":"open","subject_id":entity(m.group(2))},"agent.goal.abandon",sentence);continue
        m=re.fullmatch(r"(Pause|Resume)\s+(?:the\s+)?(.+?)\s+goal",plain,re.I)
        if m:add("goal_command",{"operation":m.group(1).lower(),"subject_id":entity(m.group(2))},"agent.goal.pause_resume",sentence);continue
        if re.fullmatch(r"Which goal is active",plain,re.I):add("query",{"kind":"active_goal"},"agent.query.goal",sentence);continue
        if re.fullmatch(r"Why is the goal blocked",plain,re.I):add("query",{"kind":"blocked_goal"},"agent.query.blocked",sentence);continue

        # Explicit topology; no other rule creates an edge.
        m=re.fullmatch(r"(?:The\s+)?(.+?)\s+does not connect to\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("connection",{"source":entity(m.group(1)),"destination":entity(m.group(2)),"direction":"bidirectional","status":"BLOCKED"},"topology.negative",sentence);continue
        m=re.fullmatch(r"(?:The\s+)?(.+?)\s+connects one-way to\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("connection",{"source":entity(m.group(1)),"destination":entity(m.group(2)),"direction":"directed","status":"OPEN"},"topology.directed",sentence);continue
        m=re.fullmatch(r"(?:The\s+)?(.+?)\s+connects to\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("connection",{"source":entity(m.group(1)),"destination":entity(m.group(2)),"direction":"bidirectional","status":"OPEN"},"topology.bidirectional",sentence);continue
        m=re.fullmatch(r"(?:The\s+)?(.+?)\s+connects\s+(?:the\s+)?(.+?)\s+to\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("connection",{"name":entity(m.group(1)),"source":entity(m.group(2)),"destination":entity(m.group(3)),"direction":"bidirectional","status":"OPEN"},"topology.named",sentence);continue
        m=re.fullmatch(r"(?:The\s+)?(?:passage|route)\s+from\s+(?:the\s+)?(.+?)\s+to\s+(?:the\s+)?(.+?)\s+is\s+(open|blocked|locked|unknown)",plain,re.I)
        if m:add("connection",{"source":entity(m.group(1)),"destination":entity(m.group(2)),"direction":"bidirectional","status":m.group(3).upper()},"topology.status",sentence);continue

        # Scheduled exogenous events.
        m=re.fullmatch(r"After\s+([A-Z][\w-]*)\s+enters\s+(?:the\s+)?(.+?),\s*([A-Z][\w-]*)\s+takes\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("scheduled_event",{"trigger":"after_enter","trigger_value":entity(m.group(2)),"actor":entity(m.group(3)),"action":"take","object":entity(m.group(4))},"environment.after_enter",sentence);continue
        m=re.fullmatch(r"After\s+(\d+|one|two)\s+agent steps?,\s*(?:the\s+)?(.+?)-to-(.+?)\s+route becomes\s+(blocked|open|locked)",plain,re.I)
        if m:
            count={"one":"1","two":"2"}.get(m.group(1).lower(),m.group(1));add("scheduled_event",{"trigger":"after_step","trigger_value":count,"action":"connection_status","source":entity(m.group(2)),"destination":entity(m.group(3)),"status":m.group(4).upper()},"environment.after_steps",sentence);continue
        m=re.fullmatch(r"Before\s+([A-Z][\w-]*)\s+unlocks\s+(?:the\s+)?(.+?),\s*([A-Z][\w-]*)\s+moves\s+(?:the\s+)?(.+?)\s+into\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("scheduled_event",{"trigger":"before_action_type","trigger_value":"unlock","actor":entity(m.group(3)),"action":"move_object","object":entity(m.group(4)),"destination":entity(m.group(5))},"environment.before_unlock",sentence);continue

        # Social constraints and world observations.
        m=re.fullmatch(r"([A-Z][\w-]*)\s+allows\s+([A-Z][\w-]*)\s+to use\s+(?:the\s+)?(.+)",plain)
        if m:add("fact",{"subject":entity(m.group(1)),"predicate":"allows_use","object":entity(m.group(2))+"@"+entity(m.group(3)),"polarity":"positive"},"social.permission",sentence);continue
        m=re.fullmatch(r"([A-Z][\w-]*)\s+is not allowed to take\s+([A-Z][\w-]*)'?s\s+(.+)",plain)
        if m:add("fact",{"subject":entity(m.group(1)),"predicate":"allowed_take","object":entity(m.group(2))+"@"+entity(m.group(3)),"polarity":"negative"},"social.prohibition",sentence);continue
        m=re.fullmatch(r"([A-Z][\w-]*)\s+(owns|carries)\s+(?:the\s+)?(.+)",plain)
        if m:add("fact",{"subject":entity(m.group(1)),"predicate":m.group(2).lower(),"object":entity(m.group(3)),"polarity":"positive"},"world.possession",sentence);continue
        m=re.fullmatch(r"(?:The\s+)?(.+?)\s+unlocks\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("fact",{"subject":entity(m.group(1)),"predicate":"unlocks","object":entity(m.group(2)),"polarity":"positive"},"world.compatibility",sentence);continue
        m=re.fullmatch(r"(?:The\s+)?(.+?)\s+is\s+(open|closed|locked|unlocked|active|inactive)",plain,re.I)
        if m:
            state=m.group(2).lower();predicate="open" if state in {"open","closed"} else "locked" if state in {"locked","unlocked"} else "active";polarity="negative" if state in {"closed","unlocked","inactive"} else "positive"
            add("fact",{"subject":entity(m.group(1)),"predicate":predicate,"object":"","polarity":polarity},"world.state",sentence);continue
        m=re.fullmatch(r"([A-Z][\w-]*)\s+is\s+(?:in|at)\s+(?:the\s+)?(.+)",plain)
        if m:add("fact",{"subject":entity(m.group(1)),"predicate":"at","object":entity(m.group(2)),"polarity":"positive"},"world.agent_location",sentence);continue
        m=re.fullmatch(r"(?:The\s+)?(.+?)\s+is\s+(?:in|at)\s+(?:the\s+)?(.+)",plain,re.I)
        if m:add("fact",{"subject":entity(m.group(1)),"predicate":"at","object":entity(m.group(2)),"polarity":"positive"},"world.object_location",sentence);continue
        warnings.append("unsupported_agent_sentence:"+sentence)
    return AgentParseResult(tuple(directives),tuple(warnings),"ok" if directives and not warnings else "partial" if directives else "unsupported")
