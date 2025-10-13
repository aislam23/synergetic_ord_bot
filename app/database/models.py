"""
Модели базы данных
"""
from datetime import datetime
from typing import Optional
from sqlalchemy import BigInteger, DateTime, String, Boolean, Integer, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func


class Base(DeclarativeBase):
    """Базовый класс для всех моделей"""
    pass


class User(Base):
    """Модель пользователя"""
    
    __tablename__ = "users"
    
    id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    full_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # ФИО для сотрудников
    role: Mapped[str] = mapped_column(String(50), default="employee")  # admin или employee
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    is_blocked: Mapped[bool] = mapped_column(Boolean, default=False)  # Заблокирован ли доступ
    invited_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # ID админа, который пригласил
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<User(id={self.id}, username={self.username}, role={self.role})>"


class BotStats(Base):
    """Модель статистики бота"""
    
    __tablename__ = "bot_stats"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    total_users: Mapped[int] = mapped_column(Integer, default=0)
    active_users: Mapped[int] = mapped_column(Integer, default=0)
    last_restart: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    status: Mapped[str] = mapped_column(String(50), default="active")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    
    def __repr__(self) -> str:
        return f"<BotStats(total_users={self.total_users}, status={self.status})>"


class MigrationHistory(Base):
    """Модель для отслеживания примененных миграций"""
    
    __tablename__ = "migration_history"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    version: Mapped[str] = mapped_column(String(20), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=True)
    applied_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    execution_time: Mapped[Optional[float]] = mapped_column(nullable=True)  # время выполнения в секундах
    
    def __repr__(self) -> str:
        return f"<MigrationHistory(version={self.version}, name={self.name})>"


class InviteLink(Base):
    """Модель пригласительных ссылок"""
    
    __tablename__ = "invite_links"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)  # Уникальный код приглашения
    created_by: Mapped[int] = mapped_column(BigInteger, nullable=False)  # ID админа, который создал ссылку
    target_role: Mapped[str] = mapped_column(String(50), default="employee")  # Роль для нового пользователя (admin/employee)
    full_name: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)  # ФИО приглашаемого сотрудника
    
    # Статус использования
    is_used: Mapped[bool] = mapped_column(Boolean, default=False)  # Использована ли ссылка
    used_by: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)  # ID пользователя, который использовал ссылку
    used_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Время использования
    
    # Время создания
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)  # Срок действия ссылки
    
    def __repr__(self) -> str:
        return f"<InviteLink(code={self.code}, is_used={self.is_used})>"


class Creative(Base):
    """Модель креатива для саморекламы"""
    
    __tablename__ = "creatives"
    
    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(BigInteger, nullable=False)  # ID пользователя Telegram
    
    # Данные креатива
    form: Mapped[str] = mapped_column(String(50), nullable=False)  # Форма креатива (Banner, Text, etc.)
    kktu_code: Mapped[str] = mapped_column(String(20), nullable=False)  # Код ККТУ
    erid: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Токен Erid
    
    # Медиаданные
    media_file_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # File ID из Telegram
    media_file_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Имя файла
    text_data: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Текстовые данные
    
    # ID из Медиаскаут
    mediascout_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # ID креатива в системе Медиаскаут
    creative_group_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # ID группы креативов
    creative_group_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Имя группы креативов
    
    # Статус
    status: Mapped[str] = mapped_column(String(50), default="draft")  # draft, created, error
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # Сообщение об ошибке
    
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())
    
    def __repr__(self) -> str:
        return f"<Creative(id={self.id}, erid={self.erid}, form={self.form})>" 