from sqlalchemy.orm import Session
from app import models
from app.auth import hash_password


class UserRepository:
    """Acceso a la BD para usuarios y roles. Sin lógica de negocio."""

    def __init__(self, db: Session):
        self.db = db

    def get_by_username(self, username: str) -> models.User | None:
        return self.db.query(models.User).filter(
            models.User.username == username
        ).first()

    def get_by_id(self, user_id: int) -> models.User | None:
        return self.db.query(models.User).filter(
            models.User.id == user_id
        ).first()

    def get_all(self) -> list[models.User]:
        return self.db.query(models.User).all()

    def create(self, username: str, password: str, role_id: int) -> models.User:
        user = models.User(
            username=username,
            password=hash_password(password),
            role_id=role_id
        )
        self.db.add(user)
        self.db.commit()
        self.db.refresh(user)
        return user

    def update(self, user: models.User) -> models.User:
        self.db.commit()
        self.db.refresh(user)
        return user

    def get_role_by_name(self, name: str) -> models.Role | None:
        return self.db.query(models.Role).filter(
            models.Role.name == name
        ).first()

    def get_role_by_id(self, role_id: int) -> models.Role | None:
        return self.db.query(models.Role).filter(
            models.Role.id == role_id
        ).first()

    def get_all_roles(self) -> list[models.Role]:
        return self.db.query(models.Role).all()

    def create_role(self, name: str, description: str | None) -> models.Role:
        role = models.Role(name=name, description=description)
        self.db.add(role)
        self.db.commit()
        self.db.refresh(role)
        return role

    def delete_role(self, role: models.Role) -> None:
        self.db.delete(role)
        self.db.commit()

    def count_users_with_role(self, role_id: int) -> int:
        return self.db.query(models.User).filter(
            models.User.role_id == role_id
        ).count()