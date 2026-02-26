from typing import List, Protocol, Optional
from models import Observation
import re

def validate_coordinates(ra: str, dec: str):
    ra_nums = [int(n) for n in re.findall(r'\d+', ra)]
    dec_nums = [int(n) for n in re.findall(r'\d+', dec)]

    if len(ra_nums) == 3:
        if ra_nums[1] >= 60 or ra_nums[2] >= 60:
            raise ValueError("RA minutes/seconds must be under 60.")
    else:
        raise ValueError("RA must contain Hours, Minutes, and Seconds.")

    if len(dec_nums) == 3:
        if dec_nums[0] > 90:
            raise ValueError("Declination degrees cannot exceed 90.")
        if dec_nums[1] >= 60 or dec_nums[2] >= 60:
            raise ValueError("Dec minutes/seconds must be under 60.")
    else:
        raise ValueError("Dec must contain Degrees, Minutes, and Seconds.")
    
class ObservationRepository(Protocol):
    def get_recent_observations(self, limit: int = 50, offset: int = 0) -> List[Observation]: ...
    def get_total_count(self) -> int: ...
    def add_observation(self, name: str, ra: str, dec: str, notes: Optional[str]) -> Observation: ...
    def delete_observation(self, target_id: int) -> bool: ... 
    def search_observations(self, query: str, limit: int = 50, offset: int = 0) -> List[Observation]: ...

class AstroService:
    def __init__(self, astro_database: ObservationRepository) -> None:
        self.db = astro_database

    def delete_observation_service(self, target_id: int) -> bool:
        """Returns True on success, False if the ID does not exist or deletion failed."""
        return self.db.delete_observation(target_id)
        
    def get_recent_observations_service(self, limit=50, offset=0) -> List[Observation]:
        return self.db.get_recent_observations(limit, offset)
    
    def get_total_count_service(self) -> int:
        return self.db.get_total_count()
    
    def add_observation_service(self, name: str, ra: str, dec: str, notes: Optional[str]) -> Observation:
        print(ra,dec)
        validate_coordinates(ra, dec)
        print(f'2 :{ra,dec}')

        return self.db.add_observation(name, ra, dec, notes)
    
    def search_observations_service(self, query: str, limit: int = 50, offset: int = 0) -> List[Observation]:
        return self.db.search_observations(query, limit, offset)