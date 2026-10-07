import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, DateTime, Boolean, ForeignKey, Text
from sqlalchemy.orm import relationship
from app.core.database import Base

def generate_uuid() -> str:
    return str(uuid.uuid4())

class ExtensionDevice(Base):
    __tablename__ = "extension_devices"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    device_id = Column(String(100), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    device_name = Column(String(100), nullable=True)
    hashed_refresh_token = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    last_used_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    revoked_at = Column(DateTime(timezone=True), nullable=True, index=True)

    user = relationship("User", back_populates="extension_devices")

    @property
    def is_revoked(self) -> bool:
        return self.revoked_at is not None

class ExtensionPairingCode(Base):
    __tablename__ = "extension_pairing_codes"

    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    code_hash = Column(String(64), nullable=False, index=True)
    is_used = Column(Boolean, default=False, nullable=False)
    expires_at = Column(DateTime(timezone=True), nullable=False, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), nullable=False)
    used_at = Column(DateTime(timezone=True), nullable=True)

    user = relationship("User", back_populates="pairing_codes")
