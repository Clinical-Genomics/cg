from pathlib import Path


class PipelineExtension:
    def configure(self, case_id: str, case_run_directory: Path) -> None:
        """Intended for pipeline specific configurations. If none is needed, this bare class
        can be used."""
        pass
