"""
Миграция: Добавление таблицы creatives для хранения креативов Erid

Version: 20241213_000001
Created: 2024-12-13
"""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncConnection
from loguru import logger

from app.database.migrations.base import Migration


class AddCreativesTable(Migration):
    """Добавление таблицы creatives"""
    
    def get_version(self) -> str:
        return "20241213_000001"
    
    def get_description(self) -> str:
        return "Добавление таблицы creatives для хранения креативов Erid"
    
    async def upgrade(self, connection: AsyncConnection) -> None:
        """Применить миграцию"""
        
        # Проверяем существует ли таблица creatives
        result = await connection.execute(text("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_schema = 'public' 
                AND table_name = 'creatives'
            );
        """))
        creatives_exists = result.scalar()
        
        if not creatives_exists:
            logger.info("Creating creatives table...")
            await connection.execute(text("""
                CREATE TABLE creatives (
                    id SERIAL PRIMARY KEY,
                    user_id BIGINT NOT NULL,
                    
                    -- Данные креатива
                    form VARCHAR(50) NOT NULL,
                    kktu_code VARCHAR(20) NOT NULL,
                    erid VARCHAR(255),
                    
                    -- Медиаданные
                    media_file_id VARCHAR(255),
                    media_file_name VARCHAR(255),
                    text_data TEXT,
                    
                    -- ID из Медиаскаут
                    mediascout_id VARCHAR(255),
                    creative_group_id VARCHAR(255),
                    creative_group_name VARCHAR(255),
                    
                    -- Статус
                    status VARCHAR(50) DEFAULT 'draft',
                    error_message TEXT,
                    
                    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
                );
            """))
            
            # Создаем индекс по user_id для быстрого поиска
            await connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_creatives_user_id 
                ON creatives(user_id);
            """))
            
            # Создаем индекс по erid для поиска по токену
            await connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_creatives_erid 
                ON creatives(erid);
            """))
            
            # Создаем индекс по статусу
            await connection.execute(text("""
                CREATE INDEX IF NOT EXISTS idx_creatives_status 
                ON creatives(status);
            """))
            
            logger.info("✅ Successfully created creatives table with indexes")
        else:
            logger.info("Table 'creatives' already exists, skipping...")
    
    async def downgrade(self, connection: AsyncConnection) -> None:
        """Откатить миграцию"""
        await connection.execute(text("DROP INDEX IF EXISTS idx_creatives_status;"))
        await connection.execute(text("DROP INDEX IF EXISTS idx_creatives_erid;"))
        await connection.execute(text("DROP INDEX IF EXISTS idx_creatives_user_id;"))
        await connection.execute(text("DROP TABLE IF EXISTS creatives;"))
        logger.info("✅ Dropped creatives table and indexes")

