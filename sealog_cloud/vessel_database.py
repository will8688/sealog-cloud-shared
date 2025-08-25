"""
Vessel Database Operations
Handles all database interactions for vessel management

This module provides database operations for vessel CRUD, user associations,
and data integrity management across the maritime application suite.
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
import logging
import json
from dataclasses import asdict

from vessel_schema import BaseVessel, YachtSchema

logger = logging.getLogger(__name__)

class VesselDatabase:
    """
    Database operations for vessel management
    Works with your existing database connection
    """
    
    def __init__(self, db_manager):
        self.db_manager = db_manager
        self.db_type = db_manager.db_type
        self.placeholder = '?' if self.db_type == 'sqlite' else '%s'
        self._ensure_tables_exist()

    # ============================================================================
    # TABLE MANAGEMENT
    # ============================================================================
    
    def _ensure_tables_exist(self):
        """
        Ensure required tables exist with proper schema
        Creates tables if they don't exist, adds missing columns if they do
        """
        try:
            # Main vessels table - extend existing or create new
            vessels_table_sql = """
            CREATE TABLE IF NOT EXISTS vessels (
                id VARCHAR(50) PRIMARY KEY,
                vessel_name VARCHAR(255) NOT NULL,
                imo_number VARCHAR(7),
                mmsi_number VARCHAR(9),
                call_sign VARCHAR(20),
                official_number VARCHAR(50),
    
                -- Classification
                vessel_type VARCHAR(50),
                flag_state VARCHAR(100),
                port_of_registry VARCHAR(100),
                classification_society VARCHAR(50),
                class_notation VARCHAR(100),
    
                -- Dimensions
                length_overall DECIMAL(10,2),
                length_waterline DECIMAL(10,2),
                beam DECIMAL(10,2),
                draft DECIMAL(10,2),
                depth DECIMAL(10,2),
                air_draft DECIMAL(10,2),
                gross_tonnage DECIMAL(10,2),
                net_tonnage DECIMAL(10,2),
                deadweight DECIMAL(10,2),
                displacement DECIMAL(10,2),
    
                -- Construction
                year_built INTEGER,
                builder VARCHAR(255),
                build_location VARCHAR(255),
                hull_material VARCHAR(50),
                hull_number VARCHAR(100),
                design_category VARCHAR(10),
    
                -- Standards and certification
                build_standards TEXT,
                survey_date DATE,
                certificate_expiry DATE,
    
                -- Radio Log specific fields
                default_operator_name VARCHAR(255),
                radio_certificate VARCHAR(255),
    
                -- Yacht-specific fields
                yacht_category VARCHAR(50),
                superyacht_status BOOLEAN DEFAULT 0,
                commercial_operation BOOLEAN DEFAULT 0,
                guest_cabins INTEGER,
                crew_cabins INTEGER,
                total_berths INTEGER,
                guest_capacity INTEGER,
                crew_capacity INTEGER,
                max_speed DECIMAL(6,2),
                cruise_speed DECIMAL(6,2),
                range_nm DECIMAL(10,2),
                fuel_capacity DECIMAL(10,2),
                water_capacity DECIMAL(10,2),
    
                -- Propulsion
                propulsion_type VARCHAR(50),
                main_engines VARCHAR(255),
                engine_power DECIMAL(10,2),
                number_of_engines INTEGER,
    
                -- Luxury amenities (stored as JSON)
                amenities TEXT,
    
                -- Operational
                home_port VARCHAR(255),
                cruising_areas TEXT,
    
                -- Metadata
                created_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                created_by VARCHAR(50),
                data_source VARCHAR(100),
                is_active BOOLEAN DEFAULT 1
            )
            """

            # Create indexes separately for SQLite
            indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_vessel_name ON vessels(vessel_name)",
                "CREATE INDEX IF NOT EXISTS idx_imo_number ON vessels(imo_number)", 
                "CREATE INDEX IF NOT EXISTS idx_mmsi_number ON vessels(mmsi_number)",
                "CREATE INDEX IF NOT EXISTS idx_call_sign ON vessels(call_sign)",
                "CREATE INDEX IF NOT EXISTS idx_vessel_type ON vessels(vessel_type)",
                "CREATE INDEX IF NOT EXISTS idx_flag_state ON vessels(flag_state)",
                "CREATE INDEX IF NOT EXISTS idx_active ON vessels(is_active)"
            ]

            user_vessels_table_sql = """
            CREATE TABLE IF NOT EXISTS user_vessels (
                user_id VARCHAR(50),
                vessel_id VARCHAR(50),
                role VARCHAR(50) DEFAULT 'operator',
                associated_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                is_active BOOLEAN DEFAULT 1,
    
                PRIMARY KEY (user_id, vessel_id),
                FOREIGN KEY (vessel_id) REFERENCES vessels(id) ON DELETE CASCADE
            )
            """

            user_vessels_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_user_vessels_user_id ON user_vessels(user_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_vessels_vessel_id ON user_vessels(vessel_id)",
                "CREATE INDEX IF NOT EXISTS idx_user_vessels_role ON user_vessels(role)"
            ]

            vessel_usage_table_sql = """
            CREATE TABLE IF NOT EXISTS vessel_usage (
                id VARCHAR(50) PRIMARY KEY,
                vessel_id VARCHAR(50),
                usage_type VARCHAR(50),
                usage_count INTEGER DEFAULT 0,
                last_used TIMESTAMP,
    
                FOREIGN KEY (vessel_id) REFERENCES vessels(id) ON DELETE CASCADE
            )
            """

            vessel_usage_indexes_sql = [
                "CREATE INDEX IF NOT EXISTS idx_vessel_usage_vessel_id ON vessel_usage(vessel_id)",
                "CREATE INDEX IF NOT EXISTS idx_vessel_usage_type ON vessel_usage(usage_type)"
            ]

            # Execute table creation
            self.db_manager.execute_query(vessels_table_sql)
            self.db_manager.execute_query(user_vessels_table_sql)
            self.db_manager.execute_query(vessel_usage_table_sql)

            # Create indexes
            for index_sql in indexes_sql:
                self.db_manager.execute_query(index_sql)
            for index_sql in user_vessels_indexes_sql:
                self.db_manager.execute_query(index_sql)
            for index_sql in vessel_usage_indexes_sql:
                self.db_manager.execute_query(index_sql)

        except Exception as e:
            logger.error(f"Error ensuring tables exist: {e}")
            raise

    def _add_missing_columns(self):
        """Add missing columns to existing vessels table for backward compatibility"""
        missing_columns = [
            "ALTER TABLE vessels ADD COLUMN IF NOT EXISTS mmsi_number VARCHAR(9)",
            "ALTER TABLE vessels ADD COLUMN IF NOT EXISTS default_operator_name VARCHAR(255)",
            "ALTER TABLE vessels ADD COLUMN IF NOT EXISTS radio_certificate VARCHAR(255)",
            "ALTER TABLE vessels ADD COLUMN IF NOT EXISTS yacht_category VARCHAR(50)",
            "ALTER TABLE vessels ADD COLUMN IF NOT EXISTS superyacht_status BOOLEAN DEFAULT FALSE",
            "ALTER TABLE vessels ADD COLUMN IF NOT EXISTS amenities TEXT",
            "ALTER TABLE vessels ADD COLUMN IF NOT EXISTS is_active BOOLEAN DEFAULT TRUE"
        ]
        
        try:
            for sql in missing_columns:
                try:
                    self.db_manager.execute_query(sql)
                except Exception as e:
                    # Column might already exist - that's okay
                    logger.debug(f"Column addition skipped: {e}")
        except Exception as e:
            logger.warning(f"Error adding missing columns: {e}")
    
    # ============================================================================
    # VESSEL RETRIEVAL OPERATIONS
    # ============================================================================
    
    def get_vessels_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Get all vessels associated with a user - Future-proof version
    
        Args:
            user_id: User ID
        
        Returns:
            List of vessel dictionaries
        """
        try:
            sql = f"""
            SELECT v.*, uv.role, uv.associated_date
            FROM vessels v
            JOIN user_vessels uv ON v.id = uv.vessel_id
            WHERE uv.user_id = {self.placeholder} 
            AND v.is_active = 1 
            AND uv.is_active = 1
            ORDER BY v.vessel_name
            """
        
            results = self.db_manager.execute_query(sql, (user_id,), fetch='all')
            if not results:
                results = []
        
            return [self._format_vessel_row(row) for row in results]
        
        except Exception as e:
            logger.error(f"Error getting vessels for user {user_id}: {e}")
            return []
    
    def get_vessel_by_id(self, vessel_id: str) -> Optional[Dict[str, Any]]:
        """
        Get vessel by ID
    
        Args:
            vessel_id: Vessel ID
        
        Returns:
            Vessel dictionary or None
        """
        try:
            sql = f"SELECT * FROM vessels WHERE id = {self.placeholder} AND is_active = 1"
        
            result = self.db_manager.execute_query(sql, (vessel_id,), fetch='one')
            if result:
                return self._format_vessel_row(result)
        
            return None
        
        except Exception as e:
            logger.error(f"Error getting vessel by ID {vessel_id}: {e}")
            return None
    
    def find_vessel_by_identifier(
        self,
        imo_number: str = None,
        mmsi_number: str = None,
        call_sign: str = None,
        vessel_name: str = None
    ) -> Optional[Dict[str, Any]]:
        """
        Find vessel by any unique identifier
        
        Args:
            imo_number: IMO number
            mmsi_number: MMSI number
            call_sign: Call sign
            vessel_name: Vessel name
            
        Returns:
            Vessel dictionary or None
        """
        try:
            conditions = []
            params = []
            
            if imo_number:
                conditions.append(f"imo_number = {self.placeholder}")
                params.append(imo_number)
            
            if mmsi_number:
                conditions.append(f"mmsi_number = {self.placeholder}")
                params.append(mmsi_number)
            
            if call_sign:
                conditions.append(f"call_sign = {self.placeholder}")
                params.append(call_sign)
            
            if vessel_name:
                conditions.append(f"vessel_name = {self.placeholder}")
                params.append(vessel_name)
            
            if not conditions:
                return None
            
            sql = f"""
            SELECT * FROM vessels 
            WHERE ({' OR '.join(conditions)}) 
            AND is_active = TRUE
            LIMIT 1
            """
            
            result = self.db_manager.execute_query(sql, tuple(params), fetch='one')
            
            if result:
                return self._format_vessel_row(result)
            return None
            
        except Exception as e:
            logger.error(f"Error finding vessel by identifier: {e}")
            return None
    
    def search_vessels(self, query: str, user_id: str = None) -> List[Dict[str, Any]]:
        """
        Search vessels by name, IMO, MMSI, or call sign
        
        Args:
            query: Search query
            user_id: Limit to user's vessels (optional)
            
        Returns:
            List of matching vessels
        """
        try:
            # Build search conditions
            search_conditions = f"""
            (vessel_name LIKE {self.placeholder} 
            OR imo_number LIKE {self.placeholder} 
            OR mmsi_number LIKE {self.placeholder} 
            OR call_sign LIKE {self.placeholder})
            """
            
            search_param = f"%{query}%"
            params = [search_param, search_param, search_param, search_param]
            
            if user_id:
                sql = f"""
                SELECT v.*, uv.role 
                FROM vessels v
                JOIN user_vessels uv ON v.id = uv.vessel_id
                WHERE uv.user_id = {self.placeholder} 
                AND {search_conditions}
                AND v.is_active = TRUE 
                AND uv.is_active = TRUE
                ORDER BY v.vessel_name
                LIMIT 50
                """
                params = [user_id] + params
            else:
                sql = f"""
                SELECT * FROM vessels 
                WHERE {search_conditions}
                AND is_active = TRUE
                ORDER BY vessel_name
                LIMIT 50
                """
            
            results = self.db_manager.execute_query(sql, tuple(params), fetch='all')
            
            return [self._format_vessel_row(row) for row in results]
            
        except Exception as e:
            logger.error(f"Error searching vessels: {e}")
            return []
    
    # ============================================================================
    # VESSEL CREATION AND UPDATES
    # ============================================================================
    
    def create_vessel(self, vessel: BaseVessel, user_id: str) -> str:
        """
        Create new vessel in database - Future-proof version
    
        Args:
            vessel: Vessel object
            user_id: User creating the vessel
        
        Returns:
            Vessel ID
        """
        try:
            # Generate vessel ID
            vessel_id = self._generate_vessel_id()
        
            # Convert vessel to database format
            vessel_data = self._vessel_to_db_format(vessel)
            vessel_data['id'] = vessel_id
            vessel_data['created_by'] = user_id
            vessel_data['created_date'] = datetime.now()
            vessel_data['updated_date'] = datetime.now()
        
            # Build INSERT statement with database-appropriate syntax
            columns = list(vessel_data.keys())
            placeholders = ', '.join([self.placeholder] * len(columns))
            values = [vessel_data[col] for col in columns]
        
            sql = f"""
            INSERT INTO vessels ({', '.join(columns)})
            VALUES ({placeholders})
            """
        
            self.db_manager.execute_query(sql, tuple(values))
        
            # Associate vessel with user
            self.associate_user_with_vessel(user_id, vessel_id, 'owner')
        
            return vessel_id
        
        except Exception as e:
            logger.error(f"Error creating vessel: {e}")
            raise
    
    def update_vessel(self, vessel_id: str, vessel: BaseVessel) -> bool:
        """
        Update existing vessel - Future-proof version
    
        Args:
            vessel_id: Vessel ID to update
            vessel: Updated vessel object
        
        Returns:
            Success status
        """
        try:
            # Convert vessel to database format
            vessel_data = self._vessel_to_db_format(vessel)
            vessel_data['updated_date'] = datetime.now()
        
            # Build UPDATE statement with database-appropriate syntax
            set_clauses = []
            values = []
        
            for column, value in vessel_data.items():
                if column != 'id':  # Don't update ID
                    set_clauses.append(f"{column} = {self.placeholder}")
                    values.append(value)
        
            values.append(vessel_id)  # For WHERE clause
        
            sql = f"""
            UPDATE vessels 
            SET {', '.join(set_clauses)}
            WHERE id = {self.placeholder}
            """
        
            self.db_manager.execute_query(sql, tuple(values))
            success = True  # db_manager handles success internally
        
            return success
        
        except Exception as e:
            logger.error(f"Error updating vessel {vessel_id}: {e}")
            return False
    
    def delete_vessel(self, vessel_id: str) -> bool:
        """
        Soft delete vessel (mark as inactive)
        
        Args:
            vessel_id: Vessel ID to delete
            
        Returns:
            Success status
        """
        try:
            sql = f"UPDATE vessels SET is_active = FALSE WHERE id = {self.placeholder}"
            
            self.db_manager.execute_query(sql, (vessel_id,))
            success = True  # db_manager handles success internally
            
            return success
            
        except Exception as e:
            logger.error(f"Error deleting vessel {vessel_id}: {e}")
            return False
    
    # ============================================================================
    # USER-VESSEL ASSOCIATIONS
    # ============================================================================
    
    def associate_user_with_vessel(self, user_id: str, vessel_id: str, role: str = 'operator') -> bool:
        """
        Associate user with vessel - Future-proof version
    
        Args:
            user_id: User ID
            vessel_id: Vessel ID
            role: User role (owner, operator, crew, guest)
        
        Returns:
            Success status
        """
        try:
            # Use database-appropriate UPSERT syntax
            if self.db_type == 'sqlite':
                sql = """
                INSERT OR REPLACE INTO user_vessels (user_id, vessel_id, role, associated_date, is_active)
                VALUES (?, ?, ?, ?, ?)
                """
            elif self.db_type == 'mysql':
                sql = """
                INSERT INTO user_vessels (user_id, vessel_id, role, associated_date, is_active)
                VALUES (%s, %s, %s, %s, %s)
                ON DUPLICATE KEY UPDATE 
                role = VALUES(role),
                is_active = VALUES(is_active),
                associated_date = VALUES(associated_date)
                """
            elif self.db_type == 'postgresql':
                sql = """
                INSERT INTO user_vessels (user_id, vessel_id, role, associated_date, is_active)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (user_id, vessel_id) 
                DO UPDATE SET 
                role = EXCLUDED.role,
                is_active = EXCLUDED.is_active,
                associated_date = EXCLUDED.associated_date
                """
            else:
                # Fallback to basic INSERT
                sql = f"""
                INSERT INTO user_vessels (user_id, vessel_id, role, associated_date, is_active)
                VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder}, {self.placeholder})
                """
        
            self.db_manager.execute_query(sql, (user_id, vessel_id, role, datetime.now(), 1))
        
            return True
        
        except Exception as e:
            logger.error(f"Error associating user {user_id} with vessel {vessel_id}: {e}")
            return False
    
    def user_has_vessel_access(self, user_id: str, vessel_id: str) -> bool:
        """
        Check if user has access to vessel
        
        Args:
            user_id: User ID
            vessel_id: Vessel ID
            
        Returns:
            Access status
        """
        try:
            sql = f"""
            SELECT 1 FROM user_vessels 
            WHERE user_id = {self.placeholder} AND vessel_id = {self.placeholder} AND is_active = TRUE
            """
            
            result = self.db_manager.execute_query(sql, (user_id, vessel_id), fetch='one')
            
            return result is not None
            
        except Exception as e:
            logger.error(f"Error checking vessel access: {e}")
            return False
    
    # ============================================================================
    # USAGE TRACKING
    # ============================================================================
    
    def track_vessel_usage(self, vessel_id: str, usage_type: str):
        """
        Track vessel usage for safe deletion
        
        Args:
            vessel_id: Vessel ID
            usage_type: Type of usage (ships_log, radio_log, etc.)
        """
        try:
            # Handle database-specific UPSERT
            if self.db_type == 'sqlite':
                sql = f"""
                INSERT OR REPLACE INTO vessel_usage (id, vessel_id, usage_type, usage_count, last_used)
                VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, 1, {self.placeholder})
                """
            else:
                sql = f"""
                INSERT INTO vessel_usage (id, vessel_id, usage_type, usage_count, last_used)
                VALUES ({self.placeholder}, {self.placeholder}, {self.placeholder}, 1, {self.placeholder})
                ON DUPLICATE KEY UPDATE
                usage_count = usage_count + 1,
                last_used = VALUES(last_used)
                """
            
            usage_id = f"{vessel_id}_{usage_type}"
            
            self.db_manager.execute_query(sql, (usage_id, vessel_id, usage_type, datetime.now()))
            
        except Exception as e:
            logger.error(f"Error tracking vessel usage: {e}")
    
    def get_vessel_usage_count(self, vessel_id: str) -> int:
        """
        Get total usage count for vessel
        
        Args:
            vessel_id: Vessel ID
            
        Returns:
            Total usage count
        """
        try:
            sql = f"SELECT SUM(usage_count) FROM vessel_usage WHERE vessel_id = {self.placeholder}"
            
            result = self.db_manager.execute_query(sql, (vessel_id,), fetch='one')
            
            return result[0] if result and result[0] else 0
            
        except Exception as e:
            logger.error(f"Error getting vessel usage count: {e}")
            return 0
    
    # ============================================================================
    # UTILITY METHODS
    # ============================================================================
    
    def _generate_vessel_id(self) -> str:
        """Generate unique vessel ID"""
        import uuid
        return f"vessel_{str(uuid.uuid4())[:8]}"
    
    def _vessel_to_db_format(self, vessel: BaseVessel) -> Dict[str, Any]:
        """
        Convert vessel object to database format - FIXED VERSION
    
        Args:
            vessel: Vessel object
        
        Returns:
            Dictionary suitable for database insertion
        """
        # Instead of using vessel.to_dict() which includes Schema.org fields,
        # manually extract only the database fields
        db_data = {}
    
        # Basic vessel information
        db_data['vessel_name'] = getattr(vessel, 'vessel_name', None)
        db_data['imo_number'] = getattr(vessel, 'imo_number', None)
        db_data['mmsi_number'] = getattr(vessel, 'mmsi_number', None)
        db_data['call_sign'] = getattr(vessel, 'call_sign', None)
        db_data['official_number'] = getattr(vessel, 'official_number', None)
    
        # Classification - handle enum conversion
        vessel_type = getattr(vessel, 'vessel_type', None)
        if vessel_type:
            db_data['vessel_type'] = vessel_type.value if hasattr(vessel_type, 'value') else str(vessel_type)
        else:
            db_data['vessel_type'] = None
        
        db_data['flag_state'] = getattr(vessel, 'flag_state', None)
        db_data['port_of_registry'] = getattr(vessel, 'port_of_registry', None)
    
        # Classification society - handle enum
        class_society = getattr(vessel, 'classification_society', None)
        if class_society:
            db_data['classification_society'] = class_society.value if hasattr(class_society, 'value') else str(class_society)
        else:
            db_data['classification_society'] = None
        
        db_data['class_notation'] = getattr(vessel, 'class_notation', None)
    
        # Dimensions
        db_data['length_overall'] = getattr(vessel, 'length_overall', None)
        db_data['length_waterline'] = getattr(vessel, 'length_waterline', None)
        db_data['beam'] = getattr(vessel, 'beam', None)
        db_data['draft'] = getattr(vessel, 'draft', None)
        db_data['depth'] = getattr(vessel, 'depth', None)
        db_data['air_draft'] = getattr(vessel, 'air_draft', None)
        db_data['gross_tonnage'] = getattr(vessel, 'gross_tonnage', None)
        db_data['net_tonnage'] = getattr(vessel, 'net_tonnage', None)
        db_data['deadweight'] = getattr(vessel, 'deadweight', None)
        db_data['displacement'] = getattr(vessel, 'displacement', None)
    
        # Construction
        db_data['year_built'] = getattr(vessel, 'year_built', None)
        db_data['builder'] = getattr(vessel, 'builder', None)
        db_data['build_location'] = getattr(vessel, 'build_location', None)
    
        # Hull material - handle enum
        hull_material = getattr(vessel, 'hull_material', None)
        if hull_material:
            db_data['hull_material'] = hull_material.value if hasattr(hull_material, 'value') else str(hull_material)
        else:
            db_data['hull_material'] = None
        
        db_data['hull_number'] = getattr(vessel, 'hull_number', None)
        db_data['design_category'] = getattr(vessel, 'design_category', None)
    
        # Handle build standards list
        build_standards = getattr(vessel, 'build_standards', [])
        if build_standards:
            # Convert enum list to string list
            standards_list = []
            for std in build_standards:
                if hasattr(std, 'value'):
                    standards_list.append(std.value)
                else:
                    standards_list.append(str(std))
            db_data['build_standards'] = json.dumps(standards_list) if standards_list else None
        else:
            db_data['build_standards'] = None
    
        # Dates - handle both date objects and strings
        survey_date = getattr(vessel, 'survey_date', None)
        if survey_date:
            if isinstance(survey_date, str):
                try:
                    db_data['survey_date'] = datetime.fromisoformat(survey_date.replace('Z', '+00:00')).date()
                except:
                    db_data['survey_date'] = None
            else:
                db_data['survey_date'] = survey_date
        else:
            db_data['survey_date'] = None
        
        cert_expiry = getattr(vessel, 'certificate_expiry', None)
        if cert_expiry:
            if isinstance(cert_expiry, str):
                try:
                    db_data['certificate_expiry'] = datetime.fromisoformat(cert_expiry.replace('Z', '+00:00')).date()
                except:
                    db_data['certificate_expiry'] = None
            else:
                db_data['certificate_expiry'] = cert_expiry
        else:
            db_data['certificate_expiry'] = None
    
        # Radio/Communications fields (for Radio Log integration)
        db_data['default_operator_name'] = getattr(vessel, 'default_operator_name', None)
        db_data['radio_certificate'] = getattr(vessel, 'radio_certificate', None)
    
        # Yacht-specific fields (if yacht object)
        if hasattr(vessel, 'yacht_category'):
            yacht_cat = getattr(vessel, 'yacht_category', None)
            if yacht_cat:
                db_data['yacht_category'] = yacht_cat.value if hasattr(yacht_cat, 'value') else str(yacht_cat)
            else:
                db_data['yacht_category'] = None
            
            db_data['superyacht_status'] = getattr(vessel, 'superyacht_status', False)
            db_data['commercial_operation'] = getattr(vessel, 'commercial_operation', False)
            db_data['guest_cabins'] = getattr(vessel, 'guest_cabins', None)
            db_data['crew_cabins'] = getattr(vessel, 'crew_cabins', None)
            db_data['total_berths'] = getattr(vessel, 'total_berths', None)
            db_data['guest_capacity'] = getattr(vessel, 'guest_capacity', None)
            db_data['crew_capacity'] = getattr(vessel, 'crew_capacity', None)
            db_data['max_speed'] = getattr(vessel, 'max_speed', None)
            db_data['cruise_speed'] = getattr(vessel, 'cruise_speed', None)
            db_data['range_nm'] = getattr(vessel, 'range', None)  # Note: range vs range_nm
            db_data['fuel_capacity'] = getattr(vessel, 'fuel_capacity', None)
            db_data['water_capacity'] = getattr(vessel, 'water_capacity', None)
        
            # Propulsion
            prop_type = getattr(vessel, 'propulsion_type', None)
            if prop_type:
                db_data['propulsion_type'] = prop_type.value if hasattr(prop_type, 'value') else str(prop_type)
            else:
                db_data['propulsion_type'] = None
            
            db_data['main_engines'] = getattr(vessel, 'main_engines', None)
            db_data['engine_power'] = getattr(vessel, 'engine_power', None)
            db_data['number_of_engines'] = getattr(vessel, 'number_of_engines', None)
        
            # Amenities - convert to JSON
            amenities = {}
            amenity_fields = [
                'helicopter_pad', 'swimming_pool', 'beach_club', 'gym', 'spa',
                'wine_cellar', 'elevator', 'air_conditioning', 'stabilizers'
            ]
            for field in amenity_fields:
                if hasattr(vessel, field):
                    amenities[field] = getattr(vessel, field, False)
        
            db_data['amenities'] = json.dumps(amenities) if amenities else None
        
            # Operational
            db_data['home_port'] = getattr(vessel, 'home_port', None)
        
            cruising_areas = getattr(vessel, 'cruising_areas', [])
            db_data['cruising_areas'] = json.dumps(cruising_areas) if cruising_areas else None
    
        # Metadata
        db_data['data_source'] = getattr(vessel, 'data_source', None)
    
        # Remove any None values to avoid database issues
        filtered_data = {k: v for k, v in db_data.items() if v is not None}
    
        return filtered_data
    
    def _format_vessel_row(self, row: Dict[str, Any]) -> Dict[str, Any]:
        """
        Format database row for application use
        
        Args:
            row: Database row dictionary
            
        Returns:
            Formatted vessel dictionary
        """
        # Handle JSON fields
        if row.get('build_standards'):
            try:
                row['build_standards'] = json.loads(row['build_standards'])
            except:
                row['build_standards'] = []
        
        if row.get('cruising_areas'):
            try:
                row['cruising_areas'] = json.loads(row['cruising_areas'])
            except:
                row['cruising_areas'] = []
        
        if row.get('amenities'):
            try:
                row['amenities'] = json.loads(row['amenities'])
            except:
                row['amenities'] = {}
        
        return row