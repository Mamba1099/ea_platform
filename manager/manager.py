from lifecycle import EALifecycleController
from mt5_runtime import MT5Runtime
from registry import create_registry
from ipc.config import IPC_ROOT
from ipc.file_bridge import EAFileBridge


def main() -> None:
    registry = create_registry()

    runtime = MT5Runtime(
        terminal_path=(
            "/home/mamba/.wine/drive_c/" "Program Files/MetaTrader 5/terminal64.exe"
        ),
        wine_prefix="/home/mamba/.wine",
    )

    bridge = EAFileBridge(IPC_ROOT)

    lifecycle = EALifecycleController(
        registry,
        runtime,
        bridge,
    )

    ea_id = "AI_BASKET_EA"

    print("\nRegistry before refresh:")
    print(registry.snapshot())

    print("\nRefreshing from EA...")
    lifecycle.refresh_status(ea_id)

    print("\nRegistry after refresh:")
    print(registry.snapshot())

    print("\nPausing EA through lifecycle controller...")
    lifecycle.pause(ea_id)

    print("\nState after pause:")
    print(registry.snapshot())

    print("\nResuming EA through lifecycle controller...")
    lifecycle.resume(ea_id)

    print("\nState after resume:")
    print(registry.snapshot())


if __name__ == "__main__":
    main()
