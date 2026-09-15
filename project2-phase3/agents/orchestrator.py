from pathlib import Path
from typing import TypedDict
from langgraph.graph import StateGraph, START, END
from agents.clean_agent import clean_dataset
from agents.analysis_agent import analyze_dataset
from agents.dashboard_agent import generate_dashboard

class PipelineState(TypedDict, total=False):
    input_file: str
    cleaned_file: str
    dashboard_file: str
    domain_config: dict
    cleaning_report: dict
    analysis_results: dict
    dashboard_result: dict
    status: str
    errors: list

def clean_node(state):
    print("\n" + "=" * 60)
    print("PIPELINE STEP 1: CLEANING")
    print("=" * 60)
    try:
        input_file = state["input_file"]

        input_path = Path(input_file)

        cleaned_name = (
            f"cleaned_{input_path.stem}.csv"
        )

        cleaned_file = str(
            input_path.parent / cleaned_name
        )

        result = clean_dataset(
            input_file,
            cleaned_file,
            state["domain_config"],
        )

        return {
            "cleaned_file": cleaned_file,
            "cleaning_report": result,
            "status": "success",
        }

    except Exception as exc:
        return {
            "status": "error",
            "errors": state.get("errors", []) + [str(exc)],
        }

def analysis_node(state):
    print("\n" + "=" * 60)
    print("PIPELINE STEP 2: ANALYSIS")
    print("=" * 60)
    try:
        analysis_result = analyze_dataset(
            state["cleaned_file"],
            state["domain_config"],
        )

        if not isinstance(
            analysis_result,
            dict
        ):
            raise ValueError(
                "Analysis Agent did not return a dictionary."
            )

        if analysis_result.get("status") != "success":
            raise ValueError(
                analysis_result.get(
                    "error",
                    "Analysis Agent failed."
                )
            )

        return {
            "analysis_results": analysis_result,
            "status": "success",
        }

    except Exception as exc:
        return {
            "status": "error",
            "errors": state.get("errors", []) + [str(exc)],
        }

def dashboard_node(state):
    print("\n" + "=" * 60)
    print("PIPELINE STEP 3: DASHBOARD")
    print("=" * 60)
    try:
        input_path = Path(
            state["input_file"]
        )

        dashboard_name = (
            f"{input_path.stem}_dashboard.html"
        )

        dashboard_file = str(
            Path("generated-dashboard") / dashboard_name
        )

        result = generate_dashboard(
            state["analysis_results"],
            dashboard_file,
        )

        if not isinstance(
            result,
            dict
        ):
            raise ValueError(
                "Dashboard Agent did not return a dictionary."
            )

        if result.get("status") != "success":
            raise ValueError(
                result.get(
                    "error",
                    "Dashboard Agent failed."
                )
            )

        return {
            "dashboard_file": dashboard_file,
            "dashboard_result": result,
            "status": "success",
        }

    except Exception as exc:
        return {
            "status": "error",
            "errors": state.get("errors", []) + [str(exc)],
        }

def check_status(state):
    if state.get("status") == "error":
        return "end"
    return "continue"

def build_pipeline():
    graph = StateGraph(
        PipelineState
    )
    graph.add_node(
        "clean",
        clean_node,
    )

    graph.add_node(
        "analysis",
        analysis_node,
    )

    graph.add_node(
        "dashboard",
        dashboard_node,
    )

    graph.add_edge(
        START,
        "clean",
    )

    graph.add_conditional_edges(
        "clean",
        check_status,
        {
            "continue": "analysis",
            "end": END,
        },
    )

    graph.add_conditional_edges(
        "analysis",
        check_status,
        {
            "continue": "dashboard",
            "end": END,
        },
    )

    graph.add_edge(
        "dashboard",
        END,
    )

    return graph.compile()

def run_pipeline(
    input_file,
    domain_config
):
    print("\n" + "=" * 60)
    print("PHASE 3 PRODUCTION PIPELINE")
    print("=" * 60)
    pipeline = build_pipeline()

    initial_state = {
        "input_file": input_file,
        "domain_config": domain_config,
        "status": "starting",
        "errors": [],
    }

    result = pipeline.invoke(
        initial_state
    )

    print("\n" + "=" * 60)
    print("PIPELINE RESULT")
    print("=" * 60)

    if result.get("status") == "success":
        print("\nPipeline completed successfully.")

        print(
            f"\nCleaned dataset:"
            f"\n{result.get('cleaned_file')}"
        )

        print(
            f"\nGenerated dashboard:"
            f"\n{result.get('dashboard_file')}"
        )

    else:
        print("\nPipeline failed.")

        for error in result.get(
            "errors",
            []
        ):
            print(
                f"\nError: {error}"
            )

    return result