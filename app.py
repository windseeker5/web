from flask import Flask, render_template, request, redirect, url_for, session, abort
from dotenv import load_dotenv
from datetime import datetime, timezone
import stripe
import os
import json
import secrets
from subprocess import run
from shutil import copytree

from utils.deploy_helpers import insert_admin_user
from utils.email_helpers import init_mail, send_user_deployment_email, send_support_error_email
from utils.mail import mail
import subprocess




# ✅ Load environment variables
load_dotenv()

# ✅ Initialize Flask app
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback123")

# ✅ Stripe setup
stripe.api_key = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")

# ✅ Flask-Mail setup
init_mail(app)
mail.init_app(app)



# ✅ Footer year context
@app.context_processor
def inject_now():
    return {'now': datetime.now(timezone.utc)}



# ✅ Homepage
@app.route("/")
def landing_page():
    return render_template("hero.html")
    #return render_template("index.html")





# ✅ Handle form submit
@app.route("/start-checkout", methods=["POST"])
def start_checkout():
    plan = request.form.get("plan")
    app_name = request.form.get("app_name")
    admin_email = request.form.get("admin_email")
    admin_password = secrets.token_urlsafe(12)

    session["checkout_info"] = {
        "plan": plan,
        "app_name": app_name,
        "admin_email": admin_email,
        "admin_password": admin_password
    }

    return redirect(url_for("create_checkout_session"))

# ✅ Stripe session
@app.route("/create-checkout-session", methods=["GET", "POST"])
def create_checkout_session():
    info = session.get("checkout_info", {})
    plan_key = info.get("plan", "basic").lower()

    plan_map = {
        "basic": {"price": 1000, "name": "MiniPass Basic"},
        "pro": {"price": 2500, "name": "MiniPass Pro"},
        "ultimate": {"price": 5000, "name": "MiniPass Ultimate"},
    }
    plan = plan_map.get(plan_key, plan_map["basic"])

    session_obj = stripe.checkout.Session.create(
        payment_method_types=["card"],
        line_items=[{
            "price_data": {
                "currency": "cad",
                "product_data": {"name": plan["name"]},
                "unit_amount": plan["price"],
            },
            "quantity": 1,
        }],
        mode="payment",
        success_url=url_for("deployment_in_progress", _external=True),
        cancel_url=url_for("landing_page", _external=True) + "?cancelled=true",
        metadata={
            "app_name": info.get("app_name", ""),
            "admin_email": info.get("admin_email", ""),
            "admin_password": info.get("admin_password", "")
        }
    )

    return redirect(session_obj.url, code=303)

# ✅ Deployment progress page
@app.route("/deployment-in-progress")
def deployment_in_progress():
    return render_template("deployment_progress.html")




# ✅ Webhook listener
@app.route("/webhook", methods=["POST"])
def stripe_webhook():
    import subprocess  # ✅ Ensure subprocess is imported
    from utils.email_helpers import send_support_error_email, send_user_deployment_email
    from shutil import copytree
    import os

    payload = request.data
    sig_header = request.headers.get("stripe-signature")
    webhook_secret = os.getenv("STRIPE_WEBHOOK_SECRET")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, webhook_secret)
    except ValueError:
        return "Invalid payload", 400
    except stripe.error.SignatureVerificationError:
        return "Invalid signature", 400

    if event["type"] == "checkout.session.completed":
        session_data = event["data"]["object"]
        metadata = session_data.get("metadata", {})
        app_name = metadata.get("app_name")
        admin_email = metadata.get("admin_email")
        admin_password = metadata.get("admin_password")

        print(f"✅ Payment confirmed for: {app_name}")
        print(f"🚀 Triggering container setup for {admin_email}")

        try:
            # 🔧 Copy app source
            base_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
            project_dir = os.path.join(base_path, "deployed", app_name)
            app_src = os.path.join(base_path, "app")
            app_dst = os.path.join(project_dir, "app")

            def ignore_git(dir, contents):
                return ['.git'] if '.git' in contents else []

            copytree(app_src, app_dst, dirs_exist_ok=True, ignore=ignore_git)
            print(f"📦 App copied to {app_dst}")

            # ❗ We DO NOT modify the SQLite DB here

            # ✅ Use full path to the script in /minipass_env/scripts/
            script_path = os.path.join(base_path, "scripts", "deploy_container.sh")
            result = subprocess.run(
                ["bash", script_path, app_name, admin_email, admin_password],
                capture_output=True, text=True, check=True
            )

            # ✅ Basic verification of output
            if "minipass_" in result.stdout or "App deployed" in result.stdout:
                print("✅ Deployment successful")
                app_url = f"https://{app_name}.minipass.me"
                send_user_deployment_email(admin_email, app_url, admin_password)
            else:
                raise RuntimeError("Container deployment did not return expected output")

        except Exception as e:
            print(f"❌ Deployment error: {e}")
            error_output = getattr(e, 'output', '') or getattr(e, 'stderr', '') or str(e)
            send_support_error_email(admin_email, app_name, error_output)
            return "Deployment failed", 500

    return "OK", 200




# ✅ Run server
if __name__ == "__main__":
    app.run(debug=True, port=5000)
