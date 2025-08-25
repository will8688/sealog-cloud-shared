"""
Log Period Schema - Data structures for maritime log periods
Defines the foundational data model for log periods that span across
Ship Log, Engine Room Log, and Radio Log systems.
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, List, Dict, Any
from enum import Enum
import json

class LogPeriodStatus(Enum):
    """Status of the log period"""
    IN_TRANSIT = "in_transit"
    IN_PORT = "in_port"
    YARD_PERIOD = "yard_period"
    
    def __str__(self):
        return self.value.replace('_', ' ').title()

class LogPeriodType(Enum):
    """Type of log period for classification"""
    PASSAGE = "passage"          # Port A to Port B
    PORT_STAY = "port_stay"      # Single port stay
    YARD_PERIOD = "yard_period"  # Maintenance/repair period
    ANCHORAGE = "anchorage"      # Anchored period
    
    def __str__(self):
        return self.value.replace('_', ' ').title()

@dataclass
class LogPeriod:
    """
    Core log period data structure
    Represents a time period for maritime operations logging
    """
    # Identity
    id: Optional[str] = None
    user_id: str = ""
    vessel_id: str = ""
    vessel_name: str = ""
    
    # Time and Location
    start_date: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    end_date: Optional[datetime] = None
    timezone_name: str = "UTC"  # e.g., "Europe/London", "America/New_York"
    
    # Ports and Locations
    port_of_departure: str = ""  # Required - where we started
    port_of_arrival: Optional[str] = None  # Optional - where we're going
    
    # Status and Classification
    status: LogPeriodStatus = LogPeriodStatus.IN_PORT
    period_type: LogPeriodType = LogPeriodType.PORT_STAY
    
    # Operational Details
    is_active: bool = True  # Current active period
    is_completed: bool = False  # Period completed
    
    # Navigation Details (optional)
    departure_coordinates: Optional[str] = None  # "lat,lon"
    arrival_coordinates: Optional[str] = None    # "lat,lon"
    planned_route: Optional[str] = None          # Route description
    
    # Administrative
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    updated_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    notes: str = ""
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization processing"""
        # Ensure timezone-aware datetimes
        if self.start_date and self.start_date.tzinfo is None:
            self.start_date = self.start_date.replace(tzinfo=timezone.utc)
        
        if self.end_date and self.end_date.tzinfo is None:
            self.end_date = self.end_date.replace(tzinfo=timezone.utc)
        
        # Auto-determine period type if not set
        if self.period_type == LogPeriodType.PORT_STAY:
            self.period_type = self._determine_period_type()
    
    def _determine_period_type(self) -> LogPeriodType:
        """Auto-determine the period type based on ports and status"""
        if self.status == LogPeriodStatus.YARD_PERIOD:
            return LogPeriodType.YARD_PERIOD
        elif self.port_of_arrival and self.port_of_arrival != self.port_of_departure:
            return LogPeriodType.PASSAGE
        elif self.status == LogPeriodStatus.IN_PORT:
            return LogPeriodType.PORT_STAY
        else:
            return LogPeriodType.PASSAGE
    
    @property
    def duration_hours(self) -> Optional[float]:
        """Calculate duration in hours"""
        if self.end_date:
            delta = self.end_date - self.start_date
            return delta.total_seconds() / 3600
        elif self.is_active:
            delta = datetime.now(timezone.utc) - self.start_date
            return delta.total_seconds() / 3600
        return None
    
    @property
    def is_passage(self) -> bool:
        """Check if this is a passage (has different departure/arrival ports)"""
        return (self.port_of_arrival is not None and 
                self.port_of_arrival != self.port_of_departure)
    
    @property
    def display_name(self) -> str:
        """Create a user-friendly display name"""
        if self.is_passage:
            return f"{self.port_of_departure} → {self.port_of_arrival}"
        else:
            status_text = str(self.status)
            return f"{status_text} at {self.port_of_departure}"
    
    @property
    def period_description(self) -> str:
        """Create a detailed description of the period"""
        parts = []
        
        # Vessel and dates
        start_str = self.start_date.strftime("%Y-%m-%d %H:%M")
        parts.append(f"{self.vessel_name} - {start_str}")
        
        # Location info
        if self.is_passage:
            parts.append(f"Passage: {self.port_of_departure} to {self.port_of_arrival}")
        else:
            parts.append(f"{str(self.status)}: {self.port_of_departure}")
        
        # Duration if available
        if self.duration_hours:
            if self.duration_hours < 24:
                parts.append(f"({self.duration_hours:.1f} hours)")
            else:
                days = self.duration_hours / 24
                parts.append(f"({days:.1f} days)")
        
        return " | ".join(parts)
    
    def complete_period(self, end_date: Optional[datetime] = None) -> None:
        """Mark the period as completed"""
        self.end_date = end_date or datetime.now(timezone.utc)
        self.is_completed = True
        self.is_active = False
        self.updated_at = datetime.now(timezone.utc)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            'id': self.id,
            'user_id': self.user_id,
            'vessel_id': self.vessel_id,
            'vessel_name': self.vessel_name,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'timezone_name': self.timezone_name,
            'port_of_departure': self.port_of_departure,
            'port_of_arrival': self.port_of_arrival,
            'status': self.status.value,
            'period_type': self.period_type.value,
            'is_active': self.is_active,
            'is_completed': self.is_completed,
            'departure_coordinates': self.departure_coordinates,
            'arrival_coordinates': self.arrival_coordinates,
            'planned_route': self.planned_route,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'notes': self.notes,
            'metadata': self.metadata
        }
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'LogPeriod':
        """Create LogPeriod from dictionary"""
        # Parse datetime fields
        start_date = None
        if data.get('start_date'):
            start_date = datetime.fromisoformat(data['start_date'].replace('Z', '+00:00'))
        
        end_date = None
        if data.get('end_date'):
            end_date = datetime.fromisoformat(data['end_date'].replace('Z', '+00:00'))
        
        created_at = None
        if data.get('created_at'):
            created_at = datetime.fromisoformat(data['created_at'].replace('Z', '+00:00'))
        
        updated_at = None
        if data.get('updated_at'):
            updated_at = datetime.fromisoformat(data['updated_at'].replace('Z', '+00:00'))
        
        return cls(
            id=data.get('id'),
            user_id=data.get('user_id', ''),
            vessel_id=data.get('vessel_id', ''),
            vessel_name=data.get('vessel_name', ''),
            start_date=start_date or datetime.now(timezone.utc),
            end_date=end_date,
            timezone_name=data.get('timezone_name', 'UTC'),
            port_of_departure=data.get('port_of_departure', ''),
            port_of_arrival=data.get('port_of_arrival'),
            status=LogPeriodStatus(data.get('status', 'in_port')),
            period_type=LogPeriodType(data.get('period_type', 'port_stay')),
            is_active=data.get('is_active', True),
            is_completed=data.get('is_completed', False),
            departure_coordinates=data.get('departure_coordinates'),
            arrival_coordinates=data.get('arrival_coordinates'),
            planned_route=data.get('planned_route'),
            created_at=created_at or datetime.now(timezone.utc),
            updated_at=updated_at or datetime.now(timezone.utc),
            notes=data.get('notes', ''),
            metadata=data.get('metadata', {})
        )

