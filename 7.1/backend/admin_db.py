# NEXO DATA - ADMINISTRADOR DE BASE DE DATOS
# Gestion de Usuarios via Terminal (CRUD)
# Uso:
#   cd C:\Users\Daly\OneDrive\Documentos\Demo7\backend
#   ..\.venv_pdf\Scripts\activate.bat
#   python admin_db.py

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.db.session import SessionLocal, engine
from app.db.base_class import Base
import app.models.user
import app.models.empleado
from app.models.user import User, RolEnum
from app.models.empleado import Grupo
from app.core.security import get_password_hash

Base.metadata.create_all(bind=engine)
db = SessionLocal()

R  = "\033[91m"
G  = "\033[92m"
Y  = "\033[93m"
B  = "\033[94m"
M  = "\033[95m"
C  = "\033[96m"
W  = "\033[97m"
X  = "\033[0m"

def cls():
    os.system('cls' if os.name == 'nt' else 'clear')

def sep(titulo=""):
    print(f"\n{B}{'---'*17}{X}")
    if titulo:
        print(f"{W}  {titulo}{X}")
        print(f"{B}{'---'*17}{X}")

def pausar():
    input(f"\n{Y}  Presiona ENTER para continuar...{X}")

# ── LISTAR ──────────────────────────────────────
def listar_usuarios():
    cls()
    sep("LISTADO DE USUARIOS")
    usuarios = db.query(User).all()
    if not usuarios:
        print(f"\n{R}  No hay usuarios registrados.{X}")
        pausar()
        return
    ROL_COLOR = {"admin": M, "supervisor": B, "operador": G}
    print(f"\n  {'ID':<5} {'NOMBRE':<22} {'EMAIL':<30} {'ROL':<12} {'ACTIVO'}")
    print(f"  {'─'*5} {'─'*22} {'─'*30} {'─'*12} {'─'*6}")
    for u in usuarios:
        color = ROL_COLOR.get(u.rol.value, W)
        activo = f"{G}Si{X}" if u.activo else f"{R}No{X}"
        print(f"  {Y}{u.id:<5}{X} {u.nombre:<22} {C}{u.email:<30}{X} {color}{u.rol.value:<12}{X} {activo}")
    print(f"\n  {W}Total: {len(usuarios)} usuario(s){X}")
    pausar()

# ── CREAR ────────────────────────────────────────
def crear_usuario():
    cls()
    sep("CREAR NUEVO USUARIO")
    print(f"\n{Y}  (Deja en blanco y presiona ENTER para cancelar){X}\n")
    nombre = input(f"  {W}Nombre completo:{X} ").strip()
    if not nombre: print(f"{R}  Cancelado.{X}"); pausar(); return
    email = input(f"  {W}Correo electronico:{X} ").strip()
    if not email: print(f"{R}  Cancelado.{X}"); pausar(); return
    if db.query(User).filter(User.email == email).first():
        print(f"\n{R}  ERROR: Ese correo ya esta registrado.{X}"); pausar(); return
    password = input(f"  {W}Contrasena:{X} ").strip()
    if not password: print(f"{R}  Cancelado.{X}"); pausar(); return
    print(f"\n  {W}Roles:{X} {M}admin{X} | {B}supervisor{X} | {G}operador{X}")
    rol_input = input(f"  {W}Rol:{X} ").strip().lower()
    if rol_input not in ["admin", "supervisor", "operador"]:
        print(f"\n{R}  Rol invalido. Use: admin, supervisor u operador.{X}"); pausar(); return
    nuevo = User(
        nombre=nombre, email=email,
        hashed_password=get_password_hash(password),
        rol=RolEnum(rol_input), activo=True
    )
    db.add(nuevo); db.commit(); db.refresh(nuevo)
    print(f"\n{G}  OK: Usuario '{nombre}' creado con ID: {nuevo.id} | Rol: {rol_input}{X}")
    pausar()

