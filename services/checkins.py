from sqlalchemy.orm import Session

from models.checkin import CheckinTable


class Checkins:
    # SELECT * FROM checkins WHERE isProcessed = false
    @staticmethod
    def getPendingCheckins(db: Session):
        return db.query(CheckinTable).filter(CheckinTable.isProcessed == False).all()

    # SELECT * FROM checkins WHERE isProcessed = true
    @staticmethod
    def getProcessedCheckins(db: Session):
        return db.query(CheckinTable).filter(CheckinTable.isProcessed == True).all()

    # UPDATE checkins SET obs = :obs WHERE id = :id
    @staticmethod
    def updateObservations(id: int, obs: str, db: Session) -> bool:
        rows = db.query(CheckinTable).filter(CheckinTable.id == id).update({"obs": obs})
        db.commit()
        return rows > 0

    # UPDATE checkins SET isProcessed = true WHERE id = :id
    @staticmethod
    def processCheckin(id: int, db: Session) -> bool:
        rows = db.query(CheckinTable).filter(CheckinTable.id == id).update({"isProcessed": True})
        db.commit()
        return rows > 0
