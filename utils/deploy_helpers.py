import sqlite3
import bcrypt
import os
import subprocess
from shutil import copytree



def insert_admin_user(db_path, email, password):
    import sqlite3
    import bcrypt

    print(f"🔐 Inserting admin: {email} into {db_path}")
    print(f"🔑 Raw password: {password}")

    hashed = bcrypt.hashpw(password.encode(), bcrypt.gensalt())  # no decode()

    conn = sqlite3.connect(db_path)
    cur = conn.cursor()

    # ✅ Define password_hash as BLOB
    cur.execute("""
    CREATE TABLE IF NOT EXISTS Admin (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        email TEXT UNIQUE NOT NULL,
        password_hash BLOB NOT NULL
    )
    """)

    # 🧹 Remove old admin if present
    cur.execute("DELETE FROM Admin")

    # ✅ Insert password hash as binary
    cur.execute("""
    INSERT INTO Admin (email, password_hash)
    VALUES (?, ?)
    """, (email, hashed))

    conn.commit()
    conn.close()







def deploy_customer_container(app_name, admin_email, admin_password, plan, port):
    import os, shutil, subprocess
    from .deploy_helpers import insert_admin_user

    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))


    # ✅ Explicit plan-to-folder mapping
    plan_folder_map = {
        "basic": "app_o1",
        "pro": "app_o2",
        "ultimate": "app_o3"
    }
    source_folder = plan_folder_map.get(plan.lower(), "app_o1")
    source_dir = os.path.join(base_dir, source_folder)
    target_dir = os.path.join(base_dir, "deployed", app_name, "app")
    os.makedirs(os.path.dirname(target_dir), exist_ok=True)

    print(f"📦 Copying app plan '{plan}' from {source_dir} → {target_dir}")
    shutil.copytree(source_dir, target_dir)

    # 🔐 Inject admin password
    db_path = os.path.join(target_dir, "instance", "dev_database.db")
    insert_admin_user(db_path, admin_email, admin_password)



    import textwrap

    # 🐳 Write docker-compose.yml
    compose_path = os.path.join(base_dir, "deployed", app_name, "docker-compose.yml")

    compose_content = textwrap.dedent(f"""\
version: '3.8'

services:
  flask-app:
    container_name: minipass_{app_name}
    build:
      context: ./app

    volumes:
      - ./app:/app
      - ./app/instance:/app/instance      
    environment:
      - FLASK_ENV=dev
      - ADMIN_EMAIL={admin_email}
      - ADMIN_PASSWORD={admin_password}
      - ORG_NAME={app_name}
    ports:
      - "{port}:5000"
    restart: unless-stopped
""")

    with open(compose_path, "w") as f:
        f.write(compose_content)






    # 🚀 Deploy the container
    deploy_dir = os.path.join(base_dir, "deployed", app_name)
    try:
        result = subprocess.run(
            ["docker-compose", "up", "-d"],
            cwd=deploy_dir,
            capture_output=True,
            text=True,
            check=True
        )
        print(result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Deployment failed:\n{e.stderr}")
        return False
