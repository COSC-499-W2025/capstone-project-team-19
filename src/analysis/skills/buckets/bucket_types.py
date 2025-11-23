from dataclasses import dataclass, field

@dataclass
class SkillBucket:
    name: str
    total_signals: int
    description: str
    detectors: list[str] = field(default_factory=list)
    
@dataclass
class TextSkillBucket:
    name: str
    description: str
    detectors: list[str] = field(default_factory=list)