# ── EDITAR ───────────────────────────────────────
def editar_usuario():
    cls()
    sep("EDITAR USUARIO")
    try:
        user_id = int(input(f"\n  {W}ID del usuario a editar:{X} ").strip())
    except ValueError:
        print(f"{R}  ID invalido.{X}"); pausar(); return
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        print(f"\n{R}  No se encontro usuario con ID {user_id}.{X}"); pausar(); return
    print(f"\n  Nombre:  {C}{u.nombre}{X}")
    print(f"  Email:   {C}{u.email}{X}")
    print(f"  Rol:     {M}{u.rol.value}{X}")
    print(f"  Activo:  {'Si' if u.activo else 'No'}")
    print(f"\n{Y}  (Deja en blanco para no cambiar ese campo){X}\n")
    nuevo_nombre = input(f"  Nuevo nombre [{u.nombre}]: ").strip()
    nuevo_email  = input(f"  Nuevo email  [{u.email}]: ").strip()
    nueva_pass   = input(f"  Nueva contrasena (oculta): ").strip()
    print(f"\n  Roles: {M}admin{X} | {B}supervisor{X} | {G}operador{X}")
    nuevo_rol    = input(f"  Nuevo rol [{u.rol.value}]: ").strip().lower()
    activo_inp   = input(f"  Activo? (s/n) [{'s' if u.activo else 'n'}]: ").strip().lower()
    if nuevo_nombre: u.nombre = nuevo_nombre
    if nuevo_email:
        if db.query(User).filter(User.email == nuevo_email, User.id != user_id).first():
            print(f"\n{R}  Ese email ya esta en uso.{X}"); pausar(); return
        u.email = nuevo_email
    if nueva_pass: u.hashed_password = get_password_hash(nueva_pass)
    if nuevo_rol:
        if nuevo_rol in ["admin", "supervisor", "operador"]:
            u.rol = RolEnum(nuevo_rol)
        else:
            print(f"{Y}  Rol invalido, se mantuvo el actual.{X}")
    if activo_inp == 's': u.activo = True
    elif activo_inp == 'n': u.activo = False
    db.commit()
    print(f"\n{G}  OK: Usuario ID {user_id} actualizado.{X}")
    pausar()

# ── ELIMINAR ─────────────────────────────────────
def eliminar_usuario():
    cls()
    sep("ELIMINAR USUARIO")
    try:
        user_id = int(input(f"\n  {W}ID del usuario a eliminar:{X} ").strip())
    except ValueError:
        print(f"{R}  ID invalido.{X}"); pausar(); return
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        print(f"\n{R}  No se encontro usuario con ID {user_id}.{X}"); pausar(); return
    print(f"\n  {R}ATENCION: Eliminaras permanentemente:{X}")
    print(f"  Nombre: {C}{u.nombre}{X} | Email: {C}{u.email}{X} | Rol: {M}{u.rol.value}{X}")
    confirm = input(f"\n  {R}Escribe SI para confirmar:{X} ").strip()
    if confirm != "SI":
        print(f"{Y}  Cancelado.{X}"); pausar(); return
    db.delete(u); db.commit()
    print(f"\n{G}  OK: Usuario '{u.nombre}' eliminado.{X}")
    pausar()

# ── GRUPOS ───────────────────────────────────────
def listar_grupos():
    cls()
    sep("GRUPOS CREADOS")
    grupos = db.query(Grupo).all()
    if not grupos:
        print(f"\n{R}  No hay grupos registrados.{X}"); pausar(); return
    print(f"\n  {'ID':<5} {'NOMBRE':<30} {'DESCRIPCION'}")
    print(f"  {'─'*5} {'─'*30} {'─'*30}")
    for g in grupos:
        print(f"  {Y}{g.id:<5}{X} {C}{g.nombre:<30}{X} {g.descripcion or '---'}")
    print(f"\n  {W}Total: {len(grupos)} grupo(s){X}")
    pausar()

# ── MENU PRINCIPAL ───────────────────────────────
def menu():
    while True:
        cls()
        print(f"""
{B}  ====================================================
     NEXO DATA - ADMINISTRADOR DE BASE DE DATOS
  ===================================================={X}

  {Y}[1]{X}  Listar todos los usuarios
  {Y}[2]{X}  Crear nuevo usuario
  {Y}[3]{X}  Editar usuario existente
  {Y}[4]{X}  Eliminar usuario
  {Y}[5]{X}  Ver grupos
  {R}[0]{X}  Salir
""")
        opcion = input(f"  {W}Elige:{X} ").strip()
        if   opcion == "1": listar_usuarios()
        elif opcion == "2": crear_usuario()
        elif opcion == "3": editar_usuario()
        elif opcion == "4": eliminar_usuario()
        elif opcion == "5": listar_grupos()
        elif opcion == "0":
            db.close()
            print(f"\n{G}  Hasta luego!\n{X}")
            sys.exit(0)
        else:
            print(f"{R}  Opcion no valida.{X}"); pausar()

if __name__ == "__main__":
    menu()