@dataclass
class LogPeriodSummary:
    """
    Summary statistics for a log period
    Used for reporting and analytics
    """
    log_period_id: str
    vessel_name: str
    period_description: str
    start_date: datetime
    end_date: Optional[datetime]
    duration_hours: Optional[float]
    
    # Entry counts by type
    navigation_entries: int = 0
    engine_entries: int = 0
    radio_entries: int = 0
    total_entries: int = 0
    
    # Navigation summary
    total_distance_nm: Optional[float] = None
    average_speed_kts: Optional[float] = None
    max_speed_kts: Optional[float] = None
    fuel_consumed_litres: Optional[float] = None
    
    # Status
    is_completed: bool = False
    
    @property
    def entries_per_day(self) -> Optional[float]:
        """Calculate average entries per day"""
        if self.duration_hours and self.duration_hours > 0:
            days = self.duration_hours / 24
            return self.total_entries / days if days > 0 else None
        return None

# Validation functions
def validate_log_period(period: LogPeriod) -> tuple[bool, List[str]]:
    """
    Validate log period data
    
    Returns:
        Tuple of (is_valid: bool, errors: List[str])
    """
    errors = []
    
    # Required fields
    if not period.user_id:
        errors.append("User ID is required")
    
    if not period.vessel_id:
        errors.append("Vessel ID is required")
    
    if not period.vessel_name.strip():
        errors.append("Vessel name is required")
    
    if not period.port_of_departure.strip():
        errors.append("Port of departure is required")
    
    # Date validation
    if not period.start_date:
        errors.append("Start date is required")
    
    if period.end_date and period.start_date:
        if period.end_date <= period.start_date:
            errors.append("End date must be after start date")
    
    # Port validation for passages
    if period.is_passage:
        if not period.port_of_arrival or not period.port_of_arrival.strip():
            errors.append("Port of arrival is required for passages")
        
        if period.port_of_arrival == period.port_of_departure:
            errors.append("Port of arrival must be different from port of departure")
    
    # Status validation
    if period.status == LogPeriodStatus.IN_TRANSIT and not period.is_passage:
        errors.append("In transit status requires different departure and arrival ports")
    
    return len(errors) == 0, errors

