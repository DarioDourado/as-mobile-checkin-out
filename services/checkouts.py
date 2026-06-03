from sqlalchemy.orm import Session

from models.checkout import CheckoutTable


class Checkouts:
    # SELECT * FROM checkouts WHERE isProcessed = false
    @staticmethod
    def getTodayCheckouts(db: Session):
        return db.query(CheckoutTable).filter(CheckoutTable.isProcessed == False).all()

    # SELECT * FROM checkouts WHERE isProcessed = true
    @staticmethod
    def getProcessedCheckouts(db: Session):
        return db.query(CheckoutTable).filter(CheckoutTable.isProcessed == True).all()

    # UPDATE checkouts SET obs = :obs WHERE id = :id
    @staticmethod
    def updateCheckoutObservations(id: int, obs: str, db: Session) -> bool:
        rows = db.query(CheckoutTable).filter(CheckoutTable.id == id).update({"obs": obs})
        db.commit()
        return rows > 0

    # UPDATE checkouts SET isProcessed = true WHERE id = :id
    @staticmethod
    def processCheckout(id: int, db: Session) -> bool:
        rows = db.query(CheckoutTable).filter(CheckoutTable.id == id).update({"isProcessed": True})
        db.commit()
        return rows > 0
