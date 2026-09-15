import sys
from pathlib import Path

from agents.domain_config_agent import configure_domain
from agents.orchestrator import run_pipeline


if __name__ == "__main__":
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    else:
        input_file = input(
            "\nEnter the path to your CSV dataset: "
        ).strip()

    input_path = Path(input_file)

    if not input_path.exists():
        print(
            f"\nError: Dataset not found: {input_file}"
        )
        sys.exit(1)

    if input_path.suffix.lower() != ".csv":
        print(
            "\nError: Please provide a CSV dataset."
        )
        sys.exit(1)

    print("\n" + "=" * 60)
    print("DOMAIN CONFIGURATION AGENT")
    print("=" * 60)

    domain_config = configure_domain(
        input_file
    )

    run_pipeline(
        input_file,
        domain_config
    )

