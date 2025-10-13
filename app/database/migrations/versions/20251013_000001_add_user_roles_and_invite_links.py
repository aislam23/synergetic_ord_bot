"""
Миграция: Добавление ролей пользователей и таблицы пригласительных ссылок

Version: 20251013_000001
Created: 2025-10-13
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from loguru import logger

from app.database.migrations.base import Migration


class AddUserRolesAndInviteLinks(Migration):
    """Добавление полей role, is_blocked, invited_by в таблицу users и создание таблицы invite_links"""
    
    def get_version(self) -> str:
        return "20251013_000001"
    
    def get_description(self) -> str:
        return "Добавление ролей пользователей и таблицы пригласительных ссылок"
    
    async def upgrade(self, connection: AsyncConnection) -> None:
        """Применить миграцию"""
        
        # Добавляем новые поля в таблицу users
        logger.info("Adding new columns to users table...")
        
        # Проверяем и добавляем колонку full_name
        result = await connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='full_name';
        """))
        if not result.scalar():
            await connection.execute(text("""
                ALTER TABLE users ADD COLUMN full_name VARCHAR(500);
            """))
            logger.info("✅ Added column 'full_name'")
        
        # Проверяем и добавляем колонку role
        result = await connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='role';
        """))
        if not result.scalar():
            await connection.execute(text("""
                ALTER TABLE users ADD COLUMN role VARCHAR(50) DEFAULT 'employee';
            """))
            logger.info("✅ Added column 'role'")
        
        # Проверяем и добавляем колонку is_blocked
        result = await connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='is_blocked';
        """))
        if not result.scalar():
            await connection.execute(text("""
                ALTER TABLE users ADD COLUMN is_blocked BOOLEAN DEFAULT FALSE;
            """))
            logger.info("✅ Added column 'is_blocked'")
        
        # Проверяем и добавляем колонку invited_by
        result = await connection.execute(text("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='users' AND column_name='invited_by';
        """))
        if not result.scalar():
            await connection.execute(text("""
                ALTER TABLE users ADD COLUMN invited_by BIGINT;
            """))
            logger.info("✅ Added column 'invited_by'")
        
        # Создаем таблицу invite_links
        result = await connection.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'invite_links'
            );
        """))
        invite_links_exists = result.scalar()
        
        if not invite_links_exists:
            logger.info("Creating invite_links table...")
            await connection.execute(text("""
                CREATE TABLE invite_links (
                    id SERIAL PRIMARY KEY,
                    code VARCHAR(100) UNIQUE NOT NULL,
                    created_by BIGINT NOT NULL,
                    target_role VARCHAR(50) DEFAULT 'employee',
                    full_name VARCHAR(500),
                    
                    -- Статус использования
                    is_used BOOLEAN DEFAULT FALSE,
                    used_by BIGINT,
                    used_at TIMESTAMP WITH TIME ZONE,
                    
                    -- Время создания и срок действия
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP WITH TIME ZONE
                );
            """))
            
            # Создаем индексы
            await connection.execute(text("""
                CREATE UNIQUE INDEX IF NOT EXISTS idx_invite_links_code 
                ON invite_links(code);
            """))
            
            await connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_invite_links_created_by 
                ON invite_links(created_by);
            """))
            
            await connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_invite_links_is_used 
                ON invite_links(is_used);
            """))
            
            logger.info("✅ Successfully created invite_links table with indexes")
        else:
            logger.info("Table 'invite_links' already exists, skipping...")
        
        # Создаем индекс по role для быстрого поиска
        await connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_role 
            ON users(role);
        """))
        
        # Создаем индекс по is_blocked
        await connection.execute(text("""
            CREATE INDEX IF NOT EXISTS idx_users_is_blocked 
            ON users(is_blocked);
        """))
        
        logger.info("✅ Migration completed successfully")
    
    async def downgrade(self, connection: AsyncConnection) -> None:
        """Откатить миграцию"""
        # Удаляем таблицу invite_links
        await connection.execute(text("DROP INDEX IF EXISTS idx_invite_links_is_used;"))
        await connection.execute(text("DROP INDEX IF EXISTS idx_invite_links_created_by;"))
        await connection.execute(text("DROP INDEX IF EXISTS idx_invite_links_code;"))
        await connection.execute(text("DROP TABLE IF EXISTS invite_links;"))
        
        # Удаляем индексы из users
        await connection.execute(text("DROP INDEX IF EXISTS idx_users_is_blocked;"))
        await connection.execute(text("DROP INDEX IF EXISTS idx_users_role;"))
        
        # Удаляем колонки из users
        await connection.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS invited_by;"))
        await connection.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS is_blocked;"))
        await connection.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS role;"))
        await connection.execute(text("ALTER TABLE users DROP COLUMN IF EXISTS full_name;"))
        
        logger.info("✅ Rollback completed successfully")


