import asyncio
import logging
import json
import os
from datetime import datetime
from telethon import TelegramClient, events
from telethon.tl.functions.channels import InviteToChannelRequest, GetParticipantsRequest
from telethon.tl.functions.messages import AddChatUserRequest
from telethon.tl.types import ChannelParticipantsSearch, ChannelParticipantsRecent
from telethon.errors import (
    UserAlreadyParticipantError,
    UserPrivacyRestrictedError,
    FloodWaitError,
    ChatAdminRequiredError,
    UserNotMutualContactError,
    UserChannelsTooMuchError,
    PeerFloodError
)
from config import Config

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class UserbotManager:
    def __init__(self):
        self.client = TelegramClient(
            Config.SESSION_NAME,
            Config.API_ID,
            Config.API_HASH
        )
        self.is_running = False
        self.scraped_members = []
        self.added_members = []
        self.stats = {
            'total_scraped': 0,
            'total_added': 0,
            'failed': 0,
            'skipped': 0,
            'flood_waits': 0
        }
        self.results_file = 'results.json'
        self.load_results()
    
    def load_results(self):
        """ផ្ទុកលទ្ធផលពីមុន"""
        if os.path.exists(self.results_file):
            try:
                with open(self.results_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.added_members = data.get('added_members', [])
                    self.stats = data.get('stats', self.stats)
            except:
                pass
    
    def save_results(self):
        """រក្សាទុកលទ្ធផល"""
        results = {
            'stats': self.stats,
            'added_members': self.added_members,
            'last_updated': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        with open(self.results_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
    
    async def start(self):
        """ចាប់ផ្តើម Userbot"""
        if not self.is_running:
            await self.client.start(phone=Config.PHONE_NUMBER)
            self.is_running = True
            logger.info("✅ Userbot បានចាប់ផ្តើម")
    
    async def stop(self):
        """បញ្ឈប់ Userbot"""
        if self.is_running:
            await self.client.disconnect()
            self.is_running = False
            logger.info("🛑 Userbot បានបញ្ឈប់")
    
    async def scrape_members(self, source_group, limit=100, search_keyword=None):
        """ទាញសមាជិកពី Group ផ្សេង"""
        try:
            source_entity = await self.client.get_entity(source_group)
            members = []
            offset = 0
            
            while len(members) < limit:
                try:
                    participants = await self.client(GetParticipantsRequest(
                        channel=source_entity,
                        filter=ChannelParticipantsSearch(search_keyword) if search_keyword else ChannelParticipantsRecent(),
                        offset=offset,
                        limit=min(100, limit - len(members)),
                        hash=0
                    ))
                    
                    if not participants.users:
                        break
                    
                    members.extend(participants.users)
                    offset += len(participants.users)
                    
                    logger.info(f"📥 ទាញបាន {len(members)} សមាជិក")
                    await asyncio.sleep(2)
                    
                except FloodWaitError as e:
                    logger.warning(f"⏳ Flood Wait: {e.seconds} វិនាទី")
                    self.stats['flood_waits'] += 1
                    await asyncio.sleep(e.seconds)
                    continue
            
            self.scraped_members = members
            self.stats['total_scraped'] = len(members)
            return members
            
        except Exception as e:
            logger.error(f"❌ កំហុសក្នុងការទាញសមាជិក: {e}")
            raise
    
    async def add_members_to_group(self, members, target_group=None, delay=3):
        """បន្ថែមសមាជិកទៅក្នុង Group"""
        if not target_group:
            target_group = Config.TARGET_GROUP
        
        target_entity = await self.client.get_entity(target_group)
        
        self.stats['total_added'] = 0
        self.stats['failed'] = 0
        self.stats['skipped'] = 0
        
        for i, member in enumerate(members, 1):
            try:
                if member.bot or member.deleted:
                    self.stats['skipped'] += 1
                    continue
                
                try:
                    await self.client(AddChatUserRequest(
                        chat_id=target_entity.id,
                        user_id=member.id,
                        fwd_limit=10
                    ))
                    
                    self.stats['total_added'] += 1
                    self.added_members.append({
                        'id': member.id,
                        'username': member.username or '',
                        'first_name': member.first_name or '',
                        'last_name': member.last_name or '',
                        'added_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    })
                    
                    logger.info(f"✅ [{i}/{len(members)}] បានបន្ថែម {member.first_name}")
                    
                except UserAlreadyParticipantError:
                    self.stats['skipped'] += 1
                    logger.info(f"⏭️ {member.first_name} មានរួចហើយ")
                    
                except UserPrivacyRestrictedError:
                    self.stats['failed'] += 1
                    logger.warning(f"🔒 {member.first_name} មាន Privacy")
                    
                except UserNotMutualContactError:
                    self.stats['failed'] += 1
                    logger.warning(f"👤 {member.first_name} មិនមែនជា Contact")
                    
                except FloodWaitError as e:
                    logger.warning(f"⏳ Flood Wait: {e.seconds} វិនាទី")
                    self.stats['flood_waits'] += 1
                    await asyncio.sleep(e.seconds)
                    # ព្យាយាមម្តងទៀត
                    try:
                        await self.client(AddChatUserRequest(
                            chat_id=target_entity.id,
                            user_id=member.id,
                            fwd_limit=10
                        ))
                        self.stats['total_added'] += 1
                        logger.info(f"✅ បានបន្ថែម {member.first_name} បន្ទាប់ពីរង់ចាំ")
                    except:
                        self.stats['failed'] += 1
                        
                except PeerFloodError:
                    logger.error("🚫 គណនីត្រូវបានកំណត់ដោយសារ Flood")
                    break
                    
                except Exception as e:
                    self.stats['failed'] += 1
                    logger.error(f"❌ កំហុស: {e}")
                
                await asyncio.sleep(delay)
                
            except Exception as e:
                logger.error(f"❌ កំហុសទូទៅ: {e}")
                continue
        
        self.save_results()
        return self.stats
    
    async def scrape_and_add(self, source_group, limit=100, delay=3):
        """ទាញសមាជិកហើយបន្ថែមភ្លាមៗ"""
        members = await self.scrape_members(source_group, limit)
        if members:
            await self.add_members_to_group(members, delay=delay)
        return self.stats
    
    def get_status(self):
        """ទាញស្ថានភាពបច្ចុប្បន្ន"""
        return {
            'is_running': self.is_running,
            'stats': self.stats,
            'total_scraped': len(self.scraped_members),
            'total_added': len(self.added_members),
            'added_members': self.added_members[-10:]  # 10 ចុងក្រោយ
        }
