from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class Identifiers:
    pgp: List[str] = field(default_factory=list)
    wallets: List[str] = field(default_factory=list)
    emails: List[str] = field(default_factory=list)
    aliases: List[str] = field(default_factory=list)

@dataclass
class Stylometry:
    language: str = "en"
    document_count: int = 0
    avg_sentence_length: Optional[float] = None
    vocabulary_diversity: Optional[float] = None
    punctuation_rate: Optional[float] = None
    function_word_frequency: Dict[str, float] = field(default_factory=dict)
    phrase_features: Dict[str, float] = field(default_factory=dict)

@dataclass
class Activity:
    posting_hours: List[int] = field(default_factory=list)
    weekday_distribution: Dict[str, float] = field(default_factory=dict)
    activity_frequency: Dict[str, Any] = field(default_factory=dict)

@dataclass
class Infrastructure:
    tls_fingerprints: List[str] = field(default_factory=list)
    sanitized_network_fingerprints: List[str] = field(default_factory=list)
    hosting_identifiers: List[str] = field(default_factory=list)

@dataclass
class ActorProfile:
    actor_id: str
    profile_version: str = "1.0"
    identifiers: Identifiers = field(default_factory=Identifiers)
    stylometry: Stylometry = field(default_factory=Stylometry)
    activity: Activity = field(default_factory=Activity)
    infrastructure: Infrastructure = field(default_factory=Infrastructure)
    sources: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "profile_version": self.profile_version,
            "actor_id": self.actor_id,
            "identifiers": {
                "pgp": self.identifiers.pgp,
                "wallets": self.identifiers.wallets,
                "emails": self.identifiers.emails,
                "aliases": self.identifiers.aliases,
            },
            "stylometry": {
                "language": self.stylometry.language,
                "document_count": self.stylometry.document_count,
                "avg_sentence_length": self.stylometry.avg_sentence_length,
                "vocabulary_diversity": self.stylometry.vocabulary_diversity,
                "punctuation_rate": self.stylometry.punctuation_rate,
                "function_word_frequency": self.stylometry.function_word_frequency,
                "phrase_features": self.stylometry.phrase_features,
            },
            "activity": {
                "posting_hours": self.activity.posting_hours,
                "weekday_distribution": self.activity.weekday_distribution,
                "activity_frequency": self.activity.activity_frequency,
            },
            "infrastructure": {
                "tls_fingerprints": self.infrastructure.tls_fingerprints,
                "sanitized_network_fingerprints": self.infrastructure.sanitized_network_fingerprints,
                "hosting_identifiers": self.infrastructure.hosting_identifiers,
            },
            "sources": self.sources,
        }
