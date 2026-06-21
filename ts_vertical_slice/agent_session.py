"""Habitat v3 language-to-agent session with explicit execution controls."""

from __future__ import annotations

from dataclasses import asdict, replace
from pathlib import Path
from typing import Any

from ts_reasoner.agent_control import Goal, GoalStatus, GoalStore, goal_id
from ts_reasoner.agent_runtime import (
    AgentLimits, AgentState, Effect, EnvironmentEvent, EnvironmentSnapshot,
    HabitatAgentLoop, SymbolicEnvironment,
)
from ts_reasoner.habitat import WorldFact
from ts_reasoner.topology import Connection, ConnectionEvidence, ConnectionStatus, connection_id
from ts_reasoner.typed_support import canonical_hash

from .agent_parser import AgentDirective, parse_agent_text
from .receipt_v3 import build_v3_receipt, write_v3_receipt


class HabitatV3Session:
    def __init__(self,artifact_dir:str|Path="artifacts/habitat_v3/receipts",*,limits:AgentLimits|None=None,repository_shas:dict[str,str]|None=None)->None:
        self.artifact_dir=Path(artifact_dir);self.limits=limits or AgentLimits();self.repository_shas=repository_shas or {"ts-reasoner-v0":"development","ts-chat-language":"development"}
        self.goals=GoalStore(max_goals=self.limits.max_active_goals);self.facts:dict[str,WorldFact]={};self.topology:dict[str,Connection]={};self.agents:dict[str,AgentState]={};self.events:dict[str,EnvironmentEvent]={}
        self.environment=SymbolicEnvironment(EnvironmentSnapshot((),(),(),0,(),()),limits=self.limits);self.loop:HabitatAgentLoop|None=None;self.turn=0;self.input_sequence=[];self.receipts=[];self.last_path=None;self.lesson_receipts=[]
        self.last_merge={};self.last_decision={"status":"IDLE"};self.last_rendering={"text":"","support_ids":[]};self.last_memory_update={"committed":False}

    def reset(self)->str:
        self.__init__(self.artifact_dir,limits=self.limits,repository_shas=self.repository_shas);return canonical_hash(self.environment.snapshot().__dict__)

    def handle(self,text:str,*,save:bool=True)->dict[str,Any]:
        self.turn+=1;self.input_sequence.append(text);parsed=parse_agent_text(text);added=[];merged=[];goal_receipts=[]
        for directive in parsed.directives:
            if directive.kind=="fact":
                row=directive.data;fact=WorldFact("fact:"+canonical_hash({"directive":directive.directive_id,"data":row})[:20],row["subject"],row["predicate"],row.get("object",""),row.get("polarity","positive"),directive.source_ids+directive.provenance_ids,"user_observation",True)
                (merged if fact.semantic_id in self.facts else added).append(fact.semantic_id);self.facts[fact.semantic_id]=fact;self._ensure_agent(row["subject"],row)
            elif directive.kind=="connection":self._add_connection(directive,added,merged)
            elif directive.kind=="goal":goal_receipts.extend(self._add_goal(directive))
            elif directive.kind=="goal_command":goal_receipts.append(self._goal_command(directive))
            elif directive.kind=="scheduled_event":self._add_event(directive)
        self.last_merge={"new_semantic_ids":sorted(added),"merged_semantic_ids":sorted(merged),"goal_verification_ids":[item.verification_id for item in goal_receipts],"committed_to_environment":bool(added or merged),"trusted_world_committed":False}
        self._refresh_environment()
        query=next((item for item in parsed.directives if item.kind=="query"),None)
        if query:self._answer_query(query)
        else:
            support=tuple(sorted({sid for item in parsed.directives for sid in item.source_ids}));self.last_decision={"status":"ACCEPT" if parsed.directives else "REPAIR","subtype":"ENVIRONMENT_OBSERVATION_STAGED" if parsed.directives else "UNSUPPORTED_GRAMMAR","support_ids":support};self.last_rendering={"text":"Staged for verifier observation." if parsed.directives else "The input is outside the bounded Habitat v3 grammar.","support_ids":support,"support_validated":bool(parsed.directives)}
        self.last_memory_update={"environment_changed":bool(added or merged),"trusted_world_changed":False,"triggering_input":text,"previous_state_hash":"","resulting_state_hash":self.environment.observe().state_hash,"support_ids":tuple(sorted({sid for item in parsed.directives for sid in item.source_ids}))}
        receipt=build_v3_receipt(turn={"turn_id":f"turn:{self.turn:04d}","input":text},parse=parsed.to_dict(),session=self);self.receipts.append(receipt)
        if save:self.last_path=write_v3_receipt(receipt,self.artifact_dir)
        return receipt

    def _ensure_agent(self,subject:str,row:dict[str,Any])->None:
        if row.get("predicate")=="at" and subject in {g.owner_agent_id for g in self.goals.goals.values()}|{"alice","bob","sarah"}:
            current=self.agents.get(subject,AgentState(subject,subject.title()));self.agents[subject]=replace(current,current_location_id=row.get("object",""))

    def _add_connection(self,directive:AgentDirective,added:list[str],merged:list[str])->None:
        row=directive.data;identity=connection_id(row["source"],row["destination"],row["direction"],row.get("name",""));evidence=ConnectionEvidence("connection_evidence:"+directive.directive_id.split(":")[-1],ConnectionStatus(row["status"]),directive.source_ids,directive.provenance_ids)
        incoming=Connection(identity,row["source"],row["destination"],row["direction"],ConnectionStatus(row["status"]),source_ids=directive.source_ids,provenance_ids=directive.provenance_ids,evidence=(evidence,));temp=self._topology_object();exists=identity in temp.connections;merged_edge=temp.merge(incoming);self.topology[identity]=merged_edge;(merged if exists else added).append(identity)

    def _topology_object(self):
        from ts_reasoner.topology import SpatialTopology
        value=SpatialTopology(max_connections=self.limits.max_topology_size)
        for edge in self.topology.values():value.merge(edge)
        return value

    def _add_goal(self,directive:AgentDirective):
        row=directive.data;owner=row["owner_agent_id"];identity=goal_id(owner,row["predicate"],row["subject_id"],row.get("object_id",""),row.get("desired_polarity","positive"));goal=Goal(identity,owner,"state_goal",row["predicate"],row["subject_id"],row.get("object_id",""),row.get("desired_polarity","positive"),GoalStatus.PROPOSED,int(row.get("priority",100)),self.turn,self.turn,source_ids=directive.source_ids,provenance_ids=directive.provenance_ids)
        proposed=self.goals.propose(goal);activated=self.goals.transition(identity,GoalStatus.ACTIVE,turn=self.turn) if proposed.approved and self.goals.goals[identity].status==GoalStatus.PROPOSED else proposed
        self.agents.setdefault(owner,AgentState(owner,owner.title()));return proposed,activated

    def _goal_command(self,directive:AgentDirective):
        row=directive.data;goal=next((g for g in self.goals.goals.values() if g.subject_id==row["subject_id"]),None)
        if not goal:raise KeyError("GOAL_NOT_FOUND")
        target={"pause":GoalStatus.PAUSED,"resume":GoalStatus.ACTIVE,"abandon":GoalStatus.ABANDONED}[row["operation"]];return self.goals.transition(goal.goal_id,target,turn=self.turn)

    def _add_event(self,directive:AgentDirective)->None:
        row=directive.data;effects=[];cid="";status="";actor=row.get("actor","")
        if row["action"]=="take":
            obj=row["object"];location=next((fact for fact in self.facts.values() if fact.subject_id==obj and fact.predicate in {"at","inside"} and fact.polarity=="positive"),None)
            if location:effects.append(Effect(obj,location.predicate,location.object_id,"negative"))
            effects.append(Effect(actor,"carries",obj))
        elif row["action"]=="move_object":
            obj=row["object"];location=next((fact for fact in self.facts.values() if fact.subject_id==obj and fact.predicate in {"at","inside"} and fact.polarity=="positive"),None)
            if location:effects.append(Effect(obj,location.predicate,location.object_id,"negative"))
            effects.append(Effect(obj,"at",row["destination"]))
        elif row["action"]=="connection_status":cid=connection_id(row["source"],row["destination"]);status=row["status"]
        event=EnvironmentEvent("event:"+directive.directive_id.split(":")[-1],row["trigger"],row["trigger_value"],tuple(effects),cid,status,directive.source_ids,directive.provenance_ids,actor);self.events[event.event_id]=event

    def _refresh_environment(self)->None:
        old=self.environment.snapshot();snapshot=EnvironmentSnapshot(tuple(self.facts.values()),tuple(self.topology.values()),tuple(self.agents.values()),old.step,tuple(self.events.values()),old.fired_event_ids,old.forced_mismatch_action_types);self.environment.restore_for_replay(snapshot)
        if self.loop is None or (self.loop.iterations==0 and not self.loop.run.action_transactions):
            self.loop=HabitatAgentLoop(self.environment,self.goals,limits=self.limits,repository_shas=self.repository_shas)

    def _answer_query(self,directive:AgentDirective)->None:
        if directive.data["kind"]=="active_goal":goals=[g.goal_id for g in self.goals.goals.values() if g.status==GoalStatus.ACTIVE];text=goals[0] if goals else "No goal is active."
        else:
            goals=[g for g in self.goals.goals.values() if g.status in {GoalStatus.BLOCKED,GoalStatus.UNREACHABLE,GoalStatus.CONFLICTED}];text=(goals[0].status.value+": "+goals[0].goal_id) if goals else "No goal is blocked."
        self.last_decision={"status":"ACCEPT","subtype":"GOAL_QUERY","support_ids":directive.source_ids};self.last_rendering={"text":text,"support_ids":directive.source_ids,"support_validated":True}

    def step(self,*,save:bool=True)->dict[str,Any]:
        self.turn+=1;result=self.loop.step();self.input_sequence.append("/step");self._set_run_render(result);return self._execution_receipt("/step",save)

    def run(self,max_steps:int|None=None,*,save:bool=True)->dict[str,Any]:
        self.turn+=1;result=self.loop.run_bounded(max_steps);self.input_sequence.append(f"/run {max_steps or ''}".strip());self._set_run_render(result);return self._execution_receipt("/run",save)

    def replan(self)->None:
        if self.loop.current_plan:
            goal=self.goals.goals[self.loop.current_plan.goal_id];self.loop._invalidate("WORLD_CHANGED",goal)

    def _set_run_render(self,result:str)->None:
        terminal=result in {"COMPLETE","UNREACHABLE","BLOCKED","BUDGET_EXHAUSTED","ERROR"};support=tuple(sorted({sid for row in self.loop.run.action_transactions if row["committed"] for sid in row["support_ids"]}));status="ACCEPT" if result=="COMPLETE" else "REJECT" if terminal else "ACCEPT";self.last_decision={"status":status,"subtype":result,"support_ids":support,"goal_satisfaction_supported":result!="COMPLETE" or any(g.resolution_support_ids for g in self.goals.goals.values() if g.status==GoalStatus.SATISFIED)}
        text={"COMPLETE":"All active goals are satisfied in the verified world state.","UNREACHABLE":"REJECT_UNREACHABLE: no verified bounded plan exists.","BLOCKED":"The active goal is blocked.","BUDGET_EXHAUSTED":"Execution budget exhausted without claiming success.","ERROR":"The agent loop stopped on a verified error."}.get(result,"One verified agent step completed.");self.last_rendering={"text":text,"support_ids":support,"support_validated":result!="COMPLETE" or self.last_decision["goal_satisfaction_supported"]};self.last_memory_update={"committed_transactions":sum(1 for row in self.loop.run.action_transactions if row["committed"]),"world_state_hash":self.loop.world.hash}

    def _execution_receipt(self,text:str,save:bool)->dict[str,Any]:
        receipt=build_v3_receipt(turn={"turn_id":f"turn:{self.turn:04d}","input":text},parse={"status":"command","directives":[],"warnings":[]},session=self);self.receipts.append(receipt)
        if save:self.last_path=write_v3_receipt(receipt,self.artifact_dir)
        return receipt

    def approve_lesson(self,identity:str)->dict[str,Any]:
        receipt=self.loop.approve_lesson(identity);self.lesson_receipts.append(receipt);return receipt

    def reject_lesson(self,identity:str)->dict[str,Any]:
        receipt=self.loop.reject_lesson(identity);self.lesson_receipts.append(receipt);return receipt

    def force_effect_mismatch(self,action_type:str)->None:
        snapshot=self.environment.snapshot();self.environment.restore_for_replay(replace(snapshot,forced_mismatch_action_types=tuple(sorted(set((*snapshot.forced_mismatch_action_types,action_type))))))

    def clear_effect_mismatch(self,action_type:str)->None:
        snapshot=self.environment.snapshot();self.environment.restore_for_replay(replace(snapshot,forced_mismatch_action_types=tuple(value for value in snapshot.forced_mismatch_action_types if value!=action_type)))
