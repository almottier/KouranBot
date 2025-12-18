"""Database models and operations for KouranBot."""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import List, Optional

from sqlalchemy import (
    BigInteger, Boolean, Column, DateTime, ForeignKey, Integer, String, Text,
    create_engine, UniqueConstraint
)
from sqlalchemy.orm import declarative_base, relationship, sessionmaker, Session, joinedload

from bot.config import DATABASE_URL

logger = logging.getLogger(__name__)

Base = declarative_base()
engine = create_engine(DATABASE_URL, echo=False, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autocommit=False, autoflush=False)


def init_database():
    """Create all tables in the database."""
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


class User(Base):
    """User model for storing Telegram user information."""
    __tablename__ = "users"

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    telegram_id = Column(BigInteger, unique=True, nullable=False, index=True)
    username = Column(String(255))
    language = Column(String(2), default="fr")
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    subscriptions = relationship("Subscription", back_populates="user", cascade="all, delete-orphan")


class District(Base):
    """District model for storing district information."""
    __tablename__ = "districts"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), unique=True, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    localities = relationship("Locality", back_populates="district", cascade="all, delete-orphan")


class Locality(Base):
    """Locality model for storing locality information."""
    __tablename__ = "localities"
    __table_args__ = (UniqueConstraint("name", "district_id", name="uq_locality_district"),)

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    district_id = Column(Integer, ForeignKey("districts.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    district = relationship("District", back_populates="localities")
    subscriptions = relationship("Subscription", back_populates="locality", cascade="all, delete-orphan")


class Subscription(Base):
    """Subscription model for user-locality relationships."""
    __tablename__ = "subscriptions"
    __table_args__ = (UniqueConstraint("user_id", "locality_id", name="uq_user_locality"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False, index=True)
    locality_id = Column(Integer, ForeignKey("localities.id", ondelete="CASCADE"), nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    user = relationship("User", back_populates="subscriptions")
    locality = relationship("Locality", back_populates="subscriptions")


class Outage(Base):
    """Outage model for storing power outage information."""
    __tablename__ = "outages"

    id = Column(String(255), primary_key=True)
    locality = Column(String(255), nullable=False, index=True)
    district = Column(String(255), nullable=False, index=True)
    streets = Column(Text)
    date_description = Column(Text)
    from_time = Column(DateTime, nullable=False)
    to_time = Column(DateTime, nullable=False)
    first_seen = Column(DateTime, default=datetime.utcnow)
    last_checked = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    notifications = relationship("NotificationSent", back_populates="outage", cascade="all, delete-orphan")


class NotificationSent(Base):
    """NotificationSent model for tracking sent notifications."""
    __tablename__ = "notifications_sent"
    __table_args__ = (UniqueConstraint("user_id", "outage_id", name="uq_user_outage"),)

    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(BigInteger, ForeignKey("users.telegram_id", ondelete="CASCADE"), nullable=False)
    outage_id = Column(String(255), ForeignKey("outages.id", ondelete="CASCADE"), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow)

    outage = relationship("Outage", back_populates="notifications")


def get_db() -> Session:
    """Get database session."""
    db = SessionLocal()
    try:
        return db
    except Exception:
        db.close()
        raise


def init_localities_from_json():
    """Initialize districts and localities from districts_localities.json file."""
    json_path = Path(__file__).parent.parent / "districts_localities.json"

    if not json_path.exists():
        logger.error(f"districts_localities.json not found at {json_path}")
        return

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    db = get_db()
    try:
        # Check if already initialized
        existing_districts = db.query(District).count()
        if existing_districts > 0:
            logger.info("Districts and localities already initialized")
            return

        logger.info("Initializing districts and localities from JSON...")

        for district_name, localities_list in data.items():
            # Create district
            district = District(name=district_name)
            db.add(district)
            db.flush()  # Get the district ID

            # Create localities for this district
            for locality_name in localities_list:
                locality = Locality(name=locality_name, district_id=district.id)
                db.add(locality)

        db.commit()

        total_districts = db.query(District).count()
        total_localities = db.query(Locality).count()
        logger.info(f"Initialized {total_districts} districts and {total_localities} localities")

    except Exception as e:
        db.rollback()
        logger.error(f"Error initializing localities: {e}")
        raise
    finally:
        db.close()


def get_or_create_user(db: Session, telegram_id: int, username: Optional[str] = None, language_code: Optional[str] = None) -> User:
    """Get existing user or create new one."""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        # Detect language from Telegram account, default to 'fr' if not supported
        detected_lang = "fr"  # Default for Mauritius
        if language_code:
            # Use user's Telegram language if it's one we support (en or fr)
            if language_code.lower().startswith(('en', 'fr')):
                detected_lang = language_code.lower()[:2]

        user = User(telegram_id=telegram_id, username=username, language=detected_lang)
        db.add(user)
        db.commit()
        db.refresh(user)
        logger.info(f"Created new user: {telegram_id} ({username}) with language: {detected_lang}")
    elif user.username != username:
        user.username = username
        user.updated_at = datetime.utcnow()
        db.commit()

    return user


def get_all_districts(db: Session) -> List[District]:
    """Get all districts ordered by name."""
    return db.query(District).order_by(District.name).all()


def get_localities_by_district(db: Session, district_id: int) -> List[Locality]:
    """Get all localities for a specific district."""
    return db.query(Locality).filter(
        Locality.district_id == district_id
    ).options(joinedload(Locality.district)).order_by(Locality.name).all()


def get_user_subscriptions(db: Session, telegram_id: int) -> List[Locality]:
    """Get all localities a user is subscribed to."""
    return db.query(Locality).join(Subscription).filter(
        Subscription.user_id == telegram_id
    ).options(joinedload(Locality.district)).order_by(Locality.name).all()


def add_subscription(db: Session, telegram_id: int, locality_id: int) -> bool:
    """Add a subscription for a user. Returns True if added, False if already exists."""
    existing = db.query(Subscription).filter(
        Subscription.user_id == telegram_id,
        Subscription.locality_id == locality_id
    ).first()

    if existing:
        return False

    subscription = Subscription(user_id=telegram_id, locality_id=locality_id)
    db.add(subscription)
    db.commit()
    logger.info(f"User {telegram_id} subscribed to locality {locality_id}")
    return True


def remove_subscription(db: Session, telegram_id: int, locality_id: int) -> bool:
    """Remove a subscription. Returns True if removed, False if didn't exist."""
    subscription = db.query(Subscription).filter(
        Subscription.user_id == telegram_id,
        Subscription.locality_id == locality_id
    ).first()

    if not subscription:
        return False

    db.delete(subscription)
    db.commit()
    logger.info(f"User {telegram_id} unsubscribed from locality {locality_id}")
    return True


def remove_all_subscriptions(db: Session, telegram_id: int) -> int:
    """Remove all subscriptions for a user. Returns count of removed subscriptions."""
    count = db.query(Subscription).filter(Subscription.user_id == telegram_id).delete()
    db.commit()
    logger.info(f"Removed {count} subscriptions for user {telegram_id}")
    return count


def is_subscribed(db: Session, telegram_id: int, locality_id: int) -> bool:
    """Check if user is subscribed to a locality."""
    return db.query(Subscription).filter(
        Subscription.user_id == telegram_id,
        Subscription.locality_id == locality_id
    ).first() is not None


def get_users_subscribed_to_locality(db: Session, locality_name: str) -> List[int]:
    """Get all telegram IDs subscribed to a specific locality name."""
    results = db.query(User.telegram_id).join(Subscription).join(Locality).filter(
        Locality.name == locality_name,
        User.is_active == True
    ).all()

    return [r[0] for r in results]


def get_user_language(db: Session, telegram_id: int) -> str:
    """Get user's language preference."""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if user and user.language:
        return user.language
    return "en"


def set_user_language(db: Session, telegram_id: int, language: str) -> bool:
    """Set user's language preference."""
    user = db.query(User).filter(User.telegram_id == telegram_id).first()
    if not user:
        return False

    user.language = language
    user.updated_at = datetime.utcnow()
    db.commit()
    logger.info(f"User {telegram_id} language changed to {language}")
    return True


def get_users_with_language_for_locality(db: Session, locality_name: str) -> List[tuple]:
    """Get telegram IDs and languages for users subscribed to a locality."""
    results = db.query(User.telegram_id, User.language).join(Subscription).join(Locality).filter(
        Locality.name == locality_name,
        User.is_active == True
    ).all()

    return [(r[0], r[1] or "en") for r in results]