# Helper functions for common operations
def create_passage_period(
    user_id: str,
    vessel_id: str,
    vessel_name: str,
    port_of_departure: str,
    port_of_arrival: str,
    start_date: Optional[datetime] = None,
    timezone_name: str = "UTC"
) -> LogPeriod:
    """Create a new passage log period"""
    return LogPeriod(
        user_id=user_id,
        vessel_id=vessel_id,
        vessel_name=vessel_name,
        port_of_departure=port_of_departure,
        port_of_arrival=port_of_arrival,
        start_date=start_date or datetime.now(timezone.utc),
        timezone_name=timezone_name,
        status=LogPeriodStatus.IN_TRANSIT,
        period_type=LogPeriodType.PASSAGE,
        is_active=True,
        is_completed=False
    )

def create_port_stay_period(
    user_id: str,
    vessel_id: str,
    vessel_name: str,
    port_name: str,
    start_date: Optional[datetime] = None,
    timezone_name: str = "UTC"
) -> LogPeriod:
    """Create a new port stay log period"""
    return LogPeriod(
        user_id=user_id,
        vessel_id=vessel_id,
        vessel_name=vessel_name,
        port_of_departure=port_name,
        port_of_arrival=None,
        start_date=start_date or datetime.now(timezone.utc),
        timezone_name=timezone_name,
        status=LogPeriodStatus.IN_PORT,
        period_type=LogPeriodType.PORT_STAY,
        is_active=True,
        is_completed=False
    )

def create_yard_period(
    user_id: str,
    vessel_id: str,
    vessel_name: str,
    yard_location: str,
    start_date: Optional[datetime] = None,
    timezone_name: str = "UTC"
) -> LogPeriod:
    """Create a new yard period log period"""
    return LogPeriod(
        user_id=user_id,
        vessel_id=vessel_id,
        vessel_name=vessel_name,
        port_of_departure=yard_location,
        port_of_arrival=None,
        start_date=start_date or datetime.now(timezone.utc),
        timezone_name=timezone_name,
        status=LogPeriodStatus.YARD_PERIOD,
        period_type=LogPeriodType.YARD_PERIOD,
        is_active=True,
        is_completed=False
    )