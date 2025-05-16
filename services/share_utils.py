from sqlalchemy.orm import Session
from models import SharePhoto
from datetime import datetime

def clean_expired_shares(db: Session):
    now = datetime.utcnow()
    expired = db.query(SharePhoto).filter(SharePhoto.expires_at < now).all()
    for share in expired:
        db.delete(share)
    db.commit()
