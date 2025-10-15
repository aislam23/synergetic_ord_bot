"""
Сервис для работы с API Медиаскаут
"""
import base64
from typing import Optional, Dict, Any, List
import aiohttp
from loguru import logger

from app.config import settings


class MediascoutAPI:
    """Класс для работы с API Медиаскаут"""
    
    def __init__(self):
        self.base_url = settings.mediascout_api_url
        self.login = settings.mediascout_login
        self.password = settings.mediascout_password
        
    def _get_auth_header(self) -> Dict[str, str]:
        """Получить заголовок авторизации Basic Auth"""
        credentials = f"{self.login}:{self.password}"
        encoded = base64.b64encode(credentials.encode()).decode()
        return {
            "Authorization": f"Basic {encoded}",
            "Content-Type": "application/json"
        }
    
    async def ping(self) -> bool:
        """Проверка связи с API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(f"{self.base_url}/ping") as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ошибка при проверке связи с API: {e}")
            return False
    
    async def ping_auth(self) -> bool:
        """Проверка авторизации в API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/pingauth",
                    headers=self._get_auth_header()
                ) as response:
                    return response.status == 200
        except Exception as e:
            logger.error(f"Ошибка при проверке авторизации: {e}")
            return False
    
    async def get_kktu_codes(self) -> Optional[List[Dict[str, Any]]]:
        """Получить список кодов ККТУ из API"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.base_url}/v3/dictionaries/kktu",
                    headers=self._get_auth_header()
                ) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        logger.error(f"Ошибка при получении ККТУ: {response.status}")
                        return None
        except Exception as e:
            logger.error(f"Ошибка при получении кодов ККТУ: {e}")
            return None
    
    async def create_creative(
        self,
        form: str,
        kktu_code: str,
        media_base64: Optional[str] = None,
        media_filename: Optional[str] = None,
        text_data: Optional[str] = None,
        description: Optional[str] = None,
        advertiser_urls: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Создать креатив саморекламы
        
        Args:
            form: Форма креатива (Banner, Text, etc.)
            kktu_code: Код ККТУ
            media_base64: Медиа-файл в base64 (опционально)
            media_filename: Имя медиа-файла (опционально)
            text_data: Текстовые данные (опционально)
            description: Описание креатива (опционально, обязательно для 30.15.1)
            advertiser_urls: Целевые ссылки (опционально)
            
        Returns:
            Dict с результатом (erid, id, и т.д.) или ошибкой
        """
        
        # Формируем тело запроса
        payload = {
            "form": form,
            "isSelfPromotion": True,
            "type": "Other",
            "isCobranding": False,
            "isNative": False,
            "isSocial": False,
            "isSocialQuota": False,
            "kktuCodes": [kktu_code]
        }
        
        # Добавляем описание, если требуется для кода ККТУ 30.15.1
        if kktu_code == "30.15.1" and description:
            payload["description"] = description
        
        # Добавляем целевые ссылки, если есть
        if advertiser_urls:
            payload["advertiserUrls"] = advertiser_urls
        
        # Добавляем медиа-данные, если есть
        if media_base64 and media_filename:
            payload["mediaData"] = [
                {
                    "fileName": media_filename,
                    "fileContentBase64": media_base64
                }
            ]
        
        # Добавляем текстовые данные, если есть
        if text_data:
            payload["textData"] = [
                {
                    "textData": text_data
                }
            ]
        
        # Логируем запрос (без base64 для читаемости)
        payload_log = payload.copy()
        if "mediaData" in payload_log:
            payload_log["mediaData"] = [
                {**item, "fileContentBase64": f"<base64 data {len(item['fileContentBase64'])} chars>"} 
                for item in payload_log["mediaData"]
            ]
        
        logger.info(f"🔄 Отправка запроса на создание креатива:")
        logger.info(f"   URL: {self.base_url}/v3/creatives")
        logger.info(f"   Payload: {payload_log}")
        logger.info(f"   Auth: {self.login}:***")
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/v3/creatives",
                    headers=self._get_auth_header(),
                    json=payload
                ) as response:
                    # Получаем текст ответа для детального логирования
                    response_text = await response.text()
                    
                    logger.info(f"📥 Ответ от API:")
                    logger.info(f"   Status: {response.status}")
                    logger.info(f"   Headers: {dict(response.headers)}")
                    logger.info(f"   Body: {response_text}")
                    
                    # Пытаемся распарсить JSON
                    try:
                        # Сначала пытаемся прочитать как JSON из text
                        import json
                        response_data = json.loads(response_text) if response_text else {}
                    except json.JSONDecodeError as json_error:
                        logger.error(f"❌ Ошибка парсинга JSON ответа: {json_error}")
                        logger.error(f"   Raw response: {response_text}")
                        return {
                            "success": False,
                            "error": f"Ошибка парсинга ответа API: {response_text[:200]}"
                        }
                    except Exception as json_error:
                        logger.error(f"❌ Неожиданная ошибка парсинга: {json_error}")
                        logger.error(f"   Raw response: {response_text}")
                        return {
                            "success": False,
                            "error": f"Ошибка парсинга ответа API: {str(json_error)}"
                        }
                    
                    if response.status == 201:
                        logger.info(f"✅ Креатив успешно создан: {response_data.get('erid')}")
                        return {
                            "success": True,
                            "erid": response_data.get("erid"),
                            "id": response_data.get("id"),
                            "creative_group_id": response_data.get("creativeGroupId"),
                            "creative_group_name": response_data.get("creativeGroupName"),
                            "data": response_data
                        }
                    else:
                        error_detail = response_data.get("detail", "Неизвестная ошибка")
                        error_title = response_data.get("title", "")
                        errors = response_data.get("errors", {})
                        
                        error_msg = f"{error_title}: {error_detail}"
                        if errors:
                            error_msg += f"\nДетали: {errors}"
                        
                        logger.error(f"❌ Ошибка создания креатива (HTTP {response.status}): {error_msg}")
                        logger.error(f"   Полный ответ: {response_data}")
                        
                        return {
                            "success": False,
                            "error": error_msg,
                            "status": response.status,
                            "full_response": response_data
                        }
                        
        except aiohttp.ClientError as e:
            logger.error(f"❌ Ошибка соединения с API: {e}")
            logger.exception(e)
            return {
                "success": False,
                "error": f"Ошибка соединения: {str(e)}"
            }
        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при создании креатива: {e}")
            logger.exception(e)
            return {
                "success": False,
                "error": f"Неожиданная ошибка: {str(e)}"
            }


# Создаем глобальный экземпляр
mediascout_api = MediascoutAPI()

