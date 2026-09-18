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

    def get_by_email(self, email: str) -> models.User | None:
        return self.db.query(models.User).filter(
            models.User.email == email
        ).first()

    def get_by_id(self, user_id: int) -> models.User | None:
        return self.db.query(models.User).filter(
            models.User.id == user_id
        ).first()

    def get_all(self) -> list[models.User]:
        return self.db.query(models.User).all()

    def create(self, username: str, email: str, password: str, role_id: int) -> models.User:
        user = models.User(
            username=username,
            email=email,
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

    def update_role(self, role: models.Role) -> models.Role:
        self.db.commit()
        self.db.refresh(role)
        return role

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

    # ── Recuperación de contraseña ───────────────────────────────────────────

    def create_reset_code(self, user_id: int, code_hash: str, expires_at) -> models.PasswordResetCode:
        # Invalida cualquier código anterior sin usar: solo el último pedido sirve
        self.db.query(models.PasswordResetCode).filter(
            models.PasswordResetCode.user_id == user_id,
            models.PasswordResetCode.used == 0
        ).update({"used": 1})

        reset_code = models.PasswordResetCode(
            user_id=user_id, code_hash=code_hash, expires_at=expires_at
        )
        self.db.add(reset_code)
        self.db.commit()
        self.db.refresh(reset_code)
        return reset_code

    def get_active_reset_code(self, user_id: int) -> models.PasswordResetCode | None:
        return self.db.query(models.PasswordResetCode).filter(
            models.PasswordResetCode.user_id == user_id,
            models.PasswordResetCode.used == 0
        ).order_by(models.PasswordResetCode.created_at.desc()).first()

    def mark_reset_code_used(self, reset_code: models.PasswordResetCode) -> None:
        reset_code.used = 1
        self.db.commit()

    def update_password(self, user: models.User, new_password: str) -> models.User:
        user.password = hash_password(new_password)
        self.db.commit()
        self.db.refresh(user)
        return user