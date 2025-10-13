"""
Класс для работы с базой данных
"""
from datetime import datetime
from typing import Optional, List
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import select, func, update
from loguru import logger

from app.config import settings
from .models import Base, User, BotStats, MigrationHistory, Creative, InviteLink
from .migrations import MigrationManager


class Database:
    """Класс для работы с базой данных"""
    
    def __init__(self):
        # Преобразуем URL для асинхронной работы
        async_url = settings.database_url.replace("postgresql://", "postgresql+asyncpg://")
        
        self.engine = create_async_engine(
            async_url,
            echo=False,
            pool_pre_ping=True
        )
        
        self.session_maker = async_sessionmaker(
            bind=self.engine,
            class_=AsyncSession,
            expire_on_commit=False
        )
        
        # Инициализируем менеджер миграций
        self.migration_manager = MigrationManager(self.engine)
    
    async def run_migrations(self):
        """Запуск всех неприменённых миграций"""
        try:
            await self.migration_manager.run_migrations()
            logger.info("✅ Database migrations completed successfully")
        except Exception as e:
            logger.error(f"❌ Failed to run migrations: {e}")
            raise
    
    async def create_tables(self):
        """Создание таблиц в базе данных"""
        # Сначала запускаем миграции
        await self.run_migrations()
        
        # Затем создаем таблицы через SQLAlchemy (для новых моделей)
        async with self.engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        logger.info("✅ Database tables created successfully")
    
    async def add_user(self, user_id: int, username: Optional[str] = None, 
                      first_name: Optional[str] = None, last_name: Optional[str] = None) -> User:
        """Добавление нового пользователя"""
        async with self.session_maker() as session:
            # Проверяем, существует ли пользователь
            existing_user = await session.get(User, user_id)
            if existing_user:
                # Обновляем данные существующего пользователя
                existing_user.username = username
                existing_user.first_name = first_name
                existing_user.last_name = last_name
                existing_user.is_active = True
                existing_user.updated_at = datetime.utcnow()
                await session.commit()
                return existing_user
            
            # Создаем нового пользователя
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Получение пользователя по ID"""
        async with self.session_maker() as session:
            return await session.get(User, user_id)
    
    async def get_all_users(self) -> List[User]:
        """Получение всех пользователей"""
        async with self.session_maker() as session:
            result = await session.execute(select(User))
            return result.scalars().all()
    
    async def get_active_users(self) -> List[User]:
        """Получение активных пользователей"""
        async with self.session_maker() as session:
            result = await session.execute(select(User).where(User.is_active == True))
            return result.scalars().all()
    
    async def get_users_count(self) -> int:
        """Получение количества пользователей"""
        async with self.session_maker() as session:
            result = await session.execute(select(func.count(User.id)))
            return result.scalar() or 0
    
    async def get_active_users_count(self) -> int:
        """Получение количества активных пользователей"""
        async with self.session_maker() as session:
            result = await session.execute(select(func.count(User.id)).where(User.is_active == True))
            return result.scalar() or 0
    
    async def update_bot_stats(self) -> BotStats:
        """Обновление статистики бота"""
        async with self.session_maker() as session:
            total_users = await self.get_users_count()
            active_users = await self.get_active_users_count()
            
            # Получаем последнюю запись статистики
            result = await session.execute(select(BotStats).order_by(BotStats.id.desc()).limit(1))
            stats = result.scalar_one_or_none()
            
            if stats:
                # Обновляем существующую запись
                stats.total_users = total_users
                stats.active_users = active_users
                stats.last_restart = datetime.utcnow()
            else:
                # Создаем новую запись
                stats = BotStats(
                    total_users=total_users,
                    active_users=active_users,
                    last_restart=datetime.utcnow()
                )
                session.add(stats)
            
            await session.commit()
            await session.refresh(stats)
            return stats
    
    async def get_bot_stats(self) -> Optional[BotStats]:
        """Получение статистики бота"""
        async with self.session_maker() as session:
            result = await session.execute(select(BotStats).order_by(BotStats.id.desc()).limit(1))
            return result.scalar_one_or_none()
    
    async def get_migration_history(self) -> List[MigrationHistory]:
        """Получение истории миграций"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(MigrationHistory).order_by(MigrationHistory.applied_at.desc())
            )
            return result.scalars().all()
    
    async def save_creative(
        self,
        user_id: int,
        form: str,
        kktu_code: str,
        erid: Optional[str] = None,
        media_file_id: Optional[str] = None,
        media_file_name: Optional[str] = None,
        text_data: Optional[str] = None,
        mediascout_id: Optional[str] = None,
        creative_group_id: Optional[str] = None,
        creative_group_name: Optional[str] = None,
        status: str = "created",
        error_message: Optional[str] = None
    ) -> Creative:
        """Сохранение креатива в базу данных"""
        async with self.session_maker() as session:
            creative = Creative(
                user_id=user_id,
                form=form,
                kktu_code=kktu_code,
                erid=erid,
                media_file_id=media_file_id,
                media_file_name=media_file_name,
                text_data=text_data,
                mediascout_id=mediascout_id,
                creative_group_id=creative_group_id,
                creative_group_name=creative_group_name,
                status=status,
                error_message=error_message
            )
            session.add(creative)
            await session.commit()
            await session.refresh(creative)
            return creative
    
    async def get_creative(self, creative_id: int) -> Optional[Creative]:
        """Получение креатива по ID"""
        async with self.session_maker() as session:
            return await session.get(Creative, creative_id)
    
    async def get_creative_by_erid(self, erid: str) -> Optional[Creative]:
        """Получение креатива по токену Erid"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(Creative).where(Creative.erid == erid)
            )
            return result.scalar_one_or_none()
    
    async def get_user_creatives(
        self, 
        user_id: int, 
        limit: int = 50, 
        offset: int = 0
    ) -> List[Creative]:
        """Получение креативов пользователя"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(Creative)
                .where(Creative.user_id == user_id)
                .order_by(Creative.created_at.desc())
                .limit(limit)
                .offset(offset)
            )
            return result.scalars().all()
    
    async def get_user_creatives_count(self, user_id: int) -> int:
        """Получение количества креативов пользователя"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(func.count(Creative.id)).where(Creative.user_id == user_id)
            )
            return result.scalar() or 0
    
    async def update_creative_status(
        self,
        creative_id: int,
        status: str,
        error_message: Optional[str] = None
    ) -> Optional[Creative]:
        """Обновление статуса креатива"""
        async with self.session_maker() as session:
            creative = await session.get(Creative, creative_id)
            if creative:
                creative.status = status
                creative.error_message = error_message
                creative.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(creative)
            return creative
    
    # Методы для работы с пригласительными ссылками
    
    async def create_invite_link(
        self,
        code: str,
        created_by: int,
        target_role: str = "employee",
        full_name: Optional[str] = None,
        expires_at: Optional[datetime] = None
    ) -> InviteLink:
        """Создание пригласительной ссылки"""
        async with self.session_maker() as session:
            invite_link = InviteLink(
                code=code,
                created_by=created_by,
                target_role=target_role,
                full_name=full_name,
                expires_at=expires_at
            )
            session.add(invite_link)
            await session.commit()
            await session.refresh(invite_link)
            return invite_link
    
    async def get_invite_link_by_code(self, code: str) -> Optional[InviteLink]:
        """Получение пригласительной ссылки по коду"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(InviteLink).where(InviteLink.code == code)
            )
            return result.scalar_one_or_none()
    
    async def use_invite_link(self, code: str, user_id: int) -> Optional[InviteLink]:
        """Использование пригласительной ссылки"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(InviteLink).where(InviteLink.code == code)
            )
            invite_link = result.scalar_one_or_none()
            
            if invite_link and not invite_link.is_used:
                invite_link.is_used = True
                invite_link.used_by = user_id
                invite_link.used_at = datetime.utcnow()
                await session.commit()
                await session.refresh(invite_link)
                return invite_link
            return None
    
    async def get_user_invite_links(self, user_id: int) -> List[InviteLink]:
        """Получение всех пригласительных ссылок, созданных пользователем"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(InviteLink)
                .where(InviteLink.created_by == user_id)
                .order_by(InviteLink.created_at.desc())
            )
            return result.scalars().all()
    
    async def delete_invite_link(self, code: str) -> bool:
        """Удаление пригласительной ссылки"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(InviteLink).where(InviteLink.code == code)
            )
            invite_link = result.scalar_one_or_none()
            
            if invite_link:
                await session.delete(invite_link)
                await session.commit()
                return True
            return False
    
    # Методы для управления пользователями
    
    async def update_user_role(self, user_id: int, role: str) -> Optional[User]:
        """Обновление роли пользователя"""
        async with self.session_maker() as session:
            user = await session.get(User, user_id)
            if user:
                user.role = role
                user.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(user)
            return user
    
    async def block_user(self, user_id: int) -> Optional[User]:
        """Блокировка пользователя"""
        async with self.session_maker() as session:
            user = await session.get(User, user_id)
            if user:
                user.is_blocked = True
                user.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(user)
            return user
    
    async def unblock_user(self, user_id: int) -> Optional[User]:
        """Разблокировка пользователя"""
        async with self.session_maker() as session:
            user = await session.get(User, user_id)
            if user:
                user.is_blocked = False
                user.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(user)
            return user
    
    async def update_user_full_name(self, user_id: int, full_name: str) -> Optional[User]:
        """Обновление ФИО пользователя"""
        async with self.session_maker() as session:
            user = await session.get(User, user_id)
            if user:
                user.full_name = full_name
                user.updated_at = datetime.utcnow()
                await session.commit()
                await session.refresh(user)
            return user
    
    async def get_employees(self) -> List[User]:
        """Получение всех сотрудников (не админов)"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User)
                .where(User.role == "employee")
                .order_by(User.created_at.desc())
            )
            return result.scalars().all()
    
    async def get_admins(self) -> List[User]:
        """Получение всех администраторов"""
        async with self.session_maker() as session:
            result = await session.execute(
                select(User)
                .where(User.role == "admin")
                .order_by(User.created_at.desc())
            )
            return result.scalars().all()
    
    async def delete_user(self, user_id: int) -> bool:
        """Удаление пользователя"""
        async with self.session_maker() as session:
            user = await session.get(User, user_id)
            if user:
                await session.delete(user)
                await session.commit()
                return True
            return False
    
    async def add_user_with_invite(
        self,
        user_id: int,
        username: Optional[str] = None,
        first_name: Optional[str] = None,
        last_name: Optional[str] = None,
        full_name: Optional[str] = None,
        role: str = "employee",
        invited_by: Optional[int] = None
    ) -> User:
        """Добавление пользователя через пригласительную ссылку"""
        async with self.session_maker() as session:
            # Проверяем, существует ли пользователь
            existing_user = await session.get(User, user_id)
            if existing_user:
                # Обновляем данные существующего пользователя
                existing_user.username = username
                existing_user.first_name = first_name
                existing_user.last_name = last_name
                existing_user.full_name = full_name
                existing_user.role = role
                existing_user.invited_by = invited_by
                existing_user.is_active = True
                existing_user.is_blocked = False
                existing_user.updated_at = datetime.utcnow()
                await session.commit()
                return existing_user
            
            # Создаем нового пользователя
            user = User(
                id=user_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
                full_name=full_name,
                role=role,
                invited_by=invited_by,
                is_active=True,
                is_blocked=False
            )
            session.add(user)
            await session.commit()
            await session.refresh(user)
            return user


# Создаем глобальный экземпляр базы данных
db = Database() 