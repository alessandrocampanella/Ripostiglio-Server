"""Gestione utenti da riga di comando (non esiste registrazione pubblica).

    python -m app.cli create-user mario mario@example.com
    python -m app.cli set-password mario
    python -m app.cli migrate        # applica db/migrations/*.sql (rieseguibili)
"""
import argparse
import getpass
import sys
from pathlib import Path

from sqlalchemy import select

from .db import SessionLocal, engine
from .models import User
from .security import hash_password


def ask_password() -> str:
    password = getpass.getpass("Password: ")
    if len(password) < 8:
        sys.exit("La password deve avere almeno 8 caratteri")
    if password != getpass.getpass("Ripeti password: "):
        sys.exit("Le password non coincidono")
    return password


def migrate() -> None:
    """Applica in ordine gli script di db/migrations: sono scritti per poter essere rieseguiti."""
    for script in sorted((Path(__file__).parent.parent / "db" / "migrations").glob("*.sql")):
        with engine.begin() as connection:
            connection.exec_driver_sql(script.read_text())
        print(f"Applicato {script.name}")


def main() -> None:
    parser = argparse.ArgumentParser(prog="python -m app.cli")
    commands = parser.add_subparsers(dest="command", required=True)
    create = commands.add_parser("create-user")
    create.add_argument("username")
    create.add_argument("email")
    commands.add_parser("set-password").add_argument("username")
    commands.add_parser("migrate")
    args = parser.parse_args()

    if args.command == "migrate":
        migrate()
        return

    username = args.username.strip().lower()
    with SessionLocal() as db:
        user = db.scalar(select(User).where(User.username == username))
        if args.command == "create-user":
            if user:
                sys.exit(f"L'utente {username} esiste già")
            db.add(User(username=username, email=args.email.strip().lower(), password_hash=hash_password(ask_password())))
        else:
            if not user:
                sys.exit(f"L'utente {username} non esiste")
            user.password_hash = hash_password(ask_password())
        db.commit()
    print("Fatto.")


if __name__ == "__main__":
    main()
