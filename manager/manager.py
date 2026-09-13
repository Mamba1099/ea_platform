from lifecycle import EALifecycleController
from mt5_runtime import MT5Runtime
from registry import create_registry


def main() -> None:
    registry = create_registry()

    runtime = MT5Runtime(
        terminal_path=(
            "/home/mamba/.wine/drive_c/"
            "Program Files/MetaTrader 5/terminal64.exe"
        ),
        wine_prefix="/home/mamba/.wine",
    )

    lifecycle = EALifecycleController(
        registry,
        runtime,
    )

    ea_id = "AI_BASKET_EA"

    print("\nInitial state:")
    print(registry.snapshot())

    print("\nRuntime before start:")
    print(runtime.heartbeat())

    print("\nStarting EA...")
    lifecycle.start(ea_id)
    print(registry.snapshot())

    print("\nRuntime after start:")
    print(runtime.heartbeat())

    print("\nStopping EA...")
    lifecycle.stop(ea_id)
    print(registry.snapshot())

    print("\nRuntime after stop:")
    print(runtime.heartbeat())


if __name__ == "__main__":
    main()