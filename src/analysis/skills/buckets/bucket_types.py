from dataclasses import dataclass, field

@dataclass
class SkillBucket:
    name: str
    total_signals: int
    description: str
    detectors: list[str] = field(default_factory=list)
    weights: dict[str, float] = field(default_factory=dict)  # +1 for positive signals, -1 for negative
    
@dataclass
class TextSkillBucket:
    name: str
    description: str
    detectors: list[str] = field(default_factory=list)