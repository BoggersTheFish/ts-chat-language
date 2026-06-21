"""Signed semantic ledger and deterministic query-cluster activation for Habitat v2."""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable

from ts_reasoner.habitat import proposition_key
from ts_reasoner.typed_support import canonical_hash
from ts_lang.meaning_graph import MeaningGraph


def semantic_id(kind: str, subject: str = "", predicate: str = "", object_id: str = "", polarity: str = "positive", operands: Iterable[str] = ()) -> str:
    payload={"kind":kind,"subject":subject,"predicate":predicate,"object":object_id,"polarity":polarity,"operands":list(operands)}
    return f"sem_{kind}_{canonical_hash(payload)[:16]}"


@dataclass(frozen=True)
class SemanticObservation:
    provenance_id: str
    turn_index: int
    source_node_id: str
    original_span: str
    rule_id: str


@dataclass
class SemanticItem:
    semantic_id: str
    kind: str
    subject_id: str = ""
    predicate: str = ""
    object_id: str = ""
    polarity: str = "positive"
    status: str = "unknown"
    first_seen_turn: int = 0
    last_seen_turn: int = 0
    observation_count: int = 0
    provenance_ids: list[str] = field(default_factory=list)
    active: bool = True
    operands: tuple[str, ...] = ()
    consequent: str = ""
    origin: str = "user_premise"
    observations: list[SemanticObservation] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]: return asdict(self)


@dataclass(frozen=True)
class ClusterActivation:
    seed_ids: tuple[str, ...]
    activated_semantic_ids: tuple[str, ...]
    dormant_semantic_ids: tuple[str, ...]
    activation_edges: tuple[dict[str, Any], ...]
    max_depth: int = 4
    truncated: bool = False

    def to_dict(self): return asdict(self)


@dataclass(frozen=True)
class StagedHabitat:
    items: tuple[SemanticItem, ...]
    query: dict[str, str]
    events: tuple[dict[str, Any], ...]
    ambiguities: tuple[dict[str, Any], ...]


class SemanticMemory:
    def __init__(self) -> None:
        self.items: dict[str, SemanticItem] = {}
        self.observations: dict[str, SemanticObservation] = {}
        self.latest_activation = ClusterActivation((),(),(),())
        self.latest_plan: dict[str, Any] = {}
        self.transitions: list[dict[str, Any]] = []

    @property
    def hash(self) -> str:
        return canonical_hash({key:item.to_dict() for key,item in sorted(self.items.items())})

    def to_dict(self) -> dict[str, Any]:
        return {key:item.to_dict() for key,item in sorted(self.items.items())}

    def conflicts(self) -> list[str]:
        groups: dict[str,set[str]]={}
        for item in self.items.values():
            if item.active and item.kind in {"fact","event_effect"}: groups.setdefault(proposition_key(item.subject_id,item.predicate,item.object_id),set()).add(item.polarity)
        return sorted(key for key,polarities in groups.items() if polarities=={"positive","negative"})

    def stage(self, graph: MeaningGraph, turn_index: int) -> StagedHabitat:
        items=[]; query={}; events=[]; ambiguities=[]
        for node in graph.nodes:
            slots=node.slots; prov=node.provenance
            observation=SemanticObservation(
                f"obs_{turn_index:04d}_{canonical_hash({'node':node.node_id,'span':prov.get('original_span','')})[:12]}",
                turn_index,node.node_id,str(prov.get("original_span","")),str(prov.get("rule_id","")),
            )
            if node.kind == "world_fact":
                sid=semantic_id("fact",slots["subject"],slots["predicate"],slots.get("object",""),slots.get("polarity","positive"))
                items.append(self._new_item(sid,"fact",slots,observation))
            elif node.kind == "relation_fact":
                translated={"subject":slots["subject"],"predicate":slots["predicate"],"object":slots.get("object",""),"polarity":slots.get("polarity","positive")}
                sid=semantic_id("fact",translated["subject"],translated["predicate"],translated["object"],translated["polarity"])
                items.append(self._new_item(sid,"fact",translated,observation))
            elif node.kind == "causal_rule":
                operands=tuple(slots["antecedents"]); consequent=str(slots["consequent"])
                sid=semantic_id("rule",operands=(*operands,consequent))
                item=self._new_item(sid,"rule",slots,observation); item.operands=operands; item.consequent=consequent; items.append(item)
            elif node.kind == "action_compatibility":
                sid=semantic_id("fact",slots["subject"],"unlocks",slots["object"])
                items.append(self._new_item(sid,"fact",{"subject":slots["subject"],"predicate":"unlocks","object":slots["object"],"polarity":"positive"},observation))
            elif node.kind == "world_event":
                event=self._event(node.node_id,slots,observation,turn_index); events.append(event)
                for effect in event["effects"]:
                    sid=semantic_id("event_effect",effect["subject_id"],effect["predicate"],effect.get("object_id",""),effect.get("polarity","positive"))
                    effect_slots={"subject":effect["subject_id"],"predicate":effect["predicate"],"object":effect.get("object_id",""),"polarity":effect.get("polarity","positive")}
                    item=self._new_item(sid,"event_effect",effect_slots,observation); item.origin="event_effect"; items.append(item)
            elif node.kind == "world_query": query={key:str(value) for key,value in slots.items()}
            elif node.kind == "ambiguity": ambiguities.append(dict(slots))
        if not query: query={"kind":"record"}
        return StagedHabitat(tuple(items),query,tuple(events),tuple(ambiguities))

    def _new_item(self,sid,kind,slots,observation):
        return SemanticItem(sid,kind,str(slots.get("subject","")),str(slots.get("predicate","")),str(slots.get("object","")),str(slots.get("polarity","positive")),"unknown",observation.turn_index,observation.turn_index,1,[observation.provenance_id],True,origin="user_premise",observations=[observation])

    def _event(self,node_id,slots,observation,turn_index):
        actor=str(slots.get("actor","")); action=str(slots["action"]); target=str(slots.get("target","")); obj=str(slots.get("object","")); destination=str(slots.get("destination",""))
        effects=[]; preconditions=[]; supersedes=[]
        if action in {"opens","closes","locks","unlocks"}:
            predicate="open" if action in {"opens","closes"} else "locked"; polarity="positive" if action in {"opens","locks"} else "negative"
            effects.append({"subject_id":target,"predicate":predicate,"object_id":"","polarity":polarity}); supersedes.append(proposition_key(target,predicate,""))
        elif action == "gives":
            preconditions.append({"subject_id":actor,"predicate":"owns","object_id":obj,"polarity":"positive"})
            effects.extend(({"subject_id":actor,"predicate":"owns","object_id":obj,"polarity":"negative"},{"subject_id":target,"predicate":"owns","object_id":obj,"polarity":"positive"})); supersedes.append(f"*|owns|{obj}")
        elif action == "takes": effects.append({"subject_id":actor,"predicate":"carries","object_id":obj or target,"polarity":"positive"})
        elif action == "moves": effects.append({"subject_id":actor,"predicate":"at","object_id":destination,"polarity":"positive"}); supersedes.append(f"{actor}|at|*")
        elif action == "puts": effects.append({"subject_id":obj,"predicate":"inside","object_id":target,"polarity":"positive"}); supersedes.append(f"{obj}|inside|*")
        elif action == "removes": effects.append({"subject_id":obj,"predicate":"inside","object_id":target,"polarity":"negative"})
        return {"event_id":semantic_id("event",actor,action,target,operands=(obj,destination,str(turn_index))),"actor_id":actor,"action":action,"target_id":target,"object_id":obj,"destination_location_id":destination,"turn_index":turn_index,"preconditions":preconditions,"effects":effects,"supersedes":supersedes,"source_ids":[observation.provenance_id]}

    def merge_preview(self, staged: StagedHabitat) -> dict[str, Any]:
        merged=[]; new=[]
        for item in staged.items:
            (merged if item.semantic_id in self.items else new).append(item.semantic_id)
        return {"merged_semantic_ids":sorted(merged),"new_semantic_ids":sorted(new),"observation_ids":sorted(obs.provenance_id for item in staged.items for obs in item.observations),"staged_count":len(staged.items)}

    def commit(self, staged: StagedHabitat, approved_ids: Iterable[str]) -> dict[str, Any]:
        approved=set(approved_ids); before=self.hash; added=[]; merged=[]; superseded=[]
        for event in staged.events:
            if not any(semantic_id("event_effect",e["subject_id"],e["predicate"],e.get("object_id",""),e.get("polarity","positive")) in approved for e in event["effects"]): continue
            for pattern in event["supersedes"]:
                a,p,o=pattern.split("|",2)
                for existing in self.items.values():
                    if not existing.active or existing.kind not in {"fact","event_effect"}: continue
                    if (a=="*" or existing.subject_id==a) and existing.predicate==p and (o=="*" or existing.object_id==o):
                        existing.active=False; superseded.append(existing.semantic_id)
            self.transitions.append(event)
        for incoming in sorted(staged.items,key=lambda item:item.semantic_id):
            if incoming.semantic_id not in approved: continue
            if incoming.semantic_id in self.items:
                existing=self.items[incoming.semantic_id]; existing.last_seen_turn=max(existing.last_seen_turn,incoming.last_seen_turn); existing.observation_count+=incoming.observation_count; existing.active=True
                for obs in incoming.observations:
                    if obs.provenance_id not in existing.provenance_ids: existing.provenance_ids.append(obs.provenance_id); existing.observations.append(obs); self.observations[obs.provenance_id]=obs
                existing.provenance_ids.sort(); existing.observations.sort(key=lambda x:x.provenance_id); merged.append(existing.semantic_id)
            else:
                self.items[incoming.semantic_id]=incoming
                for obs in incoming.observations:self.observations[obs.provenance_id]=obs
                added.append(incoming.semantic_id)
        self._refresh_statuses()
        return {"before_state_hash":before,"after_state_hash":self.hash,"added_semantic_ids":added,"merged_semantic_ids":merged,"superseded_semantic_ids":sorted(set(superseded)),"committed":bool(added or merged or superseded)}

    def _refresh_statuses(self) -> None:
        groups: dict[str,set[str]]={}
        for item in self.items.values():
            if item.active and item.kind in {"fact","event_effect"}: groups.setdefault(proposition_key(item.subject_id,item.predicate,item.object_id),set()).add(item.polarity)
        for item in self.items.values():
            if not item.active: item.status="superseded"; continue
            if item.kind not in {"fact","event_effect"}: item.status="supported_true"; continue
            polarities=groups.get(proposition_key(item.subject_id,item.predicate,item.object_id),set())
            item.status="conflicted" if polarities=={"positive","negative"} else "supported_true" if item.polarity=="positive" else "supported_false"

    def activate(self, staged: StagedHabitat, *, max_depth: int = 4) -> ClusterActivation:
        combined={**self.items,**{item.semantic_id:item for item in staged.items}}
        query=staged.query
        seeds={value for key,value in query.items() if key in {"subject_id","predicate","object_id"} and value}
        def links(item):
            values=set(item.operands)|({item.consequent} if item.consequent else set())|{item.subject_id,item.predicate,item.object_id}
            if item.kind in {"fact","event_effect"}: values.add(proposition_key(item.subject_id,item.predicate,item.object_id))
            return {value for value in values if value}
        activated=set(); edges=[]; frontier=[]
        for sid,item in sorted(combined.items()):
            tokens=links(item)
            if seeds & tokens or any(seed and seed in token.split("|") for seed in seeds for token in tokens): activated.add(sid);frontier.append((sid,0,"query_seed"))
        if staged.query.get("kind")=="record":
            for item in staged.items:
                activated.add(item.semantic_id); frontier.append((item.semantic_id,0,"current_turn"))
        while frontier:
            sid,depth,reason=frontier.pop(0)
            if depth>=max_depth: continue
            item=combined[sid]; item_links=links(item)
            for other_id,other in sorted(combined.items()):
                if other_id in activated: continue
                other_links=links(other)
                shared=sorted(item_links&other_links)
                if shared:
                    activated.add(other_id); frontier.append((other_id,depth+1,"shared:"+shared[0])); edges.append({"from":sid,"to":other_id,"reason":"shared:"+shared[0],"depth":depth+1})
        dormant=sorted(sid for sid,item in combined.items() if item.active and sid not in activated)
        result=ClusterActivation(tuple(sorted(seeds)),tuple(sorted(activated)),tuple(dormant),tuple(edges),max_depth,False)
        self.latest_activation=result; return result

    def payload(self, staged: StagedHabitat, activation: ClusterActivation) -> dict[str, Any]:
        combined={**self.items,**{item.semantic_id:item for item in staged.items}}
        active=[combined[sid] for sid in activation.activated_semantic_ids if sid in combined and combined[sid].active]
        facts=[];rules=[]
        for item in active:
            if item.kind in {"fact","event_effect"}: facts.append({"semantic_id":item.semantic_id,"subject_id":item.subject_id,"predicate":item.predicate,"object_id":item.object_id,"polarity":item.polarity,"source_ids":tuple(item.provenance_ids),"origin":item.origin,"active":item.active})
            elif item.kind=="rule": rules.append({"semantic_id":item.semantic_id,"antecedents":item.operands,"consequent":item.consequent,"source_ids":tuple(item.provenance_ids)})
        return {"facts":facts,"rules":rules,"events":list(staged.events),"query":dict(staged.query),"activation":activation.to_dict(),"memory_candidate_ids":[item.semantic_id for item in staged.items],"max_inference_depth":4,"max_derived_facts":64,"max_plan_depth":8}
