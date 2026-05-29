from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import date
from app import models


class MessageRepository:
    """Acceso a la BD para mensajes y deliveries. Sin lógica de negocio."""

    def __init__(self, db: Session):
        self.db = db

    def create_message(self, user_id: int, content: str) -> models.Message:
        message = models.Message(user_id=user_id, content=content)
        self.db.add(message)
        self.db.commit()
        self.db.refresh(message)
        return message

    def create_delivery(
        self,
        message_id: int,
        service: str,
        status: str,
        provider_response: str,
        attempt: int
    ) -> models.MessageDelivery:
        delivery = models.MessageDelivery(
            message_id=message_id,
            service=service,
            status=status,
            provider_response=provider_response,
            attempt=attempt
        )
        self.db.add(delivery)
        self.db.commit()
        self.db.refresh(delivery)
        return delivery

    def get_messages_by_user(
        self,
        user_id: int,
        status: str | None = None,
        service: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[models.Message]:
        query = self.db.query(models.Message).filter(
            models.Message.user_id == user_id
        )
        return self._apply_filters(query, status, service, from_date, to_date).all()

    def get_all_messages(
        self,
        status: str | None = None,
        service: str | None = None,
        from_date: str | None = None,
        to_date: str | None = None,
    ) -> list[models.Message]:
        query = self.db.query(models.Message)
        return self._apply_filters(query, status, service, from_date, to_date).all()

    def _apply_filters(self, query, status, service, from_date, to_date):
        if from_date:
            query = query.filter(models.Message.created_at >= from_date)
        if to_date:
            query = query.filter(models.Message.created_at <= to_date)
        if service or status:
            query = query.join(models.MessageDelivery)
            if service:
                query = query.filter(models.MessageDelivery.service == service)
            if status:
                query = query.filter(models.MessageDelivery.status == status)
        return query

    def count_messages_by_user(self, user_id: int) -> int:
        return self.db.query(func.count(models.Message.id)).filter(
            models.Message.user_id == user_id
        ).scalar()

    def count_deliveries_by_user(self, user_id: int, status: str | None = None) -> int:
        query = self.db.query(func.count(models.MessageDelivery.id)).join(
            models.Message
        ).filter(models.Message.user_id == user_id)
        if status:
            query = query.filter(models.MessageDelivery.status == status)
        return query.scalar()

    def get_daily_usage(self, user_id: int, usage_date: date) -> models.DailyUsage | None:
        return self.db.query(models.DailyUsage).filter(
            models.DailyUsage.user_id == user_id,
            models.DailyUsage.usage_date == usage_date
        ).first()

    def get_daily_stats(
        self,
        from_date: str | None = None,
        to_date: str | None = None
    ) -> list:
        query = self.db.query(
            func.date(models.Message.created_at).label("dia"),
            func.count(models.Message.id).label("total_mensajes")
        ).group_by(func.date(models.Message.created_at))
        if from_date:
            query = query.filter(models.Message.created_at >= from_date)
        if to_date:
            query = query.filter(models.Message.created_at <= to_date)
        return query.order_by(func.date(models.Message.created_at).desc()).all()

    def count_deliveries_by_date_and_status(self, day, status: str) -> int:
        return self.db.query(func.count(models.MessageDelivery.id)).join(
            models.Message
        ).filter(
            func.date(models.Message.created_at) == day,
            models.MessageDelivery.status == status
        ).scalar()

    def get_config(self) -> models.Config | None:
        return self.db.query(models.Config).filter(models.Config.id == 1).first()

    def update_config(self, config: models.Config) -> models.Config:
        self.db.commit()
        self.db.refresh(config)
        return config

    def create_audit(
        self,
        changed_by: int,
        target_user_id: int | None,
        old_limit: int,
        new_limit: int
    ) -> models.LimitAudit:
        audit = models.LimitAudit(
            changed_by=changed_by,
            target_user_id=target_user_id,
            old_limit=old_limit,
            new_limit=new_limit
        )
        self.db.add(audit)
        self.db.commit()
        return audit

    def get_all_audits(self) -> list[models.LimitAudit]:
        return self.db.query(models.LimitAudit).order_by(
            models.LimitAudit.changed_at.desc()
        ).all()