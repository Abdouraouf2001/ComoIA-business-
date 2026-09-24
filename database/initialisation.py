from database.models import creer_tables

def initialiser_base():
    creer_tables()
    print("Base de donnees initialisee avec succes")

if __name__=="__main__":
    initialiser_base()