from pathlib import Path


class PipelineExtension:
    def configure(self, case_id: str, case_path: Path):
        """Intended for pipeline specific configurations. If none is needed, this bare class
        can be used."""
        pass
