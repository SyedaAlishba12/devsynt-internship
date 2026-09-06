import os
from typing import TypedDict

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langgraph.graph import StateGraph, START, END

from agents.clean_agent import clean_dataset
from agents.analysis_agent import analyze_dataset
from agents.visualization_agent import create_visualizations


# Load environment variables from .env
load_dotenv()


class PipelineState(TypedDict):
    input_file: str
    cleaned_file: str
    cleaning_report: dict
    analysis_results: dict
    visualization_results: dict
    status: str
    route_decision: str


# -------------------------------------------------------------
# Orchestrator Decision Node
# -------------------------------------------------------------
def orchestrator_node(state: PipelineState):
    """
    The Orchestrator uses LangChain + Groq to decide
    how the raw dataset should be processed.
    """

    print("\n")
    print("=" * 60)
    print(">>> ORCHESTRATOR AGENT")
    print("=" * 60)

    print("\nInspecting input dataset...")
    print(f"Input file: {state['input_file']}")

    api_key = os.getenv("GROQ_API_KEY")

    if not api_key:
        print("\nGROQ_API_KEY not found.")
        print("Using default retail processing route.")

        return {
            "route_decision": "clean_first",
            "status": "Orchestrator selected clean-first route"
        }

    try:
        # Initialize Groq through LangChain
        llm = ChatGroq(
            model="openai/gpt-oss-20b",
            temperature=0,
            api_key=api_key
        )

        prompt = ChatPromptTemplate.from_messages([
            (
                "system",
                """
You are the Orchestrator Agent for a retail sales data pipeline.

Your job is to decide the correct first processing step for the
provided dataset.

Available routes:
- clean_first: Use this when the input is a raw or unprocessed CSV.
- analysis_first: Use this only when the dataset is already clean
  and ready for analysis.

For this project, raw retail CSV files should normally be cleaned
before analysis.

Return ONLY one of these exact values:
clean_first
analysis_first
"""
            ),
            (
                "human",
                """
Dataset information:

Input file: {input_file}

The file is the raw retail sales CSV supplied to the pipeline.

Choose the correct first processing route.
"""
            )
        ])

        chain = prompt | llm

        response = chain.invoke({
            "input_file": state["input_file"]
        })

        decision = response.content.strip().lower()

        # Make sure the LLM response is one of our valid routes
        if "analysis_first" in decision:
            route = "analysis_first"
        else:
            route = "clean_first"

        print("\nLLM Orchestrator Decision:")
        print(f"Route selected: {route}")

        return {
            "route_decision": route,
            "status": f"Orchestrator selected {route} route"
        }

    except Exception as e:
        print(f"\nOrchestrator LLM decision failed: {e}")
        print("Using safe default: clean_first")

        return {
            "route_decision": "clean_first",
            "status": "Orchestrator selected clean-first route"
        }


# -------------------------------------------------------------
# Clean Agent Node
# -------------------------------------------------------------
def clean_node(state: PipelineState):
    print("\n")
    print(">>> ORCHESTRATOR: Routing to Clean Agent")

    cleaned_df, cleaning_report = clean_dataset(
        state["input_file"],
        state["cleaned_file"]
    )

    return {
        "cleaning_report": cleaning_report,
        "status": "Dataset cleaned successfully"
    }


# -------------------------------------------------------------
# Analysis Agent Node
# -------------------------------------------------------------
def analysis_node(state: PipelineState):
    print("\n")
    print(">>> ORCHESTRATOR: Routing to Analysis Agent")

    results = analyze_dataset(
        state["cleaned_file"]
    )

    return {
        "analysis_results": results,
        "status": "Dataset analyzed successfully"
    }


# -------------------------------------------------------------
# Visualization Agent Node
# -------------------------------------------------------------
def visualization_node(state: PipelineState):
    print("\n")
    print(">>> ORCHESTRATOR: Routing to Visualization Agent")

    results = create_visualizations(
        state["cleaned_file"]
    )

    return {
        "visualization_results": results,
        "status": "Visualizations created successfully"
    }


# -------------------------------------------------------------
# Route after Orchestrator decision
# -------------------------------------------------------------
def route_from_orchestrator(state: PipelineState):
    """
    LangGraph reads the Orchestrator's decision and
    determines which node should run next.
    """

    decision = state["route_decision"]

    print("\n>>> LANGGRAPH: Applying orchestrator decision...")

    if decision == "analysis_first":
        print(">>> LANGGRAPH: Routing to Analysis Agent")
        return "analysis_agent"

    print(">>> LANGGRAPH: Routing to Clean Agent")
    return "clean_agent"


# -------------------------------------------------------------
# Build LangGraph
# -------------------------------------------------------------
def build_pipeline():
    graph = StateGraph(PipelineState)

    # Add agent nodes
    graph.add_node("orchestrator", orchestrator_node)
    graph.add_node("clean_agent", clean_node)
    graph.add_node("analysis_agent", analysis_node)
    graph.add_node("visualization_agent", visualization_node)

    # Start with Orchestrator
    graph.add_edge(START, "orchestrator")

    # Orchestrator makes the routing decision
    graph.add_conditional_edges(
        "orchestrator",
        route_from_orchestrator,
        {
            "clean_agent": "clean_agent",
            "analysis_agent": "analysis_agent",
        }
    )

    # Normal processing after the selected first step
    graph.add_edge("clean_agent", "analysis_agent")
    graph.add_edge("analysis_agent", "visualization_agent")
    graph.add_edge("visualization_agent", END)

    return graph.compile()


# -------------------------------------------------------------
# Run complete pipeline
# -------------------------------------------------------------
def run_pipeline():
    print("\n" + "=" * 60)
    print("LANGGRAPH RETAIL SALES PIPELINE")
    print("=" * 60)

    initial_state = {
        "input_file": "data/Sample - Superstore.csv",
        "cleaned_file": "data/cleaned_superstore.csv",
        "cleaning_report": {},
        "analysis_results": {},
        "visualization_results": {},
        "status": "Pipeline started",
        "route_decision": ""
    }

    pipeline = build_pipeline()

    final_state = pipeline.invoke(initial_state)

    print("\n" + "=" * 60)
    print("PIPELINE COMPLETE")
    print("=" * 60)

    print("\nFinal Status:")
    print(final_state["status"])

    print("\nOrchestrator Decision:")
    print(final_state["route_decision"])

    return final_state


if __name__ == "__main__":
    run_pipeline()

