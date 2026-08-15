from queue import Full
from sqlite3 import IntegrityError
from typing import List, Protocol, Optional
from AstroDatabase import InvalidUsernameError
from models import Observation,User
import re
from flask_bcrypt import Bcrypt
from my_exceptions import *

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

    pass

def checked_username_password(username:str, password:str):
    if (not username) or (not password):
        raise WrongUsernamePasswordFormat("Username and password is required")

    if len(password) < 8:
        raise WrongUsernamePasswordFormat("password must be at least 8 characters long.")
    
    return True
    

class DatabaseRepo(Protocol):
    def get_recent_observations(self, limit: int = 50, offset: int = 0) -> List[Observation]: ...
    def get_total_count(self) -> int: ...
    def add_observation(self, name: str, ra: str, dec: str, notes: Optional[str], user_id: int) -> Observation: ...
    def delete_observation(self, target_id: int, user_id: int) -> bool: ...
    def search_observations(self, query: str, limit: int = 50, offset: int = 0) -> List[Observation]: ...
    def search_users_recent_observations(self, user_id: int) -> List[Observation]: ...
    def count_users_exoplanets(self,user_id: int) -> int: ...
    def add_user(self, username: str, hashed_password: str) -> Optional[User]: ...
    def delete_user(self, target_id: int) -> bool: ...
    def get_user(self, username: str) -> Optional[User]: ...
    def addlike(self,user_id,obs_id) -> bool: ...
    def get_user_likes(self,user_id) -> set[int]: ...
    def get_observation_likes(self,obs_id) -> int: ...


class AstroService:
    def __init__(self, astro_database: DatabaseRepo,bcrypt_instance) -> None:
        self.db = astro_database
        self.bcrypt = bcrypt_instance

    def delete_observation_service(self, target_id: int, user_id: int) -> bool:
        """Returns True on success, False if the ID does not exist, access is denied, or deletion failed."""
        return self.db.delete_observation(target_id, user_id)
        
    def get_recent_observations_service(self, limit=50, offset=0) -> List[Observation]:
        return self.db.get_recent_observations(limit, offset)
    
    def get_total_count_service(self) -> int:
        return self.db.get_total_count()
    
    def add_observation_service(self, name: str, ra: str, dec: str, notes: Optional[str], user_id: int) -> Observation:
        validate_coordinates(ra, dec)
        try:
            return self.db.add_observation(name, ra, dec, notes,user_id)
        except DatabaseError as e:
            print(e)
            raise DatabaseError("Failed to retrieve new observation id")
    
    def search_observations_service(self, query: str, limit: int = 50, offset: int = 0) -> List[Observation]:
        return self.db.search_observations(query, limit, offset)
    
    def add_user_service(self, username: str, password: str ) -> None:
        if checked_username_password(username,password):
            try:
                #used bcrypts slow hashing wtih salt instead of custom implementation
                hashed_password = self.bcrypt.generate_password_hash(password).decode('utf-8')
                self.db.add_user(username, hashed_password)
            except UserAlreadyExistsError: 
                raise UserAlreadyExistsError(f"Observer username '{username}' is already taken.")
            except Exception as e:
                print('debug')
                raise Exception()
               
    def auth_service(self, username: str, password:str) -> Optional[User]:
        if checked_username_password(username,password):
            
            user = self.db.get_user(username)
            if not user:
                raise UserNotFoundError("Username not found.")
                
            if not self.bcrypt.check_password_hash(user.password, password):
                raise WrongPasswordError("Invalid password. Please try again.")
                
            return user
        
    def search_users_recent_observations(self, user_id: int) -> list[Observation]:
        try:
            return self.db.search_users_recent_observations(user_id)
        except Exception as e:
            raise DatabaseError("Failed to fetch user observations") from e
        
    def count_users_exoplanets(self,user_id: int) -> int:
        try:
            return self.db.count_users_exoplanets(user_id)
        except Exception as e:
            raise DatabaseError("Failed to fetch user observations exoplanets") from e

    def get_user_likes_service(self,user_id) -> set[int]:
        try:
            return self.db.get_user_likes(user_id)
        except:
            raise Exception("an unexpected exception happened.")
    
    def get_observation_likes_service(self,obs_id) -> int:

        likes = self.db.get_observation_likes(obs_id)
        if likes == -1:
            raise WrongId("This observation was not found!")
        else:
            return likes
        
    def flush_database_service(self,user_id,pending_likes):
        for obs_id,like in pending_likes.items():
                if like != 0:
                    x = self.db.addlike(user_id,obs_id)
                    print(f"** obs with id: {obs_id} got {like} from session and {x} from db **")
                else:
                    print("** got 0 **")
            
            

        