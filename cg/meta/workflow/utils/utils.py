from cg.constants.priority import Priority, TrailblazerPriority

MAP_TO_TRAILBLAZER_PRIORITY: dict[Priority, TrailblazerPriority] = {
    Priority.research: TrailblazerPriority.LOW,
    Priority.standard: TrailblazerPriority.NORMAL,
    Priority.clinical_trials: TrailblazerPriority.NORMAL,
    Priority.priority: TrailblazerPriority.HIGH,
    Priority.express: TrailblazerPriority.EXPRESS,
}
