from app import app
from models import db, Projeto, Comentario

# Executar dentro do contexto da aplicação Flask
with app.app_context():
    # Apagar todos os registros das tabelas
    db.session.query(Projeto).delete()
    db.session.query(Comentario).delete()
    db.session.commit()

    print("Todos os registros foram apagados.")
