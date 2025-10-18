from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from ...models import Setting
from pydantic import BaseModel
from typing import List

router = APIRouter()

class SettingItem(BaseModel):
    key: str
    value: str

class SettingsUpdate(BaseModel):
    settings: List[SettingItem]

@router.get("/settings/{category}")
def get_settings_by_category(category: str, db: Session = Depends(get_db)):
    """
    Gets settings by category.
    """
    settings = db.query(Setting).filter(Setting.category == category).all()
    
    settings_list = [
        {
            "key": s.key,
            "value": s.value,
            "description": s.description
        }
        for s in settings
    ]
    
    return {
        "category": category,
        "settings": settings_list
    }

@router.put("/settings/{category}")
def update_settings_by_category(category: str, settings_update: SettingsUpdate, db: Session = Depends(get_db)):
    """
    Updates settings configuration for a specific category.
    """
    for item in settings_update.settings:
        setting = db.query(Setting).filter(Setting.category == category, Setting.key == item.key).first()
        if setting:
            setting.value = item.value
        else:
            new_setting = Setting(
                category=category,
                key=item.key,
                value=item.value
            )
            db.add(new_setting)
            
    db.commit()
    
    return {"success": True, "message": f"Settings for category '{category}' have been updated."}

@router.get("/notifications/channels")
def list_notification_channels(db: Session = Depends(get_db)):
    """
    Lists all configured notification channels.
    """
    from ...models import NotificationChannel
    
    channels = db.query(NotificationChannel).all()
    
    channels_list = [
        {
            "id": channel.id,
            "channel_type": channel.channel_type,
            "channel_name": channel.channel_name,
            "configuration": channel.configuration,
            "alert_levels": channel.alert_levels,
            "is_active": channel.is_active
        }
        for channel in channels
    ]
    
    return {"channels": channels_list}

class NotificationTest(BaseModel):
    channel_id: int
    message: str

@router.post("/notifications/test")
def test_notification_channel(notification_test: NotificationTest, db: Session = Depends(get_db)):
    """
    Sends a test notification to a specified channel.
    """
    from ...models import NotificationChannel
    
    channel = db.query(NotificationChannel).filter(NotificationChannel.id == notification_test.channel_id).first()
    if not channel:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification channel not found")
        
    # In a real-world application, this would trigger a notification
    # sending service (e.g., email, webhook, Slack).
    
    # Placeholder implementation
    print(f"Sending test notification to channel {channel.channel_name}: {notification_test.message}")
    
    return {"success": True, "message": f"Test notification sent to {channel.channel_name}."}

@router.get("/access-control/roles")
def list_user_roles(db: Session = Depends(get_db)):
    """
    Lists all user roles and their permissions.
    """
    from ...models import Role
    
    roles = db.query(Role).all()
    
    roles_list = [
        {
            "id": role.id,
            "role_name": role.role_name,
            "permissions": role.permissions,
            "description": role.description
        }
        for role in roles
    ]
    
    return {"roles": roles_list}

class RolePermissionsUpdate(BaseModel):
    permissions: dict

@router.put("/access-control/roles/{role_id}")
def update_role_permissions(role_id: int, permissions_update: RolePermissionsUpdate, db: Session = Depends(get_db)):
    """
    Updates the permissions for a specific user role.
    """
    from ...models import Role
    from fastapi import HTTPException
    
    role = db.query(Role).filter(Role.id == role_id).first()
    if not role:
        raise HTTPException(status_code=404, detail="Role not found")
        
    role.permissions = permissions_update.permissions
    db.commit()
    
    return {"success": True, "message": f"Permissions for role '{role.role_name}' have been updated."}





