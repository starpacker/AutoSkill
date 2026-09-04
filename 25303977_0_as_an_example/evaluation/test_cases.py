assert abs(substitution_ratios['Others'].sum() - 19.924578840910613) < 1e-8

assert abs(substitution_ratios['A>C'].sum() - 0.34981164110408886) < 1e-8


assert abs(substitution_ratios['C>T'].sum() - 14.54864891595078) < 1e-8


assert abs(substitution_ratios['C>G'].sum() - 0.7529763077579285) < 1e-8


assert abs(substitution_ratios['C>A'].sum() - 1.1911024470062916) < 1e-8
