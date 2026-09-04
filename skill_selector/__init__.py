from .base import SkillSelector
from .similarity_selector import SimilaritySelector
from .smart_selector import SmartSelector
from .smart_selector_v6 import SmartSelectorV6
from .smart_selector_v7 import SmartSelectorV7
from .smart_selector_v8 import SmartSelectorV8
from .pipeline import SkillTransferPipeline

# V10 is the current SOTA — import from the standalone package
# (the old smart_selector_v10.py on the server is a thin wrapper)
try:
    from skill_selector_v10 import SmartSelectorV10
except ImportError:
    SmartSelectorV10 = None

__all__ = [
    'SkillSelector', 'SimilaritySelector', 'SmartSelector',
    'SmartSelectorV6', 'SmartSelectorV7', 'SmartSelectorV8',
    'SmartSelectorV10', 'SkillTransferPipeline',
]