from cg.meta.workflow.mutant.metadata_parser import MetadataParser


    def parse_metadata(self, case: Case) -> SamplesMetadataMetrics:
       

    def parse_metadata_for_case(self, case: Case) -> dict[str, SampleMetadata]:

       

    def parse_metadata_for_internal_negative_control(
        self, metadata_for_case: SamplesMetadataMetrics
    ) -> dict[str, SampleMetadata]:
        internal_negative_control_id: Sample = get_internal_negative_control_id(
            self.lims, metadata_for_case
        )

        internal_negative_control: Sample = self.status_db.get_sample_by_internal_id(
            internal_negative_control_id
        )

        if not internal_negative_control:
            return None  # TODO: How should this exception be handled.
        else:
            internal_negative_control_metadata = SampleMetadata(
                sample_internal_id=internal_negative_control.internal_id,
                sample_name=internal_negative_control.name,
                is_external_negative_control=False,
                is_internal_negative_control=True,
                reads=internal_negative_control.reads,
                target_reads=internal_negative_control.application_version.application.target_reads,
                percent_reads_guaranteed=internal_negative_control.application_version.application.percent_reads_guaranteed,
            )

            return dict[internal_negative_control.internal_id, internal_negative_control_metadata]
