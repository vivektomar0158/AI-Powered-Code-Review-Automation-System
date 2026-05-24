from typing import TypedDict, List, Dict, Any, Annotated
import operator
import asyncio
import logging

from langgraph.graph import StateGraph, END, START

from app.agents.base_agent import CodeContext, Issue
from app.agents.style_agent import StyleAgent
from app.agents.security_agent import SecurityAgent
from app.agents.performance_agent import PerformanceAgent
from app.agents.bug_agent import BugAgent
from app.agents.synthesizer import SynthesizerAgent
from app.core.config import settings

logger = logging.getLogger(__name__)

class ReviewState(TypedDict):
    pr_number: int
    repository: str
    diff_content: str
    files_changed: int
    repo_config: Dict[str, Any]
    similar_patterns: List[Dict[str, Any]]
    issues: Annotated[List[Issue], operator.add]
    final_review: Dict[str, Any]


class ReviewWorkflow:
    def __init__(self):
        self.style_agent = StyleAgent()
        self.security_agent = SecurityAgent()
        self.performance_agent = PerformanceAgent()
        self.bug_agent = BugAgent()
        self.synthesizer = SynthesizerAgent()
        self.graph = self._build_graph()

    def _build_graph(self):
        workflow = StateGraph(ReviewState)

        # Add all nodes
        workflow.add_node("style", self._run_style)
        workflow.add_node("security", self._run_security)
        workflow.add_node("performance", self._run_performance)
        workflow.add_node("bug", self._run_bug)
        workflow.add_node("synthesize", self._run_synthesizer)

        # All 4 agents run from START in parallel (fan-out)
        workflow.add_edge(START, "style")
        workflow.add_edge(START, "security")
        workflow.add_edge(START, "performance")
        workflow.add_edge(START, "bug")

        # All agents feed into synthesizer (fan-in)
        workflow.add_edge("style", "synthesize")
        workflow.add_edge("security", "synthesize")
        workflow.add_edge("performance", "synthesize")
        workflow.add_edge("bug", "synthesize")

        workflow.add_edge("synthesize", END)

        return workflow.compile()

    def _create_context(self, state: ReviewState) -> CodeContext:
        return CodeContext(
            pr_number=state["pr_number"],
            repository=state["repository"],
            diff_content=state["diff_content"],
            files_changed=state["files_changed"],
            similar_patterns=state.get("similar_patterns", []),
            repo_config=state.get("repo_config", {})
        )

    async def _run_style(self, state: ReviewState):
        logger.info("Running StyleAgent...")
        issues = await self.style_agent.analyze(self._create_context(state))
        for i in issues:
            i.agent_type = "style"
        return {"issues": issues}

    async def _run_security(self, state: ReviewState):
        logger.info("Running SecurityAgent...")
        issues = await self.security_agent.analyze(self._create_context(state))
        for i in issues:
            i.agent_type = "security"
        return {"issues": issues}

    async def _run_performance(self, state: ReviewState):
        logger.info("Running PerformanceAgent...")
        issues = await self.performance_agent.analyze(self._create_context(state))
        for i in issues:
            i.agent_type = "performance"
        return {"issues": issues}

    async def _run_bug(self, state: ReviewState):
        logger.info("Running BugAgent...")
        issues = await self.bug_agent.analyze(self._create_context(state))
        for i in issues:
            i.agent_type = "bug"
        return {"issues": issues}

    def _run_synthesizer(self, state: ReviewState):
        logger.info(f"Synthesizing {len(state.get('issues', []))} issues...")
        result = self.synthesizer.synthesize(state.get("issues", []))
        return {"final_review": result}

    async def run(self, initial_state: dict) -> dict:
        """Execute the LangGraph workflow."""
        logger.info(f"Starting review workflow for PR #{initial_state.get('pr_number')}")
        try:
            result = await self.graph.ainvoke(initial_state)
            logger.info("Review workflow completed successfully.")
            return result
        except Exception as e:
            logger.error(f"Workflow execution failed: {e}", exc_info=True)
            raise


review_workflow = ReviewWorkflow()
