# Coverage Seed

Total tests analyzed: 976
Zero-unique tests (safe to delete): 767
Low-unique tests (<10%): 93

## Zero-Unique Tests

Every line these tests cover is also covered by at least one other test.
Deleting these will NOT change coverage.

| Test | Lines Covered | Unique Lines |
|------|--------------|-------------|
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_error_message_includes_file_path` | 12 | 0 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_displays_rich_formatted_error_on_permission_error` | 12 | 0 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_does_not_continue_after_read_error` | 12 | 0 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_handles_permission_error_on_spec_read` | 12 | 0 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_handles_os_error_on_spec_read` | 13 | 0 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_displays_rich_formatted_error_on_os_error` | 13 | 0 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_aborts_on_os_error` | 13 | 0 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_succeeds_when_no_read_error` | 24 | 0 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_aborts_on_permission_error` | 12 | 0 |
| `tests.test_logs_command.TestLogsCommandFiltering.test_logs_since_filters_by_time` | 77 | 0 |
| `tests.test_logs_command.TestLogsCommandBasic.test_logs_shows_event_data` | 64 | 0 |
| `tests.test_logs_command.TestLogsCommandOutput.test_logs_tail_shows_recent_first` | 63 | 0 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_with_filtering` | 95 | 0 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_shows_logs_from_multiple_workflows` | 91 | 0 |
| `tests.test_logs_command.TestLogsCommandBasic.test_logs_formats_timestamp` | 64 | 0 |
| `tests.test_logs_command.TestLogsCommandFiltering.test_logs_level_error_shows_only_errors` | 67 | 0 |
| `tests.test_logs_command.TestLogsCommandBasic.test_logs_shows_recent_events` | 64 | 0 |
| `tests.test_logs_command.TestLogsCommandBasic.test_logs_shows_most_recent_workflow_by_default` | 96 | 0 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_with_no_workflows` | 12 | 0 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_uses_get_all_workflows_function` | 9 | 0 |
| `tests.test_status_command.TestStatusCommand.test_status_most_recent_workflow` | 52 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_does_not_continue_after_write_error` | 99 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_displays_rich_formatted_error_on_os_error` | 100 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_displays_rich_formatted_error_on_permission_error` | 99 | 0 |
| `tests.test_work_command.TestWorkPhaseTransitions.test_work_saves_state_with_planning_phase` | 227 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_error_message_includes_file_path` | 99 | 0 |
| `tests.test_work_command.TestBeadsStatusLifecycle.test_work_updates_status_to_in_progress` | 131 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_handles_os_error_on_spec_write` | 100 | 0 |
| `tests.test_work_command.TestWorkFetchAndSpec.test_work_fetches_task_and_generates_spec` | 227 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_aborts_on_permission_error` | 99 | 0 |
| `tests.test_work_command.TestWorkCommandFlags.test_model_option_accepts_valid_models` | 128 | 0 |
| `tests.test_work_command.TestWorkCommandFlags.test_dry_run_skips_workflow_execution` | 123 | 0 |
| `tests.test_work_command.TestWorkflowIntegration.test_work_model_flag_overrides_both_agents` | 152 | 0 |
| `tests.test_work_command.TestBeadsStatusLifecycle.test_work_closes_task_on_success` | 179 | 0 |
| `tests.test_work_command.TestWorkflowIntegration.test_work_calls_workflow_with_spec` | 161 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_succeeds_when_no_write_error` | 123 | 0 |
| `tests.test_work_command.TestWorkFetchAndSpec.test_work_handles_fetch_error_gracefully` | 14 | 0 |
| `tests.test_work_command.TestBeadsStatusLifecycle.test_work_does_not_close_on_failure` | 86 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_aborts_on_os_error` | 100 | 0 |
| `tests.test_work_command.TestWorkflowStateSetup.test_work_creates_and_saves_workflow_state` | 131 | 0 |
| `tests.cli.commands.test_work_error_handling.TestWorkCommandFileWriteErrorHandling.test_work_handles_permission_error_on_spec_write` | 99 | 0 |
| `tests.test_work_command.TestWorkflowIntegration.test_work_handles_workflow_errors` | 149 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_handles_permission_error_on_spec_read` | 12 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_handles_os_error_on_spec_read` | 13 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_displays_rich_formatted_error_on_os_error` | 13 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_error_message_includes_file_path` | 12 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_does_not_continue_after_read_error` | 12 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_aborts_on_permission_error` | 12 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_succeeds_when_no_read_error` | 22 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_aborts_on_os_error` | 13 | 0 |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_displays_rich_formatted_error_on_permission_error` | 12 | 0 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_help_shows_all_option` | 1 | 0 |
| `tests.test_logs_command.TestLogsCommandFollow.test_logs_follow_flag_exists` | 1 | 0 |
| `tests.test_logs_command.TestLogsHelp.test_logs_help_shows_usage` | 1 | 0 |
| `tests.test_streaming.TestStreamingDisplay.test_initialization` | 5 | 0 |
| `tests.test_streaming.TestStreamingDisplay.test_get_full_output_empty` | 6 | 0 |
| `tests.test_streaming.TestStreamingDisplay.test_get_full_output` | 7 | 0 |
| `tests.test_streaming.TestStreamingDisplay.test_tool_tracking_disabled` | 7 | 0 |
| `tests.test_streaming.TestStreamingDisplay.test_add_text` | 6 | 0 |
| `tests.core.test_budget_limit.TestBudgetPassthrough.test_no_budget_passes_none` | 47 | 0 |
| `tests.core.test_sandbox.TestSandboxPassthrough.test_sandbox_disabled_passes_none` | 47 | 0 |
| `tests.core.test_sandbox.TestSandboxPassthrough.test_sandbox_passed_to_sdk_options` | 47 | 0 |
| `tests.core.test_output_format.TestOutputFormatPassthrough.test_output_format_passed_to_sdk_options` | 47 | 0 |
| `tests.core.test_budget_limit.TestBudgetPassthrough.test_budget_passed_to_sdk_options` | 47 | 0 |
| `tests.core.test_output_format.TestOutputFormatPassthrough.test_no_output_format_passes_none` | 47 | 0 |
| `tests.test_detectors.TestDetectorSharedBehavior.test_inherits_from_blocker_detector` | 109 | 0 |
| `tests.test_detectors.TestAmbiguityDetector.test_realistic_agent_ambiguity_scenario` | 105 | 0 |
| `tests.test_detectors.TestDetectorSharedBehavior.test_case_insensitive_detection` | 296 | 0 |
| `tests.test_detectors.TestAmbiguityDetector.test_distinguish_from_other_blocker_types` | 22 | 0 |
| `tests.test_detectors.TestAmbiguityDetector.test_mixed_content_with_ambiguity` | 67 | 0 |
| `tests.test_task_validator.TestTaskValidatorTestMentions.test_test_mention_detection_in_description` | 47 | 0 |
| `tests.test_spec_generation.TestGenerateSpecFromBeads.test_generate_spec_is_idempotent` | 28 | 0 |
| `tests.test_spec_generation.TestGenerateSpecIntegration.test_spec_can_be_written_to_file` | 28 | 0 |
| `tests.test_spec_generation.TestGenerateSpecFromBeads.test_generate_spec_with_multiline_description` | 28 | 0 |
| `tests.test_spec_generation.TestGenerateSpecFromBeads.test_generate_spec_with_many_criteria` | 28 | 0 |
| `tests.core.test_beads.TestBeadsOperationsValidation.test_valid_id_proceeds_to_subprocess_for_all_operations` | 50 | 0 |
| `tests.test_task_validator.TestTaskValidatorTestMentions.test_test_keyword_in_acceptance_criteria` | 45 | 0 |
| `tests.test_task_validator.TestTaskValidatorIntegration.test_poor_task_multiple_warnings` | 52 | 0 |
| `tests.core.test_beads.TestNoDaemonFlagInOperations.test_all_operations_use_no_daemon_flag` | 50 | 0 |
| `tests.test_edit_integration.TestInteractivePromptWithEdit.test_edit_and_revalidate_handles_no_improvement` | 59 | 0 |
| `tests.test_edit_integration.TestEditAndRevalidateFlow.test_edit_and_revalidate_flow` | 54 | 0 |
| `tests.test_edit_integration.TestEditAndRevalidateFlow.test_edit_and_revalidate_with_validator` | 52 | 0 |
| `tests.test_task_validator.TestTaskValidatorAcceptanceCriteria.test_acceptance_criteria_validation` | 49 | 0 |
| `tests.test_spec_generation.TestGenerateSpecFromBeads.test_generate_spec_preserves_special_characters_and_unicode` | 24 | 0 |
| `tests.test_spec_generation.TestGenerateSpecFromBeads.test_generate_spec_without_acceptance_criteria` | 27 | 0 |
| `tests.test_spec_generation.TestGenerateSpecFromBeads.test_generate_spec_with_different_statuses` | 27 | 0 |
| `tests.test_spec_generation.TestGenerateSpecFromBeads.test_generate_spec_complete_structure` | 28 | 0 |
| `tests.core.test_beads.TestValidateBeadsId.test_case_insensitive_and_boundary_lengths` | 2 | 0 |
| `tests.core.test_beads.TestBeadsOperationsValidation.test_all_operations_reject_malicious_input` | 7 | 0 |
| `tests.core.test_beads.TestBeadsOperationsValidation.test_invalid_id_blocked_before_subprocess` | 7 | 0 |
| `tests.core.test_beads.TestValidateBeadsId.test_command_injection_attempts_blocked` | 4 | 0 |
| `tests.core.test_beads.TestValidateBeadsId.test_error_message_is_helpful` | 4 | 0 |
| `tests.core.test_beads.TestValidateBeadsId.test_valid_ids_pass_validation` | 2 | 0 |
| `tests.core.test_beads.TestRunBdCommandHelper.test_prepends_no_daemon_flag_and_passes_kwargs` | 2 | 0 |
| `tests.test_blocker_message_builder.TestBlockerMessageConstruction.test_build_message_for_error_blocker` | 36 | 0 |
| `tests.test_blocker_message_builder.TestBlockerMessageBuilderValidation.test_build_message_handles_all_blocker_types` | 28 | 0 |
| `tests.test_blocker_message_builder.TestBlockerMessageConstruction.test_build_message_for_test_failure_blocker` | 36 | 0 |
| `tests.test_blocker_message_builder.TestBlockerMessageConstruction.test_build_message_for_ambiguity_blocker` | 36 | 0 |
| `tests.test_blocker_message_builder.TestBlockerMessageBodyFormatting.test_message_body_includes_all_blocker_information` | 36 | 0 |
| `tests.test_blocker_message_builder.TestBlockerMessageBodyFormatting.test_message_body_handles_missing_context_and_suggestions` | 28 | 0 |
| `tests.test_blocker_message_builder.TestBlockerMessageBuilderIntegration.test_end_to_end_workflow_blocker_message_creation` | 36 | 0 |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorParseDiff.test_parse_identifies_code_elements` | 49 | 0 |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorGenerate.test_generate_handles_errors_and_complex_diffs` | 89 | 0 |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorGetDiff.test_get_diff_handles_git_error` | 15 | 0 |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorIntegration.test_full_workflow_new_feature_and_refactoring` | 88 | 0 |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorGetDiff.test_get_diff_success_and_staged_flag` | 14 | 0 |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorParseDiff.test_parse_identifies_file_changes` | 39 | 0 |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorGenerate.test_generate_returns_bullets_and_uses_staged_flag` | 68 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_state_persistence` | 385 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_commit_feature_tests_fail` | 40 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_max_iterations` | 374 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_single_feature` | 348 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_output_directory_structure` | 379 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_session_tracking` | 381 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_respects_max_iterations` | 381 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_progress_tracking` | 381 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_feature_failure` | 384 | 0 |
| `tests.orchestration.test_auto_continue.TestRunAutoContinue.test_run_auto_continue_multiple_features` | 382 | 0 |
| `tests.orchestration.test_auto_continue_integration.test_full_workflow_lifecycle` | 392 | 0 |
| `tests.orchestration.test_auto_continue_integration.test_workflow_with_failure_recovery` | 380 | 0 |
| `tests.orchestration.test_auto_continue_integration.test_workflow_interrupt_and_resume` | 370 | 0 |
| `tests.orchestration.test_auto_continue_integration.test_workflow_cost_and_duration_tracking` | 367 | 0 |
| `tests.test_commit_error_handler.TestCommitErrorHandlerEnhanceMessage.test_enhance_error_message` | 6 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_multiple_body_items` | 22 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_beads_task_id_format` | 19 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_complete_realistic_commit` | 22 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_commit_with_empty_body_items` | 19 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_message_structure` | 22 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_fix_commit_with_scope` | 22 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_scope_with_special_characters` | 22 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_all_valid_commit_types` | 22 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_basic_feat_commit` | 22 | 0 |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_test_commit_type` | 22 | 0 |
| `tests.test_conventional_commit_parser.TestConventionalCommitParserContext.test_common_action_prefixes` | 57 | 0 |
| `tests.test_conventional_commit_parser.TestConventionalCommitParserScopes.test_parse_scopes` | 59 | 0 |
| `tests.test_conventional_commit_parser.TestConventionalCommitParserEdgeCases.test_case_insensitive_and_ambiguous_defaults` | 59 | 0 |
| `tests.test_conventional_commit_parser.TestConventionalCommitParserEdgeCases.test_parse_returns_required_keys` | 55 | 0 |
| `tests.test_edit_integration.TestEditAndRevalidateErrorHandling.test_edit_and_revalidate_handles_edit_failure` | 3 | 0 |
| `tests.test_edit_integration.TestEditAndRevalidateErrorHandling.test_edit_and_revalidate_handles_fetch_failure` | 4 | 0 |
| `tests.test_edit_integration.TestEditTaskHandler.test_init_creates_handler` | 1 | 0 |
| `tests.test_edit_integration.TestEditTaskHandler.test_edit_task_with_empty_task_id_raises_error` | 5 | 0 |
| `tests.test_edit_integration.TestEditTaskHandlerCustomBdPath.test_init_with_custom_bd_path` | 1 | 0 |
| `tests.test_edit_integration.TestEditTaskHandlerCustomBdPath.test_init_with_default_bd_path` | 1 | 0 |
| `tests.test_edit_integration.TestEditTaskHandlerCustomBdPath.test_edit_task_uses_custom_bd_path` | 10 | 0 |
| `tests.test_edit_integration.TestEditTaskHandler.test_edit_task_returns_successfully` | 10 | 0 |
| `tests.test_edit_integration.TestEditTaskSubprocessOptions.test_edit_task_uses_text_mode` | 10 | 0 |
| `tests.test_edit_integration.TestEditTaskHandler.test_edit_task_with_whitespace_task_id_raises_error` | 5 | 0 |
| `tests.test_edit_integration.TestEditTaskHandler.test_edit_task_calls_bd_edit` | 10 | 0 |
| `tests.test_edit_integration.TestEditTaskSubprocessOptions.test_edit_task_captures_output` | 10 | 0 |
| `tests.test_edit_integration.TestEditTaskValidation.test_edit_task_handles_special_characters` | 10 | 0 |
| `tests.test_edit_integration.TestEditTaskHandler.test_edit_task_waits_for_editor_to_close` | 10 | 0 |
| `tests.test_detectors.TestErrorDetector.test_mixed_content_with_errors` | 69 | 0 |
| `tests.test_detectors.TestErrorDetector.test_ambiguous_vs_error_distinction` | 22 | 0 |
| `tests.core.test_event_store_operations.TestTransactionBoundaries.test_error_recovery_continues_operation` | 132 | 0 |
| `tests.core.test_event_store_operations.TestSnapshotBasedRecovery.test_replay_from_snapshot_with_new_events` | 235 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotErrorHandling.test_auto_snapshot_handles_corrupted_snapshot_data` | 165 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotContent.test_auto_snapshot_replaces_existing_snapshot` | 173 | 0 |
| `tests.core.test_performance_optimization.TestBatchOperations.test_append_batch_performance_gain` | 171 | 0 |
| `tests.core.test_snapshot_save.TestSaveSnapshotIntegration.test_snapshot_alongside_events` | 136 | 0 |
| `tests.core.test_event_append.TestEventAppendTransactions.test_append_rollback_on_connection_error` | 53 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotCreationBasic.test_auto_snapshot_workflow_isolation` | 166 | 0 |
| `tests.core.test_event_query.TestGetEventsBasicAndFiltering.test_get_events_reconstructs_complex_event_data` | 131 | 0 |
| `tests.core.test_event_type_handlers.TestEventTypeHandlers.test_phase_changed_event` | 37 | 0 |
| `tests.core.test_performance_optimization.TestDatabaseIndexes.test_indexes_improve_query_performance` | 93 | 0 |
| `tests.core.test_event_models.TestEventAndSnapshotIntegration.test_models_compatible_with_existing_event_infrastructure` | 13 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotCreationBasic.test_auto_snapshot_created_at_200_events` | 165 | 0 |
| `tests.core.test_event_append.TestEventAppendValidation.test_append_validates_required_event_fields` | 41 | 0 |
| `tests.core.test_event_models.TestEventModel.test_event_data_json_serialization` | 13 | 0 |
| `tests.core.test_event_store_operations.TestSubscriberIntegration.test_subscribers_notified_on_append` | 100 | 0 |
| `tests.core.test_event_store_operations.TestMultiWorkflowOperations.test_multiple_workflows_with_snapshots` | 230 | 0 |
| `tests.core.test_event_append.TestEventAppendIntegration.test_append_preserves_event_model_properties` | 101 | 0 |
| `tests.core.test_event_type_handlers.TestEventTypeHandlers.test_workflow_lifecycle_events` | 37 | 0 |
| `tests.core.test_event_type_handlers.TestEventTypeHandlers.test_worktree_lifecycle_events` | 37 | 0 |
| `tests.core.test_event_append.TestEventAppendValidation.test_append_handles_json_serialization_error` | 69 | 0 |
| `tests.core.test_performance_optimization.TestQueryPagination.test_get_events_with_limit` | 135 | 0 |
| `tests.core.test_performance_optimization.TestQueryPagination.test_pagination_handles_bounds` | 138 | 0 |
| `tests.core.test_performance_optimization.TestBatchOperations.test_append_batch_basic` | 140 | 0 |
| `tests.core.test_projection_builder.TestProjectionBuilderEventApplication.test_feature_lifecycle_with_multiple_features` | 37 | 0 |
| `tests.core.test_event_subscription.TestSubscriptionIntegration.test_callback_can_query_database` | 108 | 0 |
| `tests.core.test_event_append.TestEventAppendIntegration.test_append_integrates_with_existing_database_schema` | 101 | 0 |
| `tests.core.test_error_handling.TestDatabaseConnectionErrors.test_operations_handle_database_errors` | 103 | 0 |
| `tests.core.test_event_append.TestEventAppendTransactions.test_append_rollback_on_database_error` | 69 | 0 |
| `tests.core.test_event_replay.TestEventReplayBasic.test_rebuild_projection_multiple_workflows_isolation` | 184 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotIntegration.test_auto_snapshot_append_transaction_handling` | 174 | 0 |
| `tests.core.test_event_type_handlers.TestEventTypeHandlers.test_unknown_event_type_raises_error` | 37 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotCreationBasic.test_auto_snapshot_created_at_100_events` | 166 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotErrorHandling.test_auto_snapshot_failure_does_not_prevent_event_append` | 174 | 0 |
| `tests.core.test_event_type_handlers.TestEventTypeHandlers.test_feature_lifecycle_complete_flow` | 37 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotContent.test_auto_snapshot_contains_workflow_events_summary` | 165 | 0 |
| `tests.core.test_performance_optimization.TestQueryPagination.test_get_events_with_offset` | 138 | 0 |
| `tests.core.test_performance_optimization.TestBatchOperations.test_append_batch_transaction_rollback` | 108 | 0 |
| `tests.core.test_event_store_operations.TestCompleteEventStoreLifecycle.test_full_workflow_lifecycle` | 235 | 0 |
| `tests.core.test_projection_builder.TestProjectionBuilderEventApplication.test_state_immutability` | 37 | 0 |
| `tests.core.test_event_append.TestEventAppendBasicFunctionality.test_append_multiple_events_sequential` | 101 | 0 |
| `tests.core.test_event_models.TestEventAndSnapshotIntegration.test_models_compatible_with_database_schema` | 29 | 0 |
| `tests.core.test_event_replay.TestEventReplayBasic.test_rebuild_projection_no_snapshot_full_replay` | 184 | 0 |
| `tests.core.test_event_store_operations.TestSubscriberIntegration.test_subscribers_notified_on_batch_append` | 109 | 0 |
| `tests.core.test_event_query.TestGetEventsBasicAndFiltering.test_get_events_timestamp_ordering` | 131 | 0 |
| `tests.core.test_auto_snapshot.TestAutoSnapshotIntegration.test_auto_snapshot_integrates_with_existing_save_snapshot` | 165 | 0 |
| `tests.core.test_event_type_handlers.TestEventTypeHandlers.test_test_lifecycle_events` | 37 | 0 |
| `tests.core.test_projection_builder.TestProjectionBuilderEventApplication.test_apply_event_routes_to_correct_handlers` | 37 | 0 |
| `tests.core.test_event_store_operations.TestMultiWorkflowOperations.test_multiple_workflows_isolated` | 131 | 0 |
| `tests.core.test_projection_builder.TestProjectionBuilderEventApplication.test_unknown_event_type_raises_error` | 37 | 0 |
| `tests.core.test_event_store_operations.TestPaginationWithProjections.test_paginated_replay` | 190 | 0 |
| `tests.core.test_event_type_handlers.TestEventTypeHandlers.test_state_immutability` | 37 | 0 |
| `tests.core.test_event_models.TestEventAndSnapshotIntegration.test_models_json_serialization_roundtrip` | 29 | 0 |
| `tests.core.test_event_models.TestEventAndSnapshotIntegration.test_event_and_snapshot_share_workflow_and_sequence` | 29 | 0 |
| `tests.core.test_event_replay.TestEventReplayBasic.test_rebuild_projection_with_snapshot_partial_replay` | 232 | 0 |
| `tests.core.test_event_replay.TestEventReplayEdgeCases.test_rebuild_projection_preserves_snapshot_immutability` | 232 | 0 |
| `tests.core.test_event_store_operations.TestTransactionBoundaries.test_batch_append_atomicity` | 144 | 0 |
| `tests.core.test_event_subscription.TestSubscriptionIntegration.test_failed_append_does_not_trigger_callbacks` | 101 | 0 |
| `tests.core.test_event_append.TestEventAppendBasicFunctionality.test_append_single_event_success` | 101 | 0 |
| `tests.core.test_event_type_handlers.TestEventTypeHandlers.test_commit_events` | 37 | 0 |
| `tests.core.test_event_subscription.TestEventNotificationOnAppend.test_append_notifies_subscribers` | 108 | 0 |
| `tests.core.test_event_append.TestEventAppendBasicFunctionality.test_append_event_with_proper_timestamp` | 101 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotBasicFunctionality.test_get_snapshot_preserves_complex_snapshot_data` | 103 | 0 |
| `tests.core.test_event_replay.TestEventReplayBasic.test_rebuild_projection_snapshot_only_no_subsequent_events` | 144 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotIntegration.test_get_snapshot_works_with_database_schema` | 111 | 0 |
| `tests.core.test_error_handling.TestTransactionConflicts.test_save_snapshot_rolls_back_on_error` | 72 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotBasicFunctionality.test_get_snapshot_handles_multiple_snapshots_returns_latest` | 103 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotValidation.test_get_snapshot_handles_workflow_id_with_whitespace` | 103 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotBasicFunctionality.test_get_snapshot_returns_latest_snapshot_success` | 103 | 0 |
| `tests.core.test_snapshot_save.TestSaveSnapshotTransactions.test_commit_and_rollback_behavior` | 73 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotIntegration.test_get_snapshot_handles_concurrent_workflows` | 104 | 0 |
| `tests.core.test_snapshot_save.TestSaveSnapshotBasicFunctionality.test_save_and_replace_snapshot` | 86 | 0 |
| `tests.core.test_snapshot_save.TestSaveSnapshotBasicFunctionality.test_save_multiple_workflows` | 86 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotIntegration.test_get_snapshot_integrates_with_save_snapshot` | 103 | 0 |
| `tests.core.test_event_models.TestSnapshotModel.test_snapshot_data_json_serialization` | 16 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchemaValidation.test_extra_fields_forbidden` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchema.test_agent_message_sent_schema_creation` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentEventIntegration.test_agent_message_sent_event_serialization` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchema.test_agent_message_sent_schema_with_event` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchema.test_agent_message_sent_schema_alias` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchema.test_agent_message_sent_schema_priority_levels` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchema.test_agent_message_sent_schema_different_message_types` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchemaValidation.test_field_trimming` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchema.test_agent_message_sent_schema_defaults` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentEventIntegration.test_agent_message_sent_event_metadata` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentSchemaValidation.test_required_field_validation` | 6 | 0 |
| `tests.test_agent_message_sent_schema.TestAgentMessageSentEventIntegration.test_agent_message_sent_round_trip` | 8 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotBasicFunctionality.test_get_snapshot_returns_none_for_empty_database` | 58 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaCompatibility.test_eventstore_context_manager_transaction_handling` | 51 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotErrorHandling.test_get_snapshot_resource_cleanup_on_error` | 44 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotErrorHandling.test_get_snapshot_handles_database_connection_error` | 40 | 0 |
| `tests.test_connection_management.TestEventStoreConnectionManagement.test_close_connection_and_edge_cases` | 43 | 0 |
| `tests.core.test_error_handling.TestEventDataValidation.test_append_rejects_invalid_input` | 35 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaIntegration.test_event_store_initializes_tables_and_indexes` | 51 | 0 |
| `tests.test_connection_management.TestEventStoreErrorHandling.test_invalid_path_error_messages` | 19 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotBasicFunctionality.test_get_snapshot_returns_none_when_no_snapshot_exists` | 58 | 0 |
| `tests.test_connection_management.TestEventStoreConnectionManagement.test_multiple_connections_create_and_cleanup` | 43 | 0 |
| `tests.test_connection_management.TestEventStoreContextManager.test_multiple_sequential_context_managers` | 51 | 0 |
| `tests.core.test_database_connection.TestDatabaseConnectionManagement.test_get_connection_returns_fresh_optimized_connections` | 40 | 0 |
| `tests.core.test_error_handling.TestEventDataValidation.test_get_events_validates_parameters` | 44 | 0 |
| `tests.core.test_event_replay.TestEventReplayBasic.test_rebuild_projection_empty_event_stream` | 97 | 0 |
| `tests.test_connection_management.TestEventStoreContextManager.test_context_manager_commit_close_and_rollback` | 52 | 0 |
| `tests.core.test_database_schema.TestEventStoreInitialization.test_init_handles_special_characters_in_path` | 30 | 0 |
| `tests.core.test_event_query.TestGetEventsValidation.test_get_events_validates_parameters` | 75 | 0 |
| `tests.core.test_database_connection.TestDatabaseContextManager.test_context_manager_commits_and_closes` | 51 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaIdempotency.test_events_autoincrement_primary_key` | 51 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaIntegration.test_data_insertion_and_json_handling` | 51 | 0 |
| `tests.core.test_database_connection.TestDatabaseContextManager.test_multiple_context_managers_independent` | 51 | 0 |
| `tests.test_connection_management.TestEventStoreErrorHandling.test_corrupted_database_file` | 24 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaIntegration.test_snapshots_table_schema_structure` | 51 | 0 |
| `tests.core.test_event_replay.TestEventReplayInputValidation.test_rebuild_projection_requires_workflow_id` | 30 | 0 |
| `tests.test_connection_management.TestEventStoreConnectionIntegration.test_string_and_path_initialization_share_database` | 53 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaErrorHandling.test_database_corruption_resilience` | 24 | 0 |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotErrorHandling.test_get_snapshot_handles_sql_execution_error` | 47 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaIntegration.test_events_table_schema_structure` | 51 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaCompatibility.test_database_file_creation_in_nested_directories` | 51 | 0 |
| `tests.core.test_event_append.TestEventAppendValidation.test_append_validates_event_parameter` | 35 | 0 |
| `tests.core.test_performance_optimization.TestDatabaseIndexes.test_timestamp_index_exists` | 43 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaIntegration.test_unique_constraints` | 51 | 0 |
| `tests.core.test_event_replay.TestEventReplayInputValidation.test_rebuild_projection_requires_projection_builder` | 30 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaIdempotency.test_schema_creation_is_idempotent` | 51 | 0 |
| `tests.core.test_event_query.TestGetEventsErrorHandling.test_get_events_handles_database_errors` | 54 | 0 |
| `tests.core.test_database_connection.TestDatabaseContextManager.test_context_manager_rolls_back_on_exception` | 51 | 0 |
| `tests.core.test_performance_optimization.TestDatabaseIndexes.test_workflow_id_index_exists` | 43 | 0 |
| `tests.core.test_database_schema.TestDatabaseSchemaCompatibility.test_schema_creation_with_string_and_path_objects` | 53 | 0 |
| `tests.core.test_database_connection.TestDatabaseConnectionManagement.test_close_connection_cleanup_and_edge_cases` | 43 | 0 |
| `tests.test_connection_management.TestEventStoreConnectionIntegration.test_separate_event_stores_maintain_independent_data` | 51 | 0 |
| `tests.test_connection_management.TestEventStoreConnectionManagement.test_get_connection_creates_valid_optimized_connection` | 40 | 0 |
| `tests.core.test_database_schema.TestEventStoreInitialization.test_connection_works_after_initialization` | 43 | 0 |
| `tests.core.test_notes_api.TestNotesSQLiteEventSourcing.test_search_finds_matching_notes` | 123 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerFunctionality.test_pause_workflow_sets_waiting_for_response_true` | 60 | 0 |
| `test_notes_api.TestNotesIntegration.test_category_counts_in_tabs` | 104 | 0 |
| `tests.core.test_notes_api.TestNotesSQLiteEventSourcing.test_list_reads_from_sqlite` | 115 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerIntegration.test_pause_workflow_with_real_event_logger` | 66 | 0 |
| `tests.core.test_notes_integration.TestNotesFullIntegration.test_notes_full_flow_integration` | 89 | 0 |
| `tests.test_mailbox_tools.test_ask_user_returns_user_response` | 129 | 0 |
| `tests.orchestration.test_notes_event_emission.TestNoteEventEmission.test_verification_observation_emitted_and_queryable` | 45 | 0 |
| `tests.orchestration.test_notes_event_emission.TestNoteEventEmission.test_multiple_notes_queryable_by_category` | 45 | 0 |
| `tests.orchestration.test_notes_event_emission.TestNoteEventEmission.test_commit_success_accomplishment_emitted` | 45 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerIntegration.test_end_to_end_pause_resume_workflow` | 83 | 0 |
| `tests.orchestration.test_notes_event_emission.TestNoteEventEmission.test_feature_failure_warning_emitted` | 45 | 0 |
| `test_notes_ui.test_category_filtering_data` | 51 | 0 |
| `tests.test_mailbox_tools.test_ask_user_handles_priority_levels` | 129 | 0 |
| `tests.core.test_notes_api.TestNotesConvenienceMethodsSQLite.test_add_todo_writes_to_sqlite` | 95 | 0 |
| `tests.core.test_notes_api.TestNotesConvenienceMethodsSQLite.test_add_accomplishment_writes_to_sqlite` | 95 | 0 |
| `tests.core.test_notes_integration.TestConvenienceMethodsIntegration.test_convenience_methods_emit_events` | 125 | 0 |
| `test_notes_ui.test_notes_panel_data_integrity` | 51 | 0 |
| `test_notes_ui.test_notes_display_metadata` | 51 | 0 |
| `tests.orchestration.test_notes_event_emission.TestNoteEventEmission.test_test_result_observation_emitted` | 45 | 0 |
| `tests.core.test_notes_api.TestNotesConvenienceMethodsSQLite.test_add_learning_writes_to_sqlite` | 95 | 0 |
| `test_notes_api.TestNotesIntegration.test_notes_with_tags_and_metadata` | 104 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerFunctionality.test_resume_workflow_sets_waiting_for_response_false` | 62 | 0 |
| `tests.test_mailbox_tools.test_ask_user_waits_for_outbox_response` | 129 | 0 |
| `tests.core.test_notes_api.TestNotesConvenienceMethodsSQLite.test_add_observation_writes_to_sqlite` | 95 | 0 |
| `tests.core.test_notes_integration.TestNotesFullIntegration.test_multiple_notes_emit_multiple_events` | 89 | 0 |
| `test_notes_api.TestApiNotesEndpoint.test_api_notes_limits_to_50` | 94 | 0 |
| `tests.test_mailbox_tools.test_ask_user_writes_message_to_inbox` | 129 | 0 |
| `tests.core.test_notes_api.TestNotesSQLiteEventSourcing.test_add_note_writes_to_sqlite` | 89 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerIntegration.test_resume_workflow_with_real_event_logger` | 68 | 0 |
| `tests.core.test_notes_api.TestNotesConvenienceMethodsSQLite.test_add_warning_writes_to_sqlite` | 95 | 0 |
| `tests.core.test_notes_integration.TestNotesFullIntegration.test_event_data_completeness` | 89 | 0 |
| `tests.core.test_notes_api.TestNotesSQLiteEventSourcing.test_list_filters_by_category` | 117 | 0 |
| `tests.core.test_notes_api.TestNotesSQLiteEventSourcing.test_list_respects_limit` | 117 | 0 |
| `tests.orchestration.test_notes_event_emission.TestNoteEventEmission.test_verification_warning_emitted_and_queryable` | 45 | 0 |
| `tests.core.test_notes_api.TestNotesSQLiteEventSourcing.test_all_note_categories_emit_correct_event_types` | 89 | 0 |
| `tests.orchestration.test_notes_event_emission.TestNoteEventEmission.test_feature_success_accomplishment_emitted` | 45 | 0 |
| `tests.core.test_notes_integration.TestNotesFullIntegration.test_all_note_categories_integration` | 89 | 0 |
| `tests.core.test_notes_api.TestNotesConvenienceMethodsSQLite.test_add_decision_writes_to_sqlite` | 95 | 0 |
| `test_notes_tools.TestGetNotesSummary.test_get_notes_summary_with_notes` | 169 | 0 |
| `test_notes_tools.TestReadNotes.test_read_notes_with_limit` | 169 | 0 |
| `test_notes_tools.TestReadNotes.test_read_notes_with_category_filter` | 178 | 0 |
| `test_notes_tools.TestSearchNotes.test_search_notes_with_matches` | 172 | 0 |
| `test_notes_tools.TestTakeNote.test_take_note_success` | 121 | 0 |
| `test_notes_tools.TestTakeNote.test_take_note_all_categories` | 120 | 0 |
| `test_notes_tools.TestReadNotes.test_read_notes_after_adding` | 167 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_tags_is_required` | 2 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_agent_id_is_required` | 9 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_creates_with_required_fields` | 9 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_serialization_to_dict_with_none_optionals` | 9 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventDataIntegration.test_can_be_used_as_event_data` | 13 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_creates_with_all_fields` | 13 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventDataIntegration.test_works_with_all_note_event_types` | 9 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_title_is_required` | 9 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_related_file_is_optional_string_or_none` | 14 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_content_is_required` | 9 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_related_feature_is_optional_string_or_none` | 14 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_serialization_to_dict` | 13 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_json_serialization` | 13 | 0 |
| `tests.test_note_event_schema.TestAgentNoteEventData.test_tags_must_be_list_of_strings` | 9 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_init_with_custom_params` | 5 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_execute_commit_success` | 21 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_run_tests_passes` | 11 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_commit_feature_success` | 23 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_extract_commit_sha_from_output` | 7 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_execute_commit_extracts_sha` | 21 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_init_with_defaults` | 4 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_commit_feature_with_feature_context` | 23 | 0 |
| `tests.test_feature_commit_orchestrator.TestFeatureCommitOrchestrator.test_run_tests_fails` | 11 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_jsonl_file_with_unicode` | 10 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_jsonl_file_with_empty_lines` | 11 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_jsonl_file_empty_file` | 5 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_jsonl_file_with_whitespace_only_lines` | 11 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_valid_jsonl_file` | 10 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_jsonl_file_yields_dictionaries` | 10 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_jsonl_file_with_complex_data` | 10 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_jsonl_file_accepts_path_object` | 10 | 0 |
| `tests.test_file_utils.TestReadJsonlFile.test_read_jsonl_file_accepts_string_path` | 10 | 0 |
| `tests.test_git_file_stager.TestGitFileStagerFilterFiles.test_filter_with_feature_context_and_test_files` | 23 | 0 |
| `tests.test_git_file_stager.TestGitFileStagerIntegration.test_full_workflow_and_error_handling` | 41 | 0 |
| `tests.test_git_file_stager.TestGitFileStagerGetModifiedFiles.test_get_modified_files_git_error` | 13 | 0 |
| `tests.test_git_file_stager.TestGitFileStagerFilterFiles.test_filter_excludes_config_and_system_files` | 21 | 0 |
| `tests.test_git_file_stager.TestGitFileStagerGetModifiedFiles.test_get_modified_files_success_and_status_types` | 18 | 0 |
| `tests.test_git_file_stager.TestGitFileStagerAnalyze.test_analyze_returns_filtered_files` | 42 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookNoOps.test_hook_noop_on_unrelated_file_write` | 54 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookIntegration.test_hook_with_absolute_vs_relative_paths` | 57 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookInboxCountUpdate.test_hook_updates_inbox_count_after_reading` | 120 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookInboxWrites.test_hook_creates_inbox_count_if_missing` | 58 | 0 |
| `tests.core.test_mailbox_api.TestMailboxIntegration.test_mailbox_handles_urgent_messages` | 72 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookErrorHandling.test_hook_handles_corrupted_inbox_gracefully` | 34 | 0 |
| `tests.core.test_mailbox_api.TestMailboxSendMessage.test_send_multiple_messages` | 80 | 0 |
| `tests.core.test_mailbox_api.TestMailboxEdgeCases.test_edge_case_behaviors` | 69 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookInboxWrites.test_hook_increments_multiple_times` | 57 | 0 |
| `tests.core.test_mailbox_api.TestMailboxSendMessage.test_send_message_to_inbox_and_outbox` | 64 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookIntegration.test_hook_workflow_with_realistic_workflow_id` | 120 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookIntegration.test_hook_preserves_user_prompt` | 120 | 0 |
| `tests.core.test_mailbox_api.TestMailboxGetMessages.test_get_messages_returns_correct_type_and_order` | 85 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookUnreadMessageSelection.test_hook_only_injects_unread_messages` | 126 | 0 |
| `tests.core.test_mailbox_api.TestMailboxIsolation.test_different_workflows_are_isolated` | 80 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookBasics.test_hook_returns_none_when_unread_count_is_zero` | 79 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookIntegration.test_hook_context_format` | 120 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookNoOps.test_hook_noop_on_outbox_write` | 53 | 0 |
| `tests.core.test_mailbox_api.TestMailboxIntegration.test_mailbox_complete_workflow` | 94 | 0 |
| `tests.core.test_mailbox_api.TestMailboxUnreadCount.test_unread_count_behavior` | 63 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookNoOps.test_hook_noop_on_inbox_count_write` | 54 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookMessageFormatting.test_hook_formats_message_with_subject_and_body` | 120 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookIntegration.test_hook_returns_none_always` | 57 | 0 |
| `tests.core.test_mailbox_api.TestMailboxMarkAsRead.test_mark_as_read_behavior` | 73 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookMessageFormatting.test_hook_formats_multiple_messages_clearly` | 121 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookErrorHandling.test_hook_handles_corrupted_inbox_count_gracefully` | 71 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookBasics.test_hook_returns_none_when_no_messages` | 32 | 0 |
| `tests.core.test_mailbox_api.TestMailboxEdgeCases.test_very_long_message` | 72 | 0 |
| `tests.core.test_mailbox_api.TestMailboxErrorHandling.test_mailbox_handles_corrupted_files_gracefully` | 50 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookIntegration.test_hook_with_realistic_workflow_id` | 57 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookBasics.test_hook_injects_unread_message_as_additional_context` | 120 | 0 |
| `tests.core.test_mailbox_api.TestMailboxGetMessages.test_inbox_and_outbox_are_isolated` | 78 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookMessageFormatting.test_hook_formats_message_with_priority` | 120 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookInboxCountUpdate.test_hook_only_marks_unread_messages_as_read` | 120 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookInboxWrites.test_hook_increments_inbox_count_on_inbox_write` | 57 | 0 |
| `tests.test_mailbox_tools.test_notify_user_writes_message_to_inbox` | 53 | 0 |
| `tests.test_inbox_writer.TestInboxWriterFunctionality.test_write_to_inbox_creates_inbox_directory_and_writes_message` | 28 | 0 |
| `tests.test_inbox_writer.TestInboxWriterCreation.test_inbox_writer_has_write_to_inbox_method` | 10 | 0 |
| `tests.test_inbox_writer.TestInboxWriterCreation.test_inbox_writer_creation_with_string_path` | 10 | 0 |
| `tests.test_mailbox_tools.test_notify_user_does_not_pause_workflow` | 53 | 0 |
| `tests.test_mailbox_tools.test_notify_user_returns_success_confirmation` | 53 | 0 |
| `tests.test_inbox_writer.TestInboxWriterIntegration.test_inbox_writer_multiple_messages_different_agents` | 28 | 0 |
| `tests.test_mailbox_tools.test_ask_user_pauses_workflow` | 63 | 0 |
| `tests.test_inbox_writer.TestInboxWriterIntegration.test_inbox_writer_workflow_blocker_scenario` | 28 | 0 |
| `tests.test_inbox_writer.TestInboxWriterCreation.test_inbox_writer_creation_with_workflow_dir` | 10 | 0 |
| `tests.test_inbox_writer.TestInboxWriterFunctionality.test_write_to_inbox_with_different_message_types_and_priorities` | 28 | 0 |
| `tests.test_inbox_writer.TestInboxWriterIntegration.test_inbox_writer_idempotent_directory_creation` | 28 | 0 |
| `tests.test_inbox_writer.TestInboxWriterFunctionality.test_write_to_inbox_preserves_all_message_fields` | 27 | 0 |
| `tests.test_edit_integration.TestInteractivePromptWithEdit.test_prompt_edit_action_triggers_edit` | 51 | 0 |
| `tests.test_interactive_prompt.TestInteractivePromptHandlerIntegration.test_realistic_warning_scenario` | 50 | 0 |
| `tests.test_interactive_prompt.TestInteractivePromptHandlerInit.test_init_with_and_without_formatter` | 5 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookBasics.test_hook_returns_none_when_messages_not_awaiting_response` | 65 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookIntegration.test_hook_workflow_with_coordinator_workflow_id` | 82 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookMultipleMessages.test_hook_ignores_normal_messages_when_urgent_present` | 81 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookErrorHandling.test_hook_handles_corrupted_outbox_gracefully` | 47 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookIntegration.test_hook_notification_format` | 81 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookBasics.test_hook_returns_none_when_no_messages` | 36 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookUrgentMessages.test_hook_notifies_on_urgent_and_awaiting_response` | 82 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookUrgentMessages.test_hook_includes_message_details` | 81 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookUrgentMessages.test_hook_notifies_on_awaiting_response_message` | 81 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookBasics.test_hook_returns_none_when_only_normal_messages` | 65 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookUrgentMessages.test_hook_notifies_on_urgent_message` | 81 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorPolling.test_poll_for_new_messages_ignores_non_json_files` | 33 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorCreation.test_outbox_monitor_creation_with_workflow_dir` | 10 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorPolling.test_poll_for_new_messages_returns_empty_list_when_outbox_not_exists` | 15 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorIntegration.test_outbox_monitor_polling_after_message_processing` | 33 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorPolling.test_poll_for_new_messages_finds_single_message` | 33 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorIntegration.test_outbox_monitor_multiple_agent_responses_scenario` | 33 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManagerErrorHandling.test_ensure_directories_handles_os_error` | 7 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_ensure_directories_preserves_existing_files` | 9 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_manager_integration_workflow` | 11 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_get_inbox_path_returns_correct_path` | 7 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorValidation.test_poll_for_new_messages_handles_permission_errors` | 15 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorPolling.test_poll_for_new_messages_returns_empty_list_when_outbox_empty` | 21 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_ensure_directories_is_idempotent` | 9 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorIntegration.test_outbox_monitor_user_response_workflow_scenario` | 33 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_mailbox_directory_manager_creation` | 9 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManagerErrorHandling.test_ensure_directories_handles_permission_error` | 7 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorCreation.test_outbox_monitor_has_poll_for_new_messages_method` | 10 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_ensure_directories_creates_workflow_dir_if_not_exists` | 9 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorPolling.test_poll_for_new_messages_finds_multiple_messages` | 33 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_ensure_directories_creates_inbox_and_outbox` | 9 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorCreation.test_outbox_monitor_creation_with_string_path` | 10 | 0 |
| `tests.test_auto_continue_pause.TestAutoContinuePauseLogic.test_auto_continue_skips_when_waiting_for_response_true` | 117 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_mailbox_directory_manager_with_invalid_workflow_dir_raises_error` | 7 | 0 |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_get_outbox_path_returns_correct_path` | 7 | 0 |
| `tests.test_outbox_monitor.TestOutboxMonitorPolling.test_poll_for_new_messages_returns_messages_sorted_by_creation_time` | 32 | 0 |
| `tests.core.test_mailbox_message_models.TestInboxMessageModel.test_inbox_message_creation_from_message` | 13 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedHandler.test_apply_agent_message_acknowledged_preserves_message_immutability` | 46 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedIntegration.test_cross_agent_acknowledgment_isolation` | 68 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedHandler.test_apply_agent_message_acknowledged_preserves_outbox_and_conversation_history` | 59 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedHandler.test_apply_agent_message_completed_preserves_inbox_and_other_outbox_messages` | 85 | 0 |
| `tests.core.test_message_sent_handler.TestAgentMessageSentHandler.test_apply_agent_message_sent_preserves_existing_state` | 46 | 0 |
| `tests.core.test_mailbox_projection_integration.TestMailboxProjectionIntegrationEndToEnd.test_correlation_id_thread_tracking_and_validation` | 201 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedIntegration.test_complete_message_lifecycle_with_acknowledgment` | 86 | 0 |
| `tests.core.test_correlation_tracking.TestCorrelationIdEdgeCases.test_correlation_id_mismatch_in_acknowledgment` | 64 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedIntegration.test_complete_message_lifecycle_with_completion` | 141 | 0 |
| `tests.core.test_correlation_tracking.TestCorrelationIdValidation.test_correlation_id_tracking_across_message_lifecycle` | 137 | 0 |
| `tests.core.test_correlation_tracking.TestCorrelationIdEdgeCases.test_missing_correlation_id_handling` | 33 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedHandler.test_apply_agent_message_acknowledged_marks_matching_message_as_acknowledged` | 33 | 0 |
| `tests.core.test_mailbox_message_models.TestInboxMessageModel.test_inbox_message_acknowledge_method` | 15 | 0 |
| `tests.core.test_mailbox_message_models.TestInboxMessageModel.test_inbox_message_direct_creation` | 2 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedHandler.test_apply_agent_message_acknowledged_with_multiple_matching_messages` | 46 | 0 |
| `tests.core.test_priority_handling.TestPriorityEdgeCases.test_same_priority_different_timestamps` | 27 | 0 |
| `tests.core.test_inbox_filtering.TestInboxFilteringHelpers.test_get_unread_inbox_multiple_same_priority_maintains_stable_order` | 13 | 0 |
| `tests.core.test_mailbox_message_models.TestMessageModelsIntegration.test_serialization_and_deserialization` | 48 | 0 |
| `tests.core.test_message_sent_handler.TestAgentMessageSentIntegration.test_bidirectional_message_flow_simulation` | 56 | 0 |
| `tests.core.test_mailbox_projection_integration.TestMailboxProjectionIntegrationEndToEnd.test_message_filtering_and_retrieval_integration` | 152 | 0 |
| `tests.core.test_correlation_tracking.TestCorrelationIdValidation.test_correlation_id_format_validation` | 33 | 0 |
| `tests.core.test_mailbox_projection_integration.TestMailboxProjectionIntegrationEndToEnd.test_complete_message_lifecycle_sent_to_acknowledged_to_completed` | 137 | 0 |
| `tests.core.test_mailbox_message_models.TestMessageModelsIntegration.test_message_models_with_different_priorities` | 29 | 0 |
| `tests.core.test_mailbox_projection_integration.TestMailboxProjectionIntegrationEndToEnd.test_multi_agent_conversation_flow_with_priority_handling` | 189 | 0 |
| `tests.core.test_mailbox_message_models.TestMessageModelsIntegration.test_message_flow_inbox_to_outbox_to_conversation` | 53 | 0 |
| `tests.core.test_message_sent_handler.TestAgentMessageSentHandler.test_apply_agent_message_sent_preserves_message_timestamps` | 30 | 0 |
| `tests.core.test_mailbox_projection_integration.TestMailboxProjectionIntegrationEndToEnd.test_cross_agent_message_isolation_and_routing` | 68 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedHandler.test_apply_agent_message_acknowledged_handles_already_acknowledged_message` | 48 | 0 |
| `tests.core.test_correlation_tracking.TestCorrelationIdEdgeCases.test_duplicate_correlation_id_in_different_contexts` | 33 | 0 |
| `tests.core.test_message_sent_handler.TestAgentMessageSentHandler.test_apply_agent_message_sent_adds_to_inbox_when_recipient` | 30 | 0 |
| `tests.core.test_message_sent_handler.TestAgentMessageSentHandler.test_apply_agent_message_sent_with_different_message_types_and_priorities` | 33 | 0 |
| `tests.core.test_inbox_filtering.TestInboxFilteringHelpers.test_get_unread_inbox_all_acknowledged_returns_empty_list` | 13 | 0 |
| `tests.core.test_mailbox_projection_integration.TestMailboxProjectionIntegrationEndToEnd.test_state_transitions_and_consistency_validation` | 83 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedHandler.test_apply_agent_message_completed_with_multiple_matching_messages` | 71 | 0 |
| `tests.core.test_outbox_filtering.TestOutboxFilteringHelpers.test_get_pending_outbox_multiple_same_timestamp_maintains_stable_order` | 6 | 0 |
| `tests.core.test_outbox_filtering.TestOutboxFilteringHelpers.test_get_pending_outbox_all_completed_returns_empty_list` | 6 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedHandler.test_apply_agent_message_completed_removes_from_outbox_and_adds_to_conversation_history` | 58 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedIntegration.test_cross_agent_completion_isolation` | 93 | 0 |
| `tests.core.test_mailbox_message_models.TestOutboxMessageModel.test_outbox_message_fail_method` | 16 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedHandler.test_apply_agent_message_completed_preserves_message_immutability` | 71 | 0 |
| `tests.core.test_message_sent_handler.TestAgentMessageSentHandler.test_apply_agent_message_sent_adds_to_outbox_when_sender` | 31 | 0 |
| `tests.core.test_mailbox_message_models.TestOutboxMessageModel.test_outbox_message_direct_creation` | 2 | 0 |
| `tests.core.test_mailbox_message_models.TestOutboxMessageModel.test_outbox_message_creation_from_message` | 13 | 0 |
| `tests.core.test_mailbox_message_models.TestConversationMessageModel.test_conversation_message_creation_from_outbox` | 35 | 0 |
| `tests.core.test_outbox_filtering.TestOutboxFilteringHelpers.test_get_pending_outbox_mixed_priorities_sorted_by_timestamp_only` | 6 | 0 |
| `tests.core.test_mailbox_message_models.TestOutboxMessageModel.test_outbox_message_complete_method` | 16 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedHandler.test_apply_agent_message_completed_handles_failure_result` | 71 | 0 |
| `tests.core.test_mailbox_message_models.TestConversationMessageModel.test_conversation_message_direct_creation` | 2 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_multiple_same_timestamp_maintains_stable_order` | 7 | 0 |
| `tests.core.test_priority_handling.TestPriorityStatistics.test_has_urgent_and_next_priority` | 19 | 0 |
| `tests.core.test_priority_handling.TestPriorityBasedInboxSorting.test_acknowledged_messages_filtered_out` | 13 | 0 |
| `tests.core.test_priority_handling.TestPriorityEdgeCases.test_all_acknowledged_edge_case` | 30 | 0 |
| `tests.core.test_message_reader.TestReadMessagesBasics.test_read_messages_from_inbox_outbox_and_multiple` | 48 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_outbox_path` | 17 | 0 |
| `tests.test_commit_workflow_integration.TestCommitWorkflowIntegration.test_commit_receives_correct_task_metadata` | 219 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_mailbox_path_with_none_raises_valueerror` | 13 | 0 |
| `tests.core.test_message_reader.TestReadMessagesIOErrors.test_uses_resolve_mailbox_path` | 20 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_mailbox_path_with_invalid_type_raises_valueerror` | 13 | 0 |
| `tests.test_commit_workflow_integration.TestCommitWorkflowIntegration.test_multiple_features_each_get_commit` | 220 | 0 |
| `tests.core.test_message_reader.TestReadMessagesValidation.test_read_messages_validates_inputs` | 16 | 0 |
| `tests.test_commit_workflow_integration.TestCommitWorkflowIntegration.test_commit_sha_saved_to_feature_state` | 224 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookErrorHandling.test_hook_handles_invalid_path_gracefully` | 30 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookErrorHandling.test_hook_handles_nonexistent_base_dir_gracefully` | 31 | 0 |
| `tests.core.test_message_reader.TestReadMessagesEdgeCases.test_read_messages_edge_cases` | 43 | 0 |
| `tests.test_commit_workflow_integration.TestCommitWorkflowIntegration.test_commit_not_triggered_on_feature_failure` | 186 | 0 |
| `tests.orchestration.test_post_tool_use_hook_logging.TestPostToolUseHookLogging.test_hook_logs_with_hook_name_in_extra` | 34 | 0 |
| `tests.test_auto_continue_pause.TestAutoContinuePauseLogic.test_auto_continue_continues_when_waiting_for_response_false` | 97 | 0 |
| `tests.core.test_message_reader.TestReadMessagesIntegration.test_read_messages_realistic_workflow` | 48 | 0 |
| `tests.test_commit_workflow_integration.TestCommitWorkflowIntegration.test_commit_triggered_after_feature_completion` | 219 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_mailbox_path_works_with_different_workflows` | 16 | 0 |
| `tests.core.test_message_writer.TestWriteMessagePrioritiesAndFlags.test_write_message_preserves_all_priorities_and_flags` | 24 | 0 |
| `tests.test_commit_workflow_integration.TestCommitWorkflowIntegration.test_commit_failure_does_not_block_workflow` | 221 | 0 |
| `tests.orchestration.test_post_tool_use_hook_logging.TestPostToolUseHookLogging.test_hook_logs_path_resolution_errors` | 30 | 0 |
| `tests.test_commit_workflow_integration.TestCommitWorkflowIntegration.test_commit_orchestrator_initialized_with_repo_path` | 219 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_mailbox_path_consistency` | 19 | 0 |
| `tests.core.test_message_writer.TestWriteMessageJSONLSerialization.test_write_message_jsonl_format_and_field_preservation` | 27 | 0 |
| `tests.core.test_message_writer.TestMessageBoxEnum.test_messagebox_enum_maps_to_correct_paths` | 24 | 0 |
| `tests.core.test_message_writer.TestWriteMessageEdgeCases.test_write_message_edge_cases` | 27 | 0 |
| `tests.core.test_message_reader.TestReadMessagesBasics.test_read_messages_preserves_all_fields` | 43 | 0 |
| `tests.core.test_message_reader.TestReadMessagesReturnType.test_read_messages_returns_list_of_message_objects` | 44 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_inbox_path` | 16 | 0 |
| `tests.orchestration.test_post_tool_use_hook_logging.TestPostToolUseHookLogging.test_hook_does_not_log_when_no_error` | 31 | 0 |
| `tests.core.test_message_reader.TestReadMessagesSpecialCharacters.test_read_messages_with_special_unicode_and_multiline` | 43 | 0 |
| `tests.orchestration.test_auto_continue_integration.test_empty_workflow_completes_immediately` | 136 | 0 |
| `tests.core.test_message_writer.TestWriteMessageIntegration.test_write_message_realistic_workflow` | 27 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_mailbox_path_with_integer_raises_valueerror` | 13 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_mailbox_path_returns_path_object` | 16 | 0 |
| `tests.test_commit_workflow_integration.TestCommitWorkflowIntegration.test_commit_uses_feature_context` | 219 | 0 |
| `tests.test_auto_continue_pause.TestAutoContinuePauseLogic.test_auto_continue_waits_when_no_outbox_response` | 102 | 0 |
| `tests.core.test_projection_bases.TestProjectionBuilderShared.test_initial_state_has_empty_collections` | 9 | 0 |
| `tests.core.test_projection_bases.TestProjectionBuilderShared.test_multiple_calls_return_independent_states` | 9 | 0 |
| `tests.core.test_projection_bases.TestProjectionBuilderShared.test_creates_initial_state_with_correct_keys` | 9 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_returns_all_messages_in_chronological_order` | 5 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_filters_by_agent_sender` | 7 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_mixed_success_and_failure_messages` | 5 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_preserves_original_state` | 5 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_filters_by_agent_recipient` | 7 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_handles_missing_state_keys_gracefully` | 7 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_no_matching_agent_returns_empty_list` | 7 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_empty_history_returns_empty_list` | 7 | 0 |
| `tests.core.test_conversation_history.TestConversationHistoryHelpers.test_get_conversation_filters_by_agent_either_direction` | 7 | 0 |
| `tests.core.test_message_sent_handler.TestAgentMessageSentHandler.test_apply_agent_message_sent_ignores_unrelated_messages` | 13 | 0 |
| `tests.core.test_mailbox_projection_integration.TestMailboxProjectionIntegrationEndToEnd.test_edge_cases_and_error_scenarios` | 48 | 0 |
| `tests.core.test_projection_bases.TestMailboxProjectionBuilderAbstractMethods.test_apply_agent_message_sent_returns_state` | 3 | 0 |
| `tests.core.test_message_sent_handler.TestAgentMessageSentHandler.test_apply_agent_message_sent_handles_missing_fields_gracefully` | 3 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedHandler.test_apply_agent_message_acknowledged_handles_missing_required_fields` | 3 | 0 |
| `tests.core.test_projection_bases.TestMailboxProjectionBuilderAbstractMethods.test_apply_agent_message_acknowledged_returns_state` | 3 | 0 |
| `tests.core.test_message_acknowledgment.TestAgentMessageAcknowledgedHandler.test_apply_agent_message_acknowledged_handles_no_matching_message` | 16 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedHandler.test_apply_agent_message_completed_handles_missing_required_fields` | 3 | 0 |
| `tests.core.test_projection_bases.TestMailboxProjectionBuilderAbstractMethods.test_apply_agent_message_completed_returns_state` | 3 | 0 |
| `tests.core.test_message_completion.TestAgentMessageCompletedHandler.test_apply_agent_message_completed_handles_no_matching_message` | 18 | 0 |
| `tests.core.test_correlation_tracking.TestCorrelationIdThreadTracking.test_get_messages_by_correlation_id` | 18 | 0 |
| `tests.core.test_correlation_tracking.TestCorrelationIdThreadTracking.test_thread_consistency_validation` | 30 | 0 |
| `tests.core.test_inbox_filtering.TestInboxFilteringHelpers.test_get_unread_inbox_preserves_original_state` | 11 | 0 |
| `tests.core.test_inbox_filtering.TestInboxFilteringHelpers.test_get_unread_inbox_sorts_by_priority` | 11 | 0 |
| `tests.core.test_inbox_filtering.TestInboxFilteringHelpers.test_get_unread_inbox_empty_inbox_returns_empty_list` | 11 | 0 |
| `tests.core.test_inbox_filtering.TestInboxFilteringHelpers.test_get_unread_inbox_handles_missing_state_keys_gracefully` | 11 | 0 |
| `tests.core.test_inbox_filtering.TestInboxFilteringHelpers.test_get_unread_inbox_filters_unacknowledged_only` | 11 | 0 |
| `tests.core.test_priority_handling.TestPriorityBasedInboxSorting.test_unread_inbox_sorted_by_priority_then_time` | 11 | 0 |
| `tests.core.test_outbox_filtering.TestOutboxFilteringHelpers.test_get_pending_outbox_empty_outbox_returns_empty_list` | 4 | 0 |
| `tests.core.test_outbox_filtering.TestOutboxFilteringHelpers.test_get_pending_outbox_handles_missing_state_keys_gracefully` | 4 | 0 |
| `tests.core.test_outbox_filtering.TestOutboxFilteringHelpers.test_get_pending_outbox_preserves_original_state` | 4 | 0 |
| `tests.core.test_outbox_filtering.TestOutboxFilteringHelpers.test_get_pending_outbox_filters_uncompleted_only` | 4 | 0 |
| `tests.core.test_outbox_filtering.TestOutboxFilteringHelpers.test_get_pending_outbox_sorts_by_sent_at_timestamp` | 4 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_mailbox_path_with_none_paths_raises_typeerror` | 3 | 0 |
| `tests.test_mailbox_storage.TestResolveMailboxPath.test_resolve_mailbox_path_validates_paths_type` | 4 | 0 |
| `tests.test_response_parser.TestResponseParserIntegration.test_end_to_end_message_body_parsing` | 116 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingAllNoteTypes.test_category_indexing_for_all_note_types` | 210 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_updates_by_category_index` | 35 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingEdgeCases.test_category_indexing_state_immutability` | 35 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingBasics.test_empty_state_has_empty_by_category_index` | 5 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingBasics.test_multiple_categories_create_separate_index_entries` | 94 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_updates_by_agent_index` | 35 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_handles_empty_tags_list` | 32 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingIntegration.test_category_filtering_use_case` | 94 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingEdgeCases.test_category_indexing_preserves_existing_indexes` | 65 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_preserves_original_state_immutability` | 35 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingBasics.test_multiple_notes_same_category_index_correctly` | 35 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_note_contains_timestamp` | 35 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerAllCategories.test_adds_note_to_empty_state_with_correct_category` | 210 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_adds_note_with_minimal_data` | 32 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_updates_by_tag_index` | 35 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingBasics.test_single_note_creates_category_index_entry` | 35 | 0 |
| `tests.core.test_category_indexing.TestCategoryIndexingIntegration.test_complex_category_indexing_scenario` | 123 | 0 |
| `tests.core.test_projection_bases.TestNotesProjectionBuilderSpecific.test_indexes_are_independent_dicts` | 5 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_updates_existing_indexes_correctly` | 29 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerEdgeCases.test_preserves_existing_state_structure` | 30 | 0 |
| `tests.core.test_notes_categories.TestNoteHandlerDetailedBehavior.test_adds_note_to_existing_notes` | 30 | 0 |
| `tests.test_response_parser.TestResponseParserIntegration.test_realistic_user_response_scenarios` | 123 | 0 |
| `tests.test_response_parser.TestResponseParser.test_extract_skip_decisions` | 76 | 0 |
| `tests.test_response_parser.TestResponseParser.test_extract_abort_decisions` | 77 | 0 |
| `tests.test_response_parser.TestResponseParser.test_mixed_content_with_clear_decision` | 90 | 0 |
| `tests.test_response_parser.TestResponseParser.test_case_insensitive_detection` | 85 | 0 |
| `tests.test_response_parser.TestResponseParser.test_extract_continue_decisions` | 78 | 0 |
| `tests.test_response_parser.TestResponseParser.test_multiple_decisions_prioritization` | 82 | 0 |
| `tests.test_response_parser.TestResponseParser.test_decision_confidence_levels` | 89 | 0 |
| `tests.test_response_parser.TestResponseParser.test_extract_fix_decisions` | 75 | 0 |
| `tests.test_response_parser.TestResponseParser.test_extract_additional_context` | 73 | 0 |
| `tests.core.test_sandbox.TestGetSandboxSettings.test_development_workflow` | 2 | 0 |
| `tests.core.test_sandbox.TestGetSandboxSettings.test_readonly_workflow` | 2 | 0 |
| `tests.core.test_sandbox.TestGetSandboxSettings.test_unknown_workflow_falls_back_to_development` | 2 | 0 |
| `tests.core.test_sandbox.TestGetSandboxSettings.test_testing_workflow` | 2 | 0 |
| `tests.core.test_sandbox.TestGetSandboxSettings.test_returns_none_when_disabled` | 2 | 0 |
| `tests.test_database_indexes.TestIndexPerformanceOptimization.test_timestamp_index_improves_range_queries` | 21 | 0 |
| `tests.test_database_indexes.TestIndexPerformanceOptimization.test_combined_query_optimization` | 21 | 0 |
| `tests.test_database_indexes.TestEventStoreIndexCreation.test_creates_all_indexes_together` | 21 | 0 |
| `tests.test_database_indexes.TestEventStoreIndexCreation.test_creates_event_type_index` | 21 | 0 |
| `tests.test_database_indexes.TestIndexPerformanceOptimization.test_workflow_id_index_improves_query_performance` | 21 | 0 |
| `tests.test_database_indexes.TestEventStoreIndexCreation.test_index_creation_is_idempotent` | 21 | 0 |
| `tests.test_database_indexes.TestIndexPerformanceOptimization.test_event_type_index_improves_query_performance` | 21 | 0 |
| `tests.test_database_indexes.TestEventStoreIndexCreation.test_creates_timestamp_index` | 21 | 0 |
| `tests.test_database_indexes.TestEventStoreIndexCreation.test_creates_workflow_id_index` | 21 | 0 |
| `tests.test_database_indexes.TestEventStoreIndexCreation.test_handles_invalid_path_gracefully` | 9 | 0 |
| `tests.test_security.TestValidateCommand.test_readonly_workflow_restricts_writes` | 24 | 0 |
| `tests.test_security.TestRealWorldScenarios.test_dangerous_commands_base_validation` | 24 | 0 |
| `tests.test_security.TestExtractBaseCommand.test_simple_commands_and_paths` | 14 | 0 |
| `tests.test_security.TestExtractBaseCommand.test_env_vars_pipes_and_redirects` | 14 | 0 |
| `tests.test_security.TestValidateCommand.test_custom_allowlist` | 24 | 0 |
| `tests.test_security.TestBashSecurityHook.test_works_with_tool_use_id` | 32 | 0 |
| `tests.test_security.TestValidateCommand.test_development_workflow_allows_common_commands` | 21 | 0 |
| `tests.test_security.TestRealWorldScenarios.test_development_workflows` | 21 | 0 |
| `tests.test_security.TestBashSecurityHook.test_allow_safe_block_unsafe` | 37 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerIntegration.test_resume_workflow_from_test_failure_scenario` | 23 | 0 |
| `tests.orchestration.test_two_agent.test_initializer_uses_correct_model` | 68 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerIntegration.test_multiple_pause_resume_cycle` | 21 | 0 |
| `tests.test_state.TestWorkflowStatePersistence.test_save_load_roundtrip_with_all_fields` | 21 | 0 |
| `tests.orchestration.test_auto_continue.TestInitializeWorkflow.test_initialize_workflow_basic` | 20 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerIntegration.test_resume_workflow_with_unclear_decision` | 23 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerIntegration.test_multiple_pause_resume_cycle` | 23 | 0 |
| `tests.orchestration.test_structured_output.TestInitializerStructuredOutput.test_initializer_sets_output_format` | 67 | 0 |
| `tests.orchestration.test_structured_output.TestInitializerStructuredOutput.test_initializer_parses_clean_json` | 67 | 0 |
| `tests.orchestration.test_two_agent.test_run_initializer_auto_generates_workflow_id` | 68 | 0 |
| `tests.orchestration.test_two_agent.test_run_two_agent_workflow_with_auto_confirm` | 98 | 0 |
| `tests.orchestration.test_two_agent.test_two_agent_workflow_uses_different_models` | 91 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerIntegration.test_pause_workflow_blocker_detected_scenario` | 21 | 0 |
| `tests.orchestration.test_auto_continue.TestInitializeWorkflow.test_initialize_workflow_saves_state` | 25 | 0 |
| `tests.test_state.TestWorkflowStatePersistence.test_json_serialization_structure` | 9 | 0 |
| `tests.test_status_command.TestStatusHelperFunctions.test_find_most_recent_and_get_all_workflows` | 46 | 0 |
| `tests.orchestration.test_two_agent.test_run_initializer_success` | 67 | 0 |
| `tests.test_verification.TestWorkflowStateVerification.test_workflow_state_verification_methods` | 12 | 0 |
| `tests.test_state.TestWorkflowState.test_get_summary_with_beads_fields` | 25 | 0 |
| `tests.test_state.TestWorkflowState.test_progress_and_completion` | 11 | 0 |
| `tests.test_state.TestWorkflowStatePersistence.test_backward_compatibility_old_state_files` | 5 | 0 |
| `tests.test_state.TestWorkflowStatePersistence.test_load_nonexistent_workflow` | 3 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_with_multiple_workflows_sorted_by_updated_at` | 16 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_missing_state_json_files` | 17 | 0 |
| `tests.test_dashboard.TestDashboardTemplates.test_dashboard_includes_tailwind` | 48 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_skips_directories_without_state_json` | 17 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_prefers_events_over_state_same_workflow` | 30 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_skips_non_directory_files` | 17 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_with_only_workflow_dir` | 25 | 0 |
| `tests.test_dashboard.TestDashboardApp.test_root_returns_html` | 48 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_edge_case_workflow_names` | 16 | 0 |
| `tests.test_dashboard.TestDashboardApp.test_root_contains_dashboard_elements` | 48 | 0 |
| `tests.test_dashboard.TestDashboardApp.test_api_workflows_returns_list` | 19 | 0 |
| `tests.test_dashboard.TestDashboardWorkflowView.test_workflow_selector_shows_all_workflows` | 19 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_with_both_files` | 30 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_return_type` | 16 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_mixed_valid_and_invalid_workflows` | 19 | 0 |
| `tests.test_dashboard.TestDashboardTemplates.test_dashboard_shows_features` | 52 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_with_single_workflow` | 16 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_with_state_file` | 25 | 0 |
| `tests.test_dashboard_app.TestDashboardAppRefactoring.test_dashboard_uses_refactored_get_all_workflows` | 38 | 0 |
| `tests.test_dashboard.TestDashboardTemplates.test_dashboard_shows_workflow_title` | 52 | 0 |
| `tests.test_dashboard_app.TestDashboardAppRefactoring.test_api_workflows_returns_sorted_dict_list` | 21 | 0 |
| `tests.test_dashboard.TestDashboardTemplates.test_dashboard_includes_htmx` | 48 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_handles_io_errors_gracefully` | 18 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_corrupted_json_files_multiple_scenarios` | 18 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_skips_corrupted_json_files` | 18 | 0 |
| `tests.test_dashboard.TestDashboardWorkflowView.test_can_view_specific_workflow` | 52 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_handles_corrupted_state_file` | 27 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_non_directories_in_agents_folder` | 18 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_multiple_workflows` | 30 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_permission_errors_handling` | 18 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_large_number_of_workflows` | 16 | 0 |
| `tests.test_task_validator.TestValidationResult.test_validation_result_defaults_and_methods` | 6 | 0 |
| `tests.test_task_validator.TestTaskValidatorInit.test_init_with_defaults_and_custom` | 1 | 0 |
| `tests.test_detectors.TestFailureDetector.test_realistic_agent_failure_scenario` | 95 | 0 |
| `tests.test_detectors.TestFailureDetector.test_extract_test_failure_details` | 66 | 0 |
| `tests.test_detectors.TestFailureDetector.test_mixed_content_with_test_failures` | 59 | 0 |
| `tests.test_test_runner_validator.TestTestRunnerValidatorIntegration.test_full_validation_workflow` | 68 | 0 |
| `tests.test_test_runner_validator.TestTestRunnerValidatorParseOutput.test_parse_output_extracts_failed_test_names` | 27 | 0 |
| `tests.test_test_runner_validator.TestTestRunnerValidatorValidate.test_validate_success_and_failure` | 68 | 0 |
| `tests.test_test_runner_validator.TestTestRunnerValidatorRunTests.test_run_tests_returns_correct_result` | 19 | 0 |
| `tests.test_test_runner_validator.TestTestRunnerValidatorCustomCommands.test_various_test_commands` | 19 | 0 |
| `tests.test_verification.TestParseFailedTests.test_parse_failed_tests_all_cases` | 8 | 0 |
| `tests.test_workflow_event.TestWorkflowEventValidation.test_data_field_is_required` | 2 | 0 |
| `tests.test_json_serialization.TestWorkflowEventJSONSerialization.test_workflow_event_custom_json_encoders` | 2 | 0 |
| `tests.test_json_serialization.TestWorkflowEventJSONSerialization.test_workflow_event_deserialize_from_json_string` | 2 | 0 |
| `tests.test_json_serialization.TestWorkflowEventJSONSerialization.test_workflow_event_uuid_serialized_as_string` | 2 | 0 |
| `tests.test_json_serialization.TestWorkflowEventJSONSerialization.test_workflow_event_serializes_to_json` | 2 | 0 |
| `tests.test_workflow_event.TestWorkflowEventDataTypes.test_timestamp_is_datetime` | 2 | 0 |
| `tests.test_json_serialization.TestWorkflowEventJSONSerialization.test_workflow_event_datetime_serialized_as_iso_format` | 2 | 0 |
| `tests.test_workflow_event.TestWorkflowEventValidation.test_event_type_required` | 3 | 0 |
| `tests.test_workflow_event.TestWorkflowEventCreation.test_create_workflow_event_with_all_fields` | 2 | 0 |
| `tests.test_workflow_event.TestWorkflowEventCreation.test_create_workflow_event_with_auto_generated_fields` | 2 | 0 |
| `tests.test_json_serialization.TestWorkflowEventJSONSerialization.test_workflow_event_roundtrip_serialization` | 2 | 0 |
| `tests.test_workflow_event.TestWorkflowEventValidation.test_workflow_id_required` | 3 | 0 |
| `tests.test_workflow_event.TestWorkflowEventCreation.test_create_workflow_event_minimal` | 2 | 0 |
| `tests.test_workflow_event.TestWorkflowEventValidation.test_event_type_cannot_be_whitespace_only` | 3 | 0 |
| `tests.test_workflow_event.TestWorkflowEventImmutability.test_workflow_event_is_immutable` | 2 | 0 |
| `tests.test_workflow_event.TestWorkflowEventValidation.test_workflow_id_cannot_be_whitespace_only` | 3 | 0 |
| `tests.test_workflow_event.TestWorkflowEventImmutability.test_data_dict_mutability_note` | 2 | 0 |
| `tests.test_json_serialization.TestWorkflowEventJSONSerialization.test_workflow_event_data_field_preserved_in_json` | 2 | 0 |
| `tests.test_json_serialization.TestWorkflowEventJSONSerialization.test_workflow_event_to_dict_preserves_types` | 2 | 0 |
| `tests.test_workflow_event.TestWorkflowEventDataTypes.test_data_is_dict` | 2 | 0 |
| `tests.test_workflow_event.TestWorkflowEventDataTypes.test_event_id_is_uuid` | 2 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerValidation.test_pause_workflow_handles_save_errors_gracefully` | 8 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerFunctionality.test_pause_workflow_preserves_other_state_fields` | 15 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerCreation.test_pause_handler_creation_with_project_root` | 3 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerCreation.test_pause_handler_has_pause_workflow_method` | 3 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerFunctionality.test_pause_workflow_with_different_pause_reasons` | 15 | 0 |
| `tests.test_workflow_pause_handler.TestWorkflowPauseHandlerFunctionality.test_pause_workflow_logs_pause_event_to_events_jsonl` | 15 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerFunctionality.test_resume_workflow_preserves_other_state_fields` | 17 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerCreation.test_resume_handler_has_resume_workflow_method` | 3 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerFunctionality.test_resume_workflow_logs_resume_event_to_events_jsonl` | 17 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerValidation.test_resume_workflow_handles_save_errors_gracefully` | 7 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerFunctionality.test_resume_workflow_with_different_decision_types` | 17 | 0 |
| `tests.test_workflow_resume_handler.TestWorkflowResumeHandlerCreation.test_resume_handler_creation_with_project_root` | 3 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_with_no_agents_directory` | 3 | 0 |
| `tests.test_get_all_workflows.TestGetAllWorkflows.test_get_all_workflows_with_empty_agents_directory` | 6 | 0 |
| `tests.test_dashboard_app.TestDashboardAppRefactoring.test_get_all_workflows_handles_empty_agents_dir` | 42 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_empty_agents_directory` | 6 | 0 |
| `tests.test_dashboard_app.TestDashboardAppRefactoring.test_get_all_workflows_handles_missing_agents_dir` | 39 | 0 |
| `tests.test_workflow_utils_edge_cases.TestGetAllWorkflowsEdgeCases.test_missing_agents_directory` | 3 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_no_workflows` | 5 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_with_events_file` | 22 | 0 |
| `tests.test_workflow_utils.test_find_most_recent_workflow_no_agents_directory` | 3 | 0 |
| `test_notes_api.TestPartialNotesEndpoint.test_partial_notes_shows_category_tabs` | 59 | 0 |
| `test_notes_api.TestApiNotesEndpoint.test_api_notes_returns_all_notes` | 49 | 0 |
| `test_notes_api.TestPartialNotesEndpoint.test_partial_notes_includes_emojis` | 59 | 0 |
| `tests.test_dashboard_app.TestDashboardAppRefactoring.test_dashboard_app_calls_workflow_utils_function` | 36 | 0 |
| `test_notes_api.TestPartialNotesEndpoint.test_partial_notes_renders_html` | 59 | 0 |
| `tests.orchestration.test_auto_continue.TestBuildFeaturePrompt.test_build_feature_prompt_basic` | 16 | 0 |
| `tests.orchestration.test_auto_continue.TestBuildFeaturePrompt.test_build_feature_prompt_without_test_file` | 16 | 0 |
| `tests.orchestration.test_auto_continue.TestBuildFeaturePrompt.test_build_feature_prompt_includes_warnings` | 16 | 0 |
| `tests.orchestration.test_auto_continue_notes.TestBuildNotesContext.test_limits_to_15_notes` | 43 | 0 |
| `tests.orchestration.test_auto_continue_notes.TestBuildNotesContext.test_no_events_db` | 5 | 0 |
| `tests.orchestration.test_auto_continue_notes.TestBuildNotesContext.test_formats_notes_from_events` | 43 | 0 |
| `tests.orchestration.test_post_tool_use_hook_logging.TestPostToolUseHookLogging.test_hook_logs_exception_with_exc_info` | 19 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookBasics.test_hook_returns_none_when_file_path_missing` | 9 | 0 |
| `tests.orchestration.test_post_tool_use_hook.TestPostToolUseHookErrorHandling.test_hook_handles_permission_errors_gracefully` | 9 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookErrorHandling.test_hook_handles_empty_context_gracefully` | 5 | 0 |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookErrorHandling.test_hook_handles_missing_workflow_id_gracefully` | 5 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookErrorHandling.test_hook_handles_empty_context_gracefully` | 5 | 0 |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookErrorHandling.test_hook_handles_missing_workflow_id_gracefully` | 5 | 0 |
| `tests.test_mailbox_tools.test_set_workflow_context_stores_values` | 3 | 0 |
| `test_notes_tools_security.TestErrorSanitization.test_sanitize_generic_exception` | 4 | 0 |
| `test_notes_tools_security.TestErrorSanitization.test_sanitize_os_error` | 4 | 0 |
| `test_notes_tools_security.TestErrorSanitization.test_sanitize_type_error` | 3 | 0 |
| `test_notes_tools_security.TestErrorSanitization.test_sanitize_value_error` | 3 | 0 |
| `test_notes_tools_security.TestErrorSanitization.test_sanitize_permission_error` | 4 | 0 |
| `test_notes_tools_security.TestErrorSanitization.test_sanitize_does_not_leak_stack_traces` | 4 | 0 |

## Low-Unique Tests (<10% unique)

| Test | Lines Covered | Unique Lines | Unique % |
|------|--------------|-------------|----------|
| `tests.core.test_event_replay.TestEventReplayEdgeCases.test_rebuild_projection_handles_projection_builder_errors` | 185 | 1 | 0.5% |
| `tests.test_work_command.TestWorkEventEmission.test_work_emits_workflow_events` | 147 | 1 | 0.7% |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookIntegration.test_hook_with_mixed_priority_messages` | 122 | 1 | 0.8% |
| `tests.core.test_notes_api.TestNotesSQLiteEventSourcing.test_list_filters_by_agent_id` | 116 | 1 | 0.9% |
| `tests.test_detectors.TestErrorDetector.test_realistic_agent_error_scenario` | 110 | 1 | 0.9% |
| `tests.core.test_event_replay.TestEventReplayEdgeCases.test_rebuild_projection_invalid_workflow_id` | 98 | 1 | 1.0% |
| `tests.test_test_runner_validator.TestTestRunnerValidatorValidate.test_validate_edge_cases` | 82 | 1 | 1.2% |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookMultipleMessages.test_hook_handles_multiple_urgent_messages` | 81 | 1 | 1.2% |
| `tests.test_detectors.TestErrorDetector.test_extract_error_details` | 70 | 1 | 1.4% |
| `tests.test_detectors.TestAmbiguityDetector.test_extract_ambiguity_details` | 69 | 1 | 1.4% |
| `tests.test_logs_command.TestLogsCommandOutput.test_logs_limit_option` | 64 | 1 | 1.6% |
| `tests.test_status_command.TestStatusCommand.test_status_verbose_flag` | 61 | 1 | 1.6% |
| `test_notes_api.TestPartialNotesEndpoint.test_partial_notes_filters_by_category` | 60 | 1 | 1.7% |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_with_json_output` | 59 | 1 | 1.7% |
| `tests.test_task_validator.TestTaskValidatorDescriptionLength.test_description_length_validation` | 54 | 1 | 1.9% |
| `tests.test_interactive_prompt.TestInteractivePromptHandlerEdgeCases.test_prompt_handles_various_validation_states` | 51 | 1 | 2.0% |
| `tests.test_interactive_prompt.TestInteractivePromptHandlerCustomFormatter.test_prompt_uses_custom_formatter` | 50 | 1 | 2.0% |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorParseDiff.test_parse_handles_empty_and_complex_diffs` | 44 | 1 | 2.3% |
| `tests.orchestration.test_auto_continue_notes.TestBuildNotesContext.test_includes_related_file_if_present` | 44 | 1 | 2.3% |
| `tests.orchestration.test_auto_continue_notes.TestBuildNotesContext.test_truncates_long_content` | 44 | 1 | 2.3% |
| `tests.test_logs_command.TestLogsCommandOutput.test_logs_json_output` | 37 | 1 | 2.7% |
| `tests.orchestration.test_subagent_stop_hook.TestSubagentStopHookErrorHandling.test_hook_handles_missing_base_dir_gracefully` | 37 | 1 | 2.7% |
| `tests.test_spec_generation.TestGenerateSpecIntegration.test_generate_spec_from_json_to_spec` | 36 | 1 | 2.8% |
| `test_notes_api.TestApiNotesEndpoint.test_api_notes_empty_when_no_events_db` | 36 | 1 | 2.8% |
| `test_notes_api.TestPartialNotesEndpoint.test_partial_notes_shows_empty_state` | 36 | 1 | 2.8% |
| `tests.orchestration.test_user_prompt_submit_hook.TestUserPromptSubmitHookErrorHandling.test_hook_handles_missing_base_dir_gracefully` | 33 | 1 | 3.0% |
| `tests.orchestration.test_two_agent.test_run_initializer_empty_features` | 29 | 1 | 3.4% |
| `tests.core.test_message_writer.TestWriteMessageBasics.test_write_message_to_inbox_outbox_creates_dir_and_appends` | 28 | 1 | 3.6% |
| `tests.core.test_message_reader.TestReadMessagesEmptyAndMissing.test_read_messages_handles_missing_empty_and_whitespace_files` | 28 | 1 | 3.6% |
| `test_notes_tools.TestGetNotesSummary.test_get_notes_summary_empty` | 28 | 1 | 3.6% |
| `tests.orchestration.test_two_agent.test_run_initializer_missing_features_key` | 28 | 1 | 3.6% |
| `tests.test_detectors.TestAmbiguityDetector.test_edge_cases_and_false_positives` | 23 | 1 | 4.3% |
| `tests.test_detectors.TestAmbiguityDetector.test_no_ambiguity_detected` | 23 | 1 | 4.3% |
| `tests.test_detectors.TestErrorDetector.test_no_errors_detected` | 23 | 1 | 4.3% |
| `tests.test_database_indexes.TestEventStoreIndexCreation.test_accepts_path_object_and_string` | 23 | 1 | 4.3% |
| `tests.test_detectors.TestFailureDetector.test_edge_cases_and_false_positives` | 23 | 1 | 4.3% |
| `tests.test_detectors.TestFailureDetector.test_no_test_failures_detected` | 23 | 1 | 4.3% |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_with_description_argument_works` | 22 | 1 | 4.5% |
| `tests.test_commit_message_formatter.TestCommitMessageFormatter.test_commit_without_scope` | 22 | 1 | 4.5% |
| `tests.test_state.TestWorkflowState.test_feature_lifecycle` | 21 | 1 | 4.8% |
| `tests.cli.commands.test_workflow_error_handling.TestWorkflowCommandFileReadErrorHandling.test_workflow_with_description_argument_works` | 20 | 1 | 5.0% |
| `tests.test_dashboard.TestDashboardApp.test_api_events_returns_events` | 18 | 1 | 5.6% |
| `tests.test_streaming.test_stream_output_empty` | 16 | 1 | 6.2% |
| `tests.core.test_event_models.TestEventModel.test_event_field_validation` | 16 | 1 | 6.2% |
| `tests.test_security.TestExtractBaseCommand.test_edge_cases` | 16 | 1 | 6.2% |
| `tests.test_git_file_stager.TestGitFileStagerExclusionPatterns.test_is_excluded` | 14 | 1 | 7.1% |
| `tests.orchestration.test_auto_continue_notes.TestBuildNotesContext.test_no_notes_in_events` | 14 | 1 | 7.1% |
| `tests.test_database_indexes.TestEventStoreIndexCreation.test_handles_database_without_schema_gracefully` | 12 | 1 | 8.3% |
| `tests.test_mailbox_directory_manager.TestMailboxDirectoryManager.test_mailbox_directory_manager_creation_with_string_path` | 11 | 1 | 9.1% |
| `test_notes_tools.TestIntegration.test_full_workflow` | 230 | 2 | 0.9% |
| `tests.core.test_event_subscription.TestSubscriptionErrorHandling.test_callback_errors_dont_prevent_storage_or_other_callbacks` | 110 | 2 | 1.8% |
| `tests.test_logs_command.TestLogsCommandFiltering.test_logs_since_accepts_various_formats` | 79 | 2 | 2.5% |
| `tests.test_status_command.TestStatusCommand.test_status_handles_missing_and_malformed_events` | 73 | 2 | 2.7% |
| `tests.core.test_error_handling.TestTransactionConflicts.test_append_rolls_back_on_commit_failure` | 72 | 2 | 2.8% |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotErrorHandling.test_get_snapshot_handles_json_deserialization_error` | 70 | 2 | 2.9% |
| `tests.core.test_error_handling.TestErrorMessages.test_error_messages_include_database_path_and_context` | 65 | 2 | 3.1% |
| `tests.test_logs_command.TestLogsCommandEdgeCases.test_logs_malformed_event_line` | 62 | 2 | 3.2% |
| `tests.test_conventional_commit_parser.TestConventionalCommitParserTypes.test_parse_commit_types` | 60 | 2 | 3.3% |
| `tests.core.test_snapshot_save.TestSaveSnapshotValidation.test_validates_snapshot_parameter` | 53 | 2 | 3.8% |
| `test_notes_api.TestApiNotesEndpoint.test_api_notes_filters_by_category` | 51 | 2 | 3.9% |
| `tests.core.test_message_reader.TestReadMessagesCorruptedData.test_read_messages_handles_corrupted_and_invalid_json` | 50 | 2 | 4.0% |
| `tests.test_security.TestBashSecurityHook.test_respects_context` | 40 | 2 | 5.0% |
| `tests.test_connection_management.TestEventStoreErrorHandling.test_readonly_database_still_readable` | 39 | 2 | 5.1% |
| `tests.core.test_event_replay.TestEventReplayInputValidation.test_rebuild_projection_validates_projection_builder_type` | 38 | 2 | 5.3% |
| `tests.core.test_event_subscription.TestEventStoreSubscription.test_subscribe_returns_unique_ids_and_validates` | 37 | 2 | 5.4% |
| `tests.core.test_event_replay.TestEventReplayInputValidation.test_rebuild_projection_validates_workflow_id_type` | 34 | 2 | 5.9% |
| `tests.test_test_runner_validator.TestTestRunnerValidatorParseOutput.test_parse_output_various_formats` | 33 | 2 | 6.1% |
| `tests.core.test_notes_categories.TestNoteHandlerEdgeCases.test_handles_malformed_state_gracefully` | 32 | 2 | 6.2% |
| `tests.test_logs_command.TestLogsCommandEdgeCases.test_logs_empty_events_file` | 30 | 2 | 6.7% |
| `tests.orchestration.test_two_agent.test_run_initializer_invalid_json` | 28 | 2 | 7.1% |
| `tests.test_commit_body_generator.TestCommitBodyGeneratorFormatBullets.test_format_bullets_for_all_change_types` | 27 | 2 | 7.4% |
| `tests.core.test_message_reader.TestReadMessagesIOErrors.test_handles_io_errors_gracefully` | 24 | 2 | 8.3% |
| `tests.core.test_event_query.TestGetEventsBasicAndFiltering.test_get_events_filters_by_workflow_and_event_type` | 136 | 3 | 2.2% |
| `tests.test_work_command.TestBeadsStatusLifecycle.test_work_handles_status_update_failure_gracefully` | 133 | 3 | 2.3% |
| `tests.core.test_event_append.TestEventAppendTransactions.test_append_uses_transaction_commit_on_success` | 85 | 3 | 3.5% |
| `tests.test_detectors.TestErrorDetector.test_detects_all_error_patterns` | 73 | 3 | 4.1% |
| `tests.test_interactive_prompt.TestInteractivePromptHandlerInvalidInput.test_prompt_reprompts_on_invalid_input` | 58 | 3 | 5.2% |
| `tests.core.test_snapshot_retrieve.TestGetSnapshotValidation.test_get_snapshot_validates_workflow_id_parameter` | 36 | 3 | 8.3% |
| `tests.test_dashboard.TestDashboardSSE.test_sse_endpoint_returns_404_for_missing_workflow` | 36 | 3 | 8.3% |
| `tests.core.test_category_indexing.TestCategoryIndexingEdgeCases.test_category_indexing_handles_missing_state_keys` | 33 | 3 | 9.1% |
| `tests.test_mailbox_tools.test_ask_user_handles_timeout_gracefully` | 129 | 4 | 3.1% |
| `tests.core.test_priority_handling.TestPriorityEdgeCases.test_empty_state_edge_cases` | 78 | 4 | 5.1% |
| `tests.test_interactive_prompt.TestInteractivePromptHandlerPromptReturns.test_prompt_returns_correct_action` | 60 | 4 | 6.7% |
| `tests.test_commit_error_handler.TestCommitErrorHandlerGitErrors.test_handle_git_error_categorization` | 55 | 4 | 7.3% |
| `tests.test_conventional_commit_parser.TestConventionalCommitParserIntegration.test_multiple_scopes_and_scope_mapping` | 64 | 5 | 7.8% |
| `tests.core.test_event_subscription.TestSubscriptionManagement.test_unsubscribe_and_selective_unsubscribe` | 106 | 6 | 5.7% |
| `tests.test_detectors.TestAmbiguityDetector.test_detects_all_ambiguity_patterns` | 74 | 6 | 8.1% |
| `tests.test_status_command.TestStatusCommand.test_status_no_workflows_and_specific_workflow` | 71 | 6 | 8.5% |
| `tests.orchestration.test_two_agent.test_run_two_agent_workflow_user_cancellation` | 81 | 7 | 8.6% |
| `tests.test_detectors.TestFailureDetector.test_detects_all_failure_patterns` | 73 | 7 | 9.6% |
| `tests.test_status_command.TestStatusCommand.test_status_feature_progress_and_icons` | 72 | 7 | 9.7% |
| `tests.test_auto_continue_pause.TestAutoContinuePauseLogic.test_auto_continue_checks_outbox_for_response` | 117 | 11 | 9.4% |
| `tests.test_work_command.TestWorkflowIntegration.test_show_plan_without_approval_skips_workflow` | 126 | 12 | 9.5% |

## Module Priority

Files with the most zero-unique test coverage (best consolidation targets):

| Test File | Zero-Unique Tests |
|-----------|------------------|
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_error_message_includes_file_path` | 1 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_displays_rich_formatted_error_on_permission_error` | 1 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_does_not_continue_after_read_error` | 1 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_handles_permission_error_on_spec_read` | 1 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_handles_os_error_on_spec_read` | 1 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_displays_rich_formatted_error_on_os_error` | 1 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_aborts_on_os_error` | 1 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_succeeds_when_no_read_error` | 1 |
| `tests.cli.commands.test_initialize_error_handling.TestInitializeCommandFileReadErrorHandling.test_initialize_aborts_on_permission_error` | 1 |
| `tests.test_logs_command.TestLogsCommandFiltering.test_logs_since_filters_by_time` | 1 |
| `tests.test_logs_command.TestLogsCommandBasic.test_logs_shows_event_data` | 1 |
| `tests.test_logs_command.TestLogsCommandOutput.test_logs_tail_shows_recent_first` | 1 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_with_filtering` | 1 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_shows_logs_from_multiple_workflows` | 1 |
| `tests.test_logs_command.TestLogsCommandBasic.test_logs_formats_timestamp` | 1 |
| `tests.test_logs_command.TestLogsCommandFiltering.test_logs_level_error_shows_only_errors` | 1 |
| `tests.test_logs_command.TestLogsCommandBasic.test_logs_shows_recent_events` | 1 |
| `tests.test_logs_command.TestLogsCommandBasic.test_logs_shows_most_recent_workflow_by_default` | 1 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_with_no_workflows` | 1 |
| `tests.test_logs_command.TestLogsCommandRefactor.test_logs_all_uses_get_all_workflows_function` | 1 |
