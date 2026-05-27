from pathlib import Path


TOOL = Path(__file__).with_name("tool.py").read_text(encoding="utf-8")


def test_parent_body_observer_is_disconnected_after_message_attach():
    assert "var outerMo = null;" in TOOL
    assert "outerMo.disconnect();" in TOOL


def test_poll_timer_is_cleared_on_finalize():
    assert "var pollTimer = null;" in TOOL
    assert "clearInterval(pollTimer);" in TOOL


def test_tick_work_is_coalesced_and_throttled():
    assert "scheduleTick(" in TOOL
    assert "TICK_MIN_INTERVAL" in TOOL
    assert "tickScheduled" in TOOL


def test_marker_hiding_runs_synchronously_in_mutation_observers():
    assert "function hideMarkerRangeNow()" in TOOL
    assert "hideMarkerRangeNow();" in TOOL
    assert "function scheduleHideMarkerRange()" not in TOOL


def test_marker_hiding_can_run_after_finalize_for_late_dom_flushes():
    assert "function stripFinalizeArtifacts() {" in TOOL
    assert "hideMarkerRange(true);" in TOOL
    assert "hideScheduled" not in TOOL
    assert "if (hideScheduled || finalized) return;" not in TOOL


def test_stable_timeout_without_end_does_not_permanently_finalize():
    assert "function softRenderIncomplete(raw)" in TOOL
    assert "softRenderIncomplete(latest);" in TOOL
    assert "if (isBlockClosed() || latest === raw)" not in TOOL


def test_finalize_rebuilds_render_area_from_clean_dom():
    assert "function resetRenderAreaForFinalPaint()" in TOOL
    assert "resetRenderAreaForFinalPaint();" in TOOL
    assert "renderArea.textContent = '';" in TOOL


def test_inner_observer_reattaches_when_message_dom_is_replaced():
    assert "var innerMoTarget = null;" in TOOL
    assert "innerMoTarget === msg" in TOOL
    assert "innerMoTarget = msg;" in TOOL


def test_single_tick_uses_text_snapshot_cache():
    assert "var tickCache = null;" in TOOL
    assert "function beginTickCache()" in TOOL
    assert "function endTickCache()" in TOOL


if __name__ == "__main__":
    tests = [
        test_parent_body_observer_is_disconnected_after_message_attach,
        test_poll_timer_is_cleared_on_finalize,
        test_tick_work_is_coalesced_and_throttled,
        test_marker_hiding_runs_synchronously_in_mutation_observers,
        test_marker_hiding_can_run_after_finalize_for_late_dom_flushes,
        test_stable_timeout_without_end_does_not_permanently_finalize,
        test_finalize_rebuilds_render_area_from_clean_dom,
        test_inner_observer_reattaches_when_message_dom_is_replaced,
        test_single_tick_uses_text_snapshot_cache,
    ]
    for test in tests:
        test()
    print(f"{len(tests)} runtime guard tests passed")
