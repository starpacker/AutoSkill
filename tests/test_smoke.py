from skill_selector_v10.selector import SmartSelectorV10


def test_v10_selector_constructs_without_private_runtime():
    selector = SmartSelectorV10()
    assert selector.cfg.same_type_threshold == -0.15